"""
日志配置模块
使用structlog进行结构化日志记录
"""
import logging
import sys
from pathlib import Path

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None


def setup_logging(app=None, log_level: str = "INFO", log_file: str = "logs/app.log"):
    """
    配置结构化日志
    
    Args:
        app: Flask应用实例（可选）
        log_level: 日志级别
        log_file: 日志文件路径
    """
    if not STRUCTLOG_AVAILABLE:
        print("警告: structlog未安装，使用标准日志")
        _setup_standard_logging(log_level, log_file)
        return
    
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    
    # 配置文件日志
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # 如果有Flask应用，配置应用日志
    if app:
        app.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        app.logger.addHandler(file_handler)
        
        # 配置SQLAlchemy日志
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)


def _setup_standard_logging(log_level: str, log_file: str):
    """
    配置标准日志（当structlog不可用时）
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str = None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器实例
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def log_request(logger, method: str, path: str, user_id: int = None, 
               status_code: int = None, duration: float = None):
    """
    记录请求日志
    
    Args:
        logger: 日志记录器
        method: HTTP方法
        path: 请求路径
        user_id: 用户ID
        status_code: 响应状态码
        duration: 请求耗时（秒）
    """
    logger.info(
        "HTTP Request",
        method=method,
        path=path,
        user_id=user_id,
        status_code=status_code,
        duration_seconds=duration
    )


def log_error(logger, error: Exception, error_type: str = None, 
              path: str = None, user_id: int = None):
    """
    记录错误日志
    
    Args:
        logger: 日志记录器
        error: 异常对象
        error_type: 错误类型
        path: 请求路径
        user_id: 用户ID
    """
    logger.error(
        error_type or type(error).__name__,
        error_message=str(error),
        path=path,
        user_id=user_id,
        exc_info=True
    )


def log_user_action(logger, action: str, user_id: int, 
                   target_type: str = None, target_id: int = None, **kwargs):
    """
    记录用户行为日志
    
    Args:
        logger: 日志记录器
        action: 行为类型
        user_id: 用户ID
        target_type: 目标类型
        target_id: 目标ID
        **kwargs: 额外信息
    """
    logger.info(
        "User Action",
        action=action,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        **kwargs
    )


def log_recommendation(logger, user_id: int, strategy: str, 
                     count: int = None, **kwargs):
    """
    记录推荐日志
    
    Args:
        logger: 日志记录器
        user_id: 用户ID
        strategy: 推荐策略
        count: 推荐数量
        **kwargs: 额外信息
    """
    logger.info(
        "Recommendation Generated",
        user_id=user_id,
        strategy=strategy,
        recommendation_count=count,
        **kwargs
    )
