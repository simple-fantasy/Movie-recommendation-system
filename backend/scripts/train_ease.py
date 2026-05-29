"""EASE: Embarrassingly Shallow Autoencoders for Sparse Data (WWW 2019).
B = P @ G where G = X^T X, P = (G + λI)^(-1), diag(B)=0.
"""
import json, pickle
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import inv

LAM = 500.0

def main():
    artifacts = Path(__file__).resolve().parents[1] / "artifacts"

    # 1. Load ratings
    cache = artifacts / "ratings_cache.pkl"
    if not cache.exists():
        cache = artifacts / "ratings_cache.csv"
    if cache.suffix == ".csv":
        ratings_by_user = {}
        with open(cache) as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                uid = int(parts[0]); mid = int(parts[1])
                ratings_by_user.setdefault(uid, []).append((mid, float(parts[2]), parts[3] if len(parts) > 3 else ""))
    else:
        with open(cache, "rb") as f:
            ratings_by_user = pickle.load(f)

    # 2. Filter items with >= 50 ratings (same as ItemCF)
    item_counts = {}
    for items in ratings_by_user.values():
        for mid, *_ in items:
            item_counts[mid] = item_counts.get(mid, 0) + 1
    item_list = sorted(mid for mid, cnt in item_counts.items() if cnt >= 50)
    item2idx = {mid: i for i, mid in enumerate(item_list)}
    n_items = len(item_list)
    n_users = len(ratings_by_user)
    print(f"Items: {n_items}, Users: {n_users}")

    # 3. Build sparse X (implicit feedback)
    user_list = sorted(ratings_by_user.keys())
    user2idx = {uid: i for i, uid in enumerate(user_list)}
    rows, cols = [], []
    for uid, items in ratings_by_user.items():
        u = user2idx[uid]
        for mid, *_ in items:
            if mid in item2idx:
                rows.append(u); cols.append(item2idx[mid])
    X = csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                   shape=(n_users, n_items), dtype=np.float32)

    # 4-6. G = X^T X, invert, B = P @ G
    print(f"Computing G = X^T X ({n_items}x{n_items})...")
    G = (X.T @ X).toarray().astype(np.float64)
    print(f"Inverting (G + {LAM}I)...")
    P = inv(G + LAM * np.eye(n_items))
    B = P @ G
    np.fill_diagonal(B, 0.0)

    # 7. Save
    np.save(artifacts / "ease_B.npy", B.astype(np.float32))
    meta = {"item_list": item_list, "item2idx": item2idx, "user_list": user_list,
            "user2idx": user2idx, "n_items": n_items, "n_users": n_users, "lam": LAM}
    (artifacts / "ease_meta.json").write_text(json.dumps(meta))
    print(f"Saved B ({B.shape}) and meta")

if __name__ == "__main__":
    main()
