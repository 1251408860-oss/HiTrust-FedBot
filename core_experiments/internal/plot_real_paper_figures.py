#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).resolve().read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_comm_tradeoff(obj: dict, output_dir: Path) -> None:
    rows = sorted(obj["rows"], key=lambda x: float(x["total_bytes_est"]))
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    for row in rows:
        ax.scatter(float(row["total_bytes_est"]), float(row["test_f1"]), s=80)
        ax.annotate(str(row["tuning_mode"]), (float(row["total_bytes_est"]), float(row["test_f1"])), xytext=(6, 4), textcoords="offset points")
    ax.set_xlabel("Total Communication Bytes")
    ax.set_ylabel("Test F1")
    ax.set_title("Communication-Accuracy Tradeoff")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "comm_tradeoff.png", dpi=220)
    plt.close(fig)


def plot_sign_flip_grid(obj: dict, output_dir: Path) -> None:
    rows = sorted(obj["rows"], key=lambda x: float(x["poison_frac"]))
    x = [float(r["poison_frac"]) for r in rows]
    f1 = [float(r["test_f1"]) for r in rows]
    fpr = [float(r["test_fpr"]) for r in rows]
    kept = [float(r["kept_poisoned_clients"]) for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].plot(x, f1, marker="o", label="Test F1")
    axes[0].plot(x, fpr, marker="s", label="Test FPR")
    axes[0].set_xlabel("Poison Fraction")
    axes[0].set_ylabel("Metric")
    axes[0].set_title("Sign-Flip Robustness")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(x, kept, marker="^", color="tab:red")
    axes[1].set_xlabel("Poison Fraction")
    axes[1].set_ylabel("Kept Poisoned Clients")
    axes[1].set_title("Trust Filter Leakage")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "sign_flip_robustness.png", dpi=220)
    plt.close(fig)


def plot_cross_scenario_heatmap(obj: dict, output_dir: Path) -> None:
    scenarios = sorted({row["scenario_name"] for row in obj["rows"]})
    conditions = list(obj["conditions"])
    value_map = {(row["scenario_name"], row["condition"]): float(row["test_f1"]) for row in obj["rows"]}
    matrix = np.array([[value_map.get((scenario, condition), np.nan) for condition in conditions] for scenario in scenarios], dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    im = ax.imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))
    ax.set_xticks(range(len(conditions)), conditions, rotation=20, ha="right")
    ax.set_yticks(range(len(scenarios)), scenarios)
    ax.set_title("Cross-Scenario Test F1 Matrix")
    for i, scenario in enumerate(scenarios):
        for j, condition in enumerate(conditions):
            ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.9, label="Test F1")
    fig.tight_layout()
    fig.savefig(output_dir / "cross_scenario_f1_heatmap.png", dpi=220)
    plt.close(fig)


def plot_aggregation_sign_flip(summary_obj: dict, output_dir: Path) -> None:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in summary_obj["rows"]:
        agg = str(row["aggregation"])
        grouped[agg]["f1"].append(float(row["test_f1"]))
        grouped[agg]["fpr"].append(float(row["test_fpr"]))
    aggs = list(sorted(grouped))
    f1_means = [np.mean(grouped[a]["f1"]) for a in aggs]
    f1_stds = [np.std(grouped[a]["f1"], ddof=1) if len(grouped[a]["f1"]) > 1 else 0.0 for a in aggs]
    fpr_means = [np.mean(grouped[a]["fpr"]) for a in aggs]
    fpr_stds = [np.std(grouped[a]["fpr"], ddof=1) if len(grouped[a]["fpr"]) > 1 else 0.0 for a in aggs]

    x = np.arange(len(aggs))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.bar(x - width / 2, f1_means, width, yerr=f1_stds, label="Test F1", capsize=4)
    ax.bar(x + width / 2, fpr_means, width, yerr=fpr_stds, label="Test FPR", capsize=4)
    ax.set_xticks(x, aggs)
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Aggregators Under Sign-Flip@0.4")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "aggregation_sign_flip_comparison.png", dpi=220)
    plt.close(fig)


def plot_ablation_heatmap(obj: dict, output_dir: Path) -> None:
    thresholds = sorted({float(row["trust_threshold"]) for row in obj["rows"]})
    groups = sorted({int(row["num_groups"]) for row in obj["rows"]})
    value_map = {(float(row["trust_threshold"]), int(row["num_groups"])): float(row["test_f1"]) for row in obj["rows"]}
    matrix = np.array([[value_map[(thr, grp)] for grp in groups] for thr in thresholds], dtype=float)

    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    im = ax.imshow(matrix, aspect="auto", cmap="OrRd", vmin=np.min(matrix), vmax=np.max(matrix))
    ax.set_xticks(range(len(groups)), [str(g) for g in groups])
    ax.set_yticks(range(len(thresholds)), [f"{thr:.2f}" for thr in thresholds])
    ax.set_xlabel("num_groups")
    ax.set_ylabel("trust_threshold")
    ax.set_title("Sign-Flip Ablation: Test F1")
    for i, thr in enumerate(thresholds):
        for j, grp in enumerate(groups):
            ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.9, label="Test F1")
    fig.tight_layout()
    fig.savefig(output_dir / "ablation_threshold_groups_heatmap.png", dpi=220)
    plt.close(fig)


def plot_backbone_comparison(
    *,
    feature_clean_obj: dict,
    feature_sign_obj: dict,
    sage_clean_obj: dict,
    sage_sign_obj: dict,
    output_dir: Path,
) -> None:
    labels = ["clean", "sign_flip@0.4"]
    feature_f1 = [
        float(feature_clean_obj["stats"]["test_f1"]["mean"]),
        float(feature_sign_obj["stats"]["test_f1"]["mean"]),
    ]
    sage_f1 = [
        float(sage_clean_obj["stats"]["test_f1"]["mean"]),
        float(sage_sign_obj["stats"]["test_f1"]["mean"]),
    ]
    feature_fpr = [
        float(feature_clean_obj["stats"]["test_fpr"]["mean"]),
        float(feature_sign_obj["stats"]["test_fpr"]["mean"]),
    ]
    sage_fpr = [
        float(sage_clean_obj["stats"]["test_fpr"]["mean"]),
        float(sage_sign_obj["stats"]["test_fpr"]["mean"]),
    ]
    feature_f1_std = [
        float(feature_clean_obj["stats"]["test_f1"]["std"]),
        float(feature_sign_obj["stats"]["test_f1"]["std"]),
    ]
    sage_f1_std = [
        float(sage_clean_obj["stats"]["test_f1"]["std"]),
        float(sage_sign_obj["stats"]["test_f1"]["std"]),
    ]
    feature_fpr_std = [
        float(feature_clean_obj["stats"]["test_fpr"]["std"]),
        float(feature_sign_obj["stats"]["test_fpr"]["std"]),
    ]
    sage_fpr_std = [
        float(sage_clean_obj["stats"]["test_fpr"]["std"]),
        float(sage_sign_obj["stats"]["test_fpr"]["std"]),
    ]

    x = np.arange(len(labels))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.2))
    axes[0].bar(x - width / 2, feature_f1, width, yerr=feature_f1_std, label="FeatureMLP", capsize=4)
    axes[0].bar(x + width / 2, sage_f1, width, yerr=sage_f1_std, label="GraphSAGE", capsize=4)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylim(0.85, 1.01)
    axes[0].set_title("Backbone Comparison: Test F1")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend()

    axes[1].bar(x - width / 2, feature_fpr, width, yerr=feature_fpr_std, label="FeatureMLP", capsize=4)
    axes[1].bar(x + width / 2, sage_fpr, width, yerr=sage_fpr_std, label="GraphSAGE", capsize=4)
    axes[1].set_xticks(x, labels)
    axes[1].set_ylim(0.0, max(feature_fpr + sage_fpr) + 0.05)
    axes[1].set_title("Backbone Comparison: Test FPR")
    axes[1].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "backbone_comparison.png", dpi=220)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Generate paper-ready figures from real experiment summaries")
    p.add_argument("--comm-file", required=True)
    p.add_argument("--sign-flip-grid-file", required=True)
    p.add_argument("--cross-scenario-file", required=True)
    p.add_argument("--aggregation-sign-flip-file", required=True)
    p.add_argument("--ablation-file", required=True)
    p.add_argument("--feature-clean-seed-file", default="")
    p.add_argument("--feature-sign-flip-seed-file", default="")
    p.add_argument("--sage-clean-seed-file", default="")
    p.add_argument("--sage-sign-flip-seed-file", default="")
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)
    plot_comm_tradeoff(load_json(args.comm_file), output_dir)
    plot_sign_flip_grid(load_json(args.sign_flip_grid_file), output_dir)
    plot_cross_scenario_heatmap(load_json(args.cross_scenario_file), output_dir)
    plot_aggregation_sign_flip(load_json(args.aggregation_sign_flip_file), output_dir)
    plot_ablation_heatmap(load_json(args.ablation_file), output_dir)
    if (
        str(args.feature_clean_seed_file).strip()
        and str(args.feature_sign_flip_seed_file).strip()
        and str(args.sage_clean_seed_file).strip()
        and str(args.sage_sign_flip_seed_file).strip()
    ):
        plot_backbone_comparison(
            feature_clean_obj=load_json(args.feature_clean_seed_file),
            feature_sign_obj=load_json(args.feature_sign_flip_seed_file),
            sage_clean_obj=load_json(args.sage_clean_seed_file),
            sage_sign_obj=load_json(args.sage_sign_flip_seed_file),
            output_dir=output_dir,
        )
    print(f"[OK] wrote figures to {output_dir}")


if __name__ == "__main__":
    main()
