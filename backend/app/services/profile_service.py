"""
用户画像计算服务
根据用户的评分、收藏、评论等行为数据，计算用户的各种画像特征
"""
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from sqlalchemy.orm import selectinload

from backend.app import db
from backend.app.models import Rating, UserCollection, Review, Movie, UserProfile


class ProfileService:
    """用户画像计算服务"""
    
    @staticmethod
    def compute_user_profile(user_id: int) -> UserProfile:
        """
        计算用户画像
        
        Args:
            user_id: 用户ID
        
        Returns:
            UserProfile对象
        """
        # 获取用户的所有评分（预加载movie避免N+1）
        ratings = Rating.query.filter_by(user_id=user_id)\
            .options(selectinload(Rating.movie)).all()

        # 获取用户的收藏（预加载movie避免N+1）
        collections = UserCollection.query.filter_by(user_id=user_id)\
            .options(selectinload(UserCollection.movie)).all()
        
        # 获取用户的评论
        reviews = Review.query.filter_by(user_id=user_id).all()
        
        # 计算各种画像特征
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
        
        # 计算偏好类型
        profile.preferred_genres = ProfileService._compute_genre_preferences(ratings, collections)
        
        # 计算偏好年代
        profile.preferred_years = ProfileService._compute_year_preferences(ratings, collections)
        
        # 计算偏好演员
        profile.preferred_actors = ProfileService._compute_actor_preferences(ratings, collections)
        
        # 计算偏好导演
        profile.preferred_directors = ProfileService._compute_director_preferences(ratings, collections)
        
        # 计算评分行为画像
        profile.avg_rating_level = ProfileService._compute_avg_rating(ratings)
        profile.rating_variance = ProfileService._compute_rating_variance(ratings)
        profile.rating_entropy = ProfileService._compute_rating_entropy(ratings)
        
        # 计算观影统计
        profile.total_watch_time = ProfileService._compute_watch_time(ratings, collections)
        profile.genre_diversity = ProfileService._compute_genre_diversity(profile.preferred_genres)
        profile.decade_diversity = ProfileService._compute_decade_diversity(profile.preferred_years)
        
        # 计算用户分层
        profile.user_type = ProfileService._compute_user_type(ratings, collections, reviews)
        profile.activity_level = ProfileService._compute_activity_level(ratings, collections, reviews)
        
        # 保存或更新
        if profile.id:
            db.session.merge(profile)
        else:
            db.session.add(profile)
        db.session.commit()
        
        return profile
    
    @staticmethod
    def _compute_genre_preferences(ratings: List[Rating], collections: List[UserCollection]) -> Dict[str, float]:
        """计算类型偏好"""
        genre_scores = defaultdict(float)
        
        # 从评分中计算
        for rating in ratings:
            if rating.movie and rating.movie.genres:
                for genre in rating.movie.genres.split('|'):
                    genre = genre.strip()
                    if genre and genre != '(no genres listed)':
                        genre_scores[genre] += float(rating.rating)
        
        # 从收藏中计算（收藏视为5分）
        for collection in collections:
            if collection.movie and collection.movie.genres:
                for genre in collection.movie.genres.split('|'):
                    genre = genre.strip()
                    if genre and genre != '(no genres listed)':
                        genre_scores[genre] += 5.0
        
        # 归一化
        if not genre_scores:
            return {}
        
        max_score = max(genre_scores.values())
        normalized = {k: round(v / max_score, 3) for k, v in genre_scores.items()}
        
        # 只保留分数大于0.3的类型
        filtered = {k: v for k, v in normalized.items() if v > 0.3}
        
        return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def _compute_year_preferences(ratings: List[Rating], collections: List[UserCollection]) -> Dict[str, str]:
        """计算年代偏好"""
        decade_scores = defaultdict(float)
        
        # 从评分中计算
        for rating in ratings:
            if rating.movie and rating.movie.year:
                decade = ProfileService._get_decade(rating.movie.year)
                decade_scores[decade] += float(rating.rating)
        
        # 从收藏中计算
        for collection in collections:
            if collection.movie and collection.movie.year:
                decade = ProfileService._get_decade(collection.movie.year)
                decade_scores[decade] += 5.0
        
        # 归一化
        if not decade_scores:
            return {}
        
        max_score = max(decade_scores.values())
        normalized = {k: round(v / max_score, 3) for k, v in decade_scores.items()}
        
        # 只保留分数大于0.3的年代
        filtered = {k: v for k, v in normalized.items() if v > 0.3}
        
        return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def _get_decade(year: int) -> str:
        """获取年代"""
        decade = (year // 10) * 10
        return f"{decade}s"
    
    @staticmethod
    def _compute_actor_preferences(ratings: List[Rating], collections: List[UserCollection]) -> List[str]:
        """计算演员偏好"""
        actor_scores = defaultdict(float)
        
        # 从评分中计算
        for rating in ratings:
            if rating.movie:
                actors = rating.movie.get_actors_list()
                for actor in actors:
                    actor_scores[actor] += float(rating.rating)
        
        # 从收藏中计算
        for collection in collections:
            if collection.movie:
                actors = collection.movie.get_actors_list()
                for actor in actors:
                    actor_scores[actor] += 5.0
        
        # 排序并返回前10个
        sorted_actors = sorted(actor_scores.items(), key=lambda x: x[1], reverse=True)
        return [actor for actor, _ in sorted_actors[:10]]
    
    @staticmethod
    def _compute_director_preferences(ratings: List[Rating], collections: List[UserCollection]) -> List[str]:
        """计算导演偏好"""
        director_scores = defaultdict(float)
        
        # 从评分中计算
        for rating in ratings:
            if rating.movie and rating.movie.director:
                director_scores[rating.movie.director] += float(rating.rating)
        
        # 从收藏中计算
        for collection in collections:
            if collection.movie and collection.movie.director:
                director_scores[collection.movie.director] += 5.0
        
        # 排序并返回前10个
        sorted_directors = sorted(director_scores.items(), key=lambda x: x[1], reverse=True)
        return [director for director, _ in sorted_directors[:10]]
    
    @staticmethod
    def _compute_avg_rating(ratings: List[Rating]) -> float:
        """计算平均评分水平"""
        if not ratings:
            return 0.0
        return round(sum(r.rating for r in ratings) / len(ratings), 2)
    
    @staticmethod
    def _compute_rating_variance(ratings: List[Rating]) -> float:
        """计算评分方差（苛刻程度）"""
        if not ratings:
            return 0.0
        
        avg = ProfileService._compute_avg_rating(ratings)
        variance = sum((r.rating - avg) ** 2 for r in ratings) / len(ratings)
        return round(variance, 3)
    
    @staticmethod
    def _compute_rating_entropy(ratings: List[Rating]) -> float:
        """计算评分熵（分散度）"""
        if not ratings:
            return 0.0
        
        # 统计各评分的数量
        rating_counts = Counter(round(r.rating, 1) for r in ratings)
        total = len(ratings)
        
        # 计算熵
        entropy = 0.0
        for count in rating_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return round(entropy, 3)
    
    @staticmethod
    def _compute_watch_time(ratings: List[Rating], collections: List[UserCollection]) -> int:
        """计算累计观影时长（分钟）"""
        total_time = 0
        
        # 从评分中计算
        for rating in ratings:
            if rating.movie and rating.movie.runtime:
                total_time += rating.movie.runtime
        
        # 从收藏中计算
        for collection in collections:
            if collection.movie and collection.movie.runtime:
                total_time += collection.movie.runtime
        
        return total_time
    
    @staticmethod
    def _compute_genre_diversity(genre_preferences: Dict[str, float]) -> float:
        """计算类型多样性指数（使用香农熵）"""
        if not genre_preferences:
            return 0.0
        
        total = sum(genre_preferences.values())
        entropy = 0.0
        
        for score in genre_preferences.values():
            p = score / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return round(entropy, 3)
    
    @staticmethod
    def _compute_decade_diversity(decade_preferences: Dict[str, float]) -> float:
        """计算年代多样性指数"""
        if not decade_preferences:
            return 0.0
        
        total = sum(decade_preferences.values())
        entropy = 0.0
        
        for score in decade_preferences.values():
            p = score / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return round(entropy, 3)
    
    @staticmethod
    def _compute_user_type(ratings: List[Rating], collections: List[UserCollection], reviews: List[Review]) -> str:
        """计算用户类型"""
        total_actions = len(ratings) + len(collections) + len(reviews)
        
        if total_actions < 10:
            return "casual"
        elif total_actions < 50:
            return "regular"
        else:
            return "enthusiast"
    
    @staticmethod
    def _compute_activity_level(ratings: List[Rating], collections: List[UserCollection], reviews: List[Review]) -> str:
        """计算活跃度"""
        total_actions = len(ratings) + len(collections) + len(reviews)
        
        if total_actions < 20:
            return "low"
        elif total_actions < 100:
            return "medium"
        else:
            return "high"
    
    @staticmethod
    def get_user_insights(user_id: int) -> List[Dict[str, str]]:
        """
        获取用户观影洞察
        
        Args:
            user_id: 用户ID
        
        Returns:
            洞察列表
        """
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return []
        
        insights = []
        
        # 类型偏好洞察
        if profile.preferred_genres:
            top_genre = max(profile.preferred_genres.items(), key=lambda x: x[1])
            insights.append({
                'type': 'genre',
                'title': f'您最喜欢{top_genre[0]}类型的电影',
                'description': f'在您的观影记录中，{top_genre[0]}类型的电影占比最高',
                'icon': '🎬'
            })
        
        # 年代偏好洞察
        if profile.preferred_years:
            favorite_decade = max(profile.preferred_years.items(), key=lambda x: x[1])
            insights.append({
                'type': 'decade',
                'title': f'您偏爱{favorite_decade[0]}的电影',
                'description': f'{favorite_decade[0]}的电影在您的观影记录中占比最高',
                'icon': '📅'
            })
        
        # 评分行为洞察
        if profile.avg_rating_level:
            if profile.avg_rating_level >= 4.0:
                rating_desc = "比较宽容"
            elif profile.avg_rating_level >= 3.0:
                rating_desc = "比较客观"
            else:
                rating_desc = "比较苛刻"
            insights.append({
                'type': 'rating',
                'title': f'您的评分风格{rating_desc}',
                'description': f'平均评分为{profile.avg_rating_level}分',
                'icon': '⭐'
            })
        
        # 多样性洞察
        if profile.genre_diversity:
            if profile.genre_diversity > 2.0:
                diversity_desc = "非常丰富"
            elif profile.genre_diversity > 1.5:
                diversity_desc = "比较丰富"
            else:
                diversity_desc = "比较专注"
            insights.append({
                'type': 'diversity',
                'title': f'您的观影类型{diversity_desc}',
                'description': f'类型多样性指数为{profile.genre_diversity}',
                'icon': '🎭'
            })
        
        # 活跃度洞察
        if profile.activity_level:
            activity_map = {
                'low': '刚开始探索',
                'medium': '经常观看',
                'high': '非常活跃'
            }
            insights.append({
                'type': 'activity',
                'title': f'您{activity_map.get(profile.activity_level, "")}',
                'description': f'活跃度等级：{profile.activity_level}',
                'icon': '📊'
            })
        
        return insights
