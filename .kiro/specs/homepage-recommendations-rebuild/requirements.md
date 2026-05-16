# 需求文档

## 引言

### 项目背景

CineMatch 是一个基于 Flask + Vue 3 的电影推荐系统，后端 API 已完整实现。现有的主页（`/app`）和推荐页面（`/recommendations`）前端代码存在大量 bug，导致用户体验不佳。本次任务是完全重建这两个核心页面的前端实现，不修复旧代码，而是从零编写新的、可靠的前端代码。

### 重建目标

1. **主页（`/app`）**：重建为一个功能完整、无 bug 的电影主页，包含 Hero 展示区、个性化推荐行、热门高分行、实时搜索、我的评分行、用户画像图表、快速评分弹窗和游客引导区。
2. **推荐页（`/recommendations`）**：重建为一个清晰、无 bug 的推荐页面，包含策略切换器、推荐结果网格、骨架屏加载态、错误重试和空状态处理。

### 设计原则

- **简洁可靠**：优先保证功能正确，不追求复杂动画
- **错误隔离**：每个数据区块独立加载，一个失败不影响其他
- **认证安全**：所有需要登录的功能，未登录时优雅降级
- **复用现有组件**：使用 `window.CinemaComponents` 中的组件，不重复造轮子
- **内联 Script**：JS 逻辑写在 `{% block extra_js %}` 中，不创建新的 JS 文件

---

## 术语表

- **CineMatch_System**：整个电影推荐系统，包含前端页面和后端 API
- **Homepage**：主页，路由为 `/app`，对应模板文件 `app.html`
- **RecommendationsPage**：推荐页面，路由为 `/recommendations`，对应模板文件 `recommendations.html`
- **Hero_Section**：页面顶部的大图展示区，包含精选电影的背景图、标题、简介和操作按钮
- **MovieRow**：横向可滚动的电影卡片行，使用 `window.CinemaComponents.MovieRow` 组件
- **MovieCard**：单个电影海报卡片，使用 `window.CinemaComponents.MovieCard` 组件
- **StarRating**：星级评分组件，使用 `window.CinemaComponents.StarRating` 组件
- **RateModal**：快速评分弹窗，使用 Bootstrap Modal 实现
- **PersonaChart**：类型偏好雷达图，使用 ECharts 渲染
- **TimelineChart**：观影时间线图，使用 ECharts 渲染
- **StrategySelector**：推荐策略切换器，包含热门高分、ItemCF、NCF、混合推荐四个选项
- **RecommendationGrid**：推荐结果网格，4 列响应式布局
- **SkeletonCard**：骨架屏占位卡片，加载时显示
- **AuthUser**：已认证的登录用户
- **GuestUser**：未登录的游客用户
- **PopularStrategy**：热门高分推荐策略，调用 `/api/movies/popular`，无需登录
- **ItemCFStrategy**：基于物品协同过滤推荐策略，调用 `/api/recommendations?strategy=itemcf`，需登录且有评分历史
- **NCFStrategy**：神经网络协同过滤推荐策略，调用 `/api/recommendations?strategy=ncf`，需登录且模型已加载
- **HybridStrategy**：混合推荐策略，调用 `/api/recommendations?strategy=hybrid`，需登录且模型已加载
- **FeaturedMovie**：Hero 区展示的精选电影，从热门电影中随机选取
- **Feedback**：用户对推荐结果的点赞/踩反馈，调用 `/api/feedback`
- **Debounce**：防抖处理，搜索输入时延迟触发 API 调用
- **NormalizeMovie**：标准化电影对象的工具函数 `normalizeMovie(raw)`，处理后端字段名差异
- **Toast**：页面右下角的临时通知提示，使用 `showToast(message, type)` 函数

---

## 需求


### 需求 1：认证状态初始化

**用户故事：** 作为页面访问者，我希望页面能正确识别我的登录状态，以便根据我是否登录来显示不同的内容和功能。

#### 验收标准

1. WHEN 页面加载时，THE Homepage SHALL 通过 `window._authPromise` 获取当前用户认证状态，若 `_authPromise` 不可用则回退调用 `GET /api/me`
2. WHEN `GET /api/me` 返回 `{authenticated: true}` 时，THE Homepage SHALL 将用户对象存储在 Vue 实例的 `user` 属性中
3. WHEN `GET /api/me` 返回 `{authenticated: false}` 或请求失败时，THE Homepage SHALL 将 `user` 属性设为 `null`，不显示任何错误提示
4. THE RecommendationsPage SHALL 使用与 Homepage 相同的认证初始化逻辑
5. WHILE 认证状态为 `null`（未登录），THE Homepage SHALL 隐藏所有需要登录的功能区块（我的评分行、用户画像区）
6. WHILE 认证状态为 `null`（未登录），THE Homepage SHALL 显示游客引导区（登录 CTA）

---

### 需求 2：主页 Hero 展示区

**用户故事：** 作为访问者，我希望在主页顶部看到一部精选电影的大图展示，以便快速了解当前热门内容并进行操作。

#### 验收标准

1. WHEN 主页加载时，THE Homepage SHALL 调用 `GET /api/movies/popular?limit=5` 获取热门电影列表
2. WHEN 热门电影列表返回成功时，THE Homepage SHALL 从列表中随机选取一部电影作为 FeaturedMovie
3. WHEN FeaturedMovie 被选定后，THE Homepage SHALL 调用 `GET /api/movies/{id}` 获取该电影的完整详情（包含 backdrop、overview 等字段）
4. THE Hero_Section SHALL 使用 FeaturedMovie 的 `backdrop` 字段（优先）或 `poster` 字段作为背景图，并应用 `brightness(0.45)` 滤镜
5. THE Hero_Section SHALL 显示 FeaturedMovie 的标题（经 `formatMovieTitle` 处理）、年份、平均评分、简介（最多 600px 宽）
6. THE Hero_Section SHALL 包含"查看详情"按钮，点击后跳转至 `/movie/{id}`
7. THE Hero_Section SHALL 包含"快速评分"按钮，点击后打开 RateModal
8. IF `GET /api/movies/popular` 请求失败，THEN THE Homepage SHALL 在 Hero_Section 显示默认欢迎文案（"欢迎来到 CineMatch"），不显示错误 Toast
9. WHILE FeaturedMovie 数据加载中，THE Hero_Section SHALL 显示骨架屏占位

---

### 需求 3：主页"为你推荐"行

**用户故事：** 作为登录用户，我希望在主页看到个性化推荐电影行；作为游客，我希望看到热门电影并被引导登录。

#### 验收标准

1. WHEN 主页加载时，THE Homepage SHALL 调用 `GET /api/recommendations?n=20` 获取推荐列表
2. WHEN 推荐列表返回成功时，THE Homepage SHALL 使用 MovieRow 组件渲染"为你推荐"行，显示最多 20 部电影
3. WHEN `GET /api/recommendations` 返回 HTTP 401 时，THE Homepage SHALL 将"为你推荐"行的 `emptySubtext` 设为"登录并评分电影以获取个性化推荐"，不显示错误 Toast
4. IF `GET /api/recommendations` 返回非 401 错误，THEN THE Homepage SHALL 显示 Toast 提示"推荐加载失败，请稍后重试"
5. WHILE 推荐数据加载中，THE MovieRow 组件 SHALL 显示 6 个骨架屏占位卡片（通过 `:loading="true"` prop 控制）
6. WHEN 用户点击推荐行中的电影卡片时，THE Homepage SHALL 跳转至 `/movie/{id}`
7. WHEN 用户点击推荐行中的评分按钮时，THE Homepage SHALL 打开 RateModal

---

### 需求 4：主页"热门高分"行

**用户故事：** 作为访问者，我希望在主页看到当前热门高分电影，以便发现值得观看的电影。

#### 验收标准

1. WHEN 主页加载时，THE Homepage SHALL 调用 `GET /api/movies/popular?limit=20` 获取热门电影列表
2. WHEN 热门电影列表返回成功时，THE Homepage SHALL 使用 MovieRow 组件渲染"热门高分"行，显示最多 20 部电影
3. IF `GET /api/movies/popular` 请求失败，THEN THE Homepage SHALL 显示 Toast 提示"热门电影加载失败"，并在行内显示空状态
4. WHILE 热门数据加载中，THE MovieRow 组件 SHALL 显示骨架屏占位
5. WHEN 用户点击热门行中的电影卡片时，THE Homepage SHALL 跳转至 `/movie/{id}`
6. THE "热门高分"行 SHALL 与"为你推荐"行独立加载，互不影响

---

### 需求 5：主页实时搜索区

**用户故事：** 作为访问者，我希望在主页能实时搜索电影，以便快速找到我想看的电影。

#### 验收标准

1. THE Homepage SHALL 在搜索区显示一个文本输入框，使用 `.cinema-search` 样式类
2. WHEN 用户在搜索框输入文字时，THE Homepage SHALL 使用 300ms 防抖（Debounce）后调用 `GET /api/movies?q={keyword}&limit=20`
3. WHEN 搜索结果返回时，THE Homepage SHALL 以 6 列响应式网格（`col-6 col-md-4 col-lg-3 col-xl-2`）显示 MovieCard 列表
4. WHEN 搜索结果为空时，THE Homepage SHALL 显示"未找到相关电影"的空状态提示
5. WHILE 搜索请求进行中，THE Homepage SHALL 显示骨架屏占位（6 个）
6. IF 搜索请求失败，THEN THE Homepage SHALL 显示 Toast 提示"搜索失败"
7. WHEN 搜索框内容为空时，THE Homepage SHALL 清空搜索结果，不发起 API 请求
8. WHEN 用户点击搜索结果中的电影卡片时，THE Homepage SHALL 跳转至 `/movie/{id}`

