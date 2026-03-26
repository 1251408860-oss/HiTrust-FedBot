#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Sweep real graph pilot over a graph index")
    p.add_argument("--graph-index", required=True)
    p.add_argument("--runner", required=True)
    p.add_argument("--python-bin", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--aggregation", default="hierarchical")
    p.add_argument("--partition-mode", default="topology_noniid")
    p.add_argument("--num-clients", type=int, default=10)
    p.add_argument("--num-groups", type=int, default=3)
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--local-epochs", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--hidden-dim", type=int, default=32)
    p.add_argument("--adapter-dim", type=int, default=8)
    p.add_argument("--backbone", default="feature_mlp")
    p.add_argument("--tuning-mode", default="adapter_ft")
    p.add_argument("--global-warmup-epochs", type=int, default=8)
    p.add_argument("--poison-frac", type=float, default=0.2)
    p.add_argument("--poison-type", default="update_noise")
    p.add_argument("--poison-scale", type=float, default=0.2)
    p.add_argument("--trust-threshold", type=float, default=0.35)
    p.add_argument("--min-keep-per-group", type=int, default=0)
    p.add_argument("--run-tag", default="")
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_index = json.loads(Path(args.graph_index).resolve().read_text(encoding="utf-8"))
    rows = []

    for row in graph_index.get("rows", []):
        scenario_name = str(row["scenario_name"])
        run_name = f"real_graph_pilot_{scenario_name}_{args.aggregation}"
        if str(args.run_tag).strip():
            run_name = f"{run_name}_{str(args.run_tag).strip()}"
        config_path = output_dir / f"{run_name}.json"
        summary_file = project_root / "paper_hitrust" / "runs" / run_name / "summary.json"
        if args.skip_existing and summary_file.exists():
            rows.append({"scenario_name": scenario_name, "run_name": run_name, "status": "skipped_existing"})
            continue

        cfg = {
            "run_name": run_name,
            "graph_file": str(row["graph_file"]),
            "seed": int(args.seed),
            "num_clients": int(args.num_clients),
            "partition_mode": str(args.partition_mode),
            "aggregation": str(args.aggregation),
            "num_groups": int(args.num_groups),
            "hidden_dim": int(args.hidden_dim),
            "adapter_dim": int(args.adapter_dim),
            "backbone": str(args.backbone),
            "tuning_mode": str(args.tuning_mode),
            "global_warmup_epochs": int(args.global_warmup_epochs),
            "rounds": int(args.rounds),
            "local_epochs": int(args.local_epochs),
            "lr": 0.01,
            "poison_frac": float(args.poison_frac),
            "poison_type": str(args.poison_type),
            "poison_scale": float(args.poison_scale),
            "trust_threshold": float(args.trust_threshold),
            "min_keep_per_group": int(args.min_keep_per_group),
        }
        config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        cmd = [
            str(args.python_bin),
            str(Path(args.runner).resolve()),
            "--config",
            str(config_path),
            "--project-root",
            str(project_root),
        ]
        result = subprocess.run(cmd, cwd=str(project_root))
        status = "ok" if result.returncode == 0 else f"failed:{result.returncode}"
        rows.append({"scenario_name": scenario_name, "run_name": run_name, "status": status})
        print(f"[{status}] {run_name}")

    summary_file = output_dir / "sweep_summary.json"
    summary_file.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_file}")


if __name__ == "__main__":
    main()
