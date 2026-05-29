"""Ablation experiment: Hybrid recall_k and ItemCF per_seed_limit.
Uses 2000 users for speed. Compares against fixed ItemCF/NCF baselines.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

from backend.app import create_app, db
from backend.app.models import Rating, Movie
from backend.app.similarity import compute_item_similarity
from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.splitter import three_way_temporal_split
from backend.evaluation.ncf_inference import NCFInference
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.checks import check_random, check_oracle, check_popularity


def load_data():
    """Load ratings + movies + popularity from DB / cache."""
    cache_path = Path(__file__).resolve().parents[1] / "artifacts" / "ratings_cache.csv"
    if cache_path.exists():
        print("  Loading from CSV cache...", end=" ", flush=True)
        t0 = time.time()
        import csv
        result = {}
        with open(cache_path) as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                uid = int(row[0])
                mid = int(row[1])
                r = float(row[2])
                ts = row[3] if len(row) > 3 else ""
                result.setdefault(uid, []).append((mid, r, ts))
        print(f"{len(result)} users ({time.time()-t0:.0f}s)")
        return result

    print("  Loading from DB (slow)...")
    rows = (
        Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp)
        .order_by(Rating.user_id.asc(), Rating.timestamp.asc()).all()
    )
    result = {}
    for uid, mid, r, ts in rows:
        result.setdefault(int(uid), []).append((int(mid), float(r), ts))
    return result


def load_movies():
    rows = Movie.query.with_entities(Movie.id, Movie.genres).all()
    result = {}
    for mid, genres_str in rows:
        mid = int(mid)
        result[mid] = set(g.strip() for g in str(genres_str).split("|") if g.strip()) if genres_str else set()
    return result


def load_popularity():
    from sqlalchemy import func
    rows = db.session.query(Rating.movie_id, func.count(Rating.id)).group_by(Rating.movie_id).all()
    return {int(mid): int(cnt) for mid, cnt in rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-users", type=int, default=2000)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--recall-k-values", type=str, default="50,100,200,500")
    parser.add_argument("--per-seed-values", type=str, default="10,25,50,100")
    args = parser.parse_args()

    cfg = EvalProtocolConfig()
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else artifacts_dir / "ablation_results.json"

    project_root = Path(__file__).resolve().parents[2]
    ncf_model = str(project_root / cfg.ncf_model_path)
    ncf_meta = str(project_root / cfg.ncf_meta_path)

    recall_k_values = [int(x) for x in args.recall_k_values.split(",")]
    per_seed_values = [int(x) for x in args.per_seed_values.split(",")]

    t_total = time.time()
    app = create_app()

    with app.app_context():
        print("Loading data...")
        ratings_by_user = load_data()
        movie_genres = load_movies()
        popularity = load_popularity()

        print(f"  {sum(len(v) for v in ratings_by_user.values())} ratings, "
              f"{len(ratings_by_user)} users, {len(movie_genres)} movies")

        print("\nSplitting data (three-way temporal)...")
        train, val, test = three_way_temporal_split(ratings_by_user, cfg)
        print(f"  Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

        print("Building ItemCF similarity from training data...")
        train_df = pd.DataFrame([
            {"user_id": uid, "movie_id": mid, "rating": r}
            for uid, items in train.items() for mid, r in items
        ])
        t_sim = time.time()
        sims = compute_item_similarity(train_df, topk=cfg.sim_topk_per_movie, normalize=True)
        print(f"  {len(sims)} movies ({time.time() - t_sim:.0f}s)")

        print("Loading NCF...")
        ncf = NCFInference(ncf_model, ncf_meta, device=args.device)
        print(f"  {ncf.num_users} users, {ncf.num_items} items")

        all_test_users = sorted(test.keys())
        n_users = min(args.n_users, len(all_test_users))
        test_users = all_test_users[:n_users]
        print(f"\nAblation: {n_users} test users\n")

        results = {
            "meta": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_users": n_users,
                "recall_k_values": recall_k_values,
                "per_seed_values": per_seed_values,
            },
            "baselines": {},
            "hybrid_recall_k": [],
            "itemcf_per_seed": [],
        }

        # ---- BASELINES (run once) ----
        print("=" * 50)
        print("BASELINES: ItemCF + NCF + Popularity")
        print("=" * 50)
        data_bundle = {
            "train_by_user": train, "test_by_user": test,
            "movie_genres": movie_genres, "popularity": popularity,
            "n_users": len(ratings_by_user), "sims": sims,
        }
        engine = EvaluationEngine(cfg, data_bundle, ncf)
        baseline_models = ["popularity", "itemcf", "ncf"]
        baseline_result = engine.run(baseline_models, test_users)
        for m, s in baseline_result["summary"].items():
            print(f"  {m:<12}: P@10={s['precision_at_k']:.4f} R@10={s['recall_at_k']:.4f} NDCG@10={s['ndcg_at_k']:.4f}")
            results["baselines"][m] = {
                "precision_at_k": s["precision_at_k"],
                "recall_at_k": s["recall_at_k"],
                "ndcg_at_k": s["ndcg_at_k"],
                "users_evaluated": s["users_evaluated"],
                "coverage": s.get("coverage", 0),
            }

        # ---- ABLATION 1: Hybrid recall_k ----
        print("\n" + "=" * 50)
        print("ABLATION 1: Hybrid recall_k")
        print("=" * 50)
        for rk in recall_k_values:
            print(f"\n  recall_k={rk} ...")
            cfg_abl = EvalProtocolConfig()
            cfg_abl.recall_k_hybrid = rk  # override

            data_bundle_rk = {
                "train_by_user": train, "test_by_user": test,
                "movie_genres": movie_genres, "popularity": popularity,
                "n_users": len(ratings_by_user), "sims": sims,
            }
            engine_rk = EvaluationEngine(cfg_abl, data_bundle_rk, ncf)
            result_rk = engine_rk.run(["hybrid"], test_users)

            s = result_rk["summary"].get("hybrid", {})
            if s:
                p = s["precision_at_k"]
                r = s["recall_at_k"]
                n = s["ndcg_at_k"]
                cov = s.get("coverage", 0)
                u = s["users_evaluated"]
                print(f"    P@10={p:.4f} R@10={r:.4f} NDCG@10={n:.4f} Coverage={cov:.4f} ({u} users)")
                results["hybrid_recall_k"].append({
                    "recall_k": rk,
                    "precision_at_k": p,
                    "recall_at_k": r,
                    "ndcg_at_k": n,
                    "coverage": cov,
                    "users_evaluated": u,
                })
            else:
                print("    No hybrid results!")

        # ---- ABLATION 2: ItemCF per_seed_limit ----
        print("\n" + "=" * 50)
        print("ABLATION 2: ItemCF per_seed_limit")
        print("=" * 50)
        for psl in per_seed_values:
            print(f"\n  per_seed_limit={psl} ...")
            cfg_abl2 = EvalProtocolConfig()
            cfg_abl2.per_seed_limit = psl

            data_bundle_psl = {
                "train_by_user": train, "test_by_user": test,
                "movie_genres": movie_genres, "popularity": popularity,
                "n_users": len(ratings_by_user), "sims": sims,
            }
            engine_psl = EvaluationEngine(cfg_abl2, data_bundle_psl, ncf)
            result_psl = engine_psl.run(["itemcf"], test_users)

            s = result_psl["summary"].get("itemcf", {})
            if s:
                p = s["precision_at_k"]
                r = s["recall_at_k"]
                n = s["ndcg_at_k"]
                cov = s.get("coverage", 0)
                u = s["users_evaluated"]
                print(f"    P@10={p:.4f} R@10={r:.4f} NDCG@10={n:.4f} Coverage={cov:.4f} ({u} users)")
                results["itemcf_per_seed"].append({
                    "per_seed_limit": psl,
                    "precision_at_k": p,
                    "recall_at_k": r,
                    "ndcg_at_k": n,
                    "coverage": cov,
                    "users_evaluated": u,
                })
            else:
                print("    No itemcf results!")

        # ---- Save ----
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n{'=' * 50}")
        print(f"Results: {output_path}")
        print(f"Total: {time.time() - t_total:.0f}s")


if __name__ == "__main__":
    main()
