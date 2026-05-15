#!/usr/bin/env python3
"""
测试评论系统
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

with app.test_client() as client:
    print("=" * 60)
    print("评论系统测试")
    print("=" * 60)
    
    # 1. 先登录管理员账户
    print("\n1. 登录管理员账户:")
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    login_data = response.get_json()
    if response.status_code == 200 and login_data.get('is_admin'):
        print("   ✓ 管理员登录成功")
    
    # 2. 测试发表评论
    print("\n2. 测试发表评论:")
    response = client.post('/api/reviews', json={
        'movie_id': 1,
        'content': '这是一部非常棒的电影！剧情精彩，演员表现出色。强烈推荐给大家！',
        'rating': 5.0
    })
    review_data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 评论发表成功 (ID: {review_data['review']['id']})")
    else:
        print(f"   ✗ 发表评论失败: {review_data.get('error')}")
    
    # 3. 测试获取电影评论
    print("\n3. 测试获取电影评论:")
    response = client.get('/api/movies/1/reviews')
    reviews_data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取评论成功 (共 {len(reviews_data['reviews'])} 条)")
        if reviews_data['reviews']:
            review = reviews_data['reviews'][0]
            print(f"   最新评论: {review['content'][:50]}...")
    
    # 4. 测试点赞评论
    print("\n4. 测试点赞评论:")
    response = client.post('/api/reviews/1/like')
    like_data = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 点赞操作成功 (已{'点赞' if like_data['liked'] else '取消点赞'})")
    
    # 5. 测试获取我的评论
    print("\n5. 测试获取我的评论:")
    response = client.get('/api/my/reviews')
    my_reviews = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取成功 (共 {len(my_reviews['reviews'])} 条评论)")
    
    # 6. 测试评论管理页面
    print("\n6. 测试管理员评论管理:")
    response = client.get('/admin/reviews')
    if response.status_code == 200:
        print("   ✓ 评论管理页面可访问")
    
    # 7. 获取评论统计
    print("\n7. 测试评论统计API:")
    response = client.get('/api/admin/reviews/stats')
    stats = response.get_json()
    if response.status_code == 200:
        print(f"   ✓ 获取统计成功")
        print(f"   总评论数: {stats['total_reviews']}")
        print(f"   已通过: {stats['approved_reviews']}")
        print(f"   总点赞数: {stats['total_likes']}")
    
    print("\n" + "=" * 60)
    print("✓ 评论系统测试完成")
    print("=" * 60)
    print("\n评论API端点:")
    print("  POST /api/reviews                    - 发表评论")
    print("  GET  /api/movies/<id>/reviews        - 获取电影评论")
    print("  POST /api/reviews/<id>/like          - 点赞/取消点赞")
    print("  GET  /api/my/reviews                 - 我的评论")
    print("  DELETE /api/reviews/<id>             - 删除评论")
    print("\n管理员端点:")
    print("  GET  /admin/reviews                  - 评论管理页面")
    print("  POST /admin/reviews/<id>/approve     - 通过评论")
    print("  POST /admin/reviews/<id>/reject      - 拒绝评论")
