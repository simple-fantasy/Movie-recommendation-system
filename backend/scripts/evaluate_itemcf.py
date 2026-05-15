from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from backend.app import create_app, db
from backend.app.models import MovieSimilarity, Rating


@dataclass
class Metrics:
    precision_at_k: float
    recall_at_k: float
    map_at_k: float
    ndcg_at_k: float
    users_evaluated: int
    avg_recs: float
    coverage: float
    avg_log_popularity: float


def build_similarity_map(topk_per_movie: int) -> dict[int, list[tuple[int, float]]]:
    rows = (
        MovieSimilarity.query.with_entities(
            MovieSimilarity.movie_id, MovieSimilarity.similar_movie_id, MovieSimilarity.score
        )
        .order_by(MovieSimilarity.movie_id.asc(), MovieSimilarity.score.desc())
        .all()
    )

    sims: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for mid, sid, score in rows:
        lst = sims[int(mid)]
        if len(lst) < topk_per_movie:
            lst.append((int(sid), float(score)))
    return sims


def recommend_from_history(
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    k: int,
    per_seed_limit: int,
) -> list[int]:
    scores: dict[int, float] = {}
    for movie_id, r in history:
        neighbors = sims.get(movie_id, [])
        for sid, sim in neighbors[:per_seed_limit]:
            if sid in seen:
                continue
            scores[sid] = scores.get(sid, 0.0) + float(sim) * float(r)

    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [mid for mid, _ in ranked]


def evaluate(
    k: int,
    like_threshold: float,
    min_ratings: int,
    per_seed_limit: int,
    sim_topk_per_movie: int,
) -> Metrics:
    rows = (
        Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp)
        .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
        .all()
    )

    by_user: dict[int, list[tuple[int, float, object]]] = defaultdict(list)
    for uid, mid, r, ts in rows:
        by_user[int(uid)].append((int(mid), float(r), ts))

    sims = build_similarity_map(sim_topk_per_movie)

    precisions = []
    recalls = []
    maps = []
    ndcgs = []
    rec_counts = []
    recommended_items: set[int] = set()

    pop_rows = (
        db.session.query(Rating.movie_id, db.func.count(Rating.id).label("cnt"))
        .group_by(Rating.movie_id)
        .all()
    )
    pop = {int(mid): int(cnt) for mid, cnt in pop_rows}
    avg_log_pops = []

    for uid, items in by_user.items():
        if len(items) < max(min_ratings, 2):
            continue

        test_item = items[-1]
        train_items = items[:-1]

        test_mid, test_rating, _test_ts = test_item
        if test_rating < like_threshold:
            continue

        history = [(mid, r) for mid, r, _ts in train_items]
        train_seen = {mid for mid, _r, _ts in train_items}
        recs = recommend_from_history(sims, history, seen=train_seen, k=k, per_seed_limit=per_seed_limit)
        rec_counts.append(len(recs))
        recommended_items.update(recs)

        if k <= 0:
            continue

        hit_rank = None
        for idx, mid in enumerate(recs):
            if mid == test_mid:
                hit_rank = idx
                break

        hit = 1.0 if hit_rank is not None else 0.0
        precisions.append(hit / float(k))
        recalls.append(hit)

        maps.append(1.0 / float(hit_rank + 1) if hit_rank is not None else 0.0)
        ndcgs.append(1.0 / float(np.log2(hit_rank + 2)) if hit_rank is not None else 0.0)

        if recs:
            avg_log_pops.append(float(np.mean([np.log1p(pop.get(mid, 0)) for mid in recs])))

    users_evaluated = len(precisions)
    if users_evaluated == 0:
        return Metrics(0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0)

    precision_at_k = float(np.mean(precisions))
    recall_at_k = float(np.mean(recalls))
    map_at_k = float(np.mean(maps)) if maps else 0.0
    ndcg_at_k = float(np.mean(ndcgs)) if ndcgs else 0.0
    avg_recs = float(np.mean(rec_counts)) if rec_counts else 0.0

    total_items = db.session.query(db.func.count(db.distinct(Rating.movie_id))).scalar() or 0
    coverage = float(len(recommended_items) / float(total_items)) if total_items else 0.0

    avg_log_popularity = float(np.mean(avg_log_pops)) if avg_log_pops else 0.0

    return Metrics(precision_at_k, recall_at_k, map_at_k, ndcg_at_k, users_evaluated, avg_recs, coverage, avg_log_popularity)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--like-threshold", type=float, default=4.0)
    parser.add_argument("--min-ratings", type=int, default=10)
    parser.add_argument("--per-seed-limit", type=int, default=50)
    parser.add_argument("--sim-topk-per-movie", type=int, default=50)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        m = evaluate(
            k=int(args.k),
            like_threshold=float(args.like_threshold),
            min_ratings=int(args.min_ratings),
            per_seed_limit=int(args.per_seed_limit),
            sim_topk_per_movie=int(args.sim_topk_per_movie),
        )

        print(
            {
                "precision@k": m.precision_at_k,
                "recall@k": m.recall_at_k,
                "map@k": m.map_at_k,
                "ndcg@k": m.ndcg_at_k,
                "k": int(args.k),
                "like_threshold": float(args.like_threshold),
                "users_evaluated": m.users_evaluated,
                "avg_recs": m.avg_recs,
                "coverage": m.coverage,
                "avg_log_popularity": m.avg_log_popularity,
            }
        )

        out = {
            "precision@k": m.precision_at_k,
            "recall@k": m.recall_at_k,
            "map@k": m.map_at_k,
            "ndcg@k": m.ndcg_at_k,
            "k": int(args.k),
            "like_threshold": float(args.like_threshold),
            "min_ratings": int(args.min_ratings),
            "per_seed_limit": int(args.per_seed_limit),
            "sim_topk_per_movie": int(args.sim_topk_per_movie),
            "users_evaluated": m.users_evaluated,
            "avg_recs": m.avg_recs,
            "coverage": m.coverage,
            "avg_log_popularity": m.avg_log_popularity,
        }

        path = Path(__file__).resolve().parents[1] / "artifacts" / "offline_metrics.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
