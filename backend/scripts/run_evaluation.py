"""离线评估 CLI — Phase 1 验证 → Phase 2 全量。

用法:
    python -m backend.scripts.run_evaluation --phase1-only
    python -m backend.scripts.run_evaluation --n-users 10000 --device cuda
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

from backend.app import create_app, db
from backend.app.models import Rating, Movie
from backend.app.similarity import compute_item_similarity
from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.splitter import three_way_temporal_split
from backend.evaluation.ncf_inference import NCFInference
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.checks import check_random, check_oracle, check_popularity, check_invariants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1-only", action="store_true")
    parser.add_argument("--resume-from", type=int, default=0)
    parser.add_argument("--n-users", type=int, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--models", type=str, default="popularity,random,oracle,itemcf,ncf,hybrid,lightgcn,ease")
    parser.add_argument("--ncf-model", default=None, help="NCF .pt model path")
    parser.add_argument("--ncf-meta", default=None, help="NCF meta JSON path")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    cfg = EvalProtocolConfig()
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else artifacts_dir / "evaluation_results.json"

    project_root = Path(__file__).resolve().parents[2]
    ncf_model = str(project_root / cfg.ncf_model_path) if not args.ncf_model else str(Path(args.ncf_model).resolve())
    ncf_meta = str(project_root / cfg.ncf_meta_path) if not args.ncf_meta else str(Path(args.ncf_meta).resolve())
    models = args.models.split(",")

    t_total = time.time()

    app = create_app()
    with app.app_context():
        print("Loading data from DB...")
        ratings_by_user = _load_ratings()
        movie_genres = _load_movies()
        popularity = _load_popularity()

        print(f"  {sum(len(v) for v in ratings_by_user.values())} ratings, "
              f"{len(ratings_by_user)} users, {len(movie_genres)} movies")

        print("\nSplitting data (three-way temporal)...")
        train, val, test = three_way_temporal_split(ratings_by_user, cfg)
        print(f"  Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

        print("Building ItemCF similarity from training data...")
        train_df = _build_train_df(train)
        t_sim = time.time()
        sims = compute_item_similarity(
            train_df, topk=cfg.sim_topk_per_movie, normalize=True,
        )
        print(f"  {len(sims)} movies ({time.time() - t_sim:.0f}s)")

        print("Spot-checking similarity matrix...")
        _spot_check_sims(sims, movie_genres)
        ncf = NCFInference(ncf_model, ncf_meta, device=args.device)
        print(f"  {ncf.num_users} users, {ncf.num_items} items")

        data_bundle = {
            "train_by_user": train, "test_by_user": test,
            "movie_genres": movie_genres, "popularity": popularity,
            "n_users": len(ratings_by_user), "sims": sims,
        }
        engine = EvaluationEngine(cfg, data_bundle, ncf)

        stats = engine._excluded_stats
        print(f"\nData quality:")
        print(f"  C_all size: {len(engine._c_all)}")
        print(f"  Test items excluded from C_all: {stats['excluded_from_c_all']}/{stats['total_test_items']}")
        print(f"  Users removed (no test in C_all): {stats['users_removed_no_test_in_c_all']}")
        print(f"  Low-signal users (all train < {cfg.like_threshold}): "
              f"{stats['low_signal_users_all_train_below_threshold']}")

        all_test_users = sorted(test.keys())

        # ── Phase 1 ──
        n_p1 = min(cfg.n_phase1_users, len(all_test_users))
        p1_users = all_test_users[:n_p1]
        print(f"\n{'='*60}\nPhase 1: {n_p1} users\n{'='*60}")
        p1_results = engine.run(models, p1_users)
        _print_results(p1_results["summary"])

        # Sanity checks
        print("\nSanity Checks:")
        passed = True
        random_ok, msg = check_random(
            p1_results["per_user_data"].get("random", []), len(engine._c_all), cfg.k,
        )
        print(f"  [{'PASS' if random_ok else 'FAIL'}] Random: {msg}")
        passed = passed and random_ok

        oracle_ok, msg = check_oracle(p1_results["per_user_data"].get("oracle", []))
        print(f"  [{'PASS' if oracle_ok else 'FAIL'}] Oracle: {msg}")
        passed = passed and oracle_ok

        pop_ok, msg = check_popularity(
            p1_results["per_user_data"].get("itemcf", []),
            p1_results["per_user_data"].get("popularity", []),
        )
        print(f"  [{'PASS' if pop_ok else 'FAIL'}] Popularity: {msg}")
        passed = passed and pop_ok

        if not passed:
            print("\nFATAL: Sanity checks failed")
            sys.exit(1)

        if args.phase1_only:
            _write_phase1_output(cfg, engine, p1_results, ncf, t_total, output_path)
            return

        # ── Phase 2 ──
        n_p2 = args.n_users or cfg.n_test_users
        n_p2 = min(n_p2, len(all_test_users))
        p2_users = all_test_users[:n_p2]
        print(f"\n{'='*60}\nPhase 2: {n_p2} users\n{'='*60}")
        p2_results = engine.run(models, p2_users, resume_from=args.resume_from)
        _print_results(p2_results["summary"])

        # Invariants
        inv_ok, violations = check_invariants(p2_results["per_user_data"], None)
        if not inv_ok:
            print(f"\nFATAL: Invariants failed: {violations}")
            sys.exit(1)

        # Write output
        _write_output(cfg, engine, p2_results, ncf, t_total, passed, output_path)
        print(f"\nOutput: {output_path}")
        print(f"Total: {time.time() - t_total:.0f}s")



def _spot_check_sims(sims, movie_genres):
    """抽查 5 部电影的最相似邻居——人工验证 coo_matrix 没有行列写反。"""
    import random as _random
    keys = sorted(sims.keys())
    if len(keys) < 5:
        return
    sample = _random.Random(42).sample(keys, 5)
    # 从 DB 获取标题
    from backend.app.models import Movie as _Movie
    mids = set(sample)
    for mid, neighbors in sims.items():
        if mid in sample:
            mids.update(sid for sid, _s in neighbors[:3])
    titles = {m.id: m.title for m in _Movie.query.filter(_Movie.id.in_(list(mids))).all()}
    print("  Top-3 neighbors:")
    for mid in sample:
        title = titles.get(mid, f"<{mid}>")
        neighbor_strs = []
        for sid, score in sims.get(mid, [])[:3]:
            nt = titles.get(sid, f"<{sid}>")
            neighbor_strs.append(f"{nt}({score:.2f})")
        genres = movie_genres.get(mid, set())
        print(f"  [{','.join(sorted(genres)[:3])}] {title} → {', '.join(neighbor_strs)}")


def _load_ratings():
    # 优先读 CSV 缓存（秒级），fallback DB
    cache_path = Path(__file__).resolve().parents[1] / "artifacts" / "ratings_cache.csv"
    if cache_path.exists():
        print("  Loading from CSV cache...", end=" ", flush=True)
        t0 = time.time()
        import csv
        result = {}
        with open(cache_path) as f:
            reader = csv.reader(f)
            next(reader)  # skip header
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


def _load_movies():
    rows = Movie.query.with_entities(Movie.id, Movie.genres).all()
    result = {}
    for mid, genres_str in rows:
        mid = int(mid)
        result[mid] = set(g.strip() for g in str(genres_str).split("|") if g.strip()) if genres_str else set()
    return result


def _load_popularity():
    from sqlalchemy import func
    rows = db.session.query(Rating.movie_id, func.count(Rating.id)).group_by(Rating.movie_id).all()
    return {int(mid): int(cnt) for mid, cnt in rows}


def _build_train_df(train):
    rows = []
    for uid, items in train.items():
        for mid, r in items:
            rows.append({"user_id": uid, "movie_id": mid, "rating": r})
    return pd.DataFrame(rows)


def _print_results(summary):
    for m, s in summary.items():
        n = s.get("users_evaluated", 0)
        p = s.get("precision_at_k", 0)
        r = s.get("recall_at_k", 0)
        nd = s.get("ndcg_at_k", 0)
        print(f"  {m:<12}: {n:>5} users | P@10={p:.4f} | R@10={r:.4f} | NDCG@10={nd:.4f}")


def _write_phase1_output(cfg, engine, results, ncf, t_total, output_path):
    meta = {
        "protocol_version": "2.0", "phase": "phase1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "k": cfg.k, "candidate_set_size": len(engine._c_all),
        "n_users": len(results["per_user_data"].get("itemcf", [])),
        "runtime_seconds": time.time() - t_total,
        "ncf_users": ncf.num_users, "ncf_items": ncf.num_items,
        "sim_items": len(engine.sims),
    }
    output = {"meta": meta, "summary": results["summary"]}
    mini_path = str(output_path).replace(".json", ".phase1.json")
    with open(mini_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nPhase 1 complete — see {mini_path}")


def _write_output(cfg, engine, results, ncf, t_total, passed, output_path):
    meta = {
        "protocol_version": "2.0", "phase": "phase2",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset": "MovieLens 32M",
        "k": cfg.k, "like_threshold": cfg.like_threshold,
        "test_items_per_user": cfg.test_items_per_user,
        "min_user_interactions": cfg.min_user_interactions,
        "candidate_mode": cfg.candidate_mode,
        "candidate_set_size": len(engine._c_all),
        "seed": cfg.seed,
        "ncf_users": ncf.num_users, "ncf_items": ncf.num_items,
        "sim_items": len(engine.sims),
        "runtime_seconds": time.time() - t_total,
        "sanity_checks_passed": passed,
    }
    output = {"meta": meta, "summary": results["summary"]}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
