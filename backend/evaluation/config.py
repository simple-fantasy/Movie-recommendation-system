from dataclasses import dataclass, asdict


@dataclass
class EvalProtocolConfig:
    k: int = 10
    like_threshold: float = 4.0
    test_items_per_user: int = 3
    recall_k_hybrid: int = 200
    min_user_interactions: int = 16
    n_test_users: int = 10000
    n_phase1_users: int = 100
    candidate_mode: str = "full_ranking"
    sim_topk_per_movie: int = 50
    per_seed_limit: int = 50
    itemcf_min_ratings_per_movie: int = 50
    itemcf_min_ratings_per_user: int = 5
    itemcf_normalize: bool = True
    seed: int = 42
    ncf_model_path: str = "backend/artifacts/ncf_v2.pt"
    ncf_meta_path: str = "backend/artifacts/ncf_v2_meta.json"
    output_dir: str = "backend/artifacts"

    def __post_init__(self):
        if self.min_user_interactions < self.test_items_per_user + 2:
            raise ValueError(
                f"min_user_interactions ({self.min_user_interactions}) "
                f"must be >= test_items_per_user ({self.test_items_per_user}) + 2"
            )
        if self.n_test_users <= self.n_phase1_users:
            raise ValueError(
                f"n_test_users ({self.n_test_users}) "
                f"must be > n_phase1_users ({self.n_phase1_users})"
            )

    def to_dict(self):
        return asdict(self)
