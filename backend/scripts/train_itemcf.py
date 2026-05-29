from __future__ import annotations

import argparse

import pandas as pd

from backend.app import create_app, db
from backend.app.models import MovieSimilarity, Rating
from backend.app.similarity import compute_item_similarity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topk", type=int, default=50)
    parser.add_argument("--min-ratings-per-movie", type=int, default=50,
                        help="Only keep movies with >= N ratings")
    parser.add_argument("--min-ratings-per-user", type=int, default=5,
                        help="Only keep users with >= N ratings")
    parser.add_argument("--normalize", action=argparse.BooleanOptionalAction, default=True,
                        help="Center ratings by user mean (adjusted cosine similarity)")
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

        before_movies = df["movie_id"].nunique()
        before_users = df["user_id"].nunique()

        sims = compute_item_similarity(
            df,
            topk=int(args.topk),
            min_ratings_per_movie=int(args.min_ratings_per_movie),
            min_ratings_per_user=int(args.min_ratings_per_user),
            normalize=args.normalize,
        )

        after_movies = len(sims)
        after_users = df["user_id"].nunique()
        print(f"  Movies: {before_movies} -> {after_movies} "
              f"(min {args.min_ratings_per_movie} ratings)")
        print(f"  Users: {before_users} -> {after_users} "
              f"(min {args.min_ratings_per_user} ratings)")
        print(f"  Ratings normalized: {args.normalize}")

        # Persist to DB
        MovieSimilarity.query.delete()
        db.session.commit()

        rows: list[MovieSimilarity] = []
        for mid, pairs in sims.items():
            for sid, score in pairs:
                rows.append(
                    MovieSimilarity(
                        movie_id=mid,
                        similar_movie_id=sid,
                        score=score,
                    )
                )

        db.session.bulk_save_objects(rows)
        db.session.commit()
        print(f"  Saved {len(rows)} similarity pairs")


if __name__ == "__main__":
    main()
