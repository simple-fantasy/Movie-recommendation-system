#!/usr/bin/env python3
"""
初始化电影榜单数据
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import MovieChart, ChartItem, Movie
from sqlalchemy import func

def init_charts():
    """初始化榜单数据"""
    app = create_app()
    
    with app.app_context():
        # 1. 创建热门榜单
        hot_chart = MovieChart.query.filter_by(chart_type='hot').first()
        if not hot_chart:
            hot_chart = MovieChart(
                title='热门电影榜',
                description='本周最受欢迎的10部电影',
                chart_type='hot',
                sort_order=1
            )
            db.session.add(hot_chart)
            db.session.commit()
            print(f"✓ 创建热门榜单: {hot_chart.title}")
        
        # 2. 创建高分榜单
        top_chart = MovieChart.query.filter_by(chart_type='top_rated').first()
        if not top_chart:
            top_chart = MovieChart(
                title='高分电影榜',
                description='评分最高的经典电影',
                chart_type='top_rated',
                sort_order=2
            )
            db.session.add(top_chart)
            db.session.commit()
            print(f"✓ 创建高分榜单: {top_chart.title}")
        
        # 3. 创建编辑精选
        editor_chart = MovieChart.query.filter_by(chart_type='editor_pick').first()
        if not editor_chart:
            editor_chart = MovieChart(
                title='编辑精选',
                description='编辑精心挑选的优质电影',
                chart_type='editor_pick',
                sort_order=3
            )
            db.session.add(editor_chart)
            db.session.commit()
            print(f"✓ 创建编辑精选: {editor_chart.title}")
        
        # 4. 填充高分榜单
        top_movies = Movie.query.filter(
            Movie.avg_rating >= 4.0,
            Movie.rating_count >= 50
        ).order_by(Movie.avg_rating.desc()).limit(10).all()
        
        if top_movies and not top_chart.items:
            for i, movie in enumerate(top_movies, 1):
                item = ChartItem(
                    chart_id=top_chart.id,
                    movie_id=movie.id,
                    rank=i,
                    score=movie.avg_rating,
                    note=f"评分 {movie.avg_rating:.1f}，{movie.rating_count}人评价"
                )
                db.session.add(item)
            db.session.commit()
            print(f"✓ 填充高分榜单: {len(top_movies)} 部电影")
        
        # 5. 填充热门榜单（按评分人数排序）
        hot_movies = Movie.query.filter(
            Movie.rating_count >= 100
        ).order_by(Movie.rating_count.desc()).limit(10).all()
        
        if hot_movies and not hot_chart.items:
            for i, movie in enumerate(hot_movies, 1):
                item = ChartItem(
                    chart_id=hot_chart.id,
                    movie_id=movie.id,
                    rank=i,
                    score=movie.rating_count,
                    note=f"{movie.rating_count} 人评分"
                )
                db.session.add(item)
            db.session.commit()
            print(f"✓ 填充热门榜单: {len(hot_movies)} 部电影")
        
        print("\n✓✓✓ 榜单初始化完成！")

if __name__ == "__main__":
    init_charts()
