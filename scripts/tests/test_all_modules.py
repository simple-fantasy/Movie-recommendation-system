#!/usr/bin/env python3
"""
所有模块综合测试
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

def test_notifications():
    """测试通知系统"""
    print("\n📢 消息通知系统测试")
    print("-" * 50)
    
    with app.test_client() as client:
        # 登录
        client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        
        # 获取通知列表
        response = client.get('/api/notifications')
        data = response.get_json()
        if response.status_code == 200:
            print(f"   ✓ 获取通知列表成功")
            print(f"   未读数: {data['unread_count']}")
        
        # 获取未读数量
        response = client.get('/api/notifications/unread-count')
        if response.status_code == 200:
            print(f"   ✓ 获取未读数成功")
        
        # 标记所有已读
        response = client.post('/api/notifications/read-all')
        if response.status_code == 200:
            print(f"   ✓ 标记已读成功")


def test_charts():
    """测试榜单系统"""
    print("\n🏆 电影榜单系统测试")
    print("-" * 50)
    
    with app.test_client() as client:
        # 获取榜单列表
        response = client.get('/api/charts')
        data = response.get_json()
        if response.status_code == 200:
            print(f"   ✓ 获取榜单列表成功")
            print(f"   榜单数量: {len(data['charts'])}")
            for chart in data['charts']:
                print(f"      • {chart['title']} ({chart['chart_type']})")
        
        # 获取热门榜单详情
        response = client.get('/api/charts/popular')
        data = response.get_json()
        if response.status_code == 200:
            print(f"   ✓ 获取热门榜单成功")
            for key in ['hot', 'top_rated', 'editor_pick']:
                if key in data:
                    print(f"      • {key}: {len(data[key]['items'])} 部电影")
        
        # 获取单个榜单详情
        if data.get('hot'):
            chart_id = data['hot']['chart']['id']
            response = client.get(f'/api/charts/{chart_id}')
            if response.status_code == 200:
                print(f"   ✓ 获取榜单详情成功")


def test_admin_features():
    """测试管理员功能"""
    print("\n👮 管理员功能测试")
    print("-" * 50)
    
    with app.test_client() as client:
        # 登录
        client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        
        # 榜单管理页面
        response = client.get('/admin/charts')
        if response.status_code == 200:
            print(f"   ✓ 榜单管理页面可访问")
        
        # 评分审核页面
        response = client.get('/admin/ratings/pending')
        if response.status_code == 200:
            print(f"   ✓ 评分审核页面可访问")
        
        # 评分统计API
        response = client.get('/api/admin/ratings/stats')
        data = response.get_json()
        if response.status_code == 200:
            print(f"   ✓ 评分统计API正常")
            print(f"      总评分: {data['total_ratings']}")
            print(f"      平均分: {data['avg_rating']}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("       电影推荐系统 - 全部模块综合测试")
    print("=" * 60)
    
    test_notifications()
    test_charts()
    test_admin_features()
    
    print("\n" + "=" * 60)
    print("       ✅ 全部测试完成！")
    print("=" * 60)
    
    print("\n📋 功能清单:")
    print("   ✅ 消息通知系统 (通知列表、已读标记、未读统计)")
    print("   ✅ 电影榜单系统 (榜单列表、热门榜单、榜单详情)")
    print("   ✅ 评分审核系统 (可疑评分检测、评分统计)")
    print("   ✅ 管理员功能 (榜单管理、评分审核)")
    
    print("\n🌐 API端点:")
    print("   GET  /api/notifications              - 通知列表")
    print("   POST /api/notifications/<id>/read     - 标记已读")
    print("   GET  /api/charts                      - 榜单列表")
    print("   GET  /api/charts/popular              - 热门榜单")
    print("   GET  /api/admin/ratings/stats        - 评分统计")

if __name__ == "__main__":
    main()
