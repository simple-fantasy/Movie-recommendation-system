#!/usr/bin/env python3
"""
简单的数据库迁移脚本 - 直接使用SQLAlchemy
"""
import os
import sys

# 设置项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('FLASK_ENV', 'development')

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade

# 手动创建应用和db实例
app = Flask(__name__)
app.config.from_object('backend.config.Config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 导入模型以确保它们在SQLAlchemy中注册
from backend.app.models import User, Movie, Rating, MovieSimilarity, RecommendationFeedback

def main():
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
        try:
            migrate(directory='migrations', message='add movie metadata fields')
            print("✓ 迁移脚本创建完成")
        except Exception as e:
            print(f"创建迁移脚本时出错: {e}")
            print("可能是没有检测到模型变化，继续执行升级...")
        
        # 执行数据库升级
        print("\n执行数据库升级...")
        try:
            upgrade(directory='migrations')
            print("✓ 数据库升级完成")
        except Exception as e:
            print(f"数据库升级时出错: {e}")
            print("尝试直接创建表...")
            db.create_all()
            print("✓ 直接创建表完成")
        
        print("\n✓✓✓ 数据库迁移完成！")

if __name__ == '__main__':
    main()
