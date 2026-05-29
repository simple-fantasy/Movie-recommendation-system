import numpy as np


def compute_hit_rank(recs: list[int], test_items: set[int]) -> int | None:
    for idx, mid in enumerate(recs):
        if mid in test_items:
            return idx
    return None


def compute_precision(recs: list[int], test_items: set[int], k: int) -> float:
    if k <= 0:
        return 0.0
    hits = sum(1 for mid in recs[:k] if mid in test_items)
    return hits / float(k)


def compute_recall(recs: list[int], test_items: set[int], k: int) -> float:
    if not test_items:
        return 0.0
    hits = sum(1 for mid in recs[:k] if mid in test_items)
    return hits / float(len(test_items))


def compute_ndcg(recs: list[int], test_items: set[int], k: int) -> float:
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
    rank = compute_hit_rank(recs, test_items)
    if rank is None:
        return 0.0
    return 1.0 / float(rank + 1)


def compute_map(recs: list[int], test_items: set[int], k: int) -> float:
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
    if n_items == 0:
        return 0.0
    return float(len(all_recs)) / float(n_items)


def compute_tail_coverage(all_recs: set[int], tail_items: set[int]) -> float:
    if not tail_items:
        return 0.0
    return float(len(all_recs & tail_items)) / float(len(tail_items))


def compute_all_metrics(recs, test_items, k, sims, movie_genres, popularity, n_users, history_genres):
    return {
        "precision_at_k": compute_precision(recs, test_items, k),
        "recall_at_k": compute_recall(recs, test_items, k),
        "ndcg_at_k": compute_ndcg(recs, test_items, k),
        "mrr_at_k": compute_mrr(recs, test_items),
        "map_at_k": compute_map(recs, test_items, k),
        "ils_at_k": compute_ils(recs, sims, k),
        "genre_diversity_at_k": compute_genre_diversity(recs, movie_genres, k),
        "novelty_at_k": compute_novelty(recs, popularity, n_users, k),
        "serendipity_at_k": compute_serendipity(recs, test_items, history_genres, movie_genres, k),
    }
