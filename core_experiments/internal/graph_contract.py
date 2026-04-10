#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from hitrust_common import resolve_repo_local_path


GRAPH_CONTRACT_VERSION = "hitrust_graph_v1"

REQUIRED_TENSOR_FIELDS = (
    "x",
    "x_norm",
    "edge_index",
    "y",
    "window_idx",
    "ip_idx",
    "train_mask",
    "val_mask",
    "test_mask",
    "temporal_train_mask",
    "temporal_test_mask",
)
REQUIRED_META_FIELDS = (
    "dataset_name",
    "dataset_variant",
    "dataset_source",
    "split_scheme",
    "source_ips",
    "target_ip",
    "delta_t",
    "n_windows",
)


def repo_relative_path(path_value: str | Path, project_root: str | Path) -> str:
    raw = str(path_value).strip()
    if not raw:
        return ""
    if "://" in raw and not raw.startswith("file://"):
        return raw

    project = Path(project_root).resolve()
    path = Path(raw)
    candidate = path if path.is_absolute() else (project / path)
    if not path.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = resolve_repo_local_path(raw, project)

    try:
        return candidate.resolve().relative_to(project).as_posix()
    except Exception:
        return raw.replace("\\", "/")


def normalize_manifest_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    obj = dict(metadata or {})
    return {
        "topology": dict(obj.get("topology", {}) or {}),
        "run_config": dict(obj.get("run_config", {}) or {}),
        "roles": {str(k): str(v) for k, v in dict(obj.get("roles", {}) or {}).items()},
        "ip_labels": {str(k): int(v) for k, v in dict(obj.get("ip_labels", {}) or {}).items()},
    }


def apply_graph_contract(
    graph,
    *,
    project_root: str | Path,
    dataset_name: str,
    dataset_variant: str,
    dataset_source: str,
    split_scheme: str,
    manifest_file: str | Path = "",
    manifest_metadata: dict[str, Any] | None = None,
    graph_source_kind: str,
    builder_reference: str | Path = "",
):
    graph.dataset_name = str(dataset_name)
    graph.dataset_variant = str(dataset_variant)
    graph.dataset_source = str(dataset_source)
    graph.split_scheme = str(split_scheme)
    graph.manifest_file = repo_relative_path(manifest_file, project_root)
    graph.manifest_metadata = normalize_manifest_metadata(manifest_metadata)
    graph.graph_contract_version = GRAPH_CONTRACT_VERSION
    graph.graph_source_kind = str(graph_source_kind)
    graph.builder_reference = repo_relative_path(builder_reference, project_root)
    return graph


def validate_graph_contract(graph) -> None:
    missing: list[str] = []
    for name in REQUIRED_TENSOR_FIELDS + REQUIRED_META_FIELDS:
        if not hasattr(graph, name):
            missing.append(name)
    if missing:
        raise RuntimeError(f"graph is missing required contract fields: {', '.join(missing)}")

    num_nodes = int(getattr(graph, "num_nodes", 0) or 0)
    if num_nodes <= 0:
        raise RuntimeError("graph.num_nodes must be positive")

    for name in REQUIRED_TENSOR_FIELDS:
        value = getattr(graph, name)
        if not isinstance(value, torch.Tensor):
            raise RuntimeError(f"graph field '{name}' must be a torch.Tensor")

    if int(graph.x.shape[0]) != num_nodes or int(graph.x_norm.shape[0]) != num_nodes:
        raise RuntimeError("graph feature tensors do not match num_nodes")
    if int(graph.y.shape[0]) != num_nodes:
        raise RuntimeError("graph labels do not match num_nodes")

    for name in (
        "window_idx",
        "ip_idx",
        "train_mask",
        "val_mask",
        "test_mask",
        "temporal_train_mask",
        "temporal_test_mask",
    ):
        if int(getattr(graph, name).shape[0]) != num_nodes:
            raise RuntimeError(f"graph field '{name}' does not match num_nodes")

    if int(graph.edge_index.shape[0]) != 2:
        raise RuntimeError("graph.edge_index must have shape [2, E]")

    source_ips = list(getattr(graph, "source_ips", []))
    if not source_ips:
        raise RuntimeError("graph.source_ips must be non-empty")

    contract_version = str(getattr(graph, "graph_contract_version", "") or "")
    if contract_version and contract_version != GRAPH_CONTRACT_VERSION:
        raise RuntimeError(
            f"graph contract version mismatch: expected {GRAPH_CONTRACT_VERSION}, observed {contract_version}"
        )


def graph_stats(graph) -> dict[str, Any]:
    flow_mask = graph.window_idx >= 0 if hasattr(graph, "window_idx") else torch.ones(graph.num_nodes, dtype=torch.bool)
    return {
        "num_nodes": int(graph.num_nodes),
        "num_edges": int(graph.num_edges),
        "flow_nodes": int(flow_mask.sum().item()),
        "benign_flow_nodes": int(((graph.y == 0) & flow_mask).sum().item()),
        "attack_flow_nodes": int(((graph.y == 1) & flow_mask).sum().item()),
        "num_features": int(graph.x.shape[1]),
        "num_source_ips": int(len(list(getattr(graph, "source_ips", [])))),
        "split_counts": {
            "train": int(getattr(graph, "train_mask", torch.zeros(graph.num_nodes, dtype=torch.bool)).sum().item()),
            "val": int(getattr(graph, "val_mask", torch.zeros(graph.num_nodes, dtype=torch.bool)).sum().item()),
            "test": int(getattr(graph, "test_mask", torch.zeros(graph.num_nodes, dtype=torch.bool)).sum().item()),
        },
    }
