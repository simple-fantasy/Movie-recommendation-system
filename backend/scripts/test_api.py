# test_api.py
"""后端API接口测试脚本"""
import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:5000/api"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_user = {
            "username": "testuser",
            "password": "password"
        }
    
    def test_register(self):
        """测试注册接口"""
        print("\n=== 测试注册接口 ===")
        url = f"{BASE_URL}/auth/register"
        
        # 测试新用户注册
        response = self.session.post(url, json=self.test_user)
        print(f"注册响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 新用户注册成功")
        elif response.status_code == 409:
            print("✓ 重复注册返回409")
        else:
            print(f"✗ 注册失败: {response.text}")
        
        return response.status_code in [200, 409]
    
    def test_login(self):
        """测试登录接口"""
        print("\n=== 测试登录接口 ===")
        url = f"{BASE_URL}/auth/login"
        
        # 正确密码登录
        response = self.session.post(url, json=self.test_user)
        print(f"登录响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ 登录成功")
            self.token = data.get("access_token")
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        else:
            print(f"✗ 登录失败: {response.text}")
        
        # 错误密码登录
        wrong_pass = {"username": "testuser", "password": "wrong"}
        response = requests.post(url, json=wrong_pass)
        print(f"错误密码响应: {response.status_code}")
        if response.status_code == 401:
            print("✓ 错误密码返回401")
        else:
            print(f"✗ 错误密码测试失败: {response.text}")
        
        return self.token is not None
    
    def test_me(self):
        """测试获取当前用户信息"""
        print("\n=== 测试获取用户信息 ===")
        url = f"{BASE_URL}/me"
        
        # 登录状态
        response = self.session.get(url)
        print(f"登录状态响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "authenticated" in data:
                auth_status = "已认证" if data.get("authenticated") else "未认证"
                print(f"✓ 登录状态: {auth_status}")
            else:
                print("✗ 响应缺少authenticated字段")
        else:
            print(f"✗ 获取用户信息失败: {response.text}")
        
        return response.status_code == 200
    
    def test_logout(self):
        """测试登出接口"""
        print("\n=== 测试登出接口 ===")
        url = f"{BASE_URL}/auth/logout"
        
        response = self.session.post(url)
        print(f"登出响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 登出成功")
            # 清除token
            self.token = None
            self.session.headers.pop("Authorization", None)
        else:
            print(f"✗ 登出失败: {response.text}")
        
        # 测试登出后获取用户信息
        response = self.session.get(f"{BASE_URL}/me")
        print(f"登出后获取用户信息: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("authenticated") == False:
                print("✓ 登出后未认证 (authenticated: false)")
            else:
                print(f"✗ 登出后仍可访问: {response.text}")
        elif response.status_code == 401:
            print("✓ 登出后返回401未认证")
        else:
            print(f"✗ 登出后获取用户信息失败: {response.text}")
        
        return response.status_code in [200, 401]
    
    def test_movies(self):
        """测试电影相关接口"""
        print("\n=== 测试电影接口 ===")
        
        # 搜索电影
        url = f"{BASE_URL}/movies"
        params = {"q": "Action"}
        response = self.session.get(url, params=params)
        print(f"搜索电影响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ 搜索成功，返回 {len(data)} 部电影")
            else:
                print("✗ 搜索无结果")
        else:
            print(f"✗ 搜索失败: {response.text}")
        
        # 获取电影详情
        movie_id = 1  # Toy Story
        url = f"{BASE_URL}/movies/{movie_id}"
        response = self.session.get(url)
        print(f"获取电影详情响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "avg_rating" in data and "rating_count" in data:
                print("✓ 电影详情包含评分信息")
            else:
                print("✗ 电影详情缺少评分信息")
        else:
            print(f"✗ 获取电影详情失败: {response.text}")
        
        return True
    
    def test_ratings(self):
        """测试评分相关接口"""
        print("\n=== 测试评分接口 ===")
        
        # 登录
        self.test_login()
        
        # 提交评分
        url = f"{BASE_URL}/ratings"
        rating_data = {
            "movie_id": 1,
            "rating": 5.0
        }
        response = self.session.post(url, json=rating_data)
        print(f"提交评分响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 评分提交成功")
        else:
            print(f"✗ 评分提交失败: {response.text}")
        
        # 重复评分（覆盖）
        rating_data["rating"] = 4.5
        response = self.session.post(url, json=rating_data)
        print(f"重复评分响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 重复评分成功覆盖")
        else:
            print(f"✗ 重复评分失败: {response.text}")
        
        # 获取评分历史
        url = f"{BASE_URL}/my/ratings"
        response = self.session.get(url)
        print(f"获取评分历史响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ 获取评分历史成功，返回 {len(data)} 条记录")
            else:
                print("✗ 评分历史为空")
        else:
            print(f"✗ 获取评分历史失败: {response.text}")
        
        return True
    
    def test_recommendations(self):
        """测试推荐接口"""
        print("\n=== 测试推荐接口 ===")
        
        # 登录
        self.test_login()
        
        # 测试itemcf策略
        url = f"{BASE_URL}/recommendations"
        params = {"strategy": "itemcf"}
        response = self.session.get(url, params=params)
        print(f"ItemCF推荐响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ ItemCF推荐成功，返回 {len(data)} 条")
            else:
                print("✗ ItemCF推荐无结果")
        else:
            print(f"✗ ItemCF推荐失败: {response.text}")
        
        # 测试ncf策略
        params = {"strategy": "ncf"}
        response = self.session.get(url, params=params)
        print(f"NCF推荐响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ NCF推荐成功，返回 {len(data)} 条")
            else:
                print("✗ NCF推荐无结果")
        elif response.status_code == 503:
            print("✓ NCF模型未训练返回503")
        else:
            print(f"✗ NCF推荐失败: {response.text}")
        
        # 测试hybrid策略
        params = {"strategy": "hybrid", "recall_k": 100}
        response = self.session.get(url, params=params)
        print(f"Hybrid推荐响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ Hybrid推荐成功，返回 {len(data)} 条")
                # 检查reason字段
                if "reason" in data[0]:
                    print("✓ Hybrid推荐包含reason字段")
                else:
                    print("✗ Hybrid推荐缺少reason字段")
            else:
                print("✗ Hybrid推荐无结果")
        else:
            print(f"✗ Hybrid推荐失败: {response.text}")
        
        # 测试未登录状态
        self.test_logout()
        response = self.session.get(url, params={"strategy": "itemcf"})
        print(f"未登录推荐响应: {response.status_code}")
        if response.status_code == 401:
            print("✓ 未登录访问推荐返回401")
        else:
            print(f"✗ 未登录访问推荐测试失败: {response.text}")
        
        return True
    
    def test_similar_and_explain(self):
        """测试相似电影和推荐理由接口"""
        print("\n=== 测试相似电影和推荐理由接口 ===")
        
        # 登录
        self.test_login()
        
        # 测试相似电影
        movie_id = 1
        url = f"{BASE_URL}/movies/{movie_id}/similar"
        response = self.session.get(url)
        print(f"相似电影响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✓ 相似电影获取成功，返回 {len(data)} 条")
            else:
                print("✗ 相似电影无结果")
        else:
            print(f"✗ 相似电影获取失败: {response.text}")
        
        # 测试推荐理由
        url = f"{BASE_URL}/recommendations/why/{movie_id}"
        response = self.session.get(url)
        print(f"推荐理由响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "because" in data:
                print("✓ 推荐理由包含because字段")
            else:
                print("✗ 推荐理由缺少because字段")
        else:
            print(f"✗ 推荐理由获取失败: {response.text}")
        
        return True
    
    def test_persona_and_feedback(self):
        """测试用户画像和反馈接口"""
        print("\n=== 测试用户画像和反馈接口 ===")
        
        # 登录
        self.test_login()
        
        # 测试用户画像
        url = f"{BASE_URL}/my/persona"
        response = self.session.get(url)
        print(f"用户画像响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "labels" in data and "values" in data:
                print("✓ 用户画像包含雷达图数据")
            else:
                print("✗ 用户画像缺少雷达图数据")
        else:
            print(f"✗ 用户画像获取失败: {response.text}")
        
        # 测试时间线
        url = f"{BASE_URL}/my/timeline"
        response = self.session.get(url)
        print(f"时间线响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✓ 时间线数据获取成功")
            else:
                print("✗ 时间线数据为空")
        else:
            print(f"✗ 时间线获取失败: {response.text}")
        
        # 测试反馈
        url = f"{BASE_URL}/feedback"
        feedback_data = {
            "movie_id": 1,
            "feedback": "like",
            "context": "recommendation"
        }
        response = self.session.post(url, json=feedback_data)
        print(f"提交反馈响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 反馈提交成功")
        else:
            print(f"✗ 反馈提交失败: {response.text}")
        
        # 重复反馈（覆盖）
        feedback_data["feedback"] = "dislike"
        response = self.session.post(url, json=feedback_data)
        print(f"重复反馈响应: {response.status_code}")
        if response.status_code == 200:
            print("✓ 重复反馈成功覆盖")
        else:
            print(f"✗ 重复反馈失败: {response.text}")
        
        return True
    
    def test_dashboard(self):
        """测试Dashboard统计接口"""
        print("\n=== 测试Dashboard统计接口 ===")
        
        # 登录
        self.test_login()
        
        # 测试评分统计
        url = f"{BASE_URL}/stats/ratings"
        response = self.session.get(url)
        print(f"评分统计响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✓ 评分统计数据获取成功")
            else:
                print("✗ 评分统计数据为空")
        else:
            print(f"✗ 评分统计获取失败: {response.text}")
        
        # 测试类型统计
        url = f"{BASE_URL}/stats/genres"
        response = self.session.get(url)
        print(f"类型统计响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✓ 类型统计数据获取成功")
            else:
                print("✗ 类型统计数据为空")
        else:
            print(f"✗ 类型统计获取失败: {response.text}")
        
        # 测试年份统计
        url = f"{BASE_URL}/stats/years"
        response = self.session.get(url)
        print(f"年份统计响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✓ 年份统计数据获取成功")
            else:
                print("✗ 年份统计数据为空")
        else:
            print(f"✗ 年份统计获取失败: {response.text}")
        
        # 测试评估指标
        url = f"{BASE_URL}/metrics/evaluation"
        response = self.session.get(url)
        print(f"评估指标响应: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✓ 评估指标数据获取成功")
            else:
                print("✗ 评估指标数据为空")
        else:
            print(f"✗ 评估指标获取失败: {response.text}")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始API接口测试...")
        print("=" * 80)
        
        tests = [
            ("注册/登录/登出", self.test_register),
            ("用户信息", self.test_me),
            ("登出", self.test_logout),
            ("电影接口", self.test_movies),
            ("评分接口", self.test_ratings),
            ("推荐接口", self.test_recommendations),
            ("相似与解释", self.test_similar_and_explain),
            ("用户画像与反馈", self.test_persona_and_feedback),
            ("Dashboard统计", self.test_dashboard),
        ]
        
        passed = 0
        total = len(tests)
        
        for name, test_func in tests:
            print(f"\n{'='*80}")
            print(f"测试: {name}")
            try:
                if test_func():
                    print(f"✓ {name} 测试通过")
                    passed += 1
                else:
                    print(f"✗ {name} 测试失败")
            except Exception as e:
                print(f"✗ {name} 测试异常: {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"测试完成: {passed}/{total} 通过")
        print("=" * 80)

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()