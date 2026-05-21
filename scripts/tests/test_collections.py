#!/usr/bin/env python3
"""
测试用户收藏系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

with app.test_client() as client:
    print("=" * 60)
    print("用户收藏系统测试")
    print("=" * 60)
    
    # 1. 登录
    print("\n1. 登录用户:")
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    if response.status_code == 200:
        print("   ✓ 登录成功")
    
    # 2. 添加收藏
    print("\n2. 测试添加收藏:")
    response = client.post('/api/collections', json={
        'movie_id': 2,
        'collection_type': 'favorite',
        'notes': '这部是我最喜欢的电影之一！'
    })
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 添加收藏成功")
        print(f"   收藏ID: {data['collection']['id']}")
    elif response.status_code == 400 and '已在收藏列表' in data.get('error', ''):
        print(f"   ✓ 电影已在收藏列表中")
    else:
        print(f"   ✗ 添加失败: {data.get('error')}")
    
    # 3. 添加到想看列表
    print("\n3. 测试添加到想看列表:")
    response = client.post('/api/collections', json={
        'movie_id': 3,
        'collection_type': 'watchlist',
        'notes': '想周末看这部电影'
    })
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 添加到想看列表成功")
    elif response.status_code == 400 and '已在收藏列表' in data.get('error', ''):
        print(f"   ✓ 电影已在想看列表中")
    else:
        print(f"   ✗ 添加失败: {data.get('error')}")
    
    # 4. 获取我的收藏
    print("\n4. 测试获取我的收藏:")
    response = client.get('/api/my/collections')
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取收藏成功")
        print(f"   总收藏: {data['stats']['total']}")
        print(f"   喜欢: {data['stats']['favorite']}")
        print(f"   想看: {data['stats']['watchlist']}")
        print(f"   已看: {data['stats']['seen']}")
    
    # 5. 获取收藏状态
    print("\n5. 测试获取电影收藏状态:")
    response = client.get('/api/movies/2/collection-status')
    data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取状态成功")
        print(f"   是否收藏: {data['is_favorite']}")
        print(f"   在想看列表: {data['in_watchlist']}")
        print(f"   是否看过: {data['is_seen']}")
    
    print("\n" + "=" * 60)
    print("✓ 收藏系统测试完成")
    print("=" * 60)
    print("\n收藏API端点:")
    print("  POST /api/collections                    - 添加收藏")
    print("  GET  /api/my/collections                 - 我的收藏列表")
    print("  DELETE /api/collections/<id>               - 取消收藏")
    print("  GET  /api/movies/<id>/collection-status    - 收藏状态")
    print("  POST /api/collections/<id>/notes           - 更新备注")
