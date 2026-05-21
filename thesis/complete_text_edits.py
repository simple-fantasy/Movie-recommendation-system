"""
Complete text-only edits for graduation thesis:
1. Expand 4.2 database design (5→19 tables)
2. Add math formulas to Chapter 2 with numbering
3. Polish English abstract
4. Expand Appendix A (5→19 tables)
5. Expand Appendix B (15→40+ APIs)
6. Update Movie table field descriptions
"""
import copy
import xml.etree.ElementTree as ET
import re

w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

for prefix, uri in [('wps','http://schemas.microsoft.com/office/word/2010/wordprocessingShape'),
    ('wp','http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
    ('wp14','http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing')]:
    try: ET.register_namespace(prefix, uri)
    except: pass

DOC_XML = 'thesis/unpacked/word/document.xml'
tree = ET.parse(DOC_XML)
root = tree.getroot()
body = root.find(f'.//{{{w_ns}}}body')
children = list(body)

def get_text(p):
    if p.tag != f'{{{w_ns}}}p': return ''
    texts = []
    for t in p.iter(f'{{{w_ns}}}t'):
        if t.text: texts.append(t.text)
    return ''.join(texts)

def set_text(p, new_text):
    runs = p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]: p.remove(r)
        t = runs[0].find(f'{{{w_ns}}}t')
        if t is not None:
            t.text = new_text
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def clone_para(p, new_text):
    new_p = copy.deepcopy(p)
    runs = new_p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]: new_p.remove(r)
        t = runs[0].find(f'{{{w_ns}}}t')
        if t is not None:
            t.text = new_text
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return new_p

def find_idx(text_fragment):
    for i, el in enumerate(children):
        if el.tag == f'{{{w_ns}}}p':
            if text_fragment in get_text(el):
                return i
    return None

def find_para(text_fragment):
    idx = find_idx(text_fragment)
    return children[idx] if idx is not None else None

def insert_before(ref_idx, new_p):
    body.insert(ref_idx, new_p)

# ================================================================
# EDIT 1: Replace 4.2.1 concept design - expand to all 19 tables
# ================================================================
print("=== Edit 1: Expanding 4.2.1 concept design ===")
p_concept = find_para('系统的核心实体包括用户（User）、电影（Movie）、评分（Rating）')
if p_concept is not None:
    new_concept = (
        '系统的核心实体可分为五类：\n'
        '（1）用户与认证类：用户表（User）存储账户信息与权限。\n'
        '（2）电影与元数据类：电影表（Movie）存储电影完整元数据（含TMDB补充信息）。\n'
        '（3）评分与交互类：评分表（Rating）记录用户对电影的评分行为；相似度表（MovieSimilarity）存储ItemCF预计算的电影相似度对；推荐反馈表（RecommendationFeedback）记录用户对推荐结果的反馈。\n'
        '（4）社交与内容类：评论表（Review）存储用户对电影的评论；评论点赞表（ReviewLike）记录评论点赞关系；收藏表（UserCollection）支持favorite/watchlist/seen三种收藏类型；观看链接表（WatchLink）存储电影的在线播放链接；影单表（MovieList）、影单项表（MovieListItem）、影单点赞表（MovieListLike）和影单评论表（MovieListComment）共同构成影单社交系统。\n'
        '（5）系统支撑类：通知表（Notification）存储用户通知；通知偏好表（UserNotificationPreference）管理通知订阅设置；榜单表（MovieChart）和榜单项表（ChartItem）构成电影排行榜系统；用户行为表（UserBehavior）记录用户操作日志用于行为分析；用户画像表（UserProfile）存储12维用户偏好与行为特征。\n'
        '以上共19张数据表，以评分表为核心，通过外键关系关联用户、电影及各类扩展功能表。'
    )
    set_text(p_concept, new_concept)
    print("  4.2.1 updated")

# ================================================================
# EDIT 2: Expand 4.2.2 - Add remaining 14 tables after recommendation_feedback
# ================================================================
print("=== Edit 2: Expanding 4.2.2 logical structure ===")
p_feedback_end = find_para('feedback：反馈类型（如like/dislike）')
# Actually, find the paragraph with "context：反馈发生场景"
p_context = find_para('context：反馈发生场景')
p_unique_fb = find_para('并设置联合唯一约束(user_id, movie_id, context)')

if p_unique_fb:
    fb_idx = find_idx('并设置联合唯一约束(user_id, movie_id, context)')

    # Template paragraph for table descriptions
    template_p = find_para('（1）users（用户表）')

    new_tables_422 = [
        ('（6）reviews（评论表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（索引）\nmovie_id：int，外键关联movies.id（索引）\ncontent：text，评论内容\nrating：float，评论时的评分（可为空）\nlikes_count：int，点赞数\nis_featured：bool，是否精选评论\nstatus：enum（approved/rejected/pending），审核状态\ncreated_at：datetime\nupdated_at：datetime\n\n评论与用户、电影为多对一关系，与ReviewLike为一对多关系。', False),

        ('（7）review_likes（评论点赞表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id\nreview_id：int，外键关联reviews.id\ncreated_at：datetime\n\n设置(user_id, review_id)联合唯一约束，防止重复点赞。', False),

        ('（8）user_collections（用户收藏表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（索引）\nmovie_id：int，外键关联movies.id（索引）\ncollection_type：varchar(20)，收藏类型（favorite/watchlist/seen）\nnotes：text，用户备注\nrating：float，个人评分\ncreated_at：datetime\nupdated_at：datetime\n\n设置(user_id, movie_id, collection_type)联合唯一约束，支持同一电影加入不同类型收藏。', False),

        ('（9）watch_links（观看链接表）', True),
        ('id：int，主键\nmovie_id：int，外键关联movies.id（索引）\nuser_id：int，外键关联users.id（提交者，可为空）\nplatform：varchar(50)，平台名称\nurl：text，观看链接\nquality：varchar(20)，画质（SD/HD/4K）\nis_free：bool，是否免费\nis_official：bool，是否官方链接\nstatus：enum（active/pending/inactive/reported）\nreport_count：int，被举报次数\ncreated_at：datetime\nupdated_at：datetime', False),

        ('（10）notifications（通知表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（索引）\ntype：enum（system/review_reply/review_liked/movie_recommend/achievement）\ntitle：varchar(200)，通知标题\ncontent：text，通知内容\nrelated_id：int，关联对象ID\nis_read：bool，是否已读（索引）\ncreated_at：datetime\nread_at：datetime\n\n设置user_id索引支持快速拉取用户通知列表。', False),

        ('（11）user_notification_preferences（通知偏好表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（唯一）\nenable_system：bool，系统通知开关\nenable_review：bool，评论通知开关\nenable_recommend：bool，推荐通知开关\nenable_achievement：bool，成就通知开关\ncreated_at：datetime\nupdated_at：datetime', False),

        ('（12）movie_charts（电影榜单表）', True),
        ('id：int，主键\ntitle：varchar(100)，榜单标题\ndescription：text，榜单描述\nchart_type：enum（hot/top_rated/editor_pick/genre/year）\ngenre：varchar(50)，类型榜单的类型\nyear：int，年度榜单的年份\nis_active：bool，是否启用\nsort_order：int，排序权重\ncreated_at：datetime\nupdated_at：datetime\n\n与ChartItem为一对多关系。', False),

        ('（13）chart_items（榜单电影条目表）', True),
        ('id：int，主键\nchart_id：int，外键关联movie_charts.id\nmovie_id：int，外键关联movies.id\nrank：int，排名\nscore：float，榜单评分/热度值\nnote：varchar(200)，上榜理由\nadded_at：datetime', False),

        ('（14）user_behaviors（用户行为表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id\naction_type：varchar(50)，行为类型（view/rate/search/click）\ntarget_type：varchar(20)，目标类型（movie/person/genre/search_query）\ntarget_id：int，目标ID\nextra_data：json，额外信息\nip_address：varchar(45)\nuser_agent：varchar(500)\nsession_id：varchar(100)\nreferrer：varchar(500)\ncreated_at：datetime（索引）\n\n设置created_at索引支持时间范围查询和行为清理。', False),

        ('（15）user_profiles（用户画像表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（唯一，索引）\npreferred_genres：json，类型偏好（如{"Action":0.8,"Drama":0.6}）\npreferred_years：json，年代偏好（如{"1990s":0.7,"2000s":0.5}）\npreferred_actors：json，偏好演员列表\npreferred_directors：json，偏好导演列表\navg_rating_level：float，平均评分水平\nrating_variance：float，评分方差\nrating_entropy：float，评分分散度\ntotal_watch_time：int，累计观影时长（分钟）\ngenre_diversity：float，类型多样性指数\ndecade_diversity：float，年代多样性指数\nuser_type：varchar(20)，用户类型（casual/regular/enthusiast）\nactivity_level：varchar(20)，活跃度（low/medium/high）\nupdated_at：datetime\n\n存储12维用户偏好与行为特征，支持个性化推荐与用户分析。', False),

        ('（16）movie_lists（影单表）', True),
        ('id：int，主键\nuser_id：int，外键关联users.id（索引）\nname：varchar(100)，影单名称\ndescription：text，影单描述\ncover_image：varchar(500)，影单封面图\nis_public：bool，是否公开（索引）\nis_featured：bool，是否精选（索引）\nallow_comments：bool，是否允许评论\nview_count：int，浏览次数\nlike_count：int，点赞次数\ncomment_count：int，评论次数\ncreated_at：datetime（索引）\nupdated_at：datetime\n\n与MovieListItem、MovieListLike、MovieListComment为一对多关系。', False),

        ('（17）movie_list_items（影单项表）', True),
        ('id：int，主键\nmovie_list_id：int，外键关联movie_lists.id（索引）\nmovie_id：int，外键关联movies.id（索引）\norder：int，排序顺序\nnote：text，备注\nadded_at：datetime\n\n设置(movie_list_id, movie_id)联合唯一约束。', False),

        ('（18）movie_list_likes（影单点赞表）', True),
        ('id：int，主键\nmovie_list_id：int，外键关联movie_lists.id（索引）\nuser_id：int，外键关联users.id（索引）\ncreated_at：datetime\n\n设置(movie_list_id, user_id)联合唯一约束，防止重复点赞。', False),

        ('（19）movie_list_comments（影单评论表）', True),
        ('id：int，主键\nmovie_list_id：int，外键关联movie_lists.id（索引）\nuser_id：int，外键关联users.id（索引）\ncontent：text，评论内容\nparent_id：int，自关联外键（父评论ID，用于回复）\nlike_count：int，点赞数\ncreated_at：datetime（索引）\nupdated_at：datetime', False),
    ]

    for text, is_title in reversed(new_tables_422):
        new_p = clone_para(template_p if is_title else p_context, text)
        body.insert(fb_idx + 1, new_p)

    print("  14 tables added to 4.2.2")

# ================================================================
# EDIT 3: Expand 4.2.3 Index section
# ================================================================
print("=== Edit 3: Expanding 4.2.3 index section ===")
p_feedback_constraint = find_para('recommendation_feedback设置(user_id, movie_id, context)唯一约束')
if p_feedback_constraint:
    new_index_text = (
        'recommendation_feedback设置(user_id, movie_id, context)唯一约束，支持反馈更新覆盖；\n'
        'reviews.status与reviews.is_featured设置索引，用于审核与精选查询；\n'
        'review_likes设置(user_id, review_id)联合唯一约束，防止重复点赞；\n'
        'user_collections设置(user_id, movie_id, collection_type)联合唯一约束；\n'
        'notifications设置(user_id, is_read)索引，支持用户未读通知快速查询；\n'
        'user_notification_preferences.user_id设置唯一约束；\n'
        'user_behaviors.created_at设置索引，用于行为数据的时效查询与定期清理；\n'
        'user_profiles.user_id设置唯一约束与索引；\n'
        'movie_list_items设置(movie_list_id, movie_id)联合唯一约束；\n'
        'movie_list_likes设置(movie_list_id, user_id)联合唯一约束；\n'
        'movie_lists.is_public与is_featured设置索引，用于影单广场与精选展示。'
    )
    set_text(p_feedback_constraint, new_index_text)
    print("  4.2.3 expanded")

# ================================================================
# EDIT 4: Update Movie table fields (4.2.2, movies entry)
# ================================================================
print("=== Edit 4: Updating Movie table fields ===")
# Find the movies table description paragraph - the one with movie fields
p_movie_fields = find_para('id：主键（使用MovieLens电影ID）')
if p_movie_fields is None:
    p_movie_fields = find_para('id：主键')
    # Let me find by checking paragraphs near the movies title
    p_movie_title = find_para('（2）movies（电影表）')
    if p_movie_title:
        idx = find_idx('（2）movies（电影表）')
        # Look at next paragraph
        for j in range(idx+1, min(idx+5, len(children))):
            if 'id' in get_text(children[j]) and 'title' in get_text(children[j]):
                p_movie_fields = children[j]
                break

if p_movie_fields:
    new_movie_fields = (
        'id：int，主键（使用MovieLens电影ID）\n'
        'title：varchar(255)，电影标题（索引）\n'
        'year：int，上映年份（索引，可为空）\n'
        'genres：varchar(255)，类型字符串（"|"分隔）\n'
        'original_title：varchar(255)，原始标题\n'
        'director：varchar(255)，导演\n'
        'actors：text，演员列表（JSON格式存储，通过get_actors_list()/set_actors_list()方法序列化）\n'
        'description：text，剧情简介\n'
        'runtime：int，片长（分钟）\n'
        'poster_url：varchar(500)，海报URL（TMDB补充）\n'
        'backdrop_url：varchar(500)，背景图URL\n'
        'trailer_url：varchar(500)，预告片链接\n'
        'tagline：varchar(255)，宣传语\n'
        'tmdb_id：int，TMDB ID\n'
        'imdb_id：varchar(20)，IMDb ID\n'
        'language：varchar(10)，语言\n'
        'country：varchar(100)，制片国家\n'
        'status：enum（active/inactive/pending），电影状态\n'
        'is_featured：bool，是否精选\n'
        'view_count：int，浏览次数\n'
        'rating_count：int，评分人数\n'
        'avg_rating：float，平均评分\n'
        'created_at：datetime\n'
        'updated_at：datetime\n\n'
        '电影与评分表、评论表、收藏表、相似度表为一对多关系。'
    )
    set_text(p_movie_fields, new_movie_fields)
    print("  Movie fields updated from 4 to 20+")

# ================================================================
# EDIT 5: Add math formulas to Chapter 2
# ================================================================
print("=== Edit 5: Adding math formulas to Chapter 2 ===")
# 5a: Add formula to 2.2.1 - after the cosine similarity introduction paragraph
p_cos = find_para('对于物品(i)与物品(j)，其余弦相似度可理解为两向量夹角的余弦值')
if p_cos:
    # Insert formula paragraph after this one
    formula_text = (
        '余弦相似度公式如式(2-1)所示。设物品i和物品j对应的评分向量分别为Col_i和Col_j，'
        'U_{ij}为同时评分了两部电影的用户集合，则：'
    )
    formula_eq = (
        '                                            Σ_{u∈U_{ij}} R_{u,i} · R_{u,j}'
        '\n    sim(i, j) = cos(Col_i, Col_j) = ────────────────────────────────'
        '\n                                            ||Col_i|| × ||Col_j||           (2-1)'
    )
    formula_note = (
        '其中R_{u,i}为用户u对电影i的评分（或归一化评分），||Col_i||为向量Col_i的欧几里得范数。'
        '为消除用户评分尺度差异，本文在实际计算中先对评分进行用户均值归一化处理：'
    )
    formula_eq2 = (
        '    R^{norm}_{u,i} = R_{u,i} - μ_u                                      (2-2)'
    )
    formula_note2 = (
        '其中μ_u为用户u所有评分的均值。归一化后的评分可以取负值，'
        '表示该用户对某电影的评分低于其平均水平。相似度取值范围为[-1, 1]，'
        '转换后以1-distance得到非负相似度分数。'
    )
    for text in reversed([formula_note2, formula_eq2, formula_note, formula_eq, formula_text]):
        new_p = clone_para(p_cos, text)
        body.insert(find_idx('对于物品(i)与物品(j)，其余弦相似度可理解为两向量夹角的余弦值') + 1, new_p)
    print("  Cosine formula added to 2.2.1")

# 5b: Add recommendation scoring formula to 2.2.2
p_rec = find_para('ItemCF的候选打分通常采用"相似度加权"的方式')
if p_rec:
    formula_score = (
        '推荐分数的计算公式如式(2-3)所示：'
    )
    formula_eq3 = (
        '    score(u, i) = Σ_{j∈I_u} sim(i, j) × R_{u,j}                          (2-3)'
    )
    formula_note3 = (
        '其中I_u为用户u已评分的电影集合，sim(i, j)为电影i与电影j的余弦相似度，'
        'R_{u,j}为用户u对种子电影j的原始评分。推荐过程为：对用户历史中的每部种子电影j，'
        '将其相似度sim(i, j)与用户评分R_{u,j}加权后累加到候选电影i的得分上，'
        '最后对所有候选电影按得分降序排列，过滤已评分电影后输出Top-N推荐结果。'
    )
    idx = find_idx('ItemCF的候选打分通常采用"相似度加权"的方式')
    for text in reversed([formula_note3, formula_eq3, formula_score]):
        new_p = clone_para(p_rec, text)
        body.insert(idx + 1, new_p)
    print("  Scoring formula added to 2.2.2")

# ================================================================
# EDIT 6: Polish English abstract
# ================================================================
print("=== Edit 6: Polishing English abstract ===")
# Abstract paragraph 1
p_en1 = find_para('To address information overload and personalization demands')
if p_en1:
    new_en1 = (
        'To address information overload and meet personalization demands in movie consumption, '
        'this thesis designs and implements a multi-strategy movie recommendation system named CineMatch. '
        'Based on the MovieLens 32M dataset—comprising 32 million ratings from 270,000 users on 87,000 movies—'
        'the system leverages MySQL for data storage and management, employs the Flask application factory pattern '
        'for backend services and RESTful APIs, and integrates Jinja2 templates with Vue.js 3, Bootstrap 5, '
        'and ECharts on the frontend to deliver recommendation displays, user profiling, and visual analytics.'
    )
    set_text(p_en1, new_en1)

# Abstract paragraph 2
p_en2 = find_para('On the algorithmic side, three recommendation strategies are implemented')
if p_en2:
    new_en2 = (
        'At the algorithmic level, three recommendation strategies are implemented. '
        'Item-based Collaborative Filtering (ItemCF) serves as the primary recall model, computing movie '
        'similarities through cosine similarity with user-mean normalization and retaining only Top-K neighbors '
        'to improve storage efficiency and retrieval speed; it also supports explainable recommendations by '
        'identifying which previously liked movies contributed to each suggestion. '
        'A Neural Collaborative Filtering (NCF) model, built with PyTorch, implements a GMF architecture '
        'with asynchronous loading and a singleton inference engine for efficient candidate reranking. '
        'The Hybrid strategy combines both through a cascade architecture: ItemCF generates recall candidates, '
        'and NCF reranks them to produce the final Top-N list, balancing accuracy with interpretability. '
        'Beyond the core recommendation pipeline, the system includes comprehensive functional modules such as '
        '12-dimensional user profiling, asynchronous behavior tracking, recommendation feedback collection, '
        'movie list creation with social features, data visualization dashboards, and an admin panel.'
    )
    set_text(p_en2, new_en2)

# Abstract paragraph 3
p_en3 = find_para('For effectiveness verification, a unified offline evaluation framework')
if p_en3:
    new_en3 = (
        'To validate recommendation quality, a unified offline evaluation framework based on the '
        'Leave-Last-Out protocol is established, comparing the three strategies across five ranking-oriented '
        'metrics—Precision@K, Recall@K, MAP@K, NDCG@K, and MRR@K—supplemented by coverage and '
        'popularity bias analyses. Ablation studies examine the effects of key parameters such as recall '
        'candidate size and per-seed similarity limits. The overall system demonstrates strong usability '
        'and scalability, providing a solid foundation for future extensions including content-based features, '
        'online feedback integration, and A/B testing.'
    )
    set_text(p_en3, new_en3)

# KEY WORDS
p_kw = find_para('KEY WORDS: movie recommendation system, collaborative filtering')
if p_kw:
    set_text(p_kw,
        'KEY WORDS: movie recommendation system, collaborative filtering, neural collaborative filtering, '
        'hybrid recommendation, explainable recommendation, user profiling')

print("  English abstract polished")

# ================================================================
# EDIT 7: Expand Appendix A - add 14 tables
# ================================================================
print("=== Edit 7: Expanding Appendix A ===")
# Find after A.5 table (recommendation_feedback appendices)
p_a5_end = find_para('约束：(user_id, movie_id, context)联合唯一约束')
if p_a5_end:
    a5_idx = find_idx('约束：(user_id, movie_id, context)联合唯一约束')
    template_a = find_para('A.1  用户表 users')

    new_appendix_tables = [
        ('A.6  评论表 reviews', True),
        ('id：int，主键\nuser_id：int，外键→users.id，索引\nmovie_id：int，外键→movies.id，索引\ncontent：text\nrating：float（可为空）\nlikes_count：int\nis_featured：bool\nstatus：enum（approved/rejected/pending）\ncreated_at：datetime\nupdated_at：datetime', False),
        ('A.7  评论点赞表 review_likes', True),
        ('id：int，主键\nuser_id：int，外键→users.id\nreview_id：int，外键→reviews.id\ncreated_at：datetime\n约束：(user_id, review_id)联合唯一约束', False),
        ('A.8  用户收藏表 user_collections', True),
        ('id：int，主键\nuser_id：int，外键→users.id，索引\nmovie_id：int，外键→movies.id，索引\ncollection_type：varchar(20)（favorite/watchlist/seen）\nnotes：text\nrating：float\ncreated_at：datetime\nupdated_at：datetime\n约束：(user_id, movie_id, collection_type)联合唯一约束', False),
        ('A.9  观看链接表 watch_links', True),
        ('id：int，主键\nmovie_id：int，外键→movies.id，索引\nuser_id：int，外键→users.id（可为空）\nplatform：varchar(50)\nurl：text\nquality：varchar(20)（SD/HD/4K）\nis_free：bool\nis_official：bool\nstatus：enum（active/pending/inactive/reported）\nreport_count：int\ncreated_at：datetime\nupdated_at：datetime', False),
        ('A.10  通知表 notifications', True),
        ('id：int，主键\nuser_id：int，外键→users.id，索引\ntype：enum（system/review_reply/review_liked/movie_recommend/achievement）\ntitle：varchar(200)\ncontent：text\nrelated_id：int\nis_read：bool，索引\ncreated_at：datetime\nread_at：datetime', False),
        ('A.11  通知偏好表 user_notification_preferences', True),
        ('id：int，主键\nuser_id：int，外键→users.id（唯一）\nenable_system：bool\nenable_review：bool\nenable_recommend：bool\nenable_achievement：bool\ncreated_at：datetime\nupdated_at：datetime', False),
        ('A.12  电影榜单表 movie_charts', True),
        ('id：int，主键\ntitle：varchar(100)\ndescription：text\nchart_type：enum（hot/top_rated/editor_pick/genre/year）\ngenre：varchar(50)\nyear：int\nis_active：bool\nsort_order：int\ncreated_at：datetime\nupdated_at：datetime', False),
        ('A.13  榜单条目表 chart_items', True),
        ('id：int，主键\nchart_id：int，外键→movie_charts.id\nmovie_id：int，外键→movies.id\nrank：int\nscore：float\nnote：varchar(200)\nadded_at：datetime', False),
        ('A.14  用户行为表 user_behaviors', True),
        ('id：int，主键\nuser_id：int，外键→users.id\naction_type：varchar(50)（view/rate/search/click）\ntarget_type：varchar(20)\ntarget_id：int\nextra_data：json\nip_address：varchar(45)\nuser_agent：varchar(500)\nsession_id：varchar(100)\nreferrer：varchar(500)\ncreated_at：datetime，索引', False),
        ('A.15  用户画像表 user_profiles', True),
        ('id：int，主键\nuser_id：int，外键→users.id（唯一，索引）\npreferred_genres：json\npreferred_years：json\npreferred_actors：json\npreferred_directors：json\navg_rating_level：float\nrating_variance：float\nrating_entropy：float\ntotal_watch_time：int\ngenre_diversity：float\ndecade_diversity：float\nuser_type：varchar(20)\nactivity_level：varchar(20)\nupdated_at：datetime', False),
        ('A.16  影单表 movie_lists', True),
        ('id：int，主键\nuser_id：int，外键→users.id，索引\nname：varchar(100)\ndescription：text\ncover_image：varchar(500)\nis_public：bool，索引\nis_featured：bool，索引\nallow_comments：bool\nview_count：int\nlike_count：int\ncomment_count：int\ncreated_at：datetime，索引\nupdated_at：datetime', False),
        ('A.17  影单项表 movie_list_items', True),
        ('id：int，主键\nmovie_list_id：int，外键→movie_lists.id，索引\nmovie_id：int，外键→movies.id，索引\norder：int\nnote：text\nadded_at：datetime\n约束：(movie_list_id, movie_id)联合唯一约束', False),
        ('A.18  影单点赞表 movie_list_likes', True),
        ('id：int，主键\nmovie_list_id：int，外键→movie_lists.id，索引\nuser_id：int，外键→users.id，索引\ncreated_at：datetime\n约束：(movie_list_id, user_id)联合唯一约束', False),
        ('A.19  影单评论表 movie_list_comments', True),
        ('id：int，主键\nmovie_list_id：int，外键→movie_lists.id，索引\nuser_id：int，外键→users.id，索引\ncontent：text\nparent_id：int，自关联外键\nlike_count：int\ncreated_at：datetime，索引\nupdated_at：datetime', False),
    ]

    for text, is_title in reversed(new_appendix_tables):
        new_p = clone_para(template_a if is_title else p_a5_end, text)
        body.insert(a5_idx + 1, new_p)

    print("  Appendix A expanded to 19 tables")

# ================================================================
# EDIT 8: Expand Appendix B - API list from ~15 to ~40
# ================================================================
print("=== Edit 8: Expanding Appendix B ===")
# Find the last API entry in Appendix B
p_b_last = find_para('GET /api/metrics/evaluation：读取evaluation_results.json')
if p_b_last:
    b_idx = find_idx('GET /api/metrics/evaluation：读取evaluation_results.json')
    template_b = find_para('B.1  认证与用户接口')

    new_apis = [
        ('B.5  收藏与影单接口', True),
        ('POST /api/collections：添加收藏\nGET /api/my/collections：我的收藏列表\nDELETE /api/collections/<id>：删除收藏\nGET /api/movies/<id>/collection-status：查询收藏状态\nPOST /api/collections/<id>/notes：更新收藏备注\nPOST /api/movie-lists：创建影单\nGET /api/movie-lists：我的影单列表\nGET /api/movie-lists/public：公开影单列表\nGET /api/movie-lists/<id>：影单详情\nPUT /api/movie-lists/<id>：编辑影单\nDELETE /api/movie-lists/<id>：删除影单\nPOST /api/movie-lists/<id>/movies：添加电影到影单\nDELETE /api/movie-lists/<id>/movies/<id>：从影单移除电影\nPOST /api/movie-lists/<id>/like：点赞影单\nPOST /api/movie-lists/<id>/comments：评论影单\nGET /api/movie-lists/<id>/comments：影单评论列表', False),

        ('B.6  评论与观影链接接口', True),
        ('POST /api/reviews：发表评论\nGET /api/movies/<id>/reviews：电影评论列表\nPOST /api/reviews/<id>/like：点赞评论\nDELETE /api/reviews/<id>：删除评论\nGET /api/my/reviews：我的评论历史\nGET /api/movies/<id>/watch-links：查看观影链接\nPOST /api/movies/<id>/watch-links：提交观影链接\nPOST /api/watch-links/<id>/report：举报观影链接', False),

        ('B.7  通知与榜单接口', True),
        ('GET /api/notifications：获取通知列表\nPOST /api/notifications/<id>/read：标记已读\nPOST /api/notifications/read-all：全部标记已读\nGET /api/notifications/unread-count：未读数量\nGET /api/charts：榜单列表\nGET /api/charts/<id>：榜单详情\nGET /api/charts/popular：热门榜单', False),

        ('B.8  用户画像与行为分析接口', True),
        ('GET /api/user/profile：获取用户画像（12维特征）\nGET /api/user/insights：获取观影洞察\nPOST /api/user/profile/refresh：刷新用户画像\nGET /api/user/recommendation-reason：推荐理由详情\nGET /api/my/persona：类型偏好数据\nGET /api/my/timeline：评分时间线数据', False),

        ('B.9  数据导出接口', True),
        ('GET /api/export/user-data：导出用户数据\nGET /api/export/system-stats：导出系统统计\nGET /api/export/movie-data：导出电影数据\nGET /api/export/backup：完整备份导出', False),

        ('B.10  增强统计接口', True),
        ('GET /api/enhanced-stats/overview：系统概览统计\nGET /api/enhanced-stats/user-segments：用户分群数据\nGET /api/enhanced-stats/activity-heatmap：活动热力图数据\nGET /api/enhanced-stats/genre-trends：类型趋势数据\nGET /api/enhanced-stats/system-health：系统健康度\nGET /api/dashboard/overview：看板概览数据\nGET /api/dashboard/enhanced：增强看板数据', False),

        ('B.11  搜索接口', True),
        ('GET /api/search/advanced：高级组合搜索（标题+类型+年份+评分+排序）\nGET /api/search/suggestions：搜索建议（实时下拉提示）\nGET /api/search/history：搜索历史', False),

        ('B.12  管理员接口', True),
        ('GET /api/admin/users：用户列表\nPOST /api/admin/users/<id>/toggle-admin：切换管理员权限\nPOST /api/admin/users/<id>/toggle-active：切换账户激活状态\nGET /api/admin/dashboard：管理员仪表盘数据', False),
    ]

    for text, is_title in reversed(new_apis):
        new_p = clone_para(template_b if is_title else p_b_last, text)
        body.insert(b_idx + 1, new_p)

    print("  Appendix B expanded to 40+ endpoints")

# ================================================================
# SAVE
# ================================================================
print("\n=== Saving ===")
tree.write(DOC_XML, encoding='utf-8', xml_declaration=True)
print("All text edits complete!")
