#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize a config-grid sweep for real federated pilots")
    p.add_argument("--manifest-file", required=True)
    p.add_argument("--runs-root", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    manifest = json.loads(Path(args.manifest_file).resolve().read_text(encoding="utf-8"))
    runs_root = Path(args.runs_root).resolve()
    rows = []
    for row in manifest.get("rows", []):
        run_name = str(row["run_name"])
        summary_file = runs_root / run_name / "summary.json"
        if not summary_file.exists():
            rows.append({"id": row["id"], "run_name": run_name, "status": "missing_summary"})
            continue
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        cfg = obj.get("config", {})
        final = obj.get("final_metrics", {})
        comm = obj.get("comm_cost", {})
        tuning = obj.get("tuning_info", {})
        model_info = obj.get("model_info", {})
        out = {
            "id": row["id"],
            "run_name": run_name,
            "status": row.get("status", "unknown"),
            "backbone": model_info.get("backbone", cfg.get("backbone")),
            "aggregation": cfg.get("aggregation"),
            "graph_file": cfg.get("graph_file"),
            "num_groups": cfg.get("num_groups"),
            "trust_threshold": cfg.get("trust_threshold"),
            "tuning_mode": tuning.get("tuning_mode", cfg.get("tuning_mode")),
            "trainable_params": tuning.get("trainable_params"),
            "trainable_ratio_actual": tuning.get("trainable_ratio_actual"),
            "poison_type": cfg.get("poison_type"),
            "poison_frac": cfg.get("poison_frac"),
            "poison_scale": cfg.get("poison_scale"),
            "seed": cfg.get("seed"),
            "test_f1": final.get("test_f1"),
            "test_recall": final.get("test_recall"),
            "test_fpr": final.get("test_fpr"),
            "kept_clients": final.get("kept_clients"),
            "kept_poisoned_clients": final.get("kept_poisoned_clients"),
            "bytes_per_round_est": comm.get("bytes_per_round_est"),
            "total_bytes_est": comm.get("total_bytes_est"),
        }
        for key, value in row.get("overrides", {}).items():
            out[f"override_{key}"] = value
        rows.append(out)

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
