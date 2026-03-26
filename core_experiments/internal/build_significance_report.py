#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from scipy import stats


def mean_std(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean": 0.0, "std": 0.0}
    if len(values) == 1:
        return {"n": 1, "mean": values[0], "std": 0.0}
    return {"n": len(values), "mean": statistics.mean(values), "std": statistics.stdev(values)}


def parse_group_specs(text: str) -> list[tuple[str, str]]:
    out = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, prefix = item.split("=", 1)
        out.append((label.strip(), prefix.strip()))
    return out


def load_metric_values(runs_root: Path, prefix: str, metric: str) -> list[float]:
    values = []
    for summary_file in sorted(runs_root.glob(f"{prefix}_seed*/summary.json")):
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        value = obj["final_metrics"][metric]
        values.append(float(value))
    return values


def main() -> None:
    p = argparse.ArgumentParser(description="Build a simple statistical-significance report over seed sweeps")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--group-specs", required=True, help="CSV of label=run_prefix")
    p.add_argument("--reference", required=True)
    p.add_argument("--metric", default="test_f1")
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root).resolve()
    groups = parse_group_specs(args.group_specs)
    values_by_label = {label: load_metric_values(runs_root, prefix, args.metric) for label, prefix in groups}
    if args.reference not in values_by_label:
        raise KeyError(f"reference label not found: {args.reference}")
    ref = values_by_label[args.reference]

    rows = []
    for label, _prefix in groups:
        vals = values_by_label[label]
        row = {"label": label, args.metric: mean_std(vals)}
        if label == args.reference:
            row["p_value_vs_reference"] = None
            row["t_stat_vs_reference"] = None
        elif len(ref) >= 2 and len(vals) >= 2:
            t_stat, p_value = stats.ttest_ind(ref, vals, equal_var=False)
            row["p_value_vs_reference"] = float(p_value)
            row["t_stat_vs_reference"] = float(t_stat)
        else:
            row["p_value_vs_reference"] = None
            row["t_stat_vs_reference"] = None
        rows.append(row)

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(
            {
                "metric": args.metric,
                "reference": args.reference,
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
