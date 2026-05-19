# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dev server (port 5000)
python backend/run.py

# Data import (MovieLens 32M)
python -m backend.scripts.import_fast --data-dir data/ml-32m

# Train models
python -m backend.scripts.train_itemcf --min-ratings-per-movie 50 --min-ratings-per-user 5 --normalize
python -m backend.scripts.train_ncf --epochs 10 --batch-size 4096 --hidden-dim 128 --device cpu

# Offline evaluation
python -m backend.scripts.evaluate_models --models all --k 10

# One-shot pipeline (verify data → train ItemCF → train NCF → evaluate)
python -m backend.scripts.run_all_tests

# Create demo user (demo / demo123)
python -m backend.scripts.seed_demo_user

# Run integration tests
python scripts/tests/test_all_modules.py
```

## Architecture

### App factory pattern

`backend/app/__init__.py` is the app factory (`create_app()`). It initializes SQLAlchemy, Flask-Login, Flask-Caching (SimpleCache, in-memory), Migrate, and registers the `"main"` blueprint from `routes.py`. On first startup, `seed.py` auto-creates 20 sample movies + demo user if the DB is empty. A background thread preloads the NCF model and enriches TMDB metadata.

### Configuration flow

`backend/settings.py` uses **Pydantic BaseSettings** to load env vars from `.env`. `backend/config.py` bridges those settings into Flask's `app.config`. Always use `settings.py` (not raw `os.environ`) to read config — it validates types and ranges.

### Database

SQLAlchemy ORM with 14+ models defined in `backend/app/models.py`. MySQL in production via PyMySQL, SQLite in dev (auto-detected; falls back to `data/app.db`). Alembic migrations live in `backend/migrations/`.

### Recommendation pipeline

Three strategies, all served from `GET /api/recommendations?strategy=...`:

1. **ItemCF** (default/primary) — precomputed cosine similarity via scikit-learn NearestNeighbors, stored in `movie_similarity` table. Supports explainable "because you liked X" reasons.
2. **NCF** — PyTorch GMF model loaded by `NCFEngine` singleton in `backend/app/ncf_engine.py`. Loads asynchronously from `backend/artifacts/ncf.pt` on first request.
3. **Hybrid** — ItemCF generates recall candidates, NCF reranks them. Falls back to ItemCF if NCF not available.

Cold-start users (no ratings) get popular movies as fallback for all strategies.

### Frontend: Hybrid server-rendered + SPA

Templates are Jinja2 (`backend/app/templates/`). Each page loads Vue.js 3 (CDN, Options API) with a matching `js/page-*.js` file. Bootstrap 5 dark theme. ECharts for dashboards. Not an API-separated SPA — Flask serves pages directly.

### Routes organization

- `backend/app/routes.py` (~3100 lines) — the `"main"` Blueprint: all user-facing API endpoints + page routes. Auth, movies, ratings, recommendations, reviews, collections, notifications, charts, user profiles, movie lists, stats, search, export, evaluation metrics.
- `backend/app/admin_routes.py` (~1100 lines) — `/admin` Blueprint for admin management pages.

### Key patterns

- **NCF model is a singleton** loaded once into memory via `NCFEngine` in `ncf_engine.py`. It exposes `rank(user_id, candidate_ids)` for inference. Callers should check `ncf_engine.is_ready` before using it.
- **Rate limiting** (`rate_limit.py`) is an in-memory sliding window. Disabled by default (`RATE_LIMIT_ENABLED=False`).
- **Structured logging** — `logging_config.py` sets up structlog with JSON output, with fallback to standard logging.
- **User behavior tracking** — `behavior_tracker.py` provides decorators and functions to log user actions (view, rate, search, click) to the `user_behaviors` table.
- **Tests are procedural scripts**, not pytest/unittest. Run them as standalone Python files: `python scripts/tests/test_all_modules.py`. Individual modules can be run separately (e.g., `python scripts/tests/test_reviews.py`).
- **Decorators** — `@admin_required` and `@active_user_required` in `decorators.py` for route protection.
