#!/usr/bin/env python3
"""
测试观看链接系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

with app.test_client() as client:
    print("=" * 60)
    print("电影观看链接系统测试")
    print("=" * 60)
    
    # 1. 登录
    print("\n1. 登录用户:")
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    if response.status_code == 200:
        print("   ✓ 登录成功")
    
    # 2. 提交观看链接
    print("\n2. 测试提交观看链接:")
    response = client.post('/api/movies/1/watch-links', json={
        'platform': 'YouTube',
        'url': 'https://youtube.com/watch?v=demo123',
        'quality': 'HD',
        'is_free': True
    })
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 链接提交成功")
        print(f"   状态: {data['link']['status']}")
    elif response.status_code == 400 and '已存在' in data.get('error', ''):
        print(f"   ✓ 链接已存在")
    else:
        print(f"   ✗ 提交失败: {data.get('error')}")
    
    # 3. 获取观看链接
    print("\n3. 测试获取观看链接:")
    response = client.get('/api/movies/1/watch-links')
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取成功")
        print(f"   电影: {data['movie']['title']}")
        print(f"   可用链接: {len(data['links'])} 条")
    
    # 4. 访问管理页面
    print("\n4. 测试管理员页面:")
    response = client.get('/admin/watch-links')
    if response.status_code == 200:
        print("   ✓ 观看链接管理页面可访问")
    
    print("\n" + "=" * 60)
    print("✓ 观看链接系统测试完成")
    print("=" * 60)
    print("\nAPI端点:")
    print("  GET  /api/movies/<id>/watch-links      - 获取观看链接")
    print("  POST /api/movies/<id>/watch-links      - 提交链接")
    print("  POST /api/watch-links/<id>/report      - 举报链接")
    print("\n管理端点:")
    print("  GET  /admin/watch-links                - 管理页面")
    print("  POST /admin/watch-links/<id>/approve   - 通过链接")
    print("  POST /admin/watch-links/<id>/reject    - 拒绝链接")
