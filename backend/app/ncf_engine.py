"""
NCF (Neural Collaborative Filtering) 推理引擎。

基于 PyTorch 的 GMF (Generalized Matrix Factorization) 模型，
提供模型加载、评分预测和排序功能。

架构说明:
- NCF 模型: 双 Embedding + 3层 MLP，与 train_ncf.py 中的定义保持一致
- NCFEngine: 单例模式，管理模型的加载、状态和推理
- 支持异步加载，不阻塞 HTTP 请求线程
- PyTorch 不可用时优雅降级（TORCH_AVAILABLE 标志）

线程安全:
- _lock 保护 _loaded/_loading 等状态标志和模型引用
- score() 在锁内获取模型引用，避免与 load() 并发写入竞态

用法:
    from backend.app.ncf_engine import ncf_engine
    scores = ncf_engine.score(user_id, [1, 2, 3])
    ranked = ncf_engine.rank(user_id, candidates, top_k=10)
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

# ── PyTorch 可选导入 ──────────────────────────────────
# 当 PyTorch 未安装时，NCF 功能不可用但不会阻止应用启动
try:
    import torch
    from torch import nn

    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore
    nn = None  # type: ignore


# ═══════════════════════════════════════════════════════
# NCF 模型定义（与 backend/scripts/train_ncf.py 保持一致）
# ═══════════════════════════════════════════════════════

class NCF(nn.Module if TORCH_AVAILABLE else object):
    """
    Neural Collaborative Filtering 模型。

    GMF 架构: 用户/物品各一个 Embedding 向量 →
    拼接后通过 3 层 MLP → sigmoid 输出 0-1 的匹配概率。

    参数:
        num_users:     用户总数（决定 Embedding 表大小）
        num_items:     物品总数
        embedding_dim: 嵌入向量维度（默认 32）
        hidden_dim:    MLP 隐藏层维度（默认 64）
    """

    def __init__(self, num_users: int, num_items: int, embedding_dim: int, hidden_dim: int):
        if TORCH_AVAILABLE:
            super().__init__()
        # 用户 / 物品 Embedding 层
        self.user_emb = nn.Embedding(num_users, embedding_dim) if TORCH_AVAILABLE else None
        self.item_emb = nn.Embedding(num_items, embedding_dim) if TORCH_AVAILABLE else None

        # 3 层 MLP: (emb*2) → hidden → hidden/2 → 1
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

    def forward(self, user_idx: torch.Tensor, item_idx: torch.Tensor) -> torch.Tensor:
        """
        前向传播。

        参数:
            user_idx: [batch_size] 用户索引张量
            item_idx: [batch_size] 物品索引张量

        返回:
            [batch_size] logits（未经过 sigmoid 的原始分数）
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")
        u = self.user_emb(user_idx)          # [B, embedding_dim]
        i = self.item_emb(item_idx)          # [B, embedding_dim]
        x = torch.cat([u, i], dim=-1)        # [B, embedding_dim * 2]
        return self.mlp(x).squeeze(-1)       # [B]


# ═══════════════════════════════════════════════════════
# NCF 推理引擎（单例模式）
# ═══════════════════════════════════════════════════════

class NCFEngine:
    """
    NCF 模型推理引擎，全局单例。

    职责:
    1. 加载训练好的 NCF 模型和元数据
    2. 提供 score() 评分和 rank() 排序接口
    3. 管理加载状态（未加载 / 加载中 / 就绪 / 错误）
    4. 异步加载不阻塞主线程

    状态机:
        未初始化 → (load_async) → 加载中 → 就绪 / 错误
                                   ↓
                                 (load) 同步加载 → 就绪 / 错误
    """

    _instance: NCFEngine | None = None
    _lock = threading.Lock()            # 保护状态标志和模型引用的互斥锁

    def __new__(cls) -> NCFEngine:
        """单例创建——所有调用者共享同一个 NCFEngine 实例（线程安全）。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化状态字段，只执行一次（因为 __new__ 保证了单例）。"""
        if self._initialized:
            return
        self._initialized = True

        # ── 模型与映射表 ──
        self.model: NCF | None = None
        self.user2idx: dict[int, int] = {}    # 用户ID → 模型索引
        self.item2idx: dict[int, int] = {}    # 物品ID → 模型索引
        self.idx2item: dict[str, int] = {}    # 模型索引字符串 → 物品ID（JSON key 为字符串）
        self.config: dict[str, Any] = {}       # 模型配置（embedding_dim, hidden_dim 等）
        self.num_users = 0
        self.num_items = 0

        # ── 状态标志（由 _lock 保护）──
        self._loaded = False                   # 模型是否已就绪
        self._loading = False                  # 是否正在加载中
        self._load_error: str | None = None    # 最后一次加载错误信息
        self._load_thread: threading.Thread | None = None
        self._last_attempt_time = 0.0           # 上次尝试加载的时间戳（用于重试间隔控制）
        self._model_mtime = 0.0                 # 已加载模型文件的修改时间（用于检测更新）

    # ── 模型加载 ──────────────────────────────────────

    def load(self, artifacts_dir: str | Path | None = None) -> bool:
        """
        同步加载 NCF 模型。

        从 artifacts 目录读取 ncf.pt（PyTorch 权重）和 ncf_meta.json（映射元数据）。
        加载成功后设置 _loaded = True，后续 score()/rank() 调用即可使用。

        参数:
            artifacts_dir: 模型目录，默认 backend/artifacts/

        返回:
            True 加载成功 / False 失败（模型文件缺失、PyTorch 未安装等）
        """
        if not TORCH_AVAILABLE:
            print("[NCFEngine] PyTorch not available, skipping NCF model loading")
            with self._lock:
                self._load_error = "PyTorch not installed"
            return False

        # 检查状态：已加载直接返回，加载中防止重复加载
        with self._lock:
            if self._loaded:
                return True
            if self._loading:
                return False
            self._loading = True
            self._load_error = None

        # 确定模型文件路径
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
            # 1. 加载元数据（用户/物品 ID 映射表）
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.user2idx = {int(k): v for k, v in meta["user2idx"].items()}
            self.item2idx = {int(k): v for k, v in meta["item2idx"].items()}
            self.idx2item = {k: int(v) for k, v in meta["idx2item"].items()}  # str→int（JSON key 限制）
            self.config = meta.get("config", {})
            self.num_users = meta.get("num_users", len(self.user2idx))
            self.num_items = meta.get("num_items", len(self.item2idx))

            emb_dim = self.config.get("embedding_dim", 32)
            hidden_dim = self.config.get("hidden_dim", 64)

            # 2. 创建模型实例并加载训练权重
            self.model = NCF(self.num_users, self.num_items, emb_dim, hidden_dim)
            self.model.load_state_dict(torch.load(ckpt_path, map_location="cpu", weights_only=False))
            self.model.eval()  # 切换到评估模式（禁用 dropout/batch_norm 训练行为）

            # 记录加载时间戳和文件版本，用于重试间隔控制和自动更新检测
            import time as _time
            with self._lock:
                self._loaded = True
                self._loading = False
                self._last_attempt_time = _time.time()
                self._model_mtime = ckpt_path.stat().st_mtime
            print(f"[NCFEngine] Model loaded successfully: {self.num_users} users, {self.num_items} items")
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"[NCFEngine] Failed to load model: {error_msg}")
            import time as _time
            with self._lock:
                self._loading = False
                self._load_error = error_msg
                self._last_attempt_time = _time.time()
            return False

    def load_async(self, artifacts_dir: str | Path | None = None) -> None:
        """
        在后台守护线程中异步加载模型，不阻塞当前线程。

        典型使用场景: app 启动时调用，首个 HTTP 请求到来时可能尚未加载完毕，
        此时推荐接口会回退到 ItemCF 策略。
        """
        def _load():
            self.load(artifacts_dir)

        self._load_thread = threading.Thread(target=_load, daemon=True)
        self._load_thread.start()
        print("[NCFEngine] Async loading started...")

    def reload(self, artifacts_dir: str | Path | None = None) -> bool:
        """
        强制重新加载 NCF 模型（热重载）。

        先卸载当前模型，再重新从文件加载。用于训练新模型后不重启服务即可生效。
        加载过程同步执行，调用者负责在后台线程中使用以避免阻塞请求。

        返回:
            True 重新加载成功 / False 失败
        """
        with self._lock:
            self._loaded = False
            self._loading = False
            self._load_error = None
            self.model = None
            self.user2idx = {}
            self.item2idx = {}
            self.idx2item = {}
            self.config = {}
            self.num_users = 0
            self.num_items = 0
            self._model_mtime = 0.0

        print("[NCFEngine] Reloading model...")
        return self.load(artifacts_dir)

    def maybe_auto_reload(self, artifacts_dir: str | Path | None = None) -> bool:
        """
        检测模型文件是否已更新，如果更新则自动重新加载。

        通过比较 .pt 文件的修改时间判断是否需要重新加载。
        仅在模型已加载时检测。

        返回:
            True 检测到更新并重新加载 / False 无需更新或加载失败
        """
        if artifacts_dir is None:
            artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
        else:
            artifacts_dir = Path(artifacts_dir)

        ckpt_path = artifacts_dir / "ncf.pt"
        if not ckpt_path.exists():
            return False

        current_mtime = ckpt_path.stat().st_mtime
        with self._lock:
            if not self._loaded:
                return False
            if current_mtime <= self._model_mtime:
                return False  # 文件未更新

        print(f"[NCFEngine] New model detected (mtime {self._model_mtime} → {current_mtime}), reloading...")
        return self.reload(artifacts_dir)

    # ── 状态查询 ──────────────────────────────────────

    def is_ready(self) -> bool:
        """模型是否已加载就绪（线程安全）。"""
        with self._lock:
            return self._loaded and self.model is not None

    def is_loading(self) -> bool:
        """模型是否正在加载中（线程安全）。"""
        with self._lock:
            return self._loading

    def should_retry(self, retry_interval: float = 30.0) -> bool:
        """
        判断是否应该重新尝试加载模型。

        加载失败后，需要等待 retry_interval 秒才能重试，避免频繁失败。
        如果模型已加载但尚未检测到更新的模型文件，则不应重试。
        """
        import time as _time
        with self._lock:
            if self._loaded:
                return False
            if self._loading:
                return False
            now = _time.time()
            return (now - self._last_attempt_time) >= retry_interval

    def get_status(self) -> dict[str, Any]:
        """
        获取模型加载状态信息，用于 /api/ncf/status 健康检查端点。

        返回:
            {ready, loading, error, users, items, uptime_seconds}
        """
        import time as _time
        with self._lock:
            return {
                "ready": self._loaded,
                "loading": self._loading,
                "error": self._load_error,
                "users": len(self.user2idx),
                "items": len(self.item2idx),
                "last_attempt_ago": round(_time.time() - self._last_attempt_time, 1) if self._last_attempt_time else None,
            }

    # ── 推理接口 ──────────────────────────────────────

    def score(self, user_id: int, item_ids: list[int], batch_size: int = 256) -> dict[int, float]:
        """
        对给定用户和候选物品列表进行 NCF 评分。

        流程:
        1. 检查模型是否就绪
        2. 在锁内获取模型和映射引用的副本（防止与 load() 竞态）
        3. 将用户/物品 ID 转换为模型内部索引
        4. 分批前向传播，sigmoid 转概率，返回 {item_id: score}

        参数:
            user_id:    用户 ID
            item_ids:   候选物品 ID 列表
            batch_size: 每批处理的物品数（防止 OOM）

        返回:
            {item_id: score} 字典，score ∈ [0, 1]
            模型未就绪或用户不在训练集中时返回 {}
        """
        if not self.is_ready():
            return {}

        # 在锁内获取引用副本，防止 load() 并发修改 self.model/self.user2idx/self.item2idx
        with self._lock:
            model = self.model
            user2idx = self.user2idx
            item2idx = self.item2idx

        if model is None:
            return {}
        if user_id not in user2idx:
            return {}

        u_idx = user2idx[user_id]

        # 过滤掉不在训练集中的物品（模型无法为其生成 Embedding）
        valid_items = [mid for mid in item_ids if mid in item2idx]
        if not valid_items:
            return {}

        item_indices = [item2idx[mid] for mid in valid_items]
        scores: dict[int, float] = {}

        # 分批前向传播（no_grad 禁用梯度计算，节省内存和计算）
        with torch.no_grad():
            for i in range(0, len(item_indices), batch_size):
                batch_items = item_indices[i: i + batch_size]
                u_tensor = torch.tensor([u_idx] * len(batch_items), dtype=torch.long)
                i_tensor = torch.tensor(batch_items, dtype=torch.long)
                logits = model(u_tensor, i_tensor)
                probs = torch.sigmoid(logits).cpu().numpy()
                for mid, score in zip(valid_items[i: i + batch_size], probs):
                    scores[mid] = float(score)

        return scores

    def rank(self, user_id: int, item_ids: list[int], top_k: int = 10) -> list[tuple[int, float]]:
        """
        对候选物品进行 NCF 评分并返回 Top-K 排序结果。

        参数:
            user_id:  用户 ID
            item_ids: 候选物品 ID 列表
            top_k:    返回前 K 个结果

        返回:
            [(item_id, score), ...] 按 score 降序排列
            模型未就绪时返回 []
        """
        scores = self.score(user_id, item_ids)
        if not scores:
            return []
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# 模块级全局单例——所有模块通过此实例使用 NCF 引擎
ncf_engine = NCFEngine()
