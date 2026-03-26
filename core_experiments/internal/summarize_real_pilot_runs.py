#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize real graph pilot runs")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root)
    rows = []
    for summary_file in sorted(runs_root.glob("real_graph_pilot_*/summary.json")):
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        final = obj["final_metrics"]
        rows.append(
            {
                "run_name": summary_file.parent.name,
                "aggregation": obj["config"]["aggregation"],
                "partition_mode": obj["config"]["partition_mode"],
                "graph_file": obj["graph_file"],
                "test_f1": final["test_f1"],
                "test_recall": final["test_recall"],
                "test_fpr": final["test_fpr"],
                "kept_clients": final["kept_clients"],
                "kept_poisoned_clients": final["kept_poisoned_clients"],
            }
        )

    out = {"rows": rows}
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
