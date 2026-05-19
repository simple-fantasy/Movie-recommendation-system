"""轻量级评估：采样 2000 用户，对 ItemCF / NCF / Hybrid 分别计算 Top-K 指标"""
from __future__ import annotations

import argparse, json, time, sys, os
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import create_app, db
from backend.app.models import Movie, MovieSimilarity, Rating, User
from backend.app.ncf_engine import ncf_engine


def evaluate():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--sample-users", type=int, default=2000)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # Load NCF
        print("Loading NCF model...")
        ncf_ready = ncf_engine.load()
        if ncf_ready:
            print(f"  OK: {ncf_engine.num_users} users, {ncf_engine.num_items} items")

        # Load ItemCF similarities
        sims: dict[int, list[tuple[int, float]]] = defaultdict(list)
        for mid, sid, score in (
            MovieSimilarity.query.with_entities(
                MovieSimilarity.movie_id, MovieSimilarity.similar_movie_id, MovieSimilarity.score
            ).order_by(MovieSimilarity.movie_id, MovieSimilarity.score.desc()).all()
        ):
            if len(sims[mid]) < 50:
                sims[mid].append((sid, float(score)))

        # Get qualifying users (with >= 15 ratings)
        from sqlalchemy import func
        candidates = (
            db.session.query(Rating.user_id, func.count(Rating.id))
            .group_by(Rating.user_id)
            .having(func.count(Rating.id) >= 15)
            .limit(args.sample_users * 3)
            .all()
        )
        if not candidates:
            print("No users with enough ratings")
            return

        rng = np.random.default_rng(42)
        selected = [int(c[0]) for c in candidates]
        if len(selected) > args.sample_users:
            selected = sorted(rng.choice(selected, size=args.sample_users, replace=False).tolist())

        print(f"Evaluating on {len(selected)} users (with >=15 ratings)...")

        # Per-model metrics
        counts = {"itemcf": [], "ncf": [], "hybrid": []}
        hr = {"itemcf": [], "ncf": [], "hybrid": []}
        ndcg = {"itemcf": [], "ncf": [], "hybrid": []}
        rec_counts = {"itemcf": [], "ncf": [], "hybrid": []}

        start = time.time()
        processed = 0

        # For each user: build training history & test item
        user_data = (
            Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp)
            .filter(Rating.user_id.in_(selected))
            .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
            .all()
        )

        print(f"Loaded {len(user_data)} ratings for sampled users")
        by_user: dict[int, list[tuple[int, float]]] = defaultdict(list)
        for uid, mid, r, ts in user_data:
            by_user[int(uid)].append((int(mid), float(r)))

        total = len(selected)
        for uid in selected:
            items = by_user.get(uid, [])
            if len(items) < 10:
                continue

            test_mid, test_r = items[-1]
            if test_r < 4.0:
                continue

            train = items[:-1]
            seen = {mid for mid, _ in train}

            # ItemCF
            scores = defaultdict(float)
            for seed_mid, seed_r in train:
                for sid, sim in sims.get(seed_mid, [])[:50]:
                    if sid not in seen:
                        scores[sid] += sim * seed_r
            if scores:
                itemcf_recs = [mid for mid, _ in sorted(scores.items(), key=lambda x: -x[1])[:args.k]]
            else:
                itemcf_recs = []

            # NCF
            ncf_recs = []
            if ncf_ready and uid in ncf_engine.user2idx:
                # Sample candidate pool of 2000 unseen items (include test item)
                all_items = set(sims.keys())
                unseen = list(all_items - seen - {test_mid})
                rng.shuffle(np.array(unseen, dtype=np.int64))
                pool = [test_mid] + unseen[:1999]
                rng.shuffle(np.array(pool, dtype=np.int64))
                ranked = ncf_engine.rank(uid, pool.tolist() if isinstance(pool, np.ndarray) else pool, top_k=args.k)
                ncf_recs = [mid for mid, _ in ranked]

            # Hybrid
            hybrid_recs = []
            if ncf_ready and uid in ncf_engine.user2idx and scores:
                # ItemCF recall top 100
                recall = sorted(scores.items(), key=lambda x: -x[1])[:100]
                candidates = [mid for mid, _ in recall]
                if test_mid not in candidates:
                    candidates.append(test_mid)
                ranked = ncf_engine.rank(uid, candidates, top_k=args.k)
                hybrid_recs = [mid for mid, _ in ranked]
                if not hybrid_recs:
                    hybrid_recs = itemcf_recs[:args.k]
            elif scores:
                hybrid_recs = itemcf_recs[:args.k]

            # Compute HR and NDCG for each model
            for model, recs in [("itemcf", itemcf_recs), ("ncf", ncf_recs), ("hybrid", hybrid_recs)]:
                if not recs:
                    continue
                hit_rank = next((i for i, mid in enumerate(recs) if mid == test_mid), None)
                counts[model].append(1)
                rec_counts[model].append(len(recs))
                if hit_rank is not None:
                    hr[model].append(1.0)
                    ndcg[model].append(1.0 / np.log2(hit_rank + 2))
                else:
                    hr[model].append(0.0)
                    ndcg[model].append(0.0)

            processed += 1
            if processed % 500 == 0:
                elapsed = time.time() - start
                print(f"  {processed} users | {processed/elapsed:.1f} u/s")

        elapsed = time.time() - start
        print(f"\n完成 {processed} 用户评估，耗时 {elapsed:.1f}s\n")
        print("=" * 70)
        print(f"{'Model':<12} {'Users':<8} {'HR@K':<10} {'NDCG@K':<10} {'AvgRecs':<10}")
        print("-" * 70)
        for model in ["itemcf", "ncf", "hybrid"]:
            n = len(counts[model])
            if n == 0:
                continue
            hr_val = float(np.mean(hr[model]))
            ndcg_val = float(np.mean(ndcg[model]))
            avg_rec = float(np.mean(rec_counts[model]))
            print(f"{model:<12} {n:<8} {hr_val:<10.4f} {ndcg_val:<10.4f} {avg_rec:<10.1f}")
        print("=" * 70)


if __name__ == "__main__":
    evaluate()
