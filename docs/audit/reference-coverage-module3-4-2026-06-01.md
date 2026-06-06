# 参考文献覆盖度审计 — 模块三、四

**审计日期**：2026-06-01
**审计身份**：论文外审专家视角

---

## 模块三：算法覆盖度审计

### 3.1 审计方法

对论文涉及的每一个算法、指标、技术方法，检查四个维度的引用完整性：

| 维度 | 定义 | 权重 |
|---|---|---|
| **原始论文引用** | 该方法最初被提出的论文 | 必须 |
| **权威综述引用** | 该领域公认的综述或 survey | 建议 |
| **中文研究引用** | 中文文献对该方法的介绍或应用 | 可选（本科论文加分项） |
| **工程实践引用** | 工业界对该方法的应用报道 | 可选 |

每个算法/指标按以下矩阵评定。

---

### 3.2 推荐算法覆盖矩阵

#### 3.2.1 ItemCF（基于物品的协同过滤）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Linden, Smith, York. "Amazon.com recommendations: Item-to-item collaborative filtering." IEEE Internet Computing, 2003 | 🔴 正文声称"Amazon 2003年系统化提出[1]"，但参考文献 [1] 是 Sarwar 2001 而非 Linden 2003 | **错配** |
| 权威引用 | Sarwar, Karypis, Konstan, Riedl. "Item-based collaborative filtering recommendation algorithms." WWW, 2001（调整余弦相似度的比较研究） | 🔴 正文声称"Sarwar等人[4]比较了三种相似度"，但参考文献 [4] 是 He 2017 NCF | **错配** |
| 权威引用 | Deshpande, Karypis. "Item-based top-N recommendation algorithms." ACM TOIS, 2004（TopK 截断实验） | 🔴 正文声称"Deshpande和Karypis[6]在2004年表明K取50-100"，但参考文献 [6] 是 Netflix 2015 | **错配** |
| 中文引用 | 无 | ❌ | 缺失 |
| 综述引用 | 无 | ❌ | 缺失 |

**风险等级**：🔴 致命。论文的核心召回模型，三处关键文献引用全部错配。正文描述了三篇不同的论文，但参考文献列表中对应编号的条目均不是正文描述的那篇。

**修复**：将参考文献 [1] 替换为 Linden 2003，[4] 替换为 Sarwar 2001，[6] 替换为 Deshpande & Karypis 2004。按正文首次出现顺序重新编号。

---

#### 3.2.2 NCF（神经协同过滤）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | He, Liao, Zhang, et al. "Neural collaborative filtering." WWW, 2017 | 🔴 正文 4 次引用 [2] 声称 He 2017 NCF，但参考文献 [2] 是 Koren 2009 矩阵分解 | **错配** |
| 权威引用 | 同上，He 2017 即该领域的核心论文 | 🔴 同上 | **错配** |
| 中文引用 | 无 | ❌ | 缺失 |
| 综述引用 | Zhang et al. 2022 DL推荐综述（当前在未引用列表中） | 🟡 文献存在但正文未引用 | 可补充 |

**风险等级**：🔴 致命。论文的核心重排模型，原始论文引用完全错配。正文引用了 4 次 He 2017（包括 NCF 提出、三种变体、MLP 万能逼近定理引用），但参考文献条目与正文描述完全无关。

**修复**：将 [2] 替换为 He 2017。所有 4 次出现合并为同一编号。

---

#### 3.2.3 Hybrid（混合推荐级联架构）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Covington, Adams, Sargin. "Deep neural networks for YouTube recommendations." RecSys, 2016（级联架构的标志性工业论文） | ✅ [19] 正确指向此论文 | **正确** |
| 权威引用 | 推荐系统架构综述（三种融合方式的比较） | ❌ 无引用 | 缺失 |
| 中文引用 | 无 | ❌ | 缺失 |
| 工程实践引用 | 本文的级联实现是本论文贡献，不引用 | — | — |

**风险等级**：🟢 低。核心引用（YouTube 2016）正确。三种融合方式（加权/特征/级联）的比较缺少文献支撑，但作为本文的自主分析可接受。

---

#### 3.2.4 LightGCN（轻量图卷积网络）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | He, Deng, Wang, et al. "LightGCN: Simplifying and powering graph convolution network for recommendation." SIGIR, 2020 | 🔴 **正文无任何引用标记。** 2.6 节详细描述了 LightGCN 的原型设计，但整段没有任何引用 | **完全缺失** |
| 权威引用 | 图神经网络推荐综述（Wang et al. 2023，当前在未引用列表中） | 🔴 综述论文存在但未在正文中引用 LightGCN 部分 | 缺失 |
| 中文引用 | 无 | ❌ | 缺失 |
| 工程实践引用 | 本文用 LightGCN 作为外部对比，不引用 | — | — |

**风险等级**：🔴 致命。LightGCN 是独立方法，作为外部对比模型参与第 6 章全量排序实验中。正文在第 2.6 节描述了其全部原理（二分图 Embedding 传播、去除特征变换、3层卷积+均值聚合、BPR损失），但全文没有任何引用标记指向 He 2020 SIGIR 论文。在学术规范上，描述了他人提出的方法却不标注来源，等同于未引用。

**修复**：在 2.6 节 LightGCN 描述段首插入引用标记，指向 He 2020 LightGCN。

---

#### 3.2.5 EASE（闭式最小二乘自编码器）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Steck. "Embarrassingly shallow autoencoders for sparse data." WWW, 2019 | 🔴 **正文无任何引用标记。** 2.6 节详细描述了 EASE 的完整数学推导（G=XᵀX、闭式解、λ=500、对角线置零），但整段没有任何引用 | **完全缺失** |
| 权威引用 | 线性推荐方法综述 | ❌ | 缺失 |
| 中文引用 | 无 | ❌ | 缺失 |

**风险等级**：🔴 致命。与 LightGCN 同等严重。EASE 是独立方法，作为外部对比模型参与第 6 章全量排序实验。正文描述了其完整数学推导，但无引用。

**修复**：在 2.6 节 EASE 描述段首插入引用标记，指向 Steck 2019 EASE。

---

#### 3.2.6 RBM 推荐（受限玻尔兹曼机）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Salakhutdinov, Mnih, Hinton. "Restricted Boltzmann machines for collaborative filtering." ICML, 2007 | 🔴 正文声称"[3]用RBM在Netflix上建模"，但参考文献 [3] 是 Rendle 2009 BPR | **错配** |

**风险等级**：🟠 高。作为"神经网络在推荐领域早期尝试"的历史叙述，引用错配。

---

#### 3.2.7 SVD++ 和 PMF

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| SVD++ 原始论文 | Koren. "Factorization meets the neighborhood: a multifaceted collaborative filtering model." KDD, 2008 | 🔴 [7] 指向王喆《深度学习推荐系统》（中文专著） | **错配** |
| PMF 原始论文 | Mnih, Salakhutdinov. "Probabilistic matrix factorization." NeurIPS, 2007 | 🔴 [8] 指向李航《统计学习方法》（中文教材） | **错配** |

**风险等级**：🟠 高。两个矩阵分解经典变体，正文用"（SVD++[7]、PMF[8]）"一笔带过，引用应准确。

---

#### 3.2.8 BPR（贝叶斯个性化排序）

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Rendle, Freudenthaler, Gantner, Schmidt-Thieme. "BPR: Bayesian personalized ranking from implicit feedback." UAI, 2009 | 🔴 正文声称"Rendle等人[11]提出的BPR"，但参考文献 [11] 是 Herlocker 2004 评价指标综述 | **错配** |

**风险等级**：🟠 高。论文在讨论 NCF 训练目标时引用了 BPR 作为对比，原始论文引用错配。

---

#### 3.2.9 YouTube 推荐架构

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Covington et al. RecSys, 2016 | ✅ [19] 正确。正文中 3 次引用（1.2.2 P44、1.2.3 P48、1.2.3 P50）均指向此论文 | **唯一正确的引用** |

**风险等级**：🟢 无。

---

#### 3.2.10 Google Play Wide & Deep

| 评估维度 | 需要的内容 | 当前状态 | 判定 |
|---|---|---|---|
| 原始论文引用 | Cheng, Koc, Harmsen, et al. "Wide & deep learning for recommender systems." DLRS, 2016 | 🔴 [9] 指向王斌 2014 推荐系统综述（中文期刊），非 Cheng 2016 | **错配** |

**风险等级**：🟠 高。值得注意的是 Cheng 2016 的论文在参考文献列表中以 [18] 存在，但正文从未引用 [18]。这是一个"条目存在但编号不对"的典型案例——重新编号即可修复。

---

### 3.3 评价指标覆盖矩阵

#### 3.3.1 排序精度指标组

| 指标 | 原始出处 | 当前引用状态 | 风险 |
|---|---|---|---|
| Precision@K | 信息检索基础指标，最早可追溯到 1960s Cranfield 实验 | 🟡 组合引用 [11,12,21] 中 [21] 正确（Gunawardana 2022 评价指标综述），[11] 条目错配（正文说 Herlocker 但条目是 Koren？不，[11]正文条目是 Herlocker 2004 评价指标——但正文引用[11]是在"Rendle提出BPR"处——又一处错配） | 🟠 |
| Recall@K | 同上 | 🟡 同上 | 🟠 |
| MAP@K | 信息检索经典指标 | 🟡 同上 | 🟠 |
| NDCG@K | Järvelin & Kekäläinen. "Cumulated gain-based evaluation of IR techniques." ACM TOIS, 2002 | 🟡 无单独引用 | 🟡 |
| MRR@K | 信息检索经典指标 | 🟡 无单独引用 | 🟡 |

**判定**：五个排序精度指标均属于推荐系统和信息检索领域的标准指标，单个引用出处不是必需的——使用评价指标综述（Gunawardana 2022 或 Herlocker 2004）统一覆盖即可。当前引用标记存在但条目错配严重，实际有效引用为 0。

---

#### 3.3.2 多样性与覆盖指标组

| 指标 | 原始出处 | 当前引用状态 | 风险 |
|---|---|---|---|
| ILS（列表内相似度） | Ziegler, McNee, Konstan, Lausen. "Improving recommendation lists through topic diversification." WWW, 2005 | 🔴 0 引用 | 🟡 |
| Coverage（覆盖率） | 推荐系统评估综述中标准指标 | 🔴 0 引用 | 🟡 |
| Tail Coverage（长尾覆盖率） | 同上 | 🔴 0 引用 | 🟡 |
| Novelty（新颖度） | 同上 | 🔴 0 引用 | 🟡 |
| Serendipity（惊喜度） | 同上 | 🔴 0 引用 | 🟡 |
| Genre Diversity（类型多样性） | 同上 | 🔴 0 引用 | 🟡 |

**判定**：六个多样性与覆盖指标全部没有引用。这些指标不如 Precision/Recall 那样"通用常识"，建议至少有一篇评价指标综述统一覆盖。实际风险低于排序精度指标（因为这些指标在论文中的分析权重较小），但仍应补充。

---

#### 3.3.3 统计检验方法

| 方法 | 原始出处 | 当前引用状态 | 风险 |
|---|---|---|---|
| Wilcoxon Signed-Rank 检验 | Wilcoxon. "Individual comparisons by ranking methods." Biometrics Bulletin, 1945 | 🔴 0 引用 | 🟠 |
| Bonferroni-Holm 校正 | Holm. "A simple sequentially rejective multiple test procedure." Scandinavian Journal of Statistics, 1979 | 🔴 0 引用 | 🟠 |
| Cohen's d 效应量 | Cohen. "Statistical power analysis for the behavioral sciences." 1988 | 🔴 0 引用 | 🟠 |

**判定**：三种统计方法全部没有文献来源。在实验章节中使用特定的统计检验方法但未注明出处，属于方法论层面的引用缺失。建议使用统计学教材或方法论文统一引用。

---

### 3.4 算法覆盖度总矩阵

| 算法/方法 | 原始论文 | 权威引用 | 中文引用 | 综述引用 | 整体风险 |
|---|---|---|---|---|---|
| ItemCF | 🔴 错配 | 🔴 错配 | ❌ | ❌ | 🔴 致命 |
| 调整余弦相似度 | 🔴 错配 | — | — | — | 🔴 致命 |
| TopK 截断 | 🔴 错配 | — | — | — | 🟠 高 |
| NCF | 🔴 错配 | 🔴 错配 | ❌ | 🟡 未引用 | 🔴 致命 |
| MLP 万能逼近 | 🔴 错配 | — | — | — | 🟠 高 |
| Hybrid/级联 | ✅ 正确 | ❌ | ❌ | ❌ | 🟢 低 |
| LightGCN | 🔴 **完全缺失** | ❌ | ❌ | ❌ | 🔴 致命 |
| EASE | 🔴 **完全缺失** | ❌ | ❌ | ❌ | 🔴 致命 |
| RBM 推荐 | 🔴 错配 | — | — | — | 🟠 高 |
| SVD++ | 🔴 错配 | — | — | — | 🟠 高 |
| PMF | 🔴 错配 | — | — | — | 🟠 高 |
| BPR | 🔴 错配 | — | — | — | 🟠 高 |
| Wide & Deep | 🔴 错配 | — | — | — | 🟠 高 |
| YouTube 架构 | ✅ 正确 | — | — | — | 🟢 无 |
| Precision/Recall/MAP | — | 🟡 错配 | — | 🟡 部分 | 🟠 高 |
| NDCG/MRR | — | ❌ | — | 🟡 部分 | 🟡 中 |
| ILS/Coverage/Novelty 等 | — | ❌ | — | ❌ | 🟡 中 |
| Wilcoxon 检验 | ❌ | — | — | — | 🟠 高 |
| Bonferroni-Holm | ❌ | — | — | — | 🟠 高 |
| Cohen's d | ❌ | — | — | — | 🟠 高 |

**统计**：
- 🔴 致命（5 项）：ItemCF、NCF、LightGCN、EASE、调整余弦相似度
- 🟠 高（8 项）：TopK、MLP 万能逼近、RBM、SVD++、PMF、BPR、Wide & Deep、三统计方法
- 🟡 中（2 项）：NDCG/MRR、多样性与覆盖指标
- 🟢 无风险（2 项）：YouTube 架构、Hybrid/级联

---

## 模块四：系统设计覆盖度审计

### 4.1 审计原则

系统设计相关内容的引用判定遵循以下原则：

| 情况 | 是否需要引用 |
|---|---|
| 使用开源框架/工具的 API 完成工程任务 | ❌ 不需要。这是框架的正常使用 |
| 介绍框架/工具的底层原理或算法 | ✅ 需要。如果论文深入讨论了 MySQL 的 B+Tree 索引原理，需要引用数据库教材 |
| 提出新的架构模式或设计范式 | ✅ 需要。如果是独创的设计需要声明，否则引用已有工作 |
| 架构选型的理由陈述（如"选择 A 而非 B 因为 C"） | ⚠️ 视情况。如果引用了他人的对比研究结论，需要引用；如果是本文的分析，不需要 |
| 数据库表结构、API 路由、前端组件 | ❌ 不需要。这些是本文的实现产出 |

### 4.2 逐模块审计

#### 4.2.1 Flask 应用工厂

论文内容：使用 Flask 应用工厂模式、Blueprint 路由组织、Jinja2 模板引擎、Flask-Login 认证。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | Flask 是开源 Web 框架。论文使用的是其标准功能（create_app、Blueprint、Jinja2、Flask-Login），不涉及对框架原理的深入讨论或改进。 |

#### 4.2.2 Vue.js 3 前端

论文内容：Vue.js 3 Options API、组件系统（MovieCard/SkeletonGrid/StarRating 等）、CDN 引入方式。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | Vue.js 是开源前端框架。论文使用其标准 API，组件是自行开发的。论文提到"选择了 CDN 引入而非 Webpack/Vite 构建"是本文的工程决策，不是外部知识。 |

#### 4.2.3 MySQL 与 SQLAlchemy ORM

论文内容：14 张数据表设计、联合唯一约束、索引设计、Alembic 迁移管理。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | 数据库设计是本文的工程产出。SQLAlchemy 和 Alembic 是开源工具的标准使用。论文提到了"读写走同一个连接池，连接数上限设 10"是本文的配置决策。 |

#### 4.2.4 ECharts 与数据可视化

论文内容：评分分布柱状图、类型占比玫瑰图、年份趋势折线图、旭日图、日历热力图。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | ECharts 是开源可视化库。所有图表配置均由本文编写。论文提到的"旭日图 children 嵌套结构要求数据格式严格匹配"是本文的开发经验，不是外部文献。 |

#### 4.2.5 PyTorch 与 scikit-learn

论文内容：NCF 模型用 PyTorch 实现、ItemCF 相似度用 scikit-learn NearestNeighbors 计算。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | PyTorch 和 scikit-learn 是开源机器学习框架。论文使用的是其标准 API（nn.Embedding、nn.Linear、NearestNeighbors），不涉及框架改进。 |

#### 4.2.6 Flask-Caching (SimpleCache) 缓存策略

论文内容：使用 SimpleCache 内存缓存，选择理由为"本地单机部署没必要上 Redis"。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | 这是本文的设计决策叙述。缓存策略的比较（内存 vs Redis）是工程常识，不需要引用。 |

#### 4.2.7 structlog 日志

论文内容：结构化 JSON 日志、请求日志中间件。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | structlog 是开源日志库的标准使用。 |

#### 4.2.8 Pydantic BaseSettings 配置管理

论文内容：配置加载、类型校验、@lru_cache 单例。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | Pydantic 是开源配置库的标准使用。 |

#### 4.2.9 CSS Grid 自适应布局 + 骨架屏 + 懒加载

论文内容：grid-template-columns: auto-fill、SkeletonGrid 动画、img loading="lazy"。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | 这些是 Web 前端开发的通用技术，属于工程实现。 |

#### 4.2.10 werkzeug 密码哈希

论文内容：generate_password_hash / check_password_hash 加盐哈希。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | werkzeug 是 Flask 生态的标准工具库。论文提到了"加盐哈希"是安全常识，不需要引用。 |

#### 4.2.11 TMDB API 元数据补充

论文内容：通过 TMDB API 补充电影海报、导演、演员、剧情简介。

| 是否需要引用 | 理由 |
|---|---|
| ❌ | TMDB 是公开 API，论文使用它获取数据，属于数据采集的工程操作。 |

### 4.3 可能被质疑"需要引用"但实际上不需要的案例

以下是外审中可能被问到"这个有文献支撑吗"的情况，以及如何回应：

| 质疑 | 回应 |
|---|---|
| "Flask 应用工厂模式有什么文献依据？" | "这是 Flask 官方文档推荐的模式，属于框架的标准使用方式，不是本文提出的新架构模式。" |
| "MySQL 的索引设计有没有参考数据库教材？" | "索引设计（联合唯一约束、覆盖索引）是数据库课程的常规知识。本文的索引方案是为本系统数据访问模式量身设计的，不是从特定论文中引用的。" |
| "SimpleCache vs Redis 的选择有没有性能对比文献？" | "这是针对本文部署场景（本地单机）的工程判断，不是基于他人研究成果的选择。本文没有声称 SimpleCache 在性能上优于 Redis。" |

### 4.4 系统设计覆盖度总评

| 模块 | 数量 | 需要引用 | 实际引用 | 缺失 |
|---|---|---|---|---|
| Web 框架（Flask/Vue） | 2 | 0 | 0 | 0 |
| 数据库（MySQL/SQLAlchemy） | 2 | 0 | 0 | 0 |
| 可视化（ECharts） | 1 | 0 | 0 | 0 |
| ML 框架（PyTorch/scikit-learn） | 2 | 0 | 0 | 0 |
| 缓存/日志/配置 | 3 | 0 | 0 | 0 |
| 前端技术（CSS Grid/懒加载/骨架屏） | 3 | 0 | 0 | 0 |
| 安全（werkzeug 密码哈希） | 1 | 0 | 0 | 0 |
| 外部 API（TMDB） | 1 | 0 | 0 | 0 |
| **总计** | **15** | **0** | **0** | **0** |

**结论**：论文的系统设计部分不存在引用缺失。全部 15 个模块均属于开源工具的标准使用或本文的设计决策，在学术规范上不需要外部文献引用。**外审中不会因为"系统设计没有文献支撑"而被扣分。**
