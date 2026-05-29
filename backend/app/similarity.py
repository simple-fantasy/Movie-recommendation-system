"""Shared ItemCF similarity computation.

Extracted from backend/scripts/train_itemcf.py to support:
- Training: compute similarity from ALL ratings → persist to DB
- Evaluation: compute similarity from training ratings only → no data leakage
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.neighbors import NearestNeighbors


def compute_item_similarity(
    ratings_df: pd.DataFrame,
    topk: int = 50,
    min_ratings_per_movie: int = 50,
    min_ratings_per_user: int = 5,
    normalize: bool = True,
) -> dict[int, list[tuple[int, float]]]:
    """Compute ItemCF cosine similarity from a ratings DataFrame.

    Pipeline: filter → normalize (user-mean centering) → sparse CSR matrix →
    NearestNeighbors(cosine) → distance-to-similarity conversion.

    Args:
        ratings_df: DataFrame with columns ["user_id", "movie_id", "rating"].
        topk: Number of similar movies to keep per movie.
        min_ratings_per_movie: Drop movies with fewer ratings.
        min_ratings_per_user: Drop users with fewer ratings.
        normalize: If True, center ratings by user mean (adjusted cosine).

    Returns:
        {movie_id: [(similar_movie_id, score), ...]} sorted by score descending.
        Scores are in [0, 1] (cosine similarity). Self-pairs excluded.
    """
    df = ratings_df.copy()

    # Filter movies by minimum ratings
    if min_ratings_per_movie > 1:
        movie_counts = df.groupby("movie_id").size()
        keep_movies = set(movie_counts[movie_counts >= min_ratings_per_movie].index)
        df = df[df["movie_id"].isin(keep_movies)]

    # Filter users by minimum ratings
    if min_ratings_per_user > 1:
        user_counts = df.groupby("user_id").size()
        keep_users = set(user_counts[user_counts >= min_ratings_per_user].index)
        df = df[df["user_id"].isin(keep_users)]

    if df.empty:
        return {}

    # User-mean centering (adjusted cosine similarity)
    if normalize:
        user_means = df.groupby("user_id")["rating"].transform("mean")
        df["rating"] = df["rating"] - user_means

    user_codes, user_uniques = pd.factorize(df["user_id"], sort=True)
    movie_codes, movie_uniques = pd.factorize(df["movie_id"], sort=True)

    x = coo_matrix(
        (
            df["rating"].astype(np.float32).to_numpy(),
            (movie_codes.astype(np.int32), user_codes.astype(np.int32)),
        ),
        shape=(len(movie_uniques), len(user_uniques)),
    ).tocsr()

    n_neighbors = min(topk + 1, x.shape[0])
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine", algorithm="brute")
    nn.fit(x)
    distances, indices = nn.kneighbors(x, return_distance=True)

    sims: dict[int, list[tuple[int, float]]] = {}
    for i in range(x.shape[0]):
        mid = int(movie_uniques[i])
        pairs: list[tuple[int, float]] = []
        for dist, j in zip(distances[i], indices[i]):
            if i == int(j):
                continue
            score = float(1.0 - float(dist))
            if score <= 0:
                continue
            pairs.append((int(movie_uniques[int(j)]), score))
        if pairs:
            sims[mid] = pairs

    return sims
