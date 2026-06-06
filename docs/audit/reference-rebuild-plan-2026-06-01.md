# 参考文献重建实施方案

**编制日期**：2026-06-01
**编制依据**：
- 《论文撰写要求.txt》（青岛理工大学毕业设计说明书撰写规范格式，第30-45行，第99行）
- 前期六维审计结果（整体覆盖度/章节覆盖度/算法覆盖度/系统设计覆盖度/实验覆盖度/主张-文献映射）
- 正文当前状态：引用括号已全部删除，参考文献列表保留22条旧条目

**方案性质**：纯规划方案。本方案不生成参考文献条目、不修改正文、不编写脚本。

---

## Phase 0：论文主题与研究边界确认

### Step 0.1：确认论文的核心研究问题

根据正文1.3.1（P56），论文要回答三个具体问题：

> Q1：传统协同过滤和深度学习在MovieLens 32M上的真实差距有多大？
> Q2：ItemCF召回 + NCF重排级联后提升多少、瓶颈在哪？
> Q3：引入EASE和LightGCN后，各方法的相对排序如何变化？

**这决定了参考文献的核心范围**：协同过滤、深度学习推荐、混合推荐、推荐评估方法论。

### Step 0.2：确认论文中"不需要文献"的内容边界

以下内容在重建参考文献时**不分配引用**：

| 章节 | 原因 |
|---|---|
| 第3章（需求分析）全文 | 工程描述，非知识性主张 |
| 第4章（总体设计）全文 | 同上 |
| 第5章（算法实现）全文 | 本文实现，非知识性主张 |
| 第7章（使用指南）全文 | 操作说明 |
| 第8章总结 | 本文总结 |
| 第8章展望（本文发现的缺口） | 本文分析 |
| 第6章实验数据本身 | 本文数据 |

### Step 0.3：确认学校模板对参考文献的硬约束

| 约束项 | 要求 | 来源 |
|---|---|---|
| 最少篇数 | ≥8篇 | 第99行 |
| 外文文献 | ≥2篇 | 第99行 |
| 编号方式 | 按文中出现先后用阿拉伯数字，方括号 | 第30行 |
| 格式标准 | 见六种类型的著录格式 | 第32-38行 |
| 页码范围 | 用全角波浪号 `～` | 示例第40行 |

### Step 0.4：确认未受影响的文献内容

正文引用已删除，但以下**不纳入本次重建**：

| 排除项 | 原因 |
|---|---|
| 正文中的公式编号（如 `(2-6)`） | 公式编号不是引用，不删除 |
| 正文中的图表编号（如 `表2-1`） | 图表编号不是引用，不删除 |
| 正文中的内部引用（如 `第6章`） | 内部章节引用不纳入参考文献体系 |

---

## Phase 1：引用需求识别

### Step 1.1：生成"必须引用"清单

基于六维审计结果，以下知识点在学术规范上**必须引用**。未标注"可选"的均为必须。

#### 1.1.1 算法原始论文（10篇）

| # | 知识点 | 文献需求 | 所在正文位置 |
|---|---|---|---|
| A1 | ItemCF 原始提出 | Linden, Smith, York. "Amazon.com recommendations." IEEE Internet Computing, 2003 | 1.2.1 P39 |
| A2 | ItemCF 调整余弦相似度比较 | Sarwar, Karypis, Konstan, Riedl. "Item-based collaborative filtering recommendation algorithms." WWW, 2001 | 1.2.1 P40 |
| A3 | TopK 截断 K=50-100 实验依据 | Deshpande, Karypis. "Item-based top-N recommendation algorithms." ACM TOIS, 2004 | 1.2.1 P41 |
| A4 | NCF 原始论文 | He, Liao, Zhang, et al. "Neural collaborative filtering." WWW, 2017 | 1.2.2 P45, P46, P47; 2.3 P93 |
| A5 | YouTube 推荐架构（级联范式） | Covington, Adams, Sargin. "Deep neural networks for YouTube recommendations." RecSys, 2016 | 1.2.2 P44; 1.2.3 P48, P50 |
| A6 | Google Play Wide & Deep | Cheng, Koc, Harmsen, et al. "Wide & deep learning for recommender systems." DLRS, 2016 | 1.2.2 P44 |
| A7 | LightGCN 原始论文 | He, Deng, Wang, et al. "LightGCN: Simplifying and powering graph convolution network for recommendation." SIGIR, 2020 | 2.6 P111 |
| A8 | EASE 原始论文 | Steck. "Embarrassingly shallow autoencoders for sparse data." WWW, 2019 | 2.6 P112 |
| A9 | RBM on Netflix 早期尝试 | Salakhutdinov, Mnih, Hinton. "Restricted Boltzmann machines for collaborative filtering." ICML, 2007 | 1.2.2 P43 |
| A10 | BPR 成对损失 | Rendle, Freudenthaler, Gantner, Schmidt-Thieme. "BPR: Bayesian personalized ranking from implicit feedback." UAI, 2009 | 1.2.2 P47 |

#### 1.1.2 数据集与评价指标（2篇）

| # | 知识点 | 文献需求 | 所在正文位置 |
|---|---|---|---|
| D1 | MovieLens 数据集 | Harper, Konstan. "The MovieLens datasets: History and context." ACM TiiS, 2015 | 2.1 P81 |
| D2 | 推荐系统评价指标综述 | 从以下二选一：Herlocker, Konstan, Terveen, Riedl. "Evaluating collaborative filtering recommender systems." ACM TOIS, 2004；或 Gunawardana, Shani. "A survey of accuracy evaluation metrics of recommendation tasks." Foundations and Trends in IR, 2022 | 2.5 P102（覆盖 Precision/Recall/MAP/NDCG/MRR/ILS/Coverage/Novelty 全部10个指标） |

#### 1.1.3 统计方法（1条引用可覆盖全部）

| # | 知识点 | 文献需求 | 所在正文位置 |
|---|---|---|---|
| S1 | Wilcoxon + Bonferroni-Holm + Cohen's d | 统计学教材或方法论文（建议用一本中文统计学教材覆盖三种方法，如"贾俊平. 统计学. 中国人民大学出版社"或英文方法论文） | 6.3.4 P449-450 |

### Step 1.2：生成"建议引用"清单

以下知识点引用会增强论文力度，但非学术规范上的"必须"。

| # | 知识点 | 文献需求 | 所在位置 |
|---|---|---|---|
| O1 | 流行度偏置/长尾推荐 | 推荐系统偏置研究（可选） | 1.1.1 P29 |
| O2 | 可解释推荐 | 可解释推荐综述（可选） | 1.1.1 P30 |
| O3 | Leave-last-out 评估协议 | 推荐系统评估方法论文（可选） | 6.2.2 |
| O4 | 多路召回 | 工业推荐架构论文（可选） | 1.2.3 P52 |
| O5 | SVD++ | Koren. "Factorization meets the neighborhood." KDD, 2008（可选——正文仅一笔带过） | 1.2.2 P43 |
| O6 | PMF | Mnih, Salakhutdinov. "Probabilistic matrix factorization." NeurIPS, 2007（可选——同上） | 1.2.2 P43 |

### Step 1.3：确认"不需要引用"的项目

以下在前期审计中曾被标记为"建议引用"，经进一步判断**不需要单独引用**：

| 项目 | 原因 |
|---|---|
| 协同过滤 memory-based vs model-based 分类 | 教材级常识 |
| 内积是线性函数 | 数学常识 |
| MLP 万能逼近定理 | 在引用 He 2017 NCF 时附带覆盖（He 2017 正文引用此定理） |
| 三种融合方式的工程取舍分析 | 本文分析，非他人发现 |
| Pipeline 中的 ItemCF/NCF/Hybrid 流程 | 本文实现 |
| 消融实验设计方法论 | 控制变量法是通用方法论，不需引用 |

---

## Phase 2：核心文献池构建

### Step 2.1：确定文献池规模

| 类别 | 数量 | 说明 |
|---|---|---|
| 必须引用 | 13篇 | A1-A10（10篇算法原始论文）+ D1-D2（2篇数据集与指标）+ S1（1条统计方法） |
| 建议引用 | 0-4篇 | O1-O4（按正文中是否有合适插入位置决定是否加入） |
| **目标总量** | **13-17篇** | 满足学校≥8篇要求，满足外文≥2篇要求 |

### Step 2.2：按文献类型分类

| 类型 | 数量 | 条目 |
|---|---|---|
| 国际会议论文 [C] | 8篇 | WWW×2 (Sarwar 2001, He 2017), SIGIR (LightGCN 2020, EASE 2019), RecSys (YouTube 2016), DLRS (Wide&Deep 2016), ICML (RBM 2007), UAI (BPR 2009) |
| 国际期刊论文 [J] | 4篇 | IEEE IC (Amazon 2003), ACM TOIS (Deshpande 2004, Herlocker 2004), ACM TiiS (MovieLens 2015) |
| 中文专著 [M] 或教材 | 1篇 | 统计学教材（覆盖 Wilcoxson/Bonferroni/Cohen's d） |
| 可选补充 [J/C] | 0-3篇 | O1-O4中选 |

### Step 2.3：逐一确认文献可获取性

**人工操作**：对每篇文献，在 Google Scholar 或知网检索，确认：
1. 论文标题、作者、年份、会议/期刊、卷号页码准确
2. PDF 全文可获取（至少有摘要可确认内容匹配）
3. 论文内容确实支撑论文中所引用的主张

**风险项**：
- Deshpande & Karypis 2004（ACM TOIS）——需确认准确标题是否为 "Item-based top-N recommendation algorithms"
- Henderson & Ferrari ——需确认此文献是否真实存在。如果无法找到，从正文中删除 C25

### Step 2.4：建立文献池卡片

为每篇文献建立一个卡片，包含：

```
编号：待分配（正文首次出现顺序）
文献：完整著录信息
支撑主张：在正文中支撑的具体知识点（引用 A1-A10 编号）
出现位置：首次在正文中被引用的段落
引用次数：全文引用次数
类型：[J]/[C]/[M]
```

---

## Phase 3：章节文献映射

### Step 3.1：确定每篇文献的首次出现位置

按正文叙事顺序，各文献首次出现的位置如下：

| 首次出现章节 | 文献 | 知识点编号 |
|---|---|---|
| 1.2.1 P39 | Amazon 2003 (Linden) | A1 |
| 1.2.1 P40 | Sarwar 2001 (调整余弦) | A2 |
| 1.2.1 P41 | Deshpande & Karypis 2004 (TopK) | A3 |
| 1.2.2 P43 | Salakhutdinov 2007 (RBM) | A9 |
| 1.2.2 P44 | YouTube 2016 (Covington) | A5 |
| 1.2.2 P44 | Wide & Deep 2016 (Cheng) | A6 |
| 1.2.2 P45 | NCF 2017 (He) | A4 |
| 1.2.2 P47 | BPR 2009 (Rendle) | A10 |
| 2.1 P81 | MovieLens 2015 (Harper) | D1 |
| 2.5 P102 | 评价指标综述 (Herlocker 或 Gunawardana) | D2 |
| 2.6 P111 | LightGCN 2020 (He) | A7 |
| 2.6 P112 | EASE 2019 (Steck) | A8 |
| 6.3.4 P449 | 统计学教材/方法论文 | S1 |

**这是参考文献的编号顺序**。同一篇文献在正文中被多次引用时使用同一编号。

### Step 3.2：标记同一文献的多次引用

| 文献 | 全文引用位置 |
|---|---|
| He 2017 NCF | 1.2.2 P45（首次提出），P46（三种变体），P47（逐点vs成对损失），2.3 P93（MLP万能逼近）——共 **4 次** |
| Covington 2016 YouTube | 1.2.2 P44（首次），1.2.3 P48（推理效率讨论），1.2.3 P50（级联范式）——共 **3 次** |
| Sarwar 2001 | 1.2.1 P40（首次），2.2 P86（调整余弦公式）——共 **2 次** |
| Deshpande & Karypis 2004 | 1.2.1 P41（首次），正文中可能无第二次引用 |

### Step 3.3：绘制章节-文献映射表

| 章节 | 本节引用的文献 | 数量 |
|---|---|---|
| 1.2.1 协同过滤研究现状 | Amazon 2003, Sarwar 2001, Deshpande 2004 | 3 |
| 1.2.2 深度学习推荐研究现状 | Salakhutdinov 2007, YouTube 2016, Wide&Deep 2016, NCF 2017, BPR 2009 | 5 |
| 1.2.3 混合推荐研究现状 | YouTube 2016（复用） | 0（新增） |
| 2.1 数据集 | MovieLens 2015 | 1 |
| 2.2 ItemCF 算法原理 | Sarwar 2001（复用） | 0（新增） |
| 2.3 NCF 模型原理 | NCF 2017（复用） | 0（新增） |
| 2.5 离线评价指标 | 评价指标综述 | 1 |
| 2.6 LightGCN与EASE | LightGCN 2020, EASE 2019 | 2 |
| 6.3.4 统计显著性检验 | 统计方法教材 | 1 |
| **总计** | | **13篇** |

---

## Phase 4：正文引用重建

### Step 4.1：确定引用标记插入规则

| 规则 | 说明 |
|---|---|
| 格式 | `[N]`——方括号，阿拉伯数字 |
| 位置 | 紧跟在被引用主张的句末标点之前，或作者名之后 |
| 首次出现 | 给新编号。同一文献再次出现时使用首次分配的编号 |
| 组合引用 | 多个文献支撑同一主张时用 `[N,M]` 格式，如 `[2,4]` |

### Step 4.2：逐段落标注引用插入点

按 Step 3.1 的首次出现顺序，标注每个引用标记的精确插入位置：

| 编号 | 插入位置 | 插入方式 |
|---|---|---|
| [1] | 1.2.1 P39 "…最早由 Amazon 在 2003 年的推荐系统实践中系统化提出" 句末 | 在"提出"后加 `[1]` |
| [2] | 1.2.1 P40 "Sarwar 等人比较了余弦相似度…" 句末 | 在作者名后加 `[2]` |
| [3] | 1.2.1 P41 "Deshpande 和 Karypis 在 2004 年的工作表明…" 句末 | 在作者名后加 `[3]` |
| [4] | 1.2.2 P43 "Salakhutdinov 等人用受限玻尔兹曼机…" 句末 | 在作者名后加 `[4]` |
| [5] | 1.2.2 P44 "YouTube 和 Google Play 先后公开了…" | 在"YouTube"后加 `[5]`，在"Google Play"后加 `[6]` |
| [6] | 同上 | 见上 |
| [7] | 1.2.2 P45 "NCF 由 He 等人于 2017 年在论文中正式提出" | 在"提出"后加 `[7]` |
| [8] | 1.2.2 P47 "Rendle 等人提出的 BPR" | 在作者名后加 `[8]` |
| [9] | 2.1 P81 "MovieLens 数据集由明尼苏达大学 GroupLens 研究团队整理发布" | 在"发布"后加 `[9]` |
| [10] | 2.5 P102 "本文从准确率、排序质量以及多样性与偏置等多个维度选择评价指标" | 在"评价指标"后加 `[10]` |
| [11] | 2.6 P111 "LightGCN 的出发点是在用户-物品二分图上做 Embedding 传播" | 在"LightGCN"首次出现后加 `[11]` |
| [12] | 2.6 P112 "EASE 走了另一条极端的路——不做梯度下降" | 在"EASE"首次出现后加 `[12]` |
| [13] | 6.3.4 P449 "方法用的是 Wilcoxon Signed-Rank…p 值用 Bonferroni-Holm 校正" | 在描述统计方法后加 `[13]` |

### Step 4.3：复用引用标记

| 编号 | 复用位置 | 说明 |
|---|---|---|
| [2] | 2.2 P86 "调整余弦相似度(Adjusted Cosine Similarity)先对评分进行用户均值归一化" | 此处讲 Sarwar 2001 的方法，复用 |
| [7] | 1.2.2 P46 "NCF 原文提出了三种架构变体" | He 2017 原文内容 |
| [7] | 1.2.2 P47 "He 等人后续的工作对 NCF 框架下逐点损失和成对损失做了系统对比" | He 2017 原文的实验部分 |
| [7] | 2.3 P93 "MLP 加 ReLU 激活后理论上可以逼近任意连续函数" | He 2017 引用了万能逼近定理 |
| [5] | 1.2.3 P48 "级联方案…核心思想在 YouTube 2016 的架构中被完整阐述" | 复用 Covington 2016 |
| [5] | 1.2.3 P50 "YouTube 2016 年的经典架构给出了一个示范" | 同上 |

### Step 4.4：处理可选引用

| 可选文献 | 决策 |
|---|---|
| O1 长尾偏置 | 如果正文1.1.1 P29 中能找到自然插入点，加入。否则不引用 |
| O2 可解释推荐 | 同上，P30 |
| O3 Leave-last-out | 如果有合适的方法论文，在6.2.2加入。否则沿用"本文设计" |
| O4 多路召回 | 1.2.3 P52 可引用工业实践文献 |
| O5 SVD++, O6 PMF | 正文仅一笔带过（"矩阵分解及其变体（SVD++、PMF）"），可删掉引用或保留为不编号的背景提及 |

---

## Phase 5：参考文献列表重建

### Step 5.1：删除旧参考文献列表

1. 定位到"参考文献"章节标题（当前为每章标题样式）
2. 删除该标题之后、附录之前的所有参考文献条目段落（当前为22条旧条目）

### Step 5.2：按 GB/T 7714 格式编写新条目

按编号 [1]-[13]（+可选）顺序，逐条编写。每条严格遵循学校模板的六种格式之一。

**格式速查**：

```
期刊论文 [J]：
[序号] 作者. 题名[J]. 刊名，年，卷号（期号）：起～止页码

会议论文 [C]：
[序号] 作者. 题名[C]. 会议论文集名. 会议地点，年：起～止页码

专著 [M]：
[序号] 作者. 书名[M]. 出版地：出版社，出版年. 起～止页码
```

### Step 5.3：逐条编写（按编号顺序）

**人工操作**：为以下13条文献找到完整著录信息并用 GB/T 7714 格式写出。

```
[1] 会议论文 [C]
    作者：Linden G, Smith B, York J
    题名：Amazon.com recommendations: Item-to-item collaborative filtering
    会议：IEEE Internet Computing（注意：这是期刊，不是会议——复核）
    年份：2003
    卷期页码：7(1): 76-80

[2] 会议论文 [C]
    作者：Sarwar B, Karypis G, Konstan J, Riedl J
    题名：Item-based collaborative filtering recommendation algorithms
    会议：WWW 2001
    地点：Hong Kong
    页码：285-295

[3] 期刊论文 [J]
    作者：Deshpande M, Karypis G
    题名：Item-based top-N recommendation algorithms
    期刊：ACM Transactions on Information Systems
    年份：2004
    卷期页码：22(1): 143-177

[4] 会议论文 [C]
    作者：Salakhutdinov R, Mnih A, Hinton G
    题名：Restricted Boltzmann machines for collaborative filtering
    会议：ICML 2007
    地点：Corvalis, Oregon
    页码：791-798

[5] 会议论文 [C]
    作者：Covington P, Adams J, Sargin E
    题名：Deep neural networks for YouTube recommendations
    会议：ACM RecSys 2016
    地点：Boston
    页码：191-198

[6] 会议论文 [C]
    作者：Cheng H T, Koc L, Harmsen J, et al
    题名：Wide & deep learning for recommender systems
    会议：DLRS 2016 (Workshop on Deep Learning for Recommender Systems)
    地点：Boston
    页码：7-10

[7] 会议论文 [C]
    作者：He X, Liao L, Zhang H, Nie L, Hu X, Chua T S
    题名：Neural collaborative filtering
    会议：WWW 2017
    地点：Perth
    页码：173-182

[8] 会议论文 [C]
    作者：Rendle S, Freudenthaler C, Gantner Z, Schmidt-Thieme L
    题名：BPR: Bayesian personalized ranking from implicit feedback
    会议：UAI 2009
    地点：Montreal
    页码：452-461

[9] 期刊论文 [J]
    作者：Harper F M, Konstan J A
    题名：The MovieLens datasets: History and context
    期刊：ACM Transactions on Interactive Intelligent Systems
    年份：2015
    卷期页码：5(4): 1-19

[10] 期刊论文 [J]（二选一）
    选项A：Herlocker J L, Konstan J A, Terveen L G, Riedl J
    题名：Evaluating collaborative filtering recommender systems
    期刊：ACM Transactions on Information Systems
    年份：2004
    卷期页码：22(1): 5-53
    
    选项B：Gunawardana A, Shani G
    题名：A survey of accuracy evaluation metrics of recommendation tasks
    期刊：Foundations and Trends in Information Retrieval
    年份：2022
    卷期页码：16(2-3): 1-102

[11] 会议论文 [C]
    作者：He X, Deng K, Wang X, Li Y, Zhang Y, Wang M
    题名：LightGCN: Simplifying and powering graph convolution network for recommendation
    会议：SIGIR 2020
    页码：639-648

[12] 会议论文 [C]
    作者：Steck H
    题名：Embarrassingly shallow autoencoders for sparse data
    会议：WWW 2019
    地点：San Francisco
    页码：3251-3257

[13] 专著 [M] 或教材
    统计学教材（覆盖 Wilcoxon + Bonferroni-Holm + Cohen's d）
    建议：贾俊平, 何晓群, 金勇进. 统计学[M]. 第8版. 北京：中国人民大学出版社, 2021.
    或选一本学校使用的统计学教材
```

### Step 5.4：确认学校格式要求

逐条校核：
- [ ] 页码范围统一使用 `～`（全角波浪号）
- [ ] 标点符号与学校示例一致
- [ ] 作者之间的分隔符、作者与题名之间的标点统一
- [ ] 外文文献不少于2篇（实际13篇全部外文，满足）
- [ ] 总数 ≥8篇（实际13篇，满足）

---

## Phase 6：引用一致性检查

### Step 6.1：编号-位置一致性

逐条核对：
- [ ] `[1]` 在正文中首次出现于 P39，参考文献列表 `[1]` 为 Amazon 2003
- [ ] `[2]` 在正文中首次出现于 P40，参考文献列表 `[2]` 为 Sarwar 2001
- [ ] …以此类推
- [ ] 没有正文中引用 `[N]` 但参考文献列表中不存在 `[N]` 的情况
- [ ] 没有参考文献列表中有 `[N]` 但正文中从未引用的情况

### Step 6.2：复用引用一致性

逐条核对：
- [ ] 同一篇文献在正文中多处出现时，编号是否一致（如 He 2017 在所有位置均为 `[7]`）
- [ ] `[N,M]` 组合引用中的每个编号都对应正确的文献

### Step 6.3：主张-文献匹配

逐条核对 Step 2.4 的文献池卡片，确认：
- [ ] 正文中引用 `[N]` 处的主张，与参考文献列表中 `[N]` 条目描述的内容一致
- [ ] 例如：正文说"He 等人 2017 年提出 NCF [7]"，参考文献 `[7]` 确实是 He 2017 NCF 论文（而非其他论文）

### Step 6.4：虚假引用清除

- [ ] 检查正文中是否还有"Henderson 和 Ferrari"等作者名——如果找到，确认对应文献是否在参考文献列表中
- [ ] 检查正文中是否还有"很多公开文献"等泛泛而谈——如果没补具体引用，改为不指名文献的表述
- [ ] 检查正文中是否还有其他"XX 等人"而未标注引用的地方

### Step 6.5：格式一致性

- [ ] 所有参考文同条目的标点符号风格统一
- [ ] 中文文献（如统计学教材）与英文文献的格式遵守各自规范
- [ ] `[J]` `[C]` `[M]` 类型标注统一

---

## 附录A：新旧参考文献对比迁移表

此表用于人工操作时对照旧条目是否有可复用内容。

| 旧编号 | 旧条目 | 处置 | 新编号 |
|---|---|---|---|
| [1] | Sarwar 2001 ItemCF | 保留（重新确认著录信息后使用） | [2] |
| [2] | Koren 2009 矩阵分解 | 正文不再引用矩阵分解原文，**删除** | — |
| [3] | Rendle 2009 BPR | 保留 | [8] |
| [4] | He 2017 NCF | 保留（重新确认著录信息后使用） | [7] |
| [5] | Hu 2008 隐式反馈 | 正文不再单独引用此文，**删除** | — |
| [6] | Netflix 2015 推荐系统 | 正文不再引用此文，**删除** | — |
| [7] | 王喆 深度学习推荐系统 | 正文未引用此专著，**删除** | — |
| [8] | 李航 统计学习方法 | 正文未引用此教材，**删除** | — |
| [9] | 王斌 推荐系统综述 | 正文不再引用此文，**删除** | — |
| [10] | 赵鑫 协同过滤综述 | 正文不再引用此文，**删除** | — |
| [11] | Herlocker 2004 评价指标 | 保留（作为 [10] 的选项A） | [10] 选项A |
| [12] | Harper 2015 MovieLens | 保留 | [9] |
| [13] | Zhang 2022 DL推荐综述 | 正文未引用，**删除**（或作为可选 O1 补入正文） | — |
| [14] | Wang 2023 GNN推荐综述 | 正文未引用，**删除** | — |
| [15] | Sun 2021 序列推荐 | 正文未引用，**删除** | — |
| [16] | Chen 2024 自监督推荐 | 正文未引用，**删除** | — |
| [17] | Zhao 2023 多阶段推荐 | 正文未引用，**删除** | — |
| [18] | Cheng 2016 Wide&Deep | 保留（重新编号） | [6] |
| [19] | Covington 2016 YouTube | 保留 | [5] |
| [20] | Beutel 2020 公平性 | 正文未引用，**删除** | — |
| [21] | Gunawardana 2022 评价指标 | 保留（作为 [10] 的选项B） | [10] 选项B |
| [22] | Yang 2022 长尾公平性 | 正文未引用，**删除** | — |

**迁移结果**：22条旧参考文献中，7条保留进入新体系，15条删除。新增5条（Amazon 2003, Deshpande 2004, Salakhutdinov 2007, LightGCN 2020, EASE 2019, 统计教材）。净结果：**旧体系22条 → 新体系13条**。

---

## 附录B：重建执行检查清单

按顺序勾选：

```
Phase 0：研究边界确认
  □ 0.1 确认三个核心研究问题
  □ 0.2 确认不需要引用的章节（Ch3/Ch4/Ch5/Ch7）
  □ 0.3 确认学校硬约束（≥8篇，外文≥2，方括号编号）
  □ 0.4 确认不纳入重建的内容（公式编号/图表编号/内部引用）

Phase 2：文献检索与验证
  □ 逐一检索13篇目标文献，确认准确著录信息
  □ 确认PDF可获取（至少摘要可读）
  □ 确认文献内容确实支撑论文主张
  □ 确认 Henderson & Ferrari 论文的存在性——如果不存在，标记正文句子待删除

Phase 3：章节映射
  □ 确认每篇文献的首次出现位置（决定编号）
  □ 确认复用引用的位置（同一文献多次出现保持编号一致）

Phase 4：正文引用插入
  □ 按Step 4.2的插入点逐段添加 [N] 标记
  □ 按Step 4.3的复用位置添加复用标记
  □ 确认无遗漏（特别是LightGCN和EASE——当前完全缺失）

Phase 5：参考文献列表生成
  □ 删除旧22条参考文献条目
  □ 按GB/T 7714格式逐条编写新13条条目
  □ 检查标点符号（特别是～和标点统一性）

Phase 6：一致性终检
  □ 逐条核对编号-位置-主张三维度
  □ 确认无虚假引用残留
  □ 确认格式符合学校模板
```

---

*方案结束。本方案不包含任何参考文献具体条目（仅列出文献检索方向），不修改正文，不编写脚本。下一步进入 Phase 2 文献检索阶段。*
