# DEPRECATED since 2026-05-25 — use backend.evaluation.engine instead.
"""Unified recommendation model evaluation framework.

Supports:
- ItemCF, NCF, Hybrid models
- Fair comparison (shared candidate pool) and native retrieval modes
- K-fold temporal cross-validation (K=1 = leave-last-out)
- Accuracy + diversity + novelty + coverage + serendipity metrics
- Statistical tests (Wilcoxon, Cohen's d, Bonferroni-Holm)
- User stratification (Cold / Warm / Hot)
- Ablation studies

Usage:
    from backend.app.evaluator import EvalConfig, EvaluationEngine
    engine = EvaluationEngine(EvalConfig(k=10, fair_mode=True))
    engine.load_data()
    results = engine.run(["itemcf", "ncf", "hybrid"])
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import time
from typing import Any

import numpy as np
import pandas as pd
import torch

from backend.app.ncf_engine import ncf_engine
from backend.app.similarity import compute_item_similarity

# LightGCN lazy-load globals
_lightgcn_loaded = False
_lightgcn_user_embs = None
_lightgcn_item_embs = None
_lightgcn_user2idx = None
_lightgcn_item2idx = None

# EASE globals
_ease_loaded = False
_ease_B = None
_ease_item2idx = None
_ease_item_list = None
_ease_n_items = None
_lightgcn_num_users = None
_lightgcn_item2idx_array = None  # precomputed tensor mapping


def _ensure_lightgcn():
    global _lightgcn_loaded, _lightgcn_user_embs, _lightgcn_item_embs
    global _lightgcn_user2idx, _lightgcn_item2idx, _lightgcn_num_users
    if _lightgcn_loaded:
        return True
    import json
    from pathlib import Path
    artifacts = Path(__file__).resolve().parents[1] / "artifacts"
    emb_path = artifacts / "lightgcn_embeddings.pt"
    meta_path = artifacts / "lightgcn_meta.json"
    if not emb_path.exists() or not meta_path.exists():
        return False
    try:
        emb = torch.load(emb_path, map_location="cpu", weights_only=True)
        meta = json.loads(meta_path.read_text())
        _lightgcn_user2idx = {int(k): v for k, v in meta["user2idx"].items()}
        _lightgcn_item2idx = {int(k): v for k, v in meta["item2idx"].items()}
        _lightgcn_num_users = meta["num_users"]
        _lightgcn_user_embs = emb[:_lightgcn_num_users]
        _lightgcn_item_embs = emb[_lightgcn_num_users:]
        _lightgcn_loaded = True
        return True
    except Exception as e:
        print(f"LightGCN load failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# Data Structures
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class EvalConfig:
    """Evaluation configuration."""
    k: int = 10
    like_threshold: float = 4.0
    min_ratings: int = 10
    per_seed_limit: int = 50
    sim_topk_per_movie: int = 50
    recall_k: int = 100
    ncf_candidate_pool_size: int = 1000
    seed: int = 42
    fair_mode: bool = True
    full_ranking: bool = False      # True = all models rank ALL unseen items (scheme X)
    n_folds: int = 1                 # 1 = leave-last-out
    popularity_buckets: int = 0      # 0=uniform sampling (fast); 5=quantile stratified
    n_test_users: int = 0          # 0=all users, N=sample N random users
    models: list[str] = field(default_factory=lambda: ["itemcf", "ncf", "lightgcn", "ease", "hybrid"])


@dataclass
class Metrics:
    """Evaluation metrics for a single model / run.

    Backward-compatible with existing evaluation_results.json schema.
    New fields (ils, genre_diversity, novelty, tail_coverage, serendipity,
    per_user_metrics) default to 0/None so old consumers don't break.
    """
    model: str
    # Accuracy
    precision_at_k: float
    recall_at_k: float
    map_at_k: float
    ndcg_at_k: float
    mrr_at_k: float
    # Diversity
    ils_at_k: float = 0.0
    genre_diversity_at_k: float = 0.0
    # Novelty
    novelty_at_k: float = 0.0
    # Coverage
    coverage: float = 0.0
    tail_coverage: float = 0.0
    # Serendipity
    serendipity_at_k: float = 0.0
    # Meta
    users_evaluated: int = 0
    avg_recs: float = 0.0
    avg_log_popularity: float = 0.0
    k: int = 10
    recall_k: int | None = None
    per_seed_limit: int | None = None
    runtime_seconds: float = 0.0
    params: dict[str, Any] = field(default_factory=dict)
    per_user_metrics: dict | None = None  # {uid: {metric_name: value, ...}}


# ═══════════════════════════════════════════════════════════════════════
# Metric Functions (pure, with mathematical formulas)
# ═══════════════════════════════════════════════════════════════════════

def compute_hit_rank(recs: list[int], test_items: set[int]) -> int | None:
    """Return the 0-based rank of the first hit, or None if no hit."""
    for idx, mid in enumerate(recs):
        if mid in test_items:
            return idx
    return None


def compute_precision(recs: list[int], test_items: set[int], k: int) -> float:
    """P@K = |R_u ∩ T_u| / K"""
    if k <= 0:
        return 0.0
    hits = sum(1 for mid in recs[:k] if mid in test_items)
    return hits / float(k)


def compute_recall(recs: list[int], test_items: set[int], k: int) -> float:
    """R@K = |R_u ∩ T_u| / |T_u|

    When |T_u| = 1 (single test item), R@K = HitRate@K.
    """
    if not test_items:
        return 0.0
    hits = sum(1 for mid in recs[:k] if mid in test_items)
    return hits / float(len(test_items))


def compute_ndcg(recs: list[int], test_items: set[int], k: int) -> float:
    """NDCG@K = (1 / IDCG) * Σ_{i=1}^{K} (2^{rel_i} - 1) / log2(i + 2)

    Relevance is binary: rel_i = 1 if item i ∈ T_u, else 0.
    IDCG = 1 for single test item (ideal ranking places it at position 1).
    """
    dcg = 0.0
    for i, mid in enumerate(recs[:k]):
        rel = 1.0 if mid in test_items else 0.0
        dcg += (2.0 ** rel - 1.0) / np.log2(i + 2)
    n_test = len(test_items)
    if n_test == 0:
        return 0.0
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(n_test, k)))
    return dcg / idcg if idcg > 0 else 0.0


def compute_mrr(recs: list[int], test_items: set[int]) -> float:
    """MRR = 1 / rank_of_first_hit  (0 if no hit)"""
    rank = compute_hit_rank(recs, test_items)
    if rank is None:
        return 0.0
    return 1.0 / float(rank + 1)


def compute_map(recs: list[int], test_items: set[int], k: int) -> float:
    """MAP@K = (1 / |T_u|) * Σ_{i=1}^{K} P@i * rel_i"""
    if not test_items:
        return 0.0
    hits = 0
    ap = 0.0
    for i, mid in enumerate(recs[:k]):
        if mid in test_items:
            hits += 1
            ap += hits / float(i + 1)
    return ap / float(len(test_items))


def compute_ils(recs: list[int], item_sims: dict[int, list[tuple[int, float]]], k: int) -> float:
    """ILS = (2 / (K(K-1))) * Σ_{i<j} sim(i, j)

    Intra-List Similarity: mean pairwise cosine similarity within the
    recommended list. Lower ILS = more diverse recommendations.
    ItemCF similarity scores serve as the similarity function.
    """
    items = recs[:k]
    if len(items) < 2:
        return 0.0
    total = 0.0
    count = 0
    for a in range(len(items)):
        neighbors = dict(item_sims.get(items[a], []))
        for b in range(a + 1, len(items)):
            sim = neighbors.get(items[b], 0.0)
            total += sim
            count += 1
    return total / float(count) if count > 0 else 0.0


def compute_genre_diversity(
    recs: list[int], movie_genres: dict[int, set[str]], k: int
) -> float:
    """GenreDiv@K = |unique genres in R_u| / K

    Higher = more genre-diverse recommendation list.
    """
    items = recs[:k]
    if not items:
        return 0.0
    all_genres: set[str] = set()
    for mid in items:
        all_genres.update(movie_genres.get(mid, set()))
    return len(all_genres) / float(k)


def compute_novelty(
    recs: list[int], popularity: dict[int, int], n_users: int, k: int
) -> float:
    """Novelty@K = -(1/K) * Σ_i log2(pop(i) / N)

    Higher = recommended items are less popular (more novel).
    pop(i) = number of users who rated item i.
    N = total number of users (for probability normalization).
    """
    items = recs[:k]
    if not items or n_users <= 0:
        return 0.0
    total = 0.0
    for mid in items:
        p = max(popularity.get(mid, 1), 1) / float(n_users)
        total += -np.log2(p)
    return total / float(k)


def compute_serendipity(
    recs: list[int],
    test_items: set[int],
    history_genres: set[str],
    movie_genres: dict[int, set[str]],
    k: int,
) -> float:
    """Serendipity@K = |R_u ∩ (unexpected ∩ relevant)| / K

    An item is "unexpected" if its genres have Jaccard similarity < 0.3
    with the user's history genres (i.e., it's outside their usual taste).
    An item is "relevant" if it's in the test set.
    """
    items = recs[:k]
    if not items:
        return 0.0
    serendip_count = 0
    for mid in items:
        if mid not in test_items:
            continue
        item_g = movie_genres.get(mid, set())
        if not history_genres or not item_g:
            continue
        jaccard = len(history_genres & item_g) / len(history_genres | item_g)
        if jaccard < 0.3:
            serendip_count += 1
    return serendip_count / float(k)


def compute_coverage(all_recs: set[int], n_items: int) -> float:
    """Catalog Coverage = |∪R_u| / |I|"""
    if n_items == 0:
        return 0.0
    return float(len(all_recs)) / float(n_items)


def compute_tail_coverage(all_recs: set[int], tail_items: set[int]) -> float:
    """Tail Coverage = |∪R_u ∩ I_tail| / |I_tail|

    I_tail = bottom 80% items by popularity (the long tail).
    """
    if not tail_items:
        return 0.0
    return float(len(all_recs & tail_items)) / float(len(tail_items))


# ═══════════════════════════════════════════════════════════════════════
# Recommendation Functions (migrated from evaluate_models.py)
# ═══════════════════════════════════════════════════════════════════════

def itemcf_recommend(
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    k: int,
    per_seed_limit: int,
) -> list[int]:
    """ItemCF: weighted-sum scoring over all unseen items."""
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


def itemcf_recommend_from_pool(
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    candidate_pool: list[int],
    k: int,
    per_seed_limit: int,
) -> list[int]:
    """ItemCF ranking restricted to a given candidate pool (fair comparison)."""
    scores: dict[int, float] = {}
    pool_set = set(candidate_pool)
    for movie_id, r in history:
        neighbors = sims.get(movie_id, [])[:per_seed_limit]
        for sid, sim in neighbors:
            if sid in seen or sid not in pool_set:
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
    """ItemCF recall: larger candidate set for downstream reranking."""
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
    """NCF: rank candidate items by predicted score."""
    if not ncf_engine.is_ready():
        return []
    ranked = ncf_engine.rank(user_id, candidate_ids, top_k=k)
    return [mid for mid, _ in ranked]


def lightgcn_recommend(user_id: int, candidate_ids: list[int], k: int) -> list[int]:
    """LightGCN: user_emb · item_emb → Top-K (with lazy model load)."""
    if not _ensure_lightgcn():
        return []
    if user_id not in _lightgcn_user2idx:
        return []
    u_idx = _lightgcn_user2idx[user_id]
    u_emb = _lightgcn_user_embs[u_idx]

    # Vectorized: pre-built mapping array avoids Python loop over 80K items
    candidate_tensor = torch.LongTensor(candidate_ids)
    # _item2idx_array[idx] = lightgcn_idx or -1, built once on first call
    global _lightgcn_item2idx_array
    if _lightgcn_item2idx_array is None:
        max_id = max(_lightgcn_item2idx.keys()) + 1
        _lightgcn_item2idx_array = torch.full((max_id,), -1, dtype=torch.long)
        for mid, idx in _lightgcn_item2idx.items():
            _lightgcn_item2idx_array[mid] = idx

    # Filter candidates that exist in LightGCN
    valid_mask = candidate_tensor < len(_lightgcn_item2idx_array)
    mapped = _lightgcn_item2idx_array[candidate_tensor[valid_mask]]
    item_mask = mapped >= 0
    if not item_mask.any():
        return []

    valid_mids_tensor = candidate_tensor[valid_mask][item_mask]
    valid_idxs = mapped[item_mask]

    i_embs = _lightgcn_item_embs[valid_idxs]
    scores = torch.mv(i_embs, u_emb)
    _, top_idx = torch.topk(scores, min(k, len(scores)))
    return valid_mids_tensor[top_idx].tolist()


_ease_loaded = False
_ease_B = None
_ease_item2idx = None
_ease_item_list = None


def _ensure_ease():
    global _ease_loaded, _ease_B, _ease_item2idx, _ease_item_list
    if _ease_loaded:
        return True
    import json
    from pathlib import Path
    artifacts = Path(__file__).resolve().parents[1] / "artifacts"
    b_path = artifacts / "ease_B.npy"
    meta_path = artifacts / "ease_meta.json"
    if not b_path.exists() or not meta_path.exists():
        return False
    try:
        _ease_B = np.load(b_path)
        meta = json.loads(meta_path.read_text())
        _ease_item2idx = {int(k): v for k, v in meta["item2idx"].items()}
        _ease_item_list = meta["item_list"]
        _ease_loaded = True
        return True
    except Exception as e:
        print(f"EASE load failed: {e}")
        return False


def ease_recommend(user_id: int, candidate_ids: list[int], k: int,
                   user_history: list[int] | None = None) -> list[int]:
    """EASE: B @ x_u → Top-K using user interaction vector."""
    if not _ensure_ease():
        return []
    u_vec = np.zeros(len(_ease_item_list), dtype=np.float32)
    for mid in (user_history or []):
        if mid in _ease_item2idx:
            u_vec[_ease_item2idx[mid]] = 1.0
    if u_vec.sum() == 0:
        return []
    scores = _ease_B @ u_vec
    valid = [(mid, scores[_ease_item2idx[mid]])
             for mid in candidate_ids if mid in _ease_item2idx]
    if not valid:
        return []
    valid.sort(key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in valid[:k]]


_random_rng = np.random.default_rng(42)


def random_recommend(candidate_ids: list[int], seen: set[int], k: int,
                     rng: np.random.Generator | None = None) -> list[int]:
    """Random baseline: randomly pick k unseen items."""
    if rng is None:
        rng = np.random.default_rng(42)
    pool = [mid for mid in candidate_ids if mid not in seen]
    if not pool:
        return []
    n = min(k, len(pool))
    return rng.choice(pool, size=n, replace=False).tolist()


def sample_ncf_candidates(
    all_item_ids: set[int],
    seen: set[int],
    candidate_pool_size: int,
    rng: np.random.Generator,
    must_include: set[int] | None = None,
    popularity: dict[int, int] | None = None,
    popularity_buckets: int = 5,
    pop_sorted: list[int] | None = None,
) -> list[int]:
    """Sample candidate pool from unseen items.

    When popularity is provided and popularity_buckets > 0, items are
    divided into quantile buckets and sampled evenly from each (stratified
    by popularity). This prevents the candidate pool from being dominated
    by popular items, ensuring fair evaluation across the popularity spectrum.

    When must_include is provided, those items are guaranteed to be in the
    returned list (critical: the test item must be reachable by the model).
    """
    must = set(must_include or [])
    unseen = [i for i in (all_item_ids - seen) if i not in must]
    if candidate_pool_size <= 0:
        return list(must) + unseen

    available_slots = candidate_pool_size - len(must)
    if available_slots <= 0 or len(unseen) <= available_slots:
        return list(must) + unseen

    if popularity is None or popularity_buckets <= 1:
        # Uniform random sampling (original behavior)
        sampled = rng.choice(
            np.asarray(unseen, dtype=np.int64), size=available_slots, replace=False
        )
        result = list(must) + sampled.astype(np.int64).tolist()
        rng.shuffle(np.asarray(result, dtype=np.int64))
        return result

    # Popularity-stratified sampling (use pre-sorted list when available)
    if pop_sorted is not None:
        unseen_set = set(unseen)
        sorted_unseen = [item for item in pop_sorted if item in unseen_set]
    else:
        sorted_unseen = sorted(unseen, key=lambda x: popularity.get(x, 0))

    if not sorted_unseen:
        return list(must)

    n = len(sorted_unseen)
    bucket_size = max(1, n // popularity_buckets)
    slots_per_bucket = max(1, available_slots // popularity_buckets)

    sampled: list[int] = []
    for b in range(popularity_buckets):
        start = b * bucket_size
        end = min(start + bucket_size, n) if b < popularity_buckets - 1 else n
        bucket_items = sorted_unseen[start:end]
        if not bucket_items:
            continue
        draw = min(slots_per_bucket, len(bucket_items))
        bucket_sample = rng.choice(
            np.asarray(bucket_items, dtype=np.int64), size=draw, replace=False
        )
        sampled.extend(bucket_sample.astype(np.int64).tolist())

    # Fill remaining slots
    remaining = available_slots - len(sampled)
    if remaining > 0:
        already = set(sampled) | must
        leftover = [item for item in unseen if item not in already]
        if leftover:
            draw = min(remaining, len(leftover))
            extra = rng.choice(
                np.asarray(leftover, dtype=np.int64), size=draw, replace=False
            )
            sampled.extend(extra.astype(np.int64).tolist())

    result = list(must) + sampled[:available_slots]
    rng.shuffle(np.asarray(result, dtype=np.int64))
    return result


def hybrid_recommend(
    user_id: int,
    sims: dict[int, list[tuple[int, float]]],
    history: list[tuple[int, float]],
    seen: set[int],
    k: int,
    recall_k: int,
    per_seed_limit: int,
) -> list[int]:
    """Hybrid: ItemCF recall → NCF rerank."""
    candidates = itemcf_recall_candidates(sims, history, seen, recall_k, per_seed_limit)
    if not candidates:
        return []
    if not ncf_engine.is_ready():
        return candidates[:k]
    return ncf_recommend(user_id, candidates, k)


# ═══════════════════════════════════════════════════════════════════════
# Evaluation Engine
# ═══════════════════════════════════════════════════════════════════════

class EvaluationEngine:
    """Main evaluation engine. Instantiate within Flask app context."""

    def __init__(self, config: EvalConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self._ratings_by_user: dict[int, list[tuple[int, float, Any]]] = {}
        self._movie_genres: dict[int, set[str]] = {}
        self._popularity: dict[int, int] = {}
        self._all_item_ids: set[int] = set()
        self._n_users: int = 0

    def load_data(self, cache_dir: str | None = None) -> None:
        """Load ratings, movie genres, and popularity. Uses pickle cache (~3s load)."""
        import json
        import pickle
        from pathlib import Path
        from backend.app import db
        from backend.app.models import Movie, Rating

        if cache_dir is None:
            cache_dir = Path(__file__).resolve().parents[1] / "artifacts"
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        ratings_pkl = cache_dir / "eval_ratings_cache.pkl"
        genres_cache = cache_dir / "eval_genres_cache.json"
        pop_cache = cache_dir / "eval_popularity_cache.json"

        if ratings_pkl.exists():
            print("  Loading ratings from pickle cache...", end=" ", flush=True)
            with open(ratings_pkl, "rb") as f:
                self._ratings_by_user = pickle.load(f)
            print(f"{len(self._ratings_by_user)} users")
        else:
            print("  Loading ratings from DB (caching to pickle)...", end=" ", flush=True)
            rows = (
                Rating.query.with_entities(
                    Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp
                )
                .order_by(Rating.user_id.asc(), Rating.timestamp.asc())
                .all()
            )
            for uid, mid, r, ts in rows:
                self._ratings_by_user.setdefault(int(uid), []).append(
                    (int(mid), float(r), ts)
                )
            with open(ratings_pkl, "wb") as f:
                pickle.dump(self._ratings_by_user, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"{len(self._ratings_by_user)} users (cached)")

        # ── Genres ──
        if genres_cache.exists():
            with open(genres_cache) as f:
                raw = json.load(f)
            self._movie_genres = {int(k): set(v) for k, v in raw.items()}
        else:
            movie_rows = Movie.query.with_entities(Movie.id, Movie.genres).all()
            raw = {}
            for mid, genres_str in movie_rows:
                gset = set(g.strip() for g in str(genres_str).split("|") if g.strip()) if genres_str else set()
                self._movie_genres[int(mid)] = gset
                raw[str(mid)] = list(gset)
            with open(genres_cache, "w") as f:
                json.dump(raw, f)
        self._all_item_ids = set(self._movie_genres.keys())

        if pop_cache.exists():
            with open(pop_cache) as f:
                self._popularity = {int(k): v for k, v in json.load(f).items()}
        else:
            from sqlalchemy import func
            pop_rows = (
                db.session.query(Rating.movie_id, func.count(Rating.id).label("cnt"))
                .group_by(Rating.movie_id)
                .all()
            )
            self._popularity = {int(mid): int(cnt) for mid, cnt in pop_rows}
            with open(pop_cache, "w") as f:
                json.dump({str(k): v for k, v in self._popularity.items()}, f)
        self._n_users = len(self._ratings_by_user)

    def split_data(self) -> list[tuple[pd.DataFrame, dict[int, set[int]], dict[int, list[tuple[int, float]]]]]:
        """Temporal K-fold cross-validation split.

        Returns list of (train_ratings_df, test_items_by_user, train_by_user)
        for each fold. train_by_user is pre-built to avoid O(N^2) DataFrame
        filtering in the evaluation loop.

        K=1: leave-last-out (single fold, compatible with existing behavior).
        K>1: each user's interactions split into K time-ordered folds.
        """
        n_folds = self.config.n_folds
        folds: list[tuple[list[dict], dict[int, set[int]], dict[int, list[tuple[int, float]]]]] = []

        for _ in range(n_folds):
            folds.append(([], {}, {}))

        for uid, items in self._ratings_by_user.items():
            if len(items) < max(self.config.min_ratings, n_folds + 1):
                continue
            train_items = items[:-n_folds]
            test_slots = items[-n_folds:]

            train_rows = [
                {"user_id": uid, "movie_id": mid, "rating": r}
                for mid, r, _ts in train_items
            ]
            train_tuples = [(mid, r) for mid, r, _ts in train_items]

            for fold_idx, (test_mid, test_r, _test_ts) in enumerate(test_slots):
                if test_r >= self.config.like_threshold:
                    folds[fold_idx][0].extend(train_rows)
                    folds[fold_idx][1].setdefault(uid, set()).add(test_mid)
                    folds[fold_idx][2][uid] = train_tuples

        result = []
        for train_rows, test_dict, train_by_user in folds:
            # Sample users if n_test_users is set
            if self.config.n_test_users > 0 and len(test_dict) > self.config.n_test_users:
                rng = np.random.default_rng(self.config.seed)
                sampled_uids = set(rng.choice(
                    sorted(test_dict.keys()),
                    size=self.config.n_test_users, replace=False
                ))
                test_dict = {u: test_dict[u] for u in sampled_uids}
                train_by_user = {u: train_by_user[u] for u in sampled_uids
                                 if u in train_by_user}
            df = pd.DataFrame(train_rows) if train_rows else pd.DataFrame(
                columns=["user_id", "movie_id", "rating"]
            )
            result.append((df, test_dict, train_by_user))
        return result

    def evaluate_user(
        self,
        uid: int,
        train_history: list[tuple[int, float]],
        test_items: set[int],
        sims: dict[int, list[tuple[int, float]]],
        common_pool: list[int] | None = None,
    ) -> dict[str, dict] | None:
        """Evaluate a single user across all configured models.

        Returns {model_name: {metric: value, ...}} or None if user is skipped.
        """
        seen = {mid for mid, _r in train_history}
        history_genres: set[str] = set()
        for mid, _r in train_history:
            history_genres.update(self._movie_genres.get(mid, set()))

        results: dict[str, dict] = {}

        for model_name in self.config.models:
            # ── Generate recommendations ──
            if self.config.full_ranking:
                all_unseen = list(self._all_item_ids - seen)
                if model_name == "random":
                    recs = random_recommend(all_unseen, seen, self.config.k)
                elif model_name == "itemcf":
                    recs = itemcf_recommend(
                        sims, train_history, seen,
                        k=self.config.k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                elif model_name == "ncf":
                    recs = ncf_recommend(uid, all_unseen, self.config.k)
                elif model_name == "hybrid":
                    candidates = itemcf_recall_candidates(
                        sims, train_history, seen,
                        recall_k=self.config.recall_k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                    recs = ncf_recommend(uid, candidates, self.config.k) if candidates else []
                elif model_name == "lightgcn":
                    recs = lightgcn_recommend(uid, all_unseen, self.config.k)
                elif model_name == "ease":
                    recs = ease_recommend(
                        uid, all_unseen, self.config.k,
                        user_history=[mid for mid, _ in train_history]
                    )
                else:
                    continue
            elif self.config.fair_mode and common_pool is not None:
                if model_name == "random":
                    recs = random_recommend(common_pool, seen, self.config.k)
                elif model_name == "itemcf":
                    recs = itemcf_recommend_from_pool(
                        sims, train_history, seen,
                        candidate_pool=common_pool,
                        k=self.config.k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                elif model_name == "ncf":
                    recs = ncf_recommend(uid, common_pool, self.config.k)
                elif model_name == "hybrid":
                    candidates = itemcf_recommend_from_pool(
                        sims, train_history, seen,
                        candidate_pool=common_pool,
                        k=self.config.recall_k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                    if candidates and ncf_engine.is_ready():
                        recs = ncf_recommend(uid, candidates, self.config.k)
                    else:
                        recs = candidates[:self.config.k] if candidates else []
                elif model_name == "lightgcn":
                    recs = lightgcn_recommend(uid, common_pool, self.config.k)
                elif model_name == "ease":
                    recs = ease_recommend(
                        uid, common_pool, self.config.k,
                        user_history=[mid for mid, _ in train_history]
                    )
                else:
                    continue
            else:
                if model_name == "random":
                    all_unseen = list(self._all_item_ids - seen)
                    recs = random_recommend(all_unseen, seen, self.config.k)
                elif model_name == "itemcf":
                    recs = itemcf_recommend(
                        sims, train_history, seen,
                        k=self.config.k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                elif model_name == "ncf":
                    pool = sample_ncf_candidates(
                        self._all_item_ids, seen,
                        self.config.ncf_candidate_pool_size, self.rng,
                        must_include=test_items,
                        popularity=self._popularity,
                        popularity_buckets=self.config.popularity_buckets,
                    )
                    recs = ncf_recommend(uid, pool, self.config.k)
                elif model_name == "hybrid":
                    recs = hybrid_recommend(
                        uid, sims, train_history, seen,
                        k=self.config.k,
                        recall_k=self.config.recall_k,
                        per_seed_limit=self.config.per_seed_limit,
                    )
                elif model_name == "lightgcn":
                    all_unseen = list(self._all_item_ids - seen)
                    recs = lightgcn_recommend(uid, all_unseen, self.config.k)
                elif model_name == "ease":
                    all_unseen = list(self._all_item_ids - seen)
                    recs = ease_recommend(
                        uid, all_unseen, self.config.k,
                        user_history=[mid for mid, _ in train_history]
                    )
                else:
                    continue

            if not recs:
                continue

            # ── Compute all metrics ──
            k = self.config.k
            result = {
                "precision": compute_precision(recs, test_items, k),
                "recall": compute_recall(recs, test_items, k),
                "ndcg": compute_ndcg(recs, test_items, k),
                "mrr": compute_mrr(recs, test_items),
                "map": compute_map(recs, test_items, k),
                "ils": compute_ils(recs, sims, k),
                "genre_diversity": compute_genre_diversity(recs, self._movie_genres, k),
                "novelty": compute_novelty(recs, self._popularity, self._n_users, k),
                "serendipity": compute_serendipity(
                    recs, test_items, history_genres, self._movie_genres, k
                ),
                "avg_log_popularity": float(
                    np.mean([np.log1p(self._popularity.get(mid, 0)) for mid in recs])
                ),
                "num_recs": len(recs),
                "recs": recs,
            }
            results[model_name] = result

        return results if results else None

    def run(self, models: list[str] | None = None) -> list[Metrics]:
        """Run evaluation across all folds and aggregate results.

        Returns one Metrics object per model.
        """
        if models is not None:
            self.config.models = models

        start_time = time.time()

        folds = self.split_data()
        all_fold_results: list[dict[str, list[dict]]] = []
        total_users = sum(len(test_dict) for _, test_dict, _ in folds)
        processed = 0

        for fold_idx, (train_df, test_dict, train_by_user) in enumerate(folds):
            if not test_dict:
                continue

            # Build similarity matrix from TRAINING data only (fixes data leakage)
            print(f"  Fold {fold_idx + 1}: building similarity matrix from "
                  f"{len(train_df)} training ratings...")
            sims = compute_item_similarity(
                train_df,
                topk=self.config.sim_topk_per_movie,
                normalize=True,
            )
            print(f"  Similarity matrix ready: {len(sims)} movies")

            fold_user_results: dict[str, list[dict]] = {
                m: [] for m in self.config.models
            }
            fold_recs: dict[str, set[int]] = {m: set() for m in self.config.models}

            # Pre-compute popularity-sorted items for candidate sampling (once per fold)
            pop_sorted: list[int] | None = None
            if self.config.fair_mode:
                pop_sorted = sorted(
                    self._popularity.keys(),
                    key=lambda x: self._popularity.get(x, 0)
                )

            for uid, test_items in test_dict.items():
                # Use pre-built history dict (O(1) lookup, not O(N) DataFrame filter)
                history = train_by_user.get(uid)
                if history is None or len(history) < 2:
                    continue

                # Sample common candidate pool (fair mode)
                common_pool = None
                if self.config.fair_mode:
                    seen = {mid for mid, _r in history}
                    common_pool = sample_ncf_candidates(
                        self._all_item_ids, seen,
                        self.config.ncf_candidate_pool_size, self.rng,
                        must_include=test_items,
                        popularity=self._popularity,
                        popularity_buckets=self.config.popularity_buckets,
                        pop_sorted=pop_sorted,
                    )

                user_metrics = self.evaluate_user(
                    uid, history, test_items, sims, common_pool
                )
                if user_metrics is None:
                    continue

                for model, metrics_dict in user_metrics.items():
                    metrics_dict["user_id"] = uid
                    metrics_dict["n_train_ratings"] = len(history)
                    fold_user_results[model].append(metrics_dict)
                    fold_recs[model].update(metrics_dict["recs"])

                processed += 1
                if processed % 10000 == 0:
                    elapsed = time.time() - start_time
                    print(f"  {processed}/{total_users} users "
                          f"({processed / elapsed:.0f} u/s)...")

            all_fold_results.append(fold_user_results)

        runtime = time.time() - start_time
        print(f"  Evaluation complete: {processed} users in {runtime:.0f}s")

        return self._aggregate_results(all_fold_results, runtime)

        runtime = time.time() - start_time

        # ── Aggregate results ──
        return self._aggregate_results(all_fold_results, runtime)

    def _aggregate_results(
        self, all_fold_results: list[dict[str, list[dict]]], runtime: float
    ) -> list[Metrics]:
        """Aggregate per-user metrics across all folds into final Metrics list."""
        if not all_fold_results:
            return []

        # Combine all folds: pool per-user results
        combined: dict[str, list[dict]] = defaultdict(list)
        combined_recs: dict[str, set[int]] = defaultdict(set)

        for fold_results in all_fold_results:
            for model, user_list in fold_results.items():
                combined[model].extend(user_list)
                for u in user_list:
                    combined_recs[model].update(u["recs"])

        results: list[Metrics] = []
        total_items = len(self._all_item_ids)
        tail_cutoff = int(total_items * 0.2)
        tail_items = set(
            sorted(self._popularity, key=lambda x: self._popularity.get(x, 0))[tail_cutoff:]
        )

        for model_name, per_user in combined.items():
            n_users = len(per_user)
            if n_users == 0:
                continue

            metrics = Metrics(
                model=model_name,
                precision_at_k=float(np.mean([u["precision"] for u in per_user])),
                recall_at_k=float(np.mean([u["recall"] for u in per_user])),
                map_at_k=float(np.mean([u["map"] for u in per_user])),
                ndcg_at_k=float(np.mean([u["ndcg"] for u in per_user])),
                mrr_at_k=float(np.mean([u["mrr"] for u in per_user])),
                ils_at_k=float(np.mean([u["ils"] for u in per_user])),
                genre_diversity_at_k=float(np.mean([u["genre_diversity"] for u in per_user])),
                novelty_at_k=float(np.mean([u["novelty"] for u in per_user])),
                coverage=compute_coverage(combined_recs[model_name], total_items),
                tail_coverage=compute_tail_coverage(combined_recs[model_name], tail_items),
                serendipity_at_k=float(np.mean([u["serendipity"] for u in per_user])),
                users_evaluated=n_users,
                avg_recs=float(np.mean([u["num_recs"] for u in per_user])),
                avg_log_popularity=float(np.mean([u["avg_log_popularity"] for u in per_user])),
                k=self.config.k,
                recall_k=self.config.recall_k if model_name == "hybrid" else None,
                per_seed_limit=self.config.per_seed_limit,
                runtime_seconds=runtime,
                params={
                    "fair_mode": self.config.fair_mode,
                    "n_folds": self.config.n_folds,
                    "ncf_trained_on": "full_dataset",
                },
                per_user_metrics={"users": per_user},
            )
            results.append(metrics)

        return results


# ═══════════════════════════════════════════════════════════════════════
# Statistical Tests
# ═══════════════════════════════════════════════════════════════════════

class StatisticalTests:
    """Paired statistical tests for model comparison."""

    @staticmethod
    def _align_by_user(
        data_a: list[dict], data_b: list[dict], metric: str
    ) -> tuple[np.ndarray, np.ndarray]:
        """Align per-user metrics by shared user_ids."""
        a_by_uid = {u["user_id"]: u.get(metric, np.nan) for u in data_a}
        common_uids = set(a_by_uid) & {u["user_id"] for u in data_b}
        x = np.array([a_by_uid[uid] for uid in sorted(common_uids)])
        y = np.array([next(u.get(metric, np.nan) for u in data_b if u["user_id"] == uid)
                       for uid in sorted(common_uids)])
        return x, y

    @classmethod
    def wilcoxon_signed_rank(
        cls, x: np.ndarray, y: np.ndarray
    ) -> tuple[float, float]:
        """Wilcoxon signed-rank test for paired samples.

        H0: the median difference between x and y is zero.
        x and y must be same-length aligned arrays.
        """
        from scipy.stats import wilcoxon
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 10:
            return (0.0, 1.0)
        try:
            stat, p = wilcoxon(x[mask], y[mask], zero_method="wilcox", alternative="two-sided")
            return (float(stat), float(p))
        except Exception:
            return (0.0, 1.0)

    @staticmethod
    def cohens_d(x: np.ndarray, y: np.ndarray) -> float:
        """Cohen's d effect size for paired samples.

        d = mean(x - y) / std(x - y).  |d| ≈ 0.2 small, 0.5 medium, 0.8 large.
        x and y must be same-length aligned arrays.
        """
        diff = x - y
        mask = ~np.isnan(diff)
        if mask.sum() < 2:
            return 0.0
        diff = diff[mask]
        sd = np.std(diff, ddof=1)
        if sd < 1e-10:
            return 0.0
        return float(np.mean(diff) / sd)

    @staticmethod
    def bonferroni_holm_correction(p_values: list[float]) -> list[float]:
        """Bonferroni-Holm step-down correction.

        Returns adjusted p-values. Reject H0 if adjusted_p < alpha.
        """
        n = len(p_values)
        if n == 0:
            return []
        indexed = sorted(enumerate(p_values), key=lambda x: x[1])
        adjusted = [0.0] * n
        for rank, (idx, p) in enumerate(indexed):
            adjusted[idx] = min(p * (n - rank), 1.0)
            if rank > 0:
                adjusted[idx] = max(adjusted[idx], adjusted[indexed[rank - 1][0]])
        return adjusted

    @classmethod
    def pairwise_comparison(
        cls,
        models_data: dict[str, list[dict]],
        metrics: list[str],
        alpha: float = 0.05,
    ) -> dict:
        """Pairwise Wilcoxon test for all model pairs × all metrics.

        Returns nested dict:
            {metric: {("model_a", "model_b"): {"p": p, "p_corrected": p_c, "cohens_d": d}}}
        """
        model_names = sorted(models_data.keys())
        result: dict = {}

        for metric in metrics:
            result[metric] = {}
            p_values: list[tuple[tuple[str, str], float]] = []

            for i, ma in enumerate(model_names):
                for mb in model_names[i + 1:]:
                    x, y = cls._align_by_user(models_data[ma], models_data[mb], metric)
                    _, p = cls.wilcoxon_signed_rank(x, y)
                    d = cls.cohens_d(x, y)
                    p_values.append(((ma, mb), p))
                    result[metric][(ma, mb)] = {
                        "p_value": p,
                        "cohens_d": d,
                        "significant": "no",
                    }

            # Bonferroni-Holm correction
            raw_ps = [pv[1] for pv in p_values]
            corrected = cls.bonferroni_holm_correction(raw_ps)
            for ((ma, mb), _), p_corrected in zip(p_values, corrected):
                result[metric][(ma, mb)]["p_corrected"] = p_corrected
                result[metric][(ma, mb)]["significant"] = (
                    "yes" if p_corrected < alpha else "no"
                )

        return result


# ═══════════════════════════════════════════════════════════════════════
# User Stratification
# ═══════════════════════════════════════════════════════════════════════

class UserStratification:
    """Split evaluation results by user activity level."""

    COLD_MAX = 5
    WARM_MAX = 20

    @classmethod
    def stratify(
        cls, per_user_data: list[dict]
    ) -> dict[str, list[dict]]:
        """Split per-user metrics into Cold / Warm / Hot groups.

        Returns {"cold": [...], "warm": [...], "hot": [...]}
        """
        cold, warm, hot = [], [], []
        for u in per_user_data:
            n = u.get("n_train_ratings", 0)
            if n <= cls.COLD_MAX:
                cold.append(u)
            elif n <= cls.WARM_MAX:
                warm.append(u)
            else:
                hot.append(u)
        return {"cold": cold, "warm": warm, "hot": hot}

    @classmethod
    def report_by_stratum(
        cls, per_user_data: list[dict], metrics_list: list[str]
    ) -> dict:
        """Aggregate metrics per stratum.

        Returns {"cold": {metric: mean}, "warm": {...}, "hot": {...}}
        """
        stratified = cls.stratify(per_user_data)
        report: dict = {}
        for stratum, users in stratified.items():
            if not users:
                report[stratum] = {"n_users": 0}
                continue
            stratum_metrics = {"n_users": len(users)}
            for m in metrics_list:
                vals = [u.get(m, 0.0) for u in users]
                stratum_metrics[m] = float(np.mean(vals))
            report[stratum] = stratum_metrics
        return report


# ═══════════════════════════════════════════════════════════════════════
# Ablation Runner
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AblationConfig:
    """Single ablation parameter specification."""
    param_name: str
    param_values: list
    model: str


class AblationRunner:
    """Run ablation studies over configurable parameter grids."""

    def __init__(self, engine: EvaluationEngine):
        self.engine = engine

    def run_ablation(self, configs: list[AblationConfig]) -> list[Metrics]:
        """Run grid search over ablation configs. Each config → one Metrics."""
        results: list[Metrics] = []
        for cfg in configs:
            for val in cfg.param_values:
                # Apply parameter override to engine config
                setattr(self.engine.config, cfg.param_name, val)
                self.engine.config.models = [cfg.model]
                self.engine.rng = np.random.default_rng(self.engine.config.seed)

                fold_results = self.engine.run([cfg.model])
                for m in fold_results:
                    m.params["ablation_param"] = cfg.param_name
                    m.params["ablation_value"] = val
                    results.append(m)
        return results

    @staticmethod
    def default_ablations() -> list[AblationConfig]:
        """Predefined ablation matrix matching thesis requirements."""
        return [
            AblationConfig("per_seed_limit", [10, 25, 50, 100], "itemcf"),
            AblationConfig("recall_k", [50, 100, 200, 500], "hybrid"),
        ]
