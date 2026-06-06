#!/usr/bin/env python3
"""开发服务器启动 + 前端页面可访问性验证 — Step 4.1"""
import os, sys, time, subprocess, urllib.request, urllib.error, json

BASE = "http://127.0.0.1:5000"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def http_get(path):
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')[:500]
    except urllib.error.HTTPError as e:
        return e.code, str(e)[:200]
    except Exception as e:
        return -1, str(e)[:200]

def http_post_json(path, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(f"{BASE}{path}", data=body,
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": str(e)}
    except Exception as e:
        return -1, {"error": str(e)}

print("="*70)
print("启动开发服务器...")
print("="*70)

# 启动服务器
env = os.environ.copy()
env['PYTHONPATH'] = ROOT
env['FLASK_ENV'] = 'development'

proc = subprocess.Popen(
    [sys.executable, '-c',
     'import sys; sys.path.insert(0,"."); '
     'from backend.app import create_app; '
     'app=create_app(); app.run(host="127.0.0.1",port=5000,debug=False)'],
    cwd=ROOT, env=env,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

# 等待启动
print("等待服务器就绪...")
for i in range(30):
    try:
        urllib.request.urlopen(f"{BASE}/", timeout=2)
        print(f"服务器在第{i+1}秒就绪")
        break
    except Exception:
        time.sleep(1)
else:
    print("服务器启动超时!")
    proc.kill()
    sys.exit(1)

print()
print("="*70)
print("页面路由测试")
print("="*70)

pages = [
    ("门户页", "/"),
    ("登录页", "/login"),
    ("注册页", "/register"),
    ("应用主页", "/app"),
    ("电影详情", "/movies/1"),
    ("管理登录", "/admin/login"),
]

results = []
for name, path in pages:
    code, body = http_get(path)
    ok = code == 200
    results.append((name, code, ok))
    print(f"  {'✅' if ok else '❌'} {name:8s} GET {path:15s} -> {code}")

print()
print("="*70)
print("API连通性测试")
print("="*70)

# 不需要认证的API
apis = [
    ("电影详情API", "/api/movies/1"),
    ("热门推荐API(匿名)", "/api/recommendations"),
]

for name, path in apis:
    code, body = http_get(path)
    ok = code == 200
    try:
        data = json.loads(body) if isinstance(body, str) else body
        info = ""
        if 'title' in data:
            info = f" title={data.get('title','?')[:30]}"
        elif 'recommendations' in data:
            info = f" recs={len(data['recommendations'])} strategy={data.get('meta',{}).get('actual_strategy','?')}"
        elif 'error' in data:
            info = f" error={data['error'][:50]}"
    except Exception:
        info = ""
    results.append((name, code, ok))
    print(f"  {'✅' if ok else '❌'} {name:20s} -> {code}{info}")

# 登录API
code, data = http_post_json("/api/auth/login", {"username": "demo", "password": "demo123"})
ok = code == 200 and 'user' in data
results.append(("登录API", code, ok))
print(f"  {'✅' if ok else '❌'} 登录API -> {code} user={data.get('user',{}).get('username','?') if isinstance(data,dict) else '?'}")

print()
print("="*70)
print("静态资源测试")
print("="*70)

static_files = [
    "/static/js/api.js",
    "/static/js/vue-components.js",
]

for path in static_files:
    code, body = http_get(path)
    ok = code == 200
    results.append((f"静态{path.split('/')[-1]}", code, ok))
    print(f"  {'✅' if ok else '❌'} {path:35s} -> {code} ({len(body)} chars)")

print()
print("="*70)
print("汇总")
print("="*70)

total = len(results)
passed = sum(1 for _, _, ok in results if ok)
failed = total - passed

for name, code, ok in results:
    print(f"  {'✅' if ok else '❌'} {name:25s} -> {code}")

print(f"\n通过: {passed}/{total} ({passed/total*100:.0f}%)")

# 停止服务器
proc.kill()
proc.wait()
print("\n服务器已停止")
