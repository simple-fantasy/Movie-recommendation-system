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


db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)

    # 允许 Vue.js {{ }} 与 Jinja2 共存：未定义变量链式访问不报错
    app.jinja_env.undefined = ChainableUndefined

    # 全局 Jinja2 过滤器：安全日期格式化（兼容 datetime 和字符串）
    from datetime import datetime as _dt
    @app.template_filter('safe_date')
    def safe_date(value, fmt='%Y-%m-%d'):
        if value is None:
            return 'N/A'
        if isinstance(value, _dt):
            return value.strftime(fmt)
        # 字符串类型：截取日期部分
        s = str(value)
        if s.startswith('0000'):
            return 'N/A'
        return s[:10] if len(s) >= 10 else s

    # 验证配置
    Config.validate()

    app.config.from_object(Config)

    # Session Cookie 配置（解决登录状态丢失）
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1天

    # 配置日志系统
    setup_logging(
        app=app,
        log_level=Config.LOG_LEVEL,
        log_file=Config.LOG_FILE
    )

    # 缓存配置（FileSystemCache 磁盘持久化，重启不丢失）
    app.config["CACHE_TYPE"] = Config.CACHE_TYPE
    app.config["CACHE_DEFAULT_TIMEOUT"] = Config.CACHE_DEFAULT_TIMEOUT
    app.config["CACHE_DIR"] = Config.CACHE_DIR
    # 确保缓存目录存在
    import os as _os
    _os.makedirs(Config.CACHE_DIR, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # API 未登录时返回 JSON 错误，而非 HTML 重定向（避免前端显示乱码）
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify, redirect, request, url_for
        if request.path.startswith('/api/'):
            return jsonify({"error": "请先登录"}), 401
        return redirect(url_for('main.index'))

    cache.init_app(app)
    migrate.init_app(app, db)

    from backend.app.routes import bp
    from backend.app.admin_routes import admin_bp

    app.register_blueprint(bp)
    app.register_blueprint(admin_bp)

    # 注册全局错误处理器和中间件
    handle_all_errors(app)
    request_logging_middleware(app)
    rate_limit_middleware(app)

    with app.app_context():
        db.create_all()
        # 确保性能索引存在（MySQL 5.7 不支持 IF NOT EXISTS 语法，需逐条 try/except）
        for idx_sql, idx_name in [
            ("CREATE INDEX ix_ratings_timestamp ON ratings (timestamp)", "ix_ratings_timestamp"),
            ("CREATE INDEX ix_users_created_at ON users (created_at)", "ix_users_created_at"),
            ("CREATE INDEX ix_movies_genres ON movies (genres)", "ix_movies_genres"),
            ("CREATE INDEX ix_movies_avg_rating ON movies (avg_rating)", "ix_movies_avg_rating"),
            ("CREATE INDEX ix_movies_director ON movies (director)", "ix_movies_director"),
            ("CREATE INDEX ix_movies_updated_at ON movies (updated_at)", "ix_movies_updated_at"),
            ("CREATE INDEX ix_movies_status ON movies (status)", "ix_movies_status"),
        ]:
            try:
                db.session.execute(db.text(idx_sql))
                db.session.commit()
            except Exception:
                db.session.rollback()
                # 索引已存在或其他错误（忽略，不阻塞启动）
        # Auto-seed sample data if database is empty
        from backend.app.models import Movie, User, Rating, WatchLink
        from backend.app.seed import seed_sample_data, _seed_watch_links
        just_seeded = seed_sample_data(db, Movie, User, Rating)
        if just_seeded:
            # Seed watch links for sample movies
            movies = Movie.query.all()
            _seed_watch_links(db, WatchLink, movies)
            # Enrich posters in background thread so startup isn't blocked
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

    # 启动时异步预加载NCF模型（Flask 3.0兼容写法）
    _ncf_preloaded = False

    @app.before_request
    def _preload_ncf():
        nonlocal _ncf_preloaded
        if _ncf_preloaded:
            return
        try:
            from backend.app.ncf_engine import ncf_engine
            if not ncf_engine.is_ready() and not ncf_engine.is_loading():
                ncf_engine.load_async()
            _ncf_preloaded = True
        except ImportError as e:
            # NCF引擎可选，没有torch时不影响其他功能
            app.logger.debug(f"NCF engine not loaded: {e}")

    return app
