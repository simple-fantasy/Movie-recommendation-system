# 第4章 系统设计

## 4.1 系统总体架构设计

本系统采用经典的三层Web应用架构，分为表示层、业务逻辑层和数据持久层。系统架构如图4-1所示。

（1）**表示层（Presentation Layer）**：由Jinja2模板引擎和Vue.js 3协同构成。Jinja2负责服务端渲染页面初始结构，Vue.js处理客户端的动态交互逻辑。Bootstrap 5提供响应式UI组件，ECharts承担数据可视化任务。

（2）**业务逻辑层（Business Logic Layer）**：基于Flask应用工厂模式构建。核心组件包括：路由处理器（routes.py和admin_routes.py，共计70余个API端点）、推荐引擎（ItemCF召回模块和NCF推理引擎）、用户画像服务（ProfileService）、行为追踪模块（BehaviorTracker），以及配置管理、缓存管理、限流控制、日志记录等支撑模块。

（3）**数据持久层（Data Persistence Layer）**：通过SQLAlchemy ORM实现数据库操作的对象化抽象，支持MySQL和SQLite双后端。19张数据表覆盖用户、电影、评分、相似度、评论、收藏、影单、通知、行为日志、用户画像等业务域。

关键的设计决策遵循以下原则：

（1）**关注点分离**：前端每个页面对应独立的page-*.js文件和一个Jinja2模板文件，后端路由按功能域组织在routes.py中，数据库模型集中在models.py中。

（2）**配置外部化**：所有配置项通过Pydantic BaseSettings从.env文件加载，支持类型校验和范围验证，避免硬编码。

（3）**优雅降级**：NCF模型通过异步加载和状态检查机制实现优雅降级——模型加载中返回503重试提示，加载失败时自动回退到ItemCF策略。

（4）**单例管理**：NCFEngine采用线程安全的单例模式，确保模型在内存中只加载一份，通过lock机制保护加载状态的并发安全。

## 4.2 数据库设计

### 4.2.1 核心业务表设计

系统数据库共包含19张表，以下为各表的核心字段和设计说明：

**用户表（users）**：存储用户账户信息。核心字段包括id（主键）、username（唯一索引）、password_hash（werkzeug哈希加密存储）、email、avatar、is_admin（管理员标识）、is_active（账户状态）、last_login、login_count、created_at。其中password_hash采用werkzeug.security.generate_password_hash()进行加盐哈希，不在数据库中存储明文密码。

**电影表（movies）**：存储电影元数据。核心字段包括id、title、year、genres（竖线分隔的多值字段）、original_title、director、actors（JSON存储）、description、runtime、poster_url、backdrop_url、trailer_url、tagline、tmdb_id、imdb_id、language、country。管理字段包括status
（active/inactive/pending）、is_featured、view_count、rating_count、avg_rating。actors字段以JSON格式存储演员列表，通过get_actors_list()和set_actors_list()方法进行序列化/反序列化。

**评分表（ratings）**：存储用户对电影的评分记录。核心字段包括id、user_id、movie_id、rating（0.5-5.0）、timestamp。表上建有(user_id, movie_id)唯一约束、(user_id, timestamp)复合索引和(movie_id, rating)复合索引，分别优化用户历史查询和电影评分统计。

**电影相似度表（movie_similarity）**：存储ItemCF预计算的电影相似度对。核心字段包括id、movie_id、similar_movie_id、score。建有(movie_id, similar_movie_id)唯一约束和(movie_id, score)复合索引，优化"查询某电影最相似电影列表"这一高频操作。

### 4.2.2 社交功能表设计

**评论表（reviews）**：存储用户对电影的评论。核心字段包括id、user_id、movie_id、content、rating、likes_count、is_featured、status（approved/rejected/pending）、created_at、updated_at。

**评论点赞表（review_likes）**：存储用户对评论的点赞记录，通过(user_id, review_id)唯一约束防止重复点赞。

**收藏表（user_collections）**：存储用户的电影收藏记录。核心字段包括id、user_id、movie_id、collection_type（favorite/watchlist/seen）、notes、rating。通过(user_id, movie_id, collection_type)唯一约束支持同一用户将同一电影加入不同类型的收藏。

**影单表（movie_lists）**：存储用户创建的电影合集。核心字段包括id、user_id、name、description、cover_image、is_public、is_featured、view_count、like_count、comment_count。

**影单项表（movie_list_items）**：存储影单中的电影条目，通过(movie_list_id, movie_id)唯一约束和order字段支持排序。

### 4.2.3 其他辅助表设计

**通知表（notifications）**：存储用户通知。核心字段包括id、user_id、type（system/review_reply/review_liked/movie_recommend/achievement）、title、content、related_id、is_read、created_at、read_at。

**用户画像表（user_profiles）**：存储用户的偏好和行为分析数据。核心字段包括user_id（唯一）、preferred_genres（JSON）、preferred_years（JSON）、preferred_actors（JSON）、preferred_directors（JSON）、avg_rating_level、rating_variance、rating_entropy、total_watch_time、genre_diversity、decade_diversity、user_type、activity_level。

**用户行为表（user_behaviors）**：存储用户行为日志。核心字段包括id、user_id、action_type（view/rate/search/click）、target_type、target_id、extra_data（JSON）、ip_address、user_agent、session_id、referrer、created_at。

## 4.3 推荐算法设计

本系统的推荐算法设计围绕三个核心策略展开：ItemCF、NCF和Hybrid混合推荐。以下分别阐述各策略的详细设计。

### 4.3.1 ItemCF算法设计

ItemCF算法的设计流程分为离线训练和在线推理两个阶段。

**离线训练阶段**的步骤如下：

（1）从评分表中加载全量评分数据，构建DataFrame。

（2）执行数据过滤：按照min_ratings_per_movie（默认50）过滤冷门电影，按照min_ratings_per_user（默认5）过滤不活跃用户。

（3）执行用户均值归一化：对每位用户，将其所有评分减去该用户的评分均值，消除用户评分尺度偏差。归一化后评分为负值表示该用户对该电影的评分低于其平均水平。

（4）构建电影×用户评分矩阵：使用pandas.factorize将用户ID和电影ID映射为连续整数索引，然后通过scipy.sparse.coo_matrix构建稀疏矩阵，转换为CSR格式以优化行向量访问。

（5）训练最近邻模型：使用scikit-learn的NearestNeighbors，以余弦距离（cosine）为度量，brute算法进行检索，为每部电影找到topk（默认50）个最相似电影。

（6）相似度存储：将距离转换为相似度分数（1-distance），过滤掉非正相似度，批量写入movie_similarity表。

**在线推理阶段**的流程如下：

（1）获取当前用户的全部评分记录和已评分电影ID集合。

（2）批量查询所有已评分电影的相似电影列表（单次SQL查询获取所有相似度，使用IN子句，避免N+1查询问题）。

（3）按用户已评分电影分组相似度，每组取Top-50，在计算分数时过滤已评分电影。

（4）对每部候选电影，累加所有已评分电影的分数贡献（相似度×原评分），选取总分最高的Top-N部电影。

（5）生成推荐解释：对于每部推荐电影，回溯贡献最大的3部种子电影，返回"因为你喜欢X"的解释信息。

### 4.3.2 NCF算法设计

NCF算法同样分为训练和推理两个阶段。

**训练阶段**的步骤如下：

（1）数据加载：按用户分组加载评分数据，按交互时间排序后，采用Leave-Last-Out策略划分训练集和验证集（每个用户最后10%的交互作为验证集）。

（2）ID映射：将原始的用户ID和电影ID映射为从0开始的连续整数索引，构建user2idx和item2idx字典。

（3）负采样：训练时每个batch采样batch_size个正样本，以及batch_size×neg_ratio个负样本（随机采样用户未交互的电影）。使用碰撞检测重采样机制确保负样本不与正样本重合。

（4）模型结构：NCF模型由Embedding层和MLP层组成。用户和物品各通过维度为embedding_dim（默认32）的嵌入层映射为稠密向量。两个向量拼接后通过三层MLP：[2×embedding_dim → hidden_dim → hidden_dim/2 → 1]，每层间使用ReLU激活函数。

（5）训练配置：使用Adam优化器，BCEWithLogitsLoss损失函数，batch_size为4096。采用早停机制（patience=3），监控验证集NDCG@K指标。

（6）验证评估：验证时对每个用户采样100个负样本（不包含该用户的任何交互物品），与真实正样本组合后排序，计算HR@K和NDCG@K。

（7）模型保存：训练完成后保存模型参数（ncf.pt）和元数据（ncf_meta.json），包括user2idx、item2idx、模型配置等。

**推理阶段**：NCFEngine作为全局单例管理模型的生命周期。使用异步加载机制，在后台线程加载模型参数和映射表，不阻塞Web服务启动。推理时提供两个核心接口：score(user_id, item_ids)对候选物品批量评分，rank(user_id, item_ids, top_k)返回Top-K排序结果。

### 4.3.3 Hybrid混合推荐设计

Hybrid策略采用级联架构，将ItemCF作为召回阶段、NCF作为排序阶段：

（1）ItemCF召回：利用预计算的相似度表，从全量电影中检索recall_k（默认100）部候选电影。召回结果以(item_id, score)形式返回。

（2）NCF排序：检查NCFEngine状态（是否加载完成、当前用户是否在训练集中）。若可用，则将候选电影列表送入NCF进行重新评分排序，输出top_n推荐结果。

（3）推荐理由生成：由于NCF本身不提供可解释的中间结果，Hybrid策略的推荐理由沿用ItemCF阶段的相似度贡献信息，即对于最终推荐结果中的电影，展示ItemCF回溯到的贡献来源电影。

（4）降级策略：若NCF正在加载中（返回503状态码）、NCF加载失败，或当前用户不在NCF训练集中，系统自动降级为纯ItemCF推荐。

## 4.4 前端界面设计

系统前端采用服务端渲染与客户端交互结合的混合架构，设计上注重以下几点：

（1）**页面布局**：所有页面继承自base.html模板，该模板提供统一的导航栏、页脚和CSS框架引入。页面主体区域通过{% block content %}进行内容填充。

（2）**组件化设计**：每个功能页面对应一个Vue.js应用，通过CDN引入Vue 3并使用Options API。所有API调用封装在api.js公共模块中，提供get、post、put、delete方法，自动处理CSRF和安全请求头。

（3）**响应式设计**：基于Bootstrap 5的栅格系统实现响应式布局，适配桌面端和移动端。电影卡片、影单展示等核心组件均使用flexbox布局实现自适应。

（4）**数据可视化**：看板页面使用ECharts实现评分分布、类型分布、年份趋势、系统概览等图表。增强看板增加用户分群、活动热力图等高级分析图表。图表数据通过异步API请求获取，支持动态刷新。

（5）**视觉风格**：采用深色电影主题（CSS变量定义色彩体系），使用glass-morphism（毛玻璃效果）、渐变背景、微动画（GSAP驱动）等设计手法营造现代电影平台的视觉效果。
