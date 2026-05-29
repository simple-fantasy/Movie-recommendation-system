def popularity_recommend(candidate_ids, popularity, seen, k):
    available = [(mid, popularity.get(mid, 0)) for mid in candidate_ids if mid not in seen]
    available.sort(key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in available[:k]]


def random_recommend(candidate_ids, seen, k, rng):
    available = [mid for mid in candidate_ids if mid not in seen]
    if not available:
        return []
    k_eff = min(k, len(available))
    indices = rng.choice(len(available), size=k_eff, replace=False)
    return [available[int(i)] for i in indices]


def oracle_recommend(test_items, filler_pool, k, rng):
    recs = list(test_items)[:k]
    remaining = k - len(recs)
    if remaining > 0:
        available = [mid for mid in filler_pool if mid not in test_items]
        if available:
            n_fill = min(remaining, len(available))
            indices = rng.choice(len(available), size=n_fill, replace=False)
            recs.extend(available[int(i)] for i in indices)
    return recs[:k]
