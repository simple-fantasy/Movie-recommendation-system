"""
权限装饰器模块
"""
from functools import wraps

from flask import abort, flash, jsonify, redirect, request, url_for
from flask_login import current_user


def _is_api_request():
    """判断是否为 API 请求（JSON 响应而不是页面跳转）"""
    return request.path.startswith('/api/') or request.path.startswith('/admin/api/')


def admin_required(f):
    """
    管理员权限装饰器
    确保只有管理员可以访问被装饰的视图函数

    API 路径返回 JSON 403，页面路径返回 302 重定向。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if _is_api_request():
                return jsonify({"error": "请先登录"}), 401
            flash('请先登录', 'warning')
            return redirect(url_for('main.index'))

        if not current_user.is_admin:
            if _is_api_request():
                return jsonify({"error": "您没有管理员权限"}), 403
            flash('您没有权限访问此页面', 'error')
            return redirect(url_for('main.index'))

        if not current_user.is_active:
            if _is_api_request():
                return jsonify({"error": "您的账户已被禁用"}), 403
            flash('您的账户已被禁用', 'error')
            return redirect(url_for('main.index'))

        return f(*args, **kwargs)
    return decorated_function
