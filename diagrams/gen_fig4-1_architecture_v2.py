"""Generate updated system architecture diagram for thesis Chapter 4.
Reflects current 7-model evaluation system.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "font.size": 8,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
})

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")

# ---- Color palette ----
C_DATA     = "#dae8fc"  # blue
C_TRAIN    = "#fff2cc"  # yellow
C_SERVICE  = "#d5e8d4"  # green
C_EVAL     = "#e1d5e7"  # purple
C_FRONTEND = "#f8cecc"  # pink/red
C_ARTIFACT = "#ffe6cc"  # orange
C_DB       = "#f5f5f5"  # gray

E_DATA     = "#6c8ebf"
E_TRAIN    = "#d6b656"
E_SERVICE  = "#82b366"
E_EVAL     = "#9673a6"
E_FRONTEND = "#b85450"
E_ARTIFACT = "#d79b00"
E_DB       = "#666666"


def layer_box(ax, x, y, w, h, label, fc, ec):
    """Draw a layer container with title."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3", facecolor=fc,
                          edgecolor=ec, linewidth=1.5, alpha=0.35, zorder=1)
    ax.add_patch(box)
    ax.text(x + 0.3, y + h - 0.3, label, fontsize=9, fontweight="bold", color=ec, va="top", zorder=2)


def component(ax, x, y, w, h, text, fc="white", ec="#888888", fontsize=7, lw=1.0):
    """Draw a component box."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", facecolor=fc,
                          edgecolor=ec, linewidth=lw, zorder=3)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize,
            color="#333333", zorder=4)


def artifact(ax, x, y, w, h, text, fc=C_ARTIFACT, ec=E_ARTIFACT, fontsize=6.5):
    """Draw an artifact (model file / DB table)."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", facecolor=fc,
                          edgecolor=ec, linewidth=0.8, zorder=3)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize,
            color="#333333", fontstyle="italic", zorder=4)


def arrow(ax, x1, y1, x2, y2, color="#888888", lw=1.0, style="->"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, connectionstyle="arc3,rad=0"),
                zorder=2)


def dashed_arrow(ax, x1, y1, x2, y2, color="#888888", lw=0.8):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, linestyle="--", connectionstyle="arc3,rad=0"),
                zorder=2)


# ====== Title ======
ax.text(10, 13.6, "图 4-1  系统总体架构", ha="center", fontsize=14, fontweight="bold")

# ====== LAYER 1: Data Layer (y=10.8 to 12.8) ======
layer_box(ax, 0.3, 10.6, 19.4, 2.4, "数据层  Data Layer", C_DATA, E_DATA)

# Data source
component(ax, 0.6, 11.0, 2.5, 1.0, "MovieLens 32M\n32M ratings / 270K users / 87K movies", fc="white", ec=E_DATA, fontsize=6.5)
component(ax, 0.6, 12.2, 2.5, 0.5, "import_fast.py\nimport_movielens.py", fc=C_DATA, ec=E_DATA, fontsize=6)

# MySQL
db_x, db_y = 4.0, 11.1
component(ax, db_x, db_y, 4.5, 1.6, "", fc=C_DB, ec=E_DB)
ax.text(db_x + 2.25, db_y + 1.4, "MySQL Database", fontsize=8, fontweight="bold", ha="center", color="#333333")
tables = "users | movies | ratings | movie_similarity\nrecommendation_feedback | reviews | review_likes\nuser_collections | watch_links | user_behaviors | user_profiles"
ax.text(db_x + 2.25, db_y + 0.85, tables, fontsize=6, ha="center", va="center", color="#555555")

arrow(ax, 3.1, 11.5, db_x, 12.0, E_DATA)
arrow(ax, 3.1, 12.4, db_x, 12.4, E_DATA)

# TMDB enrichment
component(ax, 9.5, 11.3, 2.0, 1.2, "TMDB API\n海报/导演/演员\n(enrich_movies.py)", fc="white", ec=E_DATA, fontsize=6)
arrow(ax, 8.5, 12.0, 9.5, 12.0, E_DATA)

# ====== LAYER 2: Offline Training (y=7.9 to 10.4) ======
layer_box(ax, 0.3, 7.7, 19.4, 2.9, "离线训练层  Offline Training", C_TRAIN, E_TRAIN)

train_scripts = [
    ("train_itemcf.py", "scikit-learn\nNearestNeighbors\ncosine similarity", 0.6),
    ("train_ncf_v2.py", "PyTorch MLP\nBCE Loss / neg4\n三层切分 / 早停", 4.0),
    ("train_lightgcn.py", "PyTorch LightGCN\nBPR Loss / 3层GCN\nepoch级传播优化", 7.4),
    ("train_ease.py", "NumPy EASE\n闭式最小二乘\nλ=500 / 矩阵求逆", 10.8),
]
for name, desc, tx in train_scripts:
    component(ax, tx, 8.5, 3.0, 1.3, f"{name}\n{desc}", fc="white", ec=E_TRAIN, fontsize=6)

# Training output (artifacts)
art_y = 9.35
artifacts_data = [
    (0.45, "相似度表\nmovie_similarity"),
    (4.05, "ncf_v2.pt\nncf_v2_meta.json"),
    (7.45, "lightgcn.pt\nlightgcn_embeddings.pt\nlightgcn_meta.json"),
    (10.85, "ease_B.npy\nease_meta.json"),
]
for ax_pos, label in artifacts_data:
    artifact(ax, ax_pos, 8.1, 2.9, 0.65, label, fontsize=5.8)
    arrow(ax, ax_pos + 1.0, 8.55, ax_pos + 0.7, 8.75, E_TRAIN, 0.7)

# Data flow: MySQL → Training
arrow(ax, 6.25, 10.6, 2.1, 9.8, E_TRAIN, 0.8)
ax.text(4.2, 10.25, "评分数据", fontsize=6.5, color=E_TRAIN, ha="center")

# ====== LAYER 3: Online Service (y=4.5 to 7.5) ======
layer_box(ax, 0.3, 4.3, 19.4, 3.4, "在线服务层  Online Service", C_SERVICE, E_SERVICE)

# Flask core
component(ax, 0.6, 5.0, 2.8, 1.5,
          "Flask Application\ncreate_app() factory\n┌─────────────┐\n│ routes.py      │\n│ admin_routes   │\n│ decorators.py  │\n└─────────────┘\nJinja2 + Flask-Login\nFlask-Caching (FileSystem)",
          fc="white", ec=E_SERVICE, fontsize=6)

# Recommendation API
component(ax, 4.0, 5.2, 2.5, 1.2,
          "/api/recommendations\nstrategy=itemcf|ncf|hybrid\nn / recall_k params\n/api/recommendations/why\n/api/ratings /api/feedback",
          fc="white", ec=E_SERVICE, fontsize=6)

# Inference engines
engines = [
    ("ItemCF Engine\n similarity.py\nweighted-sum recall\nbecause explanation", E_DATA),
    ("NCF Engine\nncf_engine.py\nsingleton + async\nbatched_rank()\nfallback: ItemCF", E_TRAIN),
    ("LightGCN Engine\nlazy load\nembedding dot-product", E_EVAL),
    ("EASE Engine\nlazy load\nB @ x_u matrix-vector\nNumPy scoring", E_ARTIFACT),
    ("Hybrid Pipeline\nItemCF recall Top-200\n→ NCF rerank Top-10\n3-tier fallback chain", "#33aa33"),
]
eng_x = 7.0
for i, (desc, ec) in enumerate(engines):
    ex = eng_x + i * 2.6
    component(ax, ex, 4.8, 2.3, 1.7, desc, fc="white", ec=ec, fontsize=5.8, lw=1.0)

# Artifacts → Engines
artifact(ax, 4.8, 6.8, 1.5, 0.45, "ncf_v2.pt / ncf_v2_meta.json", fontsize=5.5)
arrow(ax, 5.55, 7.5, 8.15, 6.5, E_TRAIN, 0.6)
artifact(ax, 10.0, 6.8, 1.5, 0.45, "lightgcn_embeddings.pt", fontsize=5.5)
arrow(ax, 10.75, 7.5, 9.45, 6.5, E_EVAL, 0.6)
artifact(ax, 13.0, 6.8, 1.5, 0.45, "ease_B.npy", fontsize=5.5)
arrow(ax, 13.75, 7.5, 13.45, 6.5, E_ARTIFACT, 0.6)

# ====== LAYER 4: Evaluation (bottom-left) ======
layer_box(ax, 0.3, 1.5, 10.2, 3.0, "离线评估层  Offline Evaluation", C_EVAL, E_EVAL)

eval_components = [
    (0.6, 1.8, "splitter.py\n三层时间切分\ntrain/val/test\n零数据泄露"),
    (2.8, 1.8, "engine.py\nEvaluationEngine\n7-model support\nfull_ranking"),
    (5.0, 1.8, "metrics.py\n11 metrics\nP/R/NDCG/MAP/MRR\nILS/Novelty/Coverage"),
    (7.2, 1.8, "checks.py\nSanity Checks\nRandom+Oracle+Popular\nInvariants"),
]
for ex, ey, desc in eval_components:
    component(ax, ex, ey, 1.9, 1.8, desc, fc="white", ec=E_EVAL, fontsize=5.8)

# Two protocols
component(ax, 0.6, 3.7, 4.5, 0.6,
          "Protocol 1: C_all=13K (公平对比, run_evaluation.py)  |  Protocol 2: full_ranking=80K (真实场景, evaluate_models.py)",
          fc=C_EVAL, ec=E_EVAL, fontsize=6)

# Evaluation output
artifact(ax, 5.8, 3.7, 2.0, 0.6, "evaluation_results.json\nfull_ranking_final.json", fontsize=6)
arrow(ax, 5.1, 3.95, 5.8, 4.0, E_EVAL, 0.7)

# Data flow: MySQL → Evaluation
arrow(ax, 6.25, 10.6, 5.0, 4.6, E_EVAL, 0.8, "-|>")
ax.text(8.2, 7.8, "缓存数据\nCSV / Pickle", fontsize=6, color=E_EVAL, ha="center")

# ====== LAYER 5: Frontend (right side + bottom) ======
layer_box(ax, 11.0, 6.5, 8.7, 6.5, "前端展示层  Presentation", C_FRONTEND, E_FRONTEND)

fe_components = [
    (11.3, 11.5, "Jinja2 Templates\n30 HTML files\nChainableUndefined\n(Vue {{ }} coexistence)"),
    (14.0, 11.5, "Vue.js 3 (CDN)\nOptions API\n5 reusable components\nMovieCard / StarRating\nSkeletonGrid / SearchBox"),
    (11.3, 9.5, "Bootstrap 5\nDark Theme\nResponsive Grid\nCards / Modals / Tabs"),
    (14.0, 9.5, "ECharts 5.4\n评分分布 / 类型占比\n年份趋势 / 用户分群\n活动热力图 / 旭日图"),
    (11.3, 7.2, "Key Pages\n推荐页 (strategy tabs)\n增强看板 (dashboard)\n用户画像 + 洞察\n电影详情 + 评分\n收藏管理 + 评论"),
]
for ex, ey, desc in fe_components:
    component(ax, ex, ey, 2.5, 2.0, desc, fc="white", ec=E_FRONTEND, fontsize=5.8)

# API → Frontend
arrow(ax, 6.5, 6.0, 11.0, 11.0, E_FRONTEND, 0.8)
ax.text(8.5, 8.6, "JSON API", fontsize=6.5, color=E_FRONTEND, ha="center", rotation=35)
arrow(ax, 6.5, 5.5, 11.0, 5.0, E_FRONTEND, 0.8)

# User browser
component(ax, 15.0, 1.8, 3.0, 0.8, "User Browser\nHTTP Requests / JSON Responses", fc=C_FRONTEND, ec=E_FRONTEND, fontsize=6.5)

# Admin
component(ax, 16.0, 3.0, 2.0, 0.8, "Admin Panel\n/admin/*\n14 admin templates", fc=C_FRONTEND, ec=E_FRONTEND, fontsize=6)

# ====== DATA FLOW SUMMARY (bottom annotations) ======
flows = [
    ("1", "MovieLens → import → MySQL", E_DATA, 2.0),
    ("2", "MySQL → train_*.py → artifacts (.pt/.npy/sims)", E_TRAIN, 5.0),
    ("3", "artifacts → Flask API → JSON recommendations", E_SERVICE, 8.0),
    ("4", "JSON → Jinja2/Vue.js → rendered pages", E_FRONTEND, 11.0),
    ("5", "MySQL → evaluation engine → evaluation_results.json", E_EVAL, 14.0),
]
for num, desc, color, fx in flows:
    ax.text(fx, 0.7, f"({num}) {desc}", fontsize=6.5, color=color, ha="left", fontstyle="italic")

ax.text(19.5, 0.1, "Source: backend/ (app + evaluation + scripts)  |  资料来源：作者自绘",
        fontsize=6, color="#cccccc", ha="right", fontstyle="italic")

# ---- Save ----
fig.tight_layout(pad=0.5)
out_base = "d:/OneDrive/桌面/毕设/Movie-recommendation-system/diagrams/fig4-1-system-architecture-v2"
fig.savefig(f"{out_base}.pdf", dpi=200, bbox_inches="tight")
fig.savefig(f"{out_base}.png", dpi=200, bbox_inches="tight")
print(f"Saved: {out_base}.pdf, {out_base}.png")
plt.close()
