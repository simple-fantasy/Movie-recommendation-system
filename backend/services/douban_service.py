"""
豆瓣电影API服务类（备选方案）
用于在国内网络环境下获取电影信息
"""

import json
import re
import time
from typing import Dict, List, Optional

import requests


class DoubanService:
    """豆瓣电影API服务"""
    
    def __init__(self):
        self.base_url = "https://movie.douban.com/j"
        self.search_url = "https://movie.douban.com/j/subject_suggest"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://movie.douban.com/'
        }
        self.last_request_time = 0
        self.min_interval = 0.5  # 请求间隔（秒）
    
    def _make_request(self, url: str, params: Dict = None, retries: int = 3) -> Dict:
        """发起API请求"""
        # 速率限制
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        for attempt in range(retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=self.headers,
                    timeout=30
                )
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"  豆瓣API请求失败: {response.status_code}")
                    if attempt < retries - 1:
                        time.sleep(1)
                        continue
                    return {}
                    
            except requests.exceptions.Timeout:
                print(f"  请求超时 (尝试 {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return {}
            except Exception as e:
                print(f"  请求异常: {e}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return {}
        
        return {}
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """搜索电影"""
        params = {'q': title}
        
        data = self._make_request(self.search_url, params)
        if not data:
            return None
        
        # 解析搜索结果
        results = data if isinstance(data, list) else []
        
        # 查找最匹配的结果
        for result in results:
            result_year = self._extract_year(result.get('year', ''))
            if year and result_year == year:
                return result
            elif not year:
                return result
        
        # 如果没有精确匹配，返回第一个结果
        return results[0] if results else None
    
    def _extract_year(self, year_str: str) -> Optional[int]:
        """从字符串中提取年份"""
        if not year_str:
            return None
        match = re.search(r'\d{4}', str(year_str))
        return int(match.group()) if match else None
    
    def enrich_movie_data(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """丰富电影数据 - 主接口"""
        # 搜索电影
        search_result = self.search_movie(title, year)
        if not search_result:
            return None
        
        # 获取详细信息
        movie_id = search_result.get('id')
        if not movie_id:
            return None
        
        # 构建返回数据
        return {
            'title': search_result.get('title'),
            'original_title': search_result.get('original_title'),
            'overview': None,  # 豆瓣搜索API不提供简介
            'release_date': f"{search_result.get('year', '')}-01-01" if search_result.get('year') else None,
            'runtime': None,  # 豆瓣搜索API不提供时长
            'genres': [],  # 豆瓣搜索API不提供类型
            'director': None,  # 豆瓣搜索API不提供导演
            'actors': [],  # 豆瓣搜索API不提供演员
            'poster_url': search_result.get('img'),
            'backdrop_url': None,
            'trailer_url': None,
            'language': None,
            'country': None,
            'vote_average': float(search_result.get('rating', 0)) if search_result.get('rating') else None,
            'vote_count': None,
            'douban_id': movie_id
        }


class MockMovieService:
    """
    模拟电影数据服务（用于演示）
    当网络API不可用时使用
    """
    
    def __init__(self):
        self.mock_data = {
            'Toy Story': {
                'director': '约翰·拉塞特',
                'actors': ['汤姆·汉克斯', '蒂姆·艾伦', '唐·里克斯'],
                'description': '牛仔警长胡迪和太空骑警巴斯光年从互不相让的冤家，变成生死与共的朋友。',
                'runtime': 81,
                'poster_url': 'https://via.placeholder.com/300x450?text=Toy+Story',
            },
            'Jumanji': {
                'director': '乔·庄斯顿',
                'actors': ['罗宾·威廉姆斯', '克尔斯滕·邓斯特', '大卫·艾兰·格里尔'],
                'description': '一个神秘的棋盘游戏，将两个小孩带入了一个充满危险的丛林世界。',
                'runtime': 104,
                'poster_url': 'https://via.placeholder.com/300x450?text=Jumanji',
            },
        }
    
    def enrich_movie_data(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """返回模拟数据"""
        # 尝试匹配已知电影
        for key, data in self.mock_data.items():
            if key.lower() in title.lower() or title.lower() in key.lower():
                return {
                    'title': title,
                    'original_title': title,
                    'overview': data['description'],
                    'release_date': f'{year}-01-01' if year else None,
                    'runtime': data['runtime'],
                    'genres': ['Animation', 'Adventure'],
                    'director': data['director'],
                    'actors': data['actors'],
                    'poster_url': data['poster_url'],
                    'backdrop_url': None,
                    'trailer_url': None,
                    'language': 'en',
                    'country': 'USA',
                    'vote_average': 4.0,
                    'vote_count': 1000,
                }
        
        # 返回通用模拟数据
        return {
            'title': title,
            'original_title': title,
            'overview': f'电影《{title}》的精彩故事',
            'release_date': f'{year}-01-01' if year else None,
            'runtime': 100,
            'genres': ['Drama'],
            'director': '未知导演',
            'actors': ['演员A', '演员B', '演员C'],
            'poster_url': f'https://via.placeholder.com/300x450?text={title.replace(" ", "+")}',
            'backdrop_url': None,
            'trailer_url': None,
            'language': 'en',
            'country': 'USA',
            'vote_average': 3.5,
            'vote_count': 500,
        }
