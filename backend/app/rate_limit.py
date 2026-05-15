"""
API限流中间件
使用内存存储实现基于IP和用户的请求限流
"""
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, List, Tuple

from flask import jsonify, request, g
from flask_login import current_user

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    限流器类
    
    使用滑动窗口算法实现请求限流。
    支持基于IP地址和用户ID的限流。
    """
    
    def __init__(self):
        # 存储请求时间戳：key为标识符（IP或用户ID），value为请求时间戳列表
        self.requests: Dict[str, List[float]] = defaultdict(list)
        
        # 限流配置（请求次数, 时间窗口秒数）
        self.limits = {
            'default': (60, 60),      # 默认：60次/分钟
            'strict': (30, 60),       # 严格：30次/分钟
            'lenient': (120, 60),     # 宽松：120次/分钟
            'api': (100, 60),         # API：100次/分钟
            'auth': (10, 60),         # 认证：10次/分钟
        }
    
    def is_allowed(self, identifier: str, limit_type: str = 'default') -> Tuple[bool, Dict]:
        """
        检查是否允许请求
        
        Args:
            identifier: 限流标识符（IP地址或用户ID）
            limit_type: 限流类型
        
        Returns:
            (是否允许, 限流信息字典)
        """
        max_requests, window_seconds = self.limits.get(limit_type, self.limits['default'])
        current_time = time.time()
        
        # 获取该标识符的请求记录
        request_times = self.requests[identifier]
        
        # 移除时间窗口外的旧记录
        request_times[:] = [t for t in request_times if current_time - t < window_seconds]
        
        # 检查是否超过限制
        if len(request_times) >= max_requests:
            # 计算重置时间
            oldest_request = request_times[0]
            reset_time = oldest_request + window_seconds
            wait_time = max(0, reset_time - current_time)
            
            return False, {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'reset': int(reset_time),
                'retry_after': int(wait_time),
                'window': window_seconds
            }
        
        # 记录当前请求
        request_times.append(current_time)
        
        return True, {
            'allowed': True,
            'limit': max_requests,
            'remaining': max_requests - len(request_times),
            'reset': int(current_time + window_seconds),
            'window': window_seconds
        }
    
    def cleanup(self, max_age: int = 3600):
        """
        清理过期的请求记录
        
        Args:
            max_age: 最大保留时间（秒）
        """
        current_time = time.time()
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                t for t in self.requests[identifier]
                if current_time - t < max_age
            ]
            
            # 如果没有记录了，删除该标识符
            if not self.requests[identifier]:
                del self.requests[identifier]


# 全局限流器实例
rate_limiter = RateLimiter()


def get_client_identifier() -> str:
    """
    获取客户端标识符
    
    优先使用用户ID，如果用户未登录则使用IP地址。
    
    Returns:
        客户端标识符
    """
    if current_user.is_authenticated:
        return f"user:{current_user.id}"
    else:
        # 获取真实IP地址（考虑代理）
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr
        return f"ip:{ip}"


def rate_limit(limit_type: str = 'default'):
    """
    限流装饰器
    
    Args:
        limit_type: 限流类型
    
    Returns:
        装饰器函数
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否启用限流
            from flask import current_app
            if not current_app.config.get('RATE_LIMIT_ENABLED', True):
                return f(*args, **kwargs)
            
            # 获取客户端标识符
            identifier = get_client_identifier()
            
            # 检查是否允许请求
            allowed, info = rate_limiter.is_allowed(identifier, limit_type)
            
            # 记录限流信息
            g.rate_limit_info = info
            
            if not allowed:
                # 记录限流日志
                logger.warning(
                    "Rate limit exceeded",
                    identifier=identifier,
                    limit_type=limit_type,
                    path=request.path,
                    method=request.method
                )
                
                # 返回429错误
                response = jsonify({
                    'error': '请求过于频繁，请稍后再试',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': info['retry_after']
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(info['retry_after'])
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                
                return response
            
            # 添加限流信息到响应头
            response = f(*args, **kwargs)
            
            # 如果返回的是Response对象，添加限流头
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
            
            return response
        
        return decorated_function
    return decorator


def rate_limit_middleware(app):
    """
    限流中间件
    
    对所有API请求应用限流。
    
    Args:
        app: Flask应用实例
    """
    
    @app.before_request
    def check_rate_limit():
        """检查请求限流"""
        # 跳过静态文件和健康检查
        if request.path.startswith('/static') or request.path == '/health':
            return
        
        # 跳过管理员路径（管理员不受限流限制）
        if request.path.startswith('/admin'):
            return
        
        # 只对API请求应用限流
        if not request.path.startswith('/api'):
            return
        
        # 检查是否启用限流
        if not app.config.get('RATE_LIMIT_ENABLED', True):
            return
        
        # 获取客户端标识符
        identifier = get_client_identifier()
        
        # 根据路径类型选择限流策略
        if '/auth/' in request.path or '/login' in request.path:
            limit_type = 'auth'
        else:
            limit_type = 'api'
        
        # 检查是否允许请求
        allowed, info = rate_limiter.is_allowed(identifier, limit_type)
        
        # 存储限流信息供后续使用
        g.rate_limit_info = info
        
        if not allowed:
            # 记录限流日志
            logger.warning(
                "Rate limit exceeded",
                identifier=identifier,
                limit_type=limit_type,
                path=request.path,
                method=request.method
            )
            
            # 返回429错误
            response = jsonify({
                'error': '请求过于频繁，请稍后再试',
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': info['retry_after']
            })
            response.status_code = 429
            response.headers['Retry-After'] = str(info['retry_after'])
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(info['reset'])
            
            return response
    
    @app.after_request
    def add_rate_limit_headers(response):
        """添加限流信息到响应头"""
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            response.headers['X-RateLimit-Limit'] = str(info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(info['reset'])
        
        return response


def cleanup_old_records():
    """
    定期清理过期的请求记录
    
    应该在定时任务中调用。
    """
    rate_limiter.cleanup()
    logger.info("Rate limiter cleanup completed")
