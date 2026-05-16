"""
将 MovieLens links.csv 中的 tmdbId 导入 Movie 表

links.csv 格式: movieId,imdbId,tmdbId
数据库 Movie.id == movieId（来自 import_movielens.py 的导入逻辑）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from backend.app import create_app, db
from backend.app.models import Movie


def import_tmdb_ids(links_path: str):
    """批量导入 tmdbId 到 Movie 表"""
    app = create_app()
    with app.app_context():
        df = pd.read_csv(links_path)
        print(f"读取 links.csv: {len(df)} 条记录")

        # 只导入有效的 tmdbId
        df = df[df["tmdbId"].notna()]
        print(f"有效 tmdbId 记录: {len(df)} 条")

        # 获取当前数据库状态
        existing = set(db.session.query(Movie.id).all())
        existing = {r[0] for r in existing}

        updated = 0
        skipped = 0
        not_found = 0
        batch_size = 5000
        batch = []

        for _, row in df.iterrows():
            movie_id = int(row["movieId"])
            tmdb_id = int(row["tmdbId"])

            if movie_id not in existing:
                not_found += 1
                continue

            # 使用原始 SQL 批量更新，避免 ORM 开销
            batch.append({"movie_id": movie_id, "tmdb_id": tmdb_id})

            if len(batch) >= batch_size:
                _flush_batch(batch)
                updated += len(batch)
                print(f"  已更新 {updated} 部电影...")
                batch = []

        if batch:
            _flush_batch(batch)
            updated += len(batch)

        print(f"\n完成: 更新 {updated} 部, 跳过 {skipped}, 数据库中未匹配 {not_found}")


def _flush_batch(batch: list[dict]):
    """批量执行 UPDATE"""
    # Build CASE WHEN for bulk update
    ids = [b["movie_id"] for b in batch]
    case_stmt = " ".join(
        f"WHEN {b['movie_id']} THEN {b['tmdb_id']}" for b in batch
    )
    sql = f"""
        UPDATE movies
        SET tmdb_id = CASE id {case_stmt} END
        WHERE id IN ({','.join(str(i) for i in ids)})
    """
    db.session.execute(db.text(sql))
    db.session.commit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--links", default="data/ml-32m/links.csv")
    args = parser.parse_args()
    import_tmdb_ids(args.links)
