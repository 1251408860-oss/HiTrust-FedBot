#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from graph_contract import graph_stats, validate_graph_contract

TENSOR_FIELDS = (
    "x",
    "x_norm",
    "y",
    "edge_index",
    "edge_index_undirected",
    "edge_type",
    "edge_type_undirected",
    "window_idx",
    "ip_idx",
    "train_mask",
    "val_mask",
    "test_mask",
    "temporal_train_mask",
    "temporal_test_mask",
    "feat_mean",
    "feat_std",
)
ATTRIBUTE_FIELDS = (
    "dataset_name",
    "dataset_variant",
    "dataset_source",
    "split_scheme",
    "graph_contract_version",
    "graph_source_kind",
    "manifest_file",
    "manifest_metadata",
    "source_ips",
    "target_ip",
    "delta_t",
    "n_windows",
    "feature_names",
    "feature_index",
    "label_source",
    "delay_metric",
    "delay_match_rate",
    "delay_request_count",
    "delay_matched_count",
    "manifest_issue_count",
    "manifest_issues",
    "manifest_core_bw_mbps",
    "capacity_bytes_per_sec",
)
PROVENANCE_FIELDS = ("builder_reference",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare released bootstrap graphs against raw-rebuilt graphs")
    p.add_argument("--released-root", required=True)
    p.add_argument("--rebuilt-root", required=True)
    p.add_argument("--output-file", required=True)
    return p.parse_args()


def stable_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): stable_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [stable_value(v) for v in value]
    if isinstance(value, float):
        return round(float(value), 8)
    return value


def tensor_hash(tensor: torch.Tensor) -> str:
    arr = tensor.detach().cpu().contiguous().numpy()
    return hashlib.sha256(arr.tobytes()).hexdigest()


def compare_tensors(name: str, released, rebuilt) -> dict[str, Any]:
    lhs = getattr(released, name)
    rhs = getattr(rebuilt, name)
    same_shape = list(lhs.shape) == list(rhs.shape)
    exact_match = False
    allclose_match = False
    max_abs_diff = 0.0
    if same_shape:
        exact_match = bool(torch.equal(lhs, rhs))
        if torch.is_floating_point(lhs) or torch.is_floating_point(rhs):
            lhs_f = lhs.detach().cpu().to(dtype=torch.float64)
            rhs_f = rhs.detach().cpu().to(dtype=torch.float64)
            allclose_match = bool(torch.allclose(lhs_f, rhs_f, atol=1e-8, rtol=1e-6))
            max_abs_diff = float(torch.max(torch.abs(lhs_f - rhs_f)).item()) if lhs.numel() else 0.0
        else:
            allclose_match = exact_match
    return {
        "field": name,
        "same_shape": bool(same_shape),
        "exact_match": bool(exact_match),
        "allclose_match": bool(allclose_match),
        "max_abs_diff": float(max_abs_diff),
        "released_hash": tensor_hash(lhs),
        "rebuilt_hash": tensor_hash(rhs),
    }


def compare_attributes(name: str, released, rebuilt) -> dict[str, Any]:
    lhs = stable_value(getattr(released, name, None))
    rhs = stable_value(getattr(rebuilt, name, None))
    return {
        "field": name,
        "match": bool(lhs == rhs),
        "released_value": lhs,
        "rebuilt_value": rhs,
    }


def validate_graph(name: str, graph) -> str:
    try:
        validate_graph_contract(graph)
    except Exception as exc:
        return f"invalid:{type(exc).__name__}:{exc}"
    return f"valid:{name}"


def main() -> None:
    args = parse_args()
    released_root = Path(args.released_root).resolve()
    rebuilt_root = Path(args.rebuilt_root).resolve()
    rows: list[dict[str, Any]] = []

    for released_file in sorted(released_root.glob("*.pt")):
        scenario_name = released_file.stem
        rebuilt_file = rebuilt_root / released_file.name
        if not rebuilt_file.exists():
            rows.append(
                {
                    "scenario_name": scenario_name,
                    "status": "missing_rebuilt_graph",
                    "released_file": str(released_file),
                    "rebuilt_file": str(rebuilt_file),
                }
            )
            continue

        released = torch.load(released_file, weights_only=False, map_location="cpu")
        rebuilt = torch.load(rebuilt_file, weights_only=False, map_location="cpu")
        tensor_rows = [compare_tensors(name, released, rebuilt) for name in TENSOR_FIELDS]
        attribute_rows = [compare_attributes(name, released, rebuilt) for name in ATTRIBUTE_FIELDS]
        provenance_rows = [compare_attributes(name, released, rebuilt) for name in PROVENANCE_FIELDS]
        exact_tensor_match = all(bool(row["exact_match"]) for row in tensor_rows)
        allclose_tensor_match = all(bool(row["allclose_match"]) for row in tensor_rows)
        attribute_match = all(bool(row["match"]) for row in attribute_rows)
        provenance_match = all(bool(row["match"]) for row in provenance_rows)

        rows.append(
            {
                "scenario_name": scenario_name,
                "status": "ok",
                "released_file": str(released_file),
                "rebuilt_file": str(rebuilt_file),
                "released_contract_status": validate_graph("released", released),
                "rebuilt_contract_status": validate_graph("rebuilt", rebuilt),
                "released_graph_stats": graph_stats(released),
                "rebuilt_graph_stats": graph_stats(rebuilt),
                "exact_tensor_match": bool(exact_tensor_match),
                "allclose_tensor_match": bool(allclose_tensor_match),
                "attribute_match": bool(attribute_match),
                "provenance_match": bool(provenance_match),
                "overall_core_match": bool(exact_tensor_match and attribute_match),
                "tensor_rows": tensor_rows,
                "attribute_rows": attribute_rows,
                "provenance_rows": provenance_rows,
            }
        )
        print(
            f"[OK] {scenario_name}: core_match={exact_tensor_match and attribute_match} "
            f"provenance_match={provenance_match}"
        )

    ok_rows = [row for row in rows if row.get("status") == "ok"]
    report = {
        "released_root": str(released_root),
        "rebuilt_root": str(rebuilt_root),
        "num_scenarios": int(len(rows)),
        "num_ok": int(len(ok_rows)),
        "num_core_matches": int(sum(1 for row in ok_rows if row.get("overall_core_match"))),
        "num_exact_tensor_matches": int(sum(1 for row in ok_rows if row.get("exact_tensor_match"))),
        "num_provenance_matches": int(sum(1 for row in ok_rows if row.get("provenance_match"))),
        "rows": rows,
    }
    output_file = Path(args.output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
