#!/usr/bin/env python3
"""
批量补充电影信息脚本
使用TMDB API为现有电影添加详细信息
"""
import os
import sys
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('FLASK_ENV', 'development')

# 导入Flask应用
from backend.app import create_app, db
from backend.app.models import Movie

# 创建应用实例
app = create_app()

# 导入服务（根据网络环境选择）
try:
    from backend.services.tmdb_service import TMDBService
    SERVICE_TYPE = 'tmdb'
except ImportError:
    SERVICE_TYPE = 'mock'
    TMDBService = None

# 也导入备选服务
from backend.services.douban_service import DoubanService, MockMovieService


def enrich_movies(limit: int = None, skip_existing: bool = True, use_mock: bool = False):
    """
    批量补充电影信息
    
    Args:
        limit: 限制处理的电影数量，None表示处理所有
        skip_existing: 是否跳过已有详细信息的电影
        use_mock: 是否使用模拟数据（用于演示）
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始补充电影信息...")
    
    with app.app_context():
        # 初始化电影信息服务
        if use_mock:
            print("使用模拟数据服务（演示模式）")
            movie_service = MockMovieService()
        else:
            api_key = app.config.get('TMDB_API_KEY')
            if not api_key:
                print("警告: 未配置TMDB_API_KEY，切换到模拟数据模式")
                movie_service = MockMovieService()
            else:
                try:
                    movie_service = TMDBService(api_key=api_key)
                    print("使用TMDB API服务")
                except Exception as e:
                    print(f"TMDB服务初始化失败: {e}，切换到模拟数据模式")
                    movie_service = MockMovieService()
        
        # 查询需要补充信息的电影
        query = Movie.query
        if skip_existing:
            query = query.filter(
                (Movie.director.is_(None)) | 
                (Movie.description.is_(None)) |
                (Movie.poster_url.is_(None))
            )
        
        if limit:
            query = query.limit(limit)
        
        movies = query.all()
        total = len(movies)
        
        print(f"找到 {total} 部需要补充信息的电影")
        
        if total == 0:
            print("没有需要补充信息的电影")
            return
        
        # 统计
        success_count = 0
        failed_count = 0
        failed_movies = []
        
        for index, movie in enumerate(movies, 1):
            print(f"\n[{index}/{total}] 正在处理: {movie.title} ({movie.year or '未知年份'})")
            
            try:
                # 调用电影信息服务获取详细信息
                enriched_data = movie_service.enrich_movie_data(movie.title, movie.year)
                
                if not enriched_data:
                    print(f"  ✗ 未找到匹配信息")
                    failed_count += 1
                    failed_movies.append({
                        'id': movie.id,
                        'title': movie.title,
                        'year': movie.year,
                        'reason': '未找到匹配信息'
                    })
                    continue
                
                # 更新电影信息
                movie.director = enriched_data.get('director')
                movie.description = enriched_data.get('overview')
                movie.poster_url = enriched_data.get('poster_url')
                movie.backdrop_url = enriched_data.get('backdrop_url')
                movie.runtime = enriched_data.get('runtime')
                movie.tmdb_id = enriched_data.get('tmdb_id')
                movie.imdb_id = enriched_data.get('imdb_id')
                movie.original_title = enriched_data.get('original_title')
                movie.language = enriched_data.get('language')
                movie.country = enriched_data.get('country')
                
                # 设置演员列表
                if enriched_data.get('actors'):
                    movie.set_actors_list(enriched_data['actors'])
                
                # 更新状态为活跃
                movie.status = 'active'
                
                db.session.commit()
                
                success_count += 1
                print(f"  ✓ 更新成功")
                print(f"    - 导演: {movie.director or '无'}")
                print(f"    - 演员: {', '.join(movie.get_actors_list()[:3]) if movie.get_actors_list() else '无'}")
                print(f"    - 海报: {'有' if movie.poster_url else '无'}")
                
            except Exception as e:
                print(f"  ✗ 处理失败: {str(e)}")
                failed_count += 1
                failed_movies.append({
                    'id': movie.id,
                    'title': movie.title,
                    'year': movie.year,
                    'reason': str(e)
                })
                db.session.rollback()
            
            # 添加延时避免API速率限制
            time.sleep(0.3)
        
        # 打印统计信息
        print(f"\n{'='*60}")
        print(f"处理完成！")
        print(f"总计: {total} 部电影")
        print(f"成功: {success_count} 部")
        print(f"失败: {failed_count} 部")
        print(f"成功率: {success_count/total*100:.1f}%")
        
        if failed_movies:
            print(f"\n失败的电影:")
            for movie in failed_movies:
                print(f"  - {movie['title']} ({movie['year']}): {movie['reason']}")


def update_single_movie(movie_id: int):
    """更新单个电影的信息"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 更新电影 ID={movie_id}")
    
    with app.app_context():
        movie = Movie.query.get(movie_id)
        if not movie:
            print(f"错误: 电影 ID={movie_id} 不存在")
            return
        
        print(f"电影: {movie.title} ({movie.year})")
        
        api_key = app.config.get('TMDB_API_KEY')
        tmdb = TMDBService(api_key=api_key)
        
        try:
            enriched_data = tmdb.enrich_movie_data(movie.title, movie.year)
            
            if not enriched_data:
                print("✗ 未找到匹配信息")
                return
            
            # 更新信息
            movie.director = enriched_data.get('director')
            movie.description = enriched_data.get('overview')
            movie.poster_url = enriched_data.get('poster_url')
            movie.backdrop_url = enriched_data.get('backdrop_url')
            movie.runtime = enriched_data.get('runtime')
            movie.tmdb_id = enriched_data.get('tmdb_id')
            movie.imdb_id = enriched_data.get('imdb_id')
            movie.original_title = enriched_data.get('original_title')
            movie.language = enriched_data.get('language')
            movie.country = enriched_data.get('country')
            
            if enriched_data.get('actors'):
                movie.set_actors_list(enriched_data['actors'])
            
            movie.status = 'active'
            
            db.session.commit()
            
            print("✓ 更新成功")
            external_id = movie.tmdb_id or movie.imdb_id or movie.douban_id if hasattr(movie, 'douban_id') else None
            print(f"  - 外部ID: {external_id or '无'}")
            print(f"  - 导演: {movie.director or '无'}")
            print(f"  - 演员: {', '.join(movie.get_actors_list()[:5]) if movie.get_actors_list() else '无'}")
            print(f"  - 海报: {movie.poster_url or '无'}")
            
        except Exception as e:
            print(f"✗ 更新失败: {str(e)}")
            db.session.rollback()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='补充电影信息')
    parser.add_argument('--limit', type=int, help='限制处理的电影数量')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='跳过已有详细信息的电影')
    parser.add_argument('--movie-id', type=int, help='指定单个电影ID进行更新')
    parser.add_argument('--use-mock', action='store_true', help='使用模拟数据（用于演示）')
    
    args = parser.parse_args()
    
    if args.movie_id:
        update_single_movie(args.movie_id, use_mock=args.use_mock)
    else:
        enrich_movies(limit=args.limit, skip_existing=args.skip_existing, use_mock=args.use_mock)
