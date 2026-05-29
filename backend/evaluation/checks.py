import math


def check_random(per_user_data, candidate_set_size, k):
    if not per_user_data:
        return False, "no data"
    vals = [u.get("precision_at_k", 0.0) for u in per_user_data]
    observed = sum(vals) / len(vals)
    expected = float(k) / float(candidate_set_size) if candidate_set_size > 0 else 0.0
    std_err = math.sqrt(expected * (1.0 - expected) / max(len(vals), 1))
    lo = expected - 3.0 * std_err
    hi = expected + 3.0 * std_err
    passed = lo <= observed <= hi
    msg = f"P@K={observed:.6f} expected ~{expected:.6f} [{lo:.6f}, {hi:.6f}]"
    return passed, msg


def check_oracle(per_user_data):
    if not per_user_data:
        return False, "no data"
    r_vals = [u.get("recall_at_k", 0.0) for u in per_user_data]
    n_vals = [u.get("ndcg_at_k", 0.0) for u in per_user_data]
    r_mean = sum(r_vals) / len(r_vals)
    n_mean = sum(n_vals) / len(n_vals)
    passed = abs(r_mean - 1.0) < 1e-6 and abs(n_mean - 1.0) < 1e-6
    msg = f"R@K={r_mean:.6f} (expect 1.0), NDCG@K={n_mean:.6f} (expect 1.0)"
    return passed, msg


def check_popularity(itemcf_data, pop_data):
    if not itemcf_data or not pop_data:
        return False, "no data"
    itemcf_r = sum(u.get("recall_at_k", 0.0) for u in itemcf_data) / len(itemcf_data)
    pop_r = sum(u.get("recall_at_k", 0.0) for u in pop_data) / len(pop_data)
    passed = itemcf_r > pop_r
    msg = f"ItemCF R@K={itemcf_r:.4f} vs Popularity R@K={pop_r:.4f}"
    return passed, msg


def check_invariants(all_per_user_data, itemcf_r_at_200_per_user):
    violations = []

    for model_name, per_user in all_per_user_data.items():
        for u in per_user:
            for metric in ["precision_at_k", "recall_at_k", "ndcg_at_k", "mrr_at_k", "map_at_k"]:
                v = u.get(metric)
                if v is not None and not (0.0 <= v <= 1.0 + 1e-9):
                    violations.append(f"{model_name} user={u.get('user_id','?')} {metric}={v}")

    if "hybrid" in all_per_user_data and itemcf_r_at_200_per_user is not None:
        hybrid_r = []
        for u in all_per_user_data["hybrid"]:
            hybrid_r.append(u.get("recall_at_k", 0.0))
        hybrid_r_mean = sum(hybrid_r) / len(hybrid_r) if hybrid_r else 0.0

        itemcf_r200 = []
        for u in itemcf_r_at_200_per_user:
            itemcf_r200.append(u.get("recall_at_200", 0.0))
        itemcf_r200_mean = sum(itemcf_r200) / len(itemcf_r200) if itemcf_r200 else 0.0

        if hybrid_r_mean > itemcf_r200_mean + 1e-9:
            violations.append(
                f"Hybrid R@10={hybrid_r_mean:.4f} > ItemCF R@200={itemcf_r200_mean:.4f}"
            )

    return len(violations) == 0, violations
