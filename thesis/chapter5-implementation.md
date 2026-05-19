# 第5章 系统实现

## 5.1 开发环境

本系统的开发环境和依赖如下：

（1）**编程语言**：Python 3.10。选择Python的原因是其丰富的科学计算和Web开发生态，NumPy、Pandas、scikit-learn、PyTorch、Flask等库提供了完整的推荐系统开发链路。

（2）**Web框架**：Flask 3.0 + Flask-SQLAlchemy + Flask-Login + Flask-Caching。Flask的轻量级设计适合中小型Web应用，其应用工厂模式便于模块化组织和测试。

（3）**数据库**：MySQL 8.0（主数据库）+ PyMySQL驱动；SQLite 3（开发备选）。使用Alembic进行数据库迁移管理。

（4）**科学计算库**：NumPy 1.24+（矩阵运算）、Pandas 2.0+（数据处理）、scikit-learn 1.3+（近邻搜索）、SciPy 1.11+（稀疏矩阵）。

（5）**深度学习框架**：PyTorch 2.0+。使用CPU模式（--device cpu）进行训练和推理，在有GPU的环境中可切换为CUDA模式。

（6）**前端库**：Vue.js 3（CDN引入）、Bootstrap 5.3、ECharts 5.4、GSAP 3.12。

（7）**其他依赖**：Pydantic（配置管理）、structlog（结构化日志）、TMDB API v3（元数据补充）。

## 5.2 核心功能模块实现

### 5.2.1 应用工厂与配置管理

系统的入口通过create_app()工厂函数构建Flask应用实例。该函数按以下步骤初始化系统：

（1）设置Jinja2环境为ChainableUndefined，允许Vue.js的{{ }}插值表达式与Jinja2模板语法共存。

（2）从Config类加载配置项，设置Session Cookie参数（SameSite=Lax、HttpOnly=True、有效期1天）。

（3）初始化三个核心扩展：SQLAlchemy（数据库ORM）、LoginManager（用户认证）、Flask-Caching（SimpleCache内存缓存，默认5分钟过期）。

（4）注册两个蓝图：main蓝图（用户端路由，70余个端点）和admin蓝图（管理后台路由，20余个端点）。

（5）注册全局中间件：错误处理器、请求日志记录中间件和限流中间件。

（6）在应用上下文中创建所有数据库表，执行种子数据填充（首次启动时自动插入20部样本电影和demo用户），并在后台线程异步进行TMDB海报补充和NCF模型预加载。

### 5.2.2 用户认证实现

用户认证基于Flask-Login扩展实现。用户模型继承UserMixin，提供is_authenticated、is_active等标准属性。密码通过werkzeug.security.generate_password_hash()进行加盐哈希存储，验证时使用check_password_hash()。

注册接口（POST /api/auth/register）接收username、password和confirm参数，进行以下校验：用户名长度2-64字符、密码长度≥6字符、两次密码输入一致、用户名未被占用。校验通过后创建User记录并自动登录。

登录接口（POST /api/auth/login）接收username和password，验证成功后调用login_user()创建Session，并更新用户的last_login和login_count字段。对于API请求（/api/前缀），未登录时返回JSON格式的401错误，而非HTML重定向——这一设计确保前端Vue.js能正确处理认证失败的情况。

管理员权限通过is_admin字段标识。@admin_required装饰器（定义在decorators.py中）在路由处理前检查current_user.is_admin，非管理员请求返回403。

### 5.2.3 推荐API实现

推荐API（GET /api/recommendations）是整个系统的核心接口。它接受三个参数：n（推荐数量，默认10）、strategy（推荐策略）、recall_k（Hybrid召回数量，默认100）。

对于未登录用户或评分记录为空的用户（冷启动），系统调用popular_movies()逻辑返回高评分电影兜底：查询平均评分≥4.0且评分数量≥50的电影，按评分和热度排序。

ItemCF策略的流程：调用_itemcf_recall()函数，该函数批量查询用户所有已评分电影的相似电影列表（使用IN子句减少数据库查询次数），然后按已评分电影分组，对每组相似电影取Top-50，过滤已评分电影，累加分数贡献，返回Top-N推荐结果。_format_recommendations()函数负责将推荐结果格式化为包含电影详情、推荐分数和推荐理由（because字段）的JSON响应。

NCF策略的流程：检查NCFEngine状态（is_loading返回503提示重试，is_ready检查模型是否加载完成），确认用户是否在NCF训练集中（不在则降级为ItemCF），从热门未评分电影中选取500部作为候选集，调用NCFEngine.rank()进行排序，返回Top-N结果。

Hybrid策略的流程：先以recall_k参数调用ItemCF进行召回，然后检查NCFEngine可用性。若可用，将召回结果送入NCF重新排序；若不可用，直接将ItemCF召回结果截取Top-N返回。推荐理由沿用ItemCF的贡献信息。

### 5.2.4 推荐解释实现

推荐解释通过/api/recommendations/why/<movie_id>端点实现。该端点接收被推荐电影ID，查询当前用户所有已评分电影中哪些与被推荐电影存在相似度关系。对于每部贡献来源电影，计算其贡献权重（相似度×用户评分），按权重降序排列，返回Top-3作为推荐理由。推荐结果中的because字段包含{movie_id, title, weight}三元组，前端据此展示"因为你喜欢《X》"的解释。

### 5.2.5 用户画像实现

用户画像计算由ProfileService服务类实现，包含12个计算方法。compute_user_profile(user_id)方法整合了全部画像计算逻辑：

（1）偏好类型计算：遍历用户评分和收藏记录，对每部电影的genres字段进行拆分和累加，以评分加权统计各类型的偏好分数，归一化后过滤掉分数低于0.3的类型。

（2）偏好年代计算：将电影年份映射为年代标签（如1990s），以相同的评分加权方式统计年代偏好，归一化后过滤。

（3）评分行为分析：计算平均评分水平、评分方差（反映评分一致性）和评分熵（反映评分散度）。

（4）用户分层：根据总操作次数（评分+收藏+评论）将用户分为casual（<10次）、regular（10-49次）、enthusiast（≥50次）。活跃度分为low（<20次）、medium（20-99次）、high（≥100次）。

（5）观影洞察：基于画像数据自动生成最多5条个性化洞察描述，如"您最喜欢Drama类型的电影"、"您的观影类型非常丰富"等，前端通过get_user_insights()方法获取并展示。

### 5.2.6 行为追踪实现

行为追踪模块在behavior_tracker.py中实现。通过@track_behavior装饰器和record_behavior_async()异步记录函数，在不阻塞主请求流程的前提下记录用户行为。行为记录包括操作类型（view/rate/search/click）、目标类型和目标ID、请求元数据（URL、参数、Referrer）、会话ID等。

行为记录采用异步保存策略：在独立的后台线程中执行数据库写入，避免对用户请求响应时间的影响。同时提供get_user_behavior_summary()和get_behavior_analytics()函数，分别用于单用户行为摘要和全站行为分析。

## 5.3 推荐算法实现

### 5.3.1 ItemCF训练实现

ItemCF训练脚本位于backend/scripts/train_itemcf.py，接受以下关键参数：

（1）--min-ratings-per-movie（默认50）：电影最少评分数量，低于此阈值的电影被过滤。

（2）--min-ratings-per-user（默认5）：用户最少评分数量，低于此阈值的用户被过滤。

（3）--normalize（默认启用）：是否对评分进行用户均值归一化。

（4）--topk（默认50）：每部电影保留的最近邻居数量。

训练流程的核心步骤包括：使用pandas.factorize()将用户ID和电影ID映射为连续整数索引；使用scipy.sparse.coo_matrix构建稀疏评分矩阵（行为电影、列为用户）；使用sklearn.neighbors.NearestNeighbors以余弦距离进行最近邻搜索；将距离转换为相似度分数后进行批量数据库写入。

在大规模数据集（32M条评分）上，数据过滤后的结果约为：过滤后保留约数万部电影、数十万用户、数百万条评分，矩阵稀疏度约为0.5%-2%，训练时间取决于过滤后的数据规模。

### 5.3.2 NCF训练实现

NCF训练脚本位于backend/scripts/train_ncf.py。关键参数包括embedding_dim（默认32）、hidden_dim（默认64）、batch_size（默认4096）、epochs（默认5）、neg_ratio（负采样比例，默认1）、min_ratings_per_user（默认10）、user_mod（用户采样模数，用于控制训练用户数量）等。

训练流程的核心步骤包括：

（1）**数据加载**：load_interactions()函数从数据库按用户分组加载评分数据，按时间排序后对每个用户进行Leave-Last-Out划分（最后10%交互作为验证集），构建训练对和验证对数组。

（2）**负采样**：train_one()函数在每个epoch中随机采样batch_size个正样本，并通过sample_negatives_column()函数为每个正样本采样neg_ratio个负样本。负采样使用碰撞检测重采样机制——若采样到的负样本恰好是该用户的正样本，则重新采样，最多重试48次。

（3）**训练循环**：每个epoch执行steps_per_epoch = n_pos / batch_size个训练步。每个step中：采样batch数据、前向传播计算logits、计算BCEWithLogitsLoss、反向传播更新参数。每个epoch结束后在验证集上计算HR@K和NDCG@K。

（4）**早停与验证**：采用patience=3的早停策略，监控NDCG@K指标。验证时使用sample_eval_negs_row()为每个验证样本采样100个负样本（排除用户所有交互物品），计算HR@K（命中率）和NDCG@K（归一化折损累计增益）。

（5）**模型导出**：将最优模型的state_dict保存为ncf.pt文件，同时将user2idx、item2idx、idx2item映射表和模型配置保存为ncf_meta.json文件。两个文件统一存放在backend/artifacts/目录下。

### 5.3.3 推荐效果评估实现

评估脚本位于backend/scripts/evaluate_models.py，支持的模型包括itemcf、ncf、hybrid三种，以及消融实验模式。

评估协议采用Leave-Last-Out：对每个用户，按时间排序后取最后一次≥4.0分的交互作为测试样本，其余作为训练历史。评估指标包括：

（1）Precision@K（精确率） = 推荐列表中命中测试样本的数量 / K

（2）Recall@K（召回率） = 推荐列表中是否命中测试样本（单样本情况下等于0或1）

（3）MAP@K（平均精度均值） = 1 / (命中位置+1)

（4）NDCG@K（归一化折损累计增益） = 1 / log₂(命中位置+2)（命中时）

（5）MRR@K（平均倒数排名） = 1 / (命中位置+1)

此外还统计推荐覆盖率（Coverage，被推荐物品占全量物品的比例）和平均对数流行度（Avg Log Popularity）。

消融实验包括两个维度：（1）Hybrid策略在不同recall_k（50/100/200/500）下的性能变化；（2）ItemCF策略在不同per_seed_limit（10/25/50/100）下的性能变化。评估结果以JSON格式保存至backend/artifacts/evaluation_results.json。

## 5.4 前端实现

### 5.4.1 推荐页面实现

推荐页面（recommendations.html）是系统的核心前端页面。页面通过Vue.js 3管理状态，提供以下交互功能：

（1）**策略切换**：通过三个Tab按钮切换ItemCF、NCF、Hybrid策略，切换时自动重新请求推荐数据。

（2）**推荐展示**：使用CSS Grid网格布局展示推荐电影卡片。每张卡片显示电影海报、标题、年份、类型、平均评分和推荐分数。卡片具有hover动画效果。

（3）**推荐理由**：在ItemCF和Hybrid模式下，每张推荐卡片下方展示"因为你喜欢X"的推荐来源信息，通过because数据渲染。

（4）**评分交互**：用户可以直接在推荐卡片上进行星级评分（0.5-5.0），评分后立即更新本地状态。

（5）**反馈机制**：每个推荐结果提供喜欢/不喜欢按钮，点击后向/api/feedback发送反馈数据，用于后续推荐优化。

### 5.4.2 数据看板实现

增强看板页面（enhanced_dashboard.html）集成多个ECharts图表：

（1）**系统概览卡片**：展示总用户数、总电影数、总评分数、活跃用户数四个核心指标，通过动画数字效果呈现。

（2）**评分分布图**：使用ECharts柱状图展示0.5-5.0各评分值的分布情况。

（3）**类型分布图**：使用ECharts饼图（环形图）展示各电影类型的评分数量占比，支持Top-N展示。

（4）**年份趋势图**：使用ECharts折线-柱状混合图展示不同年份电影的评分数量和平均评分变化趋势。

（5）**用户分群图**：使用ECharts旭日图展示用户类型（casual/regular/enthusiast）的分布结构。

（6）**活动热力图**：使用ECharts日历热力图展示每日用户活跃度，颜色深浅反映活跃程度。

所有图表数据通过异步API请求获取，图表配置支持响应式窗口变化自动调整。

### 5.4.3 公共API模块实现

api.js模块封装了所有前端API请求，提供统一的请求处理逻辑：

（1）自动在请求头中添加CSRF Token（从cookie中读取）。

（2）请求超时设置为30秒。

（3）统一的错误处理：401错误跳转登录页，403提示权限不足，5xx提示服务器错误。

（4）支持GET、POST、PUT、DELETE四种HTTP方法，参数自动进行JSON序列化。

（5）推荐相关的API调用（getRecommendations、submitRating、submitFeedback等）均通过此模块进行。
