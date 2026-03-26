#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def main() -> None:
    p = argparse.ArgumentParser(description="Build graph index from generated graph files")
    p.add_argument("--graphs-root", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    graphs_root = Path(args.graphs_root).resolve()
    rows = []
    for graph_file in sorted(graphs_root.glob("*.pt")):
        graph = torch.load(graph_file, weights_only=False, map_location="cpu")
        flow_mask = graph.window_idx >= 0 if hasattr(graph, "window_idx") else torch.ones(graph.num_nodes, dtype=torch.bool)
        rows.append(
            {
                "graph_file": str(graph_file),
                "scenario_name": graph_file.stem,
                "num_nodes": int(graph.num_nodes),
                "num_edges": int(graph.num_edges),
                "flow_nodes": int(flow_mask.sum().item()),
                "benign_flow_nodes": int(((graph.y == 0) & flow_mask).sum().item()),
                "attack_flow_nodes": int(((graph.y == 1) & flow_mask).sum().item()),
                "num_features": int(graph.x.shape[1]),
                "target_ip": str(getattr(graph, "target_ip", "")),
                "delta_t": float(getattr(graph, "delta_t", 0.0)),
            }
        )

    out = {
        "graphs_root": str(graphs_root),
        "num_graphs": len(rows),
        "rows": rows,
    }
    output_file = Path(args.output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
