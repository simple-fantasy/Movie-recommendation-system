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

`backend/app/__init__.py` is the app factory (`create_app()`). It initializes SQLAlchemy, Flask-Login, Flask-Caching (FileSystemCache, persisted to disk), Migrate, and registers the `"main"` blueprint from `routes.py` and the `/admin` blueprint from `admin_routes.py`. On first startup, `seed.py` auto-creates 20 sample movies + demo user if the DB is empty. A background thread enriches TMDB posters, and a `before_request` hook triggers async NCF model preloading on the first request.

**Jinja2 + Vue.js coexistence**: `app.jinja_env.undefined = ChainableUndefined` prevents Jinja2 from crashing on Vue `{{ }}` expressions — undefined variables chain to empty string instead of raising `UndefinedError`.

**Login redirect handling**: `login_manager.unauthorized_handler` returns JSON `{"error": "请先登录"}` (401) for `/api/*` routes and a 302 redirect to `main.index` for page routes, so the Vue SPA doesn't receive HTML on auth failures.

### Configuration flow

`backend/settings.py` uses **Pydantic BaseSettings** to load env vars from `.env` with validation (key strength, DB driver, embedding dims, rate limit ranges). `backend/config.py` bridges validated settings into Flask's `app.config` as class attributes. Always use `settings.py` (not raw `os.environ`) to read config at runtime.

### Database

SQLAlchemy ORM with 14+ models defined in `backend/app/models.py`. MySQL in production via PyMySQL, SQLite in dev (auto-detected; falls back to `data/app.db`). Alembic migrations live in `backend/migrations/`. At startup, the app tries to create performance indexes on `ratings.timestamp` and `users.created_at` (with try/except for MySQL 5.7 compatibility). Connection pool uses `pool_pre_ping=True` to detect stale connections.

### Recommendation pipeline

Three strategies, all served from `GET /api/recommendations?strategy=...`:

1. **ItemCF** (default/primary) — precomputed cosine similarity via scikit-learn NearestNeighbors, stored in `movie_similarity` table. Supports explainable "because you liked X" reasons.
2. **NCF** — PyTorch GMF model loaded by `NCFEngine` singleton in `backend/app/ncf_engine.py`. Loads asynchronously from `backend/artifacts/ncf.pt` on first request. Model definition matches `train_ncf.py` — dual embedding + 3-layer MLP with sigmoid output.
3. **Hybrid** — ItemCF generates recall candidates, NCF reranks them. Falls back to ItemCF if NCF not available.

Cold-start users (no ratings) get popular movies as fallback for all strategies.

### Frontend: Hybrid server-rendered + SPA

Templates are Jinja2 (`backend/app/templates/`). Each page loads Vue.js 3 (CDN, Options API) with a matching `js/page-*.js` file. Bootstrap 5 dark theme. ECharts for dashboards. Not an API-separated SPA — Flask serves pages directly.

**Vue component system**: Reusable Vue components (MovieCard, SkeletonGrid, StarRating, etc.) are defined in `vue-components.js` and exposed on `window.CinemaComponents`. Page-level JS files access them via destructuring: `const { MovieCard, SkeletonGrid } = window.CinemaComponents;`.

**API client** (`api.js`): A single `api(path, options)` function wraps `fetch()`. GET requests to the same URL are automatically deduplicated (concurrent calls share one promise) via a pending request map. Non-200 responses are parsed for error messages — handles JSON errors, HTML redirects (401/403/404/5xx), and plain text.

### Routes organization

- `backend/app/routes.py` (~3100 lines) — the `"main"` Blueprint: all user-facing API endpoints + page routes. Auth, movies, ratings, recommendations, reviews, collections, notifications, charts, user profiles, movie lists, stats, search, export, evaluation metrics.
- `backend/app/admin_routes.py` (~1100 lines) — `/admin` Blueprint for admin management pages.

### Key patterns

- **NCF model is a singleton** loaded once into memory via `NCFEngine` in `ncf_engine.py`. It exposes `rank(user_id, candidate_ids)` and `score(user_id, item_ids)` for inference. Callers should check `ncf_engine.is_ready` before using it. The model definition class is replicated in `ncf_engine.py` (inference) and `train_ncf.py` (training) — keep them in sync.
- **Rate limiting** (`rate_limit.py`) is an in-memory sliding window. Disabled by default (`RATE_LIMIT_ENABLED=False`).
- **Structured logging** — `logging_config.py` sets up structlog with JSON output, with fallback to standard logging.
- **User behavior tracking** — `behavior_tracker.py` provides `@track_behavior(action_type, target_type, target_id, metadata)` decorator and `record_behavior_async()` function. Only records authenticated users; writes to `user_behaviors` table.
- **Tests are procedural scripts**, not pytest/unittest. Run them as standalone Python files: `python scripts/tests/test_all_modules.py`. Individual modules can be run separately (e.g., `python scripts/tests/test_reviews.py`).
- **Decorators** — `@admin_required` and `@active_user_required` in `decorators.py` for route protection. Both redirect unauthenticated users to login; `@admin_required` additionally checks `current_user.is_admin`.
