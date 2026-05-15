#!/usr/bin/env python3
"""
测试管理员权限系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import User

app = create_app()

with app.app_context():
    print("=" * 60)
    print("管理员权限系统测试")
    print("=" * 60)
    
    # 1. 检查管理员账户
    print("\n1. 管理员账户检查:")
    admins = User.query.filter_by(is_admin=True).all()
    print(f"   管理员数量: {len(admins)}")
    for admin in admins:
        print(f"   - {admin.username} (登录次数: {admin.login_count}, 最后登录: {admin.last_login or '从未'})")
    
    # 2. 检查普通用户
    print("\n2. 普通用户检查:")
    users = User.query.filter_by(is_admin=False).all()
    print(f"   普通用户数量: {len(users)}")
    
    # 3. 检查用户状态
    print("\n3. 用户状态统计:")
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    total_users = User.query.count()
    print(f"   总用户数: {total_users}")
    print(f"   活跃用户: {active_users}")
    print(f"   禁用用户: {inactive_users}")
    
    # 4. 测试User模型新方法
    print("\n4. 测试User模型方法:")
    if admins:
        admin = admins[0]
        user_dict = admin.to_dict()
        print(f"   管理员 {admin.username} 信息:")
        for key, value in user_dict.items():
            print(f"     {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✓ 管理员权限系统测试完成")
    print("=" * 60)
    print("\n管理员API端点:")
    print("  GET  /api/admin/dashboard     - 管理员仪表板")
    print("  GET  /api/admin/users          - 用户列表")
    print("  POST /api/admin/users/<id>/toggle-admin  - 切换管理员权限")
    print("  POST /api/admin/users/<id>/toggle-active - 启用/禁用用户")
    print("\n管理员登录信息:")
    print("  用户名: admin")
    print("  密码: admin123")
