#!/usr/bin/env python3
"""
测试管理员后台系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

with app.test_client() as client:
    print("=" * 60)
    print("管理员后台系统测试")
    print("=" * 60)
    
    # 1. 测试管理员登录页面
    print("\n1. 测试管理员登录页面:")
    response = client.get('/admin/login')
    print(f"   GET /admin/login - 状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 登录页面可访问")
    
    # 2. 测试未登录访问管理员仪表板（应该重定向）
    print("\n2. 测试权限保护:")
    response = client.get('/admin/', follow_redirects=False)
    print(f"   GET /admin/ (未登录) - 状态码: {response.status_code}")
    if response.status_code == 302:
        print("   ✓ 未登录用户被正确重定向")
    
    # 3. 使用管理员账户登录
    print("\n3. 测试管理员登录:")
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    print(f"   POST /api/auth/login - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   登录用户: {data.get('username')}")
        print(f"   是否管理员: {data.get('is_admin')}")
        if data.get('is_admin'):
            print("   ✓ 管理员登录成功")
    
    # 4. 访问管理员仪表板
    print("\n4. 测试管理员仪表板:")
    response = client.get('/admin/')
    print(f"   GET /admin/ (已登录) - 状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 管理员仪表板可访问")
    
    # 5. 测试电影管理页面
    print("\n5. 测试电影管理页面:")
    response = client.get('/admin/movies')
    print(f"   GET /admin/movies - 状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 电影管理页面可访问")
    
    # 6. 测试用户管理页面
    print("\n6. 测试用户管理页面:")
    response = client.get('/admin/users')
    print(f"   GET /admin/users - 状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 用户管理页面可访问")
    
    # 7. 测试添加电影页面
    print("\n7. 测试添加电影页面:")
    response = client.get('/admin/movies/add')
    print(f"   GET /admin/movies/add - 状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 添加电影页面可访问")
    
    # 8. 测试管理员API
    print("\n8. 测试管理员API:")
    response = client.get('/api/admin/dashboard')
    print(f"   GET /api/admin/dashboard - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"   总用户数: {data.get('total_users')}")
        print(f"   电影数: {data.get('total_movies')}")
        print("   ✓ 管理员API正常工作")
    
    print("\n" + "=" * 60)
    print("✓ 管理员后台系统测试完成")
    print("=" * 60)
    print("\n管理员后台地址:")
    print("  登录页面: http://127.0.0.1:5000/admin/login")
    print("  仪表板: http://127.0.0.1:5000/admin/")
    print("  电影管理: http://127.0.0.1:5000/admin/movies")
    print("  用户管理: http://127.0.0.1:5000/admin/users")
