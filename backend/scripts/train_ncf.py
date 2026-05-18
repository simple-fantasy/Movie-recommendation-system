from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import torch
    from torch import nn
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "PyTorch is required for NCF training. Install torch first (CPU is ok). Error: " + str(e)
    )

from backend.app import create_app, db
from backend.app.models import Rating


@dataclass
class TrainConfig:
    embedding_dim: int
    hidden_dim: int
    lr: float
    batch_size: int
    epochs: int
    neg_ratio: int
    seed: int
    min_ratings_per_user: int
    val_ratio: float = 0.1
    early_stop_patience: int = 3
    eval_k: int = 10
    eval_forward_chunk: int = 262_144
    compile_model: bool = False


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
        logits = self.mlp(x).squeeze(-1)
        return logits


def _seed_everything(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _neg_collision_mask(users: np.ndarray, neg: np.ndarray, pos_by_user: dict[int, set[int]]) -> np.ndarray:
    """Boolean mask: True where neg[i] is invalid for users[i]."""
    b = users.shape[0]
    bad = np.empty(b, dtype=np.bool_)
    for i in range(b):
        bad[i] = neg[i] in pos_by_user[int(users[i])]
    return bad


def sample_negatives_column(
    users: np.ndarray,
    pos_by_user: dict[int, set[int]],
    num_items: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """One negative item per row; batch resample only colliding indices."""
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


def sample_eval_negs_row(
    pos_set: set[int],
    pos_i: int,
    num_items: int,
    n_neg: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample n_neg negatives not in pos_set and not equal pos_i (rejection, no full item universe)."""
    row = rng.integers(0, num_items, size=n_neg, dtype=np.int64)
    for _ in range(48):
        bad = np.array([(row[j] in pos_set) or (row[j] == pos_i) for j in range(n_neg)], dtype=np.bool_)
        if not bad.any():
            break
        row[bad] = rng.integers(0, num_items, size=int(bad.sum()), dtype=np.int64)
    return row


def load_interactions(min_ratings_per_user: int, val_ratio: float = 0.1, user_mod: int = 1) -> tuple[np.ndarray, np.ndarray, dict[int, int], dict[int, int]]:
    rows = (
        Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp, Rating.id)
        .order_by(Rating.user_id.asc(), Rating.timestamp.asc(), Rating.id.asc())
        .all()
    )
    by_user: dict[int, list[tuple[int, float, object, int]]] = {}
    for uid, mid, r, ts, rid in rows:
        if int(uid) % user_mod != 0:
            continue
        by_user.setdefault(int(uid), []).append((int(mid), float(r), ts, int(rid)))

    by_user = {uid: items for uid, items in by_user.items() if len(items) >= min_ratings_per_user}
    if not by_user:
        raise SystemExit("no users meet min_ratings_per_user")

    user_ids = sorted(by_user.keys())
    item_ids = sorted({mid for items in by_user.values() for mid, _r, _ts, _rid in items})

    user2idx = {uid: i for i, uid in enumerate(user_ids)}
    item2idx = {mid: i for i, mid in enumerate(item_ids)}

    # Split train/val by user (leave-last-out for each user)
    train_pairs = []
    val_pairs = []
    for uid, items in by_user.items():
        uidx = user2idx[uid]
        # Leave-last-out by interaction time (fallback to row id for stability).
        ordered = sorted(items, key=lambda x: (x[2] is None, x[2], x[3]))
        item_idxs = [(item2idx[mid], float(r)) for mid, r, _ts, _rid in ordered]
        n_val = max(1, int(len(item_idxs) * val_ratio))
        val_items = item_idxs[-n_val:]
        train_items = item_idxs[:-n_val]
        for iidx, _ in train_items:
            train_pairs.append((uidx, iidx))
        for iidx, _ in val_items:
            val_pairs.append((uidx, iidx))

    return np.array(train_pairs, dtype=np.int64), np.array(val_pairs, dtype=np.int64), user2idx, item2idx


def evaluate_ranking(
    model: NCF,
    val_pairs: np.ndarray,
    num_items: int,
    pos_by_user: dict[int, set[int]],
    device: str,
    k: int = 10,
    n_neg_candidates: int = 100,
    forward_chunk: int = 262_144,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Evaluate HR@K / NDCG@K with sampled negatives; batched GPU forward (no O(num_items) set per user)."""
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


def train_one(
    train_pairs: np.ndarray,
    val_pairs: np.ndarray,
    num_users: int,
    num_items: int,
    cfg: TrainConfig,
    device: str,
) -> tuple[NCF, dict[str, float]]:
    if str(device).startswith("cuda") and torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision("high")

    model = NCF(num_users, num_items, cfg.embedding_dim, cfg.hidden_dim).to(device)
    if cfg.compile_model and hasattr(torch, "compile"):
        try:
            model = torch.compile(model, mode="reduce-overhead")  # type: ignore[assignment]
        except Exception as ex:
            print(f"[train_ncf] torch.compile skipped: {ex}")

    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    loss_fn = nn.BCEWithLogitsLoss()

    # build user->positive items for negative sampling
    pos_by_user: dict[int, set[int]] = {}
    for u, i in train_pairs:
        pos_by_user.setdefault(int(u), set()).add(int(i))

    n_pos = train_pairs.shape[0]
    batch_size = cfg.batch_size
    neg_ratio = max(1, int(cfg.neg_ratio))
    rng_train = np.random.default_rng(cfg.seed)
    rng_eval = np.random.default_rng(cfg.seed + 424242)
    use_pin_memory = str(device).startswith("cuda") and torch.cuda.is_available()

    def sample_batch() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        idx = rng_train.integers(0, n_pos, size=(batch_size,))
        pos = train_pairs[idx]
        users = pos[:, 0].astype(np.int64, copy=False)
        pos_items = pos[:, 1].astype(np.int64, copy=False)

        neg_users = np.repeat(users, neg_ratio)
        neg_cols = [sample_negatives_column(users, pos_by_user, num_items, rng_train) for _ in range(neg_ratio)]
        neg_items = np.concatenate(neg_cols, axis=0)

        all_users = np.concatenate([users, neg_users], axis=0)
        all_items = np.concatenate([pos_items, neg_items], axis=0)
        labels = np.concatenate(
            [np.ones(batch_size, dtype=np.float32), np.zeros(neg_users.shape[0], dtype=np.float32)],
            axis=0,
        )

        perm = rng_train.permutation(len(labels))
        all_users = all_users[perm]
        all_items = all_items[perm]
        labels = labels[perm]

        if use_pin_memory:
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

        # Validation
        val_metrics = evaluate_ranking(
            model,
            val_pairs,
            num_items,
            pos_by_user,
            device,
            k=cfg.eval_k,
            n_neg_candidates=100,
            forward_chunk=cfg.eval_forward_chunk,
            rng=rng_eval,
        )
        ndcg = val_metrics["NDCG@K"]

        print({
            "epoch": epoch + 1,
            "loss": avg_loss,
            "HR@K": round(val_metrics["HR@K"], 4),
            "NDCG@K": round(ndcg, 4),
        })

        # Early stopping check
        if ndcg > best_ndcg:
            best_ndcg = ndcg
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= cfg.early_stop_patience:
                print(f"Early stopping at epoch {epoch + 1} (patience={cfg.early_stop_patience})")
                break

    # Load best model
    if best_state is not None:
        model.load_state_dict(best_state)

    final_metrics = {
        "final_loss": avg_loss,
        "best_NDCG@K": round(best_ndcg, 6),
        "eval_k": cfg.eval_k,
    }
    return model, final_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding-dim", type=int, default=32)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--neg-ratio", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-ratings-per-user", type=int, default=10)
    parser.add_argument("--user-mod", type=int, default=1,
                        help="Only keep users where userId %% N == 0 (N=10 keeps ~10%% users)")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument(
        "--eval-forward-chunk",
        type=int,
        default=262_144,
        help="Max (user,item) pairs per GPU forward during validation (larger = fewer launches).",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Use torch.compile (PyTorch 2+); first epoch may be slower while compiling.",
    )
    args = parser.parse_args()

    cfg = TrainConfig(
        embedding_dim=int(args.embedding_dim),
        hidden_dim=int(args.hidden_dim),
        lr=float(args.lr),
        batch_size=int(args.batch_size),
        epochs=int(args.epochs),
        neg_ratio=int(args.neg_ratio),
        seed=int(args.seed),
        min_ratings_per_user=int(args.min_ratings_per_user),
        eval_forward_chunk=int(args.eval_forward_chunk),
        compile_model=bool(args.compile),
    )

    _seed_everything(cfg.seed)

    app = create_app()
    with app.app_context():
        train_pairs, val_pairs, user2idx, item2idx = load_interactions(
            cfg.min_ratings_per_user, val_ratio=cfg.val_ratio, user_mod=int(args.user_mod)
        )
        num_users = len(user2idx)
        num_items = len(item2idx)

        print({
            "users": num_users,
            "items": num_items,
            "train_positives": int(train_pairs.shape[0]),
            "val_positives": int(val_pairs.shape[0]),
        })

        model, metrics = train_one(
            train_pairs,
            val_pairs,
            num_users=num_users,
            num_items=num_items,
            cfg=cfg,
            device=str(args.device),
        )

        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)

        ckpt_path = artifacts / "ncf.pt"
        meta_path = artifacts / "ncf_meta.json"

        model = model.to("cpu")
        torch.save(model.state_dict(), ckpt_path)

        meta = {
            "user2idx": user2idx,
            "item2idx": item2idx,
            "idx2item": {str(v): int(k) for k, v in item2idx.items()},
            "config": cfg.__dict__,
            "train": metrics,
            "num_users": num_users,
            "num_items": num_items,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print({"saved": str(ckpt_path), "meta": str(meta_path)})


if __name__ == "__main__":
    main()
