"""
Add implementation details and user manual chapters to thesis.
Preserves all original formatting by cloning existing paragraphs.
"""
import copy
import xml.etree.ElementTree as ET

w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ns1_ns = 'http://schemas.microsoft.com/office/word/2010/wordml'

# Register namespaces (not ns1 which is reserved)
for prefix, uri in [('wps','http://schemas.microsoft.com/office/word/2010/wordprocessingShape'),
    ('wp','http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
    ('wp14','http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing')]:
    try: ET.register_namespace(prefix, uri)
    except: pass

DOC_XML = 'thesis/unpacked/word/document.xml'
tree = ET.parse(DOC_XML)
root = tree.getroot()
body = root.find(f'.//{{{w_ns}}}body')
paras = body.findall(f'.//{{{w_ns}}}p')

def get_text(p):
    texts = []
    for t in p.iter(f'{{{w_ns}}}t'):
        if t.text: texts.append(t.text)
    return ''.join(texts)

def clone_para(p, new_text):
    """Clone a paragraph with same formatting but new text"""
    new_p = copy.deepcopy(p)
    runs = new_p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]:
            new_p.remove(r)
        t_elem = runs[0].find(f'{{{w_ns}}}t')
        if t_elem is not None:
            t_elem.text = new_text
            t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return new_p

def insert_after(ref_para, new_p):
    """Insert new_p after ref_para in body"""
    body_children = list(body)
    idx = body_children.index(ref_para)
    body.insert(idx + 1, new_p)

# Find key anchor paragraphs - search body children directly
body_children = list(body)

def find_para(text_fragment):
    for el in body_children:
        if el.tag == f'{{{w_ns}}}p':
            if text_fragment in get_text(el):
                return el
    return None

def find_para_index(text_fragment):
    for i, el in enumerate(body_children):
        if el.tag == f'{{{w_ns}}}p':
            if text_fragment in get_text(el):
                return i
    return None

# ============================================================
# FIND ANCHOR POINTS
# ============================================================
p_ch6_title = find_para('第6章  实验设计与结果分析')
p_thanks = find_para('致  谢')
p_ch5_title = find_para('第5章  推荐算法设计与实现')

# Use a body paragraph as template for section titles and body text
p_section_template = find_para('5.5.1  数据加载与GPU训练优化')
p_body_template = find_para('ItemCF训练阶段的目标是计算电影之间的相似度')
if p_body_template is None:
    p_body_template = find_para('本文以MovieLens 32M数据集为基础构建推荐系统训练数据')

ch6_idx = find_para_index('第6章  实验设计与结果分析')
thanks_idx = find_para_index('致  谢')
print(f"Ch6 title index: {ch6_idx}")
print(f"致谢 index: {thanks_idx}")
print(f"Section template: {get_text(p_section_template)[:60] if p_section_template else 'NOT FOUND'}")
print(f"Body template: {get_text(p_body_template)[:60] if p_body_template else 'NOT FOUND'}")

# ============================================================
# PART 1: ADD 5.6 核心功能模块实现 (after 5.5.2, before Ch6)
# ============================================================
print("\n=== Adding 5.6 核心功能模块实现 ===")

new_sections_56 = [
    # Section title
    ('5.6  核心功能模块实现', True),
    # 5.6.1
    ('5.6.1  应用工厂与配置管理', True),
    ('系统的入口通过create_app()工厂函数构建Flask应用实例。核心初始化流程如下：首先设置Jinja2环境为ChainableUndefined，允许Vue.js的{{ }}插值表达式与Jinja2模板语法共存，避免未定义变量抛出UndefinedError；然后从Pydantic Settings加载配置项并通过Config类映射为Flask兼容格式；接着依次初始化SQLAlchemy（数据库ORM）、LoginManager（用户认证）和Flask-Caching（SimpleCache内存缓存）三个核心扩展；注册main和admin两个Blueprint蓝图，并挂载全局错误处理器、请求日志中间件和限流中间件；最后在应用上下文中创建所有数据库表，执行种子数据填充（首次启动自动插入20部样本电影和demo用户），并启动后台线程进行TMDB海报补充和NCF模型异步预加载。配置管理方面，系统通过Pydantic BaseSettings实现配置的类型校验与范围验证，包括SECRET_KEY强度校验（生产环境要求≥16字符）、数据库URL驱动校验（支持mysql+pymysql/sqlite/postgresql）、Embedding维度范围校验（1-512）和限流参数校验（1-1000），使用@lru_cache确保配置实例全局单例。', False),
    # 5.6.2
    ('5.6.2  用户认证与权限管理', True),
    ('用户认证基于Flask-Login扩展实现。User模型继承UserMixin，提供is_authenticated、is_active等标准属性。密码采用werkzeug.security.generate_password_hash()进行加盐哈希存储，验证时使用check_password_hash()。注册接口（POST /api/auth/register）进行四重校验：用户名长度2-64字符、密码长度不低于6字符、两次密码输入一致、用户名未被占用，通过后创建用户记录并自动登录。登录接口（POST /api/auth/login）验证成功后调用login_user()创建Session，并更新last_login和login_count字段。关键设计点在于未登录处理：对于/api/前缀的API请求，login_manager.unauthorized_handler返回JSON格式的{"error": "请先登录"}（401状态码）而非HTML重定向，确保前端Vue.js能正确解析认证失败响应。管理员权限通过@admin_required装饰器实现路由级访问控制，该装饰器在decorators.py中定义，检查current_user.is_admin属性，非管理员请求返回403错误。', False),
    # 5.6.3
    ('5.6.3  推荐API核心实现', True),
    ('推荐API（GET /api/recommendations）是系统的核心接口，接受n（推荐数量，默认10，最大50）、strategy（推荐策略，可选itemcf/ncf/hybrid）、recall_k（Hybrid召回数量，默认100，最大500）三个参数。对于冷启动用户（未登录或评分记录为空），系统调用popular_movies()逻辑返回高评分热门电影兜底：查询平均评分较高且评分数量≥50的电影，按评分和热度排序。ItemCF策略的核心在于_itemcf_recall()函数：该函数通过单次IN子句查询批量获取所有已评分电影的相似电影列表（避免经典N+1查询问题），按movie_id分组并每组取Top-50，在分数累加时过滤已评分的电影避免推荐重复内容，最后按贡献分数降序排列取Top-N。_format_recommendations()函数负责将(item_id, score)列表格式化为包含电影详情、推荐分数和推荐理由（because字段，展示贡献最大的3部种子电影）的JSON响应。NCF策略首先检查NCFEngine状态：若is_loading()返回True则返回503状态码提示用户稍后重试；若is_ready()返回False则尝试加载模型；若模型不可用或用户不在训练映射中则自动降级为ItemCF策略。Hybrid策略先以recall_k参数执行ItemCF召回获取候选集，若NCF可用则将候选集送入NCF进行重新评分排序，否则直接截取ItemCF召回结果输出。', False),
    # 5.6.4
    ('5.6.4  推荐解释机制', True),
    ('推荐解释通过/api/recommendations/why/<movie_id>端点实现。该端点接收被推荐电影ID，查询当前用户所有已评分电影中与被推荐电影存在相似度关系的记录。对每部贡献来源电影计算贡献权重（相似度分数×用户原评分），按权重降序排列后返回Top-3作为推荐理由。返回的because字段包含{movie_id, title, weight}三元组，前端据此展示"因为你喜欢《X》，所以推荐《Y》"的解释信息。这种可解释推荐机制是ItemCF算法的天然优势——相似度矩阵提供了透明的"物品A与物品B相似"关系，进而可以回溯推荐结果的来源。在Hybrid策略中，虽然排序阶段由NCF完成，但推荐理由仍沿用ItemCF阶段的相似度贡献信息，实现了"深度学习排序+传统方法解释"的互补。', False),
    # 5.6.5
    ('5.6.5  用户画像服务实现', True),
    ('用户画像计算由ProfileService服务类实现，compute_user_profile()方法整合了12个维度的特征计算：1）偏好类型计算——遍历用户评分和收藏记录，对每部电影的genres字段拆分后进行评分加权统计，归一化后过滤分数低于0.3的类型，保留Top类型偏好；2）偏好年代计算——将电影年份映射为年代标签（如1990s），以相同评分加权方式统计年代偏好并归一化过滤；3）偏好演员计算——从movies表的actors字段（JSON格式存储）中提取演员信息进行评分加权统计，取前10位；4）偏好导演计算——从director字段统计评分加权偏好，取前10位；5）评分行为分析——计算平均评分水平、评分方差（反映评分一致性）和评分熵（反映评分散度，使用香农熵公式）；6）观影统计——累计已评分和已收藏电影的runtime字段获取总观影时长，计算类型多样性指数和年代多样性指数（均基于香农熵）；7）用户分层——根据总操作次数（评分+收藏+评论）将用户分为casual（<10次）、regular（10-49次）、enthusiast（≥50次），活跃度分为low（<20次）、medium（20-99次）、high（≥100次）；8）个性化洞察——基于画像数据自动生成最多5条观影洞察描述（如"您最喜欢Drama类型的电影"、"您的观影类型比较丰富"等），通过get_user_insights()方法返回给前端展示。', False),
    # 5.6.6
    ('5.6.6  行为追踪模块实现', True),
    ('行为追踪模块采用异步非阻塞设计，确保用户操作记录不影响主请求的响应时间。核心实现在behavior_tracker.py中：track_behavior装饰器接收action_type（行为类型：view/rate/search/click）、target_type（目标类型：movie/person/genre/search_query）和target_id参数，在装饰器内部先执行原函数获取结果，再通过record_behavior_async()在独立后台线程中完成数据库写入。record_behavior_async()函数记录以下信息：用户ID、行为类型、目标类型和ID、extra_data（JSON格式，包含请求方法、端点、URL参数等元数据）、IP地址、User-Agent（截取前500字符）、session_id（从Flask session获取或新建UUID）和referrer来源页面。行为记录写入user_behaviors表，该表在created_at字段上建索引支持时间范围查询。系统同时提供get_user_behavior_summary()函数（单用户近N天行为摘要——总行为数、按类型统计、活跃天数、日均行为数）和get_behavior_analytics()函数（全站行为分析——每日行为趋势、热门操作类型Top-10、活跃用户数、热门目标Top-20），为管理员提供运营数据支撑。', False),
    # 5.6.7
    ('5.6.7  数据导入与预处理实现', True),
    ('数据导入通过import_fast.py脚本完成，针对MovieLens 32M数据集的规模特点进行了专门的性能优化。导入流程如下：首先解析movies.csv文件（约87,000部电影），将电影ID、标题、年份和类型（genres以"|"分隔的多值字段）批量写入movies表；然后解析ratings.csv文件（约32,000,000条评分），采用分批提交策略（每10,000条一批）将评分数据写入ratings表，避免单次事务过大导致内存溢出。数据入库后，通过TMDB API进行电影元数据补充：enrich_movies.py脚本遍历数据库中poster_url为空的电影，调用TMDB API v3的/search/movie和/movie/{id}端点获取海报（poster_url）、背景图（backdrop_url）、导演（director）、演员（actors，JSON数组格式）、剧情简介（description）、片长（runtime）、宣传语（tagline）和IMDb ID等元数据信息，以skip_existing模式运行可断点续传。数据过滤在训练脚本中执行：ItemCF训练时过滤评分数量<min_ratings_per_movie（默认50）的冷门电影和评分数量<min_ratings_per_user（默认5）的不活跃用户；NCF训练时过滤评分数量<min_ratings_per_user（默认10）的用户，并通过user_mod参数支持按用户ID取模采样控制训练规模。', False),
]

# Insert all 5.6 paragraphs before Ch6 title
insertion_point = ch6_idx
for text, is_title in reversed(new_sections_56):
    new_p = clone_para(p_body_template if not is_title else p_section_template, text)
    body.insert(insertion_point, new_p)

print("5.6 added successfully")

# ============================================================
# PART 2: ADD 5.7 前端核心实现 (also before Ch6)
# ============================================================
print("\n=== Adding 5.7 前端核心实现 ===")

new_sections_57 = [
    ('5.7  前端核心实现', True),
    ('5.7.1  推荐页面实现', True),
    ('推荐页面（recommendations.html）是系统的核心前端页面，通过Vue.js 3的Options API管理页面状态。页面的核心交互逻辑在page-recommendations.js中实现，关键功能包括：1）策略切换——通过三个Tab按钮（ItemCF/NCF/Hybrid）切换推荐策略，监听Tab点击事件后更新strategy变量并调用loadRecommendations()重新请求数据；2）推荐展示——使用CSS Grid网格布局（grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))）展示推荐电影卡片，每张卡片显示poster_url海报图（带懒加载和fallback占位图）、title标题、year年份、genres类型标签、avg_rating平均评分（星级组件渲染）和推荐分数；3）推荐理由——在ItemCF和Hybrid模式下，卡片下方展示"因为你喜欢X"的推荐来源信息，通过because数组渲染为小型电影缩略图+标题链接；4）评分交互——用户可直接在推荐卡片上通过StarRating组件进行星级评分（0.5-5.0，步长0.5），评分后通过api.js的post方法调用/api/ratings接口提交数据并立即更新本地评分状态；5）反馈机制——每张卡片提供喜欢/不喜欢按钮，点击后调用/api/feedback接口提交反馈，按钮状态通过CSS类切换（.feedback-active）给予视觉反馈。推荐列表加载时展示SkeletonGrid骨架屏组件（4列×2行动画占位），加载完成后过渡到实际内容。', False),
    ('5.7.2  数据看板实现', True),
    ('增强看板页面（enhanced_dashboard.html）集成多个ECharts 5.4图表，通过page-enhanced-dashboard.js管理图表实例和响应式更新。系统概览区展示四个核心指标卡片：总用户数、总电影数、总评分数、活跃用户数，数值采用countUp动画效果从0递增至实际值。评分分布图使用ECharts柱状图（bar类型），X轴为0.5-5.0共10个评分档位，Y轴为各评分值的出现次数，柱状图颜色使用渐变色（从#f59e0b到#fbbf24）。类型分布图使用ECharts环形图（pie类型，radius: [\'40%\', \'70%\']），按genres拆分统计各类型的评分数量占比，展示Top-10类型并将剩余归入"其他"。年份趋势图使用ECharts混合图：柱状图（评分数量）与折线图（平均评分）双Y轴叠加，X轴为年份，左Y轴为评分数量（柱状图），右Y轴为平均评分（折线图，平滑曲线）。用户分群图使用ECharts旭日图（sunburst类型）展示用户类型的层次结构：第一层为用户类型（casual/regular/enthusiast），第二层为活跃度（low/medium/high），通过data数组的children属性构建层次。活动热力图使用ECharts日历热力图（calendar类型+heatmap系列），X轴为日期，Y轴为周几，颜色深浅反映当日活跃用户数量。所有图表在窗口resize时自动调用chart.resize()适配新尺寸，图表数据通过api.js异步获取并支持定时刷新（30秒间隔）。', False),
    ('5.7.3  公共API模块实现', True),
    ('api.js模块封装了所有前端API请求逻辑，提供统一的请求处理层。模块核心为api(path, options)函数：支持GET/POST/PUT/DELETE四种HTTP方法，自动在请求头中添加X-CSRFToken（从cookie中读取csrf_token）和Content-Type: application/json。GET请求实现自动去重：维护一个pendingRequests的Map对象，以请求URL为键存储Promise引用，当多个组件同时请求同一URL时共享同一个Promise，避免重复网络请求。非200响应自动解析错误信息：优先尝试解析JSON格式的error字段，其次检查是否为HTML重定向（401/403/404/5xx状态码），最后回退到HTTP状态文本。请求超时通过AbortController设置为30秒。推荐相关的API调用均通过此模块进行，包括getRecommendations(params)——调用/api/recommendations、submitRating(movieId, rating)——调用/api/ratings、submitFeedback(movieId, feedback, context)——调用/api/feedback等。模块还导出了便捷方法api.get(path, params)和api.post(path, data)供各个页面的page-*.js文件使用。', False),
    ('5.7.4  Vue组件系统', True),
    ('系统通过vue-components.js定义了可复用的Vue.js 3组件，统一挂载在window.CinemaComponents命名空间下。核心组件包括：MovieCard——电影卡片组件，props接收movie对象（id/title/year/genres/poster_url/avg_rating），模板使用Bootstrap 5卡片样式，支持hover浮起动画和点击跳转详情页；SkeletonGrid——骨架屏组件，props接收cols和rows控制网格尺寸，通过CSS动画（shimmer效果）展示加载占位；StarRating——星级评分组件，props接收value（当前评分）和readonly（是否只读），支持0.5分步长的精确评分，鼠标hover时高亮到当前星级的填充色，点击时触发@update事件；MovieSearch——电影搜索组件，支持防抖输入（300ms延迟），通过/api/search/suggestions获取搜索建议下拉列表；RecommendationCard——推荐卡片组件，扩展MovieCard增加了推荐分数显示、推荐理由（because列表）和反馈按钮（like/dislike）。各页面通过解构赋值使用组件：const { MovieCard, SkeletonGrid, StarRating } = window.CinemaComponents；然后在Vue实例的components选项中注册。这种CDN组件模式避免了Webpack/Vite等构建工具链的复杂性，适合中小型项目快速开发。', False),
]

# Insert 5.7 before Ch6 (which has moved forward due to 5.6 inserts)
insertion_point = find_para_index('第6章  实验设计与结果分析')
for text, is_title in reversed(new_sections_57):
    new_p = clone_para(p_body_template if not is_title else p_section_template, text)
    body.insert(insertion_point, new_p)

print("5.7 added successfully")

# ============================================================
# PART 3: ADD Chapter 8 系统使用指南 (after 7.2, before 致谢)
# ============================================================
print("\n=== Adding 第8章 系统使用指南 ===")

# Find insertion point: before 致谢
insertion_point = find_para_index('致  谢')

new_ch8 = [
    # Chapter title
    ('第8章  系统使用指南', True),
    # 8.1
    ('8.1  普通用户使用指南', True),
    ('8.1.1  注册与登录', True),
    ('用户首次使用系统需进行注册。在登录页面点击"注册"链接进入注册页面，输入用户名（2-64字符）、密码（不低于6字符）和确认密码，提交后系统自动完成注册并跳转至系统首页。已注册用户在登录页面输入用户名和密码，点击"登录"按钮即可进入系统。系统使用Session机制维护登录状态，浏览器关闭后Session自动失效，下次访问需重新登录。用户可通过导航栏右上角的用户菜单查看个人信息（用户名、注册时间、登录次数等）和退出登录。', False),
    ('8.1.2  浏览与搜索电影', True),
    ('登录后进入系统首页（/app），页面展示推荐电影列表和热门电影区。用户可通过以下方式发现电影：1）顶部搜索栏——输入电影标题关键词，系统实时展示匹配结果列表，点击搜索结果进入电影详情页；2）高级搜索（/advanced-search）——支持按电影标题、类型（多选下拉框）、年份范围、最低评分等多维度组合筛选，搜索结果可按评分、热门程度、上映年份排序；3）电影详情页——展示电影完整信息，包括海报、标题、年份、类型、导演、演员阵容、剧情简介、片长、平均评分和评分人数，页面下方展示相似电影推荐列表。', False),
    ('8.1.3  个性化推荐', True),
    ('推荐页面（/recommendations）是系统的核心功能页面。页面顶部提供三个策略切换Tab：ItemCF（默认，基于物品协同过滤，推荐结果附带"因为你喜欢X"的解释）、NCF（神经协同过滤，基于深度学习模型）、Hybrid（混合推荐，ItemCF召回+NCF排序）。每个推荐结果展示为电影海报卡片，包含标题、年份、类型标签、平均评分、推荐分数和推荐理由（在ItemCF/Hybrid模式下）。用户可直接在推荐卡片上进行星级评分（0.5-5.0），评分提交后即刻更新卡片状态。每张卡片下方提供"喜欢"和"不喜欢"按钮，用户可通过反馈帮助系统优化推荐效果。推荐数量默认为10部，可通过URL参数n调整（最大50）。', False),
    ('8.1.4  评分与收藏', True),
    ('评分功能：用户可以通过以下途径对电影进行评分——在推荐卡片上直接评分、在电影详情页评分、在"我的评分"页面管理评分历史。评分范围为0.5至5.0分，步长为0.5分，点击星级图标选择评分值后自动提交。已评分的电影可在"我的评分"页面（/ratings）查看完整列表，按评分时间倒序排列，支持评分更新（再次点击新的星级评分覆盖旧值）。收藏功能：在电影详情页可将电影添加到收藏夹，支持三种收藏类型——喜欢（favorite）、待看（watchlist）、已看（seen）。同一电影可加入不同类型的收藏。用户可在"我的收藏"页面（/collections）查看和管理所有收藏记录，支持按类型筛选和删除操作。', False),
    ('8.1.5  评论与影单', True),
    ('评论功能：在电影详情页可发表文字评论并可附带评分。评论发表后展示在电影详情页下方评论列表，其他用户可对评论进行点赞。用户可在"我的评论"页面查看和管理自己发表的评论。影单功能：用户可创建自定义影单（/movie-lists/create），设置影单名称、描述、封面图和公开/私有模式。创建后可从电影详情页将电影添加到影单中，支持拖拽排序和添加备注。公开影单可被其他用户浏览、点赞和评论；私有影单仅创建者可见。用户可在"影单广场"（/movie-lists）浏览所有公开影单，按热门程度或创建时间排序。', False),
    ('8.1.6  用户画像与行为分析', True),
    ('用户画像页面（/user/insights）基于用户的评分、收藏和评论历史自动生成个性化分析。页面展示以下内容：1）类型偏好雷达图——展示用户评分最高的电影类型分布；2）年代偏好——展示用户偏好的电影年代区间；3）评分行为统计——平均评分、评分方差、评分次数、评分时间线（按月聚合的评分数量和平均评分趋势图）；4）观影洞察——自动生成的多条个性化描述，如"您最喜欢Drama类型的电影"、"您的观影类型比较丰富"或"您的评分风格比较宽容"等；5）用户分层——展示用户类型（轻度/中度/重度用户）和活跃度等级。用户画像数据可通过"刷新画像"按钮手动触发重新计算，以确保数据反映最新的用户行为。', False),
    # 8.2
    ('8.2  管理员使用指南', True),
    ('8.2.1  管理后台入口与概览', True),
    ('管理员通过导航栏"管理后台"链接进入管理界面（/admin）。管理后台首页为仪表盘（Dashboard），展示系统核心运行指标：总用户数（含增长趋势）、总电影数、总评分数、活跃用户数（近7天/30天）、待审核评论数、待审核观看链接数等。管理员可通过左侧导航菜单快速切换至各管理模块。普通用户账户不具备管理员权限，无法访问/admin路径下的任何页面（后端通过@admin_required装饰器进行权限拦截）。', False),
    ('8.2.2  电影管理', True),
    ('电影管理页面（/admin/movies）提供电影列表的分页浏览，支持按标题搜索、按状态筛选（active/inactive/pending）和按类型过滤。管理员可执行以下操作：1）添加电影——手动输入电影基本信息（标题、年份、类型、简介等），或通过TMDB ID自动获取元数据填充；2）编辑电影——修改电影的标题、类型、简介、海报URL、观看链接等字段，支持更新演员列表（JSON格式）和导演信息；3）状态管理——将电影标记为active（正常显示）、inactive（隐藏）或pending（待审核）；4）精选管理——将电影设为精选（is_featured），精选电影将在首页醒目位置展示；5）元数据管理——通过/metadata-management页面批量更新电影元数据（如批量设置TMDB ID、批量获取海报等）。', False),
    ('8.2.3  用户管理', True),
    ('用户管理页面（/admin/users）展示用户列表，支持按用户名搜索和按注册时间排序。管理员可执行以下操作：1）权限管理——将普通用户提升为管理员（授予is_admin权限）或撤销管理员权限；2）账户管理——启用或禁用用户账户（is_active状态），禁用后用户无法登录；3）用户详情查看——查看用户的注册时间、最后登录时间、登录次数、评分数量等统计信息。管理员不能修改用户的密码（密码仅用户本人可通过"忘记密码"流程重置）。', False),
    ('8.2.4  评论与内容审核', True),
    ('评论管理页面（/admin/reviews）展示所有用户评论，支持按状态筛选（approved/rejected/pending）。管理员可：1）审核评论——将评论状态设为"通过"（正常显示）、"拒绝"（隐藏）或"待审核"；2）精选评论——将高质量评论标记为精选（is_featured），在电影详情页优先展示；3）删除评论——删除违规或垃圾评论。观看链接管理页面（/admin/watch-links）支持审核用户提交的电影观看链接（平台、URL、画质、是否免费/官方），设置状态为active（正常）/pending（待审核）/inactive（停用）/reported（被举报）。', False),
    ('8.2.5  通知管理与数据导出', True),
    ('通知管理页面（/admin/notification-management）允许管理员向指定用户或全体用户发送系统通知，设置通知类型（system/review_reply/review_liked/movie_recommend/achievement）和标题内容。通知发送后，目标用户将在登录后通过顶部通知铃铛图标收到实时提醒。数据导出页面（/admin/data-export）支持以下导出功能：1）用户数据导出——导出指定用户的评分历史、收藏记录和评论数据（JSON/CSV格式）；2）系统统计导出——导出系统核心指标的快照数据，包括用户增长趋势、评分分布、类型统计等；3）电影数据导出——导出电影信息数据库的完整或筛选子集；4）完整备份——导出系统的完整数据快照，用于数据迁移或存档。', False),
    ('8.2.6  通知偏好与权限管理', True),
    ('通知偏好设置页面（/admin/notification-management）允许管理员配置系统的通知策略，包括各类通知的默认开关状态。权限管理页面（/admin/permission-management）展示所有用户的权限状态列表，管理员可按用户名筛选，查看用户是否为管理员及其账户激活状态，并通过切换按钮快速调整用户的管理权限和激活状态。此外，管理后台还提供日志查看功能（/admin/logs），展示系统运行日志，支持按日志级别（DEBUG/INFO/WARNING/ERROR）和时间范围筛选，便于排查系统问题和审计操作记录。', False),
]

for text, is_title in reversed(new_ch8):
    new_p = clone_para(p_body_template if not is_title else p_section_template, text)
    body.insert(insertion_point, new_p)

print("Chapter 8 added successfully")

# ============================================================
# PART 4: Update TOC entries (in the TOC section, around P[28-128])
# ============================================================
print("\n=== Updating TOC ===")
# Find the TOC section - it's between "目录" and before the main text
# Add new entries for 5.6, 5.7, and 第8章
# Find the "第7章  总结与展望" TOC entry
toc_ch7 = None
for p in paras:
    text = get_text(p).strip()
    if '第7章' in text and '总结与展望' in text and len(text) < 60:
        toc_ch7 = p
        break

if toc_ch7:
    toc_ch6_idx = find_para_index('第6章  实验设计')
    toc_thanks_idx = find_para_index('致  谢')

    # Add 5.6, 5.7 TOC entries before 第6章 TOC entry
    if toc_ch6_idx:
        new_toc_entries = [
            '5.6  核心功能模块实现29',
            '5.7  前端核心实现31',
        ]
        for entry in reversed(new_toc_entries):
            new_p = clone_para(toc_ch7, entry)
            body.insert(toc_ch6_idx, new_p)

    # Add Chapter 8 TOC entries before 致谢 TOC entry
    if toc_thanks_idx:
        toc_thanks_idx = find_para_index('致  谢')  # re-find after inserts
        new_ch8_toc = [
            '第8章  系统使用指南42',
            '8.1  普通用户使用指南42',
            '8.2  管理员使用指南45',
        ]
        for entry in reversed(new_ch8_toc):
            new_p = clone_para(toc_ch7, entry)
            body.insert(toc_thanks_idx, new_p)

print("TOC updated successfully")

# ============================================================
# PART 5: Update Ch1 thesis structure overview (P[176-178])
# ============================================================
print("\n=== Updating Ch1 structure overview ===")
p_ch5_desc = find_para('第5章为推荐算法设计与实现，详细描述数据预处理')
p_ch7_desc = find_para('第7章对全文工作进行总结，分析系统不足并展望未来改进方向')

if p_ch5_desc:
    new_ch5_desc = ('第5章为推荐算法与系统实现，详细描述数据预处理、ItemCF召回模型、NCF重排模型、'
                    '混合推荐策略的实现过程，并且详细阐述核心功能模块的实现细节（包括应用工厂、用户认证、'
                    '推荐API、推荐解释、用户画像、行为追踪、数据预处理）以及前端核心实现（推荐页面、数据看板、API模块和Vue组件系统），'
                    '并给出关键工程优化方法。')
    runs = p_ch5_desc.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]:
            p_ch5_desc.remove(r)
        t = runs[0].find(f'{{{w_ns}}}t')
        if t is not None:
            t.text = new_ch5_desc

if p_ch7_desc:
    new_ch7_desc = ('第7章对全文工作进行总结，分析系统不足并展望未来改进方向。'
                    '第8章为系统使用指南，分别从普通用户和管理员两个角度介绍系统的使用方法。')
    runs = p_ch7_desc.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]:
            p_ch7_desc.remove(r)
        t = runs[0].find(f'{{{w_ns}}}t')
        if t is not None:
            t.text = new_ch7_desc

# Also update the catalog entry descriptions
# Find "第7章" and "致谢" in TOC to add page number adjustments
print("Ch1 structure overview updated")

# ============================================================
# SAVE
# ============================================================
print("\n=== Saving ===")
# Fix potential namespace issues
tree.write(DOC_XML, encoding='utf-8', xml_declaration=True)
print("Saved! All chapters added successfully.")
