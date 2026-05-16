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

    # 缓存配置（SimpleCache内存模式，无需外部Redis）
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 默认5分钟

    db.init_app(app)
    login_manager.init_app(app)
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
        # Auto-seed sample data if database is empty
        from backend.app.models import Movie, User, Rating
        from backend.app.seed import seed_sample_data
        just_seeded = seed_sample_data(db, Movie, User, Rating)
        if just_seeded:
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

    # 启动时异步预加载NCF模型（Flask 3.0兼容写法）
    _ncf_preloaded = False
    
    @app.before_request
    def _preload_ncf():
        nonlocal _ncf_preloaded
        if _ncf_preloaded:
            return
        _ncf_preloaded = True
        try:
            from backend.app.ncf_engine import ncf_engine
            if not ncf_engine.is_ready() and not ncf_engine.is_loading():
                ncf_engine.load_async()
        except ImportError as e:
            # NCF引擎可选，没有torch时不影响其他功能
            app.logger.debug(f"NCF engine not loaded: {e}")

    return app
