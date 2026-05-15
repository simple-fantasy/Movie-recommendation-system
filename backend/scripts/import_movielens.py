from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from backend.app import create_app, db
from backend.app.models import Movie, Rating, User


def _parse_year(title: str) -> tuple[str, int | None]:
    m = re.search(r"\((\d{4})\)\s*$", title)
    if not m:
        return title, None
    year = int(m.group(1))
    clean_title = title[: m.start()].strip()
    return clean_title, year


def import_latest_small(data_dir: Path) -> None:
    movies_path = data_dir / "movies.csv"
    ratings_path = data_dir / "ratings.csv"

    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    movie_rows = []
    for row in movies_df.itertuples(index=False):
        title, year = _parse_year(str(row.title))
        movie_rows.append(Movie(id=int(row.movieId), title=title, year=year, genres=str(row.genres)))

    db.session.bulk_save_objects(movie_rows)
    db.session.commit()

    user_ids = ratings_df["userId"].drop_duplicates().tolist()
    for uid in user_ids:
        u = User(id=int(uid), username=f"user{uid}")
        u.set_password("password")
        db.session.add(u)
    db.session.commit()

    rating_rows = []
    for row in ratings_df.itertuples(index=False):
        ts = None
        if getattr(row, "timestamp", None) is not None:
            ts = datetime.utcfromtimestamp(int(row.timestamp))
        rating_rows.append(
            Rating(
                user_id=int(row.userId),
                movie_id=int(row.movieId),
                rating=float(row.rating),
                timestamp=ts,
            )
        )

    db.session.bulk_save_objects(rating_rows)
    db.session.commit()


def import_csv_chunked(
    data_dir: Path,
    chunksize: int,
    user_mod: int,
    max_ratings: int | None,
) -> None:
    movies_path = data_dir / "movies.csv"
    ratings_path = data_dir / "ratings.csv"

    movies_df = pd.read_csv(movies_path)
    movie_rows = []
    for row in movies_df.itertuples(index=False):
        title, year = _parse_year(str(row.title))
        movie_rows.append(Movie(id=int(row.movieId), title=title, year=year, genres=str(row.genres)))
    db.session.bulk_save_objects(movie_rows)
    db.session.commit()

    if user_mod < 1:
        user_mod = 1

    created_users: set[int] = set()
    imported = 0

    for chunk in pd.read_csv(ratings_path, chunksize=chunksize):
        if max_ratings is not None and imported >= max_ratings:
            break

        if user_mod > 1:
            chunk = chunk[chunk["userId"].astype(int) % user_mod == 0]
        if chunk.empty:
            continue

        if max_ratings is not None:
            remain = max_ratings - imported
            if remain <= 0:
                break
            if len(chunk) > remain:
                chunk = chunk.iloc[:remain]

        user_ids = chunk["userId"].astype(int).drop_duplicates().tolist()
        new_ids = [uid for uid in user_ids if uid not in created_users]
        for uid in new_ids:
            u = User(id=int(uid), username=f"user{uid}")
            u.set_password("password")
            db.session.add(u)
        db.session.commit()
        created_users.update(new_ids)

        rating_rows = []
        for row in chunk.itertuples(index=False):
            ts = None
            if getattr(row, "timestamp", None) is not None:
                ts = datetime.utcfromtimestamp(int(row.timestamp))
            rating_rows.append(
                Rating(
                    user_id=int(row.userId),
                    movie_id=int(row.movieId),
                    rating=float(row.rating),
                    timestamp=ts,
                )
            )

        db.session.bulk_save_objects(rating_rows)
        db.session.commit()
        imported += len(rating_rows)


def import_100k(data_dir: Path) -> None:
    item_path = data_dir / "u.item"
    data_path = data_dir / "u.data"

    movies_df = pd.read_csv(item_path, sep="|", header=None, encoding="latin-1")
    movies_df = movies_df[[0, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]]
    movies_df.columns = [
        "movie_id",
        "title",
        "unknown",
        "Action",
        "Adventure",
        "Animation",
        "Children's",
        "Comedy",
        "Crime",
        "Documentary",
        "Drama",
        "Fantasy",
        "Film-Noir",
        "Horror",
        "Musical",
        "Mystery",
        "Romance",
        "Sci-Fi",
        "Thriller",
        "War",
        "Western",
    ]

    genre_cols = movies_df.columns[2:]
    movie_rows = []
    for row in movies_df.itertuples(index=False):
        title, year = _parse_year(str(row.title))
        genres = [c for c in genre_cols if int(getattr(row, c.replace("'", ""))) == 1]
        movie_rows.append(Movie(id=int(row.movie_id), title=title, year=year, genres="|".join(genres)))

    db.session.bulk_save_objects(movie_rows)
    db.session.commit()

    ratings_df = pd.read_csv(data_path, sep="\t", header=None)
    ratings_df.columns = ["user_id", "movie_id", "rating", "timestamp"]

    user_ids = ratings_df["user_id"].drop_duplicates().tolist()
    for uid in user_ids:
        u = User(id=int(uid), username=f"user{uid}")
        u.set_password("password")
        db.session.add(u)
    db.session.commit()

    rating_rows = []
    for row in ratings_df.itertuples(index=False):
        ts = datetime.utcfromtimestamp(int(row.timestamp))
        rating_rows.append(
            Rating(
                user_id=int(row.user_id),
                movie_id=int(row.movie_id),
                rating=float(row.rating),
                timestamp=ts,
            )
        )

    db.session.bulk_save_objects(rating_rows)
    db.session.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument("--user-mod", type=int, default=1)
    parser.add_argument("--max-ratings", type=int, default=0)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"data dir not found: {data_dir}")

    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        if (data_dir / "movies.csv").exists() and (data_dir / "ratings.csv").exists():
            max_ratings = int(args.max_ratings) if int(args.max_ratings) > 0 else None
            ratings_path = data_dir / "ratings.csv"
            if ratings_path.stat().st_size > 50 * 1024 * 1024 or max_ratings is not None or int(args.user_mod) > 1:
                import_csv_chunked(
                    data_dir,
                    chunksize=int(args.chunksize),
                    user_mod=int(args.user_mod),
                    max_ratings=max_ratings,
                )
            else:
                import_latest_small(data_dir)
        elif (data_dir / "u.item").exists() and (data_dir / "u.data").exists():
            import_100k(data_dir)
        else:
            raise SystemExit("unrecognized movielens format: expected movies.csv/ratings.csv or u.item/u.data")


if __name__ == "__main__":
    main()
