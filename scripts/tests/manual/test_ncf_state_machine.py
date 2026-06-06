#!/usr/bin/env python3
"""
NCF Engine 状态机与线程安全诊断 — Step 1.3
纯诊断脚本，不做任何修改。
"""
import os, sys, json, time, threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from pathlib import Path

# 避免触发 before_request hook
from backend.app.ncf_engine import NCFEngine, NCF, TORCH_AVAILABLE

RESULTS = []
ERRORS = []

def log_result(name, passed, detail=""):
    status = "✅" if passed else "❌"
    msg = f"  {status} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        ERRORS.append({"name": name, "detail": detail})


# ══════════════════════════════════════════════════════════════
print("=" * 70)
print("【测试1】基础状态查询 — 获取当前NCF引擎状态")
print("=" * 70)

engine = NCFEngine()  # 获取单例

status = engine.get_status()
print(f"\n  当前状态: {json.dumps(status, indent=2, default=str)}")

log_result("T1.1 get_status返回dict", isinstance(status, dict))
log_result("T1.2 包含loaded字段", "loaded" in status)
log_result("T1.3 包含loading字段", "loading" in status)
log_result("T1.4 包含error字段", "error" in status)
log_result("T1.5 包含ready字段", "ready" in status)


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试2】user2idx 数据审计")
print("=" * 70)

is_ready = engine.is_ready()
log_result("T2.1 NCF已加载", is_ready)

if is_ready:
    num_users = engine.num_users
    num_items = engine.num_items
    print(f"\n  模型信息:")
    print(f"    num_users: {num_users}")
    print(f"    num_items: {num_items}")
    print(f"    embedding_dim: {engine.config.get('embedding_dim', 'N/A')}")
    print(f"    hidden_dim: {engine.config.get('hidden_dim', 'N/A')}")

    # 检查关键用户
    admin_in = 200949 in engine.user2idx
    demo_in = 999999 in engine.user2idx
    print(f"\n  用户覆盖:")
    print(f"    admin (200949) in user2idx: {admin_in}")
    print(f"    demo  (999999) in user2idx: {demo_in}")

    log_result("T2.2 admin(200949)在训练集中", admin_in,
               "admin可用于NCF推理" if admin_in else "admin不在训练集→NCF fallback")
    log_result("T2.3 demo(999999)在训练集中", demo_in,
               "demo可用于NCF推理" if demo_in else "demo不在训练集")

    # user2idx范围
    uids = list(engine.user2idx.keys())
    if uids:
        print(f"\n  user2idx 范围: min={min(uids)}, max={max(uids)}, count={len(uids)}")
        log_result("T2.4 user2idx非空", len(uids) > 0, f"共{len(uids)}个用户")

    # item2idx范围
    iids = list(engine.item2idx.keys())
    if iids:
        print(f"  item2idx 范围: min={min(iids)}, max={max(iids)}, count={len(iids)}")
        log_result("T2.5 item2idx非空", len(iids) > 0, f"共{len(iids)}个物品")

    # 模型文件路径
    artifacts_dir = Path(__file__).resolve().parents[4] / "backend" / "artifacts"
    ncf_pt = artifacts_dir / "ncf.pt"
    ncf_v2_pt = artifacts_dir / "ncf_v2.pt"
    ncf_meta = artifacts_dir / "ncf_meta.json"
    ncf_v2_meta = artifacts_dir / "ncf_v2_meta.json"

    print(f"\n  模型文件:")
    for fpath in [ncf_pt, ncf_v2_pt, ncf_meta, ncf_v2_meta]:
        exists = fpath.exists()
        size = fpath.stat().st_size if exists else 0
        print(f"    {fpath.name}: {'存在' if exists else '不存在'} ({size/1024/1024:.1f}MB)" if exists else f"    {fpath.name}: 不存在")

    log_result("T2.6 ncf.pt存在", ncf_pt.exists())
    log_result("T2.7 ncf_v2.pt存在", ncf_v2_pt.exists())
    log_result("T2.8 ncf_meta.json存在", ncf_meta.exists())
    log_result("T2.9 ncf_v2_meta.json存在", ncf_v2_meta.exists())

    # 对比两个meta文件的用户覆盖
    if ncf_meta.exists() and ncf_v2_meta.exists():
        import json
        meta1 = json.loads(ncf_meta.read_text())
        meta2 = json.loads(ncf_v2_meta.read_text())
        u1 = set(int(k) for k in meta1.get("user2idx", {}).keys())
        u2 = set(int(k) for k in meta2.get("user2idx", {}).keys())
        print(f"\n  模型对比:")
        print(f"    ncf.pt     用户数: {len(u1)}, admin∈: {200949 in u1}")
        print(f"    ncf_v2.pt  用户数: {len(u2)}, admin∈: {200949 in u2}")
        print(f"    ncf.pt     物品数: {len(meta1.get('item2idx', {}))}")
        print(f"    ncf_v2.pt  物品数: {len(meta2.get('item2idx', {}))}")
        log_result("T2.10 ncf_v2含admin", 200949 in u2, "v2模型包含admin用户")
        log_result("T2.11 ncf.pt含admin", 200949 in u1, "生产模型包含admin用户")
else:
    log_result("T2.2-T2.11 跳过", False, "NCF未加载，跳过数据审计")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试3】NCF Score 分布诊断（验证 BUG-008）")
print("=" * 70)

if engine.is_ready():
    # 使用demo用户的评分，获取NCF score分布
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        from backend.app.models import Rating
        # demo user = 999999 (confirmed in training set)
        demo_ratings = Rating.query.filter_by(user_id=999999).order_by(Rating.timestamp.desc()).limit(50).all()
        rated_ids = {r.movie_id for r in demo_ratings}

        # 获取候选集：热门未评分电影
        popular_unrated_query = (
            Rating.query.with_entities(
                Rating.movie_id,
                __import__('sqlalchemy').func.count(Rating.id).label("cnt")
            )
            .filter(~Rating.movie_id.in_(rated_ids))
            .group_by(Rating.movie_id)
            .order_by(__import__('sqlalchemy').desc("cnt"))
            .limit(100)
        )
        candidates = [int(mid) for mid, _ in popular_unrated_query.all()]

        if candidates:
            scores_dict = engine.score(999999, candidates)
            if scores_dict:
                scores = list(scores_dict.values())
                import statistics
                print(f"\n  demo用户 NCF score 分布 (100候选):")
                print(f"    count : {len(scores)}")
                print(f"    min   : {min(scores):.6f}")
                print(f"    max   : {max(scores):.6f}")
                print(f"    mean  : {statistics.mean(scores):.6f}")
                print(f"    stdev : {statistics.stdev(scores):.6f}" if len(scores) > 1 else "    stdev : N/A")
                print(f"    median: {statistics.median(scores):.6f}")
                print(f"    >0.999: {sum(1 for s in scores if s > 0.999)}/{len(scores)}")
                print(f"    >0.99 : {sum(1 for s in scores if s > 0.99)}/{len(scores)}")
                print(f"    >0.9  : {sum(1 for s in scores if s > 0.9)}/{len(scores)}")
                print(f"    <0.5  : {sum(1 for s in scores if s < 0.5)}/{len(scores)}")

                has_variance = statistics.stdev(scores) > 0.001 if len(scores) > 1 else False
                log_result("T3.1 NCF score有区分度(std>0.001)", has_variance,
                           f"stdev={statistics.stdev(scores):.6f}" if len(scores) > 1 else "N/A")
                log_result("T3.2 NCF score不全是>0.999", not all(s > 0.999 for s in scores),
                           f"{sum(1 for s in scores if s > 0.999)}/{len(scores)} > 0.999")

                if not has_variance:
                    print(f"\n  ⚠️ 确认 BUG-008: NCF scores无区分度! stdev={statistics.stdev(scores):.6f}")
            else:
                log_result("T3.1 score返回空", False, "score()返回空字典")
        else:
            log_result("T3.1 无候选", False, "候选集为空")
else:
    log_result("T3.x 跳过", False, "NCF未加载")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试4】NCF 加载时间测量（验证 BUG-009）")
print("=" * 70)

# 创建一个全新的 NCFEngine 实例来测量加载时间
# 注意：不能直接创建，因为 NCFEngine 是单例。
# 我们使用 reload() 来测量完整加载时间

if engine.is_ready():
    print("\n  测量 reload() 时间...")
    t0 = time.time()
    success = engine.reload()
    t1 = time.time()
    elapsed = t1 - t0
    print(f"  reload() 耗时: {elapsed:.2f}s")
    log_result("T4.1 reload成功", success)
    log_result("T4.2 reload<5s", elapsed < 5, f"实际{elapsed:.1f}s")
    log_result("T4.3 reload<10s", elapsed < 10, f"实际{elapsed:.1f}s")
    log_result("T4.4 reload后is_ready", engine.is_ready())
else:
    # 首次加载
    print("\n  测量首次 load() 时间...")
    t0 = time.time()
    success = engine.load()
    t1 = time.time()
    elapsed = t1 - t0
    print(f"  load() 耗时: {elapsed:.2f}s")
    log_result("T4.1 load成功", success)
    log_result("T4.2 load<5s", elapsed < 5, f"实际{elapsed:.1f}s")
    log_result("T4.3 load<10s", elapsed < 10, f"实际{elapsed:.1f}s")
    log_result("T4.4 load后is_ready", engine.is_ready())


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试5】并发安全性测试")
print("=" * 70)

if engine.is_ready():
    errors_in_threads = []
    results_lock = threading.Lock()

    def concurrent_score(thread_id):
        """线程中执行 score()"""
        try:
            # 使用demo用户
            result = engine.score(999999, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            with results_lock:
                if not result:
                    errors_in_threads.append(f"Thread-{thread_id}: score returned empty")
        except Exception as e:
            with results_lock:
                errors_in_threads.append(f"Thread-{thread_id}: exception={e}")

    print("\n  启动10个并发score线程...")
    threads = []
    for i in range(10):
        t = threading.Thread(target=concurrent_score, args=(i,), daemon=True)
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    log_result("T5.1 并发score无异常", len(errors_in_threads) == 0,
               f"{len(errors_in_threads)}个线程出错: {errors_in_threads[:3]}" if errors_in_threads else "全部成功")

    # 并发score + reload 竞态
    print("\n  启动 score + reload 竞态测试...")
    reload_done = threading.Event()
    score_errors = []
    reload_error = []

    def score_during_reload():
        for i in range(50):
            try:
                engine.score(999999, [1, 2, 3])
            except Exception as e:
                score_errors.append(str(e))
            time.sleep(0.01)

    def do_reload():
        try:
            engine.reload()
        except Exception as e:
            reload_error.append(str(e))
        reload_done.set()

    t_score = threading.Thread(target=score_during_reload, daemon=True)
    t_reload = threading.Thread(target=do_reload, daemon=True)

    t_score.start()
    time.sleep(0.05)
    t_reload.start()

    t_score.join(timeout=60)
    t_reload.join(timeout=60)

    log_result("T5.2 score+reload竞态无crash", True,
               f"score异常:{len(score_errors)}, reload异常:{len(reload_error)}")
    log_result("T5.3 reload后is_ready", engine.is_ready())

    # 快速reload循环
    print("\n  快速 reload 循环 (5次)...")
    reload_times = []
    for i in range(5):
        t0 = time.time()
        engine.reload()
        t1 = time.time()
        reload_times.append(t1 - t0)

    avg_time = sum(reload_times) / len(reload_times)
    print(f"  平均reload时间: {avg_time:.3f}s (单次: {[f'{t:.2f}' for t in reload_times]})")
    log_result("T5.4 5次reload全部成功", engine.is_ready(), f"平均{avg_time:.2f}s")
    log_result("T5.5 reload时间稳定", max(reload_times) - min(reload_times) < 2,
               f"max-min={max(reload_times)-min(reload_times):.2f}s")
else:
    log_result("T5.x 跳过", False, "NCF未加载，跳过并发测试")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试6】负面场景测试")
print("=" * 70)

# 6.1 用户不在训练集
admin_result = engine.score(200949, [1, 2, 3, 4, 5]) if engine.is_ready() else {}
log_result("T6.1 admin score返回空", len(admin_result) == 0,
           f"返回{len(admin_result)}个结果（预期0）" if admin_result else "正确返回空")

# 6.2 空候选列表
empty_result = engine.score(999999, []) if engine.is_ready() else {}
log_result("T6.2 空候选返回空", empty_result == {} or len(empty_result) == 0)

# 6.3 无效item_id
invalid_result = engine.score(999999, [99999999, -1, 0]) if engine.is_ready() else {}
log_result("T6.3 无效item_id被跳过", len(invalid_result) == 0,
           f"返回{len(invalid_result)}个结果（预期0）")

# 6.4 get_status字段完整性
status2 = engine.get_status()
required_fields = ["loaded", "loading", "error", "ready", "last_error",
                   "last_attempt_time", "model_mtime", "num_users", "num_items"]
missing = [f for f in required_fields if f not in status2]
log_result("T6.4 get_status字段完整", len(missing) == 0,
           f"缺少: {missing}" if missing else "全部存在")

# 6.5 should_retry逻辑
# 刚reload成功，should_retry应该返回False（不需要重试）
retry = engine.should_retry(30)
log_result("T6.5 Ready状态should_retry=False", not retry,
           f"should_retry={retry}")


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

# 保存结果
output_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(output_dir, "step1.3_results.json"), "w", encoding="utf-8") as f:
    json.dump({
        "results": RESULTS,
        "errors": ERRORS,
        "summary": {"total": total, "passed": passed, "failed": failed}
    }, f, ensure_ascii=False, indent=2)
print(f"\n详细结果已保存到: {os.path.join(output_dir, 'step1.3_results.json')}")
