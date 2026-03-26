#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build bootstrap graphs using the legacy graph builder")
    p.add_argument("--scenario-index", required=True)
    p.add_argument("--legacy-project-root", required=True)
    p.add_argument("--python-bin", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--delta-t", default="1.0")
    p.add_argument("--target-ip", default="10.0.0.100")
    p.add_argument("--skip-existing", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    scenario_index = json.loads(Path(args.scenario_index).resolve().read_text(encoding="utf-8"))
    legacy_root = Path(args.legacy_project_root).resolve()
    output_root = Path(args.output_root).resolve()
    graphs_dir = output_root / "graphs"
    logs_dir = output_root / "logs"
    graphs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for row in scenario_index.get("rows", []):
        scenario_name = str(row["scenario_name"])
        output_file = graphs_dir / f"{scenario_name}.pt"
        log_file = logs_dir / f"build_{scenario_name}.log"

        if args.skip_existing and output_file.exists():
            rows.append(
                {
                    "scenario_name": scenario_name,
                    "graph_file": str(output_file),
                    "log_file": str(log_file),
                    "status": "skipped_existing",
                }
            )
            continue

        cmd = [
            str(args.python_bin),
            "build_graph_v2.py",
            "--pcap-file",
            str(row["pcap_file"]),
            "--manifest-file",
            str(row["manifest_file"]),
            "--output-file",
            str(output_file),
            "--target-ip",
            str(args.target_ip),
            "--delta-t",
            str(args.delta_t),
            "--seed",
            str(args.seed),
        ]
        with log_file.open("w", encoding="utf-8") as f:
            result = subprocess.run(cmd, cwd=str(legacy_root), stdout=f, stderr=subprocess.STDOUT)

        status = "ok" if result.returncode == 0 else f"failed:{result.returncode}"
        rows.append(
            {
                "scenario_name": scenario_name,
                "graph_file": str(output_file),
                "log_file": str(log_file),
                "status": status,
            }
        )
        print(f"[{status}] {scenario_name}")

    out = {
        "legacy_project_root": str(legacy_root),
        "python_bin": str(args.python_bin),
        "output_root": str(output_root),
        "rows": rows,
    }
    summary_file = output_root / "build_summary.json"
    summary_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_file}")


if __name__ == "__main__":
    main()
