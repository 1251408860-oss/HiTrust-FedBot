#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_csv_floats(text: str) -> list[float]:
    return [float(x.strip()) for x in str(text).split(",") if x.strip()]


def parse_csv_str(text: str) -> list[str]:
    return [str(x.strip()) for x in str(text).split(",") if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser(description="Sweep poison settings for a real graph pilot config")
    p.add_argument("--base-config", required=True)
    p.add_argument("--runner", required=True)
    p.add_argument("--python-bin", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--poison-fracs", required=True)
    p.add_argument("--poison-types", required=True)
    p.add_argument("--poison-scale", type=float, default=0.2)
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    base_cfg = json.loads(Path(args.base_config).resolve().read_text(encoding="utf-8"))
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for poison_type in parse_csv_str(args.poison_types):
        for poison_frac in parse_csv_floats(args.poison_fracs):
            cfg = dict(base_cfg)
            frac_token = str(poison_frac).replace(".", "p")
            cfg["poison_type"] = poison_type
            cfg["poison_frac"] = float(poison_frac)
            cfg["poison_scale"] = float(args.poison_scale)
            cfg["run_name"] = f"{base_cfg['run_name']}_{poison_type}_frac{frac_token}"
            config_file = output_dir / f"{cfg['run_name']}.json"
            summary_file = project_root / "paper_hitrust" / "runs" / cfg["run_name"] / "summary.json"
            if args.skip_existing and summary_file.exists():
                rows.append({"run_name": cfg["run_name"], "status": "skipped_existing"})
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
            rows.append(
                {
                    "run_name": cfg["run_name"],
                    "poison_type": poison_type,
                    "poison_frac": poison_frac,
                    "status": status,
                }
            )
            print(f"[{status}] {cfg['run_name']}")

    summary_out = output_dir / "poison_sweep_summary.json"
    summary_out.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_out}")


if __name__ == "__main__":
    main()
