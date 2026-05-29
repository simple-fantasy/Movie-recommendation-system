"""Generate recommendation request sequence diagram for thesis Chapter 5.
Shows three strategies: ItemCF, NCF, Hybrid + cold-start fallback.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "font.size": 8,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
})

fig, ax = plt.subplots(1, 1, figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis("off")

# ---- Colors ----
C_LIFELINE = "#555555"
C_ACTIVE = "#dae8fc"
C_ARROW = "#333333"
C_FRAGMENT = "#f0f0f0"
C_NOTE = "#fff8e1"
C_ITEMCF = "#6c8ebf"
C_NCF = "#d79b00"
C_HYBRID = "#82b366"
C_FALLBACK = "#cc6666"

# ---- Lifeline positions ----
# Browser, Flask, ItemCF, NCF, MySQL
LIFELINES = {
    "Browser": 1.5,
    "Flask":   5.5,
    "ItemCF":  9.5,
    "NCF":    13.0,
    "MySQL":  16.5,
}
LL = LIFELINES  # shorthand

HEAD_Y = 13.2
ACTIVE_START = 12.6


def lifeline_header(ax, x, name, y=HEAD_Y):
    """Draw lifeline header box."""
    w, h = 2.0, 0.6
    box = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.1",
                          facecolor="white", edgecolor=C_LIFELINE, linewidth=1.2)
    ax.add_patch(box)
    ax.text(x, y, name, ha="center", va="center", fontsize=8, fontweight="bold", color="#333333")


def lifeline(ax, x, y_top, y_bottom):
    """Draw dashed lifeline."""
    ax.plot([x, x], [y_bottom, y_top], color=C_LIFELINE, linewidth=0.8, linestyle="--", dashes=(6, 4))


def activation(ax, x, y_bottom, y_top, w=0.3):
    """Draw activation bar on lifeline."""
    rect = Rectangle((x - w/2, y_bottom), w, y_top - y_bottom, facecolor=C_ACTIVE,
                      edgecolor="#6c8ebf", linewidth=0.8, zorder=3)
    ax.add_patch(rect)


def message(ax, x1, y1, x2, y2, text, color=C_ARROW, fontsize=7, offset=0.15):
    """Draw message arrow with label."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2, connectionstyle="arc3,rad=0"), zorder=4)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + offset, text, ha="center", va="bottom", fontsize=fontsize, color="#333333",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85), zorder=5)


def dashed_message(ax, x1, y1, x2, y2, text, color=C_ARROW, fontsize=7, offset=0.15):
    """Dashed return message."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.0, linestyle="--", connectionstyle="arc3,rad=0"), zorder=4)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mx, my + offset, text, ha="center", va="bottom", fontsize=fontsize, color="#666666",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85), zorder=5)


def fragment(ax, x, y, w, h, label, color="#e8e8e8"):
    """Draw alt/opt fragment box."""
    rect = Rectangle((x, y), w, h, facecolor="none", edgecolor="#aaaaaa", linewidth=1, linestyle="--", zorder=1)
    ax.add_patch(rect)
    # Label tab
    tab_w = 1.5
    ax.fill_between([x + 0.2, x + 0.2 + tab_w], y + h, y + h - 0.35,
                    facecolor=color, edgecolor="#aaaaaa", linewidth=0.5, zorder=2)
    ax.text(x + 0.2 + tab_w/2, y + h - 0.17, label, ha="center", va="center", fontsize=7.5,
            fontweight="bold", color="#333333", zorder=3)


def note_box(ax, x, y, w, h, text, color=C_NOTE):
    """Draw a note with folded corner."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", facecolor=color,
                          edgecolor="#ddcc88", linewidth=0.8, zorder=5)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=7, color="#555555", zorder=6)


# ====== DRAW HEADERS AND LIFELINES ======
for name, x in LL.items():
    lifeline_header(ax, x, name)
    lifeline(ax, x, HEAD_Y - 0.3, 0.3)

# Global activation for all lifelines
for name, x in LL.items():
    activation(ax, x, 0.3, ACTIVE_START)

# Title
ax.text(9, 13.85, "图 5-2  推荐系统核心请求处理时序图", ha="center", fontsize=13, fontweight="bold")

# ====== REQUEST FLOW ======
y = 12.2

# Step 1: HTTP GET /api/recommendations?strategy=...
message(ax, LL["Browser"], y, LL["Flask"], y, "GET /api/recommendations?\nstrategy=itemcf|ncf|hybrid")

y -= 0.65

# ---- BRANCH: Check if user has ratings ----
fragment(ax, 0.3, y - 5.2, 17.4, 5.4, "alt")

y_sub = y - 0.4
# Cold start branch
ax.text(3.0, y_sub, "[无评分记录]", fontsize=7, color=C_FALLBACK, fontweight="bold")
message(ax, LL["Flask"], y_sub, LL["MySQL"], y_sub, "查询评分历史", fontsize=6.5)
dashed_message(ax, LL["MySQL"], y_sub - 0.3, LL["Flask"], y_sub - 0.3, "0条", fontsize=6.5)
# Popularity fallback
message(ax, LL["Flask"], y_sub - 0.8, LL["MySQL"], y_sub - 0.8,
        "SELECT * FROM movies\nWHERE rating_count>=50\nORDER BY avg_rating DESC", fontsize=6)
dashed_message(ax, LL["MySQL"], y_sub - 1.2, LL["Flask"], y_sub - 1.2, "Top-K", fontsize=6)
dashed_message(ax, LL["Flask"], y_sub - 1.7, LL["Browser"], y_sub - 1.7,
               "JSON (cold_start:true, fallback:popular)", color=C_FALLBACK, fontsize=6.5)

# Normal branch
y_norm = y_sub - 2.4
ax.text(3.0, y_norm, "[有评分记录]", fontsize=7, color=C_ITEMCF, fontweight="bold")
message(ax, LL["Flask"], y_norm, LL["MySQL"], y_norm, "查询用户评分历史", fontsize=6.5)
dashed_message(ax, LL["MySQL"], y_norm - 0.3, LL["Flask"], y_norm - 0.3,
               "[(mid, rating), ...]", fontsize=6.5)

y = y_norm - 0.8

# ---- BRANCH: Strategy-specific processing ----
FRAG_H = 7.0
fragment(ax, 0.3, y - FRAG_H + 0.5, 17.4, FRAG_H, "opt  [strategy]")

# === ITEMCF BRANCH ===
y_icf = y - 0.4
ax.text(3.0, y_icf, "[itemcf]", fontsize=7, color=C_ITEMCF, fontweight="bold")

message(ax, LL["Flask"], y_icf, LL["ItemCF"], y_icf,
        "传入 [(mid, rating)] 列表", color=C_ITEMCF, fontsize=6.5)

y_icf -= 0.45
message(ax, LL["ItemCF"], y_icf, LL["MySQL"], y_icf,
        "SELECT similar_movie_id, score\nFROM movie_similarity\nWHERE movie_id IN (...)", fontsize=6, color=C_ITEMCF)

y_icf -= 0.45
ax.text(LL["ItemCF"] + 0.35, y_icf + 0.1, "加权求和\nscore += sim × rating\nper_seed_limit=50",
        fontsize=5.8, color=C_ITEMCF, ha="left", va="top")

y_icf -= 0.9
message(ax, LL["ItemCF"], y_icf, LL["Flask"], y_icf,
        "Top-K + because 字段", color=C_ITEMCF, fontsize=6.5)

y_icf -= 0.45
message(ax, LL["Flask"], y_icf, LL["Browser"], y_icf,
        "JSON (recs + reasons)", color=C_ITEMCF, fontsize=6.5)

# === NCF BRANCH ===
y_ncf = y - 0.4
ax.text(11.5, y_ncf, "[ncf]", fontsize=7, color=C_NCF, fontweight="bold")

y_ncf -= 0.5
message(ax, LL["Flask"], y_ncf, LL["NCF"], y_ncf,
        "ncf_engine.is_ready()?", color=C_NCF, fontsize=6.5)

# Not ready fallback
y_ncf -= 0.45
ax.text(13.8, y_ncf, "[未就绪 → ItemCF]", fontsize=6, color=C_FALLBACK)
dashed_message(ax, LL["NCF"], y_ncf - 0.25, LL["Flask"], y_ncf - 0.25, "False", color=C_FALLBACK, fontsize=6)
message(ax, LL["Flask"], y_ncf - 0.55, LL["ItemCF"], y_ncf - 0.55,
        "回退 ItemCF", color=C_FALLBACK, fontsize=6)

y_ncf = y_ncf - 1.1
ax.text(13.8, y_ncf, "[就绪]", fontsize=6, color="#33aa33")
y_ncf -= 0.35
message(ax, LL["Flask"], y_ncf, LL["MySQL"], y_ncf,
        "获取热门未评分电影", color=C_NCF, fontsize=6)
y_ncf -= 0.4
dashed_message(ax, LL["MySQL"], y_ncf, LL["Flask"], y_ncf,
               "candidate_list (N items)", fontsize=6, color=C_NCF)

y_ncf -= 0.55
message(ax, LL["Flask"], y_ncf, LL["NCF"], y_ncf,
        "ncf_engine.rank(uid, candidates, top_k=K)", color=C_NCF, fontsize=6.5)

y_ncf -= 0.55
ax.text(LL["NCF"] + 0.35, y_ncf + 0.05, "batched_rank()\n大batch forward\nsigmoid→top_k",
        fontsize=5.8, color=C_NCF, ha="left", va="top")

y_ncf -= 0.8
message(ax, LL["NCF"], y_ncf, LL["Flask"], y_ncf,
        "Top-K 排序列表", color=C_NCF, fontsize=6.5)

y_ncf -= 0.45
message(ax, LL["Flask"], y_ncf, LL["Browser"], y_ncf,
        "JSON (无 because 字段)", color=C_NCF, fontsize=6.5)

# === HYBRID BRANCH ===
y_hyb = y - 5.8
ax.text(3.0, y_hyb, "[hybrid]", fontsize=7, color=C_HYBRID, fontweight="bold")

y_hyb -= 0.45
message(ax, LL["Flask"], y_hyb, LL["ItemCF"], y_hyb,
        "ItemCF 召回 Top-" + "recall_k (200)", color=C_HYBRID, fontsize=6.5)

y_hyb -= 0.5
ax.text(LL["ItemCF"] + 0.35, y_hyb + 0.1, "同 ItemCF 流程\n但取 Top-200",
        fontsize=5.8, color=C_HYBRID, ha="left", va="top")

y_hyb -= 0.85
message(ax, LL["ItemCF"], y_hyb, LL["Flask"], y_hyb,
        "候选集 (≤ 200)", color=C_HYBRID, fontsize=6.5)

y_hyb -= 0.55
message(ax, LL["Flask"], y_hyb, LL["NCF"], y_hyb,
        "ncf_engine.rank(uid, candidates, top_k=10)", color=C_HYBRID, fontsize=6.5)

y_hyb -= 0.55
ax.text(LL["NCF"] + 0.35, y_hyb + 0.05, "NCF 重排", fontsize=5.8, color=C_HYBRID, ha="left")
y_hyb -= 0.35
message(ax, LL["NCF"], y_hyb, LL["Flask"], y_hyb,
        "重排 Top-10 [NCF 不可用→取 ItemCF 前10]", color=C_HYBRID, fontsize=6.5)

y_hyb -= 0.5
message(ax, LL["Flask"], y_hyb, LL["Browser"], y_hyb,
        "JSON (because 来自 ItemCF)", color=C_HYBRID, fontsize=6.5)

# ====== DESIGN NOTES (right side) ======
note_y = 11.0
note_box(ax, 0.4, note_y - 1.5, 2.3, 1.8,
         "Design Notes:\n"
         "NCF 异步预加载\n(load_async)\n"
         "三层回退链:\n"
         "NCF→ItemCF→Popularity", C_NOTE)

note_box(ax, 0.4, note_y - 4.0, 2.3, 2.2,
         "Key Parameters:\n"
         "Hybrid recall_k=200\n"
         "ItemCF per_seed_limit=50\n"
         "ItemCF sim_topk_per_movie=50\n"
         "NCF batch_size=4096\n"
         "NCF einference chunk\n"
         "  = 262144", C_NOTE)

# Bottom: Source
ax.text(9, 0.1, "Source: routes.py (Flask) + similarity.py (ItemCF) + ncf_engine.py (NCF)  |  资料来源：作者自绘",
        fontsize=6, color="#cccccc", ha="center", fontstyle="italic")

# ---- Save ----
fig.tight_layout(pad=0.5)
out_base = "d:/OneDrive/桌面/毕设/Movie-recommendation-system/diagrams/fig5-2-recommendation-sequence"
fig.savefig(f"{out_base}.pdf", dpi=200, bbox_inches="tight")
fig.savefig(f"{out_base}.png", dpi=200, bbox_inches="tight")
print(f"Saved: {out_base}.pdf, {out_base}.png")
plt.close()
