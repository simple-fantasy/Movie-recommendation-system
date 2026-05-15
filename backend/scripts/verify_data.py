# verify_data.py
"""数据验证脚本 - 验证MovieLens数据集导入结果"""
from backend.app import create_app, db

def main():
    app = create_app()
    with app.app_context():
        from backend.app.models import Movie, Rating, User, MovieSimilarity
        
        print("=" * 60)
        print("数据导入验证报告")
        print("=" * 60)
        
        movie_count = Movie.query.count()
        rating_count = Rating.query.count()
        user_count = User.query.count()
        
        print(f"\n📊 数据统计：")
        print(f"  电影数量 (movies): {movie_count}")
        print(f"  评分数量 (ratings): {rating_count}")
        print(f"  用户数量 (users): {user_count}")
        
        # 额外统计
        if rating_count > 0:
            from sqlalchemy import func
            avg_rating = db.session.query(func.avg(Rating.rating)).scalar()
            min_rating = db.session.query(func.min(Rating.rating)).scalar()
            max_rating = db.session.query(func.max(Rating.rating)).scalar()
            print(f"\n📈 评分统计：")
            print(f"  评分范围: {min_rating:.1f} ~ {max_rating:.1f}")
            print(f"  平均评分: {avg_rating:.2f}")
        
        # 检查相似度表
        similarity_count = MovieSimilarity.query.count()
        print(f"\n📋 相似度表状态：")
        print(f"  相似度记录数: {similarity_count}")
        if similarity_count > 0:
            min_sim = db.session.query(func.min(MovieSimilarity.score)).scalar()
            max_sim = db.session.query(func.max(MovieSimilarity.score)).scalar()
            avg_sim = db.session.query(func.avg(MovieSimilarity.score)).scalar()
            print(f"  相似度范围: {min_sim:.4f} ~ {max_sim:.4f}")
            print(f"  平均相似度: {avg_sim:.4f}")
        
        print("\n" + "=" * 60)
        
        # 返回验证结果（只要有数据就返回成功）
        return movie_count > 0 and rating_count > 0 and user_count > 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)