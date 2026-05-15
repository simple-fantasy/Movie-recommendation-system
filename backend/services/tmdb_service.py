"""
TMDB API服务类
用于获取电影详细信息（导演、演员、简介、海报等）
"""

import json
import time
from typing import Dict, List, Optional

import requests
from flask import current_app


class TMDBService:
    """TMDB API服务"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or current_app.config.get('TMDB_API_KEY')
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p"
        self.last_request_time = 0
        self.min_interval = 0.25  # API请求间隔（秒），避免速率限制
    
    def _make_request(self, url: str, params: Dict, retries: int = 3) -> Dict:
        """发起API请求，包含速率限制和重试机制"""
        # 速率限制
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=30)  # 增加超时时间到30秒
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    wait_time = 2 * (attempt + 1)
                    print(f"  触发速率限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  TMDB API请求失败: {response.status_code}")
                    if attempt < retries - 1:
                        time.sleep(1)
                        continue
                    return {}
                    
            except requests.exceptions.Timeout as e:
                print(f"  请求超时 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return {}
            except requests.exceptions.ConnectionError as e:
                print(f"  连接错误 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return {}
            except Exception as e:
                print(f"  TMDB API请求异常: {e}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return {}
        
        return {}
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Dict:
        """搜索电影"""
        url = f"{self.base_url}/search/movie"
        params = {
            'api_key': self.api_key,
            'query': title,
            'language': 'zh-CN'
        }
        if year:
            params['year'] = year
        
        return self._make_request(url, params)
    
    def get_movie_details(self, tmdb_id: int) -> Dict:
        """获取电影详细信息"""
        url = f"{self.base_url}/movie/{tmdb_id}"
        params = {
            'api_key': self.api_key,
            'language': 'zh-CN',
            'append_to_response': 'credits,images'
        }
        
        return self._make_request(url, params)
    
    def enrich_movie_data(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """丰富电影数据 - 主接口"""
        # 先搜索
        search_result = self.search_movie(title, year)
        if not search_result or not search_result.get('results'):
            return None
        
        # 找到最匹配的结果（通常是第一个）
        movie_info = search_result['results'][0]
        tmdb_id = movie_info.get('id')
        
        if not tmdb_id:
            return None
        
        # 获取详细信息
        details = self.get_movie_details(tmdb_id)
        if not details:
            return None
        
        # 构建返回数据
        return {
            'tmdb_id': tmdb_id,
            'imdb_id': details.get('imdb_id'),
            'title': details.get('title'),
            'original_title': details.get('original_title'),
            'overview': details.get('overview'),
            'release_date': details.get('release_date'),
            'runtime': details.get('runtime'),
            'genres': [g['name'] for g in details.get('genres', [])],
            'director': self._get_director(details.get('credits', {})),
            'actors': self._get_actors(details.get('credits', {})),
            'poster_url': self._get_image_url(details.get('poster_path'), 'w500'),
            'backdrop_url': self._get_image_url(details.get('backdrop_path'), 'w1280'),
            'trailer_url': None,  # 暂不支持预告片
            'language': details.get('original_language'),
            'country': self._get_countries(details.get('production_countries', [])),
            'vote_average': details.get('vote_average'),
            'vote_count': details.get('vote_count')
        }
    
    def _get_director(self, credits: Dict) -> Optional[str]:
        """获取导演信息"""
        crew = credits.get('crew', [])
        for person in crew:
            if person.get('job') == 'Director':
                return person.get('name')
        return None
    
    def _get_actors(self, credits: Dict, limit: int = 5) -> List[str]:
        """获取演员信息"""
        cast = credits.get('cast', [])
        return [actor.get('name') for actor in cast[:limit] if actor.get('name')]
    
    def _get_image_url(self, image_path: Optional[str], size: str = 'w500') -> Optional[str]:
        """获取图片完整URL"""
        if not image_path:
            return None
        return f"{self.image_base_url}/{size}{image_path}"
    
    def _get_countries(self, countries: List[Dict]) -> Optional[str]:
        """获取制片国家"""
        if not countries:
            return None
        return ', '.join([c.get('name', '') for c in countries[:3]])
