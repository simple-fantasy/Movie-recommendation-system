"""Figure: Model evaluation comparison for thesis Chapter 6.
Reads live data from evaluation_results.json and full_ranking_final.json.
Replaces the old hardcoded version (2026-05-26 audit).
"""
import sys, json
from pathlib import Path

SKILL = Path("C:/Users/姚锡岳/.claude/skills/figura")
sys.path.insert(0, str(SKILL / "scripts"))
import matplotlib
matplotlib.use("Agg")
import pubstyle, colors, export
import matplotlib.pyplot as plt
import numpy as np

pubstyle.apply()
colors.apply_cycle()

PROJECT = Path(__file__).resolve().parents[1]
ARTIFACTS = PROJECT / "backend" / "artifacts"

# ---- Load data ----
with open(ARTIFACTS / "evaluation_results.json") as f:
    p2 = json.load(f)
with open(ARTIFACTS / "full_ranking_final.json") as f:
    fr = json.load(f)

# ============================================================
# Figure 1: C_all=13K protocol — 7 models × 3 metrics
# ============================================================
models_order = ["random", "popularity", "lightgcn", "ncf", "hybrid", "ease", "itemcf"]
models_label = ["Random", "Popular.", "LightGCN", "NCF", "Hybrid", "EASE", "ItemCF"]
metrics_keys = ["precision_at_k", "recall_at_k", "ndcg_at_k"]
metrics_label = ["Precision@10", "Recall@10", "NDCG@10"]

data_c13 = {}
for m in models_order:
    s = p2["summary"].get(m, {})
    data_c13[m] = [s.get(k, 0.0) for k in metrics_keys]

fig1, ax1 = plt.subplots(figsize=pubstyle.figsize("double"))

x = np.arange(len(models_order))
width = 0.26
pal = colors.categorical(len(metrics_keys))

for i, (metric, label) in enumerate(zip(metrics_keys, metrics_label)):
    vals = [data_c13[m][i] for m in models_order]
    offset = (i - (len(metrics_keys) - 1) / 2) * width
    ax1.bar(x + offset, vals, width, label=label,
            color=pal[i], edgecolor="white", linewidth=0.4)

ax1.set_xticks(x)
ax1.set_xticklabels(models_label, rotation=20, ha="right", fontsize=7)
ax1.set_ylabel("Score", fontsize=8)
y_max = max(max(v) for v in data_c13.values())
ax1.set_ylim(0, y_max * 1.18)
ax1.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=3, handlelength=1.2)

# Value labels on highest bar per model
for j, m in enumerate(models_order):
    best_idx = np.argmax(data_c13[m])
    best_val = data_c13[m][best_idx]
    offset = (best_idx - 1) * width
    ax1.text(x[j] + offset, best_val + y_max * 0.012, f"{best_val:.3f}",
             ha="center", va="bottom", fontsize=5.8, color=pal[best_idx], fontweight="bold")

ax1.set_title("(a) C_all=13K protocol — 7 models, full ranking, 10K users",
              fontsize=8.5, loc="left", color="#444444")

# ============================================================
# Figure 2: Full 80K protocol — Coverage comparison
# ============================================================
fr_results = {r["model"]: r for r in fr["results"]}
cov_models = ["lightgcn", "itemcf", "ease"]
cov_labels = ["LightGCN", "ItemCF", "EASE"]
cov_values = [fr_results[m]["coverage"] for m in cov_models]

fig2, ax2 = plt.subplots(figsize=pubstyle.figsize("single"))

cov_colors = [colors.OKABE_ITO[0], colors.OKABE_ITO[2], colors.OKABE_ITO[1]]
bars = ax2.bar(cov_labels, cov_values, color=cov_colors, edgecolor="white",
               linewidth=0.5, width=0.45)

for bar, v in zip(bars, cov_values):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
             f"{v:.4f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

# EASE advantage annotation
ease_val = fr_results["ease"]["coverage"]
icf_val = fr_results["itemcf"]["coverage"]
ratio = ease_val / icf_val
ax2.annotate(f"{ratio:.1f}x vs ItemCF\np < 0.0004", xy=(2, ease_val),
             xytext=(1.5, ease_val * 0.55), fontsize=7.5, color="#333333",
             arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8),
             bbox=dict(boxstyle="round,pad=0.25", facecolor="#fff8e1",
                       edgecolor="#ddcc88", linewidth=0.5))

ax2.set_ylabel("Coverage@10", fontsize=8)
ax2.set_ylim(0, max(cov_values) * 1.3)
ax2.set_title("(b) Full 80K protocol — coverage comparison, 10K users",
              fontsize=8.5, loc="left", color="#444444")

# ---- Save ----
outdir = str(PROJECT / "figures")
export.save(fig1, "fig_eval_comparison", formats=("pdf", "svg", "png"), outdir=outdir)
export.save(fig2, "fig_coverage", formats=("pdf", "svg", "png"), outdir=outdir)
plt.close("all")
print("Done: figures/fig_eval_comparison.{pdf,svg,png}")
print("Done: figures/fig_coverage.{pdf,svg,png}")
