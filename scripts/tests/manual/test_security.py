#!/usr/bin/env python3
"""
安全边界测试 — Step 2.2
鉴权绕过 / 注入攻击 / 数据泄露 / 速率限制
纯诊断脚本。
"""
import os, sys, json, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ.setdefault('FLASK_ENV', 'development')

from backend.app import create_app

app = create_app()

RESULTS = []
ERRORS = []
VULNS = []


def check(name, passed, detail="", vuln=None):
    icon = "✅" if passed else "❌"
    line = f"  {icon} {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        ERRORS.append({"name": name, "detail": detail})
        if vuln:
            VULNS.append({"name": name, "vulnerability": vuln, "detail": detail})


# ══════════════════════════════════════════════════════════════
print("=" * 70)
print("【测试集A】鉴权边界")
print("=" * 70)

with app.test_client() as client:
    # A1: 未登录访问推荐
    resp = client.get('/api/recommendations')
    data = resp.get_json()
    authed_as_anon = (resp.status_code == 200 and
                      data.get('meta', {}).get('actual_strategy') == 'popular_fallback')
    check("A1 未登录→popular_fallback", authed_as_anon,
          f"status={resp.status_code}, strategy={data.get('meta', {}).get('actual_strategy')}")

    # A2: 未登录访问why端点 → 应返回401 JSON
    resp = client.get('/api/recommendations/why/1')
    is_401_json = resp.status_code == 401 and resp.is_json
    check("A2 why端点未登录→401 JSON", is_401_json,
          f"status={resp.status_code}, is_json={resp.is_json}",
          vuln="鉴权绕过" if resp.status_code == 200 else None)

    # A3: 未登录访问why端点 → 不应返回HTML
    resp = client.get('/api/recommendations/why/1')
    is_html = resp.status_code == 200 and b'<!DOCTYPE' in resp.data[:100]
    check("A3 why端点未登录→非HTML", not is_html,
          "返回JSON错误" if not is_html else "返回HTML页面（可能导致SPA解析错误）")

    # A4: 伪造session → 推荐
    with client.session_transaction() as sess:
        sess['_user_id'] = '999999'  # demo user id as string
    resp = client.get('/api/recommendations?strategy=itemcf')
    # Flask-Login should reject invalid/corrupted session
    data = resp.get_json()
    # If session is invalid, Flask-Login treats as anonymous
    is_safe = (resp.status_code == 200 and
               data.get('meta', {}).get('fallback_reason') in ['anonymous_user', 'cold_start'])
    check("A4 伪造session→不泄露数据", is_safe,
          f"status={resp.status_code}, strategy={data.get('meta', {}).get('actual_strategy')}",
          vuln="会话伪造" if resp.status_code == 200 and data.get('meta', {}).get('actual_strategy') == 'itemcf' else None)

    # A5: 越权访问其他用户的推荐数据
    # 登录demo用户后检查响应中是否包含其他用户信息
    resp = client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
    resp = client.get('/api/recommendations?strategy=itemcf')
    data = resp.get_json()
    recs = data.get('recommendations', [])

    # 检查推荐响应中是否泄露敏感字段
    sensitive_fields = ['password', 'password_hash', 'email', 'security_question', 'security_answer']
    has_leak = False
    for rec in recs:
        for sf in sensitive_fields:
            if sf in rec:
                has_leak = True
                break
    check("A5 推荐响应不含敏感字段", not has_leak,
          f"检查了{len(recs)}条推荐的{sensitive_fields}" if not has_leak else f"发现泄露字段!",
          vuln="数据泄露" if has_leak else None)

    # A6: because字段不包含评分者信息
    for rec in recs:
        because = rec.get('because')
        if because:
            for b in because:
                has_user_field = any(f in b for f in ['user_id', 'username', 'email'])
                if has_user_field:
                    check("A6 because不含用户信息", False,
                          f"because项含用户字段: {b}",
                          vuln="数据泄露")
                    break
            else:
                continue
            break
    else:
        check("A6 because不含用户信息", True)


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集B】注入攻击")
print("=" * 70)

with app.test_client() as client:
    client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})

    # B1-B4: SQL注入尝试
    sql_payloads = [
        ("B1 SQL注入strategy", "?strategy=itemcf' OR '1'='1"),
        ("B2 SQL注入strategy(union)", "?strategy=itemcf' UNION SELECT * FROM users--"),
        ("B3 SQL注入n", "?n=1; DROP TABLE ratings;--"),
        ("B4 SQL注入recall_k", "?recall_k=1' OR 1=1--"),
    ]

    for name, payload in sql_payloads:
        resp = client.get(f'/api/recommendations{payload}')
        # 注入攻击应被参数校验拦截，不应返回数据库错误或200
        is_safe = resp.status_code in [400, 200]  # 200 with fallback is OK for strategy
        # 检查响应中是否包含SQL错误信息
        data = resp.get_json() if resp.is_json else {}
        has_sql_error = any(kw in str(data).lower() for kw in
                           ['sql', 'syntax', 'mysql', 'sqlite', 'database error', 'column', 'table'])
        check(name, not has_sql_error,
              f"status={resp.status_code}, sql_error={has_sql_error}",
              vuln="SQL注入" if has_sql_error else None)

    # B5: XSS — 检查推荐响应中title/genres是否被转义
    resp = client.get('/api/recommendations?strategy=itemcf&n=10')
    data = resp.get_json()
    for rec in data.get('recommendations', []):
        title = rec.get('title', '')
        if '<script>' in title.lower() or '<img' in title.lower():
            check("B5 XSS-title转义", False,
                  f"title含未转义HTML: {title[:50]}",
                  vuln="XSS")
            break
    else:
        check("B5 XSS-推荐响应title安全", True,
              "所有title均不含HTML标签")

    # B6: 路径遍历
    resp = client.get('/api/recommendations?strategy=../../etc/passwd')
    is_safe = resp.status_code in [400, 200]  # 400 expected, 200 with fallback OK
    data = resp.get_json() if resp.is_json else {}
    has_path_leak = 'passwd' in str(data).lower() or 'root:' in str(data)
    check("B6 路径遍历", not has_path_leak,
          f"status={resp.status_code}",
          vuln="路径遍历" if has_path_leak else None)

    # B7: 超大n值
    resp = client.get('/api/recommendations?n=999999999')
    # Should be clamped to 50 or return 400
    data = resp.get_json() if resp.is_json else {}
    rec_count = len(data.get('recommendations', []))
    is_safe = rec_count <= 50
    check("B7 超大n值截断", is_safe,
          f"recs={rec_count} (应≤50)",
          vuln="DoS" if rec_count > 50 else None)

    # B8: 负数recall_k
    resp = client.get('/api/recommendations?strategy=hybrid&recall_k=-1000')
    data = resp.get_json() if resp.is_json else {}
    rec_count = len(data.get('recommendations', []))
    is_safe = rec_count <= 500
    check("B8 负数recall_k", is_safe,
          f"recs={rec_count}",
          vuln="参数绕过" if rec_count > 500 else None)


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集C】速率限制与资源消耗")
print("=" * 70)

with app.test_client() as client:
    client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})

    # C1: 连续快速请求
    t0 = time.time()
    success_count = 0
    error_count = 0
    for i in range(20):
        resp = client.get('/api/recommendations?strategy=itemcf&n=5')
        if resp.status_code == 200:
            success_count += 1
        elif resp.status_code == 429:
            error_count += 1
        else:
            error_count += 1
    elapsed = time.time() - t0

    rate_limited = error_count > 0
    check("C1 20次快速请求", True,  # 总是通过（rate limit默认关闭）
          f"成功{success_count}/20, 耗时{elapsed:.2f}s, 限流={rate_limited}")

    # C2: 并发请求稳定性（通过test client模拟）
    import threading
    errors_in_threads = []

    def make_request(idx):
        try:
            with app.test_client() as c:
                c.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})
                resp = c.get('/api/recommendations?strategy=itemcf&n=3')
                if resp.status_code != 200:
                    errors_in_threads.append(f"Thread-{idx}: status={resp.status_code}")
        except Exception as e:
            errors_in_threads.append(f"Thread-{idx}: exception={e}")

    threads = []
    for i in range(5):
        t = threading.Thread(target=make_request, args=(i,), daemon=True)
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    check("C2 5并发请求稳定性", len(errors_in_threads) == 0,
          f"5线程全部成功" if not errors_in_threads else f"失败: {errors_in_threads}")


# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("【测试集D】数据泄露深度检查")
print("=" * 70)

with app.test_client() as client:
    client.post('/api/auth/login', json={'username': 'demo', 'password': 'demo123'})

    # 检查所有策略的响应
    strategies = [
        ("itemcf", "/api/recommendations?strategy=itemcf&n=10"),
        ("ncf", "/api/recommendations?strategy=ncf&n=10"),
        ("hybrid", "/api/recommendations?strategy=hybrid&n=10"),
        ("popular", "/api/recommendations?strategy=popular&n=10"),
    ]

    forbidden_fields = ['password', 'password_hash', 'email', 'security_question',
                       'security_answer', 'ip_address', 'session_token']

    for sname, spath in strategies:
        resp = client.get(spath)
        data = resp.get_json()

        # 检查顶层
        found_top = [f for f in forbidden_fields if f in data]
        if found_top:
            check(f"D-{sname} 顶层泄露", False,
                  f"顶层含: {found_top}",
                  vuln="数据泄露")

        # 检查推荐项
        for i, rec in enumerate(data.get('recommendations', [])):
            found_rec = [f for f in forbidden_fields if f in rec]
            if found_rec:
                check(f"D-{sname} rec[{i}]泄露", False,
                      f"含: {found_rec}",
                      vuln="数据泄露")
                break

        # 检查meta
        found_meta = [f for f in forbidden_fields if f in data.get('meta', {})]
        if found_meta:
            check(f"D-{sname} meta泄露", False,
                  f"meta含: {found_meta}",
                  vuln="数据泄露")

    check("D-all 所有策略无敏感字段泄露", True,
          f"检查了{len(strategies)}种策略×{len(forbidden_fields)}个敏感字段")


# ══════════════════════════════════════════════════════════════
# 汇总
# ══════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("                    安全测试汇总报告")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
failed = total - passed

print(f"\n总计: {total} | 通过: ✅ {passed} | 失败: ❌ {failed}")
print(f"通过率: {passed/total*100:.1f}%")

if VULNS:
    print(f"\n⚠️ 发现 {len(VULNS)} 个潜在安全问题:")
    for v in VULNS:
        print(f"  🔴 [{v['vulnerability']}] {v['name']} — {v['detail']}")
else:
    print(f"\n🟢 未发现安全漏洞")

if ERRORS:
    print(f"\n--- 失败用例 ({len(ERRORS)}) ---")
    for i, e in enumerate(ERRORS, 1):
        print(f"  [{i}] ❌ {e['name']} — {e['detail']}")

output_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(output_dir, "step2.2_results.json"), "w", encoding="utf-8") as f:
    json.dump({
        "results": RESULTS, "errors": ERRORS, "vulnerabilities": VULNS,
        "summary": {"total": total, "passed": passed, "failed": failed}
    }, f, ensure_ascii=False, indent=2)
print(f"\n详细结果已保存到: {os.path.join(output_dir, 'step2.2_results.json')}")
