#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

METRICS = [
    ("server_round_ms", "Server Round ms"),
    ("server_aggregation_ms", "Aggregation ms"),
    ("round_wall_clock_ms", "Round Wall ms"),
    ("process_peak_rss_mb", "Peak RSS MB"),
]
COLORS = {
    "static": "#4e79a7",
    "condfloor": "#f28e2b",
    "keepall": "#59a14f",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a client-scaling runtime report from seed-sweep summaries")
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
            "bytes_per_round_est_mean": float(stat_value(stats_obj, "bytes_per_round_est", "mean")),
            "bytes_per_round_est_std": float(stat_value(stats_obj, "bytes_per_round_est", "std")),
        }
        for metric, _title in METRICS:
            out[f"{metric}_mean"] = float(stat_value(stats_obj, metric, "mean"))
            out[f"{metric}_std"] = float(stat_value(stats_obj, metric, "std"))
        rows.append(out)
    rows.sort(key=lambda item: (str(item["label"]), int(item["client_count"])))
    return rows


def maybe_build_figure(rows: list[dict[str, Any]], output_figure: Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["label"])].append(row)
    for label in grouped:
        grouped[label].sort(key=lambda item: int(item["client_count"]))

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0), constrained_layout=True)
    axes_flat = axes.flatten()
    for ax, (metric, title) in zip(axes_flat, METRICS):
        for label, series in grouped.items():
            x = np.asarray([int(item["client_count"]) for item in series], dtype=np.float64)
            y = np.asarray([float(item[f"{metric}_mean"]) for item in series], dtype=np.float64)
            err = np.asarray([float(item[f"{metric}_std"]) for item in series], dtype=np.float64)
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
        ax.grid(alpha=0.25)
    axes_flat[0].set_ylabel("milliseconds")
    axes_flat[1].set_ylabel("milliseconds")
    axes_flat[2].set_ylabel("milliseconds")
    axes_flat[3].set_ylabel("MB")
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
        "metrics": [metric for metric, _title in METRICS],
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
