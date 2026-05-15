#!/usr/bin/env python3
"""
初始化管理员账户
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import User


def create_admin_user(username='admin', password='admin123'):
    """创建默认管理员账户"""
    app = create_app()
    
    with app.app_context():
        # 检查是否已存在管理员
        admin = User.query.filter_by(username=username).first()
        if not admin:
            admin = User(
                username=username, 
                is_admin=True,
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"✓ 管理员账户创建成功！")
            print(f"  用户名: {username}")
            print(f"  密码: {password}")
            print(f"\n⚠️  请登录后立即修改默认密码！")
        else:
            # 如果用户存在但不是管理员，设置为管理员
            if not admin.is_admin:
                admin.is_admin = True
                db.session.commit()
                print(f"✓ 用户 {username} 已设置为管理员")
            else:
                print(f"  管理员账户 {username} 已存在")
        
        # 显示所有管理员
        admins = User.query.filter_by(is_admin=True).all()
        print(f"\n当前管理员列表 ({len(admins)}人):")
        for admin in admins:
            print(f"  - {admin.username} (创建时间: {admin.created_at.strftime('%Y-%m-%d')})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化管理员账户')
    parser.add_argument('--username', default='admin', help='管理员用户名')
    parser.add_argument('--password', default='admin123', help='管理员密码')
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.password)
