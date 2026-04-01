#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).resolve().read_text(encoding="utf-8"))


def mean_std(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean": 0.0, "std": 0.0}
    if len(values) == 1:
        return {"n": 1, "mean": float(values[0]), "std": 0.0}
    return {
        "n": len(values),
        "mean": float(statistics.mean(values)),
        "std": float(statistics.stdev(values)),
    }


def build_rows(obj: dict) -> list[dict]:
    grouped: dict[tuple[float, float], list[dict]] = {}
    for row in obj.get("rows", []):
        threshold = float(row.get("override_trust_threshold", row.get("trust_threshold", 0.0)))
        floor = float(
            row.get(
                "override_group_floor_min_trust_mass",
                row.get("group_floor_min_trust_mass", row.get("override_group_floor_min_trust_mass", 0.0)),
            )
        )
        grouped.setdefault((threshold, floor), []).append(row)

    rows: list[dict] = []
    for (threshold, floor), items in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1])):
        f1 = [float(item.get("test_f1", 0.0)) for item in items]
        fpr = [float(item.get("test_fpr", 0.0)) for item in items]
        kept_poisoned = [float(item.get("kept_poisoned_clients", 0.0)) for item in items]
        kept_clients = [float(item.get("kept_clients", 0.0)) for item in items]
        rows.append(
            {
                "trust_threshold": float(threshold),
                "group_floor_min_trust_mass": float(floor),
                "test_f1": mean_std(f1),
                "test_fpr": mean_std(fpr),
                "kept_poisoned_clients": mean_std(kept_poisoned),
                "kept_clients": mean_std(kept_clients),
                "run_names": [str(item.get("run_name", "")) for item in items],
            }
        )
    return rows


def select_best_rows(rows: list[dict]) -> dict:
    best_f1 = max(
        rows,
        key=lambda row: (
            float(row["test_f1"]["mean"]),
            -float(row["kept_poisoned_clients"]["mean"]),
            -float(row["test_fpr"]["mean"]),
        ),
    )
    best_security = min(
        rows,
        key=lambda row: (
            float(row["kept_poisoned_clients"]["mean"]),
            float(row["test_fpr"]["mean"]),
            -float(row["test_f1"]["mean"]),
        ),
    )
    return {
        "best_by_f1": dict(best_f1),
        "best_by_security": dict(best_security),
    }


def build_matrix(rows: list[dict], field: str, thresholds: list[float], floors: list[float]) -> np.ndarray:
    matrix = np.zeros((len(thresholds), len(floors)), dtype=np.float64)
    lookup = {
        (float(row["trust_threshold"]), float(row["group_floor_min_trust_mass"])): float(row[field]["mean"])
        for row in rows
    }
    for i, threshold in enumerate(thresholds):
        for j, floor in enumerate(floors):
            matrix[i, j] = lookup[(float(threshold), float(floor))]
    return matrix


def annotate_heatmap(ax, matrix: np.ndarray, fmt: str) -> None:
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(j, i, format(float(value), fmt), ha="center", va="center", color="black", fontsize=9)


def plot_rows(rows: list[dict], output_file: Path, title_prefix: str) -> None:
    thresholds = sorted({float(row["trust_threshold"]) for row in rows})
    floors = sorted({float(row["group_floor_min_trust_mass"]) for row in rows})
    specs = [
        ("test_f1", "Mean Test F1", "0.3f"),
        ("test_fpr", "Mean Test FPR", "0.3f"),
        ("kept_poisoned_clients", "Mean Retained Poisoned", "0.2f"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.6))
    for ax, (field, title, fmt) in zip(axes, specs):
        matrix = build_matrix(rows, field, thresholds, floors)
        image = ax.imshow(matrix, aspect="auto", cmap="YlGnBu")
        ax.set_xticks(np.arange(len(floors)), [f"{floor:.2f}" for floor in floors])
        ax.set_yticks(np.arange(len(thresholds)), [f"{threshold:.2f}" for threshold in thresholds])
        ax.set_xlabel("group_floor_min_trust_mass")
        ax.set_ylabel("trust_threshold")
        ax.set_title(f"{title_prefix} {title}")
        annotate_heatmap(ax, matrix, fmt)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a condfloor sensitivity report from config-grid summary")
    parser.add_argument("--grid-summary-file", required=True)
    parser.add_argument("--title-prefix", default="Condfloor Sensitivity")
    parser.add_argument("--output-table", required=True)
    parser.add_argument("--output-figure", required=True)
    args = parser.parse_args()

    rows = build_rows(load_json(args.grid_summary_file))
    summary = {
        "title_prefix": str(args.title_prefix),
        "rows": rows,
    }
    summary.update(select_best_rows(rows))

    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plot_rows(rows, Path(args.output_figure).resolve(), title_prefix=str(args.title_prefix))
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
