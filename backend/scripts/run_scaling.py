"""数据缩放实验 CLI。

评估 ItemCF / NCF / Hybrid 在不同训练集大小下的表现。

用法:
    python -m backend.scripts.run_scaling --ratios 0.01,0.05,0.25,1.0 --device cuda
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from backend.app import create_app, db
from backend.app.models import Movie, Rating
from backend.app.similarity import compute_item_similarity
from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.splitter import temporal_three_way_split
from backend.evaluation.ncf_inference import NCFModel
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.report import aggregate_summary


def sample_users(ratings_by_user: dict, ratio: float, seed: int) -> dict:
    """随机采样 ratio 比例的用户，返回其全部交互。"""
    rng = np.random.default_rng(seed)
    all_uids = sorted(ratings_by_user.keys())
    n_sample = max(1, int(len(all_uids) * ratio))
    sampled = set(rng.choice(all_uids, size=n_sample, replace=False))
    return {uid: items for uid, items in ratings_by_user.items() if uid in sampled}


def train_ncf_on_subset(
    train_df: pd.DataFrame,
    val_data: dict,
    output_dir: Path,
    ratio_label: str,
    device: str,
) -> tuple[str, str] | None:
    """在子集上训练 NCF，返回 (model_path, meta_path)。"""

    try:
        import torch
        from torch import nn
    except ImportError:
        print("  PyTorch not available — skipping NCF training")
        return None

    # 复用 train_ncf_v2 的训练逻辑
    from backend.scripts.train_ncf_v2 import (
        TrainConfig, _seed_everything, train_one, NCF,
    )

    # 构建 user/item 映射
    user_ids = sorted(set(train_df["user_id"]))
    item_ids = sorted(set(train_df["movie_id"]))
    for items in val_data.values():
        for mid, _r in items:
            if mid not in item_ids:
                item_ids.append(mid)
    item_ids = sorted(set(item_ids))

    user2idx = {uid: i for i, uid in enumerate(user_ids)}  # type: ignore[assignment]
    item2idx = {mid: i for i, mid in enumerate(item_ids)}  # type: ignore[assignment]

    # 构建 train pairs
    train_pairs = []
    for _, row in train_df.iterrows():
        uid = int(row["user_id"])
        mid = int(row["movie_id"])
        if uid in user2idx and mid in item2idx:
            train_pairs.append((user2idx[uid], item2idx[mid]))  # type: ignore[call-overload]

    # 构建 val pairs
    val_pairs = []
    for uid, items in val_data.items():
        if uid not in user2idx:
            continue
        for mid, _r in items:
            if mid in item2idx:
                val_pairs.append((user2idx[uid], item2idx[mid]))  # type: ignore[call-overload]
                break

    train_arr = np.array(train_pairs, dtype=np.int64)
    val_arr = np.array(val_pairs, dtype=np.int64)

    num_users = len(user2idx)
    num_items = len(item2idx)

    print(f"    Training NCF: {num_users} users, {num_items} items, "
          f"{train_arr.shape[0]} train pairs")

    cfg = TrainConfig(
        embedding_dim=32, hidden_dim=128, lr=1e-3, batch_size=4096,
        epochs=10, neg_ratio=1, seed=42, eval_forward_chunk=262144,
        compile_model=False,
    )
    _seed_everything(cfg.seed)

    model, metrics = train_one(train_arr, val_arr, num_users, num_items, cfg, device)

    ckpt = output_dir / f"ncf_scaling_{ratio_label}.pt"
    meta = output_dir / f"ncf_scaling_{ratio_label}_meta.json"

    model = model.to("cpu")
    torch.save(model.state_dict(), str(ckpt))

    meta_dict = {
        "user2idx": user2idx,
        "item2idx": item2idx,
        "idx2item": {str(v): int(k) for k, v in item2idx.items()},
        "config": {
            "embedding_dim": cfg.embedding_dim,
            "hidden_dim": cfg.hidden_dim,
            "lr": cfg.lr,
            "batch_size": cfg.batch_size,
            "epochs": cfg.epochs,
            "neg_ratio": cfg.neg_ratio,
            "seed": cfg.seed,
            "eval_k": cfg.eval_k,
        },
        "train": metrics,
        "num_users": num_users,
        "num_items": num_items,
        "split_strategy": "scaling_experiment",
        "scaling_ratio": ratio_label,
        "protocol_config": EvalProtocolConfig().to_dict(),
    }
    Path(meta).write_text(json.dumps(meta_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"    NDCG@10 (val): {metrics.get('best_NDCG@K', 'N/A')}")
    return str(ckpt), str(meta)


def main():
    parser = argparse.ArgumentParser(description="数据缩放实验")
    parser.add_argument("--ratios", type=str, default="0.01,0.05,0.25,1.0",
                        help="逗号分隔的训练集比例")
    parser.add_argument("--test-users", type=int, default=10000,
                        help="固定测试集用户数")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--output", type=str, default=None,
                        help="输出 JSON 路径")
    args = parser.parse_args()

    ratios = [float(r) for r in args.ratios.split(",")]
    cfg = EvalProtocolConfig()
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    scaling_dir = artifacts_dir / "scaling"
    scaling_dir.mkdir(parents=True, exist_ok=True)

    output_path = args.output or str(artifacts_dir / "scaling_results.json")

    app = create_app()
    with app.app_context():
        t0 = time.time()

        # ── 1. 加载全量数据 ──
        print("Loading full dataset...")
        rows = (
            Rating.query.with_entities(
                Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp
            )
            .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
            .all()
        )
        ratings_by_user: dict[int, list[tuple[int, float, object]]] = {}
        for uid, mid, r, ts in rows:
            ratings_by_user.setdefault(int(uid), []).append((int(mid), float(r), ts))
        print(f"  {len(rows)} ratings, {len(ratings_by_user)} users")

        movie_rows = Movie.query.with_entities(Movie.id, Movie.genres).all()
        movie_genres: dict[int, set[str]] = {}
        for mid, genres_str in movie_rows:
            mid = int(mid)
            if genres_str:
                movie_genres[mid] = set(g.strip() for g in str(genres_str).split("|") if g.strip())
            else:
                movie_genres[mid] = set()

        from sqlalchemy import func
        pop_rows = (
            db.session.query(Rating.movie_id, func.count(Rating.id).label("cnt"))
            .group_by(Rating.movie_id).all()
        )
        popularity = {int(mid): int(cnt) for mid, cnt in pop_rows}

        # ── 2. 固定测试集 ──
        print("\nBuilding fixed test set...")
        full_split = temporal_three_way_split(ratings_by_user, cfg)
        all_test_users = sorted(full_split["test_by_user"].keys())
        rng = np.random.default_rng(cfg.seed)
        n_test = min(args.test_users, len(all_test_users))
        test_users = sorted(rng.choice(all_test_users, size=n_test, replace=False).tolist())
        test_by_user = {uid: full_split["test_by_user"][uid] for uid in test_users}
        print(f"  Fixed test set: {len(test_users)} users")

        # ── 3. 对每种比例评估 ──
        all_results: dict[str, dict] = {}

        for ratio in ratios:
            ratio_label = f"{int(ratio * 100)}pct" if ratio < 1.0 else "100pct"
            print(f"\n{'=' * 60}")
            print(f"Ratio: {ratio_label} ({ratio * 100:.0f}% users)")
            print(f"{'=' * 60}")

            t_ratio = time.time()

            # 采样训练用户
            sampled = sample_users(
                {uid: items for uid, items in ratings_by_user.items() if uid not in set(test_users)},
                ratio, cfg.seed,
            )
            print(f"  Train users: {len(sampled)}")

            # 只用采样的用户 + 固定 test users 构建训练数据
            train_ratings = sampled
            # 也需要 train_by_user（训练阶段的数据）
            train_data_for_split = {**sampled, **{uid: ratings_by_user[uid] for uid in test_users}}
            ratio_split = temporal_three_way_split(train_data_for_split, cfg)
            train_by_user = {
                uid: items for uid, items in ratio_split["train_by_user"].items()
                if uid in sampled  # 只保留采样用户的训练数据
            }
            train_df = pd.DataFrame([
                {"user_id": uid, "movie_id": mid, "rating": r}
                for uid, items in train_by_user.items()
                for mid, r in items
            ], columns=["user_id", "movie_id", "rating"])
            print(f"  Train ratings: {len(train_df)}")

            # ItemCF sims
            t_sim = time.time()
            raw_sims = compute_item_similarity(train_df, topk=cfg.sim_topk_per_movie, normalize=True)
            print(f"  ItemCF sims: {len(raw_sims)} movies ({time.time() - t_sim:.0f}s)")

            # NCF 训练
            val_by_user = {
                uid: ratio_split["val_by_user"].get(uid, [])
                for uid in sampled if uid in ratio_split["val_by_user"]
            }
            ncf_result = train_ncf_on_subset(
                train_df, val_by_user, scaling_dir, ratio_label, args.device,
            )

            # 加载 NCF（或回退到 None）
            ncf_model = None
            if ncf_result:
                ncf_model = NCFModel(ncf_result[0], ncf_result[1])

            # 评估
            engine = EvaluationEngine(cfg)
            engine.set_data(train_by_user, test_by_user, movie_genres, popularity)
            engine.set_sims(raw_sims)
            if ncf_model:
                engine.set_ncf(ncf_model)
            engine.prepare()

            models_to_run = ["itemcf"]
            if ncf_model:
                models_to_run.extend(["ncf", "hybrid"])

            result = engine.run(models=models_to_run, users=test_users)
            summary = aggregate_summary(result["results"])

            all_results[ratio_label] = {
                "train_users": len(sampled),
                "train_ratings": len(train_df),
                "test_users": len(test_users),
                "itemcf_items": len(raw_sims),
                "ncf_users": ncf_model.num_users if ncf_model else 0,
                "ncf_items": ncf_model.num_items if ncf_model else 0,
                "c_all_size": len(engine._C_all),
                "runtime_seconds": time.time() - t_ratio,
                "models": _to_json_safe(summary),
            }

            # 打印当前结果
            for model_name, metrics_dict in summary.items():
                r10 = metrics_dict.get("recall_at_10", 0)
                n10 = metrics_dict.get("ndcg_at_10", 0)
                print(f"  {model_name:<12}: R@10={r10:.4f}  NDCG@10={n10:.4f}")

        # ── 4. 写输出 ──
        output = {
            "meta": {
                "experiment": "data_scaling",
                "dataset": "MovieLens 32M",
                "ratios": [f"{int(r*100)}pct" if r < 1.0 else "100pct" for r in ratios],
                "test_users": len(test_users),
                "total_runtime_seconds": time.time() - t0,
                "config": cfg.to_dict(),
            },
            "results": all_results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nResults: {output_path}")
        print(f"Total: {time.time() - t0:.0f}s")


def _to_json_safe(obj):
    """递归转换 numpy → Python 原生。"""
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


if __name__ == "__main__":
    main()
