"""
电影数据服务 - 模拟数据回退
当 TMDB API 不可用时提供基础的 mock 数据
"""

from typing import Dict, Optional


class MockMovieService:
    """
    模拟电影数据服务（用于演示 / API 回退）
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
