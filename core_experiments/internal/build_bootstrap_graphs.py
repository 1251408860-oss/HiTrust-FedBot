#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from graph_contract import GRAPH_CONTRACT_VERSION, repo_relative_path


def _is_absolute_path(text: str) -> bool:
    return text.startswith("/") or text.startswith("\\\\") or (
        len(text) >= 3 and text[1] == ":" and text[2] in ("/", "\\")
    )


def _stable_path(path: Path, *, project_root: Path, fallback: str) -> str:
    normalized = repo_relative_path(path, project_root)
    return fallback if _is_absolute_path(normalized) else normalized


def _stable_python_bin(raw_value: str) -> str:
    raw = str(raw_value).strip()
    if not raw:
        return "python3"
    if _is_absolute_path(raw):
        return Path(raw).name or "python3"
    return raw.replace("\\", "/")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build bootstrap graphs with an explicit builder root")
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
    project_root = Path.cwd().resolve()
    scenario_index = json.loads(Path(args.scenario_index).resolve().read_text(encoding="utf-8"))
    legacy_root = Path(args.legacy_project_root).resolve()
    output_root = Path(args.output_root).resolve()
    graphs_dir = output_root / "graphs"
    logs_dir = output_root / "logs"
    graphs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_root_display = _stable_path(
        output_root,
        project_root=project_root,
        fallback=Path(args.output_root).name or "bootstrap_graphs",
    )

    rows = []
    for row in scenario_index.get("rows", []):
        scenario_name = str(row["scenario_name"])
        output_file = graphs_dir / f"{scenario_name}.pt"
        log_file = logs_dir / f"build_{scenario_name}.log"

        if args.skip_existing and output_file.exists():
            rows.append(
                {
                    "scenario_name": scenario_name,
                    "graph_file": (Path(output_root_display) / "graphs" / output_file.name).as_posix(),
                    "log_file": (Path(output_root_display) / "logs" / log_file.name).as_posix(),
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
                "graph_file": (Path(output_root_display) / "graphs" / output_file.name).as_posix(),
                "log_file": (Path(output_root_display) / "logs" / log_file.name).as_posix(),
                "status": status,
            }
        )
        print(f"[{status}] {scenario_name}")

    out = {
        "builder_root": _stable_path(
            legacy_root,
            project_root=project_root,
            fallback="external_bootstrap_builder",
        ),
        "python_bin": _stable_python_bin(str(args.python_bin)),
        "output_root": output_root_display,
        "rows": rows,
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
    }
    summary_file = output_root / "build_summary.json"
    summary_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_file}")


if __name__ == "__main__":
    main()
