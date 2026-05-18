# 电影推荐系统 (Movie Recommendation System)

本科毕业设计项目，基于 Flask + MySQL + ItemCF/NCF/Hybrid 的完整电影推荐系统。

## 1. 项目定位

- **主模型**：ItemCF（基于物品协同过滤），强调可解释推荐
- **扩展模型**：NCF（神经协同过滤）与 Hybrid（ItemCF 召回 + NCF 重排）
- **数据集**：MovieLens 32M（32M 条评分 / 27万用户 / 8.7万电影）
- **目标**：可运行系统 + 可解释推荐 + 离线评估 + 可视化看板

## 2. 技术栈

- **后端**：Python 3.10 / Flask / Flask-SQLAlchemy / Flask-Login
- **数据库**：MySQL + PyMySQL
- **算法**：NumPy / Pandas / SciPy / scikit-learn / PyTorch
- **前端**：Bootstrap 5 / Vue.js 3 / ECharts / GSAP

## 3. 快速开始

### 3.1 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 MySQL 并创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS movie_rec CHARACTER SET utf8mb4;"
```

### 3.2 数据导入（ml-32m）

```bash
# 快速导入（推荐，约 5-10 分钟）
python -m backend.scripts.import_fast --data-dir data/ml-32m
```

### 3.3 模型训练

```bash
# ItemCF（必选，主模型）
python -m backend.scripts.train_itemcf \
    --min-ratings-per-movie 50 \
    --min-ratings-per-user 5 \
    --normalize

# NCF（可选，扩展模型）
python -m backend.scripts.train_ncf \
    --epochs 10 \
    --batch-size 4096 \
    --hidden-dim 128 \
    --user-mod 10 \
    --device cpu

# 离线评估
python -m backend.scripts.evaluate_models --models all --k 10
```

### 3.4 创建演示用户

```bash
python -m backend.scripts.seed_demo_user
# 登录凭据: demo / demo123
```

### 3.5 启动服务

```bash
python backend/run.py
```

访问：
- 主应用：http://127.0.0.1:5000/app
- 数据看板：http://127.0.0.1:5000/dashboard
- 增强看板：http://127.0.0.1:5000/enhanced-dashboard
- 管理后台：http://127.0.0.1:5000/admin

## 4. 推荐策略

| 策略 | URL 参数 | 说明 |
|---|---|---|
| ItemCF | `strategy=itemcf` | 默认，基于物品协同过滤 + 推荐理由 |
| NCF | `strategy=ncf` | 神经网络协同过滤 |
| Hybrid | `strategy=hybrid` | ItemCF 召回 + NCF 重排 |

冷启动用户返回热门电影兜底。

## 5. 项目结构

```
backend/
├── app/
│   ├── routes.py              # 核心 API（70+ 端点）
│   ├── admin_routes.py        # 管理后台 API
│   ├── models.py              # 数据库模型（12表）
│   ├── ncf_engine.py          # NCF 推理引擎
│   ├── services/              # 用户画像服务
│   ├── templates/             # Jinja2 模板（38页面）
│   └── static/                # 前端静态资源
├── scripts/
│   ├── import_fast.py         # ml-32m 快速导入
│   ├── import_movielens.py    # 通用 MovieLens 导入
│   ├── train_itemcf.py        # ItemCF 训练
│   ├── train_ncf.py           # NCF 训练
│   ├── evaluate_models.py     # 多模型评估 + 消融实验
│   ├── evaluate_itemcf.py     # ItemCF 单项评估
│   └── seed_demo_user.py      # 演示用户创建
└── artifacts/                 # 模型与评估产物
```

## 6. 系统功能

- 用户系统：注册/登录/权限管理/用户画像
- 电影管理：搜索/详情/评分/相似电影
- 推荐引擎：ItemCF / NCF / Hybrid + 推荐解释
- 数据看板：评分分布/类型分布/年份趋势/离线指标
- 社交功能：影评/收藏/影单/评论互动
- 管理后台：电影/用户/评论/通知/权限/元数据管理
- 数据导出：用户数据/系统统计/完整备份
- 通知系统：系统通知/评论通知/推荐通知/成就通知
