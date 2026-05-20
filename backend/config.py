"""
配置模块
使用Settings进行统一配置管理，保持向后兼容
"""
from backend.settings import get_settings

# 获取Settings实例
_settings = get_settings()


class Config:
    """Flask配置类（向后兼容）"""
    
    # Flask基础配置
    SECRET_KEY = _settings.secret_key
    DEBUG = _settings.debug
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = _settings.database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = _settings.sqlalchemy_track_modifications
    
    # 连接池优化配置
    SQLALCHEMY_ENGINE_OPTIONS = _settings.get_sqlalchemy_engine_options()
    
    # TMDB API配置
    TMDB_API_KEY = _settings.tmdb_api_key
    
    # 推荐系统参数
    ITEMCF_TOPK = _settings.itemcf_topk
    NCF_EMBEDDING_DIM = _settings.ncf_embedding_dim
    NCF_HIDDEN_DIM = _settings.ncf_hidden_dim
    NCF_LR = _settings.ncf_lr
    NCF_BATCH_SIZE = _settings.ncf_batch_size
    NCF_EPOCHS = _settings.ncf_epochs
    
    # 缓存配置
    CACHE_TYPE = _settings.cache_type
    CACHE_DEFAULT_TIMEOUT = _settings.cache_default_timeout
    CACHE_DIR = _settings.cache_dir
    
    # 限流配置
    RATE_LIMIT_ENABLED = _settings.rate_limit_enabled
    RATE_LIMIT_PER_MINUTE = _settings.rate_limit_per_minute
    
    # 日志配置
    LOG_LEVEL = _settings.log_level
    LOG_FILE = _settings.log_file
    
    @classmethod
    def validate(cls) -> None:
        """验证配置有效性
        
        在应用启动时调用，确保关键配置符合安全要求。
        
        注意：配置验证已在Settings类中通过pydantic完成，
        此方法保留用于向后兼容。
        
        Raises:
            ValueError: 当配置不符合要求时抛出
        """
        # Settings类已经通过pydantic进行了验证
        # 这里只做额外的业务逻辑验证
        pass
