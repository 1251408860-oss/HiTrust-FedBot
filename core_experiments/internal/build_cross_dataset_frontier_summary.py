#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


REPO_ROOT = Path(__file__).resolve().parents[2]

METHOD_LABELS = {
    "static": "Static",
    "condfloor": "CondFloor",
    "keepall": "KeepAll",
    "fltrust_like": "FLTrust",
    "caf": "CAF",
    "centered_clipping": "Centered",
    "arc_mean": "ARC+mean",
}

METHOD_COLORS = {
    "static": "#1f77b4",
    "condfloor": "#ff7f0e",
    "keepall": "#d62728",
    "fltrust_like": "#2ca02c",
    "caf": "#9467bd",
    "centered_clipping": "#8c564b",
    "arc_mean": "#e377c2",
}

METHOD_MARKERS = {
    "static": "o",
    "condfloor": "h",
    "keepall": "s",
    "fltrust_like": "D",
    "caf": "^",
    "centered_clipping": "P",
    "arc_mean": "X",
}

NORMALIZE_METHOD_KEY = {
    "trust_aware": "static",
    "static": "static",
    "condfloor": "condfloor",
    "hier_keepall": "keepall",
    "keepall": "keepall",
    "fltrust_like": "fltrust_like",
    "caf": "caf",
    "centered_clipping": "centered_clipping",
    "arc_mean": "arc_mean",
}


@dataclass(frozen=True)
class DatasetSpec:
    dataset_key: str
    title: str
    files: tuple[str, ...]
    methods: tuple[str, ...]


DEFAULT_SPECS = (
    DatasetSpec(
        dataset_key="cabench_scenario_e_update_noise",
        title="Ca-Bench scenario_e\nupdate_noise@0.4",
        files=("paper_hitrust/tables/public_cabench_scenario_e_update_noise_baseline_comparison.json",),
        methods=("static", "keepall", "fltrust_like", "caf", "centered_clipping", "arc_mean"),
    ),
    DatasetSpec(
        dataset_key="cabench_scenario_h_update_noise",
        title="Ca-Bench scenario_h\nupdate_noise@0.4",
        files=(
            "paper_hitrust/tables/public_cabench_scenario_h_update_noise_baseline_comparison.json",
            "paper_hitrust/tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json",
        ),
        methods=("static", "condfloor", "keepall", "fltrust_like", "caf", "centered_clipping", "arc_mean"),
    ),
    DatasetSpec(
        dataset_key="westermo_update_noise",
        title="Westermo\nupdate_noise@0.4",
        files=(
            "paper_hitrust/tables/public_westermo_update_noise_baseline_comparison.json",
            "paper_hitrust/tables/public_westermo_update_noise_condfloor_comparison.json",
        ),
        methods=("static", "condfloor", "keepall", "fltrust_like", "caf", "centered_clipping", "arc_mean"),
    ),
    DatasetSpec(
        dataset_key="litnet2020_udp_update_noise",
        title="LITNET-2020 UDP-flood\nupdate_noise@0.4",
        files=(
            "paper_hitrust/tables/public_litnet2020_udp_update_noise_baseline_comparison.json",
            "paper_hitrust/tables/public_litnet2020_udp_update_noise_condfloor_comparison.json",
        ),
        methods=("static", "condfloor", "keepall", "fltrust_like", "caf", "centered_clipping", "arc_mean"),
    ),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a cross-dataset F1/KP/KC frontier summary figure")
    p.add_argument("--project-root", default=str(REPO_ROOT))
    p.add_argument(
        "--output-table",
        default="paper_hitrust/tables/cross_dataset_f1_kp_kc_frontier_summary.json",
    )
    p.add_argument(
        "--output-figure",
        default="paper_hitrust/figures/cross_dataset_f1_kp_kc_frontier_summary.png",
    )
    p.add_argument(
        "--copy-figure-paths",
        default=(
            "paper_hitrust/figures_sage_main/cross_dataset_f1_kp_kc_frontier_summary.png,"
            "paper_hitrust/figures_eaai/cross_dataset_f1_kp_kc_frontier_summary.png"
        ),
    )
    return p.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_method_key(label: str) -> str | None:
    return NORMALIZE_METHOD_KEY.get(str(label).strip())


def is_pareto_optimal(rows: list[dict[str, Any]], idx: int) -> bool:
    target = rows[idx]
    for j, other in enumerate(rows):
        if j == idx:
            continue
        if (
            float(other["test_f1"]) >= float(target["test_f1"])
            and float(other["kept_clients"]) >= float(target["kept_clients"])
            and float(other["kept_poisoned_clients"]) <= float(target["kept_poisoned_clients"])
            and (
                float(other["test_f1"]) > float(target["test_f1"])
                or float(other["kept_clients"]) > float(target["kept_clients"])
                or float(other["kept_poisoned_clients"]) < float(target["kept_poisoned_clients"])
            )
        ):
            return False
    return True


def load_dataset_rows(project_root: Path, spec: DatasetSpec) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    sources: dict[str, list[str]] = {}
    for rel_path in spec.files:
        path = project_root / rel_path
        obj = load_json(path)
        for raw_row in obj.get("rows", []):
            method_key = normalize_method_key(str(raw_row.get("label", "")))
            if method_key is None or method_key not in spec.methods:
                continue
            merged[method_key] = {
                "dataset_key": spec.dataset_key,
                "dataset_title": spec.title,
                "method_key": method_key,
                "method_label": METHOD_LABELS[method_key],
                "source_files": [],
                "test_f1": float(raw_row["test_f1_mean"]),
                "test_fpr": float(raw_row["test_fpr_mean"]),
                "kept_poisoned_clients": float(raw_row["kept_poisoned_clients_mean"]),
                "kept_clients": float(raw_row["kept_clients_mean"]),
                "n": int(raw_row.get("n", 0)),
            }
            sources.setdefault(method_key, [])
            sources[method_key].append(rel_path)

    rows: list[dict[str, Any]] = []
    for method_key in spec.methods:
        item = merged.get(method_key)
        if item is None:
            continue
        item["source_files"] = sorted(set(sources.get(method_key, [])))
        rows.append(item)

    for idx, row in enumerate(rows):
        row["pareto_optimal"] = bool(is_pareto_optimal(rows, idx))
    return rows


def bubble_size(value: float, *, min_value: float, max_value: float) -> float:
    if max_value <= min_value + 1e-12:
        return 240.0
    ratio = (float(value) - float(min_value)) / max(float(max_value) - float(min_value), 1e-12)
    return 140.0 + 340.0 * max(0.0, min(1.0, ratio))


def build_summary(specs: tuple[DatasetSpec, ...], project_root: Path) -> dict[str, Any]:
    dataset_rows = [load_dataset_rows(project_root, spec) for spec in specs]
    all_rows = [row for rows in dataset_rows for row in rows]
    return {
        "datasets": [
            {
                "dataset_key": spec.dataset_key,
                "dataset_title": spec.title,
                "rows": rows,
            }
            for spec, rows in zip(specs, dataset_rows)
        ],
        "method_labels": METHOD_LABELS,
        "method_colors": METHOD_COLORS,
        "method_markers": METHOD_MARKERS,
        "all_rows": all_rows,
    }


def plot_summary(summary: dict[str, Any], output_figure: Path) -> None:
    datasets = list(summary["datasets"])
    all_rows = list(summary["all_rows"])
    if not all_rows:
        raise RuntimeError("no rows available for cross-dataset frontier summary")

    kc_min = min(float(row["kept_clients"]) for row in all_rows)
    kc_max = max(float(row["kept_clients"]) for row in all_rows)
    x_max = max(float(row["kept_poisoned_clients"]) for row in all_rows) + 0.25
    y_min = min(float(row["test_f1"]) for row in all_rows)
    y_max = max(float(row["test_f1"]) for row in all_rows)
    y_pad = max(0.015, 0.06 * (y_max - y_min))

    fig, axes = plt.subplots(2, 2, figsize=(12.0, 8.6), sharex=True, sharey=True)
    axes_list = list(axes.flatten())

    for ax, dataset in zip(axes_list, datasets):
        rows = list(dataset["rows"])
        frontier = sorted(
            [row for row in rows if bool(row["pareto_optimal"])],
            key=lambda item: (float(item["kept_poisoned_clients"]), -float(item["test_f1"])),
        )
        if frontier:
            ax.plot(
                [float(row["kept_poisoned_clients"]) for row in frontier],
                [float(row["test_f1"]) for row in frontier],
                color="#222222",
                linestyle="--",
                linewidth=1.1,
                alpha=0.8,
                zorder=1,
            )

        for row in rows:
            size = bubble_size(float(row["kept_clients"]), min_value=kc_min, max_value=kc_max)
            ax.scatter(
                float(row["kept_poisoned_clients"]),
                float(row["test_f1"]),
                s=size,
                marker=METHOD_MARKERS[row["method_key"]],
                color=METHOD_COLORS[row["method_key"]],
                edgecolor="#111111" if bool(row["pareto_optimal"]) else "#f5f5f5",
                linewidth=1.8 if bool(row["pareto_optimal"]) else 0.8,
                alpha=0.9,
                zorder=3,
            )

        ax.set_title(str(dataset["dataset_title"]))
        ax.grid(alpha=0.25, linestyle=":")
        ax.set_xlim(-0.1, x_max)
        ax.set_ylim(max(0.0, y_min - y_pad), min(1.02, y_max + y_pad))

    for ax in axes[:, 0]:
        ax.set_ylabel("Test F1")
    for ax in axes[1, :]:
        ax.set_xlabel("Retained Poisoned Clients (KP)")

    method_handles = [
        Line2D(
            [0],
            [0],
            marker=METHOD_MARKERS[key],
            color="w",
            markerfacecolor=METHOD_COLORS[key],
            markeredgecolor="#111111",
            markersize=8,
            linewidth=0,
            label=label,
        )
        for key, label in METHOD_LABELS.items()
    ]
    size_values = [4.0, 6.0, 10.0]
    size_handles = [
        plt.scatter([], [], s=bubble_size(val, min_value=kc_min, max_value=kc_max), color="#999999", alpha=0.45)
        for val in size_values
    ]

    fig.legend(
        handles=method_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=4,
        frameon=False,
    )
    fig.legend(
        handles=size_handles,
        labels=[f"KC={val:.0f}" for val in size_values],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncol=3,
        frameon=False,
        title="Bubble Area",
    )
    fig.text(
        0.5,
        0.02,
        "Higher F1 and higher KC are better; lower KP is better. Black outlines mark 3-metric Pareto-optimal points.",
        ha="center",
        va="center",
        fontsize=10,
    )
    fig.suptitle("Cross-Dataset F1 / KP / KC Frontier Summary", y=1.03, fontsize=15)
    fig.tight_layout(rect=(0.02, 0.06, 0.98, 0.84))
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    output_table = (project_root / str(args.output_table)).resolve()
    output_figure = (project_root / str(args.output_figure)).resolve()
    copy_paths = [
        (project_root / item.strip()).resolve()
        for item in str(args.copy_figure_paths).split(",")
        if item.strip()
    ]

    summary = build_summary(DEFAULT_SPECS, project_root)
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plot_summary(summary, output_figure)

    for extra_path in copy_paths:
        extra_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_figure, extra_path)

    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {output_figure}")
    for extra_path in copy_paths:
        print(f"[OK] copied {extra_path}")


if __name__ == "__main__":
    main()
