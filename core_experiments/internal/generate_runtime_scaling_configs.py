#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_base_specs(text: str) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, path = item.split("=", 1)
        rows.append((label.strip(), Path(path).resolve()))
    return rows


def parse_client_counts(text: str) -> list[int]:
    return [int(part.strip()) for part in str(text).split(",") if part.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate runtime scaling config variants from base runtime configs")
    p.add_argument("--base-configs", required=True)
    p.add_argument("--client-counts", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--output-index", required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for label, config_path in parse_base_specs(args.base_configs):
        base_cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
        for client_count in parse_client_counts(args.client_counts):
            cfg = dict(base_cfg)
            run_name = f"{str(base_cfg['run_name']).strip()}_clients{int(client_count)}"
            cfg["run_name"] = run_name
            cfg["num_clients"] = int(client_count)
            output_file = output_dir / f"{run_name}.json"
            output_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            rows.append(
                {
                    "label": label,
                    "client_count": int(client_count),
                    "run_name": run_name,
                    "config_file": str(output_file),
                }
            )
            print(f"[OK] generated {output_file.name}")

    index = {
        "output_dir": str(output_dir),
        "num_configs": int(len(rows)),
        "rows": rows,
    }
    output_index = Path(args.output_index).resolve()
    output_index.parent.mkdir(parents=True, exist_ok=True)
    output_index.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_index}")


if __name__ == "__main__":
    main()
