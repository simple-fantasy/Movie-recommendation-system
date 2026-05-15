#!/usr/bin/env python3
"""
创建通知系统和榜单系统表
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def create_tables():
    """创建通知和榜单表"""
    app = create_app()
    
    with app.app_context():
        # 1. 通知表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('system', 'review_reply', 'review_liked', 'movie_recommend', 'achievement') DEFAULT 'system',
                title VARCHAR(200) NOT NULL,
                content TEXT,
                related_id INT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                INDEX idx_notifications_user_id (user_id),
                INDEX idx_notifications_is_read (is_read),
                INDEX idx_notifications_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 notifications")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 notifications 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        # 2. 通知偏好设置表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                enable_system BOOLEAN DEFAULT TRUE,
                enable_review BOOLEAN DEFAULT TRUE,
                enable_recommend BOOLEAN DEFAULT TRUE,
                enable_achievement BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 notification_preferences")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 notification_preferences 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        # 3. 电影榜单表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS movie_charts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                chart_type ENUM('hot', 'top_rated', 'editor_pick', 'genre', 'year') DEFAULT 'hot',
                genre VARCHAR(50),
                year INT,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_charts_type (chart_type),
                INDEX idx_charts_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 movie_charts")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 movie_charts 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        # 4. 榜单条目表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS chart_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chart_id INT NOT NULL,
                movie_id INT NOT NULL,
                rank INT NOT NULL,
                score FLOAT,
                note VARCHAR(200),
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_chart_items_chart_id (chart_id),
                INDEX idx_chart_items_rank (rank),
                FOREIGN KEY (chart_id) REFERENCES movie_charts(id) ON DELETE CASCADE,
                FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✓ 创建表 chart_items")
        except Exception as e:
            if "already exists" in str(e).lower() or "1050" in str(e):
                print("  表 chart_items 已存在")
            else:
                print(f"✗ 创建失败: {e}")
                db.session.rollback()
        
        print("\n✓✓✓ 通知系统和榜单系统表创建完成！")

if __name__ == "__main__":
    create_tables()
