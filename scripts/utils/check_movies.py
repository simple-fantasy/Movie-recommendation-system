#!/usr/bin/env python3
"""
检查电影数据状态
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import Movie

app = create_app()

with app.app_context():
    total_movies = Movie.query.count()
    movies_with_director = Movie.query.filter(Movie.director.isnot(None)).count()
    movies_with_poster = Movie.query.filter(Movie.poster_url.isnot(None)).count()
    movies_with_description = Movie.query.filter(Movie.description.isnot(None)).count()
    
    print(f"电影数据统计:")
    print(f"  总计: {total_movies} 部")
    print(f"  有导演信息: {movies_with_director} 部 ({movies_with_director/total_movies*100:.1f}%)")
    print(f"  有海报: {movies_with_poster} 部 ({movies_with_poster/total_movies*100:.1f}%)")
    print(f"  有简介: {movies_with_description} 部 ({movies_with_description/total_movies*100:.1f}%)")
    
    print("\n前5部已更新电影示例:")
    updated_movies = Movie.query.filter(Movie.director.isnot(None)).limit(5).all()
    for movie in updated_movies:
        print(f"  - {movie.title} ({movie.year})")
        print(f"    导演: {movie.director}")
        print(f"    演员: {', '.join(movie.get_actors_list()[:3]) if movie.get_actors_list() else '无'}")
        print(f"    海报: {'有' if movie.poster_url else '无'}")
        print()
