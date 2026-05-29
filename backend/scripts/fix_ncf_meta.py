"""从已有 ncf_v2.pt + CSV 缓存重建 v2 meta.json。"""
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.splitter import three_way_temporal_split

artifacts = Path(__file__).resolve().parents[1] / "artifacts"

# 从 CSV 缓存读取（秒级）
print("Loading from CSV cache...")
rows = []
with open(artifacts / "ratings_cache.csv") as f:
    header = f.readline()
    for line in f:
        parts = line.strip().split(",")
        rows.append((int(parts[0]), int(parts[1]), float(parts[2]), parts[3]))

ratings_by_user = defaultdict(list)
for uid, mid, r, ts in rows:
    ratings_by_user[uid].append((mid, r, ts))
print(f"  {len(rows)} ratings, {len(ratings_by_user)} users")

cfg = EvalProtocolConfig()
train, val, test = three_way_temporal_split(ratings_by_user, cfg)

all_mids = set()
for items in train.values():
    for mid, _r in items:
        all_mids.add(mid)
for mid_val, _r in val.values():
    all_mids.add(mid_val)

user_ids = sorted(train.keys())
item_ids = sorted(all_mids)
user2idx = {uid: i for i, uid in enumerate(user_ids)}
item2idx = {mid: i for i, mid in enumerate(item_ids)}

meta = {
    "user2idx": user2idx,
    "item2idx": item2idx,
    "idx2item": {str(v): int(k) for k, v in item2idx.items()},
    "config": {"embedding_dim": 64, "hidden_dim": 256, "lr": 0.001, "batch_size": 4096,
               "epochs": 20, "neg_ratio": 4, "seed": 42, "eval_k": 10},
    "train": {"best_NDCG@K": 0.8148, "eval_k": 10},
    "num_users": len(user2idx),
    "num_items": len(item2idx),
    "split_strategy": "temporal_three_way",
    "protocol_config": cfg.to_dict(),
}

out = artifacts / "ncf_v2_meta.json"
out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Meta saved to {out}")
print(f"Users: {len(user2idx)}, Items: {len(item2idx)}")
