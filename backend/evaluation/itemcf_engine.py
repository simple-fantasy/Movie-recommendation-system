def itemcf_recommend(sims, history, seen, k, per_seed_limit):
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


def itemcf_recall_candidates(sims, history, seen, recall_k, per_seed_limit):
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
