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
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        ratings = Rating.query.with_entities(Rating.user_id, Rating.movie_id, Rating.rating).all()
        if not ratings:
            raise SystemExit("no ratings in database")

        df = pd.DataFrame(ratings, columns=["user_id", "movie_id", "rating"])
        user_codes, user_uniques = pd.factorize(df["user_id"], sort=True)
        movie_codes, movie_uniques = pd.factorize(df["movie_id"], sort=True)

        x = coo_matrix(
            (
                df["rating"].astype(np.float32).to_numpy(),
                (movie_codes.astype(np.int32), user_codes.astype(np.int32)),
            ),
            shape=(len(movie_uniques), len(user_uniques)),
        ).tocsr()

        n_neighbors = min(int(args.topk) + 1, x.shape[0])
        nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine", algorithm="brute")
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


if __name__ == "__main__":
    main()
