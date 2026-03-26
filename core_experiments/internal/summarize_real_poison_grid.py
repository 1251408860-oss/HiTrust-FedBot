#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize poison-grid real graph pilot runs")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--run-prefix", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    rows = []
    for summary_file in sorted(Path(args.runs_root).glob(f"{args.run_prefix}_*/summary.json")):
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        final = obj["final_metrics"]
        cfg = obj["config"]
        rows.append(
            {
                "run_name": summary_file.parent.name,
                "poison_type": cfg["poison_type"],
                "poison_frac": cfg["poison_frac"],
                "test_f1": final["test_f1"],
                "test_recall": final["test_recall"],
                "test_fpr": final["test_fpr"],
                "kept_poisoned_clients": final["kept_poisoned_clients"],
            }
        )

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
