#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="Build a scenario index from existing manifests")
    p.add_argument("--source-root", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    source_root = Path(args.source_root)
    rows = []
    for manifest_file in sorted(source_root.glob("*/arena_manifest_v2.json")):
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        top = data.get("topology", {})
        core = top.get("core_bottleneck", {})
        run = data.get("run_config", {})
        scenario_dir = manifest_file.parent
        rows.append(
            {
                "scenario_name": scenario_dir.name,
                "manifest_file": str(manifest_file),
                "pcap_file": str(scenario_dir / "full_arena_v2.pcap"),
                "pcap_exists": bool((scenario_dir / "full_arena_v2.pcap").exists()),
                "topology_type": str(top.get("type", "")),
                "users": int(top.get("users", 0) or 0),
                "bots": int(top.get("bots", 0) or 0),
                "core_bw_mbps": float(core.get("bw_mbps", 0.0) or 0.0),
                "delay": str(core.get("delay", "")),
                "max_queue_size": int(core.get("max_queue_size", 0) or 0),
                "load_profile": str(run.get("load_profile", "")),
                "bot_type_mode": str(run.get("bot_type_mode", "")),
                "duration_sec": int(run.get("duration_sec", 0) or 0),
            }
        )

    out = {
        "source_root": str(source_root),
        "num_scenarios": len(rows),
        "rows": rows,
    }
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file} with {len(rows)} scenarios")


if __name__ == "__main__":
    main()
