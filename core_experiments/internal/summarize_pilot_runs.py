#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize HiTrust pilot runs")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root)
    rows = []
    for summary_file in sorted(runs_root.glob("*/summary.json")):
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        rows.append(
            {
                "run_name": summary_file.parent.name,
                "aggregation": obj["config"]["aggregation"],
                "partition_mode": obj["config"]["partition_mode"],
                "f1": obj["metrics"]["f1"],
                "recall": obj["metrics"]["recall"],
                "fpr": obj["metrics"]["fpr"],
                "kept_clients": obj["trust_summary"]["kept_clients"],
                "kept_poisoned_clients": obj["trust_summary"]["kept_poisoned_clients"],
                "bytes_per_round_est": obj["comm_cost"]["bytes_per_round_est"],
            }
        )

    out = {"rows": rows}
    out_path = Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out_path}")


if __name__ == "__main__":
    main()
