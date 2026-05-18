"""
Seed a demo user with pre-populated ratings for presentation.

Usage:
  python -m backend.scripts.seed_demo_user

Creates user 'demo' / password 'demo123' with ~30 ratings on popular movies,
ensuring ItemCF can generate personalized recommendations immediately.
"""

from __future__ import annotations

import random

from werkzeug.security import generate_password_hash

from backend.app import create_app, db
from backend.app.models import Movie, Rating, User


DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"
NUM_RATINGS = 30


def main() -> None:
    app = create_app()
    with app.app_context():
        # Find or create demo user
        user = User.query.filter_by(username=DEMO_USERNAME).first()
        if user is None:
            user = User(
                username=DEMO_USERNAME,
                password_hash=generate_password_hash(DEMO_PASSWORD),
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created demo user: {DEMO_USERNAME} / {DEMO_PASSWORD}")
        else:
            # Clear existing ratings for clean demo state
            Rating.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            print(f"Cleared existing ratings for demo user (id={user.id})")

        # Pick diverse popular movies (high rating count) from different genres
        popular_movies = (
            db.session.query(
                Movie.id,
                Movie.title,
                Movie.genres,
                db.func.count(Rating.id).label("cnt"),
                db.func.avg(Rating.rating).label("avg_rating"),
            )
            .join(Rating, Rating.movie_id == Movie.id)
            .group_by(Movie.id)
            .having(db.func.count(Rating.id) >= 50)
            .order_by(db.desc("cnt"))
            .limit(200)
            .all()
        )

        if not popular_movies:
            print("ERROR: No movies found. Import data first with import_movielens.py")
            return

        # Select NUM_RATINGS movies with genre diversity
        rng = random.Random(42)
        # Weight: prefer higher avg rating with some randomness
        scored = [(mid, title, genres, float(avg) + rng.uniform(-0.5, 0.5))
                   for mid, title, genres, _cnt, avg in popular_movies]
        scored.sort(key=lambda x: x[3], reverse=True)

        # Pick top ~70 by score, then randomly sample from those
        candidates = scored[:70]
        rng.shuffle(candidates)
        selected = candidates[:NUM_RATINGS]

        # Assign ratings: sample from a realistic distribution (skewed to high ratings)
        rating_pool = [3.0, 3.0, 3.5, 3.5, 4.0, 4.0, 4.0, 4.5, 4.5, 5.0]
        rows = []
        for mid, _title, _genres, _score in selected:
            r = Rating(
                user_id=user.id,
                movie_id=int(mid),
                rating=rng.choice(rating_pool),
            )
            rows.append(r)

        db.session.bulk_save_objects(rows)
        db.session.commit()

        # Print summary
        genres_seen: dict[str, int] = {}
        for _mid, _title, genres, _score in selected:
            if genres:
                for g in genres.split("|"):
                    genres_seen[g] = genres_seen.get(g, 0) + 1

        rated_titles = [(title, genres) for _mid, title, genres, _score in selected[:5]]
        print(f"Seeded {len(rows)} ratings for demo user (id={user.id})")
        print(f"Genres covered: {dict(sorted(genres_seen.items(), key=lambda x: -x[1]))}")
        print(f"Sample movies rated: {rated_titles}")
        print(f"\nDemo login: username={DEMO_USERNAME} password={DEMO_PASSWORD}")
        print("Visit http://127.0.0.1:5000/app and log in as 'demo' to see recommendations.")


if __name__ == "__main__":
    main()
