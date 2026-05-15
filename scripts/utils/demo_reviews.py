#!/usr/bin/env python3
"""
演示评论系统 - 创建示例评论数据
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import Review, User, Movie

app = create_app()

def create_demo_reviews():
    """创建示例评论数据"""
    with app.app_context():
        # 获取管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("管理员用户不存在")
            return
        
        # 获取一些电影
        movies = Movie.query.limit(5).all()
        if not movies:
            print("没有电影数据")
            return
        
        sample_reviews = [
            {"content": "这部电影真的太棒了！剧情紧凑，演员演技在线，强烈推荐！", "rating": 5.0},
            {"content": "整体还可以，但是节奏有点慢，中间部分有点拖沓。", "rating": 3.5},
            {"content": "经典之作，百看不厌，每次看都有新的感受。", "rating": 5.0},
            {"content": "特效做得不错，但是剧情有点老套，缺乏新意。", "rating": 3.0},
            {"content": "非常感人，看得我热泪盈眶，值得二刷！", "rating": 4.5},
        ]
        
        created_count = 0
        for i, movie in enumerate(movies):
            # 检查是否已有评论
            existing = Review.query.filter_by(
                user_id=admin.id,
                movie_id=movie.id
            ).first()
            
            if existing:
                print(f"电影《{movie.title}》已有评论，跳过")
                continue
            
            review_data = sample_reviews[i % len(sample_reviews)]
            
            review = Review(
                user_id=admin.id,
                movie_id=movie.id,
                content=review_data['content'],
                rating=review_data['rating'],
                status='approved'
            )
            
            db.session.add(review)
            created_count += 1
            print(f"✓ 为《{movie.title}》添加评论")
        
        db.session.commit()
        print(f"\n✓ 成功创建 {created_count} 条评论")
        
        # 显示统计
        total = Review.query.count()
        approved = Review.query.filter_by(status='approved').count()
        print(f"\n评论统计:")
        print(f"  总评论数: {total}")
        print(f"  已通过: {approved}")

if __name__ == "__main__":
    create_demo_reviews()
