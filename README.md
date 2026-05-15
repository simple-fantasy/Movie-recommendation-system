# Movie Recommendation System (毕业设计)

本项目是一个面向本科毕业设计的电影推荐系统，采用 Flask + MySQL + ItemCF/NCF/Hybrid 的实现路线，覆盖了数据导入、离线训练、在线推荐、可视化看板与离线评估全链路。

## 1. 项目定位与主线

- **主模型**：ItemCF（基于物品协同过滤）
- **扩展模型**：NCF（神经协同过滤）与 Hybrid（ItemCF 召回 + NCF 重排）
- **目标**：完成“可运行系统 + 可解释推荐 + 可评估结果 + 可展示看板”

答辩建议主线：
1. 系统工程主线以 `ItemCF` 为核心，确保稳定与可解释；
2. `NCF/Hybrid` 作为扩展优化探索，不强行宣称全面优于基线。

## 2. 技术栈

- Python 3.10
- Flask / Flask-Login / Flask-SQLAlchemy
- MySQL + PyMySQL
- NumPy / Pandas / SciPy / scikit-learn
- PyTorch（NCF 训练与推理）
- Bootstrap + ECharts（前端可视化）

## 3. 目录结构（关键）

- `backend/app/routes.py`：核心 API、推荐逻辑、看板接口
- `backend/app/models.py`：数据库模型
- `backend/scripts/import_movielens.py`：数据导入
- `backend/scripts/train_itemcf.py`：ItemCF 离线训练
- `backend/scripts/train_ncf.py`：NCF 训练
- `backend/scripts/evaluate_itemcf.py`：ItemCF 离线评估
- `backend/scripts/evaluate_models.py`：多模型评估与消融
- `backend/app/templates/app.html`：主应用页
- `backend/app/templates/dashboard.html`：可视化看板
- `backend/artifacts/`：模型与评估产物

## 4. 环境准备

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

或使用 `environment.yml` 创建 Conda 环境。

### 4.2 数据库配置（MySQL）

默认读取 `backend/config.py`：

- 默认 URI: `mysql+pymysql://root:ftrk2756@localhost:3306/movie_rec?charset=utf8mb4`
- 推荐使用环境变量覆盖：

```powershell
$env:DATABASE_URL="mysql+pymysql://<user>:<password>@localhost:3306/movie_rec?charset=utf8mb4"
```

## 5. 运行流程

### Step 1: 导入数据

```bash
python -m backend.scripts.import_movielens --data-dir "<你的MovieLens目录>"
```

### Step 2: 训练 ItemCF

```bash
python -m backend.scripts.train_itemcf
```

### Step 3: （可选）训练 NCF

```bash
python -m backend.scripts.train_ncf --epochs 20 --batch-size 8192 --hidden-dim 128 --device cuda --lr 1e-3
```

> Windows + CUDA 环境下，建议先不加 `--compile`。

### Step 4: 生成离线评估

```bash
python -m backend.scripts.evaluate_itemcf
python -m backend.scripts.evaluate_models --models all --ablation --k 10
```

### Step 5: 启动服务

```bash
python backend/run.py
```

访问：

- `http://127.0.0.1:5000/app`
- `http://127.0.0.1:5000/dashboard`

## 6. 离线评估产物

- `backend/artifacts/offline_metrics.json`（ItemCF）
- `backend/artifacts/evaluation_results.json`（ItemCF / NCF / Hybrid + 消融）
- `backend/artifacts/ncf.pt` 与 `backend/artifacts/ncf_meta.json`（NCF）

## 7. 已知限制

- 当前主要是离线评估，尚无在线 A/B 测试。
- NCF/Hybrid 在当前数据规模下不一定优于 ItemCF。
- 若离线指标接口 404，需先运行评估脚本生成 artifacts 文件。

## 8. 文档入口

- 论文材料框架：`docs/毕业设计说明.md`
- 演示彩排清单：`docs/演示彩排清单.md`
- 答辩高频问答：`docs/答辩高频问答.md`
