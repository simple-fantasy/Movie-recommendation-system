"""NCF 模型重训脚本 (v2)——使用严格三层时间切分。

与 train_ncf.py 的差异:
- 使用 evaluation/splitter.py 的三层切分（train/val/test 隔离）
- 将 protocol_config 写入 meta.json（评估脚本启动时校验）
- 输出到 ncf_v2.pt / ncf_v2_meta.json（不覆盖旧文件）

用法:
    python -m backend.scripts.train_ncf_v2 --device cuda --epochs 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from backend.app import create_app, db
from backend.app.models import Rating
from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.splitter import three_way_temporal_split

# ── NCF 模型定义（与 ncf_engine.py 保持一致） ──


class NCF(nn.Module):
    def __init__(self, num_users: int, num_items: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.user_emb = nn.Embedding(num_users, embedding_dim)
        self.item_emb = nn.Embedding(num_items, embedding_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, user_idx: torch.Tensor, item_idx: torch.Tensor) -> torch.Tensor:
        u = self.user_emb(user_idx)
        i = self.item_emb(item_idx)
        x = torch.cat([u, i], dim=-1)
        return self.mlp(x).squeeze(-1)


# ── 训练配置 ──


class TrainConfig:
    def __init__(self, **kwargs):
        self.embedding_dim = kwargs.get("embedding_dim", 32)
        self.hidden_dim = kwargs.get("hidden_dim", 128)
        self.lr = kwargs.get("lr", 1e-3)
        self.batch_size = kwargs.get("batch_size", 4096)
        self.epochs = kwargs.get("epochs", 10)
        self.neg_ratio = kwargs.get("neg_ratio", 1)
        self.seed = kwargs.get("seed", 42)
        self.eval_k = kwargs.get("eval_k", 10)
        self.eval_forward_chunk = kwargs.get("eval_forward_chunk", 262144)
        self.compile_model = kwargs.get("compile_model", False)


# ── 负采样 ──


def _seed_everything(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _neg_collision_mask(users: np.ndarray, neg: np.ndarray, pos_by_user: dict[int, set[int]]) -> np.ndarray:
    b = users.shape[0]
    bad = np.empty(b, dtype=np.bool_)
    for i in range(b):
        bad[i] = neg[i] in pos_by_user[int(users[i])]
    return bad


def sample_negatives_column(users: np.ndarray, pos_by_user: dict[int, set[int]],
                            num_items: int, rng: np.random.Generator) -> np.ndarray:
    users = np.asarray(users, dtype=np.int64)
    b = users.shape[0]
    neg = rng.integers(0, num_items, size=b, dtype=np.int64)
    for _ in range(48):
        bad = _neg_collision_mask(users, neg, pos_by_user)
        if not bad.any():
            break
        n_bad = int(bad.sum())
        neg[bad] = rng.integers(0, num_items, size=n_bad, dtype=np.int64)
    return neg


def sample_eval_negs_row(pos_set: set[int], pos_i: int, num_items: int,
                         n_neg: int, rng: np.random.Generator) -> np.ndarray:
    row = rng.integers(0, num_items, size=n_neg, dtype=np.int64)
    for _ in range(48):
        bad = np.array([(row[j] in pos_set) or (row[j] == pos_i) for j in range(n_neg)], dtype=np.bool_)
        if not bad.any():
            break
        row[bad] = rng.integers(0, num_items, size=int(bad.sum()), dtype=np.int64)
    return row


# ── 验证 ──


def evaluate_ranking(model: nn.Module, val_pairs: np.ndarray, num_items: int,
                     pos_by_user: dict[int, set[int]], device: str, k: int = 10,
                     n_neg_candidates: int = 100, forward_chunk: int = 262144,
                     rng: np.random.Generator | None = None) -> dict[str, float]:
    if rng is None:
        rng = np.random.default_rng()
    model.eval()
    n_val = val_pairs.shape[0]
    if n_val == 0:
        return {"HR@K": 0.0, "NDCG@K": 0.0}

    c = 1 + n_neg_candidates
    k_eff = min(int(k), c)
    users_col = val_pairs[:, 0].astype(np.int64, copy=False)
    pos_col = val_pairs[:, 1].astype(np.int64, copy=False)

    negs = np.empty((n_val, n_neg_candidates), dtype=np.int64)
    for i in range(n_val):
        u = int(users_col[i])
        pos_i = int(pos_col[i])
        pos_set = pos_by_user.get(u, set())
        negs[i] = sample_eval_negs_row(pos_set, pos_i, num_items, n_neg_candidates, rng)

    u_flat = np.repeat(users_col, c)
    i_flat = np.empty(n_val * c, dtype=np.int64)
    i_flat[0::c] = pos_col
    for j in range(n_neg_candidates):
        i_flat[(j + 1) :: c] = negs[:, j]

    scores_chunks: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, u_flat.shape[0], forward_chunk):
            end = min(start + forward_chunk, u_flat.shape[0])
            ut = torch.from_numpy(u_flat[start:end]).to(device=device, dtype=torch.long, non_blocking=True)
            it = torch.from_numpy(i_flat[start:end]).to(device=device, dtype=torch.long, non_blocking=True)
            logits = model(ut, it)
            scores_chunks.append(logits.detach().float().cpu().numpy())

    scores = np.concatenate(scores_chunks).reshape(n_val, c)
    row_idx = np.arange(n_val, dtype=np.int64)[:, None]
    part = np.argpartition(-scores, kth=k_eff - 1, axis=1)[:, :k_eff]
    part_scores = scores[row_idx, part]
    order = np.argsort(-part_scores, axis=1)
    topk_cols = part[row_idx, order]
    match = topk_cols == 0
    in_topk = match.any(axis=1)
    ranks = match.argmax(axis=1)
    ndcg_vals = np.where(in_topk, 1.0 / np.log2(ranks.astype(np.float64) + 2.0), 0.0)

    return {"HR@K": float(in_topk.mean()), "NDCG@K": float(ndcg_vals.mean())}


# ── 训练循环 ──


def train_one(train_pairs: np.ndarray, val_pairs: np.ndarray, num_users: int,
              num_items: int, cfg: TrainConfig, device: str) -> tuple[NCF, dict]:
    if str(device).startswith("cuda") and torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision("high")

    model = NCF(num_users, num_items, cfg.embedding_dim, cfg.hidden_dim).to(device)
    if cfg.compile_model and hasattr(torch, "compile"):
        try:
            model = torch.compile(model, mode="reduce-overhead")
        except Exception as ex:
            print(f"[train_ncf_v2] torch.compile skipped: {ex}")

    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    loss_fn = nn.BCEWithLogitsLoss()

    pos_by_user: dict[int, set[int]] = {}
    for u, i in train_pairs:
        pos_by_user.setdefault(int(u), set()).add(int(i))

    n_pos = train_pairs.shape[0]
    batch_size = cfg.batch_size
    neg_ratio = max(1, int(cfg.neg_ratio))
    rng_train = np.random.default_rng(cfg.seed)
    rng_eval = np.random.default_rng(cfg.seed + 424242)
    use_pin = str(device).startswith("cuda") and torch.cuda.is_available()

    def sample_batch():
        idx = rng_train.integers(0, n_pos, size=(batch_size,))
        pos = train_pairs[idx]
        users = pos[:, 0].astype(np.int64, copy=False)
        pos_items = pos[:, 1].astype(np.int64, copy=False)

        neg_users = np.repeat(users, neg_ratio)
        neg_cols = [sample_negatives_column(users, pos_by_user, num_items, rng_train) for _ in range(neg_ratio)]
        neg_items = np.concatenate(neg_cols, axis=0)

        all_users = np.concatenate([users, neg_users], axis=0)
        all_items = np.concatenate([pos_items, neg_items], axis=0)
        labels = np.concatenate([
            np.ones(batch_size, dtype=np.float32),
            np.zeros(neg_users.shape[0], dtype=np.float32),
        ], axis=0)

        perm = rng_train.permutation(len(labels))
        all_users, all_items, labels = all_users[perm], all_items[perm], labels[perm]

        if use_pin:
            u_t = torch.as_tensor(all_users, dtype=torch.long).pin_memory().to(device, non_blocking=True)
            i_t = torch.as_tensor(all_items, dtype=torch.long).pin_memory().to(device, non_blocking=True)
            y_t = torch.as_tensor(labels, dtype=torch.float32).pin_memory().to(device, non_blocking=True)
            return u_t, i_t, y_t
        return (
            torch.tensor(all_users, dtype=torch.long, device=device),
            torch.tensor(all_items, dtype=torch.long, device=device),
            torch.tensor(labels, dtype=torch.float32, device=device),
        )

    steps_per_epoch = max(int(n_pos / batch_size), 1)
    best_ndcg = -1.0
    best_state = None
    patience_counter = 0

    for epoch in range(cfg.epochs):
        model.train()
        losses = []
        for _ in range(steps_per_epoch):
            u, it, y = sample_batch()
            opt.zero_grad(set_to_none=True)
            logits = model(u, it)
            loss = loss_fn(logits, y)
            loss.backward()
            opt.step()
            losses.append(float(loss.detach().cpu().item()))
        avg_loss = float(np.mean(losses))

        val_metrics = evaluate_ranking(
            model, val_pairs, num_items, pos_by_user, device,
            k=cfg.eval_k, n_neg_candidates=100,
            forward_chunk=cfg.eval_forward_chunk, rng=rng_eval,
        )
        ndcg = val_metrics["NDCG@K"]

        print({
            "epoch": epoch + 1,
            "loss": avg_loss,
            "HR@K": round(val_metrics["HR@K"], 4),
            "NDCG@K": round(ndcg, 4),
        })

        if ndcg > best_ndcg:
            best_ndcg = ndcg
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= 3:
                print(f"Early stopping at epoch {epoch + 1}")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    return model, {"final_loss": avg_loss, "best_NDCG@K": round(best_ndcg, 6), "eval_k": cfg.eval_k}


# ── 主函数 ──


def main() -> None:
    parser = argparse.ArgumentParser(description="NCF v2 重训（三层时间切分）")
    parser.add_argument("--embedding-dim", type=int, default=32)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--neg-ratio", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--eval-forward-chunk", type=int, default=262144)
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args()

    cfg = TrainConfig(
        embedding_dim=int(args.embedding_dim),
        hidden_dim=int(args.hidden_dim),
        lr=float(args.lr),
        batch_size=int(args.batch_size),
        epochs=int(args.epochs),
        neg_ratio=int(args.neg_ratio),
        seed=int(args.seed),
        eval_forward_chunk=int(args.eval_forward_chunk),
        compile_model=bool(args.compile),
    )
    _seed_everything(cfg.seed)

    # 协议配置（用于写入 meta.json + 评估脚本校验）
    proto_cfg = EvalProtocolConfig()

    app = create_app()
    with app.app_context():
        print("Loading ratings from DB...")
        rows = (
            Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp)
            .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
            .all()
        )
        ratings_by_user: dict[int, list[tuple[int, float, object]]] = {}
        for uid, mid, r, ts in rows:
            ratings_by_user.setdefault(int(uid), []).append((int(mid), float(r), ts))
        print(f"  {len(rows)} ratings, {len(ratings_by_user)} users")

        # 三层切分（新 API：返回三个独立 dict）
        train_data, val_data, test_data = three_way_temporal_split(ratings_by_user, proto_cfg)
        print(f"  Train users: {len(train_data)}")
        print(f"  Val users:   {len(val_data)}")
        print(f"  Test users:  {len(test_data)} (NOT used in training)")

        # 构建 user/item 索引映射
        all_mids: set[int] = set()
        for items in train_data.values():
            for mid, _r in items:
                all_mids.add(mid)
        for mid, _r in val_data.values():
            all_mids.add(mid)

        user_ids = sorted(train_data.keys())
        item_ids = sorted(all_mids)
        user2idx = {uid: i for i, uid in enumerate(user_ids)}
        item2idx = {mid: i for i, mid in enumerate(item_ids)}

        # 构建 train/val pairs
        import numpy as np
        train_pairs_list = []
        val_pairs_list = []
        pos_by_user = {}
        for uid, train_items in train_data.items():
            if uid not in user2idx:
                continue
            uidx = user2idx[uid]
            pos_set = set()
            for mid, _r in train_items:
                if mid in item2idx:
                    iidx = item2idx[mid]
                    train_pairs_list.append((uidx, iidx))
                    pos_set.add(iidx)
            if pos_set:
                pos_by_user[uidx] = pos_set
        for uid, (val_mid, val_r) in val_data.items():
            if uid in user2idx and val_mid in item2idx:
                val_pairs_list.append((user2idx[uid], item2idx[val_mid]))
        train_arr = np.array(train_pairs_list, dtype=np.int64)
        val_arr = np.array(val_pairs_list, dtype=np.int64)
        num_users = len(user2idx)
        num_items = len(item2idx)

        print({
            "users": num_users,
            "items": num_items,
            "train_positives": int(train_arr.shape[0]),
            "val_positives": int(val_arr.shape[0]),
        })

        # 训练
        model, metrics = train_one(
            train_arr, val_arr, num_users=num_users, num_items=num_items,
            cfg=cfg, device=str(args.device),
        )

        # 保存
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)

        ckpt_path = artifacts / "ncf_v2.pt"
        meta_path = artifacts / "ncf_v2_meta.json"

        model = model.to("cpu")
        torch.save(model.state_dict(), ckpt_path)

        meta = {
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
            "split_strategy": "temporal_three_way",
            "protocol_config": proto_cfg.to_dict(),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print({"saved": str(ckpt_path), "meta": str(meta_path)})


if __name__ == "__main__":
    main()
