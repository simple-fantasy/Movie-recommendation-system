"""
Flask 应用工厂模块。

CineMatch 电影推荐系统的应用入口，负责:
1. 创建和配置 Flask 应用实例
2. 初始化所有扩展（SQLAlchemy、LoginManager、Cache、Migrate）
3. 注册蓝图（main、admin）
4. 注册中间件（错误处理、请求日志、限流）
5. 首次启动时的数据库初始化、索引创建、示例数据填充
6. Jinja2 与 Vue.js 模板语法冲突解决

架构说明:
- 使用 Flask Application Factory 模式，通过 create_app() 创建应用实例
- 导入延迟到函数内部以避免循环依赖（models ↔ app ↔ routes）
- NCF 模型通过 before_request 钩子异步预加载
"""

from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from jinja2 import ChainableUndefined

from backend.config import Config
from backend.app.middleware import handle_all_errors, request_logging_middleware
from backend.app.logging_config import setup_logging
from backend.app.rate_limit import rate_limit_middleware


# 扩展实例（模块级单例，由 create_app() 初始化）
db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
migrate = Migrate()


def _ensure_indexes(app):
    """
    确保关键性能索引存在。

    MySQL 5.7 不支持 CREATE INDEX IF NOT EXISTS，
    各数据库对重复创建索引的行为不同，
    因此逐条 try/except——索引已存在时静默忽略，不影响启动。
    """
    indexes = [
        ("CREATE INDEX ix_ratings_timestamp ON ratings (timestamp)", "ix_ratings_timestamp"),
        ("CREATE INDEX ix_users_created_at ON users (created_at)", "ix_users_created_at"),
        ("CREATE INDEX ix_user_behaviors_user_id ON user_behaviors (user_id)", "ix_user_behaviors_user_id"),
        ("CREATE INDEX ix_movies_genres ON movies (genres)", "ix_movies_genres"),
        ("CREATE INDEX ix_movies_avg_rating ON movies (avg_rating)", "ix_movies_avg_rating"),
        ("CREATE INDEX ix_movies_director ON movies (director)", "ix_movies_director"),
        ("CREATE INDEX ix_movies_updated_at ON movies (updated_at)", "ix_movies_updated_at"),
        ("CREATE INDEX ix_movies_status ON movies (status)", "ix_movies_status"),
    ]
    for idx_sql, _idx_name in indexes:
        try:
            db.session.execute(db.text(idx_sql))
            db.session.commit()
        except Exception:
            db.session.rollback()


def create_app() -> Flask:
    """
    创建并配置 Flask 应用。

    启动流程:
    1. 设置 Jinja2 ChainableUndefined（解决 Vue {{ }} 与 Jinja2 冲突）
    2. 加载 Config → 初始化扩展 → 配置日志/缓存
    3. 注册蓝图（main、admin）
    4. 注册错误处理、日志、限流中间件
    5. 在 app_context 中执行启动初始化（建表、索引、种子数据）
    6. 注册 before_request 钩子异步预加载 NCF 模型

    返回:
        配置完成的 Flask 应用实例
    """
    app = Flask(__name__)

    # Jinja2 与 Vue.js 共存：未定义变量链式访问返回空字符串而非抛出 UndefinedError
    app.jinja_env.undefined = ChainableUndefined

    # 全局 Jinja2 过滤器：安全日期格式化
    from datetime import datetime as _dt

    @app.template_filter('safe_date')
    def safe_date(value, fmt='%Y-%m-%d'):
        """模板中安全格式化日期，兼容 None、datetime 和字符串。"""
        if value is None:
            return 'N/A'
        if isinstance(value, _dt):
            return value.strftime(fmt)
        s = str(value)
        if s.startswith('0000'):
            return 'N/A'
        return s[:10] if len(s) >= 10 else s

    # 加载配置
    Config.validate()
    app.config.from_object(Config)

    # Session Cookie 配置
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1天

    # 配置日志系统（structlog 可用时使用 JSON 结构化日志）
    setup_logging(
        app=app,
        log_level=Config.LOG_LEVEL,
        log_file=Config.LOG_FILE
    )

    # 缓存配置（FileSystemCache 磁盘持久化，重启不丢失）
    app.config["CACHE_TYPE"] = Config.CACHE_TYPE
    app.config["CACHE_DEFAULT_TIMEOUT"] = Config.CACHE_DEFAULT_TIMEOUT
    app.config["CACHE_DIR"] = Config.CACHE_DIR
    import os as _os
    _os.makedirs(Config.CACHE_DIR, exist_ok=True)

    # 初始化 Flask 扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 初始化行为追踪模块（提供 app 引用供 worker 线程使用）
    from backend.app.behavior_tracker import init_behavior_tracker
    init_behavior_tracker(app)

    # API 未登录时返回 JSON 错误（而非 HTML 重定向），避免前端收到乱码
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify, redirect, request, url_for
        if request.path.startswith('/api/'):
            return jsonify({"error": "请先登录"}), 401
        return redirect(url_for('main.index'))

    cache.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图（延迟导入以避免循环依赖）
    from backend.app.routes import bp
    from backend.app.admin_routes import admin_bp

    app.register_blueprint(bp)
    app.register_blueprint(admin_bp)

    # 注册全局中间件
    handle_all_errors(app)          # 统一错误处理
    request_logging_middleware(app)  # 请求日志记录
    rate_limit_middleware(app)       # 限流（默认关闭，通过 RATE_LIMIT_ENABLED 控制）

    # ── 应用启动初始化 ──
    with app.app_context():
        # 首次启动时自动创建表结构（后续启动可安全调用，不会影响已有数据）
        # 生产环境建议使用 Alembic 迁移管理 schema 变更
        db.create_all()

        # 确保关键性能索引存在
        _ensure_indexes(app)

        # 数据库为空时自动填充示例数据（20部电影 + demo 用户）
        from backend.app.models import Movie, User, Rating, WatchLink
        from backend.app.seed import seed_sample_data, _seed_watch_links
        just_seeded = seed_sample_data(db, Movie, User, Rating)
        if just_seeded:
            movies = Movie.query.all()
            _seed_watch_links(db, WatchLink, movies)
            # 后台线程丰富 TMDB 海报，不阻塞启动
            import threading

            def _enrich_posters():
                with app.app_context():
                    try:
                        from backend.scripts.enrich_movies import enrich_movies
                        enrich_movies(skip_existing=True, posters_only=True)
                    except Exception as e:
                        app.logger.warning(f"Background poster enrichment failed: {e}")

            threading.Thread(target=_enrich_posters, daemon=True).start()

        # 首次启动时填充电影统计数据（avg_rating / rating_count）
        try:
            from backend.app.routes import _ensure_movie_stats_populated
            _ensure_movie_stats_populated()
        except Exception as e:
            app.logger.warning(f"Movie stats population failed: {e}")

    # ── NCF 模型异步预加载 ──
    # 在应用启动时立即触发后台加载，不等待首次请求。
    # before_request 钩子仅负责检测模型文件更新并自动热重载。
    _ncf_initial_preload_done = False

    def _start_ncf_preload():
        """在后台线程中触发 NCF 模型预加载。"""
        import threading
        def _load():
            try:
                from backend.app.ncf_engine import ncf_engine
                ncf_engine.load()
            except ImportError:
                pass  # PyTorch 未安装
            except Exception as e:
                app.logger.warning(f"NCF preload failed: {e}")
        t = threading.Thread(target=_load, daemon=True)
        t.start()

    # 延迟一帧启动预加载，确保应用完全初始化
    _start_ncf_preload()

    @app.before_request
    def _preload_ncf():
        nonlocal _ncf_initial_preload_done
        try:
            from backend.app.ncf_engine import ncf_engine
            # 首次请求时，如果预加载尚未完成，再触发一次确保不遗漏
            if not _ncf_initial_preload_done:
                _ncf_initial_preload_done = True
                if not ncf_engine.is_ready() and not ncf_engine.is_loading():
                    ncf_engine.load_async()
            # 模型已就绪时检测文件更新，支持热重载
            if ncf_engine.is_ready():
                ncf_engine.maybe_auto_reload()
        except ImportError:
            pass

    return app
