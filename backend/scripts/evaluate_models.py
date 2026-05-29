# DEPRECATED since 2026-05-25 — use backend.scripts.run_evaluation instead.
"""Multi-model offline evaluation CLI.

Thin wrapper around backend.app.evaluator — all evaluation logic lives there.
Supports: ItemCF, NCF, Hybrid models, fair comparison, K-fold CV, ablation,
statistical tests, and user stratification.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time

from backend.app import create_app
from backend.app.evaluator import (
    AblationRunner, AblationConfig,
    EvalConfig,
    EvaluationEngine,
    StatisticalTests,
    UserStratification,
)
from backend.app.ncf_engine import ncf_engine


def _jsonify(obj):
    """Recursively convert tuple keys to strings for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k) if isinstance(k, tuple) else k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonify(v) for v in obj]
    return obj



def print_table(results: list[dict]) -> None:
    """Print results as a formatted table."""
    header = (
        f"{'Model':<25} {'P@K':<8} {'R@K':<8} {'NDCG@K':<8} {'MAP@K':<8} "
        f"{'MRR@K':<8} {'ILS':<8} {'Novel':<8} {'Cov':<8} {'Users':<8}"
    )
    sep = "-" * len(header)
    print("\n" + "=" * len(header))
    print(header)
    print(sep)
    for r in results:
        print(
            f"{r['model']:<25} "
            f"{r.get('precision_at_k', 0):<8.4f} "
            f"{r.get('recall_at_k', 0):<8.4f} "
            f"{r.get('ndcg_at_k', 0):<8.4f} "
            f"{r.get('map_at_k', 0):<8.4f} "
            f"{r.get('mrr_at_k', 0):<8.4f} "
            f"{r.get('ils_at_k', 0):<8.4f} "
            f"{r.get('novelty_at_k', 0):<8.4f} "
            f"{r.get('coverage', 0):<8.4f} "
            f"{r.get('users_evaluated', 0):<8}"
        )
    print("=" * len(header))


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-model offline evaluation")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--like-threshold", type=float, default=4.0)
    parser.add_argument("--min-ratings", type=int, default=10)
    parser.add_argument("--per-seed-limit", type=int, default=50)
    parser.add_argument("--sim-topk-per-movie", type=int, default=50)
    parser.add_argument("--recall-k", type=int, default=100)
    parser.add_argument("--models", nargs="+", choices=["itemcf", "ncf", "hybrid", "lightgcn", "ease", "popularity", "random", "all"],
                        default=["all"])
    parser.add_argument("--ablation", action="store_true")
    parser.add_argument("--ncf-candidate-pool-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fair", action="store_true",
                        help="Fair evaluation: shared candidate pool per user")
    parser.add_argument("--folds", type=int, default=1,
                        help="K-fold temporal CV (1=leave-last-out)")
    parser.add_argument("--popularity-buckets", type=int, default=0,
                        help="Popularity buckets for stratified sampling (0=uniform, 5=quantile)")
    parser.add_argument("--full-ranking", action="store_true",
                        help="Full ranking evaluation: all models rank all unseen items")
    parser.add_argument("--n-users", type=int, default=0,
                        help="Limit evaluation to N random test users (0=all)")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        models_list = ["itemcf", "ncf", "hybrid", "lightgcn", "ease"] if "all" in args.models else args.models
        # create_app() already kicked off NCF preload via _start_ncf_preload().
        # Wait for it to finish instead of calling load() again (avoids _loading race).
        if "ncf" in models_list or "hybrid" in models_list:
            print("Waiting for NCF model...")
            waited = 0
            while ncf_engine.is_loading() and waited < 120:
                time.sleep(0.5)
                waited += 0.5
            if not ncf_engine.is_ready() and not ncf_engine.is_loading():
                ncf_engine.load()
            if ncf_engine.is_ready():
                print(f"  NCF model ready: {ncf_engine.num_users} users, "
                      f"{ncf_engine.num_items} items")
            else:
                print("  WARNING: NCF model not available. NCF/Hybrid will be skipped.")

        config = EvalConfig(
            k=int(args.k),
            like_threshold=float(args.like_threshold),
            min_ratings=int(args.min_ratings),
            per_seed_limit=int(args.per_seed_limit),
            sim_topk_per_movie=int(args.sim_topk_per_movie),
            recall_k=int(args.recall_k),
            ncf_candidate_pool_size=int(args.ncf_candidate_pool_size),
            seed=int(args.seed),
            fair_mode=args.fair,
            n_folds=int(args.folds),
            popularity_buckets=int(args.popularity_buckets),
            full_ranking=args.full_ranking,
            n_test_users=int(args.n_users),
            models=models_list,
        )

        # --- Main evaluation ---
        print("\n" + "=" * 60)
        mode_label = "FAIR EVALUATION" if args.fair else "MAIN EVALUATION"
        if args.folds > 1:
            mode_label += f" ({args.folds}-fold CV)"
        print(mode_label)
        print("=" * 60)

        engine = EvaluationEngine(config)
        print("Loading data...")
        engine.load_data()
        print(f"  {len(engine._ratings_by_user)} users, "
              f"{len(engine._all_item_ids)} items")

        metrics_list = engine.run()

        # --- Print results ---
        results_dict = [asdict(m) for m in metrics_list]
        print_table(results_dict)

        # --- Save immediately (before stats/strat, so data persists even if they crash) ---
        output_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "k": args.k,
                "like_threshold": args.like_threshold,
                "min_ratings": args.min_ratings,
                "per_seed_limit": args.per_seed_limit,
                "sim_topk_per_movie": args.sim_topk_per_movie,
                "recall_k": args.recall_k,
                "ncf_candidate_pool_size": args.ncf_candidate_pool_size,
                "seed": args.seed,
                "fair_mode": args.fair,
                "n_folds": args.folds,
            },
            "results": results_dict,
        }

        if args.output:
            out_path = Path(args.output)
        else:
            out_path = Path(__file__).resolve().parents[1] / "artifacts" / "evaluation_results.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nResults saved to: {out_path}")

        # --- Statistical tests (best-effort, after save) ---
        stats_output = None
        acc_metrics = ["precision", "recall", "ndcg", "map", "mrr"]
        if len(metrics_list) >= 2:
            print("\n" + "=" * 60)
            print("STATISTICAL TESTS (Wilcoxon signed-rank + Bonferroni-Holm)")
            print("=" * 60)

            models_data = {}
            for m in metrics_list:
                if m.per_user_metrics and "users" in m.per_user_metrics:
                    models_data[m.model] = m.per_user_metrics["users"]

            if models_data:
                try:
                    stats_output = StatisticalTests.pairwise_comparison(
                        models_data, acc_metrics
                    )
                    for metric, pairs in stats_output.items():
                        print(f"\n  {metric}:")
                        for (ma, mb), info in pairs.items():
                            sig_mark = "*" if info["significant"] == "yes" else " "
                            print(
                                f"    {ma} vs {mb}: "
                                f"p={info['p_value']:.4f} "
                                f"(corrected: {info['p_corrected']:.4f}) "
                                f"d={info['cohens_d']:.3f} [{sig_mark}]"
                            )
                except Exception as e:
                    print(f"  Statistical tests failed: {e}")
                    stats_output = {"error": str(e)}

        # --- User stratification (best-effort) ---
        strat_output = None
        if metrics_list and metrics_list[0].per_user_metrics:
            print("\n" + "=" * 60)
            print("USER STRATIFICATION (Cold <=5 / Warm 6-20 / Hot >20)")
            print("=" * 60)
            strat_output = {}
            for m in metrics_list:
                if m.per_user_metrics and "users" in m.per_user_metrics:
                    try:
                        report = UserStratification.report_by_stratum(
                            m.per_user_metrics["users"],
                            acc_metrics + ["ils", "genre_diversity", "novelty", "serendipity"],
                        )
                        strat_output[m.model] = report
                        print(f"\n  {m.model}:")
                        for stratum, vals in report.items():
                            n = vals.get("n_users", 0)
                            ndcg = vals.get("ndcg", 0)
                            print(f"    {stratum:<6}: n={n:<6} NDCG={ndcg:.4f}")
                    except Exception as e:
                        print(f"  Stratification failed for {m.model}: {e}")

        # --- Ablation study ---
        if args.ablation:
            print("\n" + "=" * 60)
            print("ABLATION STUDY")
            print("=" * 60)
            ablation_runner = AblationRunner(engine)
            ablation_configs = AblationRunner.default_ablations()
            ablation_metrics = ablation_runner.run_ablation(ablation_configs)
            ablation_dicts = [asdict(m) for m in ablation_metrics]
            results_dict.extend(ablation_dicts)
            print_table(ablation_dicts)

        # --- Re-save with stats + stratification appended ---
        if stats_output or strat_output or args.ablation:
            if stats_output:
                output_data["statistical_tests"] = _jsonify(stats_output)
            if strat_output:
                output_data["stratification"] = strat_output
            if args.ablation:
                output_data["results"] = results_dict
            out_path.write_text(
                json.dumps(output_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            print(f"\nUpdated results: {out_path}")


if __name__ == "__main__":
    main()
