from __future__ import annotations

import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app import db, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, index=True)  # 是否为管理员
    is_active = db.Column(db.Boolean, default=True)  # 账户是否激活
    last_login = db.Column(db.DateTime)  # 最后登录时间
    login_count = db.Column(db.Integer, default=0)  # 登录次数
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    ratings = db.relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")
    collections = db.relationship("UserCollection", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def make_admin(self):
        """设置为管理员"""
        self.is_admin = True
        db.session.commit()
    
    def revoke_admin(self):
        """撤销管理员权限"""
        self.is_admin = False
        db.session.commit()
    
    def update_login_stats(self):
        """更新登录统计"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M') if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=True, index=True)
    genres = db.Column(db.String(255), nullable=True)
    
    # 新增元数据字段
    original_title = db.Column(db.String(255))  # 原始标题
    director = db.Column(db.String(255))       # 导演
    actors = db.Column(db.Text)                 # 演员（JSON格式存储）
    description = db.Column(db.Text)          # 简介
    runtime = db.Column(db.Integer)             # 时长（分钟）
    poster_url = db.Column(db.String(500))     # 海报URL
    backdrop_url = db.Column(db.String(500))    # 背景图URL
    trailer_url = db.Column(db.String(500))     # 预告片URL
    tagline = db.Column(db.String(255))          # 宣传语
    tmdb_id = db.Column(db.Integer)             # TMDB ID
    imdb_id = db.Column(db.String(20))          # IMDb ID
    language = db.Column(db.String(10))         # 语言
    country = db.Column(db.String(100))         # 制片国家
    
    # 管理字段
    status = db.Column(db.Enum('active', 'inactive', 'pending'), default='active')
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ratings = db.relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    collections = db.relationship("UserCollection", back_populates="movie", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    watch_links = db.relationship("WatchLink", back_populates="movie", cascade="all, delete-orphan")
    
    # 辅助方法
    def get_actors_list(self) -> list:
        """获取演员列表"""
        if self.actors:
            try:
                return json.loads(self.actors)
            except:
                return []
        return []
    
    def set_actors_list(self, actors: list):
        """设置演员列表"""
        self.actors = json.dumps(actors, ensure_ascii=False)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'original_title': self.original_title,
            'year': self.year,
            'genres': self.genres.split('|') if self.genres else [],
            'director': self.director,
            'actors': self.get_actors_list(),
            'description': self.description,
            'runtime': self.runtime,
            'poster_url': self.poster_url,
            'backdrop_url': self.backdrop_url,
            'trailer_url': self.trailer_url,
            'avg_rating': self.avg_rating,
            'rating_count': self.rating_count,
            'view_count': self.view_count,
            'status': self.status
        }


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=True, index=True)

    user = db.relationship("User", back_populates="ratings")
    movie = db.relationship("Movie", back_populates="ratings")

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie"),
        # 复合索引：用户历史查询优化（按时间倒序）
        db.Index("idx_ratings_user_time", "user_id", "timestamp"),
        # 复合索引：电影评分统计优化
        db.Index("idx_ratings_movie_rating", "movie_id", "rating"),
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'rating': self.rating,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else None,
            'movie': self.movie.to_dict() if self.movie else None
        }


class MovieSimilarity(db.Model):
    __tablename__ = "movie_similarity"

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    similar_movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("movie_id", "similar_movie_id", name="uq_movie_similar"),
        # 复合索引：ItemCF相似度查询优化（按分数倒序）
        db.Index("idx_similarity_movie_score", "movie_id", "score"),
    )


class RecommendationFeedback(db.Model):
    __tablename__ = "recommendation_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    feedback = db.Column(db.String(16), nullable=False)  # like / dislike
    context = db.Column(db.String(64), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id", "context", name="uq_feedback_user_movie_ctx"),)


class Review(db.Model):
    """电影评论模型"""
    __tablename__ = "reviews"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float)  # 评论时的评分
    likes_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)  # 是否精选评论
    status = db.Column(db.Enum('approved', 'rejected', 'pending'), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = db.relationship("User", back_populates="reviews")
    movie = db.relationship("Movie", back_populates="reviews")
    likes = db.relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'rating': self.rating,
            'likes_count': self.likes_count,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username
            }
        }


class ReviewLike(db.Model):
    """评论点赞模型"""
    __tablename__ = "review_likes"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 复合唯一约束，防止重复点赞
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id'),)
    
    user = db.relationship("User")
    review = db.relationship("Review", back_populates="likes")


class UserCollection(db.Model):
    """用户收藏模型"""
    __tablename__ = "user_collections"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    collection_type = db.Column(db.String(20), default='favorite')  # favorite, watchlist, seen
    notes = db.Column(db.Text)  # 用户备注
    rating = db.Column(db.Float)  # 个人评分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合唯一约束，同一用户不能重复收藏同一部电影
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', 'collection_type'),)
    
    user = db.relationship("User", back_populates="collections")
    movie = db.relationship("Movie", back_populates="collections")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'collection_type': self.collection_type,
            'notes': self.notes,
            'rating': self.rating,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None,
            'movie': self.movie.to_dict() if self.movie else None
        }


class WatchLink(db.Model):
    """电影观看链接模型"""
    __tablename__ = "watch_links"
    
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # 提交者，None表示系统添加
    platform = db.Column(db.String(50), nullable=False)  # 平台名称：Netflix, YouTube, bilibili等
    url = db.Column(db.Text, nullable=False)  # 观看链接
    quality = db.Column(db.String(20), default='HD')  # 画质：SD, HD, 4K等
    is_free = db.Column(db.Boolean, default=True)  # 是否免费
    is_official = db.Column(db.Boolean, default=False)  # 是否官方链接
    status = db.Column(db.Enum('active', 'pending', 'inactive', 'reported'), default='pending')
    report_count = db.Column(db.Integer, default=0)  # 被举报次数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    movie = db.relationship("Movie", back_populates="watch_links")
    user = db.relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'url': self.url,
            'quality': self.quality,
            'is_free': self.is_free,
            'is_official': self.is_official,
            'status': self.status,
            'report_count': self.report_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


# ==================== 消息通知系统 ====================

class Notification(db.Model):
    """用户通知模型"""
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.Enum('system', 'review_reply', 'review_liked', 'movie_recommend', 'achievement'), 
                     default='system')
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    related_id = db.Column(db.Integer)  # 关联对象ID (评论ID、电影ID等)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    user = db.relationship("User", backref="notifications")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M') if self.read_at else None
        }


class UserNotificationPreference(db.Model):
    """用户通知偏好设置"""
    __tablename__ = "user_notification_preferences"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    
    # 各类通知的开关
    enable_system = db.Column(db.Boolean, default=True)      # 系统通知
    enable_review = db.Column(db.Boolean, default=True)      # 评论相关
    enable_recommend = db.Column(db.Boolean, default=True)   # 推荐通知
    enable_achievement = db.Column(db.Boolean, default=True) # 成就通知
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship("User", backref="notification_preference")


# ==================== 电影榜单系统 ====================

class MovieChart(db.Model):
    """电影榜单模型"""
    __tablename__ = "movie_charts"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    chart_type = db.Column(db.Enum('hot', 'top_rated', 'editor_pick', 'genre', 'year'), 
                          default='hot')
    genre = db.Column(db.String(50))  # 如果是类型榜单
    year = db.Column(db.Integer)  # 如果是年度榜单
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship("ChartItem", back_populates="chart", 
                          cascade="all, delete-orphan", order_by="ChartItem.rank")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'chart_type': self.chart_type,
            'genre': self.genre,
            'year': self.year,
            'is_active': self.is_active,
            'item_count': len(self.items)
        }


class ChartItem(db.Model):
    """榜单电影条目"""
    __tablename__ = "chart_items"
    
    id = db.Column(db.Integer, primary_key=True)
    chart_id = db.Column(db.Integer, db.ForeignKey("movie_charts.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=False)  # 排名
    score = db.Column(db.Float)  # 榜单评分/热度值
    note = db.Column(db.String(200))  # 上榜理由
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    chart = db.relationship("MovieChart", back_populates="items")
    movie = db.relationship("Movie")
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'rank': self.rank,
            'score': self.score,
            'note': self.note,
            'movie': {
                'id': self.movie.id,
                'title': self.movie.title,
                'poster_url': self.movie.poster_url,
                'avg_rating': self.movie.avg_rating,
                'year': self.movie.year
            }
        }


# ==================== 用户行为追踪系统 ====================

class UserBehavior(db.Model):
    """用户行为日志 - 独立表，不影响现有结构"""
    __tablename__ = "user_behaviors"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # view, rate, search, click, etc.
    target_type = db.Column(db.String(20))  # movie, person, genre, search_query
    target_id = db.Column(db.Integer)
    extra_data = db.Column(db.JSON)  # 额外信息，灵活扩展
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    session_id = db.Column(db.String(100))  # 会话ID，用于追踪用户会话
    referrer = db.Column(db.String(500))  # 来源页面
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    user = db.relationship("User", backref="behaviors")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat()
        }


# ==================== 用户画像系统 ====================

class UserProfile(db.Model):
    """用户画像模型
    
    存储用户的各种偏好和行为特征，用于个性化推荐和用户分析。
    """
    __tablename__ = "user_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # 偏好画像
    preferred_genres = db.Column(db.JSON)        # {"Action": 0.8, "Drama": 0.6}
    preferred_years = db.Column(db.JSON)          # {"1990s": 0.7, "2000s": 0.5}
    preferred_actors = db.Column(db.JSON)          # ["Tom Hanks", "Leonardo DiCaprio"]
    preferred_directors = db.Column(db.JSON)        # ["Christopher Nolan", "Steven Spielberg"]
    
    # 评分行为画像
    avg_rating_level = db.Column(db.Float)     # 平均评分水平
    rating_variance = db.Column(db.Float)      # 评分方差（苛刻程度）
    rating_entropy = db.Column(db.Float)        # 评分分散度
    
    # 观影统计
    total_watch_time = db.Column(db.Integer, default=0)   # 累计观影时长(分钟)
    genre_diversity = db.Column(db.Float)      # 类型多样性指数
    decade_diversity = db.Column(db.Float)     # 年代多样性指数
    
    # 用户分层
    user_type = db.Column(db.String(20))        # casual/regular/enthusiast
    activity_level = db.Column(db.String(20))   # low/medium/high
    
    # 时间戳
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship("User", backref="profile")
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'preferred_genres': self.preferred_genres,
            'preferred_years': self.preferred_years,
            'preferred_actors': self.preferred_actors,
            'preferred_directors': self.preferred_directors,
            'avg_rating_level': self.avg_rating_level,
            'rating_variance': self.rating_variance,
            'rating_entropy': self.rating_entropy,
            'total_watch_time': self.total_watch_time,
            'genre_diversity': self.genre_diversity,
            'decade_diversity': self.decade_diversity,
            'user_type': self.user_type,
            'activity_level': self.activity_level,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }
    
    def get_top_genres(self, n: int = 5) -> list:
        """获取前N个偏好类型"""
        if not self.preferred_genres:
            return []
        sorted_genres = sorted(self.preferred_genres.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres[:n]
    
    def get_favorite_decade(self) -> str:
        """获取最爱的年代"""
        if not self.preferred_years:
            return None
        return max(self.preferred_years.items(), key=lambda x: x[1])[0]


class MovieList(db.Model):
    """影单模型
    
    用户可以创建影单，将电影归类整理，方便管理和分享。
    支持公开和私有影单。
    """
    __tablename__ = "movie_lists"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # 影单名称
    description = db.Column(db.Text)  # 影单描述
    cover_image = db.Column(db.String(500))  # 影单封面图
    
    # 影单设置
    is_public = db.Column(db.Boolean, default=False, index=True)  # 是否公开
    is_featured = db.Column(db.Boolean, default=False, index=True)  # 是否精选
    allow_comments = db.Column(db.Boolean, default=True)  # 是否允许评论
    
    # 统计信息
    view_count = db.Column(db.Integer, default=0)  # 浏览次数
    like_count = db.Column(db.Integer, default=0)  # 点赞次数
    comment_count = db.Column(db.Integer, default=0)  # 评论次数
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship("User", backref="movie_lists")
    items = db.relationship("MovieListItem", back_populates="movie_list", cascade="all, delete-orphan")
    likes = db.relationship("MovieListLike", back_populates="movie_list", cascade="all, delete-orphan")
    comments = db.relationship("MovieListComment", back_populates="movie_list", cascade="all, delete-orphan")
    
    def to_dict(self, include_items: bool = False) -> dict:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'name': self.name,
            'description': self.description,
            'cover_image': self.cover_image,
            'is_public': self.is_public,
            'is_featured': self.is_featured,
            'allow_comments': self.allow_comments,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'movie_count': len(self.items),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }
        
        if include_items:
            result['items'] = [item.to_dict() for item in self.items]
        
        return result
    
    def increment_view(self):
        """增加浏览次数"""
        self.view_count += 1
        db.session.commit()
    
    def add_movie(self, movie_id: int, note: str = None):
        """添加电影到影单"""
        # 检查是否已存在
        existing = MovieListItem.query.filter_by(
            movie_list_id=self.id,
            movie_id=movie_id
        ).first()
        
        if existing:
            return False
        
        # 获取最大排序值
        max_order = db.session.query(db.func.max(MovieListItem.order)).filter_by(
            movie_list_id=self.id
        ).scalar() or 0
        
        # 添加新项
        item = MovieListItem(
            movie_list_id=self.id,
            movie_id=movie_id,
            order=max_order + 1,
            note=note
        )
        db.session.add(item)
        db.session.commit()
        
        return True
    
    def remove_movie(self, movie_id: int):
        """从影单中移除电影"""
        item = MovieListItem.query.filter_by(
            movie_list_id=self.id,
            movie_id=movie_id
        ).first()
        
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        
        return False
    
    def reorder_movies(self, movie_ids: list):
        """重新排序影单中的电影"""
        for index, movie_id in enumerate(movie_ids, start=1):
            item = MovieListItem.query.filter_by(
                movie_list_id=self.id,
                movie_id=movie_id
            ).first()
            
            if item:
                item.order = index
        
        db.session.commit()


class MovieListItem(db.Model):
    """影单项模型
    
    影单中的单个电影项。
    """
    __tablename__ = "movie_list_items"
    
    id = db.Column(db.Integer, primary_key=True)
    movie_list_id = db.Column(db.Integer, db.ForeignKey("movie_lists.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    order = db.Column(db.Integer, default=0)  # 排序顺序
    note = db.Column(db.Text)  # 备注
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    movie_list = db.relationship("MovieList", back_populates="items")
    movie = db.relationship("Movie", backref="list_items")
    
    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('movie_list_id', 'movie_id', name='uq_movie_list_item'),
    )
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'movie_list_id': self.movie_list_id,
            'movie_id': self.movie_id,
            'movie_title': self.movie.title if self.movie else None,
            'movie_year': self.movie.year if self.movie else None,
            'movie_poster': self.movie.poster_url if self.movie else None,
            'order': self.order,
            'note': self.note,
            'added_at': self.added_at.strftime('%Y-%m-%d %H:%M') if self.added_at else None
        }


class MovieListLike(db.Model):
    """影单点赞模型
    
    用户对影单的点赞记录。
    """
    __tablename__ = "movie_list_likes"
    
    id = db.Column(db.Integer, primary_key=True)
    movie_list_id = db.Column(db.Integer, db.ForeignKey("movie_lists.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    movie_list = db.relationship("MovieList", back_populates="likes")
    user = db.relationship("User", backref="movie_list_likes")
    
    # 联合唯一约束
    __table_args__ = (
        db.UniqueConstraint('movie_list_id', 'user_id', name='uq_movie_list_like'),
    )


class MovieListComment(db.Model):
    """影单评论模型
    
    用户对影单的评论。
    """
    __tablename__ = "movie_list_comments"
    
    id = db.Column(db.Integer, primary_key=True)
    movie_list_id = db.Column(db.Integer, db.ForeignKey("movie_lists.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("movie_list_comments.id"))  # 父评论ID，用于回复
    
    # 统计
    like_count = db.Column(db.Integer, default=0)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    movie_list = db.relationship("MovieList", back_populates="comments")
    user = db.relationship("User", backref="movie_list_comments")
    parent = db.relationship("MovieListComment", remote_side=[id], backref="replies")
    
    def to_dict(self, include_replies: bool = False) -> dict:
        """转换为字典格式"""
        result = {
            'id': self.id,
            'movie_list_id': self.movie_list_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'content': self.content,
            'parent_id': self.parent_id,
            'like_count': self.like_count,
            'reply_count': len(self.replies),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }
        
        if include_replies:
            result['replies'] = [reply.to_dict() for reply in self.replies]
        
        return result
