#!/usr/bin/env python3
"""
创建观看链接表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def create_watchlinks_table():
    """创建观看链接表"""
    app = create_app()
    
    with app.app_context():
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS watch_links (
                id INT AUTO_INCREMENT PRIMARY KEY,
                movie_id INT NOT NULL,
                user_id INT,
                platform VARCHAR(50) NOT NULL,
                url TEXT NOT NULL,
                quality VARCHAR(20) DEFAULT 'HD',
                is_free BOOLEAN DEFAULT TRUE,
                is_official BOOLEAN DEFAULT FALSE,
                status ENUM('active', 'pending', 'inactive', 'reported') DEFAULT 'pending',
                report_count INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_watchlinks_movie_id (movie_id),
                INDEX idx_watchlinks_status (status),
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 watch_links")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 watch_links 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        print("\n✓✓✓ 观看链接表创建完成！")

if __name__ == "__main__":
    create_watchlinks_table()
