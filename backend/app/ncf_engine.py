from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

try:
    import torch
    from torch import nn
    TORCH_AVAILABLE = True
except Exception as e:  # pragma: no cover
    TORCH_AVAILABLE = False
    torch = None
    nn = None


class NCF(nn.Module if TORCH_AVAILABLE else object):
    """NCF model definition (same as in train_ncf.py)"""

    def __init__(self, num_users: int, num_items: int, embedding_dim: int, hidden_dim: int):
        if TORCH_AVAILABLE:
            super().__init__()
        self.user_emb = nn.Embedding(num_users, embedding_dim) if TORCH_AVAILABLE else None
        self.item_emb = nn.Embedding(num_items, embedding_dim) if TORCH_AVAILABLE else None

        if TORCH_AVAILABLE:
            self.mlp = nn.Sequential(
                nn.Linear(embedding_dim * 2, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )
        else:
            self.mlp = None

    def forward(self, user_idx, item_idx):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")
        u = self.user_emb(user_idx)
        i = self.item_emb(item_idx)
        x = torch.cat([u, i], dim=-1)
        logits = self.mlp(x).squeeze(-1)
        return logits


class NCFEngine:
    """NCF inference engine with async loading and graceful degradation."""

    _instance: NCFEngine | None = None
    _lock = threading.Lock()

    def __new__(cls) -> NCFEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.model: NCF | None = None
        self.user2idx: dict[int, int] = {}
        self.item2idx: dict[int, int] = {}
        self.idx2item: dict[str, int] = {}
        self.config: dict[str, Any] = {}
        self.num_users = 0
        self.num_items = 0
        self._loaded = False
        self._loading = False
        self._load_error: str | None = None
        self._load_thread: threading.Thread | None = None

    def load(self, artifacts_dir: str | Path | None = None) -> bool:
        """Load NCF model from artifacts directory. Returns True if successful."""
        # 检查torch是否可用
        if not TORCH_AVAILABLE:
            print("[NCFEngine] PyTorch not available, skipping NCF model loading")
            with self._lock:
                self._load_error = "PyTorch not installed"
            return False
            
        with self._lock:
            if self._loaded:
                return True
            if self._loading:
                return False
            self._loading = True
            self._load_error = None

        if artifacts_dir is None:
            artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
        else:
            artifacts_dir = Path(artifacts_dir)

        ckpt_path = artifacts_dir / "ncf.pt"
        meta_path = artifacts_dir / "ncf_meta.json"

        if not ckpt_path.exists() or not meta_path.exists():
            with self._lock:
                self._loading = False
                self._load_error = f"Model files not found: {ckpt_path}, {meta_path}"
            return False

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.user2idx = {int(k): v for k, v in meta["user2idx"].items()}
            self.item2idx = {int(k): v for k, v in meta["item2idx"].items()}
            self.idx2item = {k: int(v) for k, v in meta["idx2item"].items()}
            self.config = meta.get("config", {})
            self.num_users = meta.get("num_users", len(self.user2idx))
            self.num_items = meta.get("num_items", len(self.item2idx))

            emb_dim = self.config.get("embedding_dim", 32)
            hidden_dim = self.config.get("hidden_dim", 64)

            self.model = NCF(self.num_users, self.num_items, emb_dim, hidden_dim)
            self.model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
            self.model.eval()
            
            with self._lock:
                self._loaded = True
                self._loading = False
            print(f"[NCFEngine] Model loaded successfully: {self.num_users} users, {self.num_items} items")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"[NCFEngine] Failed to load model: {error_msg}")
            with self._lock:
                self._loading = False
                self._load_error = error_msg
            return False

    def load_async(self, artifacts_dir: str | Path | None = None) -> None:
        """在后台线程异步加载模型，不阻塞主线程"""
        def _load():
            self.load(artifacts_dir)
        
        self._load_thread = threading.Thread(target=_load, daemon=True)
        self._load_thread.start()
        print("[NCFEngine] Async loading started...")

    def is_ready(self) -> bool:
        """检查模型是否已加载完成"""
        with self._lock:
            return self._loaded and self.model is not None

    def is_loading(self) -> bool:
        """检查是否正在加载中"""
        with self._lock:
            return self._loading

    def get_status(self) -> dict[str, Any]:
        """获取模型加载状态信息"""
        with self._lock:
            return {
                "ready": self._loaded,
                "loading": self._loading,
                "error": self._load_error,
                "users": len(self.user2idx),
                "items": len(self.item2idx),
            }

    def score(self, user_id: int, item_ids: list[int], batch_size: int = 256) -> dict[int, float]:
        """Return NCF scores for given user and items."""
        if not self.is_ready():
            return {}

        if user_id not in self.user2idx:
            return {}

        u_idx = self.user2idx[user_id]
        valid_items = [mid for mid in item_ids if mid in self.item2idx]
        if not valid_items:
            return {}

        item_indices = [self.item2idx[mid] for mid in valid_items]
        scores: dict[int, float] = {}

        with torch.no_grad():
            for i in range(0, len(item_indices), batch_size):
                batch_items = item_indices[i : i + batch_size]
                u_tensor = torch.tensor([u_idx] * len(batch_items), dtype=torch.long)
                i_tensor = torch.tensor(batch_items, dtype=torch.long)
                logits = self.model(u_tensor, i_tensor)
                probs = torch.sigmoid(logits).cpu().numpy()
                for mid, score in zip(valid_items[i : i + batch_size], probs):
                    scores[mid] = float(score)

        return scores

    def rank(self, user_id: int, item_ids: list[int], top_k: int = 10) -> list[tuple[int, float]]:
        """Rank items by NCF score and return top-k (item_id, score)."""
        scores = self.score(user_id, item_ids)
        if not scores:
            return []
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# Global singleton instance
ncf_engine = NCFEngine()
