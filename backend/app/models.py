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
    is_admin = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    security_question = db.Column(db.String(255), nullable=True)
    security_answer_hash = db.Column(db.String(256), nullable=True)

    ratings = db.relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")
    collections = db.relationship("UserCollection", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def set_security_answer(self, answer: str) -> None:
        self.security_answer_hash = generate_password_hash(answer.strip().lower())

    def check_security_answer(self, answer: str) -> bool:
        if not self.security_answer_hash:
            return False
        return check_password_hash(self.security_answer_hash, answer.strip().lower())

    def make_admin(self):
        """设置为管理员"""
        self.is_admin = True

    def revoke_admin(self):
        """撤销管理员权限"""
        self.is_admin = False

    def update_login_stats(self):
        """更新登录统计"""
        self.last_login = datetime.utcnow()
        self.login_count += 1

    def to_dict(self) -> dict:
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
    genres = db.Column(db.String(255), nullable=True, index=True)

    original_title = db.Column(db.String(255))
    director = db.Column(db.String(255), index=True)
    actors = db.Column(db.Text)
    description = db.Column(db.Text)
    runtime = db.Column(db.Integer)
    poster_url = db.Column(db.String(500))
    backdrop_url = db.Column(db.String(500))
    trailer_url = db.Column(db.String(500))
    tagline = db.Column(db.String(255))
    tmdb_id = db.Column(db.Integer)
    imdb_id = db.Column(db.String(20))
    language = db.Column(db.String(10))
    country = db.Column(db.String(100))

    status = db.Column(db.Enum('active', 'inactive', 'pending'), default='active', index=True)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    rating_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    ratings = db.relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    collections = db.relationship("UserCollection", back_populates="movie", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    watch_links = db.relationship("WatchLink", back_populates="movie", cascade="all, delete-orphan")
    submitter = db.relationship("User", foreign_keys=[submitted_by], backref="submitted_movies")

    def get_actors_list(self) -> list:
        if self.actors:
            try:
                return json.loads(self.actors)
            except:
                return []
        return []

    def set_actors_list(self, actors: list):
        self.actors = json.dumps(actors, ensure_ascii=False)

    def to_dict(self) -> dict:
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
        db.Index("idx_ratings_user_time", "user_id", "timestamp"),
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
        db.Index("idx_similarity_movie_score", "movie_id", "score"),
    )


class RecommendationFeedback(db.Model):
    __tablename__ = "recommendation_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    feedback = db.Column(db.String(16), nullable=False)
    context = db.Column(db.String(64), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id", "context", name="uq_feedback_user_movie_ctx"),)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float)
    likes_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('approved', 'rejected', 'pending'), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="reviews")
    movie = db.relationship("Movie", back_populates="reviews")
    likes = db.relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
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
    __tablename__ = "review_likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'review_id'),)

    user = db.relationship("User")
    review = db.relationship("Review", back_populates="likes")


class UserCollection(db.Model):
    __tablename__ = "user_collections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    collection_type = db.Column(db.String(20), default='favorite')
    notes = db.Column(db.Text)
    rating = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', 'collection_type'),)

    user = db.relationship("User", back_populates="collections")
    movie = db.relationship("Movie", back_populates="collections")

    def to_dict(self) -> dict:
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
    __tablename__ = "watch_links"

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.Text, nullable=False)
    quality = db.Column(db.String(20), default='HD')
    is_free = db.Column(db.Boolean, default=True)
    is_official = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('active', 'pending', 'inactive', 'reported'), default='pending')
    report_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movie = db.relationship("Movie", back_populates="watch_links")
    user = db.relationship("User")

    def to_dict(self) -> dict:
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


class UserBehavior(db.Model):
    __tablename__ = "user_behaviors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(20))
    target_id = db.Column(db.Integer)
    extra_data = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    session_id = db.Column(db.String(100))
    referrer = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

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


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)

    preferred_genres = db.Column(db.JSON)
    preferred_years = db.Column(db.JSON)
    preferred_actors = db.Column(db.JSON)
    preferred_directors = db.Column(db.JSON)

    avg_rating_level = db.Column(db.Float)
    rating_variance = db.Column(db.Float)
    rating_entropy = db.Column(db.Float)

    total_watch_time = db.Column(db.Integer, default=0)
    genre_diversity = db.Column(db.Float)
    decade_diversity = db.Column(db.Float)

    user_type = db.Column(db.String(20))
    activity_level = db.Column(db.String(20))

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref="profile")

    def to_dict(self) -> dict:
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
        if not self.preferred_genres:
            return []
        sorted_genres = sorted(self.preferred_genres.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres[:n]

    def get_favorite_decade(self) -> str:
        if not self.preferred_years:
            return None
        return max(self.preferred_years.items(), key=lambda x: x[1])[0]
