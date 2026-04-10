#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from graph_contract import GRAPH_CONTRACT_VERSION, apply_graph_contract


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply the local graph contract to rebuilt bootstrap graphs")
    p.add_argument("--graphs-root", required=True)
    p.add_argument("--manifest-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--dataset-name", default="HiTrust-Bootstrap")
    p.add_argument("--dataset-source", default="repo_bootstrap:data_hitrust/bootstrap_graphs")
    p.add_argument("--split-scheme", default="released_bootstrap_graph_masks")
    p.add_argument("--graph-source-kind", default="internal_released_bootstrap")
    p.add_argument("--builder-reference", default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    graphs_root = Path(args.graphs_root).resolve()
    manifest_root = Path(args.manifest_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for graph_file in sorted(graphs_root.glob("*.pt")):
        scenario_name = graph_file.stem
        manifest_file = manifest_root / scenario_name / "arena_manifest_v2.json"
        if not manifest_file.exists():
            raise FileNotFoundError(f"missing manifest for {scenario_name}: {manifest_file}")

        graph = torch.load(graph_file, weights_only=False, map_location="cpu")
        manifest_metadata = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
        apply_graph_contract(
            graph,
            project_root=args.project_root,
            dataset_name=str(args.dataset_name),
            dataset_variant=scenario_name,
            dataset_source=str(args.dataset_source),
            split_scheme=str(args.split_scheme),
            manifest_file=manifest_file,
            manifest_metadata=manifest_metadata,
            graph_source_kind=str(args.graph_source_kind),
            builder_reference=str(args.builder_reference),
        )
        output_file = output_root / graph_file.name
        torch.save(graph, output_file)
        rows.append(
            {
                "scenario_name": scenario_name,
                "input_graph_file": str(graph_file),
                "output_graph_file": str(output_file),
                "graph_contract_version": GRAPH_CONTRACT_VERSION,
            }
        )
        print(f"[OK] normalized {scenario_name}")

    summary = {
        "graphs_root": str(graphs_root),
        "manifest_root": str(manifest_root),
        "output_root": str(output_root),
        "num_graphs": int(len(rows)),
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
        "rows": rows,
    }
    summary_file = output_root / "normalize_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {summary_file}")


if __name__ == "__main__":
    main()
