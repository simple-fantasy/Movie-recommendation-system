"""Figure: Ablation experiment results for thesis Chapter 6.4.
Reads data from ablation_results.json.
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

with open(ARTIFACTS / "ablation_results.json") as f:
    data = json.load(f)

# ---- Baseline values for reference lines ----
baselines = data["baselines"]
itemcf_baseline_ndcg = baselines["itemcf"]["ndcg_at_k"]
ncf_baseline_ndcg = baselines["ncf"]["ndcg_at_k"]

# ---- Figure 1: Hybrid recall_k ablation ----
hybrid_data = data["hybrid_recall_k"]
rk_vals = [d["recall_k"] for d in hybrid_data]
rk_ndcg = [d["ndcg_at_k"] for d in hybrid_data]
rk_recall = [d["recall_at_k"] for d in hybrid_data]

fig1, ax1 = plt.subplots(figsize=pubstyle.figsize("single"))

pal = colors.categorical(3)
ax1.plot(rk_vals, rk_ndcg, "o-", color=pal[0], linewidth=1.5, markersize=6, label="NDCG@10")
ax1.plot(rk_vals, rk_recall, "s--", color=pal[1], linewidth=1.5, markersize=6, label="R@10")

# Baseline: ItemCF NDCG
ax1.axhline(y=itemcf_baseline_ndcg, color=pal[2], linewidth=1, linestyle=":", alpha=0.8)
ax1.text(520, itemcf_baseline_ndcg + 0.0008, f"ItemCF baseline ({itemcf_baseline_ndcg:.4f})",
         fontsize=7, color=pal[2], ha="right")

# Highlight best point
best_idx = np.argmax(rk_ndcg)
ax1.annotate(f"recall_k=50\nNDCG={rk_ndcg[best_idx]:.4f}",
             xy=(rk_vals[best_idx], rk_ndcg[best_idx]),
             xytext=(150, rk_ndcg[best_idx] + 0.003),
             fontsize=7.5, fontweight="bold", color=pal[0],
             arrowprops=dict(arrowstyle="->", color=pal[0], lw=0.8))

ax1.set_xlabel("recall_k (Hybrid recall candidates)", fontsize=8)
ax1.set_ylabel("Score", fontsize=8)
ax1.set_xticks(rk_vals)
ax1.legend(loc="lower left", fontsize=7.5, frameon=False, ncol=2)
ax1.set_title("(a) Hybrid recall_k vs NDCG@10 / R@10", fontsize=9, fontweight="bold", loc="left", color="#444")

export.save(fig1, "fig_ablation_recallk", formats=("pdf", "svg", "png"),
            outdir=str(PROJECT / "figures"))
plt.close(fig1)

# ---- Figure 2: ItemCF per_seed_limit ablation ----
itemcf_data = data["itemcf_per_seed"]
psl_vals = [d["per_seed_limit"] for d in itemcf_data]
psl_ndcg = [d["ndcg_at_k"] for d in itemcf_data]
psl_recall = [d["recall_at_k"] for d in itemcf_data]
psl_coverage = [d["coverage"] for d in itemcf_data]

fig2, ax2 = plt.subplots(figsize=pubstyle.figsize("single"))

ax2.plot(psl_vals, psl_ndcg, "o-", color=pal[0], linewidth=1.5, markersize=6, label="NDCG@10")
ax2.plot(psl_vals, psl_recall, "s--", color=pal[1], linewidth=1.5, markersize=6, label="R@10")

# Baseline: psl=50 (current default)
psl50_idx = psl_vals.index(50)
ax2.axhline(y=psl_ndcg[psl50_idx], color=pal[2], linewidth=1, linestyle=":", alpha=0.8)
ax2.text(105, psl_ndcg[psl50_idx] + 0.0008, f"psl=50 baseline ({psl_ndcg[psl50_idx]:.4f})",
         fontsize=7, color=pal[2], ha="right")

# Highlight best point
best_idx2 = np.argmax(psl_ndcg)
ax2.annotate(f"psl=10\nNDCG={psl_ndcg[best_idx2]:.4f}\nCov={psl_coverage[best_idx2]:.4f}",
             xy=(psl_vals[best_idx2], psl_ndcg[best_idx2]),
             xytext=(30, psl_ndcg[best_idx2] + 0.003),
             fontsize=7.5, fontweight="bold", color=pal[0],
             arrowprops=dict(arrowstyle="->", color=pal[0], lw=0.8))

ax2.set_xlabel("per_seed_limit (ItemCF neighbor limit)", fontsize=8)
ax2.set_ylabel("Score", fontsize=8)
ax2.set_xticks(psl_vals)
ax2.legend(loc="lower right", fontsize=7.5, frameon=False, ncol=2)
ax2.set_title("(b) ItemCF per_seed_limit vs NDCG@10 / R@10", fontsize=9, fontweight="bold", loc="left", color="#444")

export.save(fig2, "fig_ablation_perseed", formats=("pdf", "svg", "png"),
            outdir=str(PROJECT / "figures"))
plt.close(fig2)

print("Done: figures/fig_ablation_recallk.{pdf,svg,png}")
print("Done: figures/fig_ablation_perseed.{pdf,svg,png}")
