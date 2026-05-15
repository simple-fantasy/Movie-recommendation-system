"""
权限装饰器模块
"""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    管理员权限装饰器
    确保只有管理员可以访问被装饰的视图函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('main.index'))
        
        if not current_user.is_admin:
            flash('您没有权限访问此页面', 'error')
            return redirect(url_for('main.index'))
        
        if not current_user.is_active:
            flash('您的账户已被禁用', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    活跃用户权限装饰器
    确保只有激活状态的用户可以访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('main.index'))
        
        if not current_user.is_active:
            flash('您的账户已被禁用', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function
