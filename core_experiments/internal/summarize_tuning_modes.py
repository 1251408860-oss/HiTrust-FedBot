#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize tuning mode comparisons")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--run-prefix", required=True)
    p.add_argument("--output-file", required=True)
    p.add_argument("--required-substrings", default="")
    p.add_argument("--exclude-substrings", default="")
    args = p.parse_args()

    required = [x.strip() for x in str(args.required_substrings).split(",") if x.strip()]
    excluded = [x.strip() for x in str(args.exclude_substrings).split(",") if x.strip()]
    rows = []
    for summary_file in sorted(Path(args.runs_root).glob(f"{args.run_prefix}_*/summary.json")):
        run_name = summary_file.parent.name
        if required and not any(tag in run_name for tag in required):
            continue
        if excluded and any(tag in run_name for tag in excluded):
            continue
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        if "tuning_info" not in obj:
            continue
        final = obj["final_metrics"]
        rows.append(
            {
                "run_name": run_name,
                "tuning_mode": obj["tuning_info"]["tuning_mode"],
                "trainable_params": obj["tuning_info"]["trainable_params"],
                "trainable_ratio_actual": obj["tuning_info"]["trainable_ratio_actual"],
                "bytes_per_round_est": obj["comm_cost"]["bytes_per_round_est"],
                "total_bytes_est": obj["comm_cost"]["total_bytes_est"],
                "test_f1": final["test_f1"],
                "test_recall": final["test_recall"],
                "test_fpr": final["test_fpr"],
            }
        )

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
