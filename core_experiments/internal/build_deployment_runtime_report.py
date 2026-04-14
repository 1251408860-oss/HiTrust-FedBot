#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

RAW_METRICS = [
    ("local_training_ms", "Local Training ms"),
    ("attack_simulation_ms", "Attack Simulation ms"),
    ("client_eval_ms", "Client Evaluation ms"),
    ("server_aggregation_ms", "Aggregation ms"),
    ("global_eval_ms", "Global Evaluation ms"),
    ("server_round_ms", "Server Round ms"),
    ("round_wall_clock_ms", "Round Wall ms"),
    ("process_peak_rss_mb", "Peak RSS MB"),
    ("bytes_per_round_est", "Bytes / Round"),
]
FIGURE_METRICS = [
    ("round_wall_clock_ms", "Round Wall ms", 1.0, "ms"),
    ("local_training_ms", "Local Training ms", 1.0, "ms"),
    ("client_eval_ms", "Client Evaluation ms", 1.0, "ms"),
    ("server_round_ms", "Server Round ms", 1.0, "ms"),
    ("bytes_per_round_est", "Bytes / Round (KiB)", 1.0 / 1024.0, "KiB"),
    ("process_peak_rss_mb", "Peak RSS MB", 1.0, "MB"),
]
COLORS = {
    "static": "#4e79a7",
    "condfloor": "#f28e2b",
    "keepall": "#59a14f",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a deployment-oriented single-host runtime package from runtime scaling seed summaries"
    )
    p.add_argument("--series-index", required=True)
    p.add_argument("--stats-dir", required=True)
    p.add_argument("--output-table", required=True)
    p.add_argument("--output-figure", default="")
    p.add_argument("--title-prefix", default="")
    return p.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stat_value(obj: dict[str, Any], metric: str, key: str) -> float:
    return float(dict(obj.get("stats", {}).get(metric, {}) or {}).get(key, 0.0))


def safe_ratio(numer: float, denom: float) -> float:
    if abs(float(denom)) <= 1e-12:
        return 0.0
    return float(numer) / float(denom)


def build_rows(index_rows: list[dict[str, Any]], stats_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in index_rows:
        run_name = str(row["run_name"])
        stats_file = stats_dir / f"{run_name}_seed_stats.json"
        stats_obj = load_json(stats_file)
        out: dict[str, Any] = {
            "label": str(row["label"]),
            "client_count": int(row["client_count"]),
            "run_name": run_name,
            "source_file": str(stats_file),
            "n": int(stat_value(stats_obj, "test_f1", "n")),
            "active_clients_mean": float(stat_value(stats_obj, "active_clients", "mean")),
            "active_clients_std": float(stat_value(stats_obj, "active_clients", "std")),
        }
        for metric, _title in RAW_METRICS:
            out[f"{metric}_mean"] = float(stat_value(stats_obj, metric, "mean"))
            out[f"{metric}_std"] = float(stat_value(stats_obj, metric, "std"))

        wall = float(out["round_wall_clock_ms_mean"])
        server = float(out["server_round_ms_mean"])
        local_train = float(out["local_training_ms_mean"])
        client_eval = float(out["client_eval_ms_mean"])
        global_eval = float(out["global_eval_ms_mean"])
        aggregation = float(out["server_aggregation_ms_mean"])
        active_clients = float(out["active_clients_mean"])
        bytes_per_round = float(out["bytes_per_round_est_mean"])

        out["server_share_of_wall_clock_mean"] = safe_ratio(server, wall)
        out["local_training_share_of_wall_clock_mean"] = safe_ratio(local_train, wall)
        out["client_eval_share_of_wall_clock_mean"] = safe_ratio(client_eval, wall)
        out["global_eval_share_of_wall_clock_mean"] = safe_ratio(global_eval, wall)
        out["aggregation_share_of_server_round_mean"] = safe_ratio(aggregation, server)
        out["bytes_per_client_per_round_est_mean"] = safe_ratio(bytes_per_round, active_clients)
        out["wall_clock_per_client_ms_mean"] = safe_ratio(wall, active_clients)
        out["clients_per_second_mean"] = safe_ratio(active_clients * 1000.0, wall)
        rows.append(out)

    rows.sort(key=lambda item: (str(item["label"]), int(item["client_count"])))
    return rows


def maybe_build_figure(rows: list[dict[str, Any]], output_figure: Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["label"])].append(row)
    for label in grouped:
        grouped[label].sort(key=lambda item: int(item["client_count"]))

    fig, axes = plt.subplots(2, 3, figsize=(13.2, 8.2), constrained_layout=True)
    axes_flat = axes.flatten()
    for ax, (metric, title, scale, ylabel) in zip(axes_flat, FIGURE_METRICS):
        for label, series in grouped.items():
            x = np.asarray([int(item["client_count"]) for item in series], dtype=np.float64)
            y = np.asarray([float(item[f"{metric}_mean"]) * float(scale) for item in series], dtype=np.float64)
            err = np.asarray([float(item[f"{metric}_std"]) * float(scale) for item in series], dtype=np.float64)
            ax.errorbar(
                x,
                y,
                yerr=err,
                marker="o",
                linewidth=2.0,
                capsize=4.0,
                label=label,
                color=COLORS.get(label, None),
            )
        ax.set_title(title)
        ax.set_xlabel("Configured Clients")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
    handles, labels = axes_flat[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=max(1, len(labels)))
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    index = load_json(Path(args.series_index).resolve())
    rows = build_rows(list(index.get("rows", [])), Path(args.stats_dir).resolve())
    report = {
        "title_prefix": str(args.title_prefix),
        "scope": "single_host_deployment_runtime_package",
        "metrics": [metric for metric, _title in RAW_METRICS],
        "derived_metrics": [
            "server_share_of_wall_clock_mean",
            "local_training_share_of_wall_clock_mean",
            "client_eval_share_of_wall_clock_mean",
            "global_eval_share_of_wall_clock_mean",
            "aggregation_share_of_server_round_mean",
            "bytes_per_client_per_round_est_mean",
            "wall_clock_per_client_ms_mean",
            "clients_per_second_mean",
        ],
        "rows": rows,
    }
    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if str(args.output_figure).strip():
        maybe_build_figure(rows, Path(args.output_figure).resolve())
    print(f"[OK] wrote {output_table}")


if __name__ == "__main__":
    main()
