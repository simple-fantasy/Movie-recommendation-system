"""轻量级三模型对比评估，结果直接写文件"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from collections import defaultdict
import numpy as np

from backend.app import create_app, db
from backend.app.models import MovieSimilarity, Rating
from backend.app.ncf_engine import ncf_engine

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "hybrid_eval_result.txt")

app = create_app()
with app.app_context():
    lines = []

    # Load similarities
    t0 = time.time()
    sims = defaultdict(list)
    for mid, sid, score in MovieSimilarity.query.with_entities(
        MovieSimilarity.movie_id, MovieSimilarity.similar_movie_id, MovieSimilarity.score
    ).order_by(MovieSimilarity.movie_id, MovieSimilarity.score.desc()).all():
        if len(sims[mid]) < 50:
            sims[mid].append((sid, float(score)))
    lines.append(f"Similarities: {len(sims)} movies ({time.time()-t0:.1f}s)")

    # Load NCF
    t0 = time.time()
    ncf_ok = ncf_engine.load()
    lines.append(f"NCF: {'ready' if ncf_ok else 'not available'} ({time.time()-t0:.1f}s)")

    # Sample users
    from sqlalchemy import func
    users = [r[0] for r in
        db.session.query(Rating.user_id, func.count(Rating.id))
        .group_by(Rating.user_id)
        .having(func.count(Rating.id) >= 15)
        .having(func.count(Rating.id) <= 60)
        .order_by(func.rand())
        .limit(300).all()]
    lines.append(f"Sampled {len(users)} users")

    # Load ratings
    t0 = time.time()
    user_data = Rating.query.with_entities(
        Rating.user_id, Rating.movie_id, Rating.rating, Rating.timestamp
    ).filter(Rating.user_id.in_(users)).order_by(Rating.user_id.asc(), Rating.timestamp.asc()).all()
    by_user = defaultdict(list)
    for uid, mid, r, ts in user_data:
        by_user[int(uid)].append((int(mid), float(r)))
    lines.append(f"Ratings loaded: {len(user_data)} rows ({time.time()-t0:.1f}s)")

    rng = np.random.default_rng(42)
    results = {
        'itemcf': {'hr': [], 'ndcg': [], 'mrr': []},
        'ncf': {'hr': [], 'ndcg': [], 'mrr': []},
        'hybrid': {'hr': [], 'ndcg': [], 'mrr': []},
    }
    k = 10
    all_mids = sorted(sims.keys())

    t0 = time.time()
    for idx, uid in enumerate(users):
        items = by_user.get(uid, [])
        if len(items) < 10:
            continue
        test_mid, test_r = items[-1]
        if test_r < 4.0:
            continue
        train = items[:-1]
        seen = {mid for mid, _ in train}

        scores = defaultdict(float)
        for seed_mid, seed_r in train:
            for sid, sim in sims.get(seed_mid, [])[:50]:
                if sid not in seen:
                    scores[sid] += sim * seed_r

        # ItemCF
        icf = [mid for mid, _ in sorted(scores.items(), key=lambda x: -x[1])[:k]] if scores else []

        # NCF
        ncf = []
        if ncf_ok and uid in ncf_engine.user2idx and scores:
            negs = [m for m in all_mids if m not in seen and m != test_mid][:1999]
            pool = np.array([test_mid] + negs, dtype=np.int64)
            rng.shuffle(pool)
            ncf = [mid for mid, _ in ncf_engine.rank(uid, pool.tolist(), top_k=k)]

        # Hybrid
        hyb = []
        if ncf_ok and uid in ncf_engine.user2idx and scores:
            recall = sorted(scores.items(), key=lambda x: -x[1])[:100]
            cands = [mid for mid, _ in recall]
            if test_mid not in cands:
                cands.append(test_mid)
            hyb = [mid for mid, _ in ncf_engine.rank(uid, cands, top_k=k)]
            if not hyb:
                hyb = icf[:k]
        elif scores:
            hyb = icf[:k]

        for model, recs in [('itemcf', icf), ('ncf', ncf), ('hybrid', hyb)]:
            if not recs:
                continue
            rank = next((i for i, mid in enumerate(recs) if mid == test_mid), None)
            results[model]['hr'].append(1.0 if rank is not None else 0.0)
            results[model]['mrr'].append(1.0 / (rank + 1) if rank is not None else 0.0)
            results[model]['ndcg'].append(1.0 / np.log2(rank + 2) if rank is not None else 0.0)

        if (idx + 1) % 50 == 0:
            lines.append(f"Processed {idx+1} users...")

    elapsed = time.time() - t0

    lines.append("")
    lines.append("=" * 65)
    lines.append(f"{'Model':<10} {'Users':<8} {'HR@10':<10} {'NDCG@10':<10} {'MRR@10':<10}")
    lines.append("-" * 65)
    for model in ['itemcf', 'ncf', 'hybrid']:
        res = results[model]
        n_u = len(res['hr'])
        if n_u == 0:
            continue
        lines.append(
            f"{model:<10} {n_u:<8} {np.mean(res['hr']):<10.4f} "
            f"{np.mean(res['ndcg']):<10.4f} {np.mean(res['mrr']):<10.4f}"
        )
    lines.append("=" * 65)
    lines.append(f"Total time: {elapsed:.1f}s")
    lines.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    result = "\n".join(lines)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(result + "\n")
    print(result)
