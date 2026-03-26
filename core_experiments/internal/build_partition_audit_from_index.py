#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from client_partition_hitrust import build_partition_audit_from_scenario_index


def main() -> None:
    p = argparse.ArgumentParser(description="Build a partition audit from a scenario index")
    p.add_argument("--scenario-index", required=True)
    p.add_argument("--output-file", required=True)
    p.add_argument("--partition-mode", default="topology_noniid")
    p.add_argument("--num-clients", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    scenario_index = json.loads(Path(args.scenario_index).read_text(encoding="utf-8"))
    out = build_partition_audit_from_scenario_index(
        scenario_index=scenario_index,
        num_clients=args.num_clients,
        partition_mode=args.partition_mode,
        seed=args.seed,
    )
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
