"""
中间件模块
包含全局错误处理、请求日志等中间件
"""
import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Tuple
import time

from flask import jsonify, request, g
from flask_login import current_user

from backend.app.logging_config import get_logger, log_error as log_error_structured, log_request

logger = get_logger(__name__)


def handle_all_errors(app):
    """
    全局错误处理器
    
    统一处理所有异常，返回标准化的错误响应格式，
    并记录详细的错误日志用于排查问题。
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误 - 请求参数错误"""
        log_error_internal(e, "BAD_REQUEST", 400)
        return error_response("请求参数错误", "BAD_REQUEST", 400)
    
    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误 - 未授权"""
        log_error_internal(e, "UNAUTHORIZED", 401)
        return error_response("未授权，请先登录", "UNAUTHORIZED", 401)
    
    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误 - 禁止访问"""
        log_error_internal(e, "FORBIDDEN", 403)
        return error_response("权限不足", "FORBIDDEN", 403)
    
    @app.errorhandler(404)
    def not_found(e):
        """处理404错误 - 资源不存在"""
        log_error_internal(e, "NOT_FOUND", 404)
        return error_response("请求的资源不存在", "NOT_FOUND", 404)
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """处理405错误 - 方法不允许"""
        log_error_internal(e, "METHOD_NOT_ALLOWED", 405)
        return error_response("请求方法不允许", "METHOD_NOT_ALLOWED", 405)
    
    @app.errorhandler(429)
    def too_many_requests(e):
        """处理429错误 - 请求过多"""
        log_error_internal(e, "TOO_MANY_REQUESTS", 429)
        return error_response("请求过于频繁，请稍后再试", "TOO_MANY_REQUESTS", 429)
    
    @app.errorhandler(500)
    def internal_error(e):
        """处理500错误 - 服务器内部错误"""
        log_error_internal(e, "INTERNAL_ERROR", 500)
        return error_response("服务器内部错误", "INTERNAL_ERROR", 500)
    
    @app.errorhandler(503)
    def service_unavailable(e):
        """处理503错误 - 服务不可用"""
        log_error_internal(e, "SERVICE_UNAVAILABLE", 503)
        return error_response("服务暂时不可用，请稍后再试", "SERVICE_UNAVAILABLE", 503)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """
        处理所有未捕获的异常
        
        这是最后的错误处理防线，确保任何异常都不会导致
        服务器返回500错误给用户，而是返回友好的错误信息。
        """
        log_error_internal(e, "UNEXPECTED_ERROR", 500)
        return error_response("服务器发生意外错误", "UNEXPECTED_ERROR", 500)


def error_response(message: str, code: str, status: int) -> Tuple[Dict[str, Any], int]:
    """
    统一错误响应格式
    
    Args:
        message: 错误消息
        code: 错误代码
        status: HTTP状态码
    
    Returns:
        (响应字典, 状态码)
    """
    return {
        "error": message,
        "code": code,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.path,
        "method": request.method
    }, status


def log_error_internal(e: Exception, error_type: str, status: int):
    """
    内部错误日志记录函数
    
    Args:
        e: 异常对象
        error_type: 错误类型
        status: HTTP状态码
    """
    log_error_structured(
        logger,
        e,
        error_type=error_type,
        path=request.path,
        user_id=current_user.id if current_user.is_authenticated else None
    )


def log_error(e: Exception, error_type: str, status: int):
    """
    记录错误日志
    
    Args:
        e: 异常对象
        error_type: 错误类型
        status: HTTP状态码
    """
    log_error_structured(
        logger,
        e,
        error_type=error_type,
        path=request.path,
        user_id=current_user.id if current_user.is_authenticated else None
    )


def request_logging_middleware(app):
    """
    请求日志中间件
    
    记录所有请求的基本信息，包括：
    - 请求路径和方法
    - 响应状态码
    - 请求耗时
    - 用户信息
    
    Args:
        app: Flask应用实例
    """
    
    @app.before_request
    def before_request():
        """请求开始时记录时间"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """请求结束时记录响应信息"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # 使用结构化日志记录请求
            log_request(
                logger,
                method=request.method,
                path=request.path,
                user_id=current_user.id if current_user.is_authenticated else None,
                status_code=response.status_code,
                duration=duration
            )
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """请求结束时清理资源"""
        if exception:
            logger.error(
                "Request teardown with exception",
                exc_info=exception,
                extra={
                    "event": "request_teardown",
                    "path": request.path,
                    "method": request.method,
                }
            )


def validate_json_content_type(f):
    """
    验证JSON请求内容类型的装饰器
    
    对于需要JSON数据的API端点，确保请求的Content-Type正确。
    
    Args:
        f: 被装饰的视图函数
    
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                return error_response(
                    "请求Content-Type必须是application/json",
                    "INVALID_CONTENT_TYPE",
                    400
                )
        return f(*args, **kwargs)
    return decorated_function


def validate_required_fields(required_fields: list):
    """
    验证必填字段的装饰器工厂
    
    Args:
        required_fields: 必填字段列表
    
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json(silent=True) or {}
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return error_response(
                        f"缺少必填字段: {', '.join(missing_fields)}",
                        "MISSING_REQUIRED_FIELDS",
                        400
                    )
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_exceeded_handler(e):
    """
    限流超出错误处理器
    
    Args:
        e: 限流异常
    
    Returns:
        错误响应
    """
    log_error(e, "RATE_LIMIT_EXCEEDED", 429)
    return error_response(
        "请求过于频繁，请稍后再试",
        "RATE_LIMIT_EXCEEDED",
        429
    )
