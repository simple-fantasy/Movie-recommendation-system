"""
Fast ml-32m import using raw SQL bulk operations + pandas multi-row INSERT.

Usage:
  python -m backend.scripts.import_fast --data-dir data/ml-32m
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text as sa_text

from backend.app import create_app, db
from backend.app.models import Movie, User


def _parse_year(title: str) -> tuple[str, int | None]:
    m = re.search(r"\((\d{4})\)\s*$", title)
    if not m:
        return title, None
    year = int(m.group(1))
    clean_title = title[: m.start()].strip()
    return clean_title, year


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    movies_csv = data_dir / "movies.csv"
    ratings_csv = data_dir / "ratings.csv"

    if not movies_csv.exists() or not ratings_csv.exists():
        raise SystemExit(f"CSV files not found in {data_dir}")

    app = create_app()
    with app.app_context():
        engine = db.engine

        # Clear seed data inserted by create_app()
        db.session.execute(sa_text("DELETE FROM ratings"))
        db.session.execute(sa_text("DELETE FROM users"))
        db.session.execute(sa_text("DELETE FROM movies"))
        db.session.commit()

        # Step 1: Import movies (87K rows, fast)
        print("Step 1/3: Importing movies...")
        movie_rows = []
        with open(movies_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                movie_id = int(row[0])
                title_raw = row[1]
                genres = row[2]
                title, year = _parse_year(title_raw)
                movie_rows.append(
                    Movie(id=movie_id, title=title, year=year, genres=genres)
                )
        db.session.bulk_save_objects(movie_rows)
        db.session.commit()
        print(f"  {len(movie_rows)} movies imported")

        # Step 2: Import users from unique userIds in ratings.csv
        print("Step 2/3: Collecting unique users from ratings.csv...")
        user_ids_set: set[int] = set()
        chunksize = 2_000_000
        total_rows = 0
        for chunk in pd.read_csv(ratings_csv, usecols=["userId"], chunksize=chunksize):
            user_ids_set.update(chunk["userId"].astype(int).tolist())
            total_rows += len(chunk)
            if total_rows % 10_000_000 == 0:
                print(f"  Scanned {total_rows/1_000_000:.0f}M rows for unique users...")

        print(f"  {len(user_ids_set)} unique users found")

        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash("password")

        # Batch insert users with parameterized SQL for speed
        print("  Inserting users into database...")
        user_ids = sorted(user_ids_set)
        batch_size = 5000
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i+batch_size]
            placeholders = ", ".join(f"(:uid_{j}, :uname_{j}, :pwd_{j})" for j in range(len(batch)))
            params = {}
            for j, uid in enumerate(batch):
                params[f"uid_{j}"] = int(uid)
                params[f"uname_{j}"] = f"user{uid}"
                params[f"pwd_{j}"] = pwd_hash
            sql = f"INSERT IGNORE INTO users (id, username, password_hash) VALUES {placeholders}"
            db.session.execute(sa_text(sql), params)
            if (i + batch_size) % 50_000 == 0:
                db.session.commit()
                print(f"  Users: {min(i+batch_size, len(user_ids))}/{len(user_ids)}")
        db.session.commit()
        print(f"  {len(user_ids)} users imported")

        # Step 3: Import ratings via pandas to_sql (method='multi' = fast)
        print("Step 3/3: Importing ratings (multi-row INSERT)...")
        ratings_chunksize = 500_000
        total = 0
        for chunk in pd.read_csv(ratings_csv, chunksize=ratings_chunksize):
            chunk.columns = ["user_id", "movie_id", "rating", "timestamp"]
            # Convert Unix timestamp to MySQL datetime
            chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], unit="s")
            chunk.to_sql(
                "ratings",
                engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=10_000,
            )
            total += len(chunk)
            if total % 5_000_000 == 0:
                print(f"  {total/1_000_000:.0f}M ratings imported...")
        print(f"  {total} ratings imported")

        # Verify
        result = db.session.execute(
            sa_text("SELECT COUNT(*) FROM movies UNION ALL SELECT COUNT(*) FROM users UNION ALL SELECT COUNT(*) FROM ratings")
        )
        counts = [r[0] for r in result]
        print(f"\nDone! Movies: {counts[0]}, Users: {counts[1]}, Ratings: {counts[2]}")


if __name__ == "__main__":
    main()
