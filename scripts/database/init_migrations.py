#!/usr/bin/env python3
"""
初始化Flask-Migrate迁移环境
"""
import os
import sys

# 设置项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('FLASK_APP', 'backend.run')
os.environ.setdefault('FLASK_ENV', 'development')

from flask_migrate import init, migrate, upgrade
from backend.app import create_app, db

def main():
    app = create_app()
    
    with app.app_context():
        # 检查migrations目录是否存在
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
        if not os.path.exists(migrations_dir):
            print("初始化Flask-Migrate...")
            init(directory='migrations')
            print("✓ 初始化完成")
        else:
            print("Migrations已存在")
        
        # 创建迁移脚本
        print("\n创建迁移脚本...")
        migrate(directory='migrations', message='add movie metadata fields')
        print("✓ 迁移脚本创建完成")
        
        # 执行数据库升级
        print("\n执行数据库升级...")
        upgrade(directory='migrations')
        print("✓ 数据库升级完成")
        
        print("\n✓✓✓ 数据库迁移完成！")

if __name__ == '__main__':
    main()
