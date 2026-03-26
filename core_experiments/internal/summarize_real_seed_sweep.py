#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


def mean_std(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"n": 0, "mean": 0.0, "std": 0.0}
    if len(vals) == 1:
        return {"n": 1, "mean": vals[0], "std": 0.0}
    return {"n": len(vals), "mean": statistics.mean(vals), "std": statistics.stdev(vals)}


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize a real graph seed sweep")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--run-prefix", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root)
    rows = []
    f1 = []
    recall = []
    fpr = []
    kept_clients = []
    kept_poisoned_clients = []
    pattern = re.compile(rf"^{re.escape(str(args.run_prefix))}_seed\d+$")
    for summary_file in sorted(runs_root.glob(f"{args.run_prefix}_seed*/summary.json")):
        if not pattern.fullmatch(summary_file.parent.name):
            continue
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        final = obj["final_metrics"]
        rows.append(
            {
                "run_name": summary_file.parent.name,
                "test_f1": final["test_f1"],
                "test_recall": final["test_recall"],
                "test_fpr": final["test_fpr"],
                "kept_clients": final.get("kept_clients", 0),
                "kept_poisoned_clients": final.get("kept_poisoned_clients", 0),
            }
        )
        f1.append(float(final["test_f1"]))
        recall.append(float(final["test_recall"]))
        fpr.append(float(final["test_fpr"]))
        kept_clients.append(float(final.get("kept_clients", 0)))
        kept_poisoned_clients.append(float(final.get("kept_poisoned_clients", 0)))

    out = {
        "rows": rows,
        "stats": {
            "test_f1": mean_std(f1),
            "test_recall": mean_std(recall),
            "test_fpr": mean_std(fpr),
            "kept_clients": mean_std(kept_clients),
            "kept_poisoned_clients": mean_std(kept_poisoned_clients),
        },
    }
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
