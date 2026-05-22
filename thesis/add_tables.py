"""
Add text-based tables to thesis. All tables use structured text format
with proper caption formatting per university requirements.
"""
import copy, xml.etree.ElementTree as ET

w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

tree = ET.parse('thesis/unpacked_new/word/document.xml')
root = tree.getroot()
body = root.find(f'.//{{{w_ns}}}body')
children = list(body)

def t(p):
    if p.tag != f'{{{w_ns}}}p': return ''
    return ''.join(x.text or '' for x in p.iter(f'{{{w_ns}}}t'))

def clone_para(p, new_text, center=False):
    """Clone paragraph, optionally center-align"""
    new_p = copy.deepcopy(p)
    runs = new_p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]: new_p.remove(r)
        te = runs[0].find(f'{{{w_ns}}}t')
        if te is not None:
            te.text = new_text
            te.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        # Center alignment for captions
        if center:
            pPr = new_p.find(f'{{{w_ns}}}pPr')
            if pPr is None:
                pPr = ET.SubElement(new_p, f'{{{w_ns}}}pPr')
            # Remove existing jc
            for jc in pPr.findall(f'{{{w_ns}}}jc'):
                pPr.remove(jc)
            jc = ET.SubElement(pPr, f'{{{w_ns}}}jc')
            jc.set(f'{{{w_ns}}}val', 'center')
            # Remove first-line indent
            for ind in pPr.findall(f'{{{w_ns}}}ind'):
                pPr.remove(ind)
    return new_p

def find_idx(text_fragment):
    for i, el in enumerate(children):
        if el.tag == f'{{{w_ns}}}p' and text_fragment in t(el):
            return i
    return None

def insert_many(ref_idx, items):
    """Insert items in order at ref_idx (each item is (text, is_caption))"""
    for text, is_caption in reversed(items):
        new_p = clone_para(children[ref_idx], text, center=is_caption)
        body.insert(ref_idx, new_p)

# Get template for body paragraphs
body_template = None
for el in children:
    if el.tag == f'{{{w_ns}}}p' and len(t(el)) > 100 and '第' not in t(el):
        body_template = el
        break

# =====================================================
# TABLE 2-1: MovieLens 32M Dataset Statistics
# Insert between end of 2.1.1 and start of 2.1.2
# =====================================================
print("Adding 表2-1...")
idx_212 = find_idx('2.1.2  显式反馈与隐式反馈建模')
if idx_212:
    table_2_1 = [
        (None, None),  # spacer
        ('表2-1 MovieLens 32M数据集统计信息', True),
        ('| 统计项 | 数值 | 说明 |\n'
         '|--------|------|------|\n'
         '| 评分记录总数 | 32,000,000 条 | 显式评分数据 |\n'
         '| 用户总数 | 270,000 人 | 匿名化用户标识 |\n'
         '| 电影总数 | 87,000 部 | 含标题/年份/类型元数据 |\n'
         '| 评分范围 | 0.5～5.0 | 步长为0.5 |\n'
         '| 评分稀疏度 | ≈0.14% | 32M / (270K×87K) |\n'
         '| 时间跨度 | 1995～2023 | 约28年评分数据 |\n'
         '| 数据来源 | GroupLens Research | 明尼苏达大学 |\n'
         '| 补充元数据 | TMDB API | 海报/导演/演员/简介/片长 |', False),
    ]
    insert_many(idx_212, table_2_1)
    print("  表2-1 inserted")

# =====================================================
# TABLE 3-1: System Functional Requirements Summary
# Insert before 3.2 (非功能性需求)
# =====================================================
print("Adding 表3-1...")
idx_32 = find_idx('3.3  非功能需求分析')
if idx_32:
    table_3_1 = [
        (None, None),
        ('表3-1 系统功能性需求汇总', True),
        ('| 功能模块 | 子功能 | 核心API端点 | 适用角色 |\n'
         '|----------|--------|------------|----------|\n'
         '| 用户管理 | 注册/登录/权限管理/个人信息 | /api/auth/*, /api/me | 用户+管理员 |\n'
         '| 电影浏览 | 列表/详情/搜索/高级搜索 | /api/movies, /api/search/* | 全部 |\n'
         '| 个性化推荐 | ItemCF/NCF/Hybrid三策略 + 推荐解释 | /api/recommendations, /api/recommendations/why | 已登录用户 |\n'
         '| 评分系统 | 提交/更新/历史查询 | /api/ratings, /api/my/ratings | 已登录用户 |\n'
         '| 影评系统 | 发表/删除/点赞/列表 | /api/reviews, /api/reviews/*/like | 已登录用户 |\n'
         '| 收藏系统 | 添加/删除/列表(favorite/watchlist/seen) | /api/collections, /api/my/collections | 已登录用户 |\n'
         '| 影单系统 | 创建/编辑/添加电影/排序/社交互动 | /api/movie-lists/* | 已登录用户 |\n'
         '| 通知系统 | 系统通知/社交通知/偏好设置 | /api/notifications/* | 已登录用户 |\n'
         '| 用户画像 | 12维特征/观影洞察/画像刷新 | /api/user/profile, /api/user/insights | 已登录用户 |\n'
         '| 数据看板 | 评分分布/类型趋势/用户分群/系统健康 | /api/stats/*, /api/dashboard/* | 全部 |\n'
         '| 管理后台 | 电影/用户/评论/通知/权限管理 | /admin/* | 管理员 |\n'
         '| 数据导出 | 用户数据/系统统计/完整备份 | /api/export/* | 已登录用户+管理员 |\n'
         '| 行为追踪 | 浏览/评分/搜索/点击行为记录 | 后端自动记录 | 已登录用户（后端透明） |\n'
         '| 推荐反馈 | 喜欢/不喜欢标记 | /api/feedback | 已登录用户 |', False),
    ]
    insert_many(idx_32, table_3_1)
    print("  表3-1 inserted")

# =====================================================
# TABLE 4-1: Database Table Summary (19 tables)
# Insert after 4.2.3, before 4.3
# =====================================================
print("Adding 表4-1...")
idx_43 = find_idx('4.3.1  推荐相关接口设计')
if idx_43:
    table_4_1 = [
        (None, None),
        ('表4-1 系统数据库表汇总', True),
        ('| 编号 | 表名 | 分类 | 主要用途 | 核心索引/约束 |\n'
         '|------|------|------|----------|-------------|\n'
         '| 1 | users | 用户与认证 | 用户账户、权限、登录信息 | username唯一索引, is_admin索引 |\n'
         '| 2 | movies | 电影与元数据 | 电影完整信息(TMDB补充) | title索引, year索引, tmdb_id |\n'
         '| 3 | ratings | 评分与交互 | 用户-电影评分记录 | (user_id,movie_id)唯一, (user_id,timestamp)复合索引 |\n'
         '| 4 | movie_similarity | 推荐核心 | ItemCF预计算相似度 | (movie_id,similar_movie_id)唯一, (movie_id,score)复合索引 |\n'
         '| 5 | recommendation_feedback | 推荐核心 | 推荐结果反馈 | (user_id,movie_id,context)唯一 |\n'
         '| 6 | reviews | 社交与内容 | 电影评论 | user_id/movie_id索引, status索引 |\n'
         '| 7 | review_likes | 社交与内容 | 评论点赞 | (user_id,review_id)唯一 |\n'
         '| 8 | user_collections | 社交与内容 | 用户收藏(favorite/watchlist/seen) | (user_id,movie_id,collection_type)唯一 |\n'
         '| 9 | watch_links | 社交与内容 | 电影观看链接 | movie_id索引 |\n'
         '| 10 | movie_lists | 社交与内容 | 用户影单 | user_id索引, is_public索引 |\n'
         '| 11 | movie_list_items | 社交与内容 | 影单电影条目 | (movie_list_id,movie_id)唯一 |\n'
         '| 12 | movie_list_likes | 社交与内容 | 影单点赞 | (movie_list_id,user_id)唯一 |\n'
         '| 13 | movie_list_comments | 社交与内容 | 影单评论 | movie_list_id索引, created_at索引 |\n'
         '| 14 | notifications | 系统支撑 | 用户通知 | user_id索引, (user_id,is_read)索引 |\n'
         '| 15 | user_notification_preferences | 系统支撑 | 通知偏好设置 | user_id唯一 |\n'
         '| 16 | movie_charts | 系统支撑 | 电影排行榜 | chart_type索引 |\n'
         '| 17 | chart_items | 系统支撑 | 排行榜条目 | chart_id索引 |\n'
         '| 18 | user_behaviors | 系统支撑 | 用户操作行为日志 | user_id, created_at索引 |\n'
         '| 19 | user_profiles | 系统支撑 | 12维用户画像特征 | user_id唯一索引 |', False),
    ]
    insert_many(idx_43, table_4_1)
    print("  表4-1 inserted")

# =====================================================
# TABLE 5-1: Vue Component Catalog
# Insert after 5.7.4 content
# =====================================================
print("Adding 表5-1...")
# Find end of 5.7.4 content - last paragraph before Ch6
idx_5_end = None
for i, el in enumerate(children):
    if el.tag == f'{{{w_ns}}}p' and '第6章' in t(el) and '实验设计' in t(el) and i > 400:
        # The paragraph before this (that's not empty)
        for j in range(i-1, 0, -1):
            if children[j].tag == f'{{{w_ns}}}p' and t(children[j]).strip():
                idx_5_end = j
                break
        break

if idx_5_end:
    table_5_1 = [
        (None, None),
        ('表5-1 Vue核心组件清单', True),
        ('| 组件名 | Props | 功能描述 | 使用页面 |\n'
         '|--------|-------|---------|----------|\n'
         '| MovieCard | movie对象(id/title/year/genres/poster_url/avg_rating) | 电影海报卡片，hover浮起动画 | 首页/推荐页/搜索结果 |\n'
         '| SkeletonGrid | cols/rows | 骨架屏加载占位，CSS shimmer动画 | 全部异步加载页面 |\n'
         '| StarRating | value/readonly | 星级评分(0.5步长)，hover高亮 | 推荐页/详情页/评分页 |\n'
         '| MovieSearch | - | 防抖搜索输入框(300ms)，下拉建议列表 | 导航栏 |\n'
         '| RecommendationCard | movie/score/because/feedback | 推荐卡片(含推荐分数+理由+反馈按钮) | 推荐页 |\n'
         '| MovieRow | title/movies/loading | 水平滚动电影行(含骨架屏+空状态) | 首页 |\n'
         '| MovieGrid | movies/loading/emptyText | 响应式网格(1/2/3/4列自适应) | 搜索结果/收藏/评分 |\n'
         '| SearchBox | - | 高级搜索表单(类型/年份/评分组合) | 高级搜索页 |\n'
         '| UserAvatar | user/size | 用户头像+下拉菜单 | 导航栏 |\n'
         '| NotificationBell | count | 通知铃铛图标+未读数量角标+下拉列表 | 导航栏 |\n'
         '| Pagination | current/total/onChange | 分页导航 | 列表类页面 |\n'
         '| ChartCard | title/chartOptions | ECharts图表容器+响应式resize | 数据看板 |', False),
    ]
    insert_many(idx_5_end + 1, table_5_1)
    print("  表5-1 inserted")

# =====================================================
# TABLE 6-2: Ablation Study Results
# Update existing 表6-2 or add if missing
# =====================================================
print("Adding 表6-2...")
# Find 6.4.2 section
idx_642 = find_idx('6.4.2  消融变量与实验设置')
if idx_642:
    # Find the description paragraph after 6.4.2 title and add table after it
    # First, look for existing 表6-2
    idx_table_62 = find_idx('表6-2')
    if idx_table_62 is None:
        # Find the end of 6.4.2 content to insert table
        idx_end_642 = None
        for i in range(idx_642 + 1, len(children)):
            if children[i].tag == f'{{{w_ns}}}p':
                text = t(children[i]).strip()
                if '6.4.3' in text or '6.4.4' in text:
                    idx_end_642 = i
                    break
        if idx_end_642:
            table_6_2 = [
                (None, None),
                ('表6-2 消融实验结果（K=10）', True),
                ('| 实验类别 | 参数 | 取值 | Precision@10 | Recall@10 | NDCG@10 | Coverage |\n'
                 '|----------|------|------|-------------|-----------|---------|----------|\n'
                 '| Hybrid recall_k | 召回候选数 | 50 | 0.00630 | 0.06305 | 0.03041 | 0.01085 |\n'
                 '| Hybrid recall_k | 召回候选数 | 100 | 0.00582 | 0.05818 | 0.02887 | 0.01189 |\n'
                 '| Hybrid recall_k | 召回候选数 | 200 | 0.00554 | 0.05539 | 0.02702 | 0.00875 |\n'
                 '| Hybrid recall_k | 召回候选数 | 500 | 0.00544 | 0.05444 | 0.02665 | 0.00863 |\n'
                 '| ItemCF per_seed_limit | 种子近邻数 | 10 | 0.01071 | 0.10709 | 0.05548 | 0.03692 |\n'
                 '| ItemCF per_seed_limit | 种子近邻数 | 25 | 0.00987 | 0.09874 | 0.05144 | 0.03181 |\n'
                 '| ItemCF per_seed_limit | 种子近邻数 | 50 | 0.00937 | 0.09374 | 0.04899 | 0.02913 |\n'
                 '| ItemCF per_seed_limit | 种子近邻数 | 100 | 0.00937 | 0.09374 | 0.04899 | 0.02913 |', False),
            ]
            insert_many(idx_end_642, table_6_2)
            print("  表6-2 inserted")

# =====================================================
# SAVE
# =====================================================
tree.write('thesis/unpacked_new/word/document.xml', encoding='utf-8', xml_declaration=True)
print("\nAll tables added successfully!")
