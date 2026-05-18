from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from sklearn.neighbors import NearestNeighbors

from backend.app import create_app, db
from backend.app.models import MovieSimilarity, Rating


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topk", type=int, default=50)
    parser.add_argument("--min-ratings-per-movie", type=int, default=50,
                        help="Only keep movies with >= N ratings")
    parser.add_argument("--min-ratings-per-user", type=int, default=5,
                        help="Only keep users with >= N ratings")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("Loading ratings from DB...")
        ratings = Rating.query.with_entities(
            Rating.user_id, Rating.movie_id, Rating.rating
        ).all()
        if not ratings:
            raise SystemExit("no ratings in database")
        print(f"  {len(ratings)} ratings loaded")

        df = pd.DataFrame(ratings, columns=["user_id", "movie_id", "rating"])

        # Filter movies by min ratings
        if args.min_ratings_per_movie > 1:
            movie_counts = df.groupby("movie_id").size()
            keep_movies = set(movie_counts[movie_counts >= args.min_ratings_per_movie].index)
            before = df["movie_id"].nunique()
            df = df[df["movie_id"].isin(keep_movies)]
            print(f"  Movies: {before} -> {df['movie_id'].nunique()} "
                  f"(min {args.min_ratings_per_movie} ratings)")

        # Filter users by min ratings
        if args.min_ratings_per_user > 1:
            user_counts = df.groupby("user_id").size()
            keep_users = set(user_counts[user_counts >= args.min_ratings_per_user].index)
            before = df["user_id"].nunique()
            df = df[df["user_id"].isin(keep_users)]
            print(f"  Users: {before} -> {df['user_id'].nunique()} "
                  f"(min {args.min_ratings_per_user} ratings)")

        print(f"  Filtered ratings: {len(df)}")
        print(f"  Sparsity: {len(df) / (df['user_id'].nunique() * df['movie_id'].nunique()):.4%}")

        user_codes, user_uniques = pd.factorize(df["user_id"], sort=True)
        movie_codes, movie_uniques = pd.factorize(df["movie_id"], sort=True)

        print(f"Building {len(movie_uniques)}x{len(user_uniques)} matrix...")
        x = coo_matrix(
            (
                df["rating"].astype(np.float32).to_numpy(),
                (movie_codes.astype(np.int32), user_codes.astype(np.int32)),
            ),
            shape=(len(movie_uniques), len(user_uniques)),
        ).tocsr()
        print(f"  Matrix built, {x.nnz} nonzeros")

        n_neighbors = min(int(args.topk) + 1, x.shape[0])
        nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine", algorithm="brute")
        print(f"Fitting NearestNeighbors (cosine, brute) on {x.shape}...")
        nn.fit(x)
        distances, indices = nn.kneighbors(x, return_distance=True)

        MovieSimilarity.query.delete()
        db.session.commit()

        rows: list[MovieSimilarity] = []
        for i in range(x.shape[0]):
            mid = int(movie_uniques[i])
            for dist, j in zip(distances[i], indices[i]):
                if i == int(j):
                    continue
                score = float(1.0 - float(dist))
                if score <= 0:
                    continue
                rows.append(
                    MovieSimilarity(
                        movie_id=mid,
                        similar_movie_id=int(movie_uniques[int(j)]),
                        score=score,
                    )
                )

        db.session.bulk_save_objects(rows)
        db.session.commit()
        print(f"  Saved {len(rows)} similarity pairs")


if __name__ == "__main__":
    main()
