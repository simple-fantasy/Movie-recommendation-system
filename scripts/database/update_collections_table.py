#!/usr/bin/env python3
"""
创建用户收藏表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def create_collections_table():
    """创建收藏表"""
    app = create_app()
    
    with app.app_context():
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS user_collections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                movie_id INT NOT NULL,
                collection_type VARCHAR(20) DEFAULT 'favorite',
                notes TEXT,
                rating FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_collections_user_id (user_id),
                INDEX idx_collections_movie_id (movie_id),
                UNIQUE KEY unique_collection (user_id, movie_id, collection_type),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 user_collections")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 user_collections 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        print("\n✓✓✓ 收藏表创建完成！")

if __name__ == "__main__":
    create_collections_table()
