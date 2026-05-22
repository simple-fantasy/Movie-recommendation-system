#!/usr/bin/env python3
"""
为热门电影批量生成在线观看链接。

策略:
1. 取评分数量最高的 N 部电影（默认 100 部，需有 tmdb_id）
2. 通过 TMDB watch/providers API 获取合法观影渠道（CN 区）
3. 为国内主流平台生成搜索链接: Bilibili / YouTube / 爱奇艺 / 腾讯视频 / 优酷 / 芒果TV
4. 已有同名链接的电影自动跳过（幂等）

用法:
    python -m backend.scripts.enrich_watch_links              # 默认 top 100
    python -m backend.scripts.enrich_watch_links --top 200    # top 200
    python -m backend.scripts.enrich_watch_links --dry-run    # 预览，不写入数据库
"""

import argparse
import os
import sys
import time
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import Movie, WatchLink
from backend.services.tmdb_service import TMDBService


# ── 平台搜索 URL 模板 ──
PLATFORMS = [
    {
        "platform": "bilibili",
        "url_template": "https://search.bilibili.com/all?keyword={query}",
        "name": "哔哩哔哩",
        "is_free": True,
    },
    {
        "platform": "YouTube",
        "url_template": "https://www.youtube.com/results?search_query={query}",
        "name": "YouTube",
        "is_free": True,
    },
    {
        "platform": "iQiyi",
        "url_template": "https://www.iqiyi.com/search.html?key={query}",
        "name": "爱奇艺",
        "is_free": False,
    },
    {
        "platform": "Tencent",
        "url_template": "https://v.qq.com/x/search/?q={query}",
        "name": "腾讯视频",
        "is_free": False,
    },
    {
        "platform": "Youku",
        "url_template": "https://so.youku.com/search_video/q_{query}",
        "name": "优酷",
        "is_free": False,
    },
    {
        "platform": "MangoTV",
        "url_template": "https://www.mgtv.com/search?q={query}",
        "name": "芒果TV",
        "is_free": False,
    },
]


def _search_keyword(movie):
    """为电影生成搜索关键词。

    优先使用电影标题（英文），如果标题过长则截取前 3 个词。
    标题中包含中文则直接使用。
    """
    title = movie.title or ""
    # 检测是否包含中文
    has_chinese = any('一' <= ch <= '鿿' for ch in title)
    if has_chinese:
        return title
    # 英文标题: 截取前 4 个词
    parts = title.split()
    if len(parts) > 4:
        return " ".join(parts[:4])
    return title


def enrich(args):
    app = create_app()
    with app.app_context():
        # 查询热门电影
        top_movies = (
            Movie.query
            .filter(Movie.rating_count > 0, Movie.tmdb_id.isnot(None))
            .order_by(Movie.rating_count.desc())
            .limit(args.top)
            .all()
        )
        print(f"找到 {len(top_movies)} 部热门电影 (rating_count > 0, 有 tmdb_id)")

        tmdb = TMDBService()
        total_added = 0
        tmdb_links_added = 0
        platform_links_added = 0
        skipped = 0

        for i, movie in enumerate(top_movies):
            keyword = _search_keyword(movie)
            if args.dry_run:
                print(f"\n[{i+1}/{len(top_movies)}] {movie.title} ({movie.year}) — 关键词: {keyword}")
            else:
                if (i + 1) % 10 == 0:
                    print(f"[{i+1}/{len(top_movies)}] 已处理... 新增 {total_added} 条链接")

            # 1. 尝试 TMDB watch providers（只对前 50 部查询，避免 API 限流）
            if i < 50 and movie.tmdb_id:
                try:
                    cn_link = tmdb.get_cn_watch_link(movie.tmdb_id)
                    if cn_link:
                        existing = WatchLink.query.filter_by(
                            movie_id=movie.id, url=cn_link
                        ).first()
                        if not existing and not args.dry_run:
                            link = WatchLink(
                                movie_id=movie.id,
                                platform="TMDB-CN",
                                url=cn_link,
                                quality="HD",
                                is_free=False,
                                is_official=True,
                                status="active",
                            )
                            db.session.add(link)
                            tmdb_links_added += 1
                            total_added += 1
                        elif not existing:
                            print(f"  [DRY-RUN] TMDB-CN: {cn_link[:80]}...")
                            tmdb_links_added += 1
                            total_added += 1
                except Exception as e:
                    pass  # TMDB 查询失败不阻塞流程

            # 2. 为每个平台生成搜索链接
            for plat in PLATFORMS:
                query = quote(keyword)
                url = plat["url_template"].format(query=query)

                existing = WatchLink.query.filter_by(
                    movie_id=movie.id, url=url
                ).first()
                if existing:
                    skipped += 1
                    continue

                if args.dry_run:
                    print(f"  [DRY-RUN] {plat['platform']} ({plat['name']}): {url[:80]}...")
                    platform_links_added += 1
                    total_added += 1
                else:
                    link = WatchLink(
                        movie_id=movie.id,
                        platform=plat["platform"],
                        url=url,
                        quality="HD",
                        is_free=plat.get("is_free", True),
                        is_official=False,
                        status="active",
                    )
                    db.session.add(link)
                    platform_links_added += 1
                    total_added += 1

            # 每 20 部电影提交一次
            if not args.dry_run and (i + 1) % 20 == 0:
                db.session.commit()

        # 最终提交
        if not args.dry_run:
            db.session.commit()

        print(f"\n{'=' * 50}")
        if args.dry_run:
            print(f"🔍 预览完成（未写入数据库）")
        else:
            print(f"✅ 完成！")
        print(f"   处理电影: {len(top_movies)}")
        print(f"   TMDB 官方链接: {tmdb_links_added}")
        print(f"   平台搜索链接: {platform_links_added}")
        print(f"   总计新增: {total_added}")
        print(f"   已跳过(重复): {skipped}")


def main():
    parser = argparse.ArgumentParser(description="为热门电影批量生成在线观看链接")
    parser.add_argument("--top", type=int, default=100, help="处理前 N 部电影 (默认 100)")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不写入数据库")
    args = parser.parse_args()
    enrich(args)


if __name__ == "__main__":
    main()
