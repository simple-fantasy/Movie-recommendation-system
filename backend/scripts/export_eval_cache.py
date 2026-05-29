"""One-shot cache exporter — run ONCE, then evaluator loads from disk in ~3s.

Usage: python -m backend.scripts.export_eval_cache
"""
from __future__ import annotations

import json
import pickle
import time
from pathlib import Path

from sqlalchemy import text
from backend.app import create_app, db
from backend.app.models import Movie


def main():
    app = create_app()
    with app.app_context():
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)

        # 1. Ratings → pickle
        ratings_pkl = artifacts / "eval_ratings_cache.pkl"
        if ratings_pkl.exists():
            print(f"Ratings cache already exists at {ratings_pkl}")
        else:
            print("Exporting ratings to pickle...")
            t0 = time.time()
            conn = db.engine.connect().execution_options(stream_results=True)
            result = conn.execute(
                text("SELECT user_id, movie_id, rating, timestamp "
                     "FROM ratings ORDER BY user_id, timestamp")
            )
            ratings_by_user: dict[int, list[tuple[int, float, str]]] = {}
            count = 0
            batch_size = 50000
            while True:
                rows = result.fetchmany(batch_size)
                if not rows:
                    break
                for uid, mid, r, ts in rows:
                    ratings_by_user.setdefault(uid, []).append((int(mid), float(r), str(ts) if ts else ""))
                count += len(rows)
                if count % 5000000 == 0:
                    elapsed = time.time() - t0
                    print(f"  {count/1e6:.0f}M rows ({count/elapsed:.0f} rows/s)...")
            result.close()
            conn.close()
            print(f"  Done: {count} rows, {len(ratings_by_user)} users ({time.time()-t0:.0f}s)")

            t0 = time.time()
            with open(ratings_pkl, "wb") as f:
                pickle.dump(ratings_by_user, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"  Pickle written ({time.time()-t0:.0f}s)")

        # 2. Movie genres
        genres_json = artifacts / "eval_genres_cache.json"
        if genres_json.exists():
            print(f"Genres cache already exists")
        else:
            print("Exporting movie genres...")
            raw = {}
            for m in Movie.query.with_entities(Movie.id, Movie.genres).all():
                gset = set(g.strip() for g in str(m.genres).split("|") if g.strip()) if m.genres else set()
                raw[str(m.id)] = list(gset)
            with open(genres_json, "w") as f:
                json.dump(raw, f)
            print(f"  {len(raw)} movies")

        # 3. Popularity
        pop_json = artifacts / "eval_popularity_cache.json"
        if pop_json.exists():
            print(f"Popularity cache already exists")
        else:
            print("Computing popularity from pickle...")
            with open(ratings_pkl, "rb") as f:
                rbu = pickle.load(f)
            pop: dict[int, int] = {}
            for items in rbu.values():
                for mid, _r, _ts in items:
                    pop[mid] = pop.get(mid, 0) + 1
            with open(pop_json, "w") as f:
                json.dump({str(k): v for k, v in pop.items()}, f)
            print(f"  {len(pop)} items")

        print("\nDone. All caches in", artifacts)


if __name__ == "__main__":
    main()
