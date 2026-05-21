#!/usr/bin/env python3
"""
为热门电影批量添加在线观看链接（搜索链接）
基于 MovieLens 标题格式匹配
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app, db
from backend.app.models import Movie, WatchLink


# 中文搜索关键词映射（MovieLens 标题 → 中文关键词）
SEARCH_KEYWORDS = {
    "Shawshank Redemption, The": "肖申克的救赎",
    "Forrest Gump": "阿甘正传",
    "Pulp Fiction": "低俗小说",
    "Matrix, The": "黑客帝国",
    "Silence of the Lambs, The": "沉默的羔羊",
    "Star Wars: Episode IV - A New Hope": "星球大战4",
    "Fight Club": "搏击俱乐部",
    "Jurassic Park": "侏罗纪公园",
    "Schindler's List": "辛德勒的名单",
    "Lord of the Rings: The Fellowship of the Ring, The": "指环王1",
    "Lord of the Rings: The Two Towers, The": "指环王2",
    "Lord of the Rings: The Return of the King, The": "指环王3",
    "Braveheart": "勇敢的心",
    "Toy Story": "玩具总动员",
    "Terminator 2: Judgment Day": "终结者2",
    "Usual Suspects, The": "非常嫌疑犯",
    "Godfather, The": "教父",
    "Inception": "盗梦空间",
    "Interstellar": "星际穿越",
    "Dark Knight, The": "蝙蝠侠黑暗骑士",
    "Parasite": "寄生虫",
    "Joker": "小丑",
    "Your Name.": "你的名字",
    "Coco": "寻梦环游记",
    "Avengers: Endgame": "复仇者联盟4",
    "Spirited Away": "千与千寻",
    "Goodfellas": "好家伙",
    "Whiplash": "爆裂鼓手",
    "Green Mile, The": "绿里奇迹",
    "Saving Private Ryan": "拯救大兵瑞恩",
    "Gladiator": "角斗士",
    "Departed, The": "无间道风云",
    "Prestige, The": "致命魔术",
    "Lion King, The": "狮子王",
    "Titanic": "泰坦尼克号",
    "American Beauty": "美国丽人",
}


def seed():
    app = create_app()
    with app.app_context():
        # Get top movies by rating count
        top_movies = (
            Movie.query
            .filter(Movie.rating_count > 0)
            .order_by(Movie.rating_count.desc())
            .limit(50)
            .all()
        )

        count = 0
        for movie in top_movies:
            # Match by title
            keyword = SEARCH_KEYWORDS.get(movie.title)
            if not keyword:
                # Try partial match
                for title_key, kw in SEARCH_KEYWORDS.items():
                    if title_key.lower() in movie.title.lower() or movie.title.lower() in title_key.lower():
                        keyword = kw
                        break

            if not keyword:
                continue

            # Determine platforms and links
            links_to_add = [
                {"platform": "bilibili", "url": f"https://search.bilibili.com/all?keyword={keyword}", "quality": "HD", "is_free": True},
                {"platform": "YouTube", "url": f"https://www.youtube.com/results?search_query={movie.title.replace(' ', '+')}+full+movie", "quality": "HD", "is_free": True},
            ]

            for link_info in links_to_add:
                existing = WatchLink.query.filter_by(movie_id=movie.id, url=link_info["url"]).first()
                if existing:
                    continue
                link = WatchLink(
                    movie_id=movie.id,
                    platform=link_info["platform"],
                    url=link_info["url"],
                    quality=link_info.get("quality", "HD"),
                    is_free=link_info.get("is_free", True),
                    is_official=False,
                    status="active",
                )
                db.session.add(link)
                count += 1

        db.session.commit()
        print(f"Added {count} watch links for popular movies")


if __name__ == "__main__":
    seed()
