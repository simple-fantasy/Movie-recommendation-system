"""
用户行为追踪模块
提供装饰器和工具函数来记录用户行为
"""

import functools
import uuid
from flask import request, session, current_app
from flask_login import current_user
from datetime import datetime
from .models import UserBehavior, db


def track_behavior(action_type, target_type=None, target_id=None, metadata=None):
    """
    行为追踪装饰器
    
    Args:
        action_type (str): 行为类型，如 'view', 'rate', 'search', 'click'
        target_type (str): 目标类型，如 'movie', 'person', 'genre'
        target_id (int): 目标ID
        metadata (dict): 额外的元数据
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 异步记录行为（不阻塞主流程）
            try:
                record_behavior_async(action_type, target_type, target_id, metadata)
            except Exception as e:
                # 记录失败不影响主功能
                current_app.logger.debug(f"Behavior tracking failed: {e}")
            
            return result
        return decorated_function
    return decorator


def record_behavior_async(action_type, target_type=None, target_id=None, metadata=None):
    """异步记录用户行为"""
    # 检查是否启用行为追踪
    if not current_app.config.get('ENABLE_BEHAVIOR_TRACKING', True):
        return
    
    # 只记录已登录用户的行为
    if not current_user.is_authenticated:
        return
    
    try:
        # 获取会话ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        # 准备元数据
        behavior_extra_data = metadata or {}
        
        # 添加请求信息
        if request:
            behavior_extra_data.update({
                'method': request.method,
                'endpoint': request.endpoint,
                'args': dict(request.args),
                'form_data': dict(request.form) if request.form else {}
            })
        
        # 创建行为记录
        behavior = UserBehavior(
            user_id=current_user.id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            extra_data=behavior_extra_data,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
            session_id=session_id,
            referrer=request.referrer if request else None
        )
        
        # 异步保存到数据库
        from threading import Thread
        
        def save_behavior():
            try:
                db.session.add(behavior)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.debug(f"Failed to save behavior: {e}")
        
        thread = Thread(target=save_behavior)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        current_app.logger.debug(f"Behavior tracking error: {e}")


def track_search_behavior(query, filters=None, results_count=0):
    """记录搜索行为"""
    metadata = {
        'query': query,
        'filters': filters or {},
        'results_count': results_count,
        'search_timestamp': datetime.utcnow().isoformat()
    }
    
    record_behavior_async('search', 'search_query', None, metadata)


def track_movie_view(movie_id, source='direct'):
    """记录电影查看行为"""
    metadata = {
        'source': source,
        'view_timestamp': datetime.utcnow().isoformat()
    }
    
    record_behavior_async('view', 'movie', movie_id, metadata)


def track_rating_behavior(movie_id, rating, previous_rating=None):
    """记录评分行为"""
    metadata = {
        'rating': rating,
        'previous_rating': previous_rating,
        'is_update': previous_rating is not None,
        'rating_timestamp': datetime.utcnow().isoformat()
    }
    
    record_behavior_async('rate', 'movie', movie_id, metadata)


def track_recommendation_click(movie_id, strategy, position=None):
    """记录推荐点击行为"""
    metadata = {
        'strategy': strategy,
        'position': position,
        'click_timestamp': datetime.utcnow().isoformat()
    }
    
    record_behavior_async('click', 'movie', movie_id, metadata)


def track_page_view(page_name, additional_data=None):
    """记录页面访问行为"""
    metadata = {
        'page': page_name,
        'additional_data': additional_data or {},
        'view_timestamp': datetime.utcnow().isoformat()
    }
    
    record_behavior_async('view', 'page', None, metadata)


def get_user_behavior_summary(user_id, days=30):
    """获取用户行为摘要"""
    try:
        from datetime import timedelta
        from sqlalchemy import func, and_
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 基础统计
        total_behaviors = UserBehavior.query.filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date
            )
        ).count()
        
        # 按行为类型统计
        behavior_types = db.session.query(
            UserBehavior.action_type,
            func.count(UserBehavior.id).label('count')
        ).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date
            )
        ).group_by(UserBehavior.action_type).all()
        
        # 按目标类型统计
        target_types = db.session.query(
            UserBehavior.target_type,
            func.count(UserBehavior.id).label('count')
        ).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date,
                UserBehavior.target_type.isnot(None)
            )
        ).group_by(UserBehavior.target_type).all()
        
        # 活跃天数
        active_days = db.session.query(
            func.count(func.distinct(func.date(UserBehavior.created_at)))
        ).filter(
            and_(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= start_date
            )
        ).scalar()
        
        return {
            'total_behaviors': total_behaviors,
            'behavior_types': {bt: count for bt, count in behavior_types},
            'target_types': {tt: count for tt, count in target_types},
            'active_days': active_days,
            'period_days': days,
            'avg_daily_behaviors': total_behaviors / max(active_days, 1)
        }
        
    except Exception as e:
        current_app.logger.error(f"Failed to get user behavior summary: {e}")
        return {
            'total_behaviors': 0,
            'behavior_types': {},
            'target_types': {},
            'active_days': 0,
            'period_days': days,
            'avg_daily_behaviors': 0
        }


def get_behavior_analytics(days=7):
    """获取行为分析数据（管理员用）"""
    try:
        from datetime import timedelta
        from sqlalchemy import func, and_
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 每日行为统计
        daily_stats = db.session.query(
            func.date(UserBehavior.created_at).label('date'),
            func.count(UserBehavior.id).label('count')
        ).filter(
            UserBehavior.created_at >= start_date
        ).group_by(
            func.date(UserBehavior.created_at)
        ).order_by('date').all()
        
        # 热门行为类型
        popular_actions = db.session.query(
            UserBehavior.action_type,
            func.count(UserBehavior.id).label('count')
        ).filter(
            UserBehavior.created_at >= start_date
        ).group_by(UserBehavior.action_type).order_by(
            func.count(UserBehavior.id).desc()
        ).limit(10).all()
        
        # 活跃用户统计
        active_users = db.session.query(
            func.count(func.distinct(UserBehavior.user_id))
        ).filter(
            UserBehavior.created_at >= start_date
        ).scalar()
        
        # 热门目标（电影、页面等）
        popular_targets = db.session.query(
            UserBehavior.target_type,
            UserBehavior.target_id,
            func.count(UserBehavior.id).label('count')
        ).filter(
            and_(
                UserBehavior.created_at >= start_date,
                UserBehavior.target_type.isnot(None),
                UserBehavior.target_id.isnot(None)
            )
        ).group_by(
            UserBehavior.target_type,
            UserBehavior.target_id
        ).order_by(
            func.count(UserBehavior.id).desc()
        ).limit(20).all()
        
        return {
            'daily_stats': [(date.isoformat(), count) for date, count in daily_stats],
            'popular_actions': [(action, count) for action, count in popular_actions],
            'active_users': active_users,
            'popular_targets': [
                {
                    'target_type': target_type,
                    'target_id': target_id,
                    'count': count
                }
                for target_type, target_id, count in popular_targets
            ],
            'period_days': days
        }
        
    except Exception as e:
        current_app.logger.error(f"Failed to get behavior analytics: {e}")
        return {
            'daily_stats': [],
            'popular_actions': [],
            'active_users': 0,
            'popular_targets': [],
            'period_days': days
        }


def cleanup_old_behaviors(days=90):
    """清理旧的行为数据"""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = UserBehavior.query.filter(
            UserBehavior.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        current_app.logger.info(f"Cleaned up {deleted_count} old behavior records")
        return deleted_count
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to cleanup old behaviors: {e}")
        return 0
