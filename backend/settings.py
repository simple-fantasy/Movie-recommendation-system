"""
配置管理模块
使用pydantic进行配置验证和管理
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # Flask基础配置
    flask_env: str = Field(default="development", env="FLASK_ENV")
    secret_key: str = Field(default="", env="SECRET_KEY")
    debug: bool = Field(default=False, env="DEBUG")

    # 数据库配置 — 必须通过 .env 文件或环境变量提供
    database_url: str = Field(
        default="",
        env="DATABASE_URL"
    )

    # TMDB API配置 — 必须通过 .env 文件或环境变量提供
    tmdb_api_key: str = Field(
        default="",
        env="TMDB_API_KEY"
    )
    
    # ItemCF参数
    itemcf_topk: int = Field(default=50, env="ITEMCF_TOPK")
    
    # NCF模型参数
    ncf_embedding_dim: int = Field(default=32, env="NCF_EMBEDDING_DIM")
    ncf_hidden_dim: int = Field(default=64, env="NCF_HIDDEN_DIM")
    ncf_lr: float = Field(default=0.001, env="NCF_LR")
    ncf_batch_size: int = Field(default=256, env="NCF_BATCH_SIZE")
    ncf_epochs: int = Field(default=20, env="NCF_EPOCHS")
    
    # 缓存配置
    cache_type: str = Field(default="FileSystemCache", env="CACHE_TYPE")
    cache_default_timeout: int = Field(default=300, env="CACHE_DEFAULT_TIMEOUT")
    cache_dir: str = Field(default="data/cache", env="CACHE_DIR")
    
    # 限流配置
    rate_limit_enabled: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # SQLAlchemy配置
    sqlalchemy_track_modifications: bool = False
    sqlalchemy_echo: bool = False
    
    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    
    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """验证SECRET_KEY强度"""
        if values.get("flask_env") == "production":
            if len(v) < 16:
                raise ValueError("生产环境SECRET_KEY长度至少16位")
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v:
            return v  # 允许空值（由 .env 提供）
        allowed_drivers = ["mysql+pymysql", "sqlite", "postgresql"]
        if not any(v.startswith(d) for d in allowed_drivers):
            raise ValueError(f"不支持的数据库驱动，支持的驱动: {', '.join(allowed_drivers)}")
        return v
    
    @validator("ncf_embedding_dim", "ncf_hidden_dim")
    def validate_embedding_dim(cls, v):
        """验证embedding维度"""
        if v <= 0 or v > 512:
            raise ValueError("embedding维度必须在1-512之间")
        return v
    
    @validator("rate_limit_per_minute")
    def validate_rate_limit(cls, v):
        """验证限流参数"""
        if v <= 0 or v > 1000:
            raise ValueError("限流值必须在1-1000之间")
        return v
    
    def get_sqlalchemy_engine_options(self) -> dict:
        """获取SQLAlchemy引擎配置"""
        opts = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.sqlalchemy_echo,
        }
        if self.pool_pre_ping:
            opts["pool_pre_ping"] = True
        return opts
    
    class Config:
        env_file = str(Path(__file__).resolve().parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    获取Settings单例
    
    使用lru_cache确保配置只加载一次，提高性能
    """
    return Settings()


# 为了向后兼容，导出settings实例
settings = get_settings()
