"""LightGCN training script for MovieLens 32M.

Architecture: 3-layer graph convolution → mean-pool layers → inner product.
Loss: BPR (Bayesian Personalized Ranking).
"""

# ===== CONFIG =====
CONFIG = {
    "embedding_dim": 64,
    "num_layers": 3,
    "batch_size": 4096,
    "epochs": 50,
    "lr": 0.005,
    "weight_decay": 1e-6,
    "early_stop_patience": 15,
    "eval_every": 1,
    "neg_per_pos": 1,
    "seed": 42,
    "val_ratio": 0.1,
    "min_user_interactions": 5,
    "artifacts_dir": "backend/artifacts",
}

# ===== IMPORTS =====
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn as nn

from backend.app import create_app, db
from backend.app.models import Rating


# ===== DATA LOADING =====

def load_data(min_user_interactions=5):
    """Load ratings, filter users, build contiguous index mappings.

    Returns:
        train_users: np.ndarray [N_train] of contiguous user indices
        train_items: np.ndarray [N_train] of contiguous item indices
        val_pairs: list of (user_idx, item_idx)
        user2idx: dict {original_user_id: contiguous_index}
        item2idx: dict {original_item_id: contiguous_index}
        num_users: int
        num_items: int
    """
    # Try cache first (CSV)
    cache_path = Path(CONFIG["artifacts_dir"]) / "ratings_cache.csv"
    if cache_path.exists():
        import pandas as pd
        df = pd.read_csv(cache_path)
        rows = [(int(r.user_id), int(r.movie_id), float(r.rating),
                 str(r.timestamp) if pd.notna(r.timestamp) else "")
                for r in df.itertuples()]
    else:
        app = create_app()
        with app.app_context():
            rows = (
                Rating.query.with_entities(
                    Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp
                )
                .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
                .all()
            )

    # Group by user, split train/val inline
    val_pairs_uid = []
    train_u_list = []
    train_i_list = []
    all_uids = set()
    all_mids = set()

    current_uid = None
    current_items = []

    def _flush_user():
        nonlocal current_uid, current_items
        if not current_items or len(current_items) < min_user_interactions:
            current_uid = None
            current_items = []
            return
        sorted_items = sorted(current_items, key=lambda x: (x[2] == "", x[2]))
        for mid, _r, _ts in sorted_items[:-1]:
            train_u_list.append(current_uid)
            train_i_list.append(mid)
            all_uids.add(current_uid)
            all_mids.add(mid)
        val_pairs_uid.append((current_uid, sorted_items[-1][0]))
        all_mids.add(sorted_items[-1][0])
        all_uids.add(current_uid)
        current_uid = None
        current_items = []

    for uid, mid, r, ts in rows:
        uid, mid = int(uid), int(mid)
        if uid != current_uid:
            _flush_user()
            current_uid = uid
            current_items = [(mid, float(r), ts)]
        else:
            current_items.append((mid, float(r), ts))
    _flush_user()

    # Build index mappings
    sorted_uids = sorted(all_uids)
    sorted_mids = sorted(all_mids)
    user2idx = {uid: i for i, uid in enumerate(sorted_uids)}
    item2idx = {mid: i for i, mid in enumerate(sorted_mids)}

    # Build numpy arrays with contiguous indices
    train_users = np.array([user2idx[uid] for uid in train_u_list], dtype=np.int64)
    train_items = np.array([item2idx[mid] for mid in train_i_list], dtype=np.int64)

    val_pairs = [(user2idx[uid], item2idx[mid]) for uid, mid in val_pairs_uid]

    return train_users, train_items, val_pairs, user2idx, item2idx, len(sorted_uids), len(sorted_mids)


# ===== ADJACENCY MATRIX =====

def build_normalized_adj(train_users, train_items, num_users, num_items):
    user_idx = train_users.astype(np.int32)
    item_idx = train_items.astype(np.int32)
    N = num_users + num_items

    ratings = np.ones(len(train_users), dtype=np.float32)
    R = sp.csr_matrix((ratings, (user_idx, item_idx)), shape=(num_users, num_items))

    user_degree = np.array(R.sum(axis=1)).flatten()
    item_degree = np.array(R.sum(axis=0)).flatten()

    user_norm = np.where(user_degree > 0, 1.0 / np.sqrt(user_degree), 0.0)
    item_norm = np.where(item_degree > 0, 1.0 / np.sqrt(item_degree), 0.0)

    R_norm = R.multiply(user_norm.reshape(-1, 1)).multiply(item_norm.reshape(1, -1))

    zero_uu = sp.csr_matrix((num_users, num_users))
    zero_ii = sp.csr_matrix((num_items, num_items))
    top = sp.hstack([zero_uu, R_norm])
    bottom = sp.hstack([R_norm.T, zero_ii])
    norm_adj = sp.vstack([top, bottom]).tocsr()

    return norm_adj


def adj_to_tensor(norm_adj, device):
    coo = norm_adj.tocoo()
    indices = torch.LongTensor(np.vstack([coo.row, coo.col]))
    values = torch.FloatTensor(coo.data)
    return torch.sparse.FloatTensor(indices, values, torch.Size(coo.shape)).to(device)


# ===== LightGCN MODEL =====

class LightGCN(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim, num_layers):
        super().__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.N = num_users + num_items
        self.num_layers = num_layers
        self.embedding = nn.Embedding(self.N, embedding_dim)
        nn.init.xavier_uniform_(self.embedding.weight)
        self.cached_emb = None

    def propagate(self, norm_adj_tensor):
        emb = self.embedding.weight
        emb_list = [emb]
        for _ in range(self.num_layers):
            emb = torch.sparse.mm(norm_adj_tensor, emb)
            emb_list.append(emb)
        self.cached_emb = torch.stack(emb_list, dim=0).mean(dim=0)

    def get_scores(self, user_indices, item_indices):
        u_emb = self.cached_emb[user_indices]
        i_emb = self.cached_emb[item_indices]
        return (u_emb * i_emb).sum(dim=1)


# ===== BPR TRAINING =====

def train_one_epoch(model, norm_adj_tensor, train_users, train_items, num_items,
                    optimizer, batch_size, device):
    model.train()
    n_samples = len(train_users)

    print(f"  Propagation...", end=" ", flush=True)
    t0 = time.time()
    E0 = model.embedding.weight
    embs = [E0]
    for layer in range(model.num_layers):
        embs.append(torch.sparse.mm(norm_adj_tensor, embs[-1]))
    with torch.no_grad():
        final_emb = torch.stack(embs, dim=0).mean(dim=0).detach()
    model.cached_emb = final_emb
    print(f"done ({time.time()-t0:.1f}s)")

    perm = torch.randperm(n_samples)
    total_loss = 0.0
    n_batches = 0
    n_batches_total = (n_samples + batch_size - 1) // batch_size
    t0 = time.time()

    accum_grad = torch.zeros_like(E0)

    for start in range(0, n_samples, batch_size):
        end = min(start + batch_size, n_samples)
        batch_idx = perm[start:end]
        B = len(batch_idx)

        user_idx = torch.LongTensor(train_users[batch_idx.numpy()]).to(device)
        pos_idx = torch.LongTensor(train_items[batch_idx.numpy()]).to(device)
        neg_idx = torch.randint(0, num_items, (B,), device=device)

        u_emb = final_emb[user_idx]
        p_emb = final_emb[pos_idx + model.num_users]
        n_emb = final_emb[neg_idx + model.num_users]

        pos_score = (u_emb * p_emb).sum(dim=1)
        neg_score = (u_emb * n_emb).sum(dim=1)
        diff = pos_score - neg_score
        sig = torch.sigmoid(diff)

        grad_coeff = (sig - 1.0) / B
        grad_coeff_n = (1.0 - sig) / B

        grad_u = grad_coeff.unsqueeze(1) * p_emb + grad_coeff_n.unsqueeze(1) * n_emb
        grad_p = grad_coeff.unsqueeze(1) * u_emb
        grad_n = grad_coeff_n.unsqueeze(1) * u_emb

        accum_grad.index_add_(0, user_idx, grad_u)
        accum_grad.index_add_(0, pos_idx + model.num_users, grad_p)
        accum_grad.index_add_(0, neg_idx + model.num_users, grad_n)

        loss_val = -torch.log(sig + 1e-10).mean()
        total_loss += loss_val.item()
        n_batches += 1

        if n_batches % 500 == 0:
            elapsed = time.time() - t0
            eta = elapsed / n_batches * (n_batches_total - n_batches)
            print(f"  [{n_batches}/{n_batches_total}] loss={loss_val.item():.4f}  "
                  f"elapsed={elapsed:.0f}s  ETA={eta:.0f}s", flush=True)

    optimizer.zero_grad()
    model.embedding.weight.grad = accum_grad
    optimizer.step()
    print(f"  grad_norm={accum_grad.norm().item():.4f}  "
          f"grad_mean={accum_grad.abs().mean().item():.8f}")
    print(f"  avg_loss={total_loss/n_batches:.4f}")
    return total_loss / n_batches


def evaluate_val_fast(model, norm_adj_tensor, val_pairs, user2idx, item2idx, num_items, device,
                      n_val_users=2000, k=10, n_neg=99):
    print(f"  Validating on {n_val_users} users...", end=" ", flush=True)
    if model.cached_emb is None:
        model.eval()
        with torch.no_grad():
            E0 = model.embedding.weight
            embs = [E0]
            for _ in range(model.num_layers):
                embs.append(torch.sparse.mm(norm_adj_tensor, embs[-1]))
            model.cached_emb = torch.stack(embs, dim=0).mean(dim=0)
    final_emb = model.cached_emb

    import random
    random.seed(42)
    sampled = random.sample(val_pairs, min(n_val_users, len(val_pairs)))

    neg_samples = torch.randint(0, num_items, (len(sampled), n_neg), device=device)

    hits = 0
    valid = 0
    ndcg_sum = 0.0

    for idx, (uid, pos_iid) in enumerate(sampled):
        if uid not in user2idx or pos_iid not in item2idx:
            continue
        u_idx = user2idx[uid]
        pos_idx = item2idx[pos_iid]

        neg_idx = neg_samples[idx].tolist()
        if pos_idx in neg_idx:
            neg_idx = [x for x in neg_idx if x != pos_idx][:n_neg]

        all_i_idx = torch.LongTensor([pos_idx] + neg_idx[:n_neg]).to(device)
        u_tensor = torch.LongTensor([u_idx] * len(all_i_idx)).to(device)
        all_i_full = all_i_idx + model.num_users

        u_emb = final_emb[u_tensor]
        i_emb = final_emb[all_i_full]
        scores = (u_emb * i_emb).sum(dim=1)
        _, top_indices = torch.topk(scores, min(k, len(scores)))

        rank_of_pos = (top_indices == 0).nonzero(as_tuple=True)
        if len(rank_of_pos[0]) > 0:
            hits += 1
            ndcg_sum += 1.0 / np.log2(rank_of_pos[0][0].item() + 2)
        valid += 1

    print(f"done")
    return {
        'recall': hits / valid if valid > 0 else 0.0,
        'ndcg': ndcg_sum / valid if valid > 0 else 0.0,
        'n_valid': valid
    }


# ===== MAIN =====

if __name__ == "__main__":
    print("Step 1: Loading data...")
    train_users, train_items, val_pairs, user2idx, item2idx, n_users, n_items = load_data(
        CONFIG["min_user_interactions"]
    )
    train_users_np = train_users.astype(np.int64)
    train_items_np = train_items.astype(np.int64)
    train_df = pd.DataFrame({"user_idx": train_users, "item_idx": train_items})
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Val pairs: {len(val_pairs):,}")
    print(f"  Users: {n_users:,}, Items: {n_items:,}")

    print("Step 2: Building adjacency + model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")

    norm_adj = build_normalized_adj(train_users, train_items, n_users, n_items)
    norm_adj_tensor = adj_to_tensor(norm_adj, device)
    print(f"  Adj on device: {norm_adj_tensor.device}, nnz: {norm_adj_tensor._nnz():,}")

    model = LightGCN(n_users, n_items, CONFIG['embedding_dim'], CONFIG['num_layers']).to(device)
    print(f"  Model params: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.Adam([model.embedding.weight], lr=CONFIG['lr'],
                                  weight_decay=CONFIG['weight_decay'])
    artifacts = Path(CONFIG['artifacts_dir'])
    artifacts.mkdir(parents=True, exist_ok=True)

    best_recall = 0.0
    patience = 0
    best_epoch = 0

    print(f"\nTraining: {CONFIG['epochs']} epochs, "
          f"{len(train_users_np)//CONFIG['batch_size']} batches/epoch")

    for epoch in range(CONFIG['epochs']):
        try:
            t0 = time.time()
            loss = train_one_epoch(model, norm_adj_tensor, train_users_np, train_items_np, n_items,
                                   optimizer, CONFIG['batch_size'], device)
            elapsed = time.time() - t0
            print(f"[Epoch {epoch:3d}] loss={loss:.4f}  time={elapsed:.0f}s")

            if epoch % CONFIG['eval_every'] == 0:
                model.eval()
                with torch.no_grad():
                    val_m = evaluate_val_fast(model, norm_adj_tensor, val_pairs, user2idx, item2idx,
                                              n_items, device, n_val_users=2000, n_neg=99)
                print(f"  Val: R@10={val_m['recall']:.4f}  NDCG@10={val_m['ndcg']:.4f}  "
                      f"users={val_m['n_valid']}")

                if val_m['recall'] > best_recall:
                    best_recall = val_m['recall']
                    best_epoch = epoch
                    patience = 0
                    torch.save(model.state_dict(), artifacts / "lightgcn.pt")
                    torch.save(model.cached_emb.detach().cpu(),
                              artifacts / "lightgcn_embeddings.pt")
                else:
                    patience += 1
                    if patience >= CONFIG['early_stop_patience']:
                        print(f"Early stop at epoch {epoch}")
                        break
        except Exception as e:
            print(f"ERROR at epoch {epoch}: {e}")
            torch.cuda.empty_cache()
            import traceback
            traceback.print_exc()
            break

    # Save metadata
    meta = {
        'num_users': n_users,
        'num_items': n_items,
        'embedding_dim': CONFIG['embedding_dim'],
        'num_layers': CONFIG['num_layers'],
        'user2idx': user2idx,
        'item2idx': item2idx,
        'best_recall': best_recall,
        'best_epoch': best_epoch,
    }
    (artifacts / "lightgcn_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )
    print(f"\nSaved to {artifacts}")
    print(f"Best: epoch={best_epoch}, R@10={best_recall:.4f}")
