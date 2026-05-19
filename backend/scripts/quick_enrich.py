"""
快速电影元数据抓取脚本
使用 TMDB 搜索 API（比直接 tmdbId 查询更可靠——links.csv 中约 40% tmdbId 已过期）
每部电影 1 次搜索 API 即可拿到海报 URL，热门电影额外调用详情 API 获取完整元数据
"""
from __future__ import annotations

import argparse
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from backend.app import create_app, db
from backend.app.models import Movie

API_KEY = "f0a5731f00e718c73788920729a24b9a"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
DETAIL_URL = "https://api.themoviedb.org/3/movie"
IMAGE_BASE = "https://image.tmdb.org/t/p"


def search_tmdb(title: str, year: int | None) -> dict | None:
    params = {"api_key": API_KEY, "query": title, "language": "zh-CN"}
    if year:
        params["year"] = year
    try:
        r = requests.get(SEARCH_URL, params=params, timeout=5)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0]
        elif r.status_code == 429:
            time.sleep(2)
            r = requests.get(SEARCH_URL, params=params, timeout=5)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    return results[0]
        return None
    except Exception:
        return None


def get_details(tmdb_id: int) -> dict:
    params = {"api_key": API_KEY, "language": "zh-CN", "append_to_response": "credits"}
    try:
        r = requests.get(f"{DETAIL_URL}/{tmdb_id}", params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3000)
    parser.add_argument("--wait", type=float, default=0.15)
    parser.add_argument("--full-limit", type=int, default=500,
                        help="前 N 部电影额外获取完整详情（导演/演员/简介）")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        movies = (
            Movie.query
            .filter(db.or_(
                Movie.poster_url.is_(None),
                Movie.poster_url == "",
                Movie.poster_url.contains("placeholder"),
            ))
            .order_by(Movie.rating_count.desc())
            .limit(args.limit)
            .all()
        )

        print(f"待处理: {len(movies)} 部电影")
        print(f"搜索间隔: {args.wait}s | 预计耗时: {len(movies) * args.wait / 60:.1f} 分钟")
        print(f"前 {args.full_limit} 部将获取完整详情")
        print(f"{'='*60}")

        poster_ok = 0
        full_ok = 0
        not_found = 0
        start = time.time()

        for i, movie in enumerate(movies):
            result = search_tmdb(movie.title, movie.year)

            if not result:
                not_found += 1
                time.sleep(args.wait)
                if (i + 1) % 25 == 0:
                    _status(i + 1, len(movies), poster_ok, full_ok, not_found, start)
                continue

            # 提取海报
            poster_path = result.get("poster_path")
            if poster_path:
                movie.poster_url = f"{IMAGE_BASE}/w342{poster_path}"
                poster_ok += 1

            backdrop_path = result.get("backdrop_path")
            if backdrop_path:
                movie.backdrop_url = f"{IMAGE_BASE}/w1280{backdrop_path}"

            # 更新 tmdb_id（如果原来的已过期）
            new_tmdb_id = result.get("id")
            if new_tmdb_id:
                movie.tmdb_id = new_tmdb_id

            # 前 N 部热门电影获取完整详情
            if i < args.full_limit:
                details = get_details(new_tmdb_id) if new_tmdb_id else {}
                if details:
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
                    # 导演
                    crew = details.get("credits", {}).get("crew", [])
                    for person in crew:
                        if person.get("job") == "Director":
                            movie.director = person.get("name")
                            break
                    # 演员
                    cast = details.get("credits", {}).get("cast", [])
                    if cast:
                        import json
                        movie.actors = json.dumps(
                            [a["name"] for a in cast[:5] if a.get("name")],
                            ensure_ascii=False,
                        )
                    # 国家
                    countries = details.get("production_countries", [])
                    if countries:
                        movie.country = ", ".join(
                            c.get("name", "") for c in countries[:3]
                        )
                    full_ok += 1

            movie.status = "active"
            db.session.commit()

            time.sleep(args.wait)

            if (i + 1) % 25 == 0:
                _status(i + 1, len(movies), poster_ok, full_ok, not_found, start)

        _status(len(movies), len(movies), poster_ok, full_ok, not_found, start)
        elapsed = time.time() - start
        print(f"\n完成! 海报 +{poster_ok} | 完整详情 +{full_ok} | 未找到 {not_found}")
        print(f"总耗时: {elapsed/60:.1f} 分钟")


def _status(done, total, poster, full, nf, start):
    elapsed = time.time() - start
    rate = done / elapsed if elapsed > 0 else 0
    eta = (total - done) / rate if rate > 0 else 0
    print(
        f"[{done}/{total} {done/total*100:.0f}%] "
        f"海报+{poster} 详情+{full} 未找到:{nf} | "
        f"{rate:.1f}/s | ETA {eta/60:.1f}min"
    )


if __name__ == "__main__":
    main()
