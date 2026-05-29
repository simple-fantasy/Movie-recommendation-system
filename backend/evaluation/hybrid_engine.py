def hybrid_recommend(user_id, sims, history, seen, k, recall_k, per_seed_limit, ncf_inference):
    from backend.evaluation.itemcf_engine import itemcf_recall_candidates

    candidates = itemcf_recall_candidates(sims, history, seen, recall_k, per_seed_limit)
    if not candidates:
        return []

    if ncf_inference is None or user_id not in ncf_inference.user2idx:
        return candidates[:k]

    ranked = ncf_inference.batched_rank(user_id, candidates, top_k=k)
    if not ranked:
        return candidates[:k]
    return [mid for mid, _score in ranked]
