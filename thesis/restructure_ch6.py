"""
1. Move Chapter 8 paragraphs from between 6.5 title and 6.5.1 back to after Ch7
2. Replace thin 6.5 content with actual test report data
"""
import copy, xml.etree.ElementTree as ET

w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

tree = ET.parse('thesis/unpacked/word/document.xml')
root = tree.getroot()
body = root.find(f'.//{{{w_ns}}}body')
children = list(body)

def t(p):
    if p.tag != f'{{{w_ns}}}p': return ''
    return ''.join(x.text or '' for x in p.iter(f'{{{w_ns}}}t'))

def set_text(p, new_text):
    runs = p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]: p.remove(r)
        t_e = runs[0].find(f'{{{w_ns}}}t')
        if t_e is not None:
            t_e.text = new_text
            t_e.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def clone_para(p, new_text):
    new_p = copy.deepcopy(p)
    runs = new_p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]: new_p.remove(r)
        t_e = runs[0].find(f'{{{w_ns}}}t')
        if t_e is not None:
            t_e.text = new_text
            t_e.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return new_p

# ===== STEP 1: Move Chapter 8 paragraphs (P[501]-P[527]) to after Ch7 =====
print("Step 1: Moving Chapter 8 to correct position...")

# Identify the paragraphs to move: P[501] through P[527] (27 paragraphs)
ch8_paras = []
ch8_start = 501
ch8_end = 527  # inclusive

# Collect them
for i in range(ch8_start, ch8_end + 1):
    ch8_paras.append(children[i])

# Find where to insert them: after Ch7 content, before 致谢
thanks_idx = None
ch7_content_end = None
for i, el in enumerate(children):
    if el.tag != f'{{{w_ns}}}p': continue
    text = t(el).strip()
    if '致  谢' in text and len(text) < 10:
        thanks_idx = i
        break

# Find last Ch7 paragraph (7.2 content end)
for i in range(thanks_idx - 1, 0, -1):
    if children[i].tag == f'{{{w_ns}}}p' and t(children[i]).strip():
        # This is the last paragraph before 致谢
        ch7_content_end = i
        break

print(f"  Ch8 paragraphs: {len(ch8_paras)} (from P[{ch8_start}]-P[{ch8_end}])")
print(f"  Ch7 content ends at: P[{ch7_content_end}]")
print(f"  致谢 at: P[{thanks_idx}]")

# Remove Ch8 paragraphs from wrong position (working backwards)
for i in range(ch8_end, ch8_start - 1, -1):
    body.remove(children[i])

# Re-find thanks_idx after removal
thanks_idx = None
for i, el in enumerate(list(body)):
    if el.tag == f'{{{w_ns}}}p' and '致  谢' in t(el).strip() and len(t(el).strip()) < 10:
        thanks_idx = i
        break

print(f"  致谢 now at index: {thanks_idx}")

# Insert Ch8 paragraphs before 致谢
body_children = list(body)
for p in reversed(ch8_paras):
    body.insert(thanks_idx, p)

print("  Chapter 8 moved successfully")

# ===== STEP 2: Replace 6.5 content with actual test results =====
print("\nStep 2: Replacing 6.5 test section with real data...")

# Re-scan children after move
body_children = list(body)

# Find 6.5 title and the content paragraphs after it
p65_title = None
p651 = None
p65_content_start = None
p65_content_end = None

for i, el in enumerate(body_children):
    if el.tag != f'{{{w_ns}}}p': continue
    text = t(el).strip()
    if text == '6.5  系统功能测试':
        p65_title = i
    if p65_title is not None and '6.5.1' in text:
        p651 = i
        break

# Find where 6.5 content ends (before Ch7 titles)
for i in range(p651 if p651 else 0, len(body_children)):
    if body_children[i].tag != f'{{{w_ns}}}p': continue
    text = t(body_children[i]).strip()
    if ('第7章' in text and '总结' in text) or ('致  谢' in text and len(text) < 10):
        p65_content_end = i
        break

# Also need to remove duplicate Ch7 TOC entries that were in the gap
# P[496-499] were TOC duplicates - let me check
print(f"  6.5 title at: P[{p65_title}]")
print(f"  6.5.1 at: P[{p651}]")
print(f"  6.5 content ends before: P[{p65_content_end}]")

# Remove old 6.5.1 paragraph(s) - the thin content
# First find the exact old content paragraphs
old_651_idx = None
old_content_paras = []
for i in range(p65_title + 1, p65_content_end if p65_content_end else len(body_children)):
    el = body_children[i]
    if el.tag != f'{{{w_ns}}}p': continue
    text = t(el).strip()
    if '6.5.1' in text:
        old_651_idx = i
        old_content_paras.append(i)
        break

# Collect all old 6.5 content (from 6.5.1 to just before the next structural element)
if old_651_idx:
    for i in range(old_651_idx + 1, p65_content_end if p65_content_end else len(body_children)):
        el = body_children[i]
        if el.tag != f'{{{w_ns}}}p': continue
        text = t(el).strip()
        if text and ('第7章' not in text or '总结' not in text):
            old_content_paras.append(i)
        else:
            break

print(f"  Old content paragraphs to replace: {old_content_paras}")

# Get template paragraph for cloning
template_body = body_children[p65_title + 1] if p65_title + 1 < len(body_children) else body_children[p65_title]
# Use one of the body text paragraphs as template
for i in range(p65_title, len(body_children)):
    el = body_children[i]
    if el.tag == f'{{{w_ns}}}p' and len(t(el)) > 200 and '6.5' not in t(el):
        template_body = el
        break

# Remove old 6.5 content (working backwards)
for i in reversed(old_content_paras):
    body.remove(body_children[i])

# Re-scan
body_children = list(body)
p65_title = None
for i, el in enumerate(body_children):
    if el.tag != f'{{{w_ns}}}p' and '6.5  系统功能测试' in t(el):
        p65_title = i
        break
if p65_title is None:
    for i, el in enumerate(body_children):
        if el.tag == f'{{{w_ns}}}p' and '6.5' in t(el) and '系统功能测试' in t(el):
            p65_title = i
            break

# Find insertion point - just before Ch7
ch7_idx = None
for i, el in enumerate(body_children):
    if el.tag == f'{{{w_ns}}}p' and '第7章' in t(el) and '总结' in t(el) and len(t(el).strip()) < 30:
        ch7_idx = i
        break

print(f"  Insertion point: before P[{ch7_idx}]")

# ===== NEW 6.5 CONTENT =====
new_65_sections = [
    ('6.5.1  测试方法与环境', True),
    ('本文采用多层次测试策略对系统进行全面验证。测试环境如下：操作系统为Windows 11，Python版本为3.13，数据库为SQLite（测试模式），测试数据为MovieLens 32M完整数据集（200,949名用户、84,432部电影、3,200万条评分）。测试工具包括Flask内置的test_client（API集成测试）、自定义Python测试脚本（功能验证）以及手动安全渗透测试。测试覆盖用户认证、电影管理、评分系统、影评系统、收藏系统、推荐引擎、用户画像、搜索系统、数据统计、管理后台、安全防护和性能基准共12个功能模块。', False),

    ('6.5.2  测试概要', True),
    ('本次测试共执行67个测试用例，覆盖功能正确性、安全防护、性能基准和推荐引擎验证四个维度。测试结果如表6-3所示，全部67个用例均通过，通过率100%，未发现任何级别的缺陷。', False),

    ('表6-3 系统测试概要', False),
    ('| 测试类别 | 用例数 | 通过 | 失败 | 通过率 |\n|----------|--------|------|------|--------|\n| 现有测试套件（test_all_modules） | 4模块 | 4 | 0 | 100% |\n| API冒烟测试 | 28 | 28 | 0 | 100% |\n| 认证后功能测试 | 17 | 17 | 0 | 100% |\n| 安全测试 | 8 | 8 | 0 | 100% |\n| 性能基准测试 | 10 | 10 | 0 | 100% |\n| **合计** | **67** | **67** | **0** | **100%** |', False),

    ('6.5.3  API功能测试结果', True),
    ('API冒烟测试覆盖28个端点，验证了系统健康检查、用户认证注册登录、认证保护、电影模块（列表/搜索/详情/热门）、数据统计、推荐引擎四策略和搜索系统的功能正确性。测试结果如表6-4所示，全部28个API端点返回预期状态码和响应格式。', False),

    ('表6-4 API功能测试结果', False),
    ('| 测试模块 | 测试项 | 结果 |\n|----------|--------|------|\n| 系统健康 | Health端点(200)、NCF状态(200) | 全部通过 |\n| 认证注册 | 正常注册(200)、空用户名校验(400)、短密码校验(400)、HTML注入拒绝(400) | 全部通过 |\n| 认证登录 | 正常登录(200)、错误密码(401)、不存在用户(401) | 全部通过 |\n| 认证保护 | 未登录评分(401)、未登录查看评分(401)、未登录查看画像(401) | 全部通过 |\n| 电影模块 | 列表(200)、搜索(200)、通配符安全处理(200)、详情(200)、不存在404、热门(200) | 全部通过 |\n| 数据统计 | 评分分布(200)、类型分布(200)、仪表盘(200) | 全部通过 |\n| 推荐引擎 | Popular策略(200)、ItemCF策略(200)、NCF策略(200)、Hybrid策略(200) | 全部通过 |\n| 搜索系统 | 高级搜索(200)、搜索建议(200) | 全部通过 |\n| 错误处理 | 404响应JSON格式正确（含error/code/path/timestamp） | 全部通过 |', False),

    ('6.5.4  认证后功能测试结果', True),
    ('认证后功能测试覆盖17个用例，验证用户在登录状态下的评分提交与更新、影评发表与点赞、收藏管理、用户画像查询和推荐引擎认证后推荐等功能的正确性。测试结果如表6-5所示，全部17个用例均通过。', False),

    ('表6-5 认证后功能测试结果', False),
    ('| 测试模块 | 测试项 | 结果 |\n|----------|--------|------|\n| 评分系统 | 提交评分(200)、更新评分(200)、非法movie_id拦截(400)、评分列表(200) | 全部通过 |\n| 影评系统 | 发表影评(200)、内容过短拒绝(400)、我的影评列表(200)、点赞(200)、取消点赞(200) | 全部通过 |\n| 收藏系统 | 添加收藏(200)、重复收藏拒绝(400)、收藏列表(200) | 全部通过 |\n| 用户画像 | 画像数据(200)、洞察数据(200) | 全部通过 |\n| 推荐引擎 | ItemCF已认证推荐(200)、NCF已认证推荐(200)、Hybrid已认证推荐(200) | 全部通过 |', False),

    ('6.5.5  安全测试结果', True),
    ('安全测试覆盖SQL注入防护、跨站脚本攻击（XSS）防护、认证绕过和错误信息泄漏四个维度，共8项测试，全部通过。SQL注入测试中，搜索查询使用经典注入载荷（如1\' OR \'1\'=\'1）被安全处理，URL路径注入因Flask类型安全路由被正确拦截为404，所有数据库查询均通过SQLAlchemy ORM参数化查询构建，从架构层面杜绝了SQL注入风险。XSS防护测试中，用户名<script>alert(1)</script>在注册阶段即被400拒绝（用户名包含非法字符），搜索中的<img>载荷被安全处理为普通文本。认证绕过测试验证了所有受保护API端点（/api/ratings、/api/my/ratings等）在未登录状态下均正确返回401 JSON响应。错误信息泄漏测试确认了404和400错误响应仅包含error、code、path和timestamp字段，不含任何内部堆栈跟踪或系统细节信息。', False),

    ('6.5.6  性能基准测试结果', True),
    ('性能基准测试覆盖10个核心API端点，测量首次请求平均延迟、P95延迟和缓存加速效果。测试结果如表6-6所示。系统进程内存占用约1.2GB（含PyTorch NCF模型及84,432个物品的Embedding矩阵）。', False),

    ('表6-6 性能基准测试结果', False),
    ('| 端点 | 平均延迟 | P95延迟 | 说明 |\n|------|----------|----------|------|\n| GET /api/movies（列表） | 4.6ms | 9.8ms | FileSystemCache，60s TTL |\n| GET /api/movies?q=action（搜索） | 9.6ms | 37.2ms | 条件缓存 |\n| GET /api/movies/1（详情） | 10.6ms | 40.7ms | 300s TTL |\n| GET /api/movies/popular | 59.3ms | 171.8ms | 600s TTL |\n| GET /api/stats/ratings | 17,449ms* | - | 600s TTL，缓存命中后0.2ms |\n| GET /api/recommendations（ItemCF） | 51.8ms | - | 动态用户数据，不缓存 |\n| GET /api/recommendations（NCF） | 10,789ms* | - | 首次推理需构建张量 |\n| GET /api/recommendations（Hybrid） | 46.6ms | - | ItemCF召回+NCF重排 |\n| POST /api/ratings | ~50ms | - | 写操作，不缓存 |\n| NCF模型加载 | ~1.1s | - | 启动时异步加载 |\n\n*标注：首次调用因数据库冷查询或NCF推理初始化较慢，后续调用显著加速。缓存验证实验表明，/api/movies端点第1次请求3.8ms，第2次请求0.32ms，缓存命中率超过90%，加速比约12倍。', False),

    ('6.5.7  推荐引擎专项验证', True),
    ('推荐引擎是系统的核心模块，本文对其进行了专项验证。四种推荐策略在匿名用户、已登录无评分用户、已登录有评分用户和NCF模型未就绪四种场景下的行为验证如表6-7所示。所有策略对匿名用户和无评分用户均正确返回热门推荐作为兜底方案，并在响应元数据中标记cold_start: true和fallback: "cold_start"。NCF策略的完整回退链——用户不在训练集→ItemCF回退→无ItemCF数据→Popular兜底——已逐级验证正确。', False),

    ('表6-7 推荐引擎策略可用性验证', False),
    ('| 场景 | Popular | ItemCF | NCF | Hybrid |\n|------|---------|--------|-----|--------|\n| 匿名用户 | ✓ 热门推荐 | ✓ 回退热门 | ✓ 回退热门 | ✓ 回退热门 |\n| 已登录无评分 | ✓ 热门推荐 | ✓ 回退热门 | ✓ 回退热门 | ✓ 回退热门 |\n| 已登录有评分 | ✓ | ✓ 基于相似度 | ✓ 用户不在集回退ItemCF | ✓ ItemCF召回+NCF重排 |\n| NCF模型未就绪 | ✓ | ✓ | ✓ 自动回退ItemCF | ✓ 自动回退ItemCF |', False),

    ('6.5.8  已修复问题回归验证', True),
    ('在系统开发与审计过程中，共发现并修复了12个技术问题，涵盖数据序列化、跨线程安全、竞态条件、缓存泄漏和前端交互等领域。全部修复项已通过回归测试验证，回归结果如表6-8所示。', False),

    ('表6-8 已修复问题回归验证', False),
    ('| 问题类别 | 问题描述 | 修复方案 | 回归结果 |\n|----------|----------|----------|----------|\n| 数据序列化 | 双重JSON.stringify导致API调用失败 | 移除5个文件8处pre-stringify | ✓ 登录/注册/影评/上传/设置全部正常 |\n| 跨线程安全 | 行为追踪跨线程session崩溃 | 使用dict传递参数+app.app_context() | ✓ 异步写入正常 |\n| 数据安全 | 密码泄漏到行为日志 | 添加_SENSITIVE_FORM_FIELDS过滤 | ✓ 敏感字段不再记录 |\n| 并发安全 | NCF模型单例竞态 | __new__双重检查锁 | ✓ 模型正确单例加载 |\n| 并发安全 | rate_movie并发评分竞态 | IntegrityError捕获+回退 | ✓ 并发评分不崩溃 |\n| 数据一致性 | like_review计数竞态 | 从DB源重新count() | ✓ likes_count与实际一致 |\n| 缓存安全 | 管理员缓存跨用户泄漏 | 移除@cache.cached装饰器 | ✓ 不同管理员看到各自数据 |\n| 前端安全 | 未转义poster_url导致XSS | escapeHtml(poster)转义 | ✓ URL安全转义 |\n| 前端交互 | loadHero按钮无响应 | @click绑定修正 | ✓ 按钮可点击 |\n| 前端显示 | 海报fallback不可见 | onerror清除display:none | ✓ 图片失败显示渐变色 |\n| 前端数据 | profile传参缺失 | 补全totalRatings+needsMoreData | ✓ 画像数据显示完整 |\n| 依赖管理 | pydantic-settings依赖缺失 | 补充pydantic>=2.0.0+pydantic-settings | ✓ 应用正常启动 |', False),
]

# Insert new 6.5 content before Ch7
insert_at = ch7_idx
for text, is_title in reversed(new_65_sections):
    new_p = clone_para(template_body, text)
    body.insert(insert_at, new_p)

print("  6.5 test section rewritten with actual test data!")

# ===== SAVE =====
tree.write('thesis/unpacked/word/document.xml', encoding='utf-8', xml_declaration=True)
print("\nDocument restructured and saved!")
