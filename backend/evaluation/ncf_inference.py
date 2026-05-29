import json
from pathlib import Path

import torch

from backend.app.ncf_engine import NCF


class NCFInference:
    def __init__(self, model_path, meta_path, device="cpu"):
        self.device = device

        meta_raw = json.loads(Path(meta_path).read_text(encoding="utf-8"))
        config = meta_raw.get("config", {})
        self.num_users = int(meta_raw["num_users"])
        self.num_items = int(meta_raw["num_items"])
        self.embedding_dim = int(config.get("embedding_dim", 32))
        self.hidden_dim = int(config.get("hidden_dim", 64))

        self.user2idx = {int(k): int(v) for k, v in meta_raw["user2idx"].items()}
        self.item2idx = {int(k): int(v) for k, v in meta_raw["item2idx"].items()}

        self.model = NCF(self.num_users, self.num_items, self.embedding_dim, self.hidden_dim)
        self.model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        self.model.to(device)
        self.model.eval()

    def batched_rank(self, user_id, candidate_ids, top_k=10, batch_size=4096):
        if user_id not in self.user2idx:
            return []
        u_idx = self.user2idx[user_id]

        valid = []
        for mid in candidate_ids:
            i_idx = self.item2idx.get(mid)
            if i_idx is not None:
                valid.append((mid, i_idx))
        if not valid:
            return []

        self._score_items(u_idx, valid, batch_size)
        k_eff = min(top_k, len(valid))
        top_indices = torch.topk(self._scores, k=k_eff).indices
        return [(valid[i][0], float(self._scores[i])) for i in top_indices.tolist()]

    def _score_items(self, u_idx, valid, batch_size):
        import numpy as np
        n = len(valid)
        self._scores = torch.empty(n)

        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            chunk = valid[start:end]
            indices = [idx for _mid, idx in chunk]
            u_t = torch.full((len(indices),), u_idx, dtype=torch.long, device=self.device)
            i_t = torch.tensor(indices, dtype=torch.long, device=self.device)
            with torch.no_grad():
                logits = self.model(u_t, i_t)
            self._scores[start:end] = torch.sigmoid(logits).cpu()
