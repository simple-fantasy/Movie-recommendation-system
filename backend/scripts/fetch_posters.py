"""
基于 tmdbId 批量抓取电影海报 URL

适用场景：Movies 表已有 tmdb_id（从 links.csv 导入），直接用 ID 获取海报。
优势：不需要标题搜索，命中率 100%，速度快。

用法：
  python backend/scripts/fetch_posters.py --limit 500          # 抓取前500部
  python backend/scripts/fetch_posters.py --limit 5000 --wait 0.3  # 自定义间隔
  python backend/scripts/fetch_posters.py --all                 # 抓取所有缺海报的电影
"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from backend.app.models import Movie
from backend.services.tmdb_service import TMDBService


def fetch_posters(limit: int | None = None, wait: float = 0.25, poster_only: bool = True):
    app = create_app()
    with app.app_context():
        api_key = app.config.get("TMDB_API_KEY")
        if not api_key:
            print("错误: 未配置 TMDB_API_KEY")
            return

        tmdb = TMDBService(api_key=api_key)

        # 查询需要海报的电影，优先热门
        query = Movie.query.filter(
            Movie.tmdb_id.isnot(None),
            db.or_(
                Movie.poster_url.is_(None),
                Movie.poster_url == "",
                Movie.poster_url.contains("placeholder"),
            ),
        ).order_by(Movie.rating_count.desc())

        total = query.count()
        print(f"缺少海报的电影: {total} 部")

        if limit:
            query = query.limit(limit)

        movies = query.all()
        count = len(movies)
        print(f"本次处理: {count} 部 (间隔 {wait}s, 预计 {_fmt_time(count * wait)})")

        success = 0
        failed = 0
        start_time = time.time()

        for i, movie in enumerate(movies):
            _progress(i + 1, count, success, failed, start_time)

            try:
                details = tmdb.get_movie_details(movie.tmdb_id)
                if not details:
                    failed += 1
                    continue

                poster_path = details.get("poster_path")
                backdrop_path = details.get("backdrop_path")

                if poster_path:
                    movie.poster_url = tmdb._get_image_url(poster_path, "w500")

                if not poster_only:
                    if details.get("overview"):
                        movie.description = details["overview"]
                    if details.get("runtime"):
                        movie.runtime = details["runtime"]
                    if details.get("tagline"):
                        movie.tagline = details["tagline"]
                    if details.get("imdb_id"):
                        movie.imdb_id = details["imdb_id"]
                    if details.get("original_language"):
                        movie.language = details["original_language"]
                    director = tmdb._get_director(details.get("credits", {}))
                    if director:
                        movie.director = director
                    actors = tmdb._get_actors(details.get("credits", {}))
                    if actors:
                        movie.set_actors_list(actors)
                    countries = tmdb._get_countries(details.get("production_countries", []))
                    if countries:
                        movie.country = countries

                if backdrop_path:
                    movie.backdrop_url = tmdb._get_image_url(backdrop_path, "w1280")

                movie.status = "active"
                db.session.commit()
                success += 1

            except Exception as e:
                failed += 1
                db.session.rollback()

            time.sleep(wait)

        _progress(count, count, success, failed, start_time)
        elapsed = time.time() - start_time
        print(f"\n完成: 成功 {success}, 失败 {failed}, 耗时 {_fmt_time(elapsed)}")


def _progress(current: int, total: int, success: int, failed: int, start_time: float):
    elapsed = time.time() - start_time
    rate = current / elapsed if elapsed > 0 else 0
    eta = (total - current) / rate if rate > 0 else 0
    bar_len = 30
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = current / total * 100 if total > 0 else 0
    print(
        f"\r[{bar}] {pct:.0f}% | {current}/{total} | "
        f"✓{success} ✗{failed} | {rate:.1f}/s | ETA {_fmt_time(eta)}",
        end="", flush=True,
    )


def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--all", dest="limit", action="store_const", const=None)
    parser.add_argument("--wait", type=float, default=0.25)
    parser.add_argument("--full", action="store_true", help="抓取完整元数据，不仅仅是海报")
    args = parser.parse_args()
    fetch_posters(limit=args.limit, wait=args.wait, poster_only=not args.full)
