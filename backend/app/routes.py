from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, session
from flask_login import current_user, login_required, login_user, logout_user

from backend.app import cache, db
from backend.app.models import (Movie, MovieSimilarity, Rating, RecommendationFeedback, User, Review, ReviewLike,
                               UserCollection, WatchLink, Notification, MovieChart, ChartItem, UserProfile,
                               MovieList, MovieListItem, MovieListLike, MovieListComment)
from backend.app.ncf_engine import ncf_engine
from backend.app.services import ProfileService


bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("portal.html")


@bp.post("/api/feedback")
@login_required
def submit_feedback():
    data = request.get_json(force=True)
    movie_id = data.get("movie_id")
    feedback = (data.get("feedback") or "").strip().lower()
    context = (data.get("context") or "").strip()

    if movie_id is None or not feedback:
        return jsonify({"error": "movie_id and feedback required"}), 400
    if feedback not in {"like", "dislike"}:
        return jsonify({"error": "feedback must be like or dislike"}), 400
    if len(context) > 64:
        return jsonify({"error": "context too long"}), 400

    movie = db.session.get(Movie, int(movie_id))
    if movie is None:
        return jsonify({"error": "movie not found"}), 404

    existing = RecommendationFeedback.query.filter_by(
        user_id=current_user.id, movie_id=movie.id, context=context
    ).first()
    if existing is None:
        existing = RecommendationFeedback(
            user_id=current_user.id,
            movie_id=movie.id,
            feedback=feedback,
            context=context,
        )
        db.session.add(existing)
    else:
        existing.feedback = feedback
        existing.created_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/api/my/persona")
@login_required
def my_persona():
    top_n = min(int(request.args.get("n") or 8), 20)
    like_threshold = float(request.args.get("like_threshold") or 4.0)

    rows = (
        db.session.query(Movie.genres, Rating.rating)
        .join(Movie, Movie.id == Rating.movie_id)
        .filter(Rating.user_id == current_user.id)
        .all()
    )
    if not rows:
        return jsonify({"labels": [], "values": [], "note": "no ratings"})

    scores: dict[str, float] = {}
    for genres, r in rows:
        if not genres:
            continue
        rr = float(r)
        if rr < like_threshold:
            continue
        for g in str(genres).split("|"):
            g = g.strip()
            if not g or g == "(no genres listed)":
                continue
            scores[g] = scores.get(g, 0.0) + rr

    if not scores:
        return jsonify({"labels": [], "values": [], "note": "no liked ratings"})

    items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [k for k, _v in items]
    vals = [float(v) for _k, v in items]
    maxv = max(vals) if vals else 1.0
    norm = [float(v / maxv * 100.0) for v in vals]
    return jsonify({"labels": labels, "values": norm})


@bp.get("/api/my/timeline")
@login_required
def my_timeline():
    rows = (
        db.session.query(Rating.timestamp, Rating.rating)
        .filter(Rating.user_id == current_user.id)
        .filter(Rating.timestamp.isnot(None))
        .all()
    )
    if not rows:
        return jsonify({"months": [], "counts": [], "avg_ratings": []})

    buckets: dict[str, list[float]] = {}
    for ts, r in rows:
        key = ts.strftime("%Y-%m")
        buckets.setdefault(key, []).append(float(r))

    months = sorted(buckets.keys())
    counts = [len(buckets[m]) for m in months]
    avgs = [float(sum(buckets[m]) / len(buckets[m])) if buckets[m] else 0.0 for m in months]
    return jsonify({"months": months, "counts": counts, "avg_ratings": avgs})


@bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@bp.get("/enhanced-dashboard")
def enhanced_dashboard():
    """增强版数据看板页面"""
    return render_template("enhanced_dashboard.html")


@bp.get("/advanced-search")
def advanced_search_page():
    """高级搜索页面"""
    return render_template("advanced_search.html")


@bp.get("/login")
def login_page():
    return render_template("login.html")


@bp.get("/recommendations")
def recommendations_page():
    return render_template("recommendations.html")


@bp.get("/app")
def web_app():
    return render_template("app.html")


@bp.get("/movie/<int:movie_id>")
def movie_page(movie_id: int):
    return render_template("movie.html", movie_id=movie_id)


@bp.get("/collections")
def collections_page():
    """用户收藏页面"""
    return render_template("collections.html")


@bp.get("/ratings")
def ratings_page():
    """用户评分记录页面"""
    return render_template("ratings.html")


@bp.get("/reviews")
def reviews_page():
    """用户评论页面"""
    return render_template("reviews.html")


@bp.get("/api/health")
def health():
    """增强版健康检查端点
    
    返回系统各组件状态，用于监控和故障排查。
    """
    status = {"status": "ok", "services": {}}
    
    # 检查数据库连接
    try:
        db.session.execute(db.text("SELECT 1"))
        status["services"]["database"] = "ok"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # 检查NCF模型状态
    try:
        from backend.app.ncf_engine import ncf_engine
        if ncf_engine.is_ready():
            status["services"]["ncf_model"] = "ready"
        elif ncf_engine.is_loading():
            status["services"]["ncf_model"] = "loading"
        else:
            status["services"]["ncf_model"] = "not_loaded"
    except Exception as e:
        status["services"]["ncf_model"] = f"error: {str(e)}"
    
    # 系统时间
    status["timestamp"] = datetime.utcnow().isoformat()
    
    return jsonify(status)


@bp.get("/api/ncf/status")
def ncf_status():
    """查询NCF模型加载状态"""
    return jsonify(ncf_engine.get_status())


@bp.post("/api/auth/register")
def register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "username already exists"}), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"id": user.id, "username": user.username})


@bp.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    
    # 检查账户是否被禁用
    if not user.is_active:
        return jsonify({"error": "账户已被禁用"}), 403

    # 执行登录（remember=True 持久化cookie，session.permanent 使PERMANENT_SESSION_LIFETIME生效）
    login_user(user, remember=True)
    session.permanent = True
    
    # 更新登录统计
    user.last_login = datetime.utcnow()
    user.login_count += 1
    db.session.commit()

    return jsonify({
        "id": user.id, 
        "username": user.username,
        "is_admin": user.is_admin,
        "message": "管理员登录成功" if user.is_admin else "登录成功"
    })


@bp.post("/api/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@bp.get("/api/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True, 
        "id": current_user.id, 
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
        "login_count": current_user.login_count,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    })


@bp.get("/api/my/ratings")
@login_required
def my_ratings():
    limit = min(int(request.args.get("limit") or 50), 200)
    rows = (
        db.session.query(Rating, Movie)
        .join(Movie, Movie.id == Rating.movie_id)
        .filter(Rating.user_id == current_user.id)
        .order_by(db.case((Rating.timestamp.is_(None), 1), else_=0), Rating.timestamp.desc(), Rating.id.desc())
        .limit(limit)
        .all()
    )
    return jsonify(
        [
            {
                "movie_id": m.id,
                "title": m.title,
                "year": m.year,
                "genres": (m.genres or ""),
                "rating": float(r.rating),
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r, m in rows
        ]
    )


@bp.get("/api/movies")
@cache.cached(timeout=60, query_string=True)  # 缓存1分钟，考虑查询参数
def list_movies():
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit") or 20)
        limit = max(1, min(limit, 100))  # 限制在1-100之间
    except ValueError:
        return jsonify({"error": "limit参数必须是整数", "code": "INVALID_PARAM"}), 400

    query = Movie.query
    if q:
        query = query.filter(Movie.title.ilike(f"%{q}%"))

    movies = query.order_by(Movie.id.asc()).limit(limit).all()
    return jsonify(
        [
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "genres": (m.genres or ""),
            }
            for m in movies
        ]
    )


@bp.get("/api/movies/popular")
@cache.cached(timeout=300, query_string=True)  # 缓存5分钟，考虑查询参数
def popular_movies():
    limit = min(int(request.args.get("limit") or 20), 100)
    min_count = int(request.args.get("min_count") or 0)
    rows = (
        db.session.query(
            Movie,
            db.func.coalesce(db.func.avg(Rating.rating), 0).label("avg_rating"),
            db.func.count(Rating.id).label("rating_count"),
        )
        .outerjoin(Rating, Rating.movie_id == Movie.id)
        .group_by(Movie.id)
    )
    if min_count > 0:
        rows = rows.having(db.func.count(Rating.id) >= min_count)
    rows = rows.order_by(db.desc("avg_rating"), db.desc("rating_count")).limit(limit).all()
    return jsonify(
        [
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "genres": (m.genres or ""),
                "avg_rating": float(avg),
                "rating_count": int(cnt),
                "poster": m.poster_url,
                "backdrop": m.backdrop_url,
                "overview": m.description,
            }
            for (m, avg, cnt) in rows
        ]
    )


@bp.get("/api/movies/<int:movie_id>")
@cache.cached(timeout=300)  # 缓存5分钟，电影详情变化较少
def movie_detail(movie_id: int):
    if movie_id <= 0:
        return jsonify({"error": "电影ID必须为正整数", "code": "INVALID_PARAM"}), 400
    m = db.session.get(Movie, int(movie_id))
    if m is None:
        return jsonify({"error": "movie not found"}), 404
    avg = (
        db.session.query(db.func.avg(Rating.rating))
        .filter(Rating.movie_id == m.id)
        .scalar()
    )
    cnt = (
        db.session.query(db.func.count(Rating.id))
        .filter(Rating.movie_id == m.id)
        .scalar()
    )
    return jsonify(
        {
            "id": m.id,
            "title": m.title,
            "year": m.year,
            "genres": (m.genres or ""),
            "avg_rating": float(avg) if avg is not None else None,
            "rating_count": int(cnt or 0),
            "poster": m.poster_url,
            "backdrop": m.backdrop_url,
            "overview": m.description,
            "director": m.director,
            "actors": m.get_actors_list(),
            "runtime": m.runtime,
            "tagline": m.tagline,
            "tmdb_id": m.tmdb_id,
        }
    )


@bp.get("/api/movies/<int:movie_id>/similar")
@cache.cached(timeout=180, query_string=True)  # 缓存3分钟
def similar_movies(movie_id: int):
    if movie_id <= 0:
        return jsonify({"error": "电影ID必须为正整数", "code": "INVALID_PARAM"}), 400
    try:
        top_n = int(request.args.get("n") or 10)
        top_n = max(1, min(top_n, 50))  # 限制在1-50之间
    except ValueError:
        return jsonify({"error": "n参数必须是整数", "code": "INVALID_PARAM"}), 400
    movie = db.session.get(Movie, int(movie_id))
    if movie is None:
        return jsonify({"error": "movie not found"}), 404

    sims = (
        MovieSimilarity.query.filter_by(movie_id=movie.id)
        .order_by(MovieSimilarity.score.desc())
        .limit(top_n)
        .all()
    )
    similar_ids = [s.similar_movie_id for s in sims]
    movies = Movie.query.filter(Movie.id.in_(similar_ids)).all()
    movie_map = {m.id: m for m in movies}

    result = []
    for s in sims:
        m = movie_map.get(s.similar_movie_id)
        if m is None:
            continue
        result.append(
            {
                "movie_id": m.id,
                "title": m.title,
                "year": m.year,
                "genres": (m.genres or ""),
                "score": float(s.score),
            }
        )
    return jsonify({"movie_id": movie.id, "title": movie.title, "similar": result})


@bp.post("/api/ratings")
@login_required
def rate_movie():
    data = request.get_json(force=True)
    movie_id = data.get("movie_id")
    rating_value = data.get("rating")

    if movie_id is None or rating_value is None:
        return jsonify({"error": "movie_id and rating required"}), 400

    movie = db.session.get(Movie, int(movie_id))
    if movie is None:
        return jsonify({"error": "movie not found"}), 404

    rating_value = float(rating_value)
    if not (0.5 <= rating_value <= 5.0):
        return jsonify({"error": "rating must be in [0.5, 5.0]"}), 400

    existing = Rating.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
    if existing is None:
        existing = Rating(user_id=current_user.id, movie_id=movie.id, rating=rating_value, timestamp=datetime.utcnow())
        db.session.add(existing)
    else:
        existing.rating = rating_value
        existing.timestamp = datetime.utcnow()

    db.session.commit()
    return jsonify({"ok": True})


def _itemcf_recall(user_id: int, user_ratings: list[Rating], top_n: int, rated_movie_ids: set[int]) -> tuple[list[tuple[int, float]], dict[int, dict[int, float]]]:
    """ItemCF recall: return (list of (movie_id, score), contributions dict).
    
    优化：使用批量查询替代N+1循环查询，显著提升性能。
    """
    scores: dict[int, float] = {}
    contributions: dict[int, dict[int, float]] = {}
    
    if not user_ratings:
        return [], {}
    
    # 批量获取所有需要的相似度（单次查询替代N次查询）
    movie_ids = [r.movie_id for r in user_ratings]
    all_sims = (
        MovieSimilarity.query
        .filter(MovieSimilarity.movie_id.in_(movie_ids))
        .order_by(MovieSimilarity.movie_id.asc(), MovieSimilarity.score.desc())
        .all()
    )
    
    # 按movie_id分组，每个只取Top50
    from collections import defaultdict
    sims_by_movie: dict[int, list[MovieSimilarity]] = defaultdict(list)
    for s in all_sims:
        if len(sims_by_movie[s.movie_id]) < 50:
            sims_by_movie[s.movie_id].append(s)
    
    # 计算推荐分数
    for r in user_ratings:
        sims = sims_by_movie.get(r.movie_id, [])
        for s in sims:
            if s.similar_movie_id in rated_movie_ids:
                continue
            inc = float(s.score) * float(r.rating)
            scores[s.similar_movie_id] = scores.get(s.similar_movie_id, 0.0) + inc
            per_item = contributions.setdefault(s.similar_movie_id, {})
            per_item[r.movie_id] = per_item.get(r.movie_id, 0.0) + inc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return ranked, contributions


def _ncf_rank(user_id: int, candidate_ids: list[int], top_k: int) -> list[tuple[int, float]]:
    """NCF rerank candidates and return top-k."""
    if not ncf_engine.is_ready():
        ncf_engine.load()
    if not ncf_engine.is_ready():
        return []
    return ncf_engine.rank(user_id, candidate_ids, top_k=top_k)


def _format_recommendations(
    ranked: list[tuple[int, float]],
    contributions: dict[int, dict[int, float]],
    user_ratings: list[Rating],
    reason: str,
    reranked: bool = False,
) -> list[dict]:
    """Format recommendations with explanations. Returns normalized fields."""
    target_ids = [mid for mid, _ in ranked]
    seed_ids = [r.movie_id for r in user_ratings]
    movies = Movie.query.filter(Movie.id.in_(target_ids + seed_ids)).all()
    movie_map = {m.id: m for m in movies}

    result = []
    for mid, score in ranked:
        m = movie_map.get(mid)
        if m is None:
            continue

        seeds = contributions.get(mid, {})
        top_seeds = sorted(seeds.items(), key=lambda x: x[1], reverse=True)[:3]
        because = []
        for seed_id, weight in top_seeds:
            sm = movie_map.get(seed_id)
            because.append(
                {
                    "movie_id": int(seed_id),
                    "title": sm.title if sm is not None else str(seed_id),
                    "weight": float(weight),
                }
            )

        rec_reason = reason
        if reranked:
            rec_reason = "hybrid"

        result.append(
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "genres": m.genres,
                "avg_rating": float(score),
                "poster": m.poster_url,
                "backdrop": m.backdrop_url,
                "overview": m.description,
                "reason": rec_reason,
                "because": because if because else None,
            }
        )
    return result


def _get_popular_fallback(top_n: int) -> list[dict]:
    """Return popular movies as fallback for cold users. Returns normalized fields."""
    movies = (
        db.session.query(Movie, db.func.coalesce(db.func.avg(Rating.rating), 0).label("avg_rating"), db.func.count(Rating.id).label("cnt"))
        .outerjoin(Rating, Rating.movie_id == Movie.id)
        .group_by(Movie.id)
        .order_by(db.desc("avg_rating"), db.desc("cnt"))
        .limit(top_n)
        .all()
    )
    return [
        {
            "id": m.id,
            "title": m.title,
            "year": m.year,
            "genres": m.genres,
            "avg_rating": float(avg),
            "rating_count": int(cnt),
            "poster": m.poster_url,
            "backdrop": m.backdrop_url,
            "overview": m.description,
            "reason": "popular",
            "because": None,
        }
        for (m, avg, cnt) in movies
    ]


@bp.get("/api/recommendations")
def recommend():
    top_n = min(int(request.args.get("n") or 10), 50)
    strategy = request.args.get("strategy", "itemcf")  # itemcf | ncf | hybrid
    recall_k = min(int(request.args.get("recall_k") or 100), 500)  # for hybrid mode

    # Anonymous users: return popular movies as fallback
    if not current_user.is_authenticated:
        return jsonify(_get_popular_fallback(top_n))

    user_ratings = Rating.query.filter_by(user_id=current_user.id).all()

    # Cold user: return popular
    if not user_ratings:
        return jsonify(_get_popular_fallback(top_n))

    rated_movie_ids = {r.movie_id for r in user_ratings}

    # ItemCF strategy (original behavior)
    if strategy == "itemcf":
        ranked, contributions = _itemcf_recall(current_user.id, user_ratings, top_n, rated_movie_ids)
        result = _format_recommendations(ranked, contributions, user_ratings, "similarity")
        return jsonify(result)

    # NCF-only strategy (require trained model)
    if strategy == "ncf":
        # 检查模型加载状态
        if ncf_engine.is_loading():
            return jsonify({
                "error": "NCF模型正在加载中，请稍后再试",
                "code": "MODEL_LOADING",
                "retry_after": 5
            }), 503
        
        if not ncf_engine.is_ready():
            # 尝试加载
            ncf_engine.load()
        
        if not ncf_engine.is_ready():
            return jsonify({
                "error": "NCF模型不可用，请先运行训练脚本: python -m backend.scripts.train_ncf",
                "code": "MODEL_NOT_AVAILABLE"
            }), 503

        # Check if user is in NCF training set
        if current_user.id not in ncf_engine.user2idx:
            # Cold user for NCF: fallback to ItemCF
            ranked, contributions = _itemcf_recall(current_user.id, user_ratings, top_n, rated_movie_ids)
            result = _format_recommendations(ranked, contributions, user_ratings, "similarity")
            return jsonify(result)

        # Use popular unrated movies as NCF candidates (deterministic + reasonable quality)
        popular_unrated = (
            db.session.query(Rating.movie_id, db.func.count(Rating.id).label("cnt"))
            .filter(~Rating.movie_id.in_(rated_movie_ids))
            .group_by(Rating.movie_id)
            .order_by(db.desc("cnt"))
            .limit(500)
            .all()
        )
        candidate_ids = [int(mid) for mid, _ in popular_unrated]

        ncf_ranked = _ncf_rank(current_user.id, candidate_ids, top_k=top_n)
        # Build empty contributions for NCF-only (no ItemCF explanation)
        contributions: dict[int, dict[int, float]] = {mid: {} for mid, _ in ncf_ranked}
        result = _format_recommendations(ncf_ranked, contributions, user_ratings, "ncf")
        return jsonify(result)

    # Hybrid strategy: ItemCF recall + NCF rerank
    if strategy == "hybrid":
        # 检查模型加载状态
        if ncf_engine.is_loading():
            return jsonify({
                "error": "NCF模型正在加载中，请稍后再试",
                "code": "MODEL_LOADING",
                "retry_after": 5
            }), 503
        
        if not ncf_engine.is_ready():
            ncf_engine.load()

        # Step 1: ItemCF recall
        itemcf_ranked, contributions = _itemcf_recall(current_user.id, user_ratings, recall_k, rated_movie_ids)

        if not itemcf_ranked:
            return jsonify([])

        # Step 2: NCF rerank if model available and user in training set
        if ncf_engine.is_ready() and current_user.id in ncf_engine.user2idx:
            candidate_ids = [mid for mid, _ in itemcf_ranked]
            ncf_ranked = _ncf_rank(current_user.id, candidate_ids, top_k=top_n)
            if ncf_ranked:
                # Merge contributions: keep ItemCF contributions for final items
                ncf_contributions = {mid: contributions.get(mid, {}) for mid, _ in ncf_ranked}
                result = _format_recommendations(ncf_ranked, ncf_contributions, user_ratings, "hybrid", reranked=True)
            else:
                # NCF returned empty (shouldn't happen with user check, but safe fallback)
                result = _format_recommendations(itemcf_ranked[:top_n], contributions, user_ratings, "similarity")
        else:
            # Fallback to ItemCF if NCF not loaded or user not in training set
            result = _format_recommendations(itemcf_ranked[:top_n], contributions, user_ratings, "similarity")

        return jsonify(result)

    # Unknown strategy
    return jsonify({"error": f"Unknown strategy: {strategy}. Use 'itemcf', 'ncf', or 'hybrid'."}), 400


@bp.get("/api/recommendations/why/<int:movie_id>")
@login_required
def explain_recommendation(movie_id: int):
    top_n = min(int(request.args.get("n") or 3), 10)
    movie = db.session.get(Movie, int(movie_id))
    if movie is None:
        return jsonify({"error": "movie not found"}), 404

    user_ratings = Rating.query.filter_by(user_id=current_user.id).all()
    if not user_ratings:
        return jsonify({"movie_id": movie.id, "title": movie.title, "because": []})

    seed_ids = [r.movie_id for r in user_ratings]
    sims = (
        MovieSimilarity.query.filter(MovieSimilarity.movie_id.in_(seed_ids))
        .filter(MovieSimilarity.similar_movie_id == movie.id)
        .all()
    )
    sim_map = {s.movie_id: float(s.score) for s in sims}

    contributions = []
    for r in user_ratings:
        sim = sim_map.get(r.movie_id)
        if sim is None:
            continue
        contributions.append((r.movie_id, float(sim) * float(r.rating)))

    contributions.sort(key=lambda x: x[1], reverse=True)
    top = contributions[:top_n]
    movies = Movie.query.filter(Movie.id.in_([mid for mid, _w in top])).all()
    movie_map = {m.id: m for m in movies}

    because = []
    for mid, w in top:
        m = movie_map.get(mid)
        because.append({"movie_id": int(mid), "title": m.title if m else str(mid), "weight": float(w)})

    return jsonify({"movie_id": movie.id, "title": movie.title, "because": because})


@bp.get("/api/stats/ratings")
@cache.cached(timeout=60)  # 缓存1分钟
def stats_ratings():
    rows = db.session.query(Rating.rating, db.func.count(Rating.id)).group_by(Rating.rating).order_by(Rating.rating.asc()).all()
    return jsonify(
        {
            "labels": [str(float(r)) for r, _c in rows],
            "values": [int(c) for _r, c in rows],
        }
    )


@bp.get("/api/stats/genres")
@cache.cached(timeout=60)  # 缓存1分钟
def stats_genres():
    rows = db.session.query(Movie.genres, db.func.count(Rating.id)).join(Rating, Rating.movie_id == Movie.id).group_by(Movie.genres).all()
    counts: dict[str, int] = {}
    for genres, cnt in rows:
        if not genres:
            continue
        for g in str(genres).split("|"):
            g = g.strip()
            if not g or g == "(no genres listed)":
                continue
            counts[g] = counts.get(g, 0) + int(cnt)

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return jsonify({"labels": [k for k, _v in items], "values": [v for _k, v in items]})


@bp.get("/api/stats/years")
@cache.cached(timeout=60)  # 缓存1分钟
def stats_years():
    rows = (
        db.session.query(Movie.year, db.func.count(Rating.id).label("cnt"), db.func.avg(Rating.rating).label("avg"))
        .join(Rating, Rating.movie_id == Movie.id)
        .filter(Movie.year.isnot(None))
        .group_by(Movie.year)
        .order_by(Movie.year.asc())
        .all()
    )
    return jsonify(
        {
            "years": [int(y) for y, _c, _a in rows],
            "counts": [int(c) for _y, c, _a in rows],
            "avg_ratings": [float(a) for _y, _c, a in rows],
        }
    )


@bp.get("/api/stats/popular")
@cache.cached(timeout=60, query_string=True)  # 缓存1分钟，考虑limit参数
def stats_popular():
    limit = min(int(request.args.get("limit") or 10), 50)
    rows = (
        db.session.query(
            Movie.title,
            db.func.count(Rating.id).label("rating_count"),
            db.func.avg(Rating.rating).label("avg_rating"),
        )
        .join(Rating, Rating.movie_id == Movie.id)
        .group_by(Movie.id)
        .order_by(db.desc("rating_count"), db.desc("avg_rating"))
        .limit(limit)
        .all()
    )
    return jsonify(
        {
            "labels": [t for t, _c, _a in rows],
            "counts": [int(c) for _t, c, _a in rows],
            "avg_ratings": [float(a) for _t, _c, a in rows],
        }
    )


@bp.get("/api/stats/user_activity")
@cache.cached(timeout=60, query_string=True)  # 缓存1分钟
def stats_user_activity():
    limit = min(int(request.args.get("limit") or 10), 50)
    rows = (
        db.session.query(User.username, db.func.count(Rating.id).label("cnt"))
        .join(Rating, Rating.user_id == User.id)
        .group_by(User.id)
        .order_by(db.desc("cnt"))
        .limit(limit)
        .all()
    )
    return jsonify({"labels": [u for u, _c in rows], "values": [int(c) for _u, c in rows]})


@bp.get("/api/stats/movie_rating_counts")
@cache.cached(timeout=300)  # 缓存5分钟，该统计变化较慢
def stats_movie_rating_counts():
    bins = [1, 2, 5, 10, 20, 50, 100, 200]
    rows = (
        db.session.query(Rating.movie_id, db.func.count(Rating.id).label("cnt"))
        .group_by(Rating.movie_id)
        .all()
    )
    counts = [0 for _ in range(len(bins) + 1)]
    for _mid, cnt in rows:
        c = int(cnt)
        placed = False
        for i, b in enumerate(bins):
            if c <= b:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1

    labels = [f"1-{bins[0]}"]
    for i in range(1, len(bins)):
        labels.append(f"{bins[i-1]+1}-{bins[i]}")
    labels.append(f">{bins[-1]}")
    return jsonify({"labels": labels, "values": counts})


# ==================== 管理员API ====================

from backend.app.decorators import admin_required

@bp.get("/api/admin/users")
@login_required
@admin_required
def admin_list_users():
    """管理员：获取用户列表"""
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = []
    for user in pagination.items:
        users.append(user.to_dict())
    
    return jsonify({
        "users": users,
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page
    })


@bp.post("/api/admin/users/<int:user_id>/toggle-admin")
@login_required
@admin_required
def admin_toggle_user_admin(user_id):
    """管理员：切换用户管理员权限"""
    user = User.query.get_or_404(user_id)
    
    # 不能修改自己的权限
    if user.id == current_user.id:
        return jsonify({"error": "不能修改自己的管理员权限"}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        "success": True,
        "user_id": user_id,
        "is_admin": user.is_admin,
        "message": f"用户 {user.username} 已{'设为' if user.is_admin else '撤销'}管理员"
    })


@bp.post("/api/admin/users/<int:user_id>/toggle-active")
@login_required
@admin_required
def admin_toggle_user_active(user_id):
    """管理员：启用/禁用用户账户"""
    user = User.query.get_or_404(user_id)
    
    # 不能禁用自己
    if user.id == current_user.id:
        return jsonify({"error": "不能禁用自己"}), 400
    
    # 不能禁用其他管理员
    if user.is_admin and user.id != current_user.id:
        return jsonify({"error": "不能禁用其他管理员"}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        "success": True,
        "user_id": user_id,
        "is_active": user.is_active,
        "message": f"用户 {user.username} 已{'启用' if user.is_active else '禁用'}"
    })


@bp.get("/api/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """管理员：获取仪表板统计数据"""
    stats = {
        "total_users": User.query.count(),
        "total_movies": Movie.query.count(),
        "total_ratings": Rating.query.count(),
        "admin_count": User.query.filter_by(is_admin=True).count(),
        "active_users": User.query.filter_by(is_active=True).count(),
        "inactive_users": User.query.filter_by(is_active=False).count(),
        "movies_with_poster": Movie.query.filter(Movie.poster_url.isnot(None)).count(),
        "movies_with_director": Movie.query.filter(Movie.director.isnot(None)).count(),
    }
    
    # 最近注册的用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    stats["recent_users"] = [user.to_dict() for user in recent_users]
    
    return jsonify(stats)


@bp.get("/api/metrics/offline")
def offline_metrics():
    path = Path(__file__).resolve().parents[1] / "artifacts" / "offline_metrics.json"
    if not path.exists():
        return jsonify({"error": "offline metrics not found, run backend/scripts/evaluate_itemcf.py first"}), 404
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return jsonify({"error": "failed to read offline metrics"}), 500
    return jsonify(data)


# ==================== 评论系统API ====================

@bp.post("/api/reviews")
@login_required
def create_review():
    """发表评论"""
    data = request.get_json()
    movie_id = data.get('movie_id')
    content = data.get('content', '').strip()
    rating = data.get('rating')
    
    if not movie_id or not content:
        return jsonify({'error': '电影ID和评论内容不能为空'}), 400
    
    if len(content) < 5:
        return jsonify({'error': '评论内容至少5个字符'}), 400
    
    if rating and (rating < 0.5 or rating > 5):
        return jsonify({'error': '评分必须在0.5-5之间'}), 400
    
    # 检查电影是否存在
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': '电影不存在'}), 404
    
    # 检查用户是否已经评论过该电影
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()
    
    if existing_review:
        return jsonify({'error': '您已经评论过这部电影了'}), 400
    
    # 创建评论
    review = Review(
        user_id=current_user.id,
        movie_id=movie_id,
        content=content,
        rating=rating
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '评论发表成功',
        'review': review.to_dict()
    })


@bp.get("/api/movies/<int:movie_id>/reviews")
def get_movie_reviews(movie_id):
    """获取电影评论列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    sort_by = request.args.get('sort_by', 'newest')  # newest, rating, likes
    
    # 检查电影是否存在
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': '电影不存在'}), 404
    
    # 构建查询
    query = Review.query.filter_by(movie_id=movie_id, status='approved')
    
    # 排序
    if sort_by == 'newest':
        query = query.order_by(Review.created_at.desc())
    elif sort_by == 'rating':
        query = query.order_by(Review.rating.desc().nullslast())
    elif sort_by == 'likes':
        query = query.order_by(Review.likes_count.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    reviews = [review.to_dict() for review in pagination.items]
    
    # 如果当前用户已登录，标记用户是否已点赞
    if current_user.is_authenticated:
        for review in reviews:
            liked = ReviewLike.query.filter_by(
                user_id=current_user.id,
                review_id=review['id']
            ).first() is not None
            review['user_liked'] = liked
    
    return jsonify({
        'reviews': reviews,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total
        }
    })


@bp.post("/api/reviews/<int:review_id>/like")
@login_required
def like_review(review_id):
    """点赞/取消点赞评论"""
    review = Review.query.get_or_404(review_id)
    
    # 检查是否已经点赞
    existing_like = ReviewLike.query.filter_by(
        user_id=current_user.id,
        review_id=review_id
    ).first()
    
    if existing_like:
        # 取消点赞
        db.session.delete(existing_like)
        review.likes_count -= 1
        liked = False
    else:
        # 点赞
        like = ReviewLike(user_id=current_user.id, review_id=review_id)
        db.session.add(like)
        review.likes_count += 1
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': review.likes_count
    })


@bp.delete("/api/reviews/<int:review_id>")
@login_required
def delete_review(review_id):
    """删除评论（仅评论作者或管理员可删除）"""
    review = Review.query.get_or_404(review_id)
    
    # 检查权限
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '没有权限删除此评论'}), 403
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '评论已删除'
    })


@bp.get("/api/my/reviews")
@login_required
def get_my_reviews():
    """获取当前用户的评论列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    pagination = Review.query.filter_by(user_id=current_user.id)\
        .order_by(Review.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    reviews = []
    for review in pagination.items:
        review_data = review.to_dict()
        review_data['movie'] = {
            'id': review.movie.id,
            'title': review.movie.title,
            'poster_url': review.movie.poster_url
        }
        reviews.append(review_data)
    
    return jsonify({
        'reviews': reviews,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total
        }
    })


@bp.get("/api/metrics/evaluation")
def multi_model_evaluation():
    """Return multi-model offline evaluation results (ItemCF, NCF, Hybrid with ablation)."""
    path = Path(__file__).resolve().parents[1] / "artifacts" / "evaluation_results.json"
    if not path.exists():
        return jsonify({"error": "evaluation results not found, run backend/scripts/evaluate_models.py first"}), 404
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return jsonify({"error": "failed to read evaluation results"}), 500
    return jsonify(data)


# ==================== 用户收藏系统API ====================

@bp.post("/api/collections")
@login_required
def add_collection():
    """添加收藏"""
    data = request.get_json()
    movie_id = data.get('movie_id')
    collection_type = data.get('collection_type', 'favorite')
    notes = data.get('notes', '').strip()
    rating = data.get('rating')
    
    if not movie_id:
        return jsonify({'error': '电影ID不能为空'}), 400
    
    if collection_type not in ['favorite', 'watchlist', 'seen']:
        return jsonify({'error': '收藏类型无效'}), 400
    
    # 检查电影是否存在
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': '电影不存在'}), 404
    
    # 检查是否已收藏
    existing = UserCollection.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id,
        collection_type=collection_type
    ).first()
    
    if existing:
        return jsonify({'error': '该电影已在收藏列表中'}), 400
    
    # 验证个人评分
    if rating and (rating < 0.5 or rating > 5):
        return jsonify({'error': '评分必须在0.5-5之间'}), 400
    
    # 创建收藏
    collection = UserCollection(
        user_id=current_user.id,
        movie_id=movie_id,
        collection_type=collection_type,
        notes=notes,
        rating=rating
    )
    
    db.session.add(collection)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '收藏成功',
        'collection': collection.to_dict()
    })


@bp.get("/api/my/collections")
@login_required
def get_my_collections():
    """获取我的收藏列表"""
    collection_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = UserCollection.query.filter_by(user_id=current_user.id)
    
    if collection_type:
        query = query.filter_by(collection_type=collection_type)
    
    pagination = query.order_by(UserCollection.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    collections = [c.to_dict() for c in pagination.items]
    
    # 统计各类型数量
    stats = {
        'favorite': UserCollection.query.filter_by(user_id=current_user.id, collection_type='favorite').count(),
        'watchlist': UserCollection.query.filter_by(user_id=current_user.id, collection_type='watchlist').count(),
        'seen': UserCollection.query.filter_by(user_id=current_user.id, collection_type='seen').count(),
        'total': UserCollection.query.filter_by(user_id=current_user.id).count()
    }
    
    return jsonify({
        'collections': collections,
        'stats': stats,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total
        }
    })


@bp.delete("/api/collections/<int:collection_id>")
@login_required
def remove_collection(collection_id):
    """取消收藏"""
    collection = UserCollection.query.get_or_404(collection_id)
    
    # 检查权限
    if collection.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '没有权限删除此收藏'}), 403
    
    db.session.delete(collection)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '已取消收藏'
    })


@bp.get("/api/movies/<int:movie_id>/collection-status")
@login_required
def get_collection_status(movie_id):
    """获取当前用户对某部电影的收藏状态"""
    collections = UserCollection.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).all()
    
    result = {
        'is_favorite': False,
        'in_watchlist': False,
        'is_seen': False,
        'collection_ids': {}
    }
    
    for c in collections:
        if c.collection_type == 'favorite':
            result['is_favorite'] = True
            result['collection_ids']['favorite'] = c.id
        elif c.collection_type == 'watchlist':
            result['in_watchlist'] = True
            result['collection_ids']['watchlist'] = c.id
        elif c.collection_type == 'seen':
            result['is_seen'] = True
            result['collection_ids']['seen'] = c.id
    
    return jsonify(result)


@bp.post("/api/collections/<int:collection_id>/notes")
@login_required
def update_collection_notes(collection_id):
    """更新收藏备注"""
    collection = UserCollection.query.get_or_404(collection_id)
    
    if collection.user_id != current_user.id:
        return jsonify({'error': '没有权限'}), 403
    
    data = request.get_json()
    notes = data.get('notes', '').strip()
    
    collection.notes = notes
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '备注已更新'
    })


# ==================== 电影观看链接系统API ====================

@bp.get("/api/movies/<int:movie_id>/watch-links")
def get_movie_watch_links(movie_id):
    """获取电影观看链接"""
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': '电影不存在'}), 404
    
    # 只返回已通过审核的链接
    links = WatchLink.query.filter_by(
        movie_id=movie_id,
        status='active'
    ).order_by(
        WatchLink.is_official.desc(),
        WatchLink.report_count.asc(),
        WatchLink.created_at.desc()
    ).all()
    
    return jsonify({
        'links': [link.to_dict() for link in links],
        'movie': {
            'id': movie.id,
            'title': movie.title,
            'year': movie.year
        }
    })


@bp.post("/api/movies/<int:movie_id>/watch-links")
@login_required
def add_watch_link(movie_id):
    """提交观看链接"""
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({'error': '电影不存在'}), 404
    
    data = request.get_json()
    platform = data.get('platform', '').strip()
    url = data.get('url', '').strip()
    quality = data.get('quality', 'HD')
    is_free = data.get('is_free', True)
    
    if not platform or not url:
        return jsonify({'error': '平台和链接不能为空'}), 400
    
    # 简单验证URL格式
    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': '链接格式不正确'}), 400
    
    # 检查是否已存在相同链接
    existing = WatchLink.query.filter_by(movie_id=movie_id, url=url).first()
    if existing:
        return jsonify({'error': '该链接已存在'}), 400
    
    link = WatchLink(
        movie_id=movie_id,
        user_id=current_user.id,
        platform=platform,
        url=url,
        quality=quality,
        is_free=is_free,
        status='pending'  # 新链接需要审核
    )
    
    db.session.add(link)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '链接提交成功，等待审核',
        'link': link.to_dict()
    })


@bp.post("/api/watch-links/<int:link_id>/report")
@login_required
def report_watch_link(link_id):
    """举报观看链接"""
    link = WatchLink.query.get_or_404(link_id)
    
    data = request.get_json()
    reason = data.get('reason', '').strip()
    
    if not reason:
        return jsonify({'error': '请提供举报原因'}), 400
    
    # 增加举报计数
    link.report_count += 1
    
    # 如果举报次数超过阈值，自动标记为reported
    if link.report_count >= 3:
        link.status = 'reported'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '举报成功，我们将尽快处理',
        'report_count': link.report_count
    })


# ==================== 消息通知系统API ====================

@bp.get("/api/notifications")
@login_required
def get_notifications():
    """获取用户通知列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 统计未读数量
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'unread_count': unread_count,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total
        }
    })


@bp.post("/api/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read(notification_id):
    """标记通知为已读"""
    notification = Notification.query.get_or_404(notification_id)
    
    # 检查权限
    if notification.user_id != current_user.id:
        return jsonify({'error': '没有权限'}), 403
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '已标记为已读'
    })


@bp.post("/api/notifications/read-all")
@login_required
def mark_all_notifications_read():
    """标记所有通知为已读"""
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '所有通知已标记为已读'
    })


@bp.get("/api/notifications/unread-count")
@login_required
def get_unread_notification_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({'unread_count': count})


# ==================== 电影榜单系统API ====================

@bp.get("/api/charts")
def get_charts():
    """获取榜单列表"""
    chart_type = request.args.get('type', '')
    
    query = MovieChart.query.filter_by(is_active=True)
    
    if chart_type:
        query = query.filter_by(chart_type=chart_type)
    
    charts = query.order_by(MovieChart.sort_order).all()
    
    return jsonify({
        'charts': [c.to_dict() for c in charts]
    })


@bp.get("/api/charts/<int:chart_id>")
def get_chart_detail(chart_id):
    """获取榜单详情"""
    chart = MovieChart.query.get_or_404(chart_id)
    
    if not chart.is_active:
        return jsonify({'error': '榜单不存在'}), 404
    
    return jsonify({
        'chart': chart.to_dict(),
        'items': [item.to_dict() for item in chart.items[:50]]  # 最多返回50条
    })


@bp.get("/api/charts/popular")
def get_popular_charts():
    """获取热门榜单（首页展示用）"""
    # 获取不同类型的榜单
    hot_chart = MovieChart.query.filter_by(chart_type='hot', is_active=True).first()
    top_rated_chart = MovieChart.query.filter_by(chart_type='top_rated', is_active=True).first()
    editor_chart = MovieChart.query.filter_by(chart_type='editor_pick', is_active=True).first()
    
    result = {}
    
    if hot_chart:
        result['hot'] = {
            'chart': hot_chart.to_dict(),
            'items': [item.to_dict() for item in hot_chart.items[:10]]
        }
    
    if top_rated_chart:
        result['top_rated'] = {
            'chart': top_rated_chart.to_dict(),
            'items': [item.to_dict() for item in top_rated_chart.items[:10]]
        }
    
    if editor_chart:
        result['editor_pick'] = {
            'chart': editor_chart.to_dict(),
            'items': [item.to_dict() for item in editor_chart.items[:10]]
        }
    
    return jsonify(result)


# ==================== 数据导出API ====================

@bp.get("/api/export/user-data")
@login_required
def export_user_data():
    """用户数据导出"""
    try:
        format_type = request.args.get('format', 'json')
        
        # 获取用户数据
        user_ratings = Rating.query.filter_by(user_id=current_user.id).all()
        user_collections = UserCollection.query.filter_by(user_id=current_user.id).all()
        user_reviews = Review.query.filter_by(user_id=current_user.id).all()
        
        # 构建导出数据
        export_data = {
            'user_info': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                'is_active': current_user.is_active
            },
            'statistics': {
                'total_ratings': len(user_ratings),
                'total_collections': len(user_collections),
                'total_reviews': len(user_reviews),
                'avg_rating': sum(r.rating for r in user_ratings) / len(user_ratings) if user_ratings else 0,
                'favorite_genres': get_user_favorite_genres(current_user.id)
            },
            'ratings': [rating.to_dict() for rating in user_ratings],
            'collections': [collection.to_dict() for collection in user_collections],
            'reviews': [review.to_dict() for review in user_reviews],
            'export_time': datetime.utcnow().isoformat(),
            'export_version': '1.0'
        }
        
        if format_type == 'csv':
            # CSV格式导出
            return export_to_csv(export_data, f'user_data_{current_user.username}.csv')
        else:
            # JSON格式导出
            from flask import current_app
            response = current_app.response_class(
                json.dumps(export_data, ensure_ascii=False, indent=2),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=user_data_{current_user.username}.json'
                }
            )
            return response
            
    except Exception as e:
        return jsonify({"error": "数据导出失败", "details": str(e)}), 500


@bp.get("/api/export/system-stats")
@login_required
@admin_required
def export_system_stats():
    """系统统计导出 - 管理员功能"""
    try:
        format_type = request.args.get('format', 'json')
        
        # 获取系统统计数据
        stats = {
            'user_statistics': get_user_statistics(),
            'movie_statistics': get_movie_statistics(),
            'rating_statistics': get_rating_statistics(),
            'review_statistics': get_review_statistics(),
            'system_health': get_system_health_export(),
            'behavior_analytics': get_behavior_analytics_export(),
            'export_time': datetime.utcnow().isoformat(),
            'export_version': '1.0'
        }
        
        if format_type == 'csv':
            # CSV格式导出（分多个工作表）
            return export_system_stats_to_csv(stats)
        else:
            # JSON格式导出
            return jsonify(stats)
            
    except Exception as e:
        return jsonify({"error": "系统统计导出失败", "details": str(e)}), 500


@bp.get("/api/export/movie-data")
@login_required
@admin_required
def export_movie_data():
    """电影数据导出 - 管理员功能"""
    from sqlalchemy import func
    try:
        format_type = request.args.get('format', 'json')
        include_ratings = request.args.get('include_ratings', 'false').lower() == 'true'
        
        # 获取电影数据
        movies = Movie.query.all()
        
        export_data = {
            'movies': [],
            'export_time': datetime.utcnow().isoformat(),
            'export_version': '1.0',
            'total_movies': len(movies)
        }
        
        for movie in movies:
            movie_data = movie.to_dict()
            
            if include_ratings:
                # 获取电影评分统计
                rating_stats = db.session.query(
                    func.count(Rating.id).label('rating_count'),
                    func.avg(Rating.rating).label('avg_rating'),
                    func.min(Rating.rating).label('min_rating'),
                    func.max(Rating.rating).label('max_rating')
                ).filter(Rating.movie_id == movie.id).first()
                
                movie_data.update({
                    'rating_count': rating_stats.rating_count or 0,
                    'avg_rating': float(rating_stats.avg_rating) if rating_stats.avg_rating else 0,
                    'min_rating': rating_stats.min_rating,
                    'max_rating': rating_stats.max_rating
                })
                
                # 获取电影评论数
                review_count = Review.query.filter_by(movie_id=movie.id).count()
                movie_data['review_count'] = review_count
            
            export_data['movies'].append(movie_data)
        
        if format_type == 'csv':
            return export_movies_to_csv(export_data)
        else:
            return jsonify(export_data)
            
    except Exception as e:
        return jsonify({"error": "电影数据导出失败", "details": str(e)}), 500


@bp.get("/api/export/backup")
@login_required
@admin_required
def export_system_backup():
    """系统完整备份 - 管理员功能"""
    try:
        # 创建完整备份
        backup_data = {
            'backup_info': {
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'created_by': current_user.username
            },
            'users': [user.to_dict() for user in User.query.all()],
            'movies': [movie.to_dict() for movie in Movie.query.all()],
            'ratings': [rating.to_dict() for rating in Rating.query.all()],
            'reviews': [review.to_dict() for review in Review.query.all()],
            'collections': [collection.to_dict() for collection in UserCollection.query.all()],
            'charts': [chart.to_dict() for chart in MovieChart.query.all()],
            'chart_items': [item.to_dict() for item in ChartItem.query.all()]
        }
        
        # 返回JSON格式的备份
        response = jsonify(backup_data)
        response.headers['Content-Disposition'] = f'attachment; filename=movie_system_backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
        return response
        
    except Exception as e:
        return jsonify({"error": "系统备份失败", "details": str(e)}), 500


# ==================== 增强统计API ====================

@bp.get("/api/enhanced-stats/overview")
@cache.cached(timeout=300)
def enhanced_overview_stats():
    """增强版概览统计"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # 基础统计（复用现有逻辑）
        stats = {
            "total_users": User.query.count(),
            "total_movies": Movie.query.count(),
            "total_ratings": Rating.query.count(),
        }
        
        # 新增统计指标
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        # 本周新增用户
        stats["users_this_week"] = User.query.filter(User.created_at >= one_week_ago).count()
        
        # 今日评分数
        stats["ratings_today"] = Rating.query.filter(Rating.timestamp >= one_day_ago).count()
        
        # 热门类型统计
        genre_stats = db.session.query(
            Movie.genres, func.count(Rating.id).label('count')
        ).join(Rating).group_by(Movie.genres).order_by(func.count(Rating.id).desc()).limit(5).all()
        
        stats["popular_genres"] = [
            {"genre": genre or "未知", "count": count} 
            for genre, count in genre_stats
        ]
        
        # 本月热门电影
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        monthly_movies = db.session.query(
            Movie, func.count(Rating.id).label('rating_count')
        ).join(Rating).filter(
            Rating.timestamp >= one_month_ago
        ).group_by(Movie.id).order_by(func.count(Rating.id).desc()).limit(5).all()
        
        stats["top_movies_this_month"] = [
            {
                "id": movie.id,
                "title": movie.title,
                "year": movie.year,
                "rating_count": rating_count
            }
            for movie, rating_count in monthly_movies
        ]
        
        # 用户活跃度统计
        active_users_today = User.query.join(Rating).filter(
            Rating.timestamp >= one_day_ago
        ).distinct().count()
        
        stats["active_users_today"] = active_users_today
        
        return jsonify(stats)
        
    except Exception as e:
        # 错误处理，确保系统稳定
        return jsonify({"error": "统计服务暂时不可用", "details": str(e)}), 500


@bp.get("/api/enhanced-stats/user-segments")
@cache.cached(timeout=600)
def user_segment_analysis():
    """用户分群分析"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, case
        
        # 活跃度分群
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # 计算用户最后活跃时间
        user_activity = db.session.query(
            User.id,
            func.max(Rating.timestamp).label('last_rating'),
            func.count(Rating.id).label('total_ratings')
        ).outerjoin(Rating).group_by(User.id).all()
        
        # 分群统计
        highly_active = 0  # 7天内有评分
        moderately_active = 0  # 30天内有评分但7天内无
        low_active = 0  # 有评分记录但30天内无
        dormant = 0  # 无评分记录
        
        for user_id, last_rating, total_ratings in user_activity:
            if last_rating:
                if last_rating >= seven_days_ago:
                    highly_active += 1
                elif last_rating >= thirty_days_ago:
                    moderately_active += 1
                else:
                    low_active += 1
            else:
                dormant += 1
        
        activity_segments = {
            "highly_active": highly_active,
            "moderately_active": moderately_active,
            "low_active": low_active,
            "dormant": dormant
        }
        
        # 评分偏好分群
        rating_patterns = db.session.query(
            User.id,
            func.avg(Rating.rating).label('avg_rating')
        ).join(Rating).group_by(User.id).all()
        
        generous_raters = 0  # 平均评分 >= 4.0
        critical_raters = 0  # 平均评分 <= 2.5
        balanced_raters = 0  # 2.5 < 平均评分 < 4.0
        
        for user_id, avg_rating in rating_patterns:
            if avg_rating >= 4.0:
                generous_raters += 1
            elif avg_rating <= 2.5:
                critical_raters += 1
            else:
                balanced_raters += 1
        
        rating_segments = {
            "generous_raters": generous_raters,
            "critical_raters": critical_raters,
            "balanced_raters": balanced_raters
        }
        
        # 计算百分比
        total_users = User.query.count()
        if total_users > 0:
            for segment in activity_segments:
                activity_segments[segment] = round(activity_segments[segment] / total_users * 100, 1)
            for segment in rating_segments:
                rating_segments[segment] = round(rating_segments[segment] / total_users * 100, 1)
        
        return jsonify({
            "activity_segments": activity_segments,
            "rating_segments": rating_segments,
            "total_users": total_users,
            "segment_trends": {
                "note": "趋势分析需要历史数据积累，当前为基准数据"
            }
        })
        
    except Exception as e:
        return jsonify({"error": "用户分群分析失败", "details": str(e)}), 500


@bp.get("/api/enhanced-stats/activity-heatmap")
@cache.cached(timeout=300)
def activity_heatmap_data():
    """用户活跃度热力图数据"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        # 获取过去30天的活跃数据
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 按小时统计活跃度
        hourly_activity = db.session.query(
            extract('hour', Rating.timestamp).label('hour'),
            extract('dow', Rating.timestamp).label('day_of_week'),
            func.count(Rating.id).label('activity_count')
        ).filter(
            Rating.timestamp >= thirty_days_ago
        ).group_by(
            extract('hour', Rating.timestamp),
            extract('dow', Rating.timestamp)
        ).all()
        
        # 构建热力图数据矩阵 (7天 x 24小时)
        heatmap_data = []
        for hour in range(24):
            for day in range(7):  # 0=周日, 6=周六
                count = 0
                for h, d, activity_count in hourly_activity:
                    if int(h) == hour and int(d) == day:
                        count = int(activity_count)
                        break
                
                heatmap_data.append([hour, day, count])
        
        return jsonify({
            "heatmap_data": heatmap_data,
            "time_range": {
                "start": thirty_days_ago.isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"error": "活跃度热力图数据获取失败", "details": str(e)}), 500


@bp.get("/api/enhanced-stats/genre-trends")
@cache.cached(timeout=600)
def genre_trends_analysis():
    """类型趋势分析"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # 获取过去12个月的类型趋势
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        # 按月统计各类型评分数量
        monthly_genre_stats = db.session.query(
            func.date_trunc('month', Rating.timestamp).label('month'),
            Movie.genres,
            func.count(Rating.id).label('count')
        ).join(Movie).filter(
            Rating.timestamp >= twelve_months_ago
        ).group_by(
            func.date_trunc('month', Rating.timestamp),
            Movie.genres
        ).order_by('month').all()
        
        # 处理数据格式
        trend_data = {}
        for month, genres, count in monthly_genre_stats:
            month_str = month.strftime('%Y-%m') if month else None
            if month_str:
                genre_list = genres.split('|') if genres else ['未知']
                for genre in genre_list:
                    genre = genre.strip()
                    if genre and genre != '(no genres listed)':
                        if genre not in trend_data:
                            trend_data[genre] = {}
                        trend_data[genre][month_str] = trend_data[genre].get(month_str, 0) + count
        
        # 获取热门类型（按总评分数排序）
        genre_totals = {}
        for genre, monthly_data in trend_data.items():
            genre_totals[genre] = sum(monthly_data.values())
        
        top_genres = sorted(genre_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            "trend_data": trend_data,
            "top_genres": [{"genre": genre, "total": total} for genre, total in top_genres],
            "months": sorted({month for data in trend_data.values() for month in data.keys()})
        })
        
    except Exception as e:
        return jsonify({"error": "类型趋势分析失败", "details": str(e)}), 500


@bp.get("/api/enhanced-stats/system-health")
@cache.cached(timeout=60)
def system_health_metrics():
    """系统健康指标"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # 基础系统指标
        health_metrics = {
            "database_status": "healthy",
            "cache_status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 数据库连接测试
        try:
            db.session.execute(db.text("SELECT 1"))
            health_metrics["database_response_time"] = "< 10ms"
        except Exception as e:
            health_metrics["database_status"] = "error"
            health_metrics["database_error"] = str(e)
        
        # 数据完整性检查
        health_metrics["data_integrity"] = {
            "movies_without_ratings": Movie.query.outerjoin(Rating).filter(Rating.id.is_(None)).count(),
            "ratings_without_movies": Rating.query.outerjoin(Movie).filter(Movie.id.is_(None)).count(),
            "users_without_ratings": User.query.outerjoin(Rating).filter(Rating.id.is_(None)).count()
        }
        
        # 系统负载指标（简化版）
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        health_metrics["system_load"] = {
            "ratings_last_hour": Rating.query.filter(Rating.timestamp >= one_hour_ago).count(),
            "active_users_last_hour": User.query.join(Rating).filter(
                Rating.timestamp >= one_hour_ago
            ).distinct().count(),
            "api_requests_estimate": "N/A"  # 需要添加请求日志才能统计
        }
        
        # 缓存效率（简化版）
        health_metrics["cache_efficiency"] = {
            "cache_type": "SimpleCache",
            "default_timeout": "300s",
            "note": "内存缓存，适合开发环境"
        }
        
        return jsonify(health_metrics)
        
    except Exception as e:
        return jsonify({"error": "系统健康检查失败", "details": str(e)}), 500


# ==================== 增强搜索API ====================

@bp.get("/api/search/advanced")
@cache.cached(timeout=180, query_string=True)
def advanced_search():
    """高级搜索 - 独立API，不影响现有搜索"""
    from sqlalchemy import func
    try:
        import time
        start_time = time.time()

        query = request.args.get('q', '').strip()
        genre = request.args.get('genre', '').strip()
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        rating_min = request.args.get('rating_min', type=float)
        sort_by = request.args.get('sort_by', 'relevance')  # relevance, year, rating, title
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        
        # 构建查询（使用现有Movie模型）
        movie_query = Movie.query
        
        # 文本搜索
        if query:
            movie_query = movie_query.filter(
                Movie.title.ilike(f"%{query}%")
            )
        
        # 类型筛选
        if genre:
            movie_query = movie_query.filter(Movie.genres.ilike(f"%{genre}%"))
        
        # 年份范围筛选
        if year_min:
            movie_query = movie_query.filter(Movie.year >= year_min)
        if year_max:
            movie_query = movie_query.filter(Movie.year <= year_max)
        
        # 评分筛选（需要join Rating表）
        if rating_min is not None:
            movie_query = movie_query.join(Rating).group_by(Movie.id).having(
                func.avg(Rating.rating) >= rating_min
            )
        
        # 排序
        if sort_by == 'year':
            movie_query = movie_query.order_by(Movie.year.desc())
        elif sort_by == 'rating':
            movie_query = movie_query.outerjoin(Rating).group_by(Movie.id).order_by(
                func.avg(Rating.rating).desc().nulls_last()
            )
        elif sort_by == 'title':
            movie_query = movie_query.order_by(Movie.title.asc())
        else:  # relevance (默认)
            if query:
                # 简单的相关性排序：标题匹配优先
                movie_query = movie_query.order_by(
                    Movie.title.ilike(f"{query}%").desc(),
                    Movie.title.ilike(f"%{query}%").desc()
                )
            else:
                movie_query = movie_query.order_by(Movie.year.desc())
        
        # 分页
        pagination = movie_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 获取每部电影的平均评分
        movies_with_ratings = []
        for movie in pagination.items:
            avg_rating = db.session.query(func.avg(Rating.rating)).filter(
                Rating.movie_id == movie.id
            ).scalar() or 0.0
            
            rating_count = db.session.query(func.count(Rating.id)).filter(
                Rating.movie_id == movie.id
            ).scalar() or 0
            
            movies_with_ratings.append({
                **movie.to_dict(),
                'avg_rating': round(avg_rating, 1),
                'rating_count': rating_count
            })
        
        # 获取搜索建议
        suggestions = get_search_suggestions(query) if query else []
        
        # 计算搜索时间
        search_time = round(time.time() - start_time, 3)
        
        return jsonify({
            "results": movies_with_ratings,
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "suggestions": suggestions,
            "search_time": f"{search_time}s",
            "query_info": {
                "query": query,
                "genre": genre,
                "year_min": year_min,
                "year_max": year_max,
                "rating_min": rating_min,
                "sort_by": sort_by
            }
        })
        
    except Exception as e:
        # 错误处理
        return jsonify({
            "error": "搜索服务暂时不可用",
            "suggestions": [],
            "results": [],
            "details": str(e)
        }), 500


@bp.get("/api/search/suggestions")
@cache.cached(timeout=600)
def search_suggestions():
    """搜索建议 - 独立功能"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({"suggestions": []})
        
        # 基于标题的模糊匹配
        title_suggestions = Movie.query.filter(
            Movie.title.ilike(f"{query}%")
        ).limit(8).all()
        
        # 基于类型的匹配
        genre_suggestions = Movie.query.filter(
            Movie.genres.ilike(f"%{query}%")
        ).distinct(Movie.genres).limit(5).all()
        
        # 组合建议
        suggestions = []
        
        # 标题建议
        for movie in title_suggestions:
            suggestions.append({
                "type": "movie",
                "text": movie.title,
                "value": movie.title,
                "year": movie.year
            })
        
        # 类型建议
        for movie in genre_suggestions:
            genres = movie.genres.split('|') if movie.genres else []
            for genre in genres:
                genre = genre.strip()
                if genre and query.lower() in genre.lower() and genre not in [s["text"] for s in suggestions]:
                    suggestions.append({
                        "type": "genre",
                        "text": genre,
                        "value": genre
                    })
                    if len(suggestions) >= 10:
                        break
        
        return jsonify({"suggestions": suggestions[:10]})
        
    except Exception as e:
        return jsonify({"suggestions": [], "error": str(e)})


@bp.get("/api/search/history")
@login_required
def search_history():
    """搜索历史记录"""
    try:
        # 获取用户最近的搜索记录
        # 这里可以扩展为存储在数据库中的搜索历史
        # 暂时返回空数组，后续可以添加搜索历史功能
        return jsonify({
            "history": [],
            "popular_searches": [
                "动作", "喜剧", "科幻", "爱情", "恐怖",
                "2023", "2024", "高分电影", "经典电影"
            ]
        })
        
    except Exception as e:
        return jsonify({"error": "获取搜索历史失败", "details": str(e)}), 500


def get_search_suggestions(query):
    """获取搜索建议的辅助函数"""
    try:
        suggestions = []
        
        # 标题匹配
        title_matches = Movie.query.filter(
            Movie.title.ilike(f"{query}%")
        ).limit(5).all()
        
        for movie in title_matches:
            suggestions.append(movie.title)
        
        # 类型匹配
        genre_matches = Movie.query.filter(
            Movie.genres.ilike(f"%{query}%")
        ).distinct(Movie.genres).limit(3).all()
        
        for movie in genre_matches:
            genres = movie.genres.split('|') if movie.genres else []
            for genre in genres:
                genre = genre.strip()
                if genre and query.lower() in genre.lower() and genre not in suggestions:
                    suggestions.append(genre)
        
        return suggestions[:8]
        
    except Exception:
        return []


# ==================== 导出功能辅助函数 ====================

def get_user_favorite_genres(user_id):
    """获取用户喜爱类型"""
    try:
        from sqlalchemy import func
        
        genre_stats = db.session.query(
            Movie.genres,
            func.avg(Rating.rating).label('avg_rating'),
            func.count(Rating.id).label('count')
        ).join(Rating).filter(Rating.user_id == user_id).group_by(Movie.genres).all()
        
        # 返回评分最高的前3个类型
        sorted_genres = sorted(genre_stats, key=lambda x: x[1], reverse=True)
        return [g[0] for g in sorted_genres[:3]]
    except Exception:
        return []


def get_user_statistics():
    """获取用户统计数据"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # 基础统计
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        # 本月新增用户
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        new_users_this_month = User.query.filter(User.created_at >= one_month_ago).count()
        
        # 有评分的用户
        users_with_ratings = db.session.query(Rating.user_id).distinct().count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'new_users_this_month': new_users_this_month,
            'users_with_ratings': users_with_ratings,
            'users_without_ratings': total_users - users_with_ratings
        }
    except Exception:
        return {}


def get_movie_statistics():
    """获取电影统计数据"""
    try:
        total_movies = Movie.query.count()
        movies_with_posters = Movie.query.filter(Movie.poster_url.isnot(None)).count()
        movies_with_ratings = db.session.query(Rating.movie_id).distinct().count()
        
        return {
            'total_movies': total_movies,
            'movies_with_posters': movies_with_posters,
            'movies_with_ratings': movies_with_ratings,
            'movies_without_ratings': total_movies - movies_with_ratings
        }
    except Exception:
        return {}


def get_rating_statistics():
    """获取评分统计数据"""
    try:
        from sqlalchemy import func
        
        # 基础统计
        total_ratings = Rating.query.count()
        avg_rating = db.session.query(func.avg(Rating.rating)).scalar() or 0
        
        return {
            'total_ratings': total_ratings,
            'average_rating': float(avg_rating)
        }
    except Exception:
        return {}


def get_review_statistics():
    """获取评论统计数据"""
    try:
        total_reviews = Review.query.count()
        approved_reviews = Review.query.filter_by(status='approved').count()
        pending_reviews = Review.query.filter_by(status='pending').count()
        rejected_reviews = Review.query.filter_by(status='rejected').count()
        
        return {
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_reviews': pending_reviews,
            'rejected_reviews': rejected_reviews
        }
    except Exception:
        return {}


def get_system_health_export():
    """获取系统健康数据"""
    try:
        # 数据完整性检查
        movies_without_ratings = Movie.query.outerjoin(Rating).filter(Rating.id.is_(None)).count()
        ratings_without_movies = Rating.query.outerjoin(Movie).filter(Movie.id.is_(None)).count()
        
        return {
            'data_integrity': {
                'movies_without_ratings': movies_without_ratings,
                'ratings_without_movies': ratings_without_movies
            }
        }
    except Exception:
        return {}


def get_behavior_analytics_export():
    """获取行为分析数据"""
    try:
        # 这里可以集成之前创建的行为分析功能
        return {
            'note': '行为分析功能需要用户行为追踪模块支持',
            'status': 'available'
        }
    except Exception:
        return {}


def export_to_csv(data, filename):
    """导出数据为CSV格式"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        
        if 'ratings' in data:
            # 导出评分数据
            writer = csv.writer(output)
            writer.writerow(['电影ID', '电影标题', '评分', '评分时间'])
            
            for rating in data['ratings']:
                writer.writerow([
                    rating.get('movie_id'),
                    rating.get('movie_title'),
                    rating.get('rating'),
                    rating.get('timestamp')
                ])
        
        # 创建响应
        from flask import current_app
        response = current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        return response
        
    except Exception as e:
        return jsonify({"error": "CSV导出失败", "details": str(e)}), 500


def export_system_stats_to_csv(stats):
    """导出系统统计数据为CSV"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 导出用户统计
        writer.writerow(['用户统计'])
        writer.writerow(['指标', '数值'])
        for key, value in stats['user_statistics'].items():
            writer.writerow([key, value])
        
        # 创建响应
        from flask import current_app
        response = current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=system_stats.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({"error": "系统统计CSV导出失败", "details": str(e)}), 500


def export_movies_to_csv(movie_data):
    """导出电影数据为CSV"""
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        headers = ['ID', '标题', '年份', '类型', '导演', '时长', '评分', '评分数']
        writer.writerow(headers)
        
        # 写入数据
        for movie in movie_data['movies']:
            writer.writerow([
                movie.get('id'),
                movie.get('title'),
                movie.get('year'),
                movie.get('genres'),
                movie.get('director'),
                movie.get('runtime'),
                movie.get('avg_rating', 0),
                movie.get('rating_count', 0)
            ])
        
        # 创建响应
        from flask import current_app
        response = current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=movies_data.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({"error": "电影数据CSV导出失败", "details": str(e)}), 500


# ==================== 用户画像系统API ====================

@bp.get("/api/user/profile")
@login_required
def get_user_profile():
    """获取用户画像"""
    try:
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            # 如果画像不存在，先计算
            profile = ProfileService.compute_user_profile(current_user.id)
        
        return jsonify({
            'profile': profile.to_dict(),
            'message': '获取成功'
        })
        
    except Exception as e:
        return jsonify({
            'error': '获取用户画像失败',
            'details': str(e)
        }), 500


@bp.get("/api/user/insights")
@login_required
def get_user_insights():
    """获取用户观影洞察"""
    try:
        insights = ProfileService.get_user_insights(current_user.id)
        
        return jsonify({
            'insights': insights,
            'count': len(insights)
        })
        
    except Exception as e:
        return jsonify({
            'error': '获取用户洞察失败',
            'details': str(e)
        }), 500


@bp.post("/api/user/profile/refresh")
@login_required
def refresh_user_profile():
    """手动触发画像重新计算"""
    try:
        profile = ProfileService.compute_user_profile(current_user.id)
        
        return jsonify({
            'success': True,
            'message': '画像重新计算成功',
            'profile': profile.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'error': '画像重新计算失败',
            'details': str(e)
        }), 500


@bp.get("/api/user/recommendation-reason")
@login_required
def get_recommendation_reason():
    """获取推荐理由（基于画像）"""
    try:
        movie_id = request.args.get('movie_id', type=int)
        
        if not movie_id:
            return jsonify({
                'error': '请提供电影ID'
            }), 400
        
        # 获取用户画像
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            return jsonify({
                'reason': '基于您的观影历史推荐',
                'details': []
            })
        
        # 获取电影信息
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({
                'error': '电影不存在'
            }), 404
        
        # 生成推荐理由
        reasons = []
        
        # 类型匹配
        if movie.genres and profile.preferred_genres:
            for genre in movie.genres.split('|'):
                genre = genre.strip()
                if genre in profile.preferred_genres:
                    reasons.append({
                        'type': 'genre',
                        'text': f'您喜欢{genre}类型的电影',
                        'match_score': profile.preferred_genres[genre]
                    })
        
        # 年代匹配
        if movie.year and profile.preferred_years:
            decade = f"{(movie.year // 10) * 10}s"
            if decade in profile.preferred_years:
                reasons.append({
                    'type': 'decade',
                    'text': f'您偏爱{decade}的电影',
                    'match_score': profile.preferred_years[decade]
                })
        
        # 演员匹配
        if movie.director and profile.preferred_directors:
            if movie.director in profile.preferred_directors:
                reasons.append({
                    'type': 'director',
                    'text': f'您喜欢{movie.director}导演的作品',
                    'match_score': 1.0
                })
        
        # 演员匹配
        if movie.actors:
            actors = movie.get_actors_list()
            for actor in actors:
                if actor in profile.preferred_actors:
                    reasons.append({
                        'type': 'actor',
                        'text': f'您喜欢{actor}主演的电影',
                        'match_score': 1.0
                    })
        
        return jsonify({
            'movie_id': movie_id,
            'movie_title': movie.title,
            'reason': '基于您的观影偏好推荐',
            'details': reasons[:3]  # 只返回前3个理由
        })
        
    except Exception as e:
        return jsonify({
            'error': '获取推荐理由失败',
            'details': str(e)
        }), 500


@bp.get("/user/profile")
@login_required
def user_profile_page():
    """用户画像页面"""
    return render_template('user_profile.html')


@bp.get("/user/insights")
@login_required
def user_insights_page():
    """用户洞察页面"""
    return render_template('user_insights.html')


# ==================== 影单功能 API ====================

@bp.post("/api/movie-lists")
@login_required
def create_movie_list():
    """创建影单"""
    try:
        data = request.get_json() or request.form
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        is_public = data.get('is_public', False)
        allow_comments = data.get('allow_comments', True)
        
        if not name:
            return jsonify({'error': '影单名称不能为空'}), 400
        
        movie_list = MovieList(
            user_id=current_user.id,
            name=name,
            description=description,
            is_public=is_public,
            allow_comments=allow_comments
        )
        
        db.session.add(movie_list)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '影单创建成功',
            'movie_list': movie_list.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建影单失败', 'details': str(e)}), 500


@bp.get("/api/movie-lists")
@login_required
def get_my_movie_lists():
    """获取当前用户的影单列表"""
    try:
        movie_lists = MovieList.query.filter_by(user_id=current_user.id).all()
        
        return jsonify({
            'movie_lists': [ml.to_dict() for ml in movie_lists],
            'count': len(movie_lists)
        })
        
    except Exception as e:
        return jsonify({'error': '获取影单列表失败', 'details': str(e)}), 500


@bp.get("/api/movie-lists/public")
def get_public_movie_lists():
    """获取公开的影单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        from sqlalchemy.orm import joinedload, selectinload

        query = MovieList.query.filter_by(is_public=True)\
            .options(joinedload(MovieList.user))\
            .options(selectinload(MovieList.items).joinedload(MovieListItem.movie))

        if search:
            query = query.filter(MovieList.name.ilike(f'%{search}%'))

        query = query.order_by(MovieList.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'movie_lists': [ml.to_dict() for ml in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total
            }
        })
        
    except Exception as e:
        return jsonify({'error': '获取公开影单失败', 'details': str(e)}), 500


@bp.get("/api/movie-lists/<int:list_id>")
def get_movie_list_detail(list_id):
    """获取影单详情"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        # 检查权限
        if not movie_list.is_public and movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限访问此影单'}), 403
        
        # 增加浏览次数
        movie_list.increment_view()
        
        return jsonify({
            'movie_list': movie_list.to_dict(include_items=True)
        })
        
    except Exception as e:
        return jsonify({'error': '获取影单详情失败', 'details': str(e)}), 500


@bp.put("/api/movie-lists/<int:list_id>")
@login_required
def update_movie_list(list_id):
    """更新影单"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        if movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限修改此影单'}), 403
        
        data = request.get_json() or request.form
        
        if 'name' in data:
            movie_list.name = data['name'].strip()
        
        if 'description' in data:
            movie_list.description = data['description'].strip()
        
        if 'is_public' in data:
            movie_list.is_public = bool(data['is_public'])
        
        if 'allow_comments' in data:
            movie_list.allow_comments = bool(data['allow_comments'])
        
        if 'cover_image' in data:
            movie_list.cover_image = data['cover_image']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '影单更新成功',
            'movie_list': movie_list.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新影单失败', 'details': str(e)}), 500


@bp.delete("/api/movie-lists/<int:list_id>")
@login_required
def delete_movie_list(list_id):
    """删除影单"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        if movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限删除此影单'}), 403
        
        db.session.delete(movie_list)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '影单删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除影单失败', 'details': str(e)}), 500


@bp.post("/api/movie-lists/<int:list_id>/movies")
@login_required
def add_movie_to_list(list_id):
    """添加电影到影单"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        if movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限修改此影单'}), 403
        
        data = request.get_json() or request.form
        movie_id = data.get('movie_id')
        note = data.get('note', '')
        
        if not movie_id:
            return jsonify({'error': '电影ID不能为空'}), 400
        
        success = movie_list.add_movie(movie_id, note)
        
        if success:
            return jsonify({
                'success': True,
                'message': '电影添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '该电影已在影单中'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '添加电影失败', 'details': str(e)}), 500


@bp.delete("/api/movie-lists/<int:list_id>/movies/<int:movie_id>")
@login_required
def remove_movie_from_list(list_id, movie_id):
    """从影单中移除电影"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        if movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限修改此影单'}), 403
        
        success = movie_list.remove_movie(movie_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '电影移除成功'
            })
        else:
            return jsonify({'error': '该电影不在影单中'}), 404
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '移除电影失败', 'details': str(e)}), 500


@bp.post("/api/movie-lists/<int:list_id>/like")
@login_required
def like_movie_list(list_id):
    """点赞/取消点赞影单"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        # 检查是否已点赞
        existing_like = MovieListLike.query.filter_by(
            movie_list_id=list_id,
            user_id=current_user.id
        ).first()
        
        if existing_like:
            # 取消点赞
            db.session.delete(existing_like)
            movie_list.like_count -= 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'liked': False,
                'like_count': movie_list.like_count
            })
        else:
            # 点赞
            like = MovieListLike(
                movie_list_id=list_id,
                user_id=current_user.id
            )
            db.session.add(like)
            movie_list.like_count += 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'liked': True,
                'like_count': movie_list.like_count
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '操作失败', 'details': str(e)}), 500


@bp.post("/api/movie-lists/<int:list_id>/comments")
@login_required
def add_comment_to_movie_list(list_id):
    """评论影单"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        if not movie_list.allow_comments:
            return jsonify({'error': '该影单不允许评论'}), 403
        
        data = request.get_json() or request.form
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return jsonify({'error': '评论内容不能为空'}), 400
        
        comment = MovieListComment(
            movie_list_id=list_id,
            user_id=current_user.id,
            content=content,
            parent_id=parent_id
        )
        
        db.session.add(comment)
        movie_list.comment_count += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '评论成功',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '评论失败', 'details': str(e)}), 500


@bp.get("/api/movie-lists/<int:list_id>/comments")
def get_movie_list_comments(list_id):
    """获取影单评论列表"""
    try:
        movie_list = MovieList.query.get(list_id)
        
        if not movie_list:
            return jsonify({'error': '影单不存在'}), 404
        
        # 检查权限
        if not movie_list.is_public and movie_list.user_id != current_user.id:
            return jsonify({'error': '您没有权限访问此影单'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = MovieListComment.query.filter_by(
            movie_list_id=list_id,
            parent_id=None  # 只获取顶级评论
        ).order_by(MovieListComment.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        comments = []
        for comment in pagination.items:
            comment_dict = comment.to_dict(include_replies=True)
            comments.append(comment_dict)
        
        return jsonify({
            'comments': comments,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total
            }
        })
        
    except Exception as e:
        return jsonify({'error': '获取评论失败', 'details': str(e)}), 500


# ==================== 影单页面路由 ====================

@bp.get("/movie-lists")
def movie_lists_page():
    """影单首页"""
    return render_template('movie_lists.html')


@bp.get("/movie-lists/create")
@login_required
def create_movie_list_page():
    """创建影单页面"""
    return render_template('create_movie_list.html')


@bp.get("/movie-lists/<int:list_id>")
def movie_list_detail_page(list_id):
    """影单详情页面"""
    return render_template('movie_list_detail.html', list_id=list_id)


@bp.get("/movie-lists/<int:list_id>/edit")
@login_required
def edit_movie_list_page(list_id):
    """编辑影单页面"""
    return render_template('edit_movie_list.html', list_id=list_id)
