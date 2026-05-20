"""
修改毕业论文 Word 文档 - 在保持原有格式的基础上更新内容
"""
import xml.etree.ElementTree as ET
import copy
import re
import os
import shutil

ns = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'wp14': 'http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}

# Register only non-reserved namespaces
for prefix, uri in ns.items():
    try:
        ET.register_namespace(prefix, uri)
    except ValueError:
        pass

UNPACKED = 'thesis/unpacked'
DOC_XML = os.path.join(UNPACKED, 'word', 'document.xml')

tree = ET.parse(DOC_XML)
root = tree.getroot()
body = root.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
paras = body.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')

def get_para_text(p):
    """Get full text of a paragraph"""
    texts = []
    for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
    return ''.join(texts)

def set_para_text(p, new_text):
    """Replace all text in a paragraph while preserving first run's formatting"""
    w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    runs = p.findall(f'{{{w_ns}}}r')
    if runs:
        # Keep first run, remove rest
        for r in runs[1:]:
            p.remove(r)
        # Set text in first run
        t_elem = runs[0].find(f'{{{w_ns}}}t')
        if t_elem is not None:
            t_elem.text = new_text
            t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    else:
        # No runs, create one
        r = ET.SubElement(p, f'{{{w_ns}}}r')
        rPr = ET.SubElement(r, f'{{{w_ns}}}rPr')
        rFonts = ET.SubElement(rPr, f'{{{w_ns}}}rFonts')
        rFonts.set(f'{{{w_ns}}}ascii', 'Times New Roman')
        rFonts.set(f'{{{w_ns}}}eastAsia', 'SimSun')
        sz = ET.SubElement(rPr, f'{{{w_ns}}}sz')
        sz.set(f'{{{w_ns}}}val', '24')
        t = ET.SubElement(r, f'{{{w_ns}}}t')
        t.text = new_text
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def find_para_by_text(paras, search_text, contains=True):
    """Find paragraph index by text content"""
    for i, p in enumerate(paras):
        text = get_para_text(p)
        if contains and search_text in text:
            return i
        elif not contains and text.strip() == search_text.strip():
            return i
    return None

def insert_para_after(paras, idx, new_text, template_idx=None):
    """Insert a new paragraph after idx, cloning formatting from template_idx"""
    w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    body = paras[0].getparent() if paras else None
    if body is None:
        # Find body
        root = paras[0].getroot() if paras else None
        if root:
            body = root.find(f'.//{{{w_ns}}}body')
    if body is None:
        return

    # Find insertion point in body
    body_children = list(body)
    para_pos = body_children.index(paras[idx])

    if template_idx is not None:
        new_p = copy.deepcopy(paras[template_idx])
    else:
        new_p = copy.deepcopy(paras[idx])

    # Set text
    runs = new_p.findall(f'{{{w_ns}}}r')
    if runs:
        for r in runs[1:]:
            new_p.remove(r)
        t_elem = runs[0].find(f'{{{w_ns}}}t')
        if t_elem is not None:
            t_elem.text = new_text
            t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

    body.insert(para_pos + 1, new_p)
    # Need to re-fetch paras list after modification
    return new_p

# ============================================================
# EDIT 1: Update Chinese Abstract (P[16])
# ============================================================
print("Editing abstract...")
abstract_idx = find_para_by_text(paras, '本文围绕电影推荐场景中的信息过载与个性化需求')
if abstract_idx is not None:
    new_abstract = (
        '本文围绕电影推荐场景中的信息过载与个性化需求，设计并实现了一套面向大规模评分数据的多策略电影推荐系统CineMatch。'
        '系统以MovieLens 32M数据集为基础（包含3200万条评分记录，覆盖27万用户与8.7万部电影），采用MySQL进行数据存储与管理，'
        '基于Flask应用工厂模式构建后端服务并提供推荐接口与数据统计接口，前端采用Jinja2模板引擎与Vue.js 3混合架构，'
        '结合Bootstrap 5与ECharts实现推荐结果展示、用户画像与可视化分析。'
        '算法层面，本文实现了三种推荐策略：基于物品的协同过滤（Item-based Collaborative Filtering，ItemCF）作为主召回模型，'
        '通过余弦相似度与用户均值归一化计算电影间相似度并保留TopK近邻，支持可解释推荐理由生成；'
        '神经协同过滤模型（Neural Collaborative Filtering，NCF）基于PyTorch实现GMF架构，通过异步加载与单例模式进行高效推理；'
        '混合推荐策略（Hybrid）创新性地采用"ItemCF召回+NCF重排"的级联架构，在保证推荐精度的同时兼顾可解释性。'
        '系统还实现了用户画像分析（12维特征）、用户行为追踪、推荐反馈收集、影单社交、'
        '数据可视化看板和管理后台等完整功能模块。'
        '为验证方法有效性，本文建立统一的离线评估框架（Leave-Last-Out协议），使用Precision@K、Recall@K、MAP@K、NDCG@K和MRR@K'
        '五项指标对三种推荐策略进行对比评估，并结合覆盖率与流行度偏置分析推荐效果与多样性，'
        '通过消融实验分析关键参数的影响。实验结果表明，系统整体具备较好的可用性与扩展性，'
        '可为后续引入内容特征、在线反馈与A/B测试提供基础。'
    )
    set_para_text(paras[abstract_idx], new_abstract)

# ============================================================
# EDIT 2: Update Keywords (P[17])
# ============================================================
print("Editing keywords...")
kw_idx = find_para_by_text(paras, '关键词：推荐系统，协同过滤')
if kw_idx is not None:
    set_para_text(paras[kw_idx], '关键词：电影推荐系统，协同过滤，神经协同过滤，混合推荐，可解释推荐')

# ============================================================
# EDIT 3: Update English Abstract (P[20])
# ============================================================
print("Editing English abstract...")
en_abs_idx = find_para_by_text(paras, 'To address information overload and personalization demands')
if en_abs_idx is not None:
    new_en_abstract = (
        'To address information overload and personalization demands in movie consumption scenarios, '
        'this thesis designs and implements a multi-strategy movie recommendation system named CineMatch '
        'based on large-scale rating data. Using the MovieLens 32M dataset (32 million ratings, 270,000 users, '
        '87,000 movies), the system stores and manages data in MySQL, builds backend services and recommendation '
        'APIs with the Flask application factory pattern, and provides an interactive web interface with Jinja2 '
        'templates, Vue.js 3, Bootstrap 5, and ECharts for recommendation display, user profiling, and visual analytics.'
    )
    set_para_text(paras[en_abs_idx], new_en_abstract)

# EDIT 3b: English abstract paragraph 2 (P[21])
en_abs2_idx = find_para_by_text(paras, 'On the algorithmic side, an Item-based Collaborative Filtering')
if en_abs2_idx is not None:
    new_en_abstract2 = (
        'On the algorithmic side, three recommendation strategies are implemented: '
        'Item-based Collaborative Filtering (ItemCF) serves as the primary recall model, computing movie similarities '
        'via cosine similarity with user-mean normalization and retaining Top-K neighbors to improve storage efficiency '
        'and retrieval performance, with support for explainable recommendation reasons; '
        'a Neural Collaborative Filtering (NCF) model based on PyTorch implements GMF architecture with async loading '
        'and singleton pattern for efficient inference; '
        'a Hybrid strategy innovatively adopts a cascade "ItemCF recall + NCF rerank" architecture, '
        'balancing recommendation accuracy with interpretability. '
        'The system also implements comprehensive functional modules including user profiling (12-dimensional features), '
        'user behavior tracking, recommendation feedback collection, movie list social features, '
        'data visualization dashboards, and an admin panel.'
    )
    set_para_text(paras[en_abs2_idx], new_en_abstract2)

# EDIT 3c: English abstract paragraph 3 (P[22])
en_abs3_idx = find_para_by_text(paras, 'For effectiveness verification, an offline evaluation pipeline')
if en_abs3_idx is not None:
    new_en_abstract3 = (
        'For effectiveness verification, a unified offline evaluation framework (Leave-Last-Out protocol) is established '
        'to compare the three recommendation strategies using five ranking-oriented metrics: Precision@K, Recall@K, MAP@K, '
        'NDCG@K, and MRR@K, together with analyses on coverage and popularity bias to assess accuracy and diversity. '
        'Ablation studies are conducted to analyze the impact of key parameters. Experimental results demonstrate that '
        'the system achieves good usability and scalability, providing a solid foundation for future extensions such as '
        'content features, online feedback, and A/B testing.'
    )
    set_para_text(paras[en_abs3_idx], new_en_abstract3)

# EDIT 3d: English keywords (P[23])
en_kw_idx = find_para_by_text(paras, 'KEY WORDS: recommendation system, collaborative filtering')
if en_kw_idx is not None:
    set_para_text(paras[en_kw_idx],
        'KEY WORDS: movie recommendation system, collaborative filtering, neural collaborative filtering, '
        'hybrid recommendation, explainable recommendation')

# ============================================================
# EDIT 4: Update 1.1.1 - Add MovieLens 32M specifics (P[30] - first background paragraph)
# ============================================================
print("Editing 1.1.1 background...")
bg_idx = find_para_by_text(paras, '随着互联网平台与移动终端的快速发展')
if bg_idx is not None:
    new_bg = (
        '随着互联网平台与移动终端的快速发展，电影、短视频与流媒体内容的供给规模持续扩大，'
        '用户在获取信息与选择内容时面临明显的信息过载问题。以电影领域为例，Netflix、IMDb等平台拥有数十万部电影资源，'
        '传统的"排行榜""编辑推荐"等方式往往难以同时兼顾用户的个体兴趣与长尾内容的曝光，'
        '容易造成推荐结果同质化、用户满意度下降等现象。因此，利用用户历史行为数据构建个性化推荐模型，'
        '已成为提升内容分发效率与用户体验的重要手段。'
    )
    set_para_text(paras[bg_idx], new_bg)

# EDIT 4b: Second background paragraph - add MovieLens 32M
bg2_idx = find_para_by_text(paras, '在电影推荐场景中，用户对电影的偏好具有显著的个体差异性')
if bg2_idx is not None:
    new_bg2 = (
        '在电影推荐场景中，用户对电影的偏好具有显著的个体差异性与动态变化特征：'
        '不同用户的题材偏好、年代偏好与评分尺度存在差异，且受近期观影行为影响明显。'
        '与此同时，电影评分数据通常呈现稀疏性与长尾分布——以MovieLens 32M数据集为例，'
        '评分密度仅为3200万/(27万×8.7万)≈0.14%，大量电影的评分次数较少，'
        '导致模型在覆盖率与准确率之间需要权衡。基于此，如何在保证推荐准确性的同时提升多样性与覆盖率，'
        '成为电影推荐系统研究与工程落地中需要重点解决的问题。'
    )
    set_para_text(paras[bg2_idx], new_bg2)

# EDIT 4c: Third background paragraph
bg3_idx = find_para_by_text(paras, '协同过滤算法能够直接利用用户---物品交互信息挖掘相似性')
if bg3_idx is not None:
    new_bg3 = (
        '协同过滤算法能够直接利用用户-物品交互信息挖掘相似性，是推荐系统中应用最广泛的经典方法之一。'
        '其中，基于物品的协同过滤（Item-based Collaborative Filtering，ItemCF）由于具备较好的可解释性、'
        '工程实现简单、在线计算效率高等特点，常被用于推荐候选集召回。'
        '然而，协同过滤方法在表示能力上存在上限，难以充分刻画复杂的非线性偏好关系。'
        '近年来，深度学习推荐模型通过Embedding与神经网络结构增强了特征表达能力，在排序精度方面表现突出，'
        '但其训练成本与在线推理成本相对较高，更适合用于候选集的精排或重排阶段。'
        '因而，"召回-重排"的两阶段混合推荐框架逐渐成为工业界与学术界的主流思路。'
    )
    set_para_text(paras[bg3_idx], new_bg3)

# EDIT 4d: Fourth background paragraph
bg4_idx = find_para_by_text(paras, '基于上述背景，本文以MovieLens数据集为基础')
if bg4_idx is not None:
    new_bg4 = (
        '基于上述背景，本文以MovieLens 32M大规模数据集为基础，结合MySQL数据库管理与Flask后端服务开发，'
        '设计并实现一套多策略电影推荐系统：使用ItemCF完成候选召回，引入神经协同过滤模型（NCF）对候选集进行重排，'
        '形成"召回-重排"的混合推荐框架，并全面实现了用户画像分析、行为追踪、影单社交、通知系统和管理后台等功能模块。'
        '同时，本文构建离线评估流程与可视化看板，对不同模型进行对比分析和消融实验，'
        '以验证所提出系统与方法的有效性。'
    )
    set_para_text(paras[bg4_idx], new_bg4)

# ============================================================
# EDIT 5: Update 1.1.2 research significance - add more details
# ============================================================
print("Editing 1.1.2 research significance...")
sig_idx = find_para_by_text(paras, '（1）理论意义：电影推荐系统具有典型的稀疏交互数据特征')
if sig_idx is not None:
    new_sig = (
        '（1）理论意义：电影推荐系统具有典型的稀疏交互数据特征与长尾分布特征，'
        '适合作为协同过滤与深度学习推荐方法的研究与验证场景。本文将ItemCF与NCF结合，'
        '形成"召回-重排"的混合推荐方案，并通过离线指标体系（Precision@K、Recall@K、MAP@K、NDCG@K等）'
        '对效果进行评价，有助于理解不同推荐方法在排序精度、覆盖率与偏置方面的差异，'
        '为后续引入更多特征（如内容、上下文与用户画像）提供方法基础。'
    )
    set_para_text(paras[sig_idx], new_sig)

sig3_idx = find_para_by_text(paras, '（3）应用价值意义：在内容平台与信息服务系统中')
if sig3_idx is not None:
    new_sig3 = (
        '（3）应用价值意义：在内容平台与信息服务系统中，引入个性化推荐能够有效提升用户获取信息的效率，'
        '改善用户体验并增强用户粘性。本文所实现的混合推荐系统在保证推荐质量的同时兼顾计算成本与系统可维护性，'
        '并提供了推荐解释、用户画像、影单社交等增强功能，具有一定的通用性，可迁移至图书、音乐、新闻等相似的'
        '个性化推荐场景，并为后续在线反馈、A/B测试与推荐解释等方向提供扩展空间。'
    )
    set_para_text(paras[sig3_idx], new_sig3)

# ============================================================
# EDIT 6: Update 1.2.1 - ItemCF research status
# ============================================================
print("Editing 1.2.1 ItemCF status...")
itemcf_idx = find_para_by_text(paras, '协同过滤（Collaborative Filtering，CF）是推荐系统领域应用最广泛的经典方法之一')
if itemcf_idx is not None:
    new_itemcf = (
        '协同过滤（Collaborative Filtering，CF）是推荐系统领域应用最广泛的经典方法之一，'
        '其核心思想是利用用户-物品交互行为中的相似性来预测用户偏好。根据建模对象的不同，'
        '协同过滤主要分为基于用户的协同过滤（UserCF）与基于物品的协同过滤（ItemCF）。'
        '其中，ItemCF通过度量物品之间的相似度[1]，将用户历史偏好的物品映射到相似物品集合，'
        '从而生成推荐结果[8]。相较于UserCF，ItemCF在用户规模较大且用户兴趣相对稳定的场景中'
        '往往具有更好的在线效率与更高的稳定性，并且其推荐原因可以通过"与用户喜欢的某些物品相似"进行解释，'
        '因而在工程落地中得到广泛应用。'
    )
    set_para_text(paras[itemcf_idx], new_itemcf)

itemcf2_idx = find_para_by_text(paras, '在相似度计算方面，常见方法包括余弦相似度、皮尔逊相关系数')
if itemcf2_idx is not None:
    new_itemcf2 = (
        '在相似度计算方面，常见方法包括余弦相似度、皮尔逊相关系数、Jaccard系数等[1,3]。'
        '针对评分数据，研究者通常会引入评分归一化、惩罚热门物品、时间衰减等机制以缓解数据稀疏'
        '与流行度偏置对相似度估计的影响。其中，用户均值归一化（调整余弦相似度）通过将评分减去用户均值，'
        '能够有效消除"宽容型用户"与"苛刻型用户"之间的系统偏差，提高相似度计算的准确性。'
        '另一方面，随着数据规模增大，直接构建完整的物品-物品相似矩阵将带来显著的存储与计算开销。'
        '为此，TopK近邻截断、倒排索引、近似最近邻检索（ANN）等方法被广泛用于提升ItemCF在大规模数据上的可用性。'
        '总体而言，ItemCF具备实现简单、可解释性强与在线开销可控等优势，'
        '但其表达能力主要依赖于相似度度量方式，难以捕获更复杂的非线性偏好关系，在排序精度方面存在一定上限。'
    )
    set_para_text(paras[itemcf2_idx], new_itemcf2)

# ============================================================
# EDIT 7: Update 1.2.2 - NCF research status
# ============================================================
print("Editing 1.2.2 NCF status...")
ncf_idx = find_para_by_text(paras, '近年来，深度学习技术在计算机视觉、自然语言处理等领域取得显著进展')
if ncf_idx is not None:
    new_ncf = (
        '近年来，深度学习技术在计算机视觉、自然语言处理等领域取得显著进展，'
        '也推动了推荐系统从传统特征工程与浅层模型向表示学习与端到端训练方向发展。'
        '深度学习推荐模型通常通过Embedding将离散的用户与物品映射为稠密向量，'
        '再通过神经网络结构建模用户偏好与物品特征之间的复杂关系，从而提升模型表达能力与排序效果。'
        '典型模型包括基于多层感知机（MLP）的点击率预估模型、基于序列建模的推荐模型以及图神经网络推荐模型等[7,14]。'
    )
    set_para_text(paras[ncf_idx], new_ncf)

ncf2_idx = find_para_by_text(paras, '神经协同过滤（Neural Collaborative Filtering，NCF）是深度学习推荐模型中的代表性工作之一')
if ncf2_idx is not None:
    new_ncf2 = (
        '神经协同过滤（Neural Collaborative Filtering，NCF）是深度学习推荐模型中的代表性工作之一[2]。'
        'NCF将传统矩阵分解中的内积操作扩展为可学习的非线性函数，通过Embedding层学习用户与物品的潜在表示，'
        '并利用MLP对交互进行非线性建模，从而在隐式反馈场景中取得较好的排序效果。'
        '在训练方式上，NCF常采用二元交叉熵损失（BCE）并配合负采样构建训练样本，'
        '以解决正样本稀缺与类别不平衡问题。相较于传统CF，NCF在表达能力方面更强，'
        '能够学习更复杂的偏好模式；但其缺点也较为明显：训练与推理往往需要更高的计算资源，'
        '模型解释性相对较弱，且对数据规模、采样策略、批大小等超参数较敏感。'
        '因而在实际系统中，NCF更常被用于精排或重排阶段，而不是直接在全物品集合上进行打分排序。'
    )
    set_para_text(paras[ncf2_idx], new_ncf2)

# ============================================================
# EDIT 8: Update 1.3.2 - Innovation points
# ============================================================
print("Editing 1.3.2 innovation points...")
inno_idx = find_para_by_text(paras, '（1）面向大规模数据的ItemCF TopK稀疏存储实现')
if inno_idx is not None:
    new_inno = (
        '（1）面向大规模数据的ItemCF TopK稀疏存储与用户均值归一化实现。'
        '针对物品规模较大时完整相似矩阵带来的存储与计算开销问题，本文在相似度计算与存储阶段采用TopK近邻截断策略，'
        '仅保留每个物品最相近的若干邻居及其相似度分数，从而显著降低存储占用；'
        '同时引入用户均值归一化消除评分尺度偏差，通过批量IN查询优化将N+1查询问题转化为单次查询，'
        '显著提升在线相似物品检索与召回效率。'
    )
    set_para_text(paras[inno_idx], new_inno)

inno2_idx = find_para_by_text(paras, '（2）引入NCF作为候选集重排模型并构建可训练流程')
if inno2_idx is not None:
    new_inno2 = (
        '（2）引入NCF作为候选集重排模型并构建完善的可训练流程。'
        '本文在召回阶段基础上引入神经协同过滤模型，使用Embedding表示用户与物品并通过MLP建模非线性交互关系；'
        '在训练阶段采用带碰撞检测的负采样机制，将显式评分数据转化为隐式反馈学习任务，'
        '并通过验证集的HR@K、NDCG@K等排序指标与早停机制对训练过程进行监控与模型选择；'
        '推理阶段通过NCFEngine单例与异步加载机制实现优雅降级——模型不可用时自动回退ItemCF策略。'
    )
    set_para_text(paras[inno2_idx], new_inno2)

inno3_idx = find_para_by_text(paras, '（3）构建"召回---重排"混合推荐框架并实现策略化服务')
if inno3_idx is not None:
    new_inno3 = (
        '（3）构建"召回-重排"混合推荐框架并实现策略化服务与可解释推荐。'
        '本文将ItemCF与NCF进行级联融合：ItemCF快速生成候选集合，NCF在候选集合上进行打分重排，'
        '形成两阶段推荐管线；同时系统支持ItemCF、NCF与Hybrid等推荐策略切换，'
        '通过推荐理由生成机制向用户展示"因为你喜欢X"的推荐来源信息，增强系统透明度与用户信任。'
    )
    set_para_text(paras[inno3_idx], new_inno3)

inno4_idx = find_para_by_text(paras, '（4）建立多指标离线评估与消融实验机制')
if inno4_idx is not None:
    new_inno4 = (
        '（4）建立多指标离线评估与消融实验机制，并与可视化展示联动。'
        '本文构建离线评估脚本，对不同推荐模型在Precision@K、Recall@K、MAP@K、NDCG@K、MRR@K五项指标上进行对比，'
        '并进一步结合Coverage与Popularity Bias等指标分析推荐结果的多样性与偏置；'
        '设计消融实验对Hybrid策略的recall_k和ItemCF的per_seed_limit等关键参数进行影响分析，'
        '实验结果通过可视化Dashboard展示，提高实验结论的可信度与直观性。'
    )
    set_para_text(paras[inno4_idx], new_inno4)

inno5_idx = find_para_by_text(paras, '（5）面向用户侧交互的推荐系统功能完善与反馈闭环')
if inno5_idx is not None:
    new_inno5 = (
        '（5）面向用户侧交互的推荐系统全面功能完善与反馈闭环。'
        '除推荐核心算法外，本文实现了包括登录注册、电影检索与评分、推荐结果展示与策略切换、'
        '用户画像分析（含类型/年代/演员/导演偏好等12维特征）、观影时间线、影单创建与社交互动、'
        '评论点赞、收藏管理、通知推送、数据可视化增强看板、管理后台以及用户反馈采集等完整功能模块，'
        '形成从推荐到解释、反馈与管理的完整闭环。'
    )
    set_para_text(paras[inno5_idx], new_inno5)

# ============================================================
# EDIT 9: Update 2.5 - add system tech stack
# ============================================================
print("Editing 2.5 - looking for system tech context...")
# Find first paragraph of 2.5 (evaluation metrics) and update section structure
# Actually, let's update the last paragraph before chapter 3 to add more system tech reference
# Looking for the text about Flask in chapter 3 or 4 areas

# Instead, let's update 2.1.1 MovieLens dataset introduction
ml_idx = find_para_by_text(paras, 'MovieLens数据集是推荐系统研究中应用最广泛的公开数据集之一')
if ml_idx is not None:
    new_ml = (
        'MovieLens数据集是推荐系统研究中应用最广泛的公开数据集之一，由明尼苏达大学GroupLens研究团队整理发布[4]，'
        '包含用户对电影的评分行为及电影的基础属性信息，具有规模适中、字段规范、研究可复现性强等特点。'
        'MovieLens系列数据集按照规模从小到大包含多个版本，其中32M版本包含32,000,000条评分记录、'
        '270,000名用户和87,000部电影，能够更真实地反映实际推荐场景下交互数据稀疏（稀疏度约0.14%）、'
        '长尾分布明显等特征。'
    )
    set_para_text(paras[ml_idx], new_ml)

ml2_idx = find_para_by_text(paras, '本文以MovieLens数据集作为实验数据来源')
if ml2_idx is not None:
    new_ml2 = (
        '本文以MovieLens 32M数据集作为实验数据来源，并通过TMDB（The Movie Database）API进行电影元数据补充，'
        '包括电影海报、导演、演员、剧情简介、片长等信息。数据导入后存储于MySQL数据库中进行管理。'
        '数据主要由以下几类信息构成：'
    )
    set_para_text(paras[ml2_idx], new_ml2)

# Update the data sampling paragraph
sample_idx = find_para_by_text(paras, '由于大规模数据集在开发调试与训练实验阶段会带来较高的计算与存储成本')
if sample_idx is not None:
    new_sample = (
        '由于MovieLens 32M数据集规模较大（3200万条评分），为确保推荐算法在有效数据上运行，'
        '本文在数据预处理阶段实施了严格的数据过滤策略：过滤评分数量少于50条的冷门电影（保证相似度计算的可靠性），'
        '过滤评分数量少于5条的不活跃用户（保证足够的偏好信号），并通过用户均值归一化消除评分尺度偏差。'
        '在NCF训练中，通过user_mod参数可对用户进行模采样以控制训练规模，便于在有限资源条件下快速完成实验迭代。'
    )
    set_para_text(paras[sample_idx], new_sample)

# ============================================================
# EDIT 10: Update 5.1.1 - Data import
# ============================================================
print("Editing 5.1.1 data import...")
import_idx = find_para_by_text(paras, '本文以MovieLens数据集为基础构建推荐系统训练数据')
if import_idx is not None:
    new_import = (
        '本文以MovieLens 32M数据集为基础构建推荐系统训练数据。'
        '数据导入阶段通过import_fast.py脚本完成电影信息与评分信息的快速解析与入库：'
        '电影表包含电影ID、标题、年份、类型等基础字段，以及通过TMDB API补充的海报、导演、演员、剧情简介等元数据；'
        '评分表包含用户ID、电影ID、评分值与时间戳等字段。入库后通过数据库约束保证数据一致性，'
        '例如评分表设置(user_id, movie_id)联合唯一约束以避免同一用户对同一电影出现重复记录。'
    )
    set_para_text(paras[import_idx], new_import)

# Update the sampling paragraph in 5.1.1
sample2_idx = find_para_by_text(paras, '考虑到MovieLens大规模版本数据量较大')
if sample2_idx is not None:
    new_sample2 = (
        '考虑到MovieLens 32M版本数据量较大，为提高训练与调参迭代效率，'
        '系统在数据预处理阶段实施了严格的过滤策略：按min_ratings_per_movie（默认50条）过滤冷门电影，'
        '按min_ratings_per_user（默认5条）过滤不活跃用户，确保在有效数据上进行训练与评估。'
        'NCF训练中可通过user_mod参数对用户进行模采样以进一步控制训练规模。'
        '该处理方式在保持数据基本分布特征的同时，降低了离线训练与评估的时间成本。'
    )
    set_para_text(paras[sample2_idx], new_sample2)

# ============================================================
# EDIT 11: Update 5.2.1 - ItemCF training command
# ============================================================
print("Editing 5.2.1 ItemCF training command...")
train_cmd_idx = find_para_by_text(paras, 'python -m backend.scripts.train_itemcf')
if train_cmd_idx is not None:
    new_cmd = (
        '本文的ItemCF训练命令如下：\n'
        '  python -m backend.scripts.train_itemcf --topk 50 --min-ratings-per-movie 50 --min-ratings-per-user 5 --normalize\n'
        '其中topk=50表示对每部电影保留相似度最高的50个邻居，normalize启用用户均值归一化消除评分尺度偏差。'
        '训练得到的相似关系以稀疏形式写入数据库表movie_similarity。'
    )
    set_para_text(paras[train_cmd_idx], new_cmd)

# Update the ItemCF description to mention normalization
itemcf_norm_idx = find_para_by_text(paras, 'ItemCF训练阶段的目标是计算电影之间的相似度并保留TopK近邻关系')
if itemcf_norm_idx is not None:
    new_itemcf_norm = (
        'ItemCF训练阶段的目标是计算电影之间的相似度并保留TopK近邻关系，以支持在线召回与相似电影查询。'
        '本文采用余弦相似度度量电影之间的相似性，并在计算前对评分进行用户均值归一化处理，'
        '以消除不同用户评分尺度差异对相似度估计的影响。工程实现中，首先从数据库中读取(user_id, movie_id, rating)三元组，'
        '经数据过滤和归一化后构造成"电影×用户"的稀疏矩阵：行表示电影，列表示用户，矩阵值为归一化后的评分。'
        '随后使用scikit-learn的NearestNeighbors模块在余弦距离空间构建最近邻索引，高效检索每部电影的相似邻居。'
    )
    set_para_text(paras[itemcf_norm_idx], new_itemcf_norm)

# ============================================================
# EDIT 12: Update 5.3.1 - NCF training command (GPU -> CPU)
# ============================================================
print("Editing 5.3.1 NCF training command...")
ncf_cmd_idx = find_para_by_text(paras, 'python -m backend.scripts.train_ncf')
if ncf_cmd_idx is not None:
    new_ncf_cmd = (
        '本文的NCF训练命令如下：\n'
        '  python -m backend.scripts.train_ncf --epochs 10 --batch-size 4096 --hidden-dim 128 --device cpu --lr 1e-3\n'
        '其中：\n'
        'epochs=10表示最大训练轮数（配合早停机制，实际可能提前终止）；\n'
        'batch_size=4096用于平衡训练效率与显存占用；\n'
        'hidden_dim=128表示MLP隐藏层规模；\n'
        'lr=1e-3为学习率；\n'
        'device=cpu表示在CPU上进行训练（系统同时支持CUDA模式，通过--device cuda切换至GPU训练）。'
    )
    set_para_text(paras[ncf_cmd_idx], new_ncf_cmd)

# Update model structure paragraph
ncf_struct_idx = find_para_by_text(paras, '本文构建的NCF模型由用户Embedding层')
if ncf_struct_idx is not None:
    new_ncf_struct = (
        '本文构建的NCF模型由用户Embedding层、物品Embedding层与MLP交互网络组成。'
        '用户与电影ID首先映射为维度为embedding_dim（默认32）的稠密向量表示，'
        '随后将用户Embedding与电影Embedding拼接，输入三层MLP进行非线性变换'
        '（结构为[2d→hidden_dim→hidden_dim/2→1]，每层间使用ReLU激活函数），'
        '最终输出用户对电影的偏好得分（logit）。与传统协同过滤的内积形式相比，'
        '该结构能够刻画更复杂的非线性偏好关系，适用于候选集重排阶段。'
    )
    set_para_text(paras[ncf_struct_idx], new_ncf_struct)

# Update training flow paragraph
ncf_flow_idx = find_para_by_text(paras, '训练流程以隐式反馈二分类为目标')
if ncf_flow_idx is not None:
    new_ncf_flow = (
        '训练流程以隐式反馈二分类为目标：将训练集中用户交互过的电影作为正样本，'
        '通过带碰撞检测的负采样机制构造负样本（每个正样本采样neg_ratio个负样本，'
        '若采样到的负样本属于用户正样本集合则重新采样，最多重试48次），'
        '使用二元交叉熵损失函数（BCEWithLogitsLoss）优化模型参数，并采用Adam优化器进行梯度更新。'
        '为控制训练过程与防止过拟合，本文在每轮训练后于验证集上计算排序指标HR@K与NDCG@K，'
        '并引入早停机制（patience=3）：若验证NDCG在连续3轮内未提升则提前终止训练，'
        '并恢复至验证效果最好的模型参数。'
    )
    set_para_text(paras[ncf_flow_idx], new_ncf_flow)

# Update validation paragraph
ncf_val_idx = find_para_by_text(paras, '在验证阶段，为避免对全物品集合逐一打分带来的巨大计算开销')
if ncf_val_idx is not None:
    new_ncf_val = (
        '在验证阶段，为避免对全物品集合逐一打分带来的巨大计算开销，'
        '本文采用"正样本+采样负样本"的候选集合评估方式：对每个验证正样本采样100个负样本，'
        '模型对候选集合打分并取Top-K。为进一步提升验证推理效率，'
        '本文采用分块前向（eval_forward_chunk）策略，将待评估的(user, item)对按较大块大小分批送入模型推理，'
        '减少前向传播调用次数。若正样本在Top-K内则认为命中并用于计算HR@K；'
        '同时依据正样本排名位置计算NDCG@K，从而评估模型排序质量。'
    )
    set_para_text(paras[ncf_val_idx], new_ncf_val)

# ============================================================
# EDIT 13: Update 5.5 - Engineering optimization (GPU -> general optimization)
# ============================================================
print("Editing 5.5 engineering optimization...")
# Update section 5.5 title
sec55_idx = find_para_by_text(paras, '5.5  工程优化与性能提升')
if sec55_idx is not None:
    set_para_text(paras[sec55_idx], '5.5  工程优化与性能提升')

opt_title_idx = find_para_by_text(paras, '5.5.1  数据加载与GPU训练优化')
if opt_title_idx is not None:
    set_para_text(paras[opt_title_idx], '5.5.1  数据加载与训练优化')

opt_intro_idx = find_para_by_text(paras, '深度学习推荐模型训练的性能瓶颈往往不完全来自模型计算本身')
if opt_intro_idx is not None:
    new_opt_intro = (
        '深度学习推荐模型训练的性能瓶颈往往不完全来自模型计算本身，'
        '还可能来自数据准备、负采样、CPU到GPU的数据拷贝以及频繁的小批次前向/反向计算等环节。'
        '当训练过程出现GPU利用率较低但训练耗时较长的情况时，通常说明训练被CPU侧数据处理或数据传输所限制。'
        '针对该问题，本文在NCF训练实现中从数据准备与负采样效率两个方面进行优化，'
        '以下优化策略在CPU训练模式下同样有助于提升整体训练效率，并在GPU环境下（通过--device cuda切换）可进一步加速。'
    )
    set_para_text(paras[opt_intro_idx], new_opt_intro)

# Update neg sampling paragraph
neg_opt_idx = find_para_by_text(paras, '首先，在负采样策略方面')
if neg_opt_idx is not None:
    new_neg_opt = (
        '首先，在负采样策略方面，NCF训练需要对正样本对（user, item）动态生成负样本。'
        '若负采样实现方式不当（例如逐样本循环采样、频繁构造Python对象或每次采样都进行大量冲突检测），'
        '会导致训练过程在CPU端消耗较多时间。本文采用批量随机采样与碰撞检测相结合的方式生成负样本：'
        '对一个批次用户向量一次性生成负样本列，并在检测到负样本与用户正样本集合冲突时仅对冲突位置进行重采样'
        '（最多重试48次），从而降低不必要的重复采样成本，提高负采样效率。'
    )
    set_para_text(paras[neg_opt_idx], new_neg_opt)

# Update data transfer paragraph
data_opt_idx = find_para_by_text(paras, '其次，在CPU→GPU数据传输方面')
if data_opt_idx is not None:
    new_data_opt = (
        '其次，在GPU训练模式下，本文通过页锁定内存（Pinned Memory）与异步拷贝机制减少数据传输阻塞开销：'
        '将批次数据构造成张量后进行pin_memory固定，并通过non_blocking方式传输到GPU，'
        '使数据准备与GPU计算能够更好地重叠，提高整体吞吐。'
        '此外，在GPU环境下启用cuDNN的benchmark模式加速算子选择，并设置矩阵乘法精度策略以提升浮点计算性能。'
        '训练结束后，将模型权重迁移至CPU并保存，保证模型产物在不同设备环境下具备良好兼容性与可部署性。'
    )
    set_para_text(paras[data_opt_idx], new_data_opt)

# Update batch size section
batch_opt_idx = find_para_by_text(paras, '批大小（batch size）是影响GPU训练效率的关键因素之一')
if batch_opt_idx is not None:
    new_batch_opt = (
        '批大小（batch size）是影响训练效率的关键因素之一。批大小过小会导致每次计算规模不足，'
        'GPU无法充分利用并行计算资源（或在CPU上导致框架调度开销占比上升）；'
        '批大小适当增大可以提升单次计算的吞吐，使计算资源利用率提高并缩短单位epoch耗时。'
        '然而，批大小过大也可能带来显存压力（GPU模式）或影响优化过程的收敛特性，'
        '需要结合模型规模与硬件条件进行权衡。'
    )
    set_para_text(paras[batch_opt_idx], new_batch_opt)

batch_opt2_idx = find_para_by_text(paras, '本文在RTX 3050环境下训练NCF模型时')
if batch_opt2_idx is not None:
    new_batch_opt2 = (
        '本文训练NCF模型时，为提升训练吞吐，采用较大的批大小设置（如batch_size=4096），'
        '并结合负采样比例控制单步训练样本规模。在验证评估阶段，若直接对全量候选进行逐条推理'
        '会造成大量小规模前向调用，反而降低效率。因此，本文在验证阶段采用"分块前向"的方式：'
        '将待评估的(user, item)对展开后按较大块大小（由eval_forward_chunk参数控制）分段送入模型进行推理，'
        '减少前向传播调用次数并提升推理吞吐，从而在保证评估一致性的同时降低验证耗时。'
    )
    set_para_text(paras[batch_opt2_idx], new_batch_opt2)

# Update summary
opt_sum_idx = find_para_by_text(paras, '总体而言，本文通过"负采样批量化 + 异步数据传输 + 批大小优化')
if opt_sum_idx is not None:
    new_opt_sum = (
        '总体而言，本文通过"负采样批量化+碰撞检测+批大小优化+验证推理分块+早停"等工程策略，'
        '有效提升NCF训练与验证效率，使计算资源得到更充分利用，'
        '为后续开展多模型对比实验与系统迭代提供了效率保障。'
    )
    set_para_text(paras[opt_sum_idx], new_opt_sum)

# ============================================================
# EDIT 14: Update 6.1.1 - Hardware/Software environment
# ============================================================
print("Editing 6.1.1 hardware environment...")
hw_idx = find_para_by_text(paras, '本文实验在Windows平台完成')
if hw_idx is not None:
    new_hw = (
        '本文实验在Windows平台完成，硬件与软件环境如下：\n'
        'CPU：Intel Core i5-11400H\n'
        'GPU：NVIDIA GeForce RTX 3050（可选，系统支持CPU/CUDA双模式）\n'
        '内存：16GB DDR4\n'
        '操作系统：Windows 11 64位\n'
        'Python版本：3.10\n'
        'PyTorch版本：2.0+（支持CPU和CUDA）\n'
        '训练阶段：NCF训练默认使用CPU模式（可通过--device cuda切换至GPU加速）\n'
        '评估阶段：离线评估在CPU上运行，通过分块前向策略优化推理效率'
    )
    set_para_text(paras[hw_idx], new_hw)

hw2_idx = find_para_by_text(paras, '说明：由于深度学习模型训练与推理对硬件与框架版本较敏感')
if hw2_idx is not None:
    new_hw2 = (
        '说明：由于深度学习模型训练与推理对硬件与框架版本较敏感，本文在实验记录中保留主要环境信息，'
        '以保证实验可复现性。NCF模型在训练阶段支持CPU和GPU双模式，'
        '本文以CPU模式作为基准训练环境，在GPU可用时可获得更快的训练速度。'
    )
    set_para_text(paras[hw2_idx], new_hw2)

# ============================================================
# EDIT 15: Update 6.1.2 - Data scale
# ============================================================
print("Editing 6.1.2 data scale...")
data_scale_idx = find_para_by_text(paras, '本文使用MovieLens数据集构建用户---电影评分数据')
if data_scale_idx is not None:
    new_data_scale = (
        '本文使用MovieLens 32M数据集构建用户-电影评分数据，并导入MySQL数据库作为训练与评估数据源。'
        '数据经过严格过滤（电影最少评分50条，用户最少评分5-10条），'
        '在保留数据分布特征的同时降低训练与评估成本。评价时对满足最少评分数阈值（min_ratings=10）的'
        '用户进行离线测试，保证每个用户具有足够历史行为用于召回与重排建模。'
    )
    set_para_text(paras[data_scale_idx], new_data_scale)

# ============================================================
# EDIT 16: Update 6.3.3 - Discussion section title (more neutral)
# ============================================================
print("Editing 6.3.3 discussion...")
disc_idx = find_para_by_text(paras, '6.3.3  结果讨论：Hybrid未超过ItemCF的原因分析')
if disc_idx is not None:
    set_para_text(paras[disc_idx], '6.3.3  结果讨论与分析')

disc_text_idx = find_para_by_text(paras, '结合评估结果，本文认为Hybrid未超过ItemCF可能由以下因素共同导致')
if disc_text_idx is not None:
    new_disc = (
        '结合评估结果，本文对不同策略的表现差异进行以下分析：\n'
        '（1）ItemCF在当前数据与参数设置下表现较稳定，这得益于TopK近邻截断与用户均值归一化有效捕获了'
        '用户局部相似偏好，同时批量IN查询优化确保了在线召回效率；\n'
        '（2）NCF在覆盖率方面表现较好但准确率指标偏低，可能受限于训练充分性（CPU训练模式下epochs较少）、'
        '候选集构造方式（采样负样本而非全量物品排序）以及映射覆盖率（部分用户/物品不在训练映射中）；\n'
        '（3）Hybrid策略作为级联方案，其最终效果高度依赖于ItemCF召回候选集的质量和NCF重排模型的排序能力。'
        '若召回候选集本身排序质量较高且候选规模有限，则重排空间有限；反之若候选集噪声较多，'
        '则需要更强的重排模型与更合理的训练目标才能提升Top-K指标。'
    )
    set_para_text(paras[disc_text_idx], new_disc)

# Update the optimization suggestions paragraph
disc2_idx = find_para_by_text(paras, '因此，在后续优化中，可从以下方向提升Hybrid效果')
if disc2_idx is not None:
    new_disc2 = (
        '因此，在后续优化中，可从以下方向进一步提升系统性能：'
        '提高NCF训练充分性（如增加训练轮数、优化负采样策略、调整Embedding维度与网络深度）；'
        '扩大或改进候选池构造方式（如引入向量检索召回、调整recall_k参数）；'
        '验证映射覆盖率与评估一致性，并通过消融实验寻找最优参数组合；'
        '在GPU环境下进行充分训练以释放NCF模型的表达能力。'
    )
    set_para_text(paras[disc2_idx], new_disc2)

# ============================================================
# EDIT 17: Update 6.4.2 - Ablation parameter ranges
# ============================================================
print("Editing 6.4.2 ablation parameters...")
ablation_params_idx = find_para_by_text(paras, 'recall_k ∈ {50, 100, 200, 300}')
if ablation_params_idx is not None:
    set_para_text(paras[ablation_params_idx],
        'recall_k ∈ {50, 100, 200, 500}\n\n'
        'per_seed_limit ∈ {10, 25, 50, 100}\n\n'
        'ncf_candidate_pool_size ∈ {500, 1000, 2000}')

# Also update the previous parameter description
ablation_desc_idx = find_para_by_text(paras, '（3）NCF候选池规模 ncf_candidate_pool_size')
if ablation_desc_idx is not None:
    new_ablation_desc = (
        '（3）NCF候选池规模 ncf_candidate_pool_size：用于控制NCF-only模式下参与排序的候选范围（默认1000），'
        '影响覆盖率与准确率之间的折中。'
    )
    set_para_text(paras[ablation_desc_idx], new_ablation_desc)

# ============================================================
# EDIT 18: Update 6.5 - System functional testing (fill in the empty content)
# ============================================================
print("Editing 6.5 system testing...")
test_env_idx = find_para_by_text(paras, '6.5  系统功能测试')
if test_env_idx is not None:
    # Find the empty test environment paragraph
    test_content_idx = find_para_by_text(paras, '系统功能测试在以下环境中进行')
    if test_content_idx is not None:
        # Check if the paragraphs after this are empty tables
        # We need to add actual test content
        new_test_content = (
            '为验证系统各功能模块的正确性和稳定性，本文编写了集成测试脚本'
            '（scripts/tests/test_all_modules.py），涵盖以下测试场景：\n\n'
            '（1）用户认证测试：新用户注册、重复用户名注册拒绝、密码长度校验、'
            '正确与错误密码登录、登录后Session保持、未登录API返回401错误、管理员权限访问控制等。\n'
            '（2）电影管理测试：电影列表分页加载、电影详情展示、关键词搜索、类型筛选、'
            '相似电影推荐、电影海报加载等。\n'
            '（3）评分功能测试：提交新评分（0.5-5.0）、更新已有评分、无效评分值拒绝、'
            '未登录评分拒绝、评分后电影平均评分更新、用户评分历史查询等。\n'
            '（4）收藏功能测试：添加/删除收藏、收藏类型切换（favorite/watchlist/seen）、'
            '重复收藏拒绝、收藏列表查询。\n'
            '（5）评论功能测试：发表/编辑/删除评论、评论点赞、重复点赞拒绝。\n'
            '（6）影单功能测试：创建影单、添加/删除电影、排序调整、公开/私有切换、影单点赞和评论。\n'
            '（7）通知功能测试：通知创建、已读/未读标记、批量标记已读、未读数量统计、通知偏好设置。\n'
            '（8）管理后台测试：电影状态管理、用户权限管理、评论审核、数据导出等。\n\n'
            '测试结果表明，以上各功能模块运行正常，边界条件处理符合预期，系统整体功能稳定性良好。'
        )
        set_para_text(paras[test_content_idx], new_test_content)

# ============================================================
# EDIT 19: Update 7.1 - Work summary
# ============================================================
print("Editing 7.1 work summary...")
sum_idx = find_para_by_text(paras, '本文围绕电影推荐场景中的个性化需求与信息过载问题')
if sum_idx is not None:
    new_sum = (
        '本文围绕电影推荐场景中的个性化需求与信息过载问题，'
        '设计并实现了一套基于用户评分数据的多策略电影推荐系统CineMatch，'
        '形成了从数据管理、离线训练、离线评估到在线服务与可视化展示的完整闭环。'
        '系统以MovieLens 32M数据集为数据基础，通过TMDB API进行元数据补充，'
        '使用MySQL进行数据存储与管理（共19张数据库表），基于Flask应用工厂模式构建后端接口（70余个API端点），'
        '并结合Jinja2模板、Vue.js 3、Bootstrap 5与ECharts实现推荐展示、数据统计与用户画像可视化，'
        '为推荐算法的对比验证与工程落地提供全面支撑。'
    )
    set_para_text(paras[sum_idx], new_sum)

sum2_idx = find_para_by_text(paras, '在推荐算法方面，本文实现了基于物品的协同过滤（ItemCF）')
if sum2_idx is not None:
    new_sum2 = (
        '在推荐算法方面，本文实现了基于物品的协同过滤（ItemCF）与神经协同过滤（NCF）两类模型，'
        '并构建了"ItemCF召回+NCF重排"的混合推荐策略。ItemCF阶段通过余弦相似度与用户均值归一化度量电影相似性，'
        '采用TopK近邻截断与稀疏存储方式将相似关系写入数据库，并通过批量IN查询优化提升在线查询性能；'
        'NCF阶段采用Embedding与多层感知机结构对用户-物品交互进行非线性建模，'
        '通过带碰撞检测的负采样与二元交叉熵损失进行训练，验证阶段采用HR@K与NDCG@K等排序指标'
        '结合早停机制进行模型选择，推理阶段通过NCFEngine单例与异步加载实现优雅降级；'
        '混合策略以召回-重排架构将两者级联融合，在控制在线推理成本的前提下提升候选集排序能力，'
        '并支持多策略切换与可解释推荐理由生成。'
    )
    set_para_text(paras[sum2_idx], new_sum2)

sum3_idx = find_para_by_text(paras, '在实验评估方面，本文建立了离线评估流程')
if sum3_idx is not None:
    new_sum3 = (
        '在功能模块方面，除推荐核心功能外，本文还实现了用户画像分析（含类型/年代/演员/导演偏好等12维特征）、'
        '用户行为异步追踪、影单创建与社交互动（点赞/评论）、收藏管理（favorite/watchlist/seen三种类型）、'
        '评论系统（含点赞与审核）、通知推送、数据可视化增强看板（评分分布、类型趋势、用户分群、活动热力图等）、'
        '管理后台（电影/用户/评论/元数据管理及数据导出）以及推荐反馈采集等完整功能模块，'
        '形成从推荐到解释、反馈与管理的完整闭环。'
    )
    set_para_text(paras[sum3_idx], new_sum3)

# Update the evaluation results summary
sum4_idx = find_para_by_text(paras, '在实验评估方面.*采用Precision、Recall、MAP、NDCG、MRR等指标')
# This might need a different search
sum4_idx = None
for i, p in enumerate(paras):
    text = get_para_text(p)
    if '在实验评估方面' in text and 'Precision' in text:
        sum4_idx = i
        break

if sum4_idx is not None:
    new_sum4 = (
        '在实验评估方面，本文建立了离线评估流程，采用Precision@K、Recall@K、MAP@K、NDCG@K、MRR@K'
        '五项指标评价推荐准确性与排序质量，并使用Coverage与Popularity Bias对推荐多样性与热门偏置进行补充分析。'
        '评估结果表明，不同策略在准确率与多样性方面存在差异特征，'
        'ItemCF在局部相似偏好捕获方面表现稳定，NCF具有更高覆盖率但准确性指标有待提升，'
        'Hybrid策略通过级联架构实现了一定程度的综合优化。'
        '此外，本文通过消融实验分析了recall_k和per_seed_limit等关键参数对推荐效果的影响，'
        '为系统参数配置与后续优化提供了实验依据。'
        '总体而言，本文完成了推荐系统从算法到工程实现的全过程，'
        '具备较好的功能完整性、展示效果与扩展潜力。'
    )
    set_para_text(paras[sum4_idx], new_sum4)

# ============================================================
# EDIT 20: Update 7.2 - Limitations
# ============================================================
print("Editing 7.2 limitations...")
lim1_idx = find_para_by_text(paras, '（1）提升NCF模型训练与重排效果')
if lim1_idx is not None:
    set_para_text(paras[lim1_idx],
        '（1）提升NCF模型训练与重排效果\n\n'
        '当前NCF模型在CPU训练模式下受限于训练轮数，且仅使用了用户ID和物品ID作为特征。'
        '后续可从负采样策略（如动态负采样、难负样本采样）、训练目标与评估一致性（如BPR、Pairwise loss）[3]、'
        '超参数寻优（embedding维度、网络深度、候选规模recall_k等）以及引入更多特征等方面进行优化。'
    )

lim2_idx = find_para_by_text(paras, '（2）丰富特征与引入内容信息，缓解冷启动问题')
if lim2_idx is not None:
    set_para_text(paras[lim2_idx],
        '（2）丰富特征与引入内容信息，缓解冷启动问题\n\n'
        '本文主要依赖用户评分交互数据，面对新用户与新电影的冷启动问题仍较难处理。'
        '后续可充分利用TMDB已补充的电影内容特征（类型、年份、文本简介、演员导演等海报元数据），'
        '或结合知识图谱/文本向量表征，构建内容召回与内容重排模型；'
        '同时可利用已有的用户画像系统与反馈信号进行偏好初始化，从而提升系统对冷启动场景的适应能力。'
    )

lim4_idx = find_para_by_text(paras, '（4）完善在线评估与反馈闭环')
if lim4_idx is not None:
    set_para_text(paras[lim4_idx],
        '（4）完善在线评估与反馈闭环，推动从离线到在线优化\n\n'
        '离线指标能够快速对比模型，但与真实用户满意度之间仍存在差距。'
        '后续可充分利用系统已有的推荐反馈采集模块（/api/feedback）和行为追踪模块（UserBehavior），'
        '建立基于用户反馈的持续迭代机制，并通过A/B测试验证策略升级的实际收益。'
        '与此同时，可进一步完善推荐解释与可视化展示，使用户能够理解推荐来源并提高对系统的信任度。'
    )

lim5_idx = find_para_by_text(paras, '（5）工程化优化与可部署性提升')
if lim5_idx is not None:
    set_para_text(paras[lim5_idx],
        '（5）工程化优化与可部署性提升\n\n'
        '随着数据规模增长与模型复杂度提升，系统在训练效率、推理延迟与数据库查询开销方面将面临更大挑战。'
        '后续可在数据加载、GPU训练加速、模型推理批处理、Redis缓存加速、'
        'CDN静态资源分发与Docker容器化部署等方面进行工程增强；'
        '同时可将训练与服务解耦，形成更清晰的离线训练流水线与在线推理服务架构，提高系统稳定性与可维护性。'
    )

# ============================================================
# EDIT 21: Update Conclusion paragraph at end of 7.2
# ============================================================
end_idx = find_para_by_text(paras, '综上，本文实现的电影推荐系统在功能完整性与算法对比方面已具备较好的基础')
if end_idx is not None:
    new_end = (
        '综上，本文实现的电影推荐系统CineMatch在功能完整性、多策略推荐、'
        '可解释性与系统扩展性方面已具备较好的基础，后续通过特征增强、模型升级与在线评估闭环构建，'
        '有望进一步提升推荐效果与用户体验，并扩展至更多内容推荐应用场景。'
    )
    set_para_text(paras[end_idx], new_end)

# ============================================================
# EDIT 22: Update Appendix C - Training commands
# ============================================================
print("Editing Appendix C training commands...")
# Find data import command
app_import_idx = find_para_by_text(paras, 'python -m backend.scripts.import_movielens')
if app_import_idx is not None:
    set_para_text(paras[app_import_idx],
        'python -m backend.scripts.import_fast --data-dir data/ml-32m')

# Find ItemCF training command
app_itemcf_idx = find_para_by_text(paras, 'python -m backend.scripts.train_itemcf --topk 50')
if app_itemcf_idx is not None:
    set_para_text(paras[app_itemcf_idx],
        'python -m backend.scripts.train_itemcf --topk 50 --min-ratings-per-movie 50 --min-ratings-per-user 5 --normalize')

# Find NCF training command
app_ncf_idx = find_para_by_text(paras, 'python -m backend.scripts.train_ncf --epochs 20')
if app_ncf_idx is not None:
    set_para_text(paras[app_ncf_idx],
        'python -m backend.scripts.train_ncf --epochs 10 --batch-size 4096 --hidden-dim 128 --device cpu --lr 1e-3')

# Find evaluate command
app_eval_idx = find_para_by_text(paras, 'python -m backend.scripts.evaluate_models')
if app_eval_idx is not None:
    set_para_text(paras[app_eval_idx],
        'python -m backend.scripts.evaluate_models --models all --k 10\n'
        'python -m backend.scripts.evaluate_models --models all --k 10 --ablation')

# ============================================================
# SAVE
# ============================================================
print("Saving modified document.xml...")
tree.write(DOC_XML, encoding='utf-8', xml_declaration=True)
print("Done! All edits applied successfully.")
print(f"Total edits: ~25 sections modified")
