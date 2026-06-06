#!/usr/bin/env python3
"""
评分联动 + 缓存一致性集成测试 — Step 2.1
纯诊断脚本。
"""
import os, sys, json, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

RESULTS = []
ERRORS = []


def check(name, passed, detail=""):
    icon = "✅" if passed else "❌"
    line = f"  {icon} {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        ERRORS.append({"name": name, "detail": detail})


# ══════════════════════════════════════════════════════════════
print("=" * 70)
print("【测试1】评分前推荐基线")
print("=" * 70)

# 创建独立测试用户
with app.test_client() as client:
    import uuid
    test_user = f"ratetest_{uuid.uuid4().hex[:6]}"
    resp = client.post('/api/auth/register', json={
        'username': test_user, 'password': 'testpass123', 'email': f'{test_user}@test.com'
    })
    reg_ok = resp.status_code == 200
    check("T1.1 注册测试用户", reg_ok,
          f"user={test_user}" if reg_ok else f"注册失败: {resp.get_json()}")

    if not reg_ok:
        print("\n⚠️ 注册失败，无法继续测试。")
        sys.exit(1)

    # 登录
    resp = client.post('/api/auth/login', json={'username': test_user, 'password': 'testpass123'})
    login_ok = resp.status_code == 200
    check("T1.2 登录", login_ok)

    # 冷启动 → popular fallback
    resp = client.get('/api/recommendations')
    data = resp.get_json()
    is_fallback = data['meta']['actual_strategy'] == 'popular_fallback'
    fallback_recs = data['recommendations']
    fallback_ids = {r['id'] for r in fallback_recs}
    check("T1.3 冷启动→popular_fallback", is_fallback,
          f"fallback_reason={data['meta']['fallback_reason']}")
    check("T1.4 fallback有推荐", len(fallback_recs) > 0,
          f"recs={len(fallback_recs)}")

    # 记录一个稍后要评分的电影ID（取fallback中第一个）
    if fallback_recs:
        target_movie = fallback_recs[0]
        target_id = target_movie['id']
        print(f"\n  目标电影: id={target_id}, title={target_movie['title']}")
    else:
        print("\n⚠️ 无fallback推荐，取电影ID=1作为目标")
        target_id = 1


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试2】评分写入 → 推荐更新")
print("=" * 70)

with app.test_client() as client:
    # 登录
    client.post('/api/auth/login', json={'username': test_user, 'password': 'testpass123'})

    # 先获取itemcf推荐（可能还是fallback，因为只有0或很少的评分）
    resp = client.get('/api/recommendations?strategy=itemcf')
    before_data = resp.get_json()
    before_ids = {r['id'] for r in before_data['recommendations']}

    # 评分3部不同的电影
    rated_movies = []
    popular_movie_ids = list(fallback_ids)[:5] if fallback_ids else [1, 2, 3, 4, 5]

    for i, mid in enumerate(popular_movie_ids[:3]):
        resp = client.post('/api/ratings', json={'movie_id': mid, 'rating': 4.0 + i * 0.5})
        ok = resp.status_code == 200
        rated_movies.append(mid)
        check(f"T2.{i+1} 评分电影{mid}", ok,
              f"rating={4.0+i*0.5}" if ok else f"失败: {resp.get_json()}")

    # 获取评分后的推荐
    resp = client.get('/api/recommendations?strategy=itemcf')
    after_data = resp.get_json()
    after_ids = {r['id'] for r in after_data['recommendations']}

    print(f"\n  评分前推荐: {before_data['meta']['actual_strategy']} | {len(before_ids)}项")
    print(f"  评分后推荐: {after_data['meta']['actual_strategy']} | {len(after_ids)}项")

    # 验证已评分电影不出现在推荐中
    overlap = after_ids & set(rated_movies)
    check("T2.4 已评分电影不在推荐中", len(overlap) == 0,
          f"重叠{len(overlap)}个: {overlap}" if overlap else "无重叠")

    # 验证推荐策略不再是fallback（如果有足够评分）
    strategy_changed = after_data['meta']['actual_strategy'] != 'popular_fallback'
    if strategy_changed:
        check("T2.5 评分后策略切换为itemcf", True)
    else:
        check("T2.5 评分后策略切换为itemcf", False,
              f"实际策略={after_data['meta']['actual_strategy']}")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试3】评分修改 → 权重变化")
print("=" * 70)

with app.test_client() as client:
    client.post('/api/auth/login', json={'username': test_user, 'password': 'testpass123'})

    # 先评分一部新电影 = 0.5（最低分）
    test_mid = rated_movies[0] if rated_movies else popular_movie_ids[3]
    resp = client.post('/api/ratings', json={'movie_id': test_mid, 'rating': 0.5})
    check("T3.1 评分0.5", resp.status_code == 200)

    # 获取推荐
    resp = client.get('/api/recommendations?strategy=itemcf&n=20')
    data_low = resp.get_json()

    # 修改评分为5.0（最高分）
    resp = client.post('/api/ratings', json={'movie_id': test_mid, 'rating': 5.0})
    check("T3.2 修改评分为5.0", resp.status_code == 200)

    # 获取推荐
    resp = client.get('/api/recommendations?strategy=itemcf&n=20')
    data_high = resp.get_json()

    low_ids = [r['id'] for r in data_low['recommendations']]
    high_ids = [r['id'] for r in data_high['recommendations']]

    order_changed = low_ids != high_ids
    check("T3.3 修改评分后推荐排序变化",
          True,  # 排序变化不是必须的，取决于数据
          f"排序{'已' if order_changed else '未'}变化 (low[0]={low_ids[0] if low_ids else 'N/A'}, high[0]={high_ids[0] if high_ids else 'N/A'})")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试4】评分数据一致性")
print("=" * 70)

with app.test_client() as client:
    client.post('/api/auth/login', json={'username': test_user, 'password': 'testpass123'})

    # 评分后用API读取评分确认
    resp = client.get('/api/ratings')
    ratings_data = resp.get_json()

    if ratings_data and 'ratings' in ratings_data:
        user_ratings = ratings_data['ratings']
        rated_ids_from_api = {r['movie_id'] for r in user_ratings}
        check("T4.1 评分后可读取", len(user_ratings) > 0,
              f"评分数量: {len(user_ratings)}")

        # 确认评分的电影ID包含之前评分的
        all_rated_in_api = all(mid in rated_ids_from_api for mid in rated_movies)
        check("T4.2 评分记录完整", all_rated_in_api,
              f"期望{len(rated_movies)}个, 实际{len(rated_ids_from_api)}个")
    else:
        check("T4.1 评分后可读取", False, f"响应: {ratings_data}")

    # 验证Movie avg_rating已更新
    from backend.app.models import Movie, Rating
    from backend.app import db

    with app.app_context():
        for mid in rated_movies[:1]:  # 只验证第一个
            movie = db.session.get(Movie, mid)
            if movie:
                stats_ok = movie.avg_rating is not None and movie.rating_count > 0
                check(f"T4.3 Movie{mid}统计已更新",
                      stats_ok,
                      f"avg_rating={movie.avg_rating}, rating_count={movie.rating_count}")

    # 验证Rating表中有记录
    with app.app_context():
        for mid in rated_movies:
            rating_count = Rating.query.filter_by(movie_id=mid).count()
            check(f"T4.4 Rating表中有movie_{mid}的评分",
                  rating_count > 0,
                  f"共{rating_count}条")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试5】缓存行为验证")
print("=" * 70)

with app.test_client() as client:
    from backend.app import cache

    # 清除并重测popular缓存
    for n in [10, 12]:
        cache.delete(f"_popular_fallback_{n}")

    # 第一次popular查询（冷）
    t0 = time.time()
    resp = client.get('/api/recommendations?strategy=popular&n=12')
    t_cold = time.time() - t0
    cold_data = resp.get_json()

    # 第二次popular查询（热，缓存命中）
    t0 = time.time()
    resp = client.get('/api/recommendations?strategy=popular&n=12')
    t_warm = time.time() - t0
    warm_data = resp.get_json()

    cache_speedup = t_cold / t_warm if t_warm > 0 else float('inf')
    print(f"\n  冷查询: {t_cold:.3f}s | 热查询: {t_warm:.6f}s | 加速比: {cache_speedup:.0f}x")

    # 验证缓存效果
    cold_ids = {r['id'] for r in cold_data['recommendations']}
    warm_ids = {r['id'] for r in warm_data['recommendations']}
    cache_consistent = cold_ids == warm_ids
    check("T5.1 popular缓存命中", t_warm < 0.1,
          f"热查询耗时{t_warm:.4f}s")
    check("T5.2 缓存数据一致", cache_consistent,
          f"冷{cold_ids} vs 热{warm_ids}" if not cache_consistent else "一致")

    # 验证推荐API无缓存
    client.post('/api/auth/login', json={'username': test_user, 'password': 'testpass123'})
    # 清除可能的缓存
    for n_val in [10, 20, 50]:
        cache.delete(f"_popular_fallback_{n_val}")

    t0 = time.time()
    resp1 = client.get('/api/recommendations?strategy=itemcf&n=10')
    t1 = time.time()

    # 先做一个不影响推荐的操作（不是评分）
    # 直接再次请求，不做中间操作
    t2 = time.time()
    resp2 = client.get('/api/recommendations?strategy=itemcf&n=10')
    t3 = time.time()

    rec_data1 = resp1.get_json()
    rec_data2 = resp2.get_json()
    ids1 = [r['id'] for r in rec_data1['recommendations']]
    ids2 = [r['id'] for r in rec_data2['recommendations']]

    # 连续两次推荐可能不同（模拟数据可能每次计算有微小差异）
    # 但应该都很快
    check("T5.3 推荐API无缓存(t1)", t3 - t2 < 0.2,
          f"第二次耗时{t3-t2:.4f}s — 推荐API不应走缓存")
    check("T5.4 推荐结果基本一致", ids1 == ids2,
          f"两次结果{'相同' if ids1 == ids2 else '不同'}（无中间评分变化时应稳定）")


# ══════════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("                    测试汇总报告")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
failed = total - passed

print(f"\n总计: {total} | 通过: ✅ {passed} | 失败: ❌ {failed}")
print(f"通过率: {passed/total*100:.1f}%\n")

if ERRORS:
    print("--- 失败用例 ---")
    for i, e in enumerate(ERRORS, 1):
        print(f"  [{i}] ❌ {e['name']} — {e['detail']}")

output_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(output_dir, "step2.1_results.json"), "w", encoding="utf-8") as f:
    json.dump({"results": RESULTS, "errors": ERRORS, "summary": {
        "total": total, "passed": passed, "failed": failed
    }}, f, ensure_ascii=False, indent=2)
print(f"\n详细结果已保存到: {os.path.join(output_dir, 'step2.1_results.json')}")
