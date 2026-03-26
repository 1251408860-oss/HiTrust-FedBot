#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def scenario_from_run_name(run_name: str, aggregation: str, condition: str) -> str:
    prefix = "real_graph_pilot_"
    suffix = f"_{aggregation}_{condition}"
    if not run_name.startswith(prefix) or not run_name.endswith(suffix):
        raise ValueError(f"run name does not match expected pattern: {run_name}")
    return run_name[len(prefix) : -len(suffix)]


def main() -> None:
    p = argparse.ArgumentParser(description="Build a cross-scenario robustness matrix from run summaries")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--aggregation", default="hierarchical")
    p.add_argument("--conditions", required=True, help="CSV of condition tags, e.g. clean,sign_flip_frac0p4")
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root).resolve()
    conditions = [x.strip() for x in str(args.conditions).split(",") if x.strip()]
    rows = []
    for condition in conditions:
        for summary_file in sorted(runs_root.glob(f"real_graph_pilot_scenario_*_{args.aggregation}_{condition}/summary.json")):
            obj = json.loads(summary_file.read_text(encoding="utf-8"))
            final = obj["final_metrics"]
            run_name = summary_file.parent.name
            rows.append(
                {
                    "condition": condition,
                    "scenario_name": scenario_from_run_name(run_name, args.aggregation, condition),
                    "run_name": run_name,
                    "test_f1": final["test_f1"],
                    "test_recall": final["test_recall"],
                    "test_fpr": final["test_fpr"],
                    "kept_poisoned_clients": final["kept_poisoned_clients"],
                }
            )

    out = {
        "aggregation": args.aggregation,
        "conditions": conditions,
        "rows": rows,
    }
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
