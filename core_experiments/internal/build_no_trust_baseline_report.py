#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

SEED_PATTERN = re.compile(r"_seed(\d+)$")


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).resolve().read_text(encoding="utf-8"))


def extract_seed_key(run_name: str, fallback_index: int) -> str:
    match = SEED_PATTERN.search(str(run_name))
    if match:
        return str(match.group(1))
    return f"row_{fallback_index}"


def metric_seed_map(obj: dict, metric: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for idx, row in enumerate(obj.get("rows", [])):
        seed_key = extract_seed_key(str(row.get("run_name", "")), idx)
        out[seed_key] = float(row.get(metric, 0.0))
    return out


def aligned_pairs(reference: dict[str, float], candidate: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    keys = sorted(set(reference) & set(candidate), key=lambda x: (len(str(x)), str(x)))
    if not keys:
        return np.asarray([], dtype=np.float64), np.asarray([], dtype=np.float64)
    ref = np.asarray([float(reference[k]) for k in keys], dtype=np.float64)
    cand = np.asarray([float(candidate[k]) for k in keys], dtype=np.float64)
    return ref, cand


def paired_sign_flip_p_value(reference: dict[str, float], candidate: dict[str, float]) -> float | None:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size <= 0:
        return None
    diff = (ref - cand).astype(np.float64, copy=False)
    diff = diff[np.abs(diff) > 1e-12]
    if diff.size <= 0:
        return 1.0
    observed = float(abs(np.mean(diff)))
    if diff.size <= 18:
        total = 1 << int(diff.size)
        extreme = 0
        for mask in range(total):
            signs = np.ones(diff.size, dtype=np.float64)
            for bit in range(diff.size):
                if (mask >> bit) & 1:
                    signs[bit] = -1.0
            stat = float(abs(np.mean(signs * diff)))
            if stat + 1e-12 >= observed:
                extreme += 1
        return float(extreme / total)
    rng = np.random.default_rng(20260402)
    signs = rng.choice(np.asarray([-1.0, 1.0], dtype=np.float64), size=(50000, diff.size))
    boot = np.abs((signs * diff[None, :]).mean(axis=1))
    return float(np.mean(boot + 1e-12 >= observed))


def build_condition_row(condition: str, trust_obj: dict, keepall_obj: dict) -> dict:
    trust_f1 = [float(row["test_f1"]) for row in trust_obj.get("rows", [])]
    keepall_f1 = [float(row["test_f1"]) for row in keepall_obj.get("rows", [])]
    trust_fpr = [float(row["test_fpr"]) for row in trust_obj.get("rows", [])]
    keepall_fpr = [float(row["test_fpr"]) for row in keepall_obj.get("rows", [])]
    trust_f1_map = metric_seed_map(trust_obj, "test_f1")
    keepall_f1_map = metric_seed_map(keepall_obj, "test_f1")
    paired_trust_f1, paired_keepall_f1 = aligned_pairs(trust_f1_map, keepall_f1_map)
    p_value = None
    t_stat = None
    paired_sign_flip = paired_sign_flip_p_value(trust_f1_map, keepall_f1_map)
    paired_n = int(min(paired_trust_f1.size, paired_keepall_f1.size))
    if paired_n >= 2:
        if np.allclose(paired_trust_f1, paired_keepall_f1):
            t_stat = 0.0
            p_value = 1.0
        else:
            t_stat, p_value = stats.ttest_rel(paired_trust_f1, paired_keepall_f1)
            if np.isfinite(p_value) and np.isfinite(t_stat):
                p_value = float(p_value)
                t_stat = float(t_stat)
            else:
                p_value = None
                t_stat = None
    return {
        "condition": condition,
        "trust_aware": {
            "test_f1_mean": float(trust_obj["stats"]["test_f1"]["mean"]),
            "test_f1_std": float(trust_obj["stats"]["test_f1"]["std"]),
            "test_fpr_mean": float(trust_obj["stats"]["test_fpr"]["mean"]),
            "test_fpr_std": float(trust_obj["stats"]["test_fpr"]["std"]),
            "kept_clients_mean": float(trust_obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
            "kept_poisoned_clients_mean": float(trust_obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
            "n": int(trust_obj["stats"]["test_f1"]["n"]),
        },
        "keep_all": {
            "test_f1_mean": float(keepall_obj["stats"]["test_f1"]["mean"]),
            "test_f1_std": float(keepall_obj["stats"]["test_f1"]["std"]),
            "test_fpr_mean": float(keepall_obj["stats"]["test_fpr"]["mean"]),
            "test_fpr_std": float(keepall_obj["stats"]["test_fpr"]["std"]),
            "kept_clients_mean": float(keepall_obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
            "kept_poisoned_clients_mean": float(keepall_obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
            "n": int(keepall_obj["stats"]["test_f1"]["n"]),
        },
        "delta_trust_minus_keepall": {
            "test_f1": float(trust_obj["stats"]["test_f1"]["mean"] - keepall_obj["stats"]["test_f1"]["mean"]),
            "test_fpr": float(trust_obj["stats"]["test_fpr"]["mean"] - keepall_obj["stats"]["test_fpr"]["mean"]),
            "kept_clients": float(trust_obj["stats"].get("kept_clients", {}).get("mean", 0.0) - keepall_obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
            "kept_poisoned_clients": float(trust_obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0) - keepall_obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
        },
        "f1_p_value_trust_vs_keepall": p_value,
        "f1_t_stat_trust_vs_keepall": t_stat,
        "f1_test_type_trust_vs_keepall": "paired_ttest",
        "f1_sign_flip_p_value_trust_vs_keepall": paired_sign_flip,
        "f1_paired_n_trust_vs_keepall": paired_n if paired_n > 0 else None,
    }


def plot_rows(rows: list[dict], output_figure: Path, scenario_label: str) -> None:
    labels = [str(row["condition"]) for row in rows]
    x = np.arange(len(labels))
    width = 0.35

    trust_f1 = [float(row["trust_aware"]["test_f1_mean"]) for row in rows]
    keepall_f1 = [float(row["keep_all"]["test_f1_mean"]) for row in rows]
    trust_f1_std = [float(row["trust_aware"]["test_f1_std"]) for row in rows]
    keepall_f1_std = [float(row["keep_all"]["test_f1_std"]) for row in rows]
    trust_fpr = [float(row["trust_aware"]["test_fpr_mean"]) for row in rows]
    keepall_fpr = [float(row["keep_all"]["test_fpr_mean"]) for row in rows]
    trust_fpr_std = [float(row["trust_aware"]["test_fpr_std"]) for row in rows]
    keepall_fpr_std = [float(row["keep_all"]["test_fpr_std"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2))

    axes[0].bar(x - width / 2, trust_f1, width, yerr=trust_f1_std, capsize=4, label="Trust-aware")
    axes[0].bar(x + width / 2, keepall_f1, width, yerr=keepall_f1_std, capsize=4, label="Keep-all")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_title(f"{scenario_label} F1: Trust-Aware vs Keep-All")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend()

    axes[1].bar(x - width / 2, trust_fpr, width, yerr=trust_fpr_std, capsize=4, label="Trust-aware")
    axes[1].bar(x + width / 2, keepall_fpr, width, yerr=keepall_fpr_std, capsize=4, label="Keep-all")
    axes[1].set_xticks(x, labels)
    axes[1].set_ylim(0.0, max(trust_fpr + keepall_fpr) + 0.1)
    axes[1].set_title(f"{scenario_label} FPR: Trust-Aware vs Keep-All")
    axes[1].grid(axis="y", alpha=0.25)

    fig.tight_layout()
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure, dpi=220)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Build a trust-aware vs keep-all comparison report")
    p.add_argument("--trust-clean-file", required=True)
    p.add_argument("--trust-sign-file", required=True)
    p.add_argument("--trust-update-file", required=True)
    p.add_argument("--keepall-clean-file", required=True)
    p.add_argument("--keepall-sign-file", required=True)
    p.add_argument("--keepall-update-file", required=True)
    p.add_argument("--scenario-label", default="Scenario-H")
    p.add_argument("--output-table", required=True)
    p.add_argument("--output-figure", required=True)
    args = p.parse_args()

    rows = [
        build_condition_row("clean", load_json(args.trust_clean_file), load_json(args.keepall_clean_file)),
        build_condition_row("sign_flip_frac0p4", load_json(args.trust_sign_file), load_json(args.keepall_sign_file)),
        build_condition_row("update_noise_frac0p4", load_json(args.trust_update_file), load_json(args.keepall_update_file)),
    ]

    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(
        json.dumps({"scenario_label": str(args.scenario_label), "rows": rows}, indent=2),
        encoding="utf-8",
    )
    plot_rows(rows, Path(args.output_figure).resolve(), scenario_label=str(args.scenario_label))
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
