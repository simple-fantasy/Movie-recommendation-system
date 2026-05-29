import numpy as np

from backend.evaluation.config import EvalProtocolConfig
from backend.evaluation.metrics import compute_all_metrics, compute_coverage, compute_tail_coverage
from backend.evaluation.itemcf_engine import itemcf_recommend, itemcf_recall_candidates
from backend.evaluation.baselines import popularity_recommend, random_recommend, oracle_recommend
from backend.evaluation.hybrid_engine import hybrid_recommend


class EvaluationEngine:
    def __init__(self, config, data_bundle, ncf_inference):
        self.cfg = config
        self.train = data_bundle["train_by_user"]
        self.test = data_bundle["test_by_user"]
        self.movie_genres = data_bundle["movie_genres"]
        self.popularity = data_bundle["popularity"]
        self.n_users = data_bundle["n_users"]
        self.sims = data_bundle.get("sims", {})
        self.ncf = ncf_inference
        self.rng = np.random.default_rng(config.seed)
        self._c_all = []
        self._pop_ranking = []
        self._tail_items = set()
        self._init_candidates()
        self._c_all_set = set(self._c_all)
        self._excluded_stats = self._validate_test_items()

    def _init_candidates(self):
        ncf_items = set(self.ncf.item2idx.keys()) if self.ncf else set(self.sims.keys())
        itemcf_items = set(self.sims.keys())
        self._c_all = sorted(itemcf_items & ncf_items)
        self._filter_sims(ncf_items)
        train_pop = {}
        for uid, items in self.train.items():
            for mid, _r in items:
                train_pop[mid] = train_pop.get(mid, 0) + 1
        self._pop_ranking = sorted(train_pop, key=lambda x: train_pop.get(x, 0), reverse=True)
        cutoff = max(1, int(len(self._c_all) * 0.2))
        sorted_by_pop = sorted(train_pop, key=lambda x: train_pop.get(x, 0))
        self._tail_items = set(sorted_by_pop[cutoff:])

    def _filter_sims(self, ncf_items):
        filtered = {}
        for mid, neighbors in self.sims.items():
            if mid not in ncf_items:
                continue
            f_neighbors = [(sid, s) for sid, s in neighbors if sid in ncf_items]
            if f_neighbors:
                filtered[mid] = f_neighbors
        self.sims = filtered

    def _validate_test_items(self):
        """检查 test items 在 C_all 中的覆盖率 + 低信号用户统计。"""
        total_test = 0
        excluded = 0
        users_to_remove = []
        low_signal = 0
        for uid, items in self.test.items():
            in_c = sum(1 for mid, _r in items if mid in self._c_all_set)
            total_test += len(items)
            excluded += len(items) - in_c
            if in_c == 0:
                users_to_remove.append(uid)
            train_items = self.train.get(uid, [])
            if train_items and all(r < self.cfg.like_threshold for _mid, r in train_items):
                low_signal += 1
        for uid in users_to_remove:
            del self.test[uid]
        return {
            "total_test_items": total_test,
            "excluded_from_c_all": excluded,
            "users_removed_no_test_in_c_all": len(users_to_remove),
            "low_signal_users_all_train_below_threshold": low_signal,
        }

    def run(self, models, test_users, resume_from=0):
        import time as _time
        per_user_data = {}
        all_recs_by_model = {}

        for model_name in models:
            n = len(test_users) - resume_from
            print(f"  {model_name}: {n} users...", end=" ", flush=True)
            t0 = _time.time()
            per_user, all_recs = self._evaluate_model(model_name, test_users, resume_from)
            elapsed = _time.time() - t0
            print(f"{len(per_user)} evaluated ({elapsed:.0f}s, {n/elapsed:.0f} u/s)")
            per_user_data[model_name] = per_user
            all_recs_by_model[model_name] = all_recs

        summary = self._build_summary(per_user_data, all_recs_by_model)
        return {"summary": summary, "per_user_data": per_user_data}

    def _evaluate_model(self, model_name, test_users, resume_from):
        per_user = []
        all_recs = set()
        users = test_users[resume_from:]

        for uid in users:
            if uid not in self.train or uid not in self.test:
                continue
            result = self._eval_one_user(model_name, uid)
            if result is None:
                continue
            per_user.append(result["metrics"])
            all_recs.update(result["recs"])

        return per_user, all_recs

    def _eval_one_user(self, model_name, uid):
        history = self.train[uid]
        test_items = {mid for mid, _r in self.test[uid]}
        seen = {mid for mid, _r in history}
        history_genres = set()
        for mid, _r in history:
            history_genres.update(self.movie_genres.get(mid, set()))

        recs = self._get_recs(model_name, uid, history, seen)
        if recs is None or not recs:
            return None

        metrics = compute_all_metrics(
            recs, test_items, self.cfg.k, self.sims,
            self.movie_genres, self.popularity, self.n_users, history_genres,
        )
        metrics["user_id"] = uid
        metrics["n_train_ratings"] = len(history)
        return {"metrics": metrics, "recs": recs}

    def _get_recs(self, model_name, uid, history, seen):
        C_u = [mid for mid in self._c_all if mid not in seen]
        if model_name == "popularity":
            return popularity_recommend(C_u, self.popularity, seen, self.cfg.k)
        if model_name == "random":
            return random_recommend(C_u, seen, self.cfg.k, self.rng)
        if model_name == "oracle":
            test_set = {mid for mid, _r in self.test[uid]}
            return oracle_recommend(test_set, C_u, self.cfg.k, self.rng)
        if model_name == "itemcf":
            return itemcf_recommend(self.sims, history, seen, self.cfg.k, self.cfg.per_seed_limit)
        if model_name == "ncf":
            if self.ncf is None or uid not in self.ncf.user2idx:
                return None
            ranked = self.ncf.batched_rank(uid, C_u, top_k=self.cfg.k)
            return [mid for mid, _score in ranked] if ranked else None
        if model_name == "hybrid":
            candidates = itemcf_recall_candidates(
                self.sims, history, seen, self.cfg.recall_k_hybrid, self.cfg.per_seed_limit,
            )
            assert all(mid in self._c_all_set for mid in candidates), \
                f"Hybrid recall leaked {sum(1 for mid in candidates if mid not in self._c_all_set)} items outside C_all"
            if not candidates:
                return None
            if self.ncf is None or uid not in self.ncf.user2idx:
                return candidates[:self.cfg.k]
            ranked = self.ncf.batched_rank(uid, candidates, top_k=self.cfg.k)
            return [mid for mid, _score in ranked] if ranked else candidates[:self.cfg.k]
        if model_name == "lightgcn":
            return self._lightgcn_recs(uid, C_u)
        if model_name == "ease":
            return self._ease_recs(uid, C_u, history)
        return None

    _lightgcn_emb = None
    _lightgcn_u2i = None
    _lightgcn_i2i = None
    _lightgcn_nu = None

    def _load_lightgcn(self):
        if self._lightgcn_emb is not None:
            return
        import json
        from pathlib import Path
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        emb_path = artifacts / "lightgcn_embeddings.pt"
        meta_path = artifacts / "lightgcn_meta.json"
        if emb_path.exists() and meta_path.exists():
            import torch
            emb = torch.load(emb_path, map_location="cpu", weights_only=True)
            meta = json.loads(meta_path.read_text())
            self._lightgcn_u2i = {int(k): v for k, v in meta["user2idx"].items()}
            self._lightgcn_i2i = {int(k): v for k, v in meta["item2idx"].items()}
            self._lightgcn_nu = meta["num_users"]
            self._lightgcn_emb = emb

    def _lightgcn_recs(self, uid, C_u):
        self._load_lightgcn()
        if self._lightgcn_emb is None or uid not in self._lightgcn_u2i:
            return None
        u_emb = self._lightgcn_emb[self._lightgcn_u2i[uid]]
        valid = [(mid, self._lightgcn_i2i[mid]) for mid in C_u if mid in self._lightgcn_i2i]
        if not valid:
            return None
        import torch
        idxs = torch.LongTensor([i for _, i in valid])
        scores = torch.mv(self._lightgcn_emb[self._lightgcn_nu:][idxs], u_emb)
        _, top = torch.topk(scores, min(self.cfg.k, len(scores)))
        return [valid[i][0] for i in top.tolist()]

    _ease_B = None
    _ease_item2idx = None
    _ease_n_items = None

    def _load_ease(self):
        if self._ease_B is not None:
            return
        import json
        from pathlib import Path
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        b_path = artifacts / "ease_B.npy"
        meta_path = artifacts / "ease_meta.json"
        if b_path.exists() and meta_path.exists():
            self._ease_B = np.load(b_path)
            meta = json.loads(meta_path.read_text())
            self._ease_item2idx = {int(k): v for k, v in meta["item2idx"].items()}
            self._ease_n_items = meta["n_items"]

    def _ease_recs(self, uid, C_u, history):
        self._load_ease()
        if self._ease_B is None:
            return None
        u_vec = np.zeros(self._ease_n_items, dtype=np.float32)
        for mid, _r in history:
            if mid in self._ease_item2idx:
                u_vec[self._ease_item2idx[mid]] = 1.0
        if u_vec.sum() == 0:
            return None
        scores = self._ease_B @ u_vec
        valid = [(mid, scores[self._ease_item2idx[mid]])
                 for mid in C_u if mid in self._ease_item2idx]
        if not valid:
            return None
        valid.sort(key=lambda x: x[1], reverse=True)
        return [mid for mid, _ in valid[:self.cfg.k]]

    def _build_summary(self, per_user_data, all_recs_by_model):
        summary = {}
        metric_keys = [
            "precision_at_k", "recall_at_k", "ndcg_at_k", "mrr_at_k", "map_at_k",
            "ils_at_k", "genre_diversity_at_k", "novelty_at_k", "serendipity_at_k",
        ]
        for model_name, per_user in per_user_data.items():
            if not per_user:
                continue
            s = {"users_evaluated": len(per_user)}
            for key in metric_keys:
                vals = [u[key] for u in per_user if key in u]
                s[key] = float(np.mean(vals)) if vals else 0.0
            s["coverage"] = compute_coverage(
                all_recs_by_model.get(model_name, set()), len(self._c_all)
            )
            s["tail_coverage"] = compute_tail_coverage(
                all_recs_by_model.get(model_name, set()), self._tail_items
            )
            summary[model_name] = s
        return summary
