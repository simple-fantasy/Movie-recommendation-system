#!/usr/bin/env python3
"""
手动更新数据库表结构，添加新列
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def add_columns():
    """添加新列到movies表"""
    app = create_app()
    
    with app.app_context():
        # 添加新列的SQL语句
        columns_to_add = [
            ("original_title", "VARCHAR(255)"),
            ("director", "VARCHAR(255)"),
            ("actors", "TEXT"),
            ("description", "TEXT"),
            ("runtime", "INT"),
            ("poster_url", "VARCHAR(500)"),
            ("backdrop_url", "VARCHAR(500)"),
            ("trailer_url", "VARCHAR(500)"),
            ("tmdb_id", "INT"),
            ("imdb_id", "VARCHAR(20)"),
            ("language", "VARCHAR(10)"),
            ("country", "VARCHAR(100)"),
            ("status", "ENUM('active', 'inactive', 'pending') DEFAULT 'active'"),
            ("is_featured", "BOOLEAN DEFAULT FALSE"),
            ("view_count", "INT DEFAULT 0"),
            ("rating_count", "INT DEFAULT 0"),
            ("avg_rating", "FLOAT DEFAULT 0.0"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                sql = f"ALTER TABLE movies ADD COLUMN {column_name} {column_type}"
                db.session.execute(text(sql))
                db.session.commit()
                print(f"✓ 添加列 {column_name}")
            except Exception as e:
                # 如果列已存在，会报错，忽略错误
                if "Duplicate" in str(e) or "already exists" in str(e):
                    print(f"  列 {column_name} 已存在")
                else:
                    print(f"✗ 添加列 {column_name} 失败: {e}")
                    db.session.rollback()
        
        print("\n✓✓✓ 数据库更新完成！")

if __name__ == "__main__":
    add_columns()
