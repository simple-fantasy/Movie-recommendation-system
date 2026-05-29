"""
论文第6章实验图生成脚本。
运行: python scripts/plot_figures_ch6.py
输出: thesis/figures/fig6-*.pdf
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "thesis" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

cjk_fonts = [f.name for f in fm.fontManager.ttflist
             if any(k in f.name for k in ["SimSun", "SimHei", "Microsoft YaHei", "Noto Sans CJK"])]
font = cjk_fonts[0] if cjk_fonts else "Times New Roman"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [font, "Times New Roman", "DejaVu Sans"],
    "font.size": 12,
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.format": "pdf",
    "savefig.bbox": "tight",
})

models = ["Random", "Popularity", "LightGCN", "NCF",
          "Hybrid", "EASE", "ItemCF", "Oracle"]

precision = [0.00009, 0.01151, 0.01133, 0.01413,
             0.01467, 0.01550, 0.01666, 0.21045]
recall    = [0.00045, 0.05435, 0.05327, 0.06637,
             0.06893, 0.07572, 0.07715, 1.00000]
map_score = [0.00008, 0.02049, 0.02050, 0.02434,
             0.02487, 0.02659, 0.02966, 1.00000]
ndcg = [0.00020, 0.03403, 0.03381, 0.04089, 0.04210, 0.04493, 0.04903, 1.00000]
mrr  = [0.00016, 0.03878, 0.03885, 0.04548, 0.04662, 0.04789, 0.05625, 1.00000]


def plot_fig6_1():
    """图6-1: 各模型推荐精度对比"""
    fig, ax = plt.subplots(figsize=(10, 5.8))
    x = np.arange(len(models))
    width = 0.25

    ax.bar(x - width, precision, width, label="Precision@10",
           color="white", edgecolor="black", linewidth=1.0, hatch="///")
    ax.bar(x, recall, width, label="Recall@10",
           color="white", edgecolor="black", linewidth=1.0, hatch="...")
    ax.bar(x + width, map_score, width, label="MAP@10",
           color="white", edgecolor="black", linewidth=1.0, hatch="\\\\")

    # 只在非 Oracle 柱顶标值 (字体缩小, 避免重叠)
    for i in range(len(models) - 1):
        ax.text(i - width, precision[i] + 0.0004, f"{precision[i]:.4f}",
                ha="center", fontsize=5.5, rotation=90, color="#555")
        ax.text(i, recall[i] + 0.0008, f"{recall[i]:.4f}",
                ha="center", fontsize=5.5, rotation=90, color="#555")
        ax.text(i + width, map_score[i] + 0.0004, f"{map_score[i]:.4f}",
                ha="center", fontsize=5.5, rotation=90, color="#555")

    # Oracle 标注 (图上空白区域)
    ax.text(7, 0.088, "Oracle\nP@10=0.2105\nR@10=1.0  MAP=1.0",
            ha="center", fontsize=8.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="black", linewidth=0.8))

    # ItemCF vs NCF — 放在图上方空白处
    y_top = 0.087
    ax.plot([3, 3, 6, 6], [y_top - 0.003, y_top, y_top, y_top - 0.003],
            color="black", linewidth=0.8, clip_on=False)
    ax.text(4.5, y_top + 0.0015, "ItemCF vs NCF: +18.3% (P@10)",
            ha="center", fontsize=9, fontweight="bold")

    ax.set_ylim(0, 0.095)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Score", fontsize=13)
    ax.legend(loc="upper left", frameon=False, fontsize=10, ncol=3)
    ax.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.set_title("Model Ranking Accuracy Comparison (K=10, C_all=13304, 10k users)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Model", fontsize=13)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig6-1.pdf")
    plt.close(fig)
    print("fig6-1.pdf saved")


def plot_fig6_2():
    """图6-2: 各模型排序质量对比"""
    fig, ax = plt.subplots(figsize=(10, 5.8))
    x = np.arange(len(models))
    width = 0.30

    ax.bar(x - width / 2, ndcg, width, label="NDCG@10",
           color="white", edgecolor="black", linewidth=1.2, hatch="///")
    ax.bar(x + width / 2, mrr, width, label="MRR@10",
           color="white", edgecolor="black", linewidth=1.2, hatch="...")

    for i in range(len(models) - 1):
        ax.text(i - width / 2, ndcg[i] + 0.0004, f"{ndcg[i]:.4f}",
                ha="center", fontsize=5.5, rotation=90, color="#555")

    # ItemCF vs NCF — 图上方
    y_top = 0.065
    ax.plot([3, 3, 6, 6], [y_top - 0.002, y_top, y_top, y_top - 0.002],
            color="black", linewidth=0.8, clip_on=False)
    ax.text(4.5, y_top + 0.001, "ItemCF vs NCF: NDCG +19.9%",
            ha="center", fontsize=9, fontweight="bold")

    ax.text(7, 0.058, "Oracle\nNDCG=1.0  MRR=1.0",
            ha="center", fontsize=8.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="black", linewidth=0.8))

    ax.set_ylim(0, 0.070)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Score", fontsize=13)
    ax.legend(loc="upper left", frameon=False, fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.5)
    ax.set_title("Model Ranking Quality Comparison (K=10, C_all=13304, 10k users)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Model", fontsize=13)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig6-2.pdf")
    plt.close(fig)
    print("fig6-2.pdf saved")


# 多样性指标数据 (6模型 × 5指标)
div_models = ["Popularity", "LightGCN", "NCF", "Hybrid", "EASE", "ItemCF"]
div_metrics = {
    "ILS":       [0.14392, 0.13831, 0.11997, 0.12321, 0.02677, 0.15703],
    "Genre Div": [1.14865, 1.17298, 1.17572, 1.15155, 0.90785, 0.96486],
    "Novelty":   [1.40467, 1.42377, 1.69376, 1.71229, 5.92196, 2.40491],
    "Coverage":  [0.01315, 0.01496, 0.04750, 0.05194, 0.65800, 0.10238],
    "Serendip":  [0.01073, 0.01049, 0.01282, 0.01333, 0.01444, 0.01545],
}

def _minmax_norm(series, invert=False):
    """归一化到 [0,1], invert=True 时反转方向"""
    lo, hi = min(series), max(series)
    if hi == lo:
        return [0.5] * len(series)
    vals = [(v - lo) / (hi - lo) for v in series]
    return [1.0 - v for v in vals] if invert else vals


def plot_fig6_3():
    """图6-3: 多样性指标对比 (5张独立柱状图)"""
    metric_specs = [
        ("fig6-3a.pdf", "ILS (lower is better)", "ILS", [0.14392, 0.13831, 0.11997, 0.12321, 0.02677, 0.15703]),
        ("fig6-3b.pdf", "Genre Diversity",         "Genre Div", [1.14865, 1.17298, 1.17572, 1.15155, 0.90785, 0.96486]),
        ("fig6-3c.pdf", "Novelty",                  "Novelty", [1.40467, 1.42377, 1.69376, 1.71229, 5.92196, 2.40491]),
        ("fig6-3d.pdf", "Coverage",                 "Coverage", [0.01315, 0.01496, 0.04750, 0.05194, 0.65800, 0.10238]),
        ("fig6-3e.pdf", "Serendipity",              "Serendip", [0.01073, 0.01049, 0.01282, 0.01333, 0.01444, 0.01545]),
    ]
    hatches = ["///", "|||", "---", "\\\\", "xxx", "..."]

    for fname, mname, _mkey, values in metric_specs:
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(div_models))

        for j, (model, v) in enumerate(zip(div_models, values)):
            edge_w = 2.5 if model == "EASE" else 1.0
            ax.bar(j, v, color="white", edgecolor="black",
                   linewidth=edge_w, hatch=hatches[j], width=0.6)
            ax.text(j, v, f"{v:.4f}" if v < 10 else f"{v:.2f}",
                    ha="center", va="bottom", fontsize=8, rotation=90,
                    color="#333",
                    fontweight="bold" if model == "EASE" else "normal")

        # Coverage 图额外标注 EASE
        if mname == "Coverage":
            ax.annotate("6.4x higher than next best (ItemCF)",
                        xy=(4, 0.66), fontsize=9, ha="center", fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                  edgecolor="black", linewidth=0.8))

        ax.set_xticks(x)
        ax.set_xticklabels(div_models, rotation=15, ha="right", fontsize=11)
        ax.set_ylabel("Score", fontsize=13)
        ax.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.5)
        ax.set_title(mname, fontsize=14, fontweight="bold", pad=10)

        handles = [plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="black",
                                 hatch=h) for h in hatches]
        ax.legend(handles, div_models, loc="lower left",
                  bbox_to_anchor=(1.01, 0), frameon=False,
                  fontsize=9, ncol=1, borderaxespad=0)

        fig.tight_layout(rect=[0, 0, 0.85, 1])
        fig.savefig(OUTPUT_DIR / fname)
        plt.close(fig)
        print(f"{fname} saved")


# 消融实验数据
recall_k_vals   = [50, 100, 200, 500]
recall_k_prec   = [0.01790, 0.01605, 0.01590, 0.01525]
recall_k_rec    = [0.08266, 0.07648, 0.07406, 0.07130]
recall_k_ndcg_v = [0.05096, 0.04628, 0.04544, 0.04406]

per_seed_vals   = [10, 25, 50, 100]
per_seed_prec   = [0.01891, 0.01841, 0.01645, 0.01645]
per_seed_rec    = [0.08626, 0.08300, 0.07397, 0.07397]
per_seed_ndcg_v = [0.05310, 0.05177, 0.04833, 0.04833]


def plot_fig6_4():
    """图6-4: Hybrid recall_k 消融 (双Y轴折线图)"""
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(recall_k_vals))

    # 左Y轴: Precision + Recall
    l1 = ax1.plot(x, recall_k_prec, "s--", color="black",
                   markerfacecolor="white", markersize=10, linewidth=1.5,
                   label="Precision@10")
    l2 = ax1.plot(x, recall_k_rec, "o-", color="black",
                   markerfacecolor="white", markersize=10, linewidth=1.5,
                   label="Recall@10")
    ax1.set_xlabel("recall_k", fontsize=13)
    ax1.set_ylabel("Precision@10 / Recall@10", fontsize=13)
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(v) for v in recall_k_vals], fontsize=11)

    # 右Y轴: NDCG
    ax2 = ax1.twinx()
    l3 = ax2.plot(x, recall_k_ndcg_v, "D-.", color="black",
                   markerfacecolor="lightgray", markersize=10, linewidth=1.5,
                   label="NDCG@10")
    ax2.set_ylabel("NDCG@10", fontsize=13)

    # 最佳点标注 — 用 transAxes 定位, 不挡线
    ax2.text(0.02, 0.92, f"Best: NDCG={recall_k_ndcg_v[0]:.4f}\nat recall_k=50",
             transform=ax2.transAxes, ha="left", va="top",
             fontsize=9, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor="black", linewidth=0.8))

    # 合并图例
    lines = l1 + l2 + l3
    labels = [ln.get_label() for ln in lines]
    ax1.legend(lines, labels, loc="center right", frameon=False, fontsize=10)

    ax1.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.5)
    ax1.set_title("Hybrid Strategy: recall_k Ablation (2000 users)",
                  fontsize=14, fontweight="bold", pad=12)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig6-4.pdf")
    plt.close(fig)
    print("fig6-4.pdf saved")


def plot_fig6_5():
    """图6-5: ItemCF per_seed_limit 消融 (双Y轴折线图)"""
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(per_seed_vals))

    l1 = ax1.plot(x, per_seed_prec, "s--", color="black",
                   markerfacecolor="white", markersize=10, linewidth=1.5,
                   label="Precision@10")
    l2 = ax1.plot(x, per_seed_rec, "o-", color="black",
                   markerfacecolor="white", markersize=10, linewidth=1.5,
                   label="Recall@10")
    ax1.set_xlabel("per_seed_limit", fontsize=13)
    ax1.set_ylabel("Precision@10 / Recall@10", fontsize=13)
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(v) for v in per_seed_vals], fontsize=11)

    ax2 = ax1.twinx()
    l3 = ax2.plot(x, per_seed_ndcg_v, "D-.", color="black",
                   markerfacecolor="lightgray", markersize=10, linewidth=1.5,
                   label="NDCG@10")
    ax2.set_ylabel("NDCG@10", fontsize=13)

    # 最优区间标注
    ax1.axvspan(-0.3, 1.3, alpha=0.06, color="black")
    ax1.text(0.5, per_seed_prec[0] - 0.0012, "optimal\nrange",
             ha="center", fontsize=9, fontweight="bold")

    # 饱和标注 — 放在图右下方空白区, 不挡线
    ax1.text(0.97, 0.08, "per_seed >= 50:\nmetrics saturate\nno further gain",
             transform=ax1.transAxes, ha="right", va="bottom",
             fontsize=9, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor="black", linewidth=0.8))

    lines = l1 + l2 + l3
    labels = [ln.get_label() for ln in lines]
    ax1.legend(lines, labels, loc="center right", frameon=False, fontsize=10)

    ax1.grid(axis="y", linestyle="--", alpha=0.3, linewidth=0.5)
    ax1.set_title("ItemCF Strategy: per_seed_limit Ablation (2000 users)",
                  fontsize=14, fontweight="bold", pad=12)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig6-5.pdf")
    plt.close(fig)
    print("fig6-5.pdf saved")


if __name__ == "__main__":
    plot_fig6_1()
    plot_fig6_2()
    plot_fig6_3()
    plot_fig6_4()
    plot_fig6_5()
    print("Done. Output:", OUTPUT_DIR)
