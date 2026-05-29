"""Compute correct stratification NDCG using min_user_interactions=16 protocol.

Loads models once, evaluates itemcf/ease/lightgcn on 10000 test users,
exports per-user NDCG data, and computes Warm(16-20)/Hot(>20) stratification.
"""

import csv, json, time, sys
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


def main():
    t_start = time.time()
    cfg = EvalProtocolConfig()
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    project_root = Path(__file__).resolve().parents[2]

    # ── 1. Load ratings from CSV cache ──
    cache_path = artifacts_dir / "ratings_cache.csv"
    print("Loading ratings...")
    ratings_by_user = {}
    with open(cache_path) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            uid = int(row[0])
            mid = int(row[1])
            r = float(row[2])
            ts = row[3] if len(row) > 3 else ""
            ratings_by_user.setdefault(uid, []).append((mid, r, ts))
    print(f"  {sum(len(v) for v in ratings_by_user.values())} ratings, "
          f"{len(ratings_by_user)} users ({time.time()-t_start:.0f}s)")

    # ── 2. Split ──
    train, val, test = three_way_temporal_split(ratings_by_user, cfg)
    print(f"Split: train={len(train)}, val={len(val)}, test={len(test)}")

    # ── 3. Load movie genres + popularity ──
    app = create_app()
    with app.app_context():
        movie_genres = {}
        for m in Movie.query.with_entities(Movie.id, Movie.genres).all():
            mid = int(m.id)
            g_str = m.genres
            movie_genres[mid] = set(g.strip() for g in str(g_str).split("|") if g.strip()) if g_str else set()

        from sqlalchemy import func
        pop_rows = db.session.query(Rating.movie_id, func.count(Rating.id)).group_by(Rating.movie_id).all()
        popularity = {int(mid): int(cnt) for mid, cnt in pop_rows}
    print(f"  {len(movie_genres)} movies, {len(popularity)} items with popularity")

    # ── 4. Build ItemCF similarity from training data ──
    print("Building ItemCF similarity...")
    t_sim = time.time()
    train_rows = []
    for uid, items in train.items():
        for mid, r in items:
            train_rows.append({"user_id": uid, "movie_id": mid, "rating": r})
    train_df = pd.DataFrame(train_rows)
    sims = compute_item_similarity(train_df, topk=cfg.sim_topk_per_movie, normalize=True)
    print(f"  {len(sims)} movies ({time.time()-t_sim:.0f}s)")

    # ── 5. Load models ──
    print("Loading EASE...")
    t_m = time.time()
    import json as _json
    ease_b_path = artifacts_dir / "ease_B.npy"
    ease_meta_path = artifacts_dir / "ease_meta.json"
    if ease_b_path.exists() and ease_meta_path.exists():
        EASE_B = np.load(ease_b_path)
        ease_meta = _json.loads(ease_meta_path.read_text())
        ease_item2idx = {int(k): int(v) for k, v in ease_meta["item2idx"].items()}
        ease_n_items = ease_meta["n_items"]
        print(f"  EASE: {ease_n_items} items ({time.time()-t_m:.0f}s)")
    else:
        print("  EASE model not found, skipping")
        EASE_B = None

    print("Loading LightGCN...")
    t_m = time.time()
    lgcn_emb_path = artifacts_dir / "lightgcn_embeddings.pt"
    lgcn_meta_path = artifacts_dir / "lightgcn_meta.json"
    if lgcn_emb_path.exists() and lgcn_meta_path.exists():
        import torch
        lgcn_emb = torch.load(lgcn_emb_path, map_location="cpu", weights_only=True)
        lgcn_meta = _json.loads(lgcn_meta_path.read_text())
        lgcn_u2i = {int(k): int(v) for k, v in lgcn_meta["user2idx"].items()}
        lgcn_i2i = {int(k): int(v) for k, v in lgcn_meta["item2idx"].items()}
        lgcn_nu = lgcn_meta["num_users"]
        print(f"  LightGCN: {lgcn_nu} users, {len(lgcn_i2i)} items ({time.time()-t_m:.0f}s)")
    else:
        print("  LightGCN model not found, skipping")
        lgcn_emb = None

    # ── 6. Get test users (first 10000) ──
    all_test_users = sorted(test.keys())
    n_users = min(10000, len(all_test_users))
    test_users = all_test_users[:n_users]
    print(f"\nEvaluating {n_users} test users...")

    # ── 7. Build C_all ──
    ncf_items = set()
    # Try to get NCF item set from meta
    ncf_meta_path = artifacts_dir / "ncf_v2_meta.json"
    if ncf_meta_path.exists():
        ncf_meta = _json.loads(ncf_meta_path.read_text())
        ncf_items = set(int(k) for k in ncf_meta["item2idx"].keys())
    itemcf_items = set(sims.keys())
    c_all = sorted(itemcf_items & ncf_items) if ncf_items else sorted(itemcf_items)
    c_all_set = set(c_all)
    print(f"  C_all size: {len(c_all)}")

    # ── 8. Per-user evaluation ──
    per_user_results = {"itemcf": [], "ease": [], "lightgcn": []}
    total_interactions = {}  # uid -> total ratings count

    # Build total interaction counts from ratings_by_user
    for uid, items in ratings_by_user.items():
        total_interactions[uid] = len(items)

    # Helper functions
    def itemcf_rec(history, seen, k, per_seed_limit):
        scores = {}
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

    def ease_rec(uid, history, seen, k):
        if EASE_B is None:
            return None
        u_vec = np.zeros(ease_n_items, dtype=np.float32)
        for mid, _r in history:
            if mid in ease_item2idx:
                u_vec[ease_item2idx[mid]] = 1.0
        if u_vec.sum() == 0:
            return None
        scores = EASE_B @ u_vec
        valid = [(mid, float(scores[ease_item2idx[mid]]))
                 for mid in c_all if mid not in seen and mid in ease_item2idx]
        valid.sort(key=lambda x: x[1], reverse=True)
        return [mid for mid, _ in valid[:k]]

    def lightgcn_rec(uid, seen, k):
        if lgcn_emb is None or uid not in lgcn_u2i:
            return None
        u_emb = lgcn_emb[lgcn_u2i[uid]]
        valid = [(mid, lgcn_i2i[mid]) for mid in c_all if mid not in seen and mid in lgcn_i2i]
        if not valid:
            return None
        import torch
        idxs = torch.LongTensor([i for _, i in valid])
        scores = torch.mv(lgcn_emb[lgcn_nu:][idxs], u_emb)
        _, top = torch.topk(scores, min(k, len(scores)))
        return [valid[i][0] for i in top.tolist()]

    from backend.evaluation.metrics import compute_ndcg

    t_eval = time.time()
    for i, uid in enumerate(test_users):
        if uid not in train or uid not in test:
            continue
        history = train[uid]
        test_items = {mid for mid, _r in test[uid]}
        seen = {mid for mid, _r in history}

        if i % 2000 == 0:
            elapsed = time.time() - t_eval
            print(f"  {i}/{n_users} ({elapsed:.0f}s)...")

        # ItemCF
        itemcf_recs = itemcf_rec(history, seen, cfg.k, cfg.per_seed_limit)
        if itemcf_recs:
            ndcg = compute_ndcg(itemcf_recs, test_items, cfg.k)
            per_user_results["itemcf"].append({"user_id": uid, "ndcg": ndcg,
                                               "n_total": total_interactions.get(uid, 0)})

        # EASE
        ease_recs = ease_rec(uid, history, seen, cfg.k)
        if ease_recs:
            ndcg = compute_ndcg(ease_recs, test_items, cfg.k)
            per_user_results["ease"].append({"user_id": uid, "ndcg": ndcg,
                                             "n_total": total_interactions.get(uid, 0)})

        # LightGCN
        lgcn_recs = lightgcn_rec(uid, seen, cfg.k)
        if lgcn_recs:
            ndcg = compute_ndcg(lgcn_recs, test_items, cfg.k)
            per_user_results["lightgcn"].append({"user_id": uid, "ndcg": ndcg,
                                                  "n_total": total_interactions.get(uid, 0)})

    elapsed = time.time() - t_eval
    print(f"  Done: {n_users} users in {elapsed:.0f}s ({n_users/elapsed:.0f} u/s)")

    # ── 9. Compute stratification ──
    print(f"\n{'='*70}")
    print("STRATIFICATION RESULTS (min_user_interactions=16)")
    print(f"{'='*70}")
    print(f"{'Model':<12} {'Warm NDCG@10':<16} {'Hot NDCG@10':<16} {'Warm/Hot':<12} {'Warm n':<10} {'Hot n':<10}")
    print(f"{'-'*70}")

    for model in ["itemcf", "ease", "lightgcn"]:
        users_data = per_user_results[model]
        warm_vals = [u["ndcg"] for u in users_data if 16 <= u["n_total"] <= 20]
        hot_vals = [u["ndcg"] for u in users_data if u["n_total"] > 20]
        w_mean = np.mean(warm_vals) if warm_vals else 0
        h_mean = np.mean(hot_vals) if hot_vals else 0
        ratio = w_mean / h_mean if h_mean > 0 else 0
        print(f"{model:<12} {w_mean:<16.6f} {h_mean:<16.6f} {ratio:<12.4f} {len(warm_vals):<10} {len(hot_vals):<10}")

    # ── 10. Save results ──
    output = {
        "protocol": "min_user_interactions=16",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_users_evaluated": n_users,
        "k": cfg.k,
        "c_all_size": len(c_all),
        "stratification": {}
    }
    for model in ["itemcf", "ease", "lightgcn"]:
        users_data = per_user_results[model]
        warm_vals = [u["ndcg"] for u in users_data if 16 <= u["n_total"] <= 20]
        hot_vals = [u["ndcg"] for u in users_data if u["n_total"] > 20]
        output["stratification"][model] = {
            "warm_n": len(warm_vals),
            "warm_ndcg": float(np.mean(warm_vals)) if warm_vals else 0,
            "hot_n": len(hot_vals),
            "hot_ndcg": float(np.mean(hot_vals)) if hot_vals else 0,
        }

    out_path = artifacts_dir / "stratification_results.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")
    print(f"Total time: {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
