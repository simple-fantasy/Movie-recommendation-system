# Bug 清单 — 推荐引擎系统功能测试

> **创建时间**: 2026-06-06
> **测试阶段**: Phase 1 冒烟测试 (Step 1.1 + Step 1.2)
> **状态**: 待修复（测试完成后统一进入缺陷修复模式）

---

## Bug 总览

| # | 等级 | 模块 | 简述 | 来源 |
|---|------|------|------|------|
| BUG-001 | 🔴 P0 | Notifications | 通知API全部404 | Step 1.1 |
| BUG-002 | 🔴 P0 | Charts | 榜单API全部404 | Step 1.1 |
| BUG-003 | 🟡 P1 | Admin API | 3个管理统计API 404 | Step 1.1 |
| BUG-004 | 🟡 P1 | 测试脚本 | 无断言机制，404被静默隐藏 | Step 1.1 |
| BUG-005 | 🟢 P2 | Admin Dashboard | 仪表板API响应3.7s | Step 1.1 |
| BUG-006 | 🔴 P0 | 推荐API | n=负数绕过推荐数量上限 | Step 1.2 |
| BUG-007 | 🔴 P0 | 推荐API | n=非数字导致500错误 | Step 1.2 |
| BUG-008 | 🟡 P1 | NCF推理 | score全部≈1.0无区分度 | Step 1.2 |
| BUG-009 | 🔴 P0 | NCF加载 | 首次请求阻塞12秒 | Step 1.2 |
| BUG-010 | 🟡 P1 | NCF训练 | admin用户不在训练集中 | Step 1.2 |

**统计**: P0×5 / P1×4 / P2×1 = **10个**

---

---

## BUG-001

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-001 |
| **严重等级** | 🔴 P0 — 功能缺失，用户可见 |
| **发现时间** | 2026-06-06 Step 1.1 |
| **所属模块** | `backend/app/routes.py` — Notifications（消息通知系统） |
| **测试脚本** | `scripts/tests/test_all_modules.py` |

### 复现步骤

```bash
# 1. 以admin用户登录
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 请求通知列表
curl http://127.0.0.1:5000/api/notifications

# 3. 请求未读数量
curl http://127.0.0.1:5000/api/notifications/unread-count

# 4. 标记全部已读
curl -X POST http://127.0.0.1:5000/api/notifications/read-all
```

### 预期行为

- `GET /api/notifications` → 200, 返回通知列表JSON
- `GET /api/notifications/unread-count` → 200, 返回未读数
- `POST /api/notifications/read-all` → 200, 标记已读

### 实际行为

全部返回 **404 Not Found**

### 日志证据

```
werkzeug.exceptions.NotFound: 404 Not Found: The requested URL was not found
on the server.
  path: /api/notifications
  path: /api/notifications/unread-count
  path: /api/notifications/read-all
```

### 根因猜测

通知API路由未在 `routes.py` 中注册。可能原因：
1. 通知功能在重构中被移除但测试脚本未同步更新
2. 路由注册条件未满足（如某个feature flag）
3. 通知端点被迁移到其他Blueprint但未正确挂载

### 影响范围

- 🔴 用户无法收到任何通知（评论回复、系统消息等）
- 🔴 前端通知图标可能永远显示空状态
- 🟡 如前端有轮询通知的JS代码，会持续产生404错误日志

### 关联Bug

- BUG-004（测试脚本未检测到404即失败）

---

## BUG-002

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-002 |
| **严重等级** | 🔴 P0 — 功能缺失，用户可见 |
| **发现时间** | 2026-06-06 Step 1.1 |
| **所属模块** | `backend/app/routes.py` — Charts（电影榜单系统） |
| **测试脚本** | `scripts/tests/test_all_modules.py` |

### 复现步骤

```bash
# 1. 请求榜单列表
curl http://127.0.0.1:5000/api/charts

# 2. 请求热门榜单
curl http://127.0.0.1:5000/api/charts/popular
```

### 预期行为

- `GET /api/charts` → 200, 返回榜单列表 `{charts: [...]}`
- `GET /api/charts/popular` → 200, 返回热门/高分/编辑推荐

### 实际行为

全部返回 **404 Not Found**

### 日志证据

```
werkzeug.exceptions.NotFound: 404 Not Found:
  path: /api/charts
  path: /api/charts/popular
```

### 根因猜测

榜单API路由未在 `routes.py` 中注册。可能原因同BUG-001——在重构中被移除但测试脚本未更新。

### 影响范围

- 🔴 前端榜单页面（如有）无法加载数据
- 🔴 演示中无法展示"热门榜单""高分榜单"功能

### 关联Bug

- BUG-004（测试脚本未检测到404即失败）

---

## BUG-003

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-003 |
| **严重等级** | 🟡 P1 — 管理功能缺失 |
| **发现时间** | 2026-06-06 Step 1.1 |
| **所属模块** | `backend/app/admin_routes.py` — Admin API |
| **测试脚本** | `scripts/tests/test_all_modules.py`, `scripts/tests/test_reviews.py` |

### 复现步骤

```bash
# 以admin登录后：
# 1. 评分统计
curl http://127.0.0.1:5000/api/admin/ratings/stats

# 2. 评论统计
curl http://127.0.0.1:5000/api/admin/reviews/stats

# 3. 榜单管理页面
curl http://127.0.0.1:5000/admin/charts
```

### 预期行为

三个端点均返回 200

### 实际行为

全部返回 **404 Not Found**

### 日志证据

```
werkzeug.exceptions.NotFound: 404 Not Found:
  path: /api/admin/ratings/stats  (Step 1.1)
  path: /api/admin/reviews/stats  (Step 1.1)
  path: /admin/charts             (Step 1.1)
```

### 根因猜测

`admin_routes.py` 未注册这三个端点。可能是功能未实现或路由路径变更后测试脚本未更新。

### 影响范围

- 🟡 管理员统计面板部分数据缺失
- 🟡 榜单管理功能不可用

---

## BUG-004

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-004 |
| **严重等级** | 🟡 P1 — 测试基础设施缺陷 |
| **发现时间** | 2026-06-06 Step 1.1 |
| **所属模块** | `scripts/tests/test_all_modules.py` |
| **测试脚本** | `scripts/tests/test_all_modules.py` |

### 复现步骤

阅读 `test_all_modules.py` 源码：

```python
# test_notifications() 中:
response = client.get('/api/notifications')
data = response.get_json()
if response.status_code == 200:
    print(f"   ✓ 获取通知列表成功")
    print(f"   未读数: {data['unread_count']}")
# ← 没有 else 分支! 404时什么都不输出

# test_admin_features() 中:
response = client.get('/api/admin/ratings/stats')
data = response.get_json()
if response.status_code == 200:
    print(f"   ✓ 评分统计API正常")
# ← 同样没有 else 分支
```

### 预期行为

```python
# 正确的测试写法:
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
# 或:
if response.status_code != 200:
    print(f"   ✗ FAIL: expected 200, got {response.status_code}")
    failures.append(...)
```

### 实际行为

- 6 个 404 错误被静默忽略
- 脚本始终打印 "✅ 全部测试完成"
- 脚本始终以 exit code 0 退出
- 所有手动运行此脚本的人都被误导为"全部通过"

### 根因分析

6 个测试脚本均采用相同的 "if 200 → print ✓" 模式，无断言、无失败计数、无非零退出码。这是结构性问题，影响全部 6 个脚本。

### 影响范围

- 🔴 任何依赖这些测试脚本的CI/CD流水线会误报通过
- 🟡 后续开发者无法信任测试结果
- 🟡 BUG-001/002/003 因测试脚本缺陷而长期未被发现

### 关联Bug

- BUG-001, BUG-002, BUG-003（均因本Bug被隐藏）

---

## BUG-005

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-005 |
| **严重等级** | 🟢 P2 — 性能退化 |
| **发现时间** | 2026-06-06 Step 1.1 |
| **所属模块** | `backend/app/admin_routes.py` — Admin Dashboard API |
| **测试脚本** | `scripts/tests/test_admin_dashboard.py` |

### 复现步骤

```bash
# 以admin登录
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 请求仪表板数据
time curl http://127.0.0.1:5000/api/admin/dashboard
```

### 预期行为

响应时间 < 1s

### 实际行为

响应时间 **3.7 秒**

### 日志证据

```
"method": "GET", "path": "/api/admin/dashboard",
"duration_seconds": 3.697176218032837
```

### 根因猜测

Dashboard 聚合查询可能涉及：
1. 全表扫描 `ratings` 表（32M行）做 COUNT/AVG
2. 多个大表 JOIN
3. 缺少复合索引

### 影响范围

- 🟢 管理员仪表板打开慢（登录后首次加载3.7s）
- 🟢 答辩演示时打开管理面板有可感知延迟
- 🟢 对普通用户无影响（管理员专用端点）

---

## BUG-006

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-006 |
| **严重等级** | 🔴 P0 — 参数校验绕过 |
| **发现时间** | 2026-06-06 Step 1.2 |
| **所属模块** | `backend/app/routes.py:929` — 推荐API参数校验 |
| **测试脚本** | `scripts/tests/manual/test_recommend_api.py` |

### 复现步骤

```bash
# 以有评分用户登录后：
curl "http://127.0.0.1:5000/api/recommendations?strategy=itemcf&n=-5" \
  -H "Cookie: session=<valid_session>"
```

### 预期行为

- 方案A：400 Bad Request + `{"error": "n must be a positive integer"}`
- 方案B：负数被截断为默认值10

### 实际行为

返回 **95 个推荐项**，远超上限50

### 日志证据

```
T2.11 admin-itemcf-n=负数 → 200 | recs=95 | scores=2.0118 ~ 18.2953
```

### 根因分析

```python
# routes.py:929
top_n = min(int(request.args.get("n") or 10), 50)

# 执行流程:
# int("-5") = -5
# min(-5, 50) = -5          ← 没有对负数做校验!
# ranked[: -5]              ← Python切片: "除最后5项外的全部"
#                           ← 等价于 ranked[:len(ranked)-5]
```

**关键缺陷**: `min()` 不能保护负数输入。必须显式校验 `n > 0`。

### 影响范围

- 🔴 **安全风险**: 恶意请求可绕过 n=50 上限，单次获取大量推荐数据
- 🔴 **性能风险**: n=-10000 可能返回数万条数据，消耗内存和带宽
- 🔴 **逻辑缺陷**: 与 n=0 返回空→fallback 的语义矛盾

### 修复建议

```python
try:
    n = int(request.args.get("n") or 10)
except (ValueError, TypeError):
    return jsonify({"error": "n must be an integer"}), 400
if n < 1 or n > 50:
    return jsonify({"error": "n must be between 1 and 50"}), 400
```

### 关联Bug

- BUG-007（同一行代码的不同异常路径）

---

## BUG-007

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-007 |
| **严重等级** | 🔴 P0 — 未处理异常导致500 |
| **发现时间** | 2026-06-06 Step 1.2 |
| **所属模块** | `backend/app/routes.py:929` — 推荐API参数校验 |
| **测试脚本** | `scripts/tests/manual/test_recommend_api.py` |

### 复现步骤

```bash
curl "http://127.0.0.1:5000/api/recommendations?strategy=itemcf&n=abc"
```

### 预期行为

- 400 Bad Request + `{"error": "n must be an integer"}`

### 实际行为

**500 Internal Server Error**

### 日志证据

```
ValueError: invalid literal for int() with base 10: 'abc'

Traceback:
  File "...flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  ...
  File "backend/app/routes.py", line 929, in recommend
    top_n = min(int(request.args.get("n") or 10), 50)

Response: {"code": "UNEXPECTED_ERROR", "error": "服务器发生意外错误"}
```

### 根因分析

```python
# routes.py:929
top_n = min(int(request.args.get("n") or 10), 50)
#           ~~~                          ← 没有 try/except 包裹
# "abc" → int("abc") → ValueError → 未捕获 → Flask 500
```

`recall_k` 有类似的模式（line 931）:
```python
recall_k = min(int(request.args.get("recall_k") or 100), 500)
#             ~~~ 同样没有 try/except
```

### 影响范围

- 🔴 任何含非数字 `n` 或 `recall_k` 参数的请求导致500
- 🔴 搜索引擎爬虫/安全扫描器可能触发此错误
- 🔴 在生产环境中5xx错误会触发告警

### 修复建议

与 BUG-006 合并修复，统一参数校验逻辑。

### 关联Bug

- BUG-006（同一行代码，不同输入触发的不同错误模式）

---

## BUG-008

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-008 |
| **严重等级** | 🟡 P1 — 推荐质量缺陷 |
| **发现时间** | 2026-06-06 Step 1.2 |
| **所属模块** | `backend/app/ncf_engine.py` — NCF 推理 |
| **测试脚本** | `scripts/tests/manual/test_recommend_api.py` |

### 复现步骤

```bash
# 以demo用户登录（在NCF训练集中）:
curl "http://127.0.0.1:5000/api/recommendations?strategy=ncf&n=10" \
  -H "Cookie: session=<demo_session>"
```

### 预期行为

NCF scores 分布在 [0, 1] 区间，有明显区分度（如 0.12, 0.34, 0.56, ...）

### 实际行为

全部 scores 集中在 **0.9988 ~ 0.9999**，几乎无区分度

### 日志证据

```
T3.4 demo-ncf:
  scores=0.9991 ~ 0.9999  ← NCF独立推荐
  reasons=['ncf']

T3.5 demo-hybrid:
  scores=0.9988 ~ 0.9999  ← Hybrid重排后
  reasons=['hybrid']
```

对比 ItemCF（同一用户）:
```
T3.3 demo-itemcf:
  scores=32.5222 ~ 47.4196  ← ItemCF有明显的分数梯度
```

### 根因猜测

1. **Sigmoid 饱和**: NCF模型训练过度，输出logits过大→sigmoid饱和在接近1的区域
2. **负采样不足**: 训练时负样本太少，模型学会了"几乎所有item-user对都预测高分"
3. **训练数据泄露**: 验证集/测试集的item在训练时被模型"记住"
4. **模型架构问题**: 3层MLP容量不足以学习区分性特征

### 验证方法

```python
# 检测NCF score分布
scores = ncf_engine.score(user_id, candidate_ids)
import numpy as np
print(f"NCF score stats: min={min(scores):.4f}, max={max(scores):.4f}, "
      f"mean={np.mean(scores):.4f}, std={np.std(scores):.6f}")
# 如果 std < 0.001 → 确认score饱和
```

### 影响范围

- 🔴 **Hybrid策略退化**: ItemCF召回→NCF重排几乎等于随机打乱ItemCF结果（因为所有候选分数一样）
- 🟡 论文实验结论"NCF未超过ItemCF"可能有此原因
- 🟡 演示中切换NCF策略无法体现"深度学习模型"的任何优势

### 关联Bug

- BUG-010（admin不在训练集中，无法交叉验证score分布）

---

## BUG-009

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-009 |
| **严重等级** | 🔴 P0 — 严重性能问题 |
| **发现时间** | 2026-06-06 Step 1.2 |
| **所属模块** | `backend/app/__init__.py` — `before_request` NCF预加载钩子 |
| **测试脚本** | `scripts/tests/manual/test_recommend_api.py` |

### 复现步骤

```bash
# 1. 重启Flask应用（冷启动）
# 2. 匿名用户请求热门推荐（不需要NCF）:
curl "http://127.0.0.1:5000/api/recommendations"
```

### 预期行为

热门推荐不需要NCF模型，应直接返回缓存数据，响应 < 200ms

### 实际行为

响应时间 **12.6 秒**

### 日志证据

```
# 首个请求（匿名，popular_fallback）:
T1.1: "duration_seconds": 12.576174974441528

# 对比——缓存命中后的相同请求:
T1.2: "duration_seconds": 0.001413    ← 仅1.4ms!

# admin登录后的popular请求（再次触发NCF加载）:
T2.2: "duration_seconds": 12.473610    ← 又等了12.5s!
```

每次 `create_app()` 后的首次请求被阻塞12秒，因为 `before_request` 钩子中同步触发 NCF 模型加载。

### 根因分析

`backend/app/__init__.py` 中的 `before_request` 钩子:

```python
@app.before_request
def _preload_ncf():
    if not ncf_engine.is_ready() and not ncf_engine.is_loading():
        ncf_engine.load()  # ← 同步加载! 阻塞12秒!
```

关键问题:
1. `load()` 是**同步**方法（不是 `load_async()`）
2. 钩子对**所有请求**触发（包括匿名用户、静态资源）
3. NCF模型文件加载 + 200K×84K 索引映射解析耗时12秒

### 影响范围

- 🔴 **答辩演示不可接受**: 评委打开网页需等待12秒 → 印象分极差
- 🔴 **用户体验**: 首次访问用户（匿名）也要等待12秒
- 🔴 **并发问题**: 12秒加载期间如有其他请求到达，`is_loading()`=True 时不会重复加载，但 `is_ready()`=False 时NCF策略会fallback

### 修复建议

方案A — 改用异步加载：
```python
@app.before_request
def _preload_ncf():
    if not ncf_engine.is_ready() and not ncf_engine.is_loading():
        ncf_engine.load_async()  # 不阻塞请求线程
```

方案B — 条件触发（仅已登录用户）：
```python
@app.before_request
def _preload_ncf():
    if current_user.is_authenticated:
        if not ncf_engine.is_ready() and not ncf_engine.is_loading():
            ncf_engine.load_async()
```

方案C — 启动时预加载（推荐）：
```python
# 在 create_app() 的最后，app.run() 之前:
with app.app_context():
    ncf_engine.load_async()  # 后台加载，不影响首个请求
```

### 关联Bug

- BUG-010（NCF加载后admin仍无法使用NCF）

---

## BUG-010

| 字段 | 内容 |
|------|------|
| **Bug编号** | BUG-010 |
| **严重等级** | 🟡 P1 — 数据/配置不一致 |
| **发现时间** | 2026-06-06 Step 1.2 |
| **所属模块** | NCF 训练数据 vs 生产推理 |
| **测试脚本** | `scripts/tests/manual/test_recommend_api.py` |

### 复现步骤

```bash
# 以admin用户（user_id=200949）登录后：
curl "http://127.0.0.1:5000/api/recommendations?strategy=ncf&n=10"
```

### 预期行为

NCF推理正常，返回 `reason="ncf"` 的推荐。

admin用户特征：
- 有评分记录（ItemCF推荐正常）
- 是活跃用户（login_count=35）
- user_id=200949

### 实际行为

fallback 到 ItemCF: `meta.fallback_reason="user_not_in_ncf_training_set"`

### 日志证据

```
T2.6 admin-ncf:
  meta={'actual_strategy': 'itemcf_fallback',
        'fallback_reason': 'user_not_in_ncf_training_set'}
```

### 根因猜测

1. **版本不匹配**: NCF模型文件 (`ncf.pt`) 用旧版训练数据训练，当时user_id 200949 不存在
2. **手动创建**: admin 用户是 `seed.py` 或 `seed_demo_user.py` 手动创建的，创建时间晚于NCF训练
3. **用户ID范围**: MovieLens原始用户ID范围可能是 1~200948，200949 是系统自动分配的第一个手动用户ID
4. **模型文件混淆**: `ncf_engine.py` 加载 `ncf.pt`，离线评估用 `ncf_v2.pt`，两者可能包含不同的用户集

### 验证方法

```python
from backend.app.ncf_engine import ncf_engine
# 检查admin是否在user2idx中
print(200949 in ncf_engine.user2idx)  # 预期: False
# 检查NCF模型的用户数量
print(f"num_users: {ncf_engine.num_users}")  # 预期: 200949
```

### 影响范围

- 🟡 **演示限制**: admin 是默认演示账号，无法展示NCF策略
- 🟡 demo用户（999999）在训练集中 → NCF正常 → 演示可用demo替代admin
- 🟡 论文实验数据不包含admin（无影响）

### 关联Bug

- handoff 中已知的 `ncf.pt` vs `ncf_v2.pt` 路径不一致
- BUG-008（demo用户NCF score饱和）

---

## 附录A — Bug 严重等级定义

| 等级 | 标签 | 定义 | 修复时限 |
|------|------|------|----------|
| **P0** | 🔴 高 | 功能缺失/崩溃/安全漏洞/演示阻塞 | 答辩前必须修复 |
| **P1** | 🟡 中 | 质量缺陷/数据不一致/功能降级 | 答辩前建议修复 |
| **P2** | 🟢 低 | 性能退化/体验优化/代码异味 | 择期修复 |

## 附录B — 按模块分布

```
Notifications  ██ P0×1
Charts         ██ P0×1
Admin API      ██ P1×1  ██ P2×1
测试脚本        ██ P1×1
推荐API参数校验  ██ P0×2 (BUG-006, BUG-007)
NCF推理        ██ P1×1 (BUG-008)
NCF加载        ██ P0×1 (BUG-009)
NCF训练数据     ██ P1×1 (BUG-010)
```

## 附录C — 变更记录

| 日期 | 变更 | 来源 |
|------|------|------|
| 2026-06-06 | 初始创建，记录BUG-001 ~ BUG-010 | Step 1.1 + Step 1.2 |
