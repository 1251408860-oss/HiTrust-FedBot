#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Run a config-grid sweep for real federated pilots")
    p.add_argument("--base-config", required=True)
    p.add_argument("--grid-file", required=True)
    p.add_argument("--runner", required=True)
    p.add_argument("--python-bin", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--skip-existing", action="store_true")
    args = p.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    base_cfg = json.loads(Path(args.base_config).resolve().read_text(encoding="utf-8"))
    grid = json.loads(Path(args.grid_file).resolve().read_text(encoding="utf-8"))
    rows = []

    for row in grid.get("rows", []):
        row_id = str(row["id"])
        overrides = dict(row.get("overrides", {}))
        cfg = dict(base_cfg)
        cfg.update(overrides)
        cfg["run_name"] = f"{base_cfg['run_name']}_{row_id}"
        config_file = output_dir / f"{cfg['run_name']}.json"
        summary_file = project_root / "paper_hitrust" / "runs" / cfg["run_name"] / "summary.json"
        if args.skip_existing and summary_file.exists():
            status = "skipped_existing"
        else:
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
                "id": row_id,
                "run_name": cfg["run_name"],
                "status": status,
                "overrides": overrides,
            }
        )
        print(f"[{status}] {cfg['run_name']}")

    manifest = {"base_config": str(Path(args.base_config).resolve()), "rows": rows}
    manifest_file = output_dir / "grid_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[OK] wrote {manifest_file}")


if __name__ == "__main__":
    main()
