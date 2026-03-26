#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Sweep seeds for a real graph pilot config")
    p.add_argument("--base-config", required=True)
    p.add_argument("--runner", required=True)
    p.add_argument("--python-bin", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--seeds", required=True)
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    base_cfg = json.loads(Path(args.base_config).resolve().read_text(encoding="utf-8"))
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    seeds = [int(x.strip()) for x in str(args.seeds).split(",") if x.strip()]
    for seed in seeds:
        cfg = dict(base_cfg)
        cfg["seed"] = int(seed)
        cfg["run_name"] = f"{base_cfg['run_name']}_seed{seed}"
        config_file = output_dir / f"{cfg['run_name']}.json"
        summary_file = project_root / "paper_hitrust" / "runs" / cfg["run_name"] / "summary.json"
        if args.skip_existing and summary_file.exists():
            rows.append({"run_name": cfg["run_name"], "seed": seed, "status": "skipped_existing"})
            continue
        config_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        cmd = [
            str(args.python_bin),
            str(Path(args.runner).resolve()),
            "--config",
            str(config_file),
            "--project-root",
            str(project_root),
        ]
        result = subprocess.run(cmd, cwd=str(project_root))
        status = "ok" if result.returncode == 0 else f"failed:{result.returncode}"
        rows.append({"run_name": cfg["run_name"], "seed": seed, "status": status})
        print(f"[{status}] {cfg['run_name']}")

    summary_out = output_dir / "seed_sweep_summary.json"
    summary_out.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_out}")


if __name__ == "__main__":
    main()
