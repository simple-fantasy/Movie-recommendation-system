#!/usr/bin/env python3
"""
推荐响应契约 Schema 验证 + DB查询性能诊断 — Step 1.4
纯诊断脚本。
"""
import os, sys, json, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

# 14 必需字段
REQUIRED_FIELDS = ["id", "title", "year", "genres", "avg_rating", "rating_count",
                   "score", "poster", "backdrop", "overview", "reason", "because"]

META_REQUIRED = ["actual_strategy"]

REASON_ENUM = {"similarity", "ncf", "hybrid", "popular"}

RESULTS = []
SCHEMA_ERRORS = []
TIMING_DATA = []


def validate_recommendation_item(item, strategy_name):
    """验证单个推荐项的契约"""
    errors = []

    # 字段存在性
    for field in REQUIRED_FIELDS:
        if field not in item:
            errors.append(f"缺少字段: {field}")

    # 类型检查
    if "id" in item and not isinstance(item["id"], int):
        errors.append(f"id类型错误: {type(item['id']).__name__}")
    if "title" in item and not isinstance(item["title"], str):
        errors.append(f"title类型错误")
    if "avg_rating" in item and not isinstance(item["avg_rating"], (int, float)):
        errors.append(f"avg_rating类型错误: {type(item['avg_rating']).__name__}")
    if "rating_count" in item and not isinstance(item["rating_count"], int):
        errors.append(f"rating_count类型错误: {type(item['rating_count']).__name__}")

    # reason枚举
    reason = item.get("reason")
    if reason not in REASON_ENUM:
        errors.append(f"reason值非法: '{reason}' ∉ {REASON_ENUM}")

    # score规则
    score = item.get("score")
    if score is not None:
        if not isinstance(score, (int, float)):
            errors.append(f"score类型错误: {type(score).__name__}")
        elif score < 0 or score > 50:  # ItemCF score can be >1
            errors.append(f"score范围异常: {score}")

    # because规则
    because = item.get("because")
    if because is not None:
        if not isinstance(because, list):
            errors.append(f"because类型错误: {type(because).__name__}")
        elif len(because) > 3:
            errors.append(f"because超过3项: {len(because)}")
        else:
            for b in because:
                if not isinstance(b, dict):
                    errors.append(f"because项不是dict")
                elif "movie_id" not in b or "title" not in b or "weight" not in b:
                    errors.append(f"because项缺少字段")

    return errors


def test_strategy(name, path, expected_reason, expected_score_rule, expected_because_rule,
                  expected_fallback=None, login_as=None):
    """测试单个策略的契约"""
    print(f"\n  [{name}] {path}")
    with app.test_client() as client:
        if login_as:
            client.post('/api/auth/login', json=login_as)

        t0 = time.time()
        resp = client.get(path)
        elapsed = time.time() - t0

        status = resp.status_code
        print(f"    状态码: {status} | 耗时: {elapsed:.3f}s")

        if status != 200:
            try:
                err = resp.get_json()
                print(f"    错误: {err.get('error', str(err)[:100])}")
            except Exception:
                print(f"    响应: {resp.data[:200]}")
            return {"name": name, "passed": False, "error": f"status={status}"}

        data = resp.get_json()
        if not data:
            return {"name": name, "passed": False, "error": "非JSON响应"}

        # 验证meta
        meta = data.get("meta", {})
        meta_errors = []
        for f in META_REQUIRED:
            if f not in meta:
                meta_errors.append(f"meta缺少{f}")

        recs = data.get("recommendations", [])
        item_errors = []
        reasons_found = set()
        all_scores_null = True
        has_scores = False
        all_because_null = True
        has_because = False
        ids = []

        for i, item in enumerate(recs):
            errs = validate_recommendation_item(item, name)
            if errs:
                item_errors.append(f"rec[{i}]: {', '.join(errs)}")
            reasons_found.add(item.get("reason"))
            if item.get("score") is not None:
                all_scores_null = False
                has_scores = True
            if item.get("because") is not None:
                all_because_null = False
                has_because = True
            ids.append(item.get("id"))

        # 策略规则验证
        errors = []

        # meta
        if meta_errors:
            errors.extend(meta_errors)

        # 字段级
        if item_errors:
            errors.extend(item_errors[:5])  # 取前5个

        # reason
        if expected_reason and expected_reason not in reasons_found:
            errors.append(f"期望reason={expected_reason}, 实际={reasons_found}")

        # score规则
        if expected_score_rule == "all_null":
            if has_scores:
                errors.append("期望score=null, 但存在非null score")
        elif expected_score_rule == "not_null":
            if all_scores_null:
                errors.append("期望score≠null, 但全部为null")

        # because规则
        if expected_because_rule == "all_null":
            if has_because:
                errors.append("期望because=null, 但存在非null because")
        elif expected_because_rule == "not_null":
            if all_because_null:
                errors.append("期望because≠null, 但全部为null")

        # 去重
        if len(ids) != len(set(ids)):
            errors.append(f"存在重复ID: {len(ids)}项中有{len(ids)-len(set(ids))}个重复")

        # fallback检查
        fallback = meta.get("fallback_reason")
        if expected_fallback and fallback != expected_fallback:
            errors.append(f"fallback_reason期望={expected_fallback}, 实际={fallback}")

        passed = len(errors) == 0
        result = {
            "name": name,
            "passed": passed,
            "elapsed": elapsed,
            "rec_count": len(recs),
            "reasons": list(reasons_found),
            "all_scores_null": all_scores_null,
            "all_because_null": all_because_null,
            "fallback": fallback,
            "errors": errors,
        }

        status_icon = "✅" if passed else "❌"
        print(f"    {status_icon} {'通过' if passed else '失败'} | recs={len(recs)} | reasons={reasons_found} | scores={'null' if all_scores_null else '非null'} | because={'null' if all_because_null else '非null'}")
        if errors:
            for e in errors[:3]:
                print(f"       ⚠️  {e}")

        return result


# ══════════════════════════════════════════════════════════════
print("=" * 70)
print("【测试集A】契约 Schema 验证")
print("=" * 70)

login = {'username': 'demo', 'password': 'demo123'}

results = {}

# A1: 匿名 → popular_fallback
results['anon'] = test_strategy(
    "匿名用户-popular_fallback", "/api/recommendations",
    expected_reason="popular", expected_score_rule="all_null",
    expected_because_rule="all_null", expected_fallback="anonymous_user")

# A2: 冷启动 → popular_fallback (使用之前创建的用户)
# 注册一个新的冷启动用户
with app.test_client() as client:
    import uuid
    cold_user = f"cold_{uuid.uuid4().hex[:6]}"
    resp = client.post('/api/auth/register', json={
        'username': cold_user, 'password': 'test123', 'email': f'{cold_user}@test.com'
    })

cold_login = {'username': cold_user, 'password': 'test123'}
results['cold'] = test_strategy(
    "冷启动用户-popular_fallback", "/api/recommendations",
    expected_reason="popular", expected_score_rule="all_null",
    expected_because_rule="all_null", expected_fallback="cold_start",
    login_as=cold_login)

# A3: demo-popular
results['popular'] = test_strategy(
    "demo-popular", "/api/recommendations?strategy=popular&n=10",
    expected_reason="popular", expected_score_rule="all_null",
    expected_because_rule="all_null", login_as=login)

# A4: demo-itemcf
results['itemcf'] = test_strategy(
    "demo-itemcf", "/api/recommendations?strategy=itemcf&n=10",
    expected_reason="similarity", expected_score_rule="not_null",
    expected_because_rule="not_null", login_as=login)

# A5: demo-ncf
results['ncf'] = test_strategy(
    "demo-ncf", "/api/recommendations?strategy=ncf&n=10",
    expected_reason="ncf", expected_score_rule="not_null",
    expected_because_rule="all_null", login_as=login)

# A6: demo-hybrid
results['hybrid'] = test_strategy(
    "demo-hybrid", "/api/recommendations?strategy=hybrid&n=10",
    expected_reason="hybrid", expected_score_rule="not_null",
    expected_because_rule="not_null", login_as=login)

# A7: demo-默认(itemcf)
results['default'] = test_strategy(
    "demo-默认策略", "/api/recommendations?n=10",
    expected_reason="similarity", expected_score_rule="not_null",
    expected_because_rule="not_null", login_as=login)

# A8: 无效策略
print(f"\n  [invalid] /api/recommendations?strategy=bad_strategy")
with app.test_client() as client:
    client.post('/api/auth/login', json=login)
    resp = client.get('/api/recommendations?strategy=bad_strategy')
    print(f"    状态码: {resp.status_code}")
    data = resp.get_json()
    is_json_error = data and "error" in data
    print(f"    {'✅' if resp.status_code == 400 and is_json_error else '❌'} "
          f"{'标准错误格式' if is_json_error else '非标准格式'} | error={data.get('error', 'N/A') if data else 'N/A'}")
    results['invalid'] = {"name": "无效策略", "passed": resp.status_code == 400 and is_json_error}


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集B】DB查询性能诊断（BUG-009根因确认）")
print("=" * 70)

with app.app_context():
    from backend.app.models import Rating, Movie
    from backend.app import cache, db
    from sqlalchemy import func

    # 清除popular fallback缓存
    cache.delete("_popular_fallback_12")

    print("\n  B1: _get_popular_fallback(12) — 冷查询")
    t0 = time.time()
    from backend.app.routes import _get_popular_fallback
    result = _get_popular_fallback(12)
    t1 = time.time()
    print(f"    耗时: {t1-t0:.3f}s | 结果数: {len(result)}")
    TIMING_DATA.append({"query": "popular_fallback(12) cold", "elapsed": t1-t0, "count": len(result)})

    print("\n  B2: _get_popular_fallback(12) — 热查询(缓存命中)")
    t0 = time.time()
    result2 = _get_popular_fallback(12)
    t1 = time.time()
    print(f"    耗时: {t1-t0:.6f}s | 结果数: {len(result2)}")
    TIMING_DATA.append({"query": "popular_fallback(12) warm", "elapsed": t1-t0, "count": len(result2)})

    # 直接测试DB查询（复制_get_popular_fallback中的子查询）
    print("\n  B3: 原始DB子查询 — GROUP BY movie_id on ratings")
    t0 = time.time()
    subq = (
        db.session.query(
            Rating.movie_id,
            func.count(Rating.id).label("cnt"),
            func.avg(Rating.rating).label("avg_r"),
        )
        .group_by(Rating.movie_id)
        .having(func.count(Rating.id) >= 50)
        .order_by(func.count(Rating.id).desc())
        .limit(300)
        .subquery()
    )
    movies = (
        Movie.query
        .join(subq, Movie.id == subq.c.movie_id)
        .filter(
            Movie.poster_url.isnot(None),
            Movie.poster_url != "",
            ~Movie.poster_url.contains("placeholder"),
        )
        .order_by(func.desc(subq.c.avg_r), func.desc(subq.c.cnt))
        .limit(12)
        .all()
    )
    t1 = time.time()
    print(f"    耗时: {t1-t0:.3f}s | 结果数: {len(movies)}")
    TIMING_DATA.append({"query": "raw DB: GROUP BY + JOIN movies", "elapsed": t1-t0, "count": len(movies)})

    # rating表记录数
    rating_count = db.session.query(func.count(Rating.id)).scalar()
    print(f"\n  ratings表总记录数: {rating_count:,}")

    # 检查索引
    print("\n  B4: 检查ratings表索引（通过查询计划）")
    t0 = time.time()
    # 尝试explain
    try:
        explain_result = db.session.execute(
            db.text("EXPLAIN QUERY PLAN SELECT movie_id, COUNT(id) as cnt, AVG(rating) as avg_r "
                    "FROM ratings GROUP BY movie_id HAVING COUNT(id) >= 50 "
                    "ORDER BY cnt DESC LIMIT 300")
        ).fetchall()
        for row in explain_result:
            print(f"    {row[0]} | {row[1]} | {row[2]}")
    except Exception as e:
        print(f"    EXPLAIN失败: {e}")
    t1 = time.time()
    TIMING_DATA.append({"query": "EXPLAIN QUERY PLAN", "elapsed": t1-t0})


# ══════════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("                    测试汇总报告")
print("=" * 70)

print("\n--- Schema契约验证 ---")
total = len(results)
passed = sum(1 for r in results.values() if r.get("passed", False))
failed = total - passed
print(f"策略数: {total} | 通过: ✅ {passed} | 失败: ❌ {failed}")

for key, r in results.items():
    if isinstance(r, dict) and "passed" in r:
        icon = "✅" if r["passed"] else "❌"
        extra = ""
        if r.get("errors"):
            extra = f" | 错误: {r['errors'][:2]}"
        print(f"  {icon} [{key}] recs={r.get('rec_count','?')} "
              f"reasons={r.get('reasons','?')} "
              f"scores={'null' if r.get('all_scores_null') else '非null'} "
              f"because={'null' if r.get('all_because_null') else '非null'} "
              f"fallback={r.get('fallback')}{extra}")

print("\n--- DB性能诊断 ---")
for t in TIMING_DATA:
    flag = " ⚠️ >1s" if t["elapsed"] > 1 else ""
    print(f"  {t['query']}: {t['elapsed']:.3f}s (count={t.get('count','N/A')}){flag}")

# 保存结果
output_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(output_dir, "step1.4_results.json"), "w", encoding="utf-8") as f:
    json.dump({
        "schema_results": {k: v for k, v in results.items()},
        "timing_data": TIMING_DATA,
        "summary": {"schema_passed": passed, "schema_failed": failed}
    }, f, ensure_ascii=False, indent=2, default=str)
print(f"\n详细结果已保存到: {os.path.join(output_dir, 'step1.4_results.json')}")
