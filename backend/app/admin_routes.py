"""
管理员后台路由
提供管理员界面和相关API
"""
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user

from backend.app import db, cache
from backend.app.decorators import admin_required
from backend.app.models import Movie, User, Review, ReviewLike, Rating
from backend.services.tmdb_service import TMDBService
from backend.services.douban_service import MockMovieService


def _safe_isoformat(value, default=None):
    """安全将日期转为 ISO 字符串，兼容 datetime 对象和字符串（如 '0000-00-00'）"""
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.isoformat()
    s = str(value)
    if s.startswith('0000') or s.startswith('00'):
        return default
    return s[:19] if len(s) >= 10 else s

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录页面"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_admin:
                flash('您没有管理员权限', 'error')
                return render_template('admin/login.html')
            
            if not user.is_active:
                flash('账户已被禁用', 'error')
                return render_template('admin/login.html')
            
            # 更新登录统计
            from flask_login import login_user
            login_user(user)
            user.last_login = datetime.utcnow()
            user.login_count += 1
            db.session.commit()
            
            return redirect(url_for('admin.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('admin/login.html')


@admin_bp.route('/')
@login_required
@admin_required
@cache.cached(timeout=300)
def dashboard():
    """管理员仪表板"""
    # 统计数据
    stats = {
        'total_users': User.query.count(),
        'total_movies': Movie.query.count(),
        'admin_count': User.query.filter_by(is_admin=True).count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'movies_with_poster': Movie.query.filter(Movie.poster_url.isnot(None)).count(),
        'movies_with_director': Movie.query.filter(Movie.director.isnot(None)).count(),
    }
    
    # 最近注册用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # 最近更新的电影
    recent_movies = Movie.query.order_by(Movie.updated_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_movies=recent_movies)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard_alias():
    """管理员仪表板别名（兼容前端链接）"""
    return dashboard()


@admin_bp.route('/movies')
@login_required
@admin_required
def movies_list():
    """电影列表页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Movie.query
    
    if search:
        query = query.filter(Movie.title.contains(search))
    
    if status:
        query = query.filter(Movie.status == status)
    
    pagination = query.order_by(Movie.updated_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/movies.html', 
                         pagination=pagination, 
                         search=search, 
                         status=status)


@admin_bp.route('/movies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_movie():
    """添加电影页面"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        year = request.form.get('year', type=int)
        
        if not title:
            flash('电影标题不能为空', 'error')
            return render_template('admin/add_movie.html')
        
        # 检查是否已存在
        existing = Movie.query.filter_by(title=title, year=year).first()
        if existing:
            flash('该电影已存在', 'error')
            return render_template('admin/add_movie.html')
        
        # 创建电影
        movie = Movie(
            title=title,
            year=year,
            status='pending'
        )
        
        db.session.add(movie)
        db.session.commit()
        
        # 尝试自动获取详细信息
        try:
            api_key = current_app.config.get('TMDB_API_KEY')
            if api_key:
                service = TMDBService(api_key=api_key)
            else:
                service = MockMovieService()
            
            data = service.enrich_movie_data(title, year)
            
            if data:
                movie.director = data.get('director')
                movie.description = data.get('overview')
                movie.poster_url = data.get('poster_url')
                movie.backdrop_url = data.get('backdrop_url')
                movie.runtime = data.get('runtime')
                movie.tmdb_id = data.get('tmdb_id')
                movie.imdb_id = data.get('imdb_id')
                movie.original_title = data.get('original_title')
                movie.language = data.get('language')
                movie.country = data.get('country')
                
                if data.get('actors'):
                    movie.set_actors_list(data['actors'])
                
                movie.status = 'active'
                db.session.commit()
                
                flash('电影添加成功，已自动获取详细信息', 'success')
            else:
                flash('电影添加成功，但未找到详细信息，请手动补充', 'warning')
                
        except Exception as e:
            flash(f'电影添加成功，但获取详细信息失败: {e}', 'warning')
        
        return redirect(url_for('admin.movies_list'))
    
    return render_template('admin/add_movie.html')


@admin_bp.route('/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_movie(movie_id):
    """编辑电影页面"""
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form.get('title', '').strip()
        movie.year = request.form.get('year', type=int)
        movie.director = request.form.get('director', '').strip()
        movie.description = request.form.get('description', '').strip()
        movie.genres = request.form.get('genres', '').strip()
        movie.runtime = request.form.get('runtime', type=int)
        movie.poster_url = request.form.get('poster_url', '').strip()
        movie.backdrop_url = request.form.get('backdrop_url', '').strip()
        movie.trailer_url = request.form.get('trailer_url', '').strip()
        movie.status = request.form.get('status', 'active')
        movie.is_featured = request.form.get('is_featured') == 'on'
        
        # 处理演员列表
        actors_input = request.form.get('actors', '').strip()
        if actors_input:
            actors = [actor.strip() for actor in actors_input.split(',') if actor.strip()]
            movie.set_actors_list(actors)
        
        db.session.commit()
        flash('电影信息更新成功', 'success')
        return redirect(url_for('admin.movies_list'))
    
    return render_template('admin/edit_movie.html', movie=movie)


@admin_bp.route('/movies/<int:movie_id>/fetch-metadata', methods=['POST'])
@login_required
@admin_required
def fetch_movie_metadata(movie_id):
    """手动获取电影元数据"""
    movie = Movie.query.get_or_404(movie_id)
    
    try:
        api_key = current_app.config.get('TMDB_API_KEY')
        if api_key:
            service = TMDBService(api_key=api_key)
        else:
            service = MockMovieService()
        
        data = service.enrich_movie_data(movie.title, movie.year)
        
        if not data:
            return jsonify({'success': False, 'message': '未找到匹配的电影信息'}), 404
        
        # 更新电影信息
        movie.director = data.get('director')
        movie.description = data.get('overview')
        movie.poster_url = data.get('poster_url')
        movie.backdrop_url = data.get('backdrop_url')
        movie.runtime = data.get('runtime')
        movie.tmdb_id = data.get('tmdb_id')
        movie.imdb_id = data.get('imdb_id')
        movie.original_title = data.get('original_title')
        movie.language = data.get('language')
        movie.country = data.get('country')
        
        if data.get('actors'):
            movie.set_actors_list(data['actors'])
        
        movie.status = 'active'
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '元数据获取成功',
            'data': {
                'director': movie.director,
                'poster_url': movie.poster_url,
                'actors': movie.get_actors_list()[:5]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@admin_bp.route('/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_movie(movie_id):
    """删除电影"""
    movie = Movie.query.get_or_404(movie_id)
    
    try:
        db.session.delete(movie)
        db.session.commit()
        flash(f'电影《{movie.title}》已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {e}', 'error')
    
    return redirect(url_for('admin.movies_list'))


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """用户列表页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(User.username.contains(search))
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', 
                         pagination=pagination, 
                         search=search)


# ==================== 评论管理 ====================

from backend.app.models import Review

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews_list():
    """评论管理页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Review.query
    
    if status:
        query = query.filter(Review.status == status)
    
    pagination = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/reviews.html', 
                         pagination=pagination, 
                         status=status)


@admin_bp.post('/reviews/<int:review_id>/approve')
@login_required
@admin_required
def approve_review(review_id):
    """审核通过评论"""
    review = Review.query.get_or_404(review_id)
    
    review.status = 'approved'
    db.session.commit()
    
    flash('评论已审核通过', 'success')
    return redirect(url_for('admin.reviews_list'))


@admin_bp.post('/reviews/<int:review_id>/reject')
@login_required
@admin_required
def reject_review(review_id):
    """拒绝评论"""
    review = Review.query.get_or_404(review_id)
    
    review.status = 'rejected'
    db.session.commit()
    
    flash('评论已被拒绝', 'warning')
    return redirect(url_for('admin.reviews_list'))


@admin_bp.post('/reviews/<int:review_id>/delete')
@login_required
@admin_required
def admin_delete_review(review_id):
    """删除评论"""
    review = Review.query.get_or_404(review_id)
    
    try:
        db.session.delete(review)
        db.session.commit()
        flash('评论已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {e}', 'error')
    
    return redirect(url_for('admin.reviews_list'))


@admin_bp.get('/api/admin/reviews/stats')
@login_required
@admin_required
def reviews_stats():
    """获取评论统计数据"""
    stats = {
        'total_reviews': Review.query.count(),
        'approved_reviews': Review.query.filter_by(status='approved').count(),
        'pending_reviews': Review.query.filter_by(status='pending').count(),
        'rejected_reviews': Review.query.filter_by(status='rejected').count(),
        'featured_reviews': Review.query.filter_by(is_featured=True).count(),
        'total_likes': db.session.query(db.func.sum(Review.likes_count)).scalar() or 0
    }
    
    return jsonify(stats)


# ==================== 观看链接管理 ====================

from backend.app.models import WatchLink

@admin_bp.route('/watch-links')
@login_required
@admin_required
def watch_links_list():
    """观看链接管理页面"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = WatchLink.query
    
    if status:
        query = query.filter(WatchLink.status == status)
    
    pagination = query.order_by(WatchLink.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/watch_links.html', 
                         pagination=pagination, 
                         status=status)


@admin_bp.post('/watch-links/<int:link_id>/approve')
@login_required
@admin_required
def approve_watch_link(link_id):
    """审核通过观看链接"""
    link = WatchLink.query.get_or_404(link_id)
    
    link.status = 'active'
    db.session.commit()
    
    flash('观看链接已审核通过', 'success')
    return redirect(url_for('admin.watch_links_list'))


@admin_bp.post('/watch-links/<int:link_id>/reject')
@login_required
@admin_required
def reject_watch_link(link_id):
    """拒绝观看链接"""
    link = WatchLink.query.get_or_404(link_id)
    
    link.status = 'inactive'
    db.session.commit()
    
    flash('观看链接已被拒绝', 'warning')
    return redirect(url_for('admin.watch_links_list'))


@admin_bp.post('/watch-links/<int:link_id>/delete')
@login_required
@admin_required
def delete_watch_link(link_id):
    """删除观看链接"""
    link = WatchLink.query.get_or_404(link_id)
    
    try:
        db.session.delete(link)
        db.session.commit()
        flash('观看链接已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {e}', 'error')
    
    return redirect(url_for('admin.watch_links_list'))


# ==================== 电影榜单管理 ====================

from backend.app.models import MovieChart, ChartItem

@admin_bp.route('/charts')
@login_required
@admin_required
def charts_list():
    """榜单管理页面"""
    charts = MovieChart.query.order_by(MovieChart.sort_order).all()
    return render_template('admin/charts.html', charts=charts)


@admin_bp.post('/charts/<int:chart_id>/toggle')
@login_required
@admin_required
def toggle_chart(chart_id):
    """启用/禁用榜单"""
    chart = MovieChart.query.get_or_404(chart_id)
    chart.is_active = not chart.is_active
    db.session.commit()
    
    status = '启用' if chart.is_active else '禁用'
    flash(f'榜单已{status}', 'success')
    return redirect(url_for('admin.charts_list'))


@admin_bp.post('/charts/create')
@login_required
@admin_required
def create_chart():
    """创建榜单"""
    data = request.get_json() or request.form
    
    chart = MovieChart(
        title=data.get('title'),
        description=data.get('description'),
        chart_type=data.get('chart_type', 'hot'),
        genre=data.get('genre'),
        year=data.get('year'),
        sort_order=data.get('sort_order', 0)
    )
    
    db.session.add(chart)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'chart': chart.to_dict()})
    
    flash('榜单创建成功', 'success')
    return redirect(url_for('admin.charts_list'))


# ==================== 电影元数据管理 ====================

@admin_bp.route('/metadata-management')
@login_required
@admin_required
def metadata_management():
    """电影元数据管理页面"""
    return render_template('admin/metadata_management.html')


@admin_bp.route('/api/metadata-stats')
@login_required
@admin_required
def metadata_stats():
    """元数据统计API"""
    try:
        from sqlalchemy import func
        
        # 总电影数
        total_movies = Movie.query.count()
        
        # 缺少元数据的电影
        missing_metadata = Movie.query.filter(
            (Movie.title.is_(None) | (Movie.title == '')) |
            (Movie.year.is_(None)) |
            (Movie.director.is_(None) | (Movie.director == '')) |
            (Movie.genres.is_(None) | (Movie.genres == ''))
        ).count()
        
        # 缺少海报的电影
        missing_posters = Movie.query.filter(
            (Movie.poster_url.is_(None) | (Movie.poster_url == ''))
        ).count()
        
        # 完整信息的电影
        complete_movies = total_movies - missing_metadata
        
        return jsonify({
            'total_movies': total_movies,
            'missing_metadata': missing_metadata,
            'missing_posters': missing_posters,
            'complete_movies': complete_movies
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/movies-metadata')
@login_required
@admin_required
def movies_metadata():
    """电影元数据列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        metadata_status = request.args.get('metadata_status', '').strip()
        poster_status = request.args.get('poster_status', '').strip()
        
        # 构建查询
        query = Movie.query
        
        # 搜索过滤
        if search:
            query = query.filter(Movie.title.ilike(f'%{search}%'))
        
        # 元数据状态过滤
        if metadata_status == 'complete':
            query = query.filter(
                Movie.title.isnot(None) & (Movie.title != '') &
                Movie.year.isnot(None) &
                Movie.director.isnot(None) & (Movie.director != '') &
                Movie.genres.isnot(None) & (Movie.genres != '')
            )
        elif metadata_status == 'incomplete':
            query = query.filter(
                (Movie.title.is_(None) | (Movie.title == '')) |
                (Movie.year.is_(None)) |
                (Movie.director.is_(None) | (Movie.director == '')) |
                (Movie.genres.is_(None) | (Movie.genres == ''))
            )
        elif metadata_status == 'missing':
            query = query.filter(
                (Movie.title.is_(None) | (Movie.title == ''))
            )
        
        # 海报状态过滤
        if poster_status == 'has':
            query = query.filter(Movie.poster_url.isnot(None) & (Movie.poster_url != ''))
        elif poster_status == 'missing':
            query = query.filter(Movie.poster_url.is_(None) | (Movie.poster_url == ''))
        
        # 分页
        pagination = query.paginate(page=page, per_page=20, error_out=False)
        
        movies = []
        for movie in pagination.items:
            movies.append({
                'id': movie.id,
                'title': movie.title,
                'year': movie.year,
                'director': movie.director,
                'genres': movie.genres,
                'poster_url': movie.poster_url,
                'updated_at': _safe_isoformat(movie.updated_at)
            })
        
        return jsonify({
            'movies': movies,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 权限管理系统 ====================

@admin_bp.route('/permission-management')
@login_required
@admin_required
def permission_management():
    """权限管理页面"""
    return render_template('admin/permission_management.html')


@admin_bp.route('/api/permission-stats')
@login_required
@admin_required
@cache.cached(timeout=300)
def permission_stats():
    """权限统计API（缓存5分钟）"""
    from sqlalchemy import func
    try:
        # 总用户数
        total_users = User.query.count()
        
        # 管理员数
        admin_users = User.query.filter_by(is_admin=True).count()
        
        # 未活跃管理员（30天未登录）
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        inactive_admins = User.query.filter(
            User.is_admin == True,
            User.last_login < thirty_days_ago
        ).count()
        
        # 今日登录
        today = datetime.utcnow().date()
        recent_logins = User.query.filter(
            func.date(User.last_login) == today
        ).count()
        
        return jsonify({
            'total_users': total_users,
            'admin_users': admin_users,
            'inactive_admins': inactive_admins,
            'recent_logins': recent_logins
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users-permissions')
@login_required
@admin_required
def users_permissions():
    """用户权限列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        user_type = request.args.get('user_type', '').strip()
        permission_level = request.args.get('permission_level', '').strip()
        
        # 构建查询
        query = User.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                (User.username.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%'))
            )
        
        # 用户类型过滤
        if user_type == 'admin':
            query = query.filter_by(is_admin=True)
        elif user_type == 'user':
            query = query.filter_by(is_admin=False)
        elif user_type == 'inactive':
            query = query.filter_by(is_active=False)
        
        # 权限级别过滤（这里需要在User模型中添加permission_level字段）
        # 暂时跳过这个过滤
        
        # 分页
        pagination = query.paginate(page=page, per_page=20, error_out=False)
        
        users = []
        for user in pagination.items:
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_active': user.is_active,
                'avatar': user.avatar,
                'last_login': _safe_isoformat(user.last_login),
                'created_at': _safe_isoformat(user.created_at),
                'permission_level': 'admin' if user.is_admin else 'user'  # 简化处理
            })
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 消息通知系统 ====================

@admin_bp.route('/notification-management')
@login_required
@admin_required
def notification_management():
    """消息通知管理页面"""
    return render_template('admin/notification_management.html')


@admin_bp.route('/api/notification-stats')
@login_required
@admin_required
def notification_stats():
    """通知统计API"""
    from sqlalchemy import func
    try:
        from backend.app.models import Notification
        from datetime import datetime
        
        # 总通知数
        total_notifications = Notification.query.count()
        
        # 已读通知数
        read_notifications = Notification.query.filter_by(is_read=True).count()
        
        # 未读通知数
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        # 今日发送通知数
        today = datetime.utcnow().date()
        today_notifications = Notification.query.filter(
            func.date(Notification.created_at) == today
        ).count()
        
        return jsonify({
            'total_notifications': total_notifications,
            'read_notifications': read_notifications,
            'unread_notifications': unread_notifications,
            'today_notifications': today_notifications
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/notifications')
@login_required
@admin_required
def notifications():
    """通知列表API"""
    try:
        from backend.app.models import Notification
        
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        notification_type = request.args.get('type', '').strip()
        status = request.args.get('status', '').strip()
        
        # 构建查询
        query = Notification.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                (Notification.title.ilike(f'%{search}%')) |
                (Notification.content.ilike(f'%{search}%'))
            )
        
        # 类型过滤
        if notification_type:
            query = query.filter_by(type=notification_type)
        
        # 状态过滤
        if status == 'read':
            query = query.filter_by(is_read=True)
        elif status == 'unread':
            query = query.filter_by(is_read=False)
        
        # 分页
        pagination = query.paginate(page=page, per_page=20, error_out=False)
        
        notifications = []
        for notification in pagination.items:
            notifications.append({
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'type': notification.type,
                'target_user': notification.user.username if notification.user else None,
                'is_read': notification.is_read,
                'created_at': _safe_isoformat(notification.created_at)
            })
        
        return jsonify({
            'notifications': notifications,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 评分审核系统 ====================

@admin_bp.route('/ratings/pending')
@login_required
@admin_required
@cache.cached(timeout=120, query_string=True)  # 缓存2分钟，按页码分键
def pending_ratings():
    """待审核评分列表（快速版：跳过 COUNT(*)，假分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # 用 id DESC 代替 timestamp DESC（走 PRIMARY 主键索引，毫秒级）
    # timestmp 缺少单列索引 → ORDER BY timestamp 会全表扫描 32M 行
    items = (
        Rating.query
        .order_by(Rating.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )

    # 近似总数（instant），用于"是否有下一页"的假分页
    approx_total = db.session.execute(
        db.text("SELECT table_rows FROM information_schema.tables WHERE table_name='ratings' AND table_schema=DATABASE()")
    ).scalar() or 0

    class FastPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = max(1, total // per_page)
            self.has_next = page * per_page < total
            self.has_prev = page > 1
            self.prev_num = page - 1 if page > 1 else None
            self.next_num = page + 1 if page * per_page < total else None
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            # Simplified page iterator for the template
            pages = set()
            for i in range(1, min(left_edge, self.pages) + 1):
                pages.add(i)
            for i in range(max(1, self.page - left_current), min(self.pages, self.page + right_current) + 1):
                pages.add(i)
            for i in range(max(1, self.pages - right_edge + 1), self.pages + 1):
                pages.add(i)
            return sorted(p for p in pages if 1 <= p <= self.pages)
        def __iter__(self):
            return iter(self.items)

    pagination = FastPagination(items, page, per_page, int(approx_total))

    return render_template('admin/pending_ratings.html',
                         pagination=pagination,
                         suspicious_users=[])


@admin_bp.get('/api/admin/ratings/stats')
@login_required
@admin_required
@cache.cached(timeout=300)
def ratings_stats():
    """评分统计数据（缓存5分钟）"""
    from sqlalchemy import func
    
    total_ratings = Rating.query.count()
    avg_rating = db.session.query(func.avg(Rating.rating)).scalar() or 0
    
    # 评分分布
    distribution = db.session.query(
        Rating.rating,
        func.count(Rating.id).label('count')
    ).group_by(Rating.rating).all()
    
    return jsonify({
        'total_ratings': total_ratings,
        'avg_rating': round(float(avg_rating), 2),
        'distribution': {str(d[0]): d[1] for d in distribution}
    })


# ==================== 通知管理 ====================

from backend.app.models import Notification

@admin_bp.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def send_notification():
    """发送系统通知"""
    data = request.get_json() or request.form
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    user_ids = data.get('user_ids', [])  # 空列表表示发给所有用户
    
    if not title:
        if request.is_json:
            return jsonify({'error': '标题不能为空'}), 400
        flash('标题不能为空', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # 发送给指定用户或所有用户
    if user_ids:
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type='system',
                title=title,
                content=content
            )
            db.session.add(notification)
    else:
        # 发送给所有用户
        users = User.query.filter_by(is_active=True).all()
        for user in users:
            notification = Notification(
                user_id=user.id,
                type='system',
                title=title,
                content=content
            )
            db.session.add(notification)
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': '通知发送成功'})
    
    flash('通知发送成功', 'success')
    return redirect(url_for('admin.dashboard'))


# ==================== 系统日志管理 ====================

@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """系统日志查看页面"""
    return render_template('admin/logs.html')


@admin_bp.route('/data-export')
@login_required
@admin_required
def data_export():
    """数据导出页面"""
    return render_template('admin/data_export.html')


@admin_bp.route('/api/admin/logs')
@login_required
@admin_required
def get_logs():
    """获取系统日志API"""
    try:
        import os
        from pathlib import Path
        
        log_file = Path(current_app.config.get('LOG_FILE', 'logs/app.log'))
        
        if not log_file.exists():
            return jsonify({
                'logs': [],
                'total': 0,
                'message': '日志文件不存在'
            })
        
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析JSON格式的日志
        logs = []
        for line in lines[-1000:]:  # 只读取最后1000行
            line = line.strip()
            if not line:
                continue
            
            try:
                import json
                log_data = json.loads(line)
                logs.append(log_data)
            except json.JSONDecodeError:
                # 如果不是JSON格式，跳过
                continue
        
        # 按时间倒序排列
        logs.reverse()
        
        return jsonify({
            'logs': logs,
            'total': len(logs)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'logs': []
        }), 500


@admin_bp.route('/api/admin/logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    """清空系统日志"""
    try:
        from pathlib import Path
        
        log_file = Path(current_app.config.get('LOG_FILE', 'logs/app.log'))
        
        if log_file.exists():
            # 清空日志文件
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('')
            
            return jsonify({
                'success': True,
                'message': '日志已清空'
            })
        else:
            return jsonify({
                'success': True,
                'message': '日志文件不存在'
            })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
