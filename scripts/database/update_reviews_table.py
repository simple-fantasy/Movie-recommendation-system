#!/usr/bin/env python3
"""
创建评论相关的数据库表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def create_reviews_tables():
    """创建评论相关的表"""
    app = create_app()
    
    with app.app_context():
        # 创建reviews表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                movie_id INT NOT NULL,
                content TEXT NOT NULL,
                rating FLOAT,
                likes_count INT DEFAULT 0,
                is_featured BOOLEAN DEFAULT FALSE,
                status ENUM('approved', 'rejected', 'pending') DEFAULT 'approved',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_reviews_user_id (user_id),
                INDEX idx_reviews_movie_id (movie_id),
                INDEX idx_reviews_status (status),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 reviews")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 reviews 已存在")
            else:
                print(f"✗ 创建表 reviews 失败: {e}")
                db.session.rollback()
        
        # 创建review_likes表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS review_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                review_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_review (user_id, review_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 review_likes")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 review_likes 已存在")
            else:
                print(f"✗ 创建表 review_likes 失败: {e}")
                db.session.rollback()
        
        print("\n✓✓✓ 评论表创建完成！")

if __name__ == "__main__":
    create_reviews_tables()
