"""Generate NCF-MLP architecture diagram for thesis Chapter 5.
Data source: ncf_engine.py (NCF class) + ncf_v2_meta.json
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---- Style ----
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 12,
    "figure.facecolor": "white",
    "axes.unicode_minus": False,
})

fig, ax = plt.subplots(1, 1, figsize=(16, 6))
ax.set_xlim(0, 16)
ax.set_ylim(0, 6)
ax.axis("off")

# ---- Color palette (engineering paper style) ----
C_EMB   = "#dae8fc"  # blue  - Embedding
C_LINEAR = "#ffe6cc"  # orange - Linear
C_RELU   = "#d5e8d4"  # green - ReLU
C_SIGMOID = "#fff2cc" # yellow - Sigmoid
C_OUT    = "#dae8fc"  # blue  - Output
C_INPUT  = "#f5f5f5"  # gray  - Input
C_MERGE  = "#f5f5f5"  # gray  - Concat
EDGE_DARK = "#555555"

STROKE_EMB = "#6c8ebf"
STROKE_LINEAR = "#d79b00"
STROKE_RELU = "#82b366"
STROKE_SIGMOID = "#d6b656"


def draw_box(ax, x, y, w, h, text, fc, ec, fontsize=8, fontstyle="normal", fontweight="normal", fontcolor="#333333", lw=1.2):
    """Draw a rounded box with text."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", facecolor=fc,
                          edgecolor=ec, linewidth=lw, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
            fontstyle=fontstyle, fontweight=fontweight, color=fontcolor, zorder=3)


def draw_arrow(ax, x1, y1, x2, y2, color=EDGE_DARK, lw=1.2):
    """Draw an arrow from (x1,y1) to (x2,y2)."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, connectionstyle="arc3,rad=0"),
                zorder=1)


def draw_dim_label(ax, x, y, text, color="#888888"):
    """Small dimension annotation."""
    ax.text(x, y, text, ha="center", va="top", fontsize=7, color=color, fontstyle="italic")


# ---- Layout coordinates ----
# Row centers for the two input branches
y_user = 4.0   # user branch
y_item = 1.2   # item branch
y_mid  = 2.6   # middle (concat + mlp)

# X positions for pipeline blocks
x_input   = 0.8
x_emb     = 2.6
x_concat  = 5.0
x_fc1     = 7.2
x_relu1   = 9.0
x_fc2     = 10.6
x_relu2   = 12.4
x_fc3     = 14.0
x_sigmoid = 15.2

# Box sizes
bw, bh   = 1.2, 0.65   # standard box
bw_small, bh_small = 0.55, 0.55  # ReLU / Sigmoid
bw_concat, bh_concat = 0.9, 1.5  # concat (tall)
bw_out, bh_out = 0.85, 0.75      # output

# ---- Title ----
ax.text(8.0, 5.5, "图 5-1  NCF-MLP 模型架构", ha="center", va="center",
        fontsize=13, fontweight="bold", color="black")

# ---- INPUTS ----
draw_box(ax, x_input, y_user - bh / 2, bw, bh, "User ID", C_INPUT, "#999999", fontweight="bold")
draw_box(ax, x_input, y_item - bh / 2, bw, bh, "Item ID", C_INPUT, "#999999", fontweight="bold")

# ---- EMBEDDINGS ----
draw_box(ax, x_emb, y_user - bh / 2, bw, bh, "User Embedding\n170,279 × 64", C_EMB, STROKE_EMB, fontsize=7.5)
draw_box(ax, x_emb, y_item - bh / 2, bw, bh, "Item Embedding\n71,307 × 64", C_EMB, STROKE_EMB, fontsize=7.5)
draw_dim_label(ax, x_emb + bw / 2, y_user - bh / 2 - 0.05, "64-dim")
draw_dim_label(ax, x_emb + bw / 2, y_item - bh / 2 - 0.05, "64-dim")

# Input → Embedding arrows
draw_arrow(ax, x_input + bw, y_user, x_emb, y_user, STROKE_EMB)
draw_arrow(ax, x_input + bw, y_item, x_emb, y_item, STROKE_EMB)

# ---- CONCAT ----
draw_box(ax, x_concat, y_mid - bh_concat / 2, bw_concat, bh_concat, "Concat\n(128)", C_MERGE, "#999999", fontsize=8)
# Embedding → Concat arrows
draw_arrow(ax, x_emb + bw, y_user, x_concat, y_mid + bh_concat * 0.25, "#9673a6")
draw_arrow(ax, x_emb + bw, y_item, x_concat, y_mid - bh_concat * 0.25, "#9673a6")

# ---- MLP Layers ----
# FC1: Linear(128,256)
draw_box(ax, x_fc1, y_mid - bh / 2, bw, bh, "Linear\n128 → 256", C_LINEAR, STROKE_LINEAR, fontsize=7.5)
draw_dim_label(ax, x_fc1 + bw / 2, y_mid - bh / 2 - 0.05, "256")
draw_arrow(ax, x_concat + bw_concat, y_mid, x_fc1, y_mid, STROKE_LINEAR)

# ReLU1
draw_box(ax, x_relu1, y_mid - bh_small / 2, bw_small, bh_small, "ReLU", C_RELU, STROKE_RELU, fontsize=7.5)
draw_arrow(ax, x_fc1 + bw, y_mid, x_relu1, y_mid, STROKE_RELU)

# FC2: Linear(256,128)
draw_box(ax, x_fc2, y_mid - bh / 2, bw, bh, "Linear\n256 → 128", C_LINEAR, STROKE_LINEAR, fontsize=7.5)
draw_dim_label(ax, x_fc2 + bw / 2, y_mid - bh / 2 - 0.05, "128")
draw_arrow(ax, x_relu1 + bw_small, y_mid, x_fc2, y_mid, STROKE_LINEAR)

# ReLU2
draw_box(ax, x_relu2, y_mid - bh_small / 2, bw_small, bh_small, "ReLU", C_RELU, STROKE_RELU, fontsize=7.5)
draw_arrow(ax, x_fc2 + bw, y_mid, x_relu2, y_mid, STROKE_RELU)

# FC3: Linear(128,1)
draw_box(ax, x_fc3, y_mid - bh / 2, bw, bh, "Linear\n128 → 1", C_LINEAR, STROKE_LINEAR, fontsize=7.5)
draw_arrow(ax, x_relu2 + bw_small, y_mid, x_fc3, y_mid, STROKE_LINEAR)

# Sigmoid
draw_box(ax, x_sigmoid, y_mid - bh_small / 2, bw_small, bh_small, "σ", C_SIGMOID, STROKE_SIGMOID, fontsize=10, fontweight="bold")
draw_arrow(ax, x_fc3 + bw, y_mid, x_sigmoid, y_mid, STROKE_SIGMOID)

# Output
x_out = x_sigmoid + bw_small + 0.3
draw_box(ax, x_out, y_mid - bh_out / 2, bw_out, bh_out, "ŷui ∈ [0, 1]", C_OUT, STROKE_EMB, fontsize=8, fontweight="bold")
draw_arrow(ax, x_sigmoid + bw_small, y_mid, x_out, y_mid, STROKE_EMB, lw=1.5)

# ---- MLP bracket ----
mlp_x1 = x_fc1 - 0.15
mlp_x2 = x_fc3 + bw + 0.15
mlp_y_top = y_mid + bh / 2 + 0.15
ax.plot([mlp_x1, mlp_x1], [y_mid - 0.95, mlp_y_top], color="#aaaaaa", lw=1, linestyle="--")
ax.plot([mlp_x1, mlp_x2], [mlp_y_top, mlp_y_top], color="#aaaaaa", lw=1, linestyle="--")
ax.text(mlp_x1 + 0.1, mlp_y_top + 0.08, "MLP (3-layer FC)", fontsize=8, color="#999999", fontstyle="italic")

# ---- Training Info Box ----
info_y = 0.25
info_text = (
    "Loss: BCEWithLogitsLoss  |  Neg Ratio: 4  |  Optimizer: Adam (lr=0.001)  |  Max Epochs: 20  |  Batch: 4096\n"
    "Early Stop: val NDCG@10 no improvement for 3 epochs  |  Split: three-way temporal (train/val/test)  |  Best Val NDCG@10: 0.8148"
)
ax.text(0.5, info_y, info_text, ha="left", va="top", fontsize=7.5, color="#555555",
        fontfamily="monospace", transform=ax.transData,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fafafa", edgecolor="#cccccc", linewidth=0.8))

# ---- Legend ----
leg_y = 4.8
leg_items = [
    (C_EMB, STROKE_EMB, "Embedding"),
    (C_LINEAR, STROKE_LINEAR, "Linear"),
    (C_RELU, STROKE_RELU, "ReLU"),
    (C_SIGMOID, STROKE_SIGMOID, "Sigmoid"),
    (C_INPUT, "#999999", "Input/Output"),
    (C_MERGE, "#999999", "Concat"),
]
leg_x = 0.5
for fc, ec, label in leg_items:
    box = FancyBboxPatch((leg_x, leg_y), 0.28, 0.18, boxstyle="round,pad=0.05",
                          facecolor=fc, edgecolor=ec, linewidth=0.8)
    ax.add_patch(box)
    ax.text(leg_x + 0.38, leg_y + 0.09, label, fontsize=7, va="center", color="#333333")
    leg_x += 1.4

# Source annotation
ax.text(15.5, 0.05, "Source: ncf_engine.py + ncf_v2_meta.json", fontsize=6.5,
        color="#cccccc", ha="right", fontstyle="italic")
ax.text(15.5, 5.65, "资料来源：作者自绘", fontsize=6.5, color="#cccccc", ha="right")

# ---- Save ----
fig.tight_layout(pad=1.0)
out_base = "d:/OneDrive/桌面/毕设/Movie-recommendation-system/diagrams/fig5-1-ncf-gmf-architecture"
fig.savefig(f"{out_base}.pdf", dpi=200, bbox_inches="tight")
fig.savefig(f"{out_base}.png", dpi=200, bbox_inches="tight")
print(f"Saved: {out_base}.pdf, {out_base}.png")
plt.close()
