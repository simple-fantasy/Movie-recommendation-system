#!/usr/bin/env python3
"""
更新users表结构，添加管理员权限字段
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from sqlalchemy import text

def update_users_table():
    """添加新列到users表"""
    app = create_app()
    
    with app.app_context():
        # 添加新列的SQL语句
        columns_to_add = [
            ("is_admin", "BOOLEAN DEFAULT FALSE"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("last_login", "DATETIME"),
            ("login_count", "INT DEFAULT 0"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                db.session.execute(text(sql))
                db.session.commit()
                print(f"✓ 添加列 {column_name}")
            except Exception as e:
                # 如果列已存在，会报错，忽略错误
                if "Duplicate" in str(e) or "already exists" in str(e) or "1060" in str(e):
                    print(f"  列 {column_name} 已存在")
                else:
                    print(f"✗ 添加列 {column_name} 失败: {e}")
                    db.session.rollback()
        
        print("\n✓✓✓ users表更新完成！")

if __name__ == "__main__":
    update_users_table()
