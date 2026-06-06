#!/usr/bin/env python3
"""
手动推荐API测试 — Step 1.2
纯诊断脚本，不做任何修复。
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

RESULTS = []
ERRORS = []


def test(name, method, path, expected_status=200, json_body=None, check_fields=None, check_meta=None, login_as=None):
    """执行单次API测试并记录结果"""
    with app.test_client() as client:
        # 登录
        if login_as:
            client.post('/api/auth/login', json=login_as)

        # 发起请求
        if method == 'GET':
            resp = client.get(path)
        elif method == 'POST':
            resp = client.post(path, json=json_body)
        else:
            resp = client.get(path)

        status = resp.status_code
        passed = (status == expected_status)

        result = {
            "name": name,
            "method": method,
            "path": path,
            "expected_status": expected_status,
            "actual_status": status,
            "passed": passed,
            "login_as": login_as.get('username') if login_as else None,
        }

        # 解析JSON
        try:
            data = resp.get_json()
            result["has_json"] = True
        except Exception:
            data = None
            result["has_json"] = False

        if data:
            result["keys"] = list(data.keys())
            if "recommendations" in data:
                recs = data["recommendations"]
                result["rec_count"] = len(recs) if recs else 0

                # 字段完整性
                if recs and len(recs) > 0:
                    r = recs[0]
                    expected_keys = ["id", "title", "year", "genres", "avg_rating", "rating_count",
                                     "score", "poster", "backdrop", "overview", "reason", "because"]
                    missing = [k for k in expected_keys if k not in r]
                    result["missing_fields"] = missing if missing else None

                    # reason枚举
                    result["reasons"] = list(set(item.get("reason") for item in recs))

                    # score范围
                    scores = [item.get("score") for item in recs if item.get("score") is not None]
                    if scores:
                        result["score_range"] = f"{min(scores):.4f} ~ {max(scores):.4f}"
                    else:
                        result["score_range"] = "all None"

                    # because
                    has_because = sum(1 for item in recs if item.get("because") is not None)
                    result["has_because"] = f"{has_because}/{len(recs)}"

                    # 去重
                    ids = [item["id"] for item in recs]
                    result["has_duplicates"] = len(ids) != len(set(ids))

            if "meta" in data:
                result["meta"] = data["meta"]
            if "error" in data:
                result["error"] = data["error"]

        if not passed:
            error_detail = {
                "name": name,
                "expected": expected_status,
                "actual": status,
                "path": path,
                "body_preview": str(data)[:200] if data else "N/A",
            }
            ERRORS.append(error_detail)
            result["error_detail"] = str(data)[:200] if data else "N/A"

        RESULTS.append(result)
    return result


# ══════════════════════════════════════════════════════════════
# 测试1: 鉴权边界
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集1】鉴权边界")
print("=" * 70)

test("T1.1 匿名用户-默认推荐", "GET", "/api/recommendations", 200,
     check_meta={"actual_strategy": "popular_fallback", "fallback_reason": "anonymous_user"})

test("T1.2 匿名用户-显式popular", "GET", "/api/recommendations?strategy=popular", 200)

test("T1.3 匿名用户-显式itemcf", "GET", "/api/recommendations?strategy=itemcf", 200,
     check_meta={"actual_strategy": "popular_fallback"})

test("T1.4 匿名用户-显式ncf", "GET", "/api/recommendations?strategy=ncf", 200)

test("T1.5 匿名用户-显式hybrid", "GET", "/api/recommendations?strategy=hybrid", 200)


# ══════════════════════════════════════════════════════════════
# 测试2: admin用户 (200949, 有评分, 是管理员)
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集2】admin用户 (有评分记录)")
print("=" * 70)

login = {'username': 'admin', 'password': 'admin123'}

test("T2.1 admin-默认策略", "GET", "/api/recommendations", 200, login_as=login)
test("T2.2 admin-popular", "GET", "/api/recommendations?strategy=popular&n=12", 200, login_as=login)
test("T2.3 admin-itemcf-n=10", "GET", "/api/recommendations?strategy=itemcf&n=10", 200, login_as=login)
test("T2.4 admin-itemcf-n=50", "GET", "/api/recommendations?strategy=itemcf&n=50", 200, login_as=login)
test("T2.5 admin-itemcf-n=1", "GET", "/api/recommendations?strategy=itemcf&n=1", 200, login_as=login)
test("T2.6 admin-ncf", "GET", "/api/recommendations?strategy=ncf&n=10", 200, login_as=login)
test("T2.7 admin-hybrid", "GET", "/api/recommendations?strategy=hybrid&n=10", 200, login_as=login)
test("T2.8 admin-hybrid-recall_k=500", "GET", "/api/recommendations?strategy=hybrid&recall_k=500&n=10", 200, login_as=login)
test("T2.9 admin-itemcf-n=100截断", "GET", "/api/recommendations?strategy=itemcf&n=100", 200, login_as=login)
test("T2.10 admin-itemcf-n=0", "GET", "/api/recommendations?strategy=itemcf&n=0", 200, login_as=login)
test("T2.11 admin-itemcf-n=负数", "GET", "/api/recommendations?strategy=itemcf&n=-5", 200, login_as=login)
test("T2.12 admin-itemcf-n=非数字", "GET", "/api/recommendations?strategy=itemcf&n=abc", 200, login_as=login)
test("T2.13 admin-未知策略", "GET", "/api/recommendations?strategy=invalid_strategy", 400, login_as=login)


# ══════════════════════════════════════════════════════════════
# 测试3: demo用户 (非管理员, 可能有评分)
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集3】demo用户")
print("=" * 70)

demo_login = {'username': 'demo', 'password': 'demo123'}

test("T3.1 demo-默认", "GET", "/api/recommendations", 200, login_as=demo_login)
test("T3.2 demo-popular", "GET", "/api/recommendations?strategy=popular", 200, login_as=demo_login)
test("T3.3 demo-itemcf", "GET", "/api/recommendations?strategy=itemcf", 200, login_as=demo_login)
test("T3.4 demo-ncf", "GET", "/api/recommendations?strategy=ncf", 200, login_as=demo_login)
test("T3.5 demo-hybrid", "GET", "/api/recommendations?strategy=hybrid", 200, login_as=demo_login)


# ══════════════════════════════════════════════════════════════
# 测试4: 冷启动用户（新建一个临时用户）
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集4】冷启动用户 (0评分)")
print("=" * 70)

import uuid
cold_username = f"test_cold_{uuid.uuid4().hex[:8]}"
cold_password = "test123456"

# 注册新用户
with app.test_client() as client:
    resp = client.post('/api/auth/register', json={
        'username': cold_username,
        'password': cold_password,
        'email': f'{cold_username}@test.com'
    })
    reg_data = resp.get_json()
    if resp.status_code == 200:
        print(f"   ℹ️  冷启动用户已注册: {cold_username}")
    else:
        print(f"   ⚠️ 注册失败: {reg_data.get('error', 'unknown')}")

cold_login = {'username': cold_username, 'password': cold_password}

test("T4.1 冷启动-默认", "GET", "/api/recommendations", 200, login_as=cold_login)
test("T4.2 冷启动-popular", "GET", "/api/recommendations?strategy=popular", 200, login_as=cold_login)
test("T4.3 冷启动-itemcf", "GET", "/api/recommendations?strategy=itemcf", 200, login_as=cold_login,
     check_meta={"fallback_reason": "cold_start"})

# ══════════════════════════════════════════════════════════════
# 测试5: why端点
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集5】推荐解释端点")
print("=" * 70)

test("T5.1 why端点-有效movie_id", "GET", "/api/recommendations/why/1", 200, login_as=login)
test("T5.2 why端点-无效movie_id", "GET", "/api/recommendations/why/999999", 200, login_as=login)
test("T5.3 why端点-未登录", "GET", "/api/recommendations/why/1", 302, login_as=None)


# ══════════════════════════════════════════════════════════════
# 汇总报告
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
    print(f"--- 失败用例 ({len(ERRORS)}) ---")
    for i, e in enumerate(ERRORS, 1):
        print(f"\n  [{i}] {e['name']}")
        print(f"      路径: {e['path']}")
        print(f"      预期状态码: {e['expected']} → 实际: {e['actual']}")
        print(f"      响应: {e['body_preview']}")

print("\n--- 策略响应详情 ---")
for r in RESULTS:
    status = "✅" if r["passed"] else "❌"
    meta_str = ""
    if r.get("meta"):
        meta_str = f" | meta={r['meta']}"
    rec_str = ""
    if r.get("rec_count") is not None:
        rec_str = f" | recs={r['rec_count']}"
        if r.get("reasons"):
            rec_str += f" reasons={r['reasons']}"
        if r.get("missing_fields"):
            rec_str += f" ❌missing={r['missing_fields']}"
        if r.get("has_duplicates"):
            rec_str += " ❌DUPLICATES"
        if r.get("score_range"):
            rec_str += f" scores={r['score_range']}"
        if r.get("has_because"):
            rec_str += f" because={r['has_because']}"
    error_str = ""
    if r.get("error"):
        error_str = f" | error={r['error']}"
    print(f"  {status} [{r['name']}] {r['method']} {r['path']} → {r['actual_status']}{meta_str}{rec_str}{error_str}")

# 输出JSON结果文件
output_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(output_dir, "step1.2_results.json"), "w", encoding="utf-8") as f:
    json.dump({"results": RESULTS, "errors": ERRORS, "summary": {
        "total": total, "passed": passed, "failed": failed,
        "pass_rate": f"{passed/total*100:.1f}%"
    }}, f, ensure_ascii=False, indent=2)
print(f"\n详细结果已保存到: {os.path.join(output_dir, 'step1.2_results.json')}")
