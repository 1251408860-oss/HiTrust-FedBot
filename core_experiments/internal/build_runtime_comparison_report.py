#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

TIME_METRICS = [
    ("server_round_ms", "Server Round ms"),
    ("server_aggregation_ms", "Aggregation ms"),
    ("client_eval_ms", "Client Eval ms"),
    ("global_eval_ms", "Global Eval ms"),
    ("local_training_ms", "Local Emulation ms"),
    ("round_wall_clock_ms", "Round Wall ms"),
]
MEMORY_METRICS = [
    ("process_rss_mb", "Process RSS MB"),
    ("process_peak_rss_mb", "Peak RSS MB"),
]


def parse_specs(text: str) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, path = item.split("=", 1)
        out.append((label.strip(), Path(path).resolve()))
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_stats(obj: dict[str, Any], metric: str) -> dict[str, float]:
    return dict(obj.get("stats", {}).get(metric, {}) or {})


def build_rows(specs: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, path in specs:
        obj = load_json(path)
        contract = dict(obj.get("experiment_contract", {}) or {})
        method = dict(contract.get("method", {}) or {})
        attack = dict(contract.get("attack", {}) or {})
        benchmark = dict(contract.get("benchmark", {}) or {})
        row: dict[str, Any] = {
            "label": label,
            "source_file": str(path),
            "n": int(metric_stats(obj, "test_f1").get("n", 0)),
            "method_key": str(method.get("method_key", "")),
            "method_family": str(method.get("method_family", "")),
            "attack_key": str(attack.get("attack_key", "")),
            "benchmark_key": str(benchmark.get("benchmark_key", "")),
            "bytes_per_round_est_mean": float(metric_stats(obj, "bytes_per_round_est").get("mean", 0.0)),
            "bytes_per_round_est_std": float(metric_stats(obj, "bytes_per_round_est").get("std", 0.0)),
            "active_clients_mean": float(metric_stats(obj, "active_clients").get("mean", 0.0)),
            "active_clients_std": float(metric_stats(obj, "active_clients").get("std", 0.0)),
        }
        for metric, _title in TIME_METRICS + MEMORY_METRICS:
            stats_obj = metric_stats(obj, metric)
            row[f"{metric}_mean"] = float(stats_obj.get("mean", 0.0))
            row[f"{metric}_std"] = float(stats_obj.get("std", 0.0))
        rows.append(row)
    return rows


def maybe_build_figure(rows: list[dict[str, Any]], output_figure: Path) -> None:
    labels = [str(row["label"]) for row in rows]
    x = np.arange(len(rows), dtype=np.float64)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    figure_metrics = [
        ("server_round_ms", "Mean Server Round ms"),
        ("server_aggregation_ms", "Mean Aggregation ms"),
    ]
    for ax, (metric, title) in zip(axes, figure_metrics):
        means = np.asarray([float(row[f"{metric}_mean"]) for row in rows], dtype=np.float64)
        stds = np.asarray([float(row[f"{metric}_std"]) for row in rows], dtype=np.float64)
        ax.bar(x, means, yerr=stds, capsize=4.0, color=["#4e79a7", "#f28e2b", "#59a14f"][: len(rows)])
        ax.set_title(title)
        ax.set_ylabel("milliseconds")
        ax.set_xticks(x, labels, rotation=20, ha="right")
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact runtime comparison report")
    parser.add_argument("--method-specs", required=True)
    parser.add_argument("--title-prefix", default="")
    parser.add_argument("--output-table", required=True)
    parser.add_argument("--output-figure", default="")
    args = parser.parse_args()

    specs = parse_specs(args.method_specs)
    rows = build_rows(specs)
    report = {
        "title_prefix": str(args.title_prefix),
        "rows": rows,
        "timing_metrics": [metric for metric, _title in TIME_METRICS],
        "memory_metrics": [metric for metric, _title in MEMORY_METRICS],
    }
    output_table = Path(args.output_table)
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if str(args.output_figure).strip():
        maybe_build_figure(rows, Path(args.output_figure))
    print(f"[OK] wrote {output_table}")


if __name__ == "__main__":
    main()
