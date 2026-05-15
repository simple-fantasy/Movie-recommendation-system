"""Multi-model offline evaluation with ablation study support.

Supports:
- ItemCF (baseline)
- NCF (neural collaborative filtering)
- Hybrid (ItemCF recall + NCF rerank)

Ablation studies:
- Hybrid with different recall_k values
- ItemCF with different per_seed_limit
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any

import numpy as np

from backend.app import create_app, db
from backend.app.models import Movie, MovieSimilarity, Rating
from backend.app.ncf_engine import ncf_engine


@dataclass
class Metrics:
    """Evaluation metrics for a single model/run."""

    model: str
    precision_at_k: float
    recall_at_k: float
    map_at_k: float
    ndcg_at_k: float
    mrr_at_k: float
    users_evaluated: int
    avg_recs: float
    coverage: float
    avg_log_popularity: float
    # Additional metadata
    k: int = 10
    recall_k: int | None = None
    per_seed_limit: int | None = None
    runtime_seconds: float = 0.0
    params: dict[str, Any] = field(default_factory=dict)


def build_similarity_map(topk_per_movie: int) -> dict[int, list[tuple[int, float]]]:
    """Load precomputed ItemCF similarities."""
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


def get_all_item_ids() -> set[int]:
    """Get all movie IDs from database."""
    rows = Movie.query.with_entities(Movie.id).all()
    return {int(r[0]) for r in rows}


def get_item_popularity() -> dict[int, int]:
    """Get popularity (rating count) for each item."""
    pop_rows = (
        db.session.query(Rating.movie_id, db.func.count(Rating.id).label("cnt"))
        .group_by(Rating.movie_id)
        .all()
    )
    return {int(mid): int(cnt) for mid, cnt in pop_rows}


def itemcf_recommend(
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    k: int,
    per_seed_limit: int,
) -> list[int]:
    """Generate ItemCF recommendations."""
    scores: dict[int, float] = {}
    for movie_id, r in history:
        neighbors = sims.get(movie_id, [])[:per_seed_limit]
        for sid, sim in neighbors:
            if sid in seen:
                continue
            scores[sid] = scores.get(sid, 0.0) + float(sim) * float(r)

    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [mid for mid, _ in ranked]


def itemcf_recall_candidates(
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    recall_k: int,
    per_seed_limit: int,
) -> list[int]:
    """Generate ItemCF recall candidates (larger set for reranking)."""
    scores: dict[int, float] = {}
    for movie_id, r in history:
        neighbors = sims.get(movie_id, [])[:per_seed_limit]
        for sid, sim in neighbors:
            if sid in seen:
                continue
            scores[sid] = scores.get(sid, 0.0) + float(sim) * float(r)

    if not scores:
        return []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:recall_k]
    return [mid for mid, _ in ranked]


def ncf_recommend(user_id: int, candidate_ids: list[int], k: int) -> list[int]:
    """Generate NCF recommendations by ranking candidates."""
    if not ncf_engine.is_ready():
        return []
    ranked = ncf_engine.rank(user_id, candidate_ids, top_k=k)
    return [mid for mid, _ in ranked]


def sample_ncf_candidates(
    all_item_ids: set[int],
    seen: set[int],
    candidate_pool_size: int,
    rng: np.random.Generator,
) -> list[int]:
    """Sample NCF candidate pool from unseen items."""
    unseen = list(all_item_ids - seen)
    if not unseen:
        return []
    if candidate_pool_size <= 0 or len(unseen) <= candidate_pool_size:
        return unseen
    sampled = rng.choice(np.asarray(unseen, dtype=np.int64), size=candidate_pool_size, replace=False)
    return sampled.astype(np.int64).tolist()


def hybrid_recommend(
    user_id: int,
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    k: int,
    recall_k: int,
    per_seed_limit: int,
) -> list[int]:
    """Hybrid: ItemCF recall + NCF rerank."""
    candidates = itemcf_recall_candidates(sims, history, seen, recall_k, per_seed_limit)
    if not candidates:
        return []

    if not ncf_engine.is_ready():
        # Fallback to ItemCF if NCF not available
        return candidates[:k]

    return ncf_recommend(user_id, candidates, k)


def compute_metrics(
    recommendations: list[int],
    test_mid: int,
    k: int,
    pop: dict[int, int],
) -> tuple[float, float, float, float, float]:
    """Compute P@K, R@K, MAP@K, NDCG@K, MRR@K for a single user.

    Returns: (precision, recall, map, ndcg, mrr)
    """
    hit_rank = None
    for idx, mid in enumerate(recommendations):
        if mid == test_mid:
            hit_rank = idx
            break

    hit = 1.0 if hit_rank is not None else 0.0
    precision = hit / float(k)
    recall = hit
    map_score = 1.0 / float(hit_rank + 1) if hit_rank is not None else 0.0
    ndcg = 1.0 / float(np.log2(hit_rank + 2)) if hit_rank is not None else 0.0
    mrr = 1.0 / float(hit_rank + 1) if hit_rank is not None else 0.0

    return precision, recall, map_score, ndcg, mrr


def evaluate_model(
    model_name: str,
    k: int,
    like_threshold: float,
    min_ratings: int,
    sims: dict[int, list[tuple[int, float]]],
    pop: dict[int, int],
    all_item_ids: set[int],
    recall_k: int = 100,
    per_seed_limit: int = 50,
    ncf_candidate_pool_size: int = 1000,
    rng_seed: int = 42,
) -> Metrics:
    """Evaluate a single model (ItemCF, NCF, or Hybrid)."""
    start_time = time.time()
    rng = np.random.default_rng(rng_seed)

    rows = (
        Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp)
        .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
        .all()
    )

    by_user: dict[int, list[tuple[int, float, Any]]] = defaultdict(list)
    for uid, mid, r, ts in rows:
        by_user[int(uid)].append((int(mid), float(r), ts))

    precisions = []
    recalls = []
    maps = []
    ndcgs = []
    mrrs = []
    rec_counts = []
    recommended_items: set[int] = set()
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
        # IMPORTANT: seen should only contain training interactions.
        # If test item is included here, hit@k will always be zero.
        seen = {mid for mid, _r, _ts in train_items}

        # Generate recommendations based on model
        if model_name == "itemcf":
            recs = itemcf_recommend(sims, history, seen, k=k, per_seed_limit=per_seed_limit)
        elif model_name == "ncf":
            # NCF: rank a sampled unseen candidate pool
            candidates = sample_ncf_candidates(all_item_ids, seen, ncf_candidate_pool_size, rng)
            recs = ncf_recommend(uid, candidates, k)
        elif model_name == "hybrid":
            recs = hybrid_recommend(
                uid, sims, history, seen, k=k, recall_k=recall_k, per_seed_limit=per_seed_limit
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")

        if not recs:
            continue

        rec_counts.append(len(recs))
        recommended_items.update(recs)

        # Compute metrics
        p, r, m, n, rr = compute_metrics(recs, test_mid, k, pop)
        precisions.append(p)
        recalls.append(r)
        maps.append(m)
        ndcgs.append(n)
        mrrs.append(rr)

        if recs:
            avg_log_pops.append(float(np.mean([np.log1p(pop.get(mid, 0)) for mid in recs])))

    runtime = time.time() - start_time
    users_evaluated = len(precisions)

    if users_evaluated == 0:
        return Metrics(
            model=model_name,
            precision_at_k=0.0,
            recall_at_k=0.0,
            map_at_k=0.0,
            ndcg_at_k=0.0,
            mrr_at_k=0.0,
            users_evaluated=0,
            avg_recs=0.0,
            coverage=0.0,
            avg_log_popularity=0.0,
            k=k,
            recall_k=recall_k if model_name == "hybrid" else None,
            per_seed_limit=per_seed_limit,
            runtime_seconds=runtime,
        )

    total_items = len(all_item_ids)
    coverage = float(len(recommended_items) / float(total_items)) if total_items else 0.0

    return Metrics(
        model=model_name,
        precision_at_k=float(np.mean(precisions)),
        recall_at_k=float(np.mean(recalls)),
        map_at_k=float(np.mean(maps)) if maps else 0.0,
        ndcg_at_k=float(np.mean(ndcgs)) if ndcgs else 0.0,
        mrr_at_k=float(np.mean(mrrs)) if mrrs else 0.0,
        users_evaluated=users_evaluated,
        avg_recs=float(np.mean(rec_counts)) if rec_counts else 0.0,
        coverage=coverage,
        avg_log_popularity=float(np.mean(avg_log_pops)) if avg_log_pops else 0.0,
        k=k,
        recall_k=recall_k if model_name == "hybrid" else None,
        per_seed_limit=per_seed_limit,
        runtime_seconds=runtime,
    )


def print_table(results: list[Metrics]) -> None:
    """Print results as a formatted table."""
    # Header
    print("\n" + "=" * 120)
    print(
        f"{'Model':<12} {'K':<4} {'RecallK':<8} {'SeedLmt':<8} "
        f"{'P@K':<8} {'R@K':<8} {'MAP@K':<8} {'NDCG@K':<8} {'MRR@K':<8} "
        f"{'Users':<8} {'Cov':<8} {'Time(s)':<8}"
    )
    print("-" * 120)

    # Rows
    for r in results:
        recall_k_str = str(r.recall_k) if r.recall_k is not None else "-"
        seed_str = str(r.per_seed_limit) if r.per_seed_limit is not None else "-"
        print(
            f"{r.model:<12} {r.k:<4} {recall_k_str:<8} {seed_str:<8} "
            f"{r.precision_at_k:<8.4f} {r.recall_at_k:<8.4f} {r.map_at_k:<8.4f} "
            f"{r.ndcg_at_k:<8.4f} {r.mrr_at_k:<8.4f} {r.users_evaluated:<8} "
            f"{r.coverage:<8.4f} {r.runtime_seconds:<8.2f}"
        )
    print("=" * 120)


def run_ablation_study(
    k: int,
    like_threshold: float,
    min_ratings: int,
    sims: dict[int, list[tuple[int, float]]],
    pop: dict[int, int],
    all_item_ids: set[int],
    ncf_candidate_pool_size: int,
    rng_seed: int,
) -> list[Metrics]:
    """Run ablation study on hybrid recall_k and itemcf per_seed_limit."""
    results = []

    print("\n[Ablation Study 1] Hybrid with different recall_k values...")
    for recall_k in [50, 100, 200, 500]:
        print(f"  Testing recall_k={recall_k}...")
        m = evaluate_model(
            "hybrid",
            k=k,
            like_threshold=like_threshold,
            min_ratings=min_ratings,
            sims=sims,
            pop=pop,
            all_item_ids=all_item_ids,
            recall_k=recall_k,
            per_seed_limit=50,
            ncf_candidate_pool_size=ncf_candidate_pool_size,
            rng_seed=rng_seed,
        )
        results.append(m)

    print("\n[Ablation Study 2] ItemCF with different per_seed_limit values...")
    for psl in [10, 25, 50, 100]:
        print(f"  Testing per_seed_limit={psl}...")
        m = evaluate_model(
            "itemcf",
            k=k,
            like_threshold=like_threshold,
            min_ratings=min_ratings,
            sims=sims,
            pop=pop,
            all_item_ids=all_item_ids,
            per_seed_limit=psl,
            ncf_candidate_pool_size=ncf_candidate_pool_size,
            rng_seed=rng_seed,
        )
        results.append(m)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-model offline evaluation")
    parser.add_argument("--k", type=int, default=10, help="Top-K for evaluation")
    parser.add_argument("--like-threshold", type=float, default=4.0, help="Rating threshold for positive feedback")
    parser.add_argument("--min-ratings", type=int, default=10, help="Min ratings per user to evaluate")
    parser.add_argument("--per-seed-limit", type=int, default=50, help="Max neighbors per seed movie (ItemCF)")
    parser.add_argument("--sim-topk-per-movie", type=int, default=50, help="Precomputed similarities per movie")
    parser.add_argument("--recall-k", type=int, default=100, help="Recall set size for hybrid model")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["itemcf", "ncf", "hybrid", "all"],
        default=["all"],
        help="Models to evaluate",
    )
    parser.add_argument("--ablation", action="store_true", help="Run ablation study")
    parser.add_argument(
        "--ncf-candidate-pool-size",
        type=int,
        default=1000,
        help="Number of unseen candidates sampled per user for NCF ranking (0 means all unseen).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible candidate sampling")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("Loading similarity data...")
        sims = build_similarity_map(int(args.sim_topk_per_movie))
        pop = get_item_popularity()
        all_item_ids = get_all_item_ids()
        print(f"Loaded {len(sims)} movies with similarities, {len(all_item_ids)} total items")

        # Load NCF model if needed
        if "ncf" in args.models or "hybrid" in args.models or "all" in args.models:
            print("Loading NCF model...")
            loaded = ncf_engine.load()
            if loaded:
                print(f"  NCF model loaded: {ncf_engine.num_users} users, {ncf_engine.num_items} items")
            else:
                print("  WARNING: NCF model not found. NCF and Hybrid evaluations will fail.")

        models_to_eval = []
        if "all" in args.models:
            models_to_eval = ["itemcf", "ncf", "hybrid"]
        else:
            models_to_eval = args.models

        results: list[Metrics] = []

        # Main evaluation
        print("\n" + "=" * 60)
        print("MAIN EVALUATION")
        print("=" * 60)

        for model in models_to_eval:
            print(f"\nEvaluating {model.upper()}...")
            try:
                m = evaluate_model(
                    model,
                    k=int(args.k),
                    like_threshold=float(args.like_threshold),
                    min_ratings=int(args.min_ratings),
                    sims=sims,
                    pop=pop,
                    all_item_ids=all_item_ids,
                    recall_k=int(args.recall_k),
                    per_seed_limit=int(args.per_seed_limit),
                    ncf_candidate_pool_size=int(args.ncf_candidate_pool_size),
                    rng_seed=int(args.seed),
                )
                results.append(m)
                print(f"  P@K={m.precision_at_k:.4f}, R@K={m.recall_at_k:.4f}, NDCG@K={m.ndcg_at_k:.4f}")
            except Exception as e:
                print(f"  ERROR: {e}")

        # Ablation study
        if args.ablation:
            print("\n" + "=" * 60)
            print("ABLATION STUDY")
            print("=" * 60)
            ablation_results = run_ablation_study(
                k=int(args.k),
                like_threshold=float(args.like_threshold),
                min_ratings=int(args.min_ratings),
                sims=sims,
                pop=pop,
                all_item_ids=all_item_ids,
                ncf_candidate_pool_size=int(args.ncf_candidate_pool_size),
                rng_seed=int(args.seed),
            )
            results.extend(ablation_results)

        # Print results table
        print_table(results)

        # Save results
        output_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "k": args.k,
                "like_threshold": args.like_threshold,
                "min_ratings": args.min_ratings,
                "per_seed_limit": args.per_seed_limit,
                "sim_topk_per_movie": args.sim_topk_per_movie,
                "recall_k": args.recall_k,
                "ncf_candidate_pool_size": args.ncf_candidate_pool_size,
                "seed": args.seed,
            },
            "results": [asdict(r) for r in results],
        }

        if args.output:
            out_path = Path(args.output)
        else:
            out_path = Path(__file__).resolve().parents[1] / "artifacts" / "evaluation_results.json"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
