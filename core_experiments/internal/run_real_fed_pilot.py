#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

from adapter_tuning import resolve_tuning_mode
from attack_injection import apply_attack, mark_poisoned_clients, summarize_poisoned_ids
from hierarchical_aggregation import (
    aggregate_hierarchical,
    aggregate_krum_proxy,
    aggregate_mean,
    aggregate_median,
    aggregate_rfa_geometric_median,
)
from hitrust_common import resolve_repo_local_path, resolve_suite_paths, save_json, timestamp_utc
from trust_scoring import compute_trust_score, normalize_scores


class FeatureMLP(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 32, adapter_dim: int = 8, dropout: float = 0.2):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden_dim)
        self.adapter_down = nn.Linear(hidden_dim, adapter_dim)
        self.adapter_up = nn.Linear(adapter_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 2)
        self.classifier = self.fc2
        self.dropout = float(dropout)
        self.adapter_scale = 0.1
        self.backbone_name = "feature_mlp"

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor | None = None) -> torch.Tensor:
        h = F.relu(self.fc1(x))
        a = F.relu(self.adapter_down(h))
        h = h + self.adapter_scale * self.adapter_up(a)
        h = F.dropout(h, p=self.dropout, training=self.training)
        return self.fc2(h)


class GraphSAGEAdapter(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 32, adapter_dim: int = 8, dropout: float = 0.2):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.adapter_down = nn.Linear(hidden_dim, adapter_dim)
        self.adapter_up = nn.Linear(adapter_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, 2)
        self.dropout = float(dropout)
        self.adapter_scale = 0.1
        self.backbone_name = "sage"

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor | None = None) -> torch.Tensor:
        if edge_index is None:
            raise ValueError("edge_index is required for GraphSAGEAdapter")
        h = F.relu(self.conv1(x, edge_index))
        a = F.relu(self.adapter_down(h))
        h = h + self.adapter_scale * self.adapter_up(a)
        h = F.relu(self.conv2(h, edge_index))
        h = F.dropout(h, p=self.dropout, training=self.training)
        return self.classifier(h)


def build_model(backbone: str, in_dim: int, hidden_dim: int, adapter_dim: int) -> nn.Module:
    if backbone == "feature_mlp":
        return FeatureMLP(in_dim=in_dim, hidden_dim=hidden_dim, adapter_dim=adapter_dim)
    if backbone == "sage":
        return GraphSAGEAdapter(in_dim=in_dim, hidden_dim=hidden_dim, adapter_dim=adapter_dim)
    raise KeyError(f"unknown backbone: {backbone}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a real-graph federated pilot on feature inputs")
    p.add_argument("--config", required=True)
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--python-bin", default="")
    return p.parse_args()


def load_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def temporal_split(window_idx: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    valid = window_idx[window_idx >= 0]
    w_min = int(valid.min().item())
    w_max = int(valid.max().item())
    span = max(w_max - w_min + 1, 1)
    tr_end = w_min + int(0.6 * span)
    va_end = w_min + int(0.8 * span)
    train = (window_idx >= w_min) & (window_idx < tr_end)
    val = (window_idx >= tr_end) & (window_idx < va_end)
    test = window_idx >= va_end
    return train, val, test


def parse_role_family(role: str) -> str:
    text = str(role).strip()
    if not text:
        return "unknown"
    if text == "target":
        return "target"
    if text.startswith("bot:"):
        return text
    if text.startswith("benign"):
        return "benign_user"
    return text


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return bool(default)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return bool(default)
    return bool(value)


def load_manifest_metadata(graph) -> dict[str, Any]:
    manifest_file = str(getattr(graph, "manifest_file", "")).strip()
    out: dict[str, Any] = {
        "manifest_file": manifest_file,
        "topology_type": "",
        "load_profile": "",
        "bot_type_mode": "",
        "role_by_ip": {},
        "label_by_ip": {},
    }
    if not manifest_file:
        return out
    path = Path(manifest_file)
    if not path.exists():
        out["manifest_error"] = f"missing_manifest:{path}"
        return out
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        out["manifest_error"] = f"{type(exc).__name__}: {exc}"
        return out
    topology = obj.get("topology", {})
    run_cfg = obj.get("run_config", {})
    out["topology_type"] = str(topology.get("type", ""))
    out["load_profile"] = str(run_cfg.get("load_profile", ""))
    out["bot_type_mode"] = str(run_cfg.get("bot_type_mode", ""))
    out["role_by_ip"] = {str(k): str(v) for k, v in dict(obj.get("roles", {})).items()}
    out["label_by_ip"] = {str(k): safe_int(v, default=-1) for k, v in dict(obj.get("ip_labels", {})).items()}
    return out


def build_ip_records(
    *,
    graph,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
    test_mask: torch.Tensor,
    manifest_meta: dict[str, Any],
) -> list[dict[str, Any]]:
    source_ips = [str(x) for x in list(getattr(graph, "source_ips", []))]
    records: list[dict[str, Any]] = []
    flow_mask = graph.ip_idx >= 0
    role_by_ip = dict(manifest_meta.get("role_by_ip", {}))
    label_by_ip = dict(manifest_meta.get("label_by_ip", {}))
    for ip_index, ip in enumerate(source_ips):
        node_mask = graph.ip_idx == int(ip_index)
        flow_node_mask = node_mask & flow_mask
        total_nodes = int(flow_node_mask.sum().item())
        if total_nodes <= 0:
            continue
        attack_nodes = int(((graph.y == 1) & flow_node_mask).sum().item())
        train_nodes = int((flow_node_mask & train_mask).sum().item())
        val_nodes = int((flow_node_mask & val_mask).sum().item())
        test_nodes = int((flow_node_mask & test_mask).sum().item())
        role = str(role_by_ip.get(ip, "unknown"))
        role_family = parse_role_family(role)
        manifest_label = safe_int(label_by_ip.get(ip, -1), default=-1)
        records.append(
            {
                "ip_index": int(ip_index),
                "ip": ip,
                "role": role,
                "role_family": role_family,
                "manifest_label": manifest_label,
                "total_nodes": total_nodes,
                "train_nodes": train_nodes,
                "val_nodes": val_nodes,
                "test_nodes": test_nodes,
                "attack_nodes": attack_nodes,
                "attack_ratio": float(attack_nodes / max(total_nodes, 1)),
            }
        )
    return records


def assign_ip_records_to_clients(
    *,
    ip_records: list[dict[str, Any]],
    num_clients: int,
    partition_mode: str,
    seed: int,
) -> list[list[dict[str, Any]]]:
    clients: list[list[dict[str, Any]]] = [[] for _ in range(int(num_clients))]
    if not ip_records:
        return clients
    rng = np.random.default_rng(seed)

    if partition_mode == "iid_lite":
        shuffled = list(ip_records)
        rng.shuffle(shuffled)
        client_loads = [0] * int(num_clients)
        for record in sorted(shuffled, key=lambda x: (-int(x["total_nodes"]), int(x["ip_index"]))):
            cid = min(range(int(num_clients)), key=lambda idx: (client_loads[idx], idx))
            clients[cid].append(record)
            client_loads[cid] += int(record["total_nodes"])
        return clients

    if partition_mode == "attack_noniid":
        ordered = sorted(
            ip_records,
            key=lambda x: (
                float(x["attack_ratio"]),
                str(x["role_family"]),
                int(x["ip_index"]),
            ),
        )
    elif partition_mode == "load_noniid":
        ordered = sorted(
            ip_records,
            key=lambda x: (
                int(x["total_nodes"]),
                float(x["attack_ratio"]),
                int(x["ip_index"]),
            ),
        )
    else:
        ordered = sorted(
            ip_records,
            key=lambda x: (
                int(x["ip_index"]),
                str(x["role_family"]),
            ),
        )

    chunks = np.array_split(np.asarray(ordered, dtype=object), int(num_clients))
    for cid, chunk in enumerate(chunks):
        clients[cid] = [dict(item) for item in chunk.tolist()]
    return clients


def compress_named_groups(group_candidates: list[str], num_groups: int) -> list[str]:
    if num_groups <= 1 or not group_candidates:
        return ["group_0" for _ in group_candidates]
    counts = Counter(group_candidates)
    keep_names = {name for name, _count in counts.most_common(max(1, int(num_groups) - 1))}
    out: list[str] = []
    for name in group_candidates:
        out.append(name if name in keep_names else "group_other")
    return out


def assign_client_groups(client_rows: list[dict[str, Any]], num_groups: int) -> list[str]:
    if not client_rows:
        return []
    named_candidates: list[str] = []
    for row in client_rows:
        role_counts = {
            str(k): int(v)
            for k, v in dict(row.get("role_counts", {})).items()
            if str(k) not in {"unknown", "target"} and int(v) > 0
        }
        if role_counts:
            dominant_role = max(sorted(role_counts), key=lambda x: (role_counts[x], x))
            named_candidates.append(f"role:{dominant_role}")
        else:
            named_candidates.append("")
    if any(named_candidates):
        base = [name if name else "role:unknown" for name in named_candidates]
        return compress_named_groups(base, num_groups=num_groups)

    if num_groups <= 1:
        return ["group_0" for _ in client_rows]
    rows_with_load = sorted(
        [(idx, int(row.get("train_nodes", 0))) for idx, row in enumerate(client_rows)],
        key=lambda x: (x[1], x[0]),
    )
    groups = ["group_0" for _ in client_rows]
    for bucket_id, bucket in enumerate(np.array_split(np.asarray(rows_with_load, dtype=object), int(num_groups))):
        for idx, _load in bucket.tolist():
            groups[int(idx)] = f"load_bucket_{bucket_id}"
    return groups


def induce_local_subgraph(visible_mask: torch.Tensor, edge_index: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    local_nodes = torch.nonzero(visible_mask, as_tuple=False).view(-1)
    relabel = torch.full((int(visible_mask.numel()),), -1, dtype=torch.long)
    relabel[local_nodes] = torch.arange(local_nodes.numel(), dtype=torch.long)
    keep_edges = visible_mask[edge_index[0]] & visible_mask[edge_index[1]]
    local_edge_index = relabel[edge_index[:, keep_edges]]
    return local_nodes, local_edge_index


def build_client_views(
    *,
    graph,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
    test_mask: torch.Tensor,
    num_clients: int,
    partition_mode: str,
    seed: int,
    num_groups: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_meta = load_manifest_metadata(graph)
    ip_records = build_ip_records(
        graph=graph,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        manifest_meta=manifest_meta,
    )
    assigned_records = assign_ip_records_to_clients(
        ip_records=ip_records,
        num_clients=num_clients,
        partition_mode=partition_mode,
        seed=seed,
    )
    x = graph.x_norm.float()
    y = graph.y.long()
    edge_index = graph.edge_index.long()
    support_mask = graph.ip_idx < 0
    client_views: list[dict[str, Any]] = []
    client_rows: list[dict[str, Any]] = []
    for cid, records in enumerate(assigned_records):
        owned_ip_indices = sorted(int(r["ip_index"]) for r in records)
        owned_mask = torch.zeros(graph.num_nodes, dtype=torch.bool)
        for ip_index in owned_ip_indices:
            owned_mask |= graph.ip_idx == int(ip_index)
        visible_mask = support_mask | owned_mask
        local_nodes, local_edge_index = induce_local_subgraph(visible_mask, edge_index)
        role_counts = Counter(str(r["role_family"]) for r in records if str(r["role_family"]) not in {"unknown", "target"})
        label_counts = Counter(str(int(r["manifest_label"])) for r in records if int(r["manifest_label"]) >= 0)
        attack_nodes = sum(int(r["attack_nodes"]) for r in records)
        total_nodes = sum(int(r["total_nodes"]) for r in records)
        client_views.append(
            {
                "client_id": int(cid),
                "x": x[local_nodes],
                "y": y[local_nodes],
                "edge_index": local_edge_index,
                "train_mask": train_mask[local_nodes],
                "global_node_ids": local_nodes,
                "owned_ip_indices": owned_ip_indices,
                "owned_ips": [str(r["ip"]) for r in records],
                "train_nodes": int(train_mask[local_nodes].sum().item()),
            }
        )
        client_rows.append(
            {
                "client_id": int(cid),
                "owned_ip_indices": owned_ip_indices,
                "owned_ips": [str(r["ip"]) for r in records],
                "owned_ip_count": len(owned_ip_indices),
                "visible_nodes": int(local_nodes.numel()),
                "visible_flow_nodes": int((visible_mask & (graph.ip_idx >= 0)).sum().item()),
                "local_num_edges": int(local_edge_index.shape[1]),
                "train_nodes": int(train_mask[local_nodes].sum().item()),
                "val_nodes": int(val_mask[local_nodes].sum().item()),
                "test_nodes": int(test_mask[local_nodes].sum().item()),
                "attack_nodes": int(attack_nodes),
                "attack_ratio": float(attack_nodes / max(total_nodes, 1)),
                "role_counts": dict(sorted(role_counts.items())),
                "label_counts": dict(sorted(label_counts.items())),
                "partition_mode": partition_mode,
            }
        )

    group_names = assign_client_groups(client_rows, num_groups=num_groups)
    for view, row, group_name in zip(client_views, client_rows, group_names):
        view["group_name"] = group_name
        row["group_name"] = group_name

    partition_manifest = {
        "partition_mode": partition_mode,
        "seed": int(seed),
        "num_clients": int(num_clients),
        "num_assigned_ips": int(len(ip_records)),
        "support_nodes": int(support_mask.sum().item()),
        "manifest_file": str(manifest_meta.get("manifest_file", "")),
        "topology_type": str(manifest_meta.get("topology_type", "")),
        "load_profile": str(manifest_meta.get("load_profile", "")),
        "bot_type_mode": str(manifest_meta.get("bot_type_mode", "")),
        "clients": client_rows,
    }
    return client_views, partition_manifest


def state_to_numpy(model: nn.Module) -> np.ndarray:
    parts = []
    for tensor in model.state_dict().values():
        parts.append(tensor.detach().cpu().reshape(-1).numpy().astype(np.float64))
    return np.concatenate(parts, axis=0)


def numpy_to_state_like(model: nn.Module, flat: np.ndarray) -> dict[str, torch.Tensor]:
    flat = np.asarray(flat, dtype=np.float64)
    out: dict[str, torch.Tensor] = {}
    cursor = 0
    for key, tensor in model.state_dict().items():
        size = int(tensor.numel())
        chunk = flat[cursor : cursor + size]
        out[key] = torch.as_tensor(chunk, dtype=tensor.dtype).reshape(tensor.shape)
        cursor += size
    return out


def build_state_layout(model: nn.Module) -> list[dict[str, int | str]]:
    layout: list[dict[str, int | str]] = []
    cursor = 0
    for key, tensor in model.state_dict().items():
        size = int(tensor.numel())
        layout.append(
            {
                "name": str(key),
                "start": int(cursor),
                "stop": int(cursor + size),
                "size": int(size),
            }
        )
        cursor += size
    return layout


def evaluate_probs(
    *,
    probs: torch.Tensor,
    y_true: torch.Tensor,
    threshold: float,
) -> dict[str, float]:
    y_pred = (probs >= float(threshold)).long()
    tp = int(((y_pred == 1) & (y_true == 1)).sum().item())
    fp = int(((y_pred == 1) & (y_true == 0)).sum().item())
    fn = int(((y_pred == 0) & (y_true == 1)).sum().item())
    tn = int(((y_pred == 0) & (y_true == 0)).sum().item())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2.0 * precision * recall / max(precision + recall, 1e-8)
    fpr = fp / max(fp + tn, 1)
    acc = (tp + tn) / max(tp + fp + fn + tn, 1)
    return {
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "fpr": float(fpr),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def predict_positive_probs(
    model: nn.Module,
    *,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    mask: torch.Tensor,
) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(x, edge_index)
        probs = F.softmax(logits[mask], dim=1)[:, 1]
    return probs.detach().cpu().numpy().astype(np.float64, copy=False)


def build_behavioral_probe_features(
    x: torch.Tensor,
    *,
    mask: torch.Tensor,
    mix: float,
    scale: float,
) -> torch.Tensor:
    mask = mask.bool()
    if int(mask.sum().item()) <= 0:
        return x.clone()
    root_x = x[mask]
    root_mean = root_x.mean(dim=0, keepdim=True)
    root_std = root_x.std(dim=0, unbiased=False, keepdim=True)
    probe_x = x.clone()
    centered = root_x - root_mean
    direction = torch.sign(centered)
    direction = torch.where(direction == 0, torch.ones_like(direction), direction)
    probe_x[mask] = (1.0 - float(mix)) * root_x + float(mix) * root_mean + float(scale) * root_std * direction
    return probe_x


def bounded_similarity_from_abs_error(error_value: float, scale: float = 0.5) -> float:
    normalized = float(error_value) / max(float(scale), 1e-12)
    return float(max(0.0, min(1.0, 1.0 - normalized)))


def compute_behavioral_probe_metrics(
    *,
    root_probs: np.ndarray,
    probe_probs: np.ndarray,
    server_root_probs: np.ndarray,
    server_probe_probs: np.ndarray,
) -> dict[str, float]:
    root_arr = np.asarray(root_probs, dtype=np.float64)
    probe_arr = np.asarray(probe_probs, dtype=np.float64)
    server_root_arr = np.asarray(server_root_probs, dtype=np.float64)
    server_probe_arr = np.asarray(server_probe_probs, dtype=np.float64)
    alignment_error = float(np.mean(np.abs(root_arr - server_root_arr)))
    probe_alignment_error = float(np.mean(np.abs(probe_arr - server_probe_arr)))
    local_shift = probe_arr - root_arr
    server_shift = server_probe_arr - server_root_arr
    shift_error = float(np.mean(np.abs(local_shift - server_shift)))
    probe_instability = float(np.mean(np.abs(probe_arr - root_arr)))
    return {
        "behavior_alignment": bounded_similarity_from_abs_error(alignment_error, scale=0.5),
        "behavior_probe_alignment": bounded_similarity_from_abs_error(probe_alignment_error, scale=0.5),
        "behavior_shift_alignment": bounded_similarity_from_abs_error(shift_error, scale=0.25),
        "behavior_probe_instability": float(probe_instability),
    }


def compute_layerwise_alignment_metrics(
    update: np.ndarray,
    anchor: np.ndarray,
    *,
    state_layout: list[dict[str, int | str]],
) -> dict[str, float]:
    update_arr = np.asarray(update, dtype=np.float64)
    anchor_arr = np.asarray(anchor, dtype=np.float64)
    layer_cosines: list[float] = []
    layer_residuals: list[float] = []
    layer_weights: list[float] = []
    update_norms: list[float] = []
    anchor_norms: list[float] = []
    for item in state_layout:
        start = int(item["start"])
        stop = int(item["stop"])
        layer_update = update_arr[start:stop]
        layer_anchor = anchor_arr[start:stop]
        update_norm = float(np.linalg.norm(layer_update))
        anchor_norm = float(np.linalg.norm(layer_anchor))
        weight = max(update_norm, anchor_norm, 1e-12)
        layer_cosines.append(cosine_similarity(layer_update, layer_anchor))
        layer_residuals.append(float(np.linalg.norm(layer_update - layer_anchor) / max(anchor_norm, 1e-6)))
        layer_weights.append(weight)
        update_norms.append(update_norm)
        anchor_norms.append(anchor_norm)

    weights = np.asarray(layer_weights, dtype=np.float64)
    weights = weights / max(float(np.sum(weights)), 1e-12)
    cosine_arr = np.asarray(layer_cosines, dtype=np.float64)
    residual_arr = np.asarray(layer_residuals, dtype=np.float64)
    update_norm_arr = np.asarray(update_norms, dtype=np.float64)
    anchor_norm_arr = np.asarray(anchor_norms, dtype=np.float64)
    update_share = update_norm_arr / max(float(np.sum(update_norm_arr)), 1e-12)
    anchor_share = anchor_norm_arr / max(float(np.sum(anchor_norm_arr)), 1e-12)
    profile_shift = 0.5 * float(np.sum(np.abs(update_share - anchor_share)))
    concentration = float(np.max(update_share)) if update_share.size > 0 else 0.0
    anchor_concentration = float(np.max(anchor_share)) if anchor_share.size > 0 else 0.0
    low_align_mass = float(np.sum(weights[cosine_arr < 0.2]))
    return {
        "layerwise_server_cosine": float(np.sum(weights * np.maximum(cosine_arr, 0.0))),
        "layerwise_low_align_mass": float(low_align_mass),
        "layerwise_residual": float(np.sum(weights * np.minimum(residual_arr, 2.0))),
        "layer_profile_shift": float(profile_shift),
        "layer_concentration": float(concentration),
        "layer_anchor_concentration": float(anchor_concentration),
        "layer_concentration_delta": float(max(concentration - anchor_concentration, 0.0)),
    }


def compute_temporal_camouflage_flags(
    *,
    use_temporal_v2: bool,
    peer_redundancy_penalty: float,
    server_cosine: float,
    layerwise_server_cosine: float,
    peer_high_similarity_count: int,
    peer_topk_similarity: float,
    temporal_camouflage_peer_threshold: float,
    temporal_camouflage_server_cosine_max: float,
    temporal_camouflage_layerwise_max: float,
    temporal_camouflage_similarity_threshold: float,
    temporal_camouflage_min_redundant_peers: int,
    temporal_camouflage_cluster_server_cosine_max: float,
) -> dict[str, bool]:
    if not bool(use_temporal_v2):
        return {
            "camouflage_use_temporal_v2": False,
            "camouflage_pair_flag": False,
            "camouflage_cluster_flag": False,
            "camouflage_flag": False,
        }

    pair_flag = bool(
        float(peer_redundancy_penalty) >= float(temporal_camouflage_peer_threshold)
        and float(server_cosine) <= float(temporal_camouflage_server_cosine_max)
        and float(layerwise_server_cosine) <= float(temporal_camouflage_layerwise_max)
    )
    cluster_flag = bool(
        int(peer_high_similarity_count) >= int(temporal_camouflage_min_redundant_peers)
        and float(peer_topk_similarity) >= float(temporal_camouflage_similarity_threshold)
        and float(server_cosine) <= float(temporal_camouflage_cluster_server_cosine_max)
    )
    return {
        "camouflage_use_temporal_v2": True,
        "camouflage_pair_flag": bool(pair_flag),
        "camouflage_cluster_flag": bool(cluster_flag),
        "camouflage_flag": bool(pair_flag or cluster_flag),
    }


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray, eps: float = 1e-12) -> float:
    arr_a = np.asarray(vec_a, dtype=np.float64)
    arr_b = np.asarray(vec_b, dtype=np.float64)
    norm_a = float(np.linalg.norm(arr_a))
    norm_b = float(np.linalg.norm(arr_b))
    if norm_a <= float(eps) or norm_b <= float(eps):
        return 0.0
    cosine = float(np.dot(arr_a, arr_b) / max(norm_a * norm_b, float(eps)))
    return max(-1.0, min(1.0, cosine))


def ema_blend(prev: np.ndarray | None, current: np.ndarray, decay: float) -> np.ndarray:
    current_arr = np.asarray(current, dtype=np.float64)
    if prev is None:
        return current_arr.copy()
    decay = min(max(float(decay), 0.0), 0.999)
    prev_arr = np.asarray(prev, dtype=np.float64)
    return decay * prev_arr + (1.0 - decay) * current_arr


def find_best_threshold(
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
) -> tuple[float, dict[str, float]]:
    model.eval()
    with torch.no_grad():
        logits = model(x, edge_index)
        probs = F.softmax(logits[mask], dim=1)[:, 1]
    best_t = 0.5
    best = evaluate_probs(probs=probs, y_true=y[mask], threshold=best_t)
    for t in np.linspace(0.1, 0.9, 17):
        cur = evaluate_probs(probs=probs, y_true=y[mask], threshold=float(t))
        if cur["f1"] > best["f1"]:
            best_t = float(t)
            best = cur
    return best_t, best


def local_train(
    *,
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    epochs: int,
    lr: float,
) -> nn.Module:
    out = copy.deepcopy(model)
    out.train()
    trainable = [p for p in out.parameters() if p.requires_grad]
    if not trainable:
        raise RuntimeError("no trainable parameters for local training")
    opt = torch.optim.Adam(trainable, lr=lr)
    class_weights = torch.tensor(
        [
            1.0,
            max(1.0, float(((y[mask] == 0).sum().item()) / max(int((y[mask] == 1).sum().item()), 1))),
        ],
        dtype=torch.float32,
    )
    for _ in range(int(epochs)):
        opt.zero_grad()
        logits = out(x, edge_index)[mask]
        loss = F.cross_entropy(logits, y[mask], weight=class_weights)
        loss.backward()
        opt.step()
    return out


def global_warmup_train(
    *,
    model: nn.Module,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    epochs: int,
    lr: float,
) -> None:
    if epochs <= 0:
        return
    for p in model.parameters():
        p.requires_grad = True
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    class_weights = torch.tensor(
        [
            1.0,
            max(1.0, float(((y[mask] == 0).sum().item()) / max(int((y[mask] == 1).sum().item()), 1))),
        ],
        dtype=torch.float32,
    )
    for _ in range(int(epochs)):
        opt.zero_grad()
        logits = model(x, edge_index)[mask]
        loss = F.cross_entropy(logits, y[mask], weight=class_weights)
        loss.backward()
        opt.step()


def build_server_root_mask(
    *,
    train_mask: torch.Tensor,
    y: torch.Tensor,
    root_size: int,
    seed: int,
    selection: str = "balanced_label",
) -> torch.Tensor:
    train_indices = torch.nonzero(train_mask, as_tuple=False).view(-1)
    if train_indices.numel() <= 0:
        raise RuntimeError("cannot build FLTrust root subset from an empty train split")

    target_size = min(max(int(root_size), 1), int(train_indices.numel()))
    rng = np.random.default_rng(int(seed))
    train_indices_np = train_indices.detach().cpu().numpy()

    if selection == "random_train":
        selected = train_indices_np.copy()
        rng.shuffle(selected)
        selected = selected[:target_size]
    elif selection == "balanced_label":
        train_labels = y[train_indices].detach().cpu().numpy()
        pos = train_indices_np[train_labels == 1]
        neg = train_indices_np[train_labels == 0]
        rng.shuffle(pos)
        rng.shuffle(neg)

        selected_parts: list[np.ndarray] = []
        if pos.size > 0 and neg.size > 0 and target_size >= 2:
            take_pos = min(pos.size, max(1, target_size // 2))
            take_neg = min(neg.size, max(1, target_size - take_pos))
            selected_parts.extend([pos[:take_pos], neg[:take_neg]])
            remaining = target_size - take_pos - take_neg
            if remaining > 0:
                leftovers = np.concatenate([pos[take_pos:], neg[take_neg:]], axis=0)
                rng.shuffle(leftovers)
                selected_parts.append(leftovers[:remaining])
        else:
            fallback = train_indices_np.copy()
            rng.shuffle(fallback)
            selected_parts.append(fallback[:target_size])
        selected = np.concatenate(selected_parts, axis=0)
        if selected.shape[0] > target_size:
            selected = selected[:target_size]
        rng.shuffle(selected)
    else:
        raise KeyError(f"unknown server_root_selection: {selection}")

    mask = torch.zeros_like(train_mask, dtype=torch.bool)
    mask[torch.as_tensor(selected, dtype=torch.long)] = True
    return mask


def aggregate_fltrust_like(
    *,
    local_updates: dict[int, np.ndarray],
    server_update: np.ndarray,
) -> tuple[np.ndarray, dict[int, dict[str, float]], str]:
    if not local_updates:
        raise RuntimeError("no client updates available for FLTrust-like aggregation")

    eps = 1e-12
    server_update = np.asarray(server_update, dtype=np.float64)
    server_norm = float(np.linalg.norm(server_update))
    diagnostics: dict[int, dict[str, float]] = {}
    accepted_updates: list[np.ndarray] = []
    accepted_weights: list[float] = []

    for cid, update in local_updates.items():
        update = np.asarray(update, dtype=np.float64)
        update_norm = float(np.linalg.norm(update))
        cosine = 0.0
        trust_weight = 0.0
        normalized_update = np.zeros_like(server_update)
        if server_norm > eps and update_norm > eps:
            cosine = float(np.dot(update, server_update) / max(update_norm * server_norm, eps))
            cosine = max(-1.0, min(1.0, cosine))
            trust_weight = max(0.0, cosine)
            normalized_update = (server_norm / max(update_norm, eps)) * update
        diagnostics[int(cid)] = {
            "server_cosine": float(cosine),
            "trust_weight": float(trust_weight),
            "server_update_norm": float(server_norm),
            "normalized_update_norm": float(np.linalg.norm(normalized_update)),
        }
        if trust_weight > 0.0:
            accepted_updates.append(normalized_update)
            accepted_weights.append(trust_weight)

    if accepted_updates:
        return aggregate_mean(accepted_updates, accepted_weights), diagnostics, "trusted_clients"
    return server_update.copy(), diagnostics, "server_fallback"


def evaluate_candidate_update(
    *,
    model: nn.Module,
    base_state: np.ndarray,
    update: np.ndarray,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
) -> tuple[float, dict[str, float]]:
    candidate = copy.deepcopy(model)
    candidate.load_state_dict(numpy_to_state_like(model, base_state + np.asarray(update, dtype=np.float64)))
    return find_best_threshold(candidate, x=x, edge_index=edge_index, y=y, mask=mask)


def aggregate_fedtruth_like(
    *,
    local_updates: dict[int, np.ndarray],
    iterations: int = 4,
    temperature: float = 4.0,
) -> tuple[np.ndarray, dict[int, dict[str, float]], str]:
    if not local_updates:
        raise RuntimeError("no client updates available for FedTruth-like aggregation")

    ordered = sorted((int(cid), np.asarray(update, dtype=np.float64)) for cid, update in local_updates.items())
    client_ids = [cid for cid, _ in ordered]
    stack = np.stack([update for _, update in ordered], axis=0)
    update_norms = np.linalg.norm(stack, axis=1)
    distance_scale = float(max(np.median(update_norms), 1e-12))
    truth = np.median(stack, axis=0)
    weights = np.full(len(client_ids), 1.0 / max(len(client_ids), 1), dtype=np.float64)
    distances = np.zeros(len(client_ids), dtype=np.float64)

    for _ in range(max(int(iterations), 1)):
        distances = np.linalg.norm(stack - truth[None, :], axis=1) / distance_scale
        weights = np.exp(-max(float(temperature), 1e-6) * distances)
        if not np.isfinite(weights).all() or float(np.sum(weights)) <= 1e-12:
            weights = np.ones(len(client_ids), dtype=np.float64)
        weights = weights / max(float(np.sum(weights)), 1e-12)
        truth = np.tensordot(weights, stack, axes=1)

    truth_norm = float(np.linalg.norm(truth))
    diagnostics: dict[int, dict[str, float]] = {}
    for idx, cid in enumerate(client_ids):
        cosine = 0.0
        if truth_norm > 1e-12 and float(update_norms[idx]) > 1e-12:
            cosine = float(np.dot(stack[idx], truth) / max(float(update_norms[idx]) * truth_norm, 1e-12))
            cosine = max(-1.0, min(1.0, cosine))
        diagnostics[cid] = {
            "truth_weight": float(weights[idx]),
            "truth_distance": float(distances[idx]),
            "truth_cosine": float(cosine),
            "truth_update_norm": float(truth_norm),
            "distance_scale": float(distance_scale),
        }
    return truth, diagnostics, "truth_weighted"


def normalize_update_stack(stack: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    norms = np.linalg.norm(stack, axis=1, keepdims=True)
    safe_norms = np.where(norms > 1e-12, norms, 1.0)
    return stack / safe_norms, norms.reshape(-1)


def cluster_updates_by_direction(
    stack: np.ndarray,
    *,
    num_clusters: int,
    iterations: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    num_points = int(stack.shape[0])
    if num_points <= 0:
        raise RuntimeError("cannot cluster an empty update stack")

    normalized_stack, norms = normalize_update_stack(stack)
    num_clusters = max(1, min(int(num_clusters), num_points))
    if num_clusters == 1:
        return np.zeros(num_points, dtype=np.int64), normalized_stack[:1].copy()

    centroid_indices = [int(np.argmax(norms))]
    while len(centroid_indices) < num_clusters:
        selected = normalized_stack[np.asarray(centroid_indices, dtype=np.int64)]
        similarities = normalized_stack @ selected.T
        nearest_similarity = np.max(similarities, axis=1)
        for idx in centroid_indices:
            nearest_similarity[int(idx)] = 1.0
        next_idx = int(np.argmin(nearest_similarity))
        if next_idx in centroid_indices:
            remaining = [idx for idx in range(num_points) if idx not in centroid_indices]
            if not remaining:
                break
            next_idx = int(remaining[0])
        centroid_indices.append(next_idx)

    centroids = normalized_stack[np.asarray(centroid_indices, dtype=np.int64)].copy()
    assignments = np.zeros(num_points, dtype=np.int64)
    for _ in range(max(int(iterations), 1)):
        similarities = normalized_stack @ centroids.T
        new_assignments = np.argmax(similarities, axis=1).astype(np.int64)
        if np.array_equal(new_assignments, assignments):
            break
        assignments = new_assignments
        for cluster_id in range(num_clusters):
            members = normalized_stack[assignments == cluster_id]
            if members.size == 0:
                similarities = normalized_stack @ centroids.T
                nearest_similarity = np.max(similarities, axis=1)
                refill_idx = int(np.argmin(nearest_similarity))
                assignments[refill_idx] = cluster_id
                members = normalized_stack[assignments == cluster_id]
            center = np.mean(members, axis=0)
            center_norm = float(np.linalg.norm(center))
            centroids[cluster_id] = members[0] if center_norm <= 1e-12 else center / center_norm
    return assignments, centroids


def aggregate_flshield_like(
    *,
    local_updates: dict[int, np.ndarray],
    model: nn.Module,
    base_state: np.ndarray,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    y: torch.Tensor,
    mask: torch.Tensor,
    num_clusters: int = 2,
    cluster_iterations: int = 6,
) -> tuple[np.ndarray, dict[int, dict[str, float | int | bool]], list[int], list[dict[str, Any]], str]:
    if not local_updates:
        raise RuntimeError("no client updates available for FLShield-like aggregation")

    ordered = sorted((int(cid), np.asarray(update, dtype=np.float64)) for cid, update in local_updates.items())
    client_ids = [cid for cid, _ in ordered]
    stack = np.stack([update for _, update in ordered], axis=0)
    normalized_stack, _ = normalize_update_stack(stack)
    assignments, centroids = cluster_updates_by_direction(
        stack,
        num_clusters=num_clusters,
        iterations=cluster_iterations,
    )

    cluster_rows: list[dict[str, Any]] = []
    for cluster_id in sorted(set(int(x) for x in assignments.tolist())):
        member_indices = np.where(assignments == cluster_id)[0]
        member_ids = [int(client_ids[idx]) for idx in member_indices.tolist()]
        cluster_update = aggregate_mean(stack[member_indices])
        threshold, val_metrics = evaluate_candidate_update(
            model=model,
            base_state=base_state,
            update=cluster_update,
            x=x,
            edge_index=edge_index,
            y=y,
            mask=mask,
        )
        centroid = centroids[int(cluster_id)]
        member_cosines = np.clip(normalized_stack[member_indices] @ centroid, -1.0, 1.0)
        cluster_rows.append(
            {
                "cluster_id": int(cluster_id),
                "member_ids": member_ids,
                "cluster_size": int(len(member_ids)),
                "cluster_val_f1": float(val_metrics["f1"]),
                "cluster_val_accuracy": float(val_metrics["accuracy"]),
                "cluster_best_threshold": float(threshold),
                "mean_centroid_cosine": float(np.mean(member_cosines)),
                "cluster_update_norm": float(np.linalg.norm(cluster_update)),
                "cluster_update": cluster_update,
            }
        )

    cluster_rows.sort(
        key=lambda row: (
            float(row["cluster_val_f1"]),
            int(row["cluster_size"]),
            float(row["mean_centroid_cosine"]),
            -int(row["cluster_id"]),
        ),
        reverse=True,
    )
    selected_cluster = cluster_rows[0]
    selected_cluster_id = int(selected_cluster["cluster_id"])
    selected_member_ids = [int(cid) for cid in list(selected_cluster["member_ids"])]
    cluster_meta = {int(row["cluster_id"]): row for row in cluster_rows}
    diagnostics: dict[int, dict[str, float | int | bool]] = {}
    for idx, cid in enumerate(client_ids):
        cluster_id = int(assignments[idx])
        centroid = centroids[cluster_id]
        centroid_cosine = float(np.clip(np.dot(normalized_stack[idx], centroid), -1.0, 1.0))
        diagnostics[cid] = {
            "cluster_id": int(cluster_id),
            "cluster_val_f1": float(cluster_meta[cluster_id]["cluster_val_f1"]),
            "cluster_size": int(cluster_meta[cluster_id]["cluster_size"]),
            "centroid_cosine": float(centroid_cosine),
            "distance_to_centroid": float(1.0 - centroid_cosine),
            "selected_cluster": bool(cluster_id == selected_cluster_id),
            "selected_client": bool(cluster_id == selected_cluster_id),
        }

    serialized_clusters = []
    for row in cluster_rows:
        item = dict(row)
        item.pop("cluster_update", None)
        serialized_clusters.append(item)
    return (
        np.asarray(selected_cluster["cluster_update"], dtype=np.float64),
        diagnostics,
        selected_member_ids,
        serialized_clusters,
        "validation_selected_cluster",
    )


def compute_foolsgold_weights(history_stack: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    history = np.asarray(history_stack, dtype=np.float64)
    if history.ndim != 2:
        raise ValueError("history_stack must be a 2D array")
    num_clients = int(history.shape[0])
    if num_clients <= 0:
        raise RuntimeError("cannot compute FoolsGold weights for zero clients")
    if num_clients == 1:
        return np.ones(1, dtype=np.float64), np.zeros((1, 1), dtype=np.float64)

    eps = 1e-5
    norms = np.linalg.norm(history, axis=1, keepdims=True)
    safe_norms = np.where(norms > 1e-12, norms, 1.0)
    normalized = history / safe_norms
    cosine = np.clip(normalized @ normalized.T, -1.0, 1.0)
    cosine = cosine - np.eye(num_clients, dtype=np.float64)
    maxcs = np.max(cosine, axis=1) + eps

    pardoned = cosine.copy()
    for i in range(num_clients):
        for j in range(num_clients):
            if i == j:
                continue
            if maxcs[i] < maxcs[j]:
                pardoned[i, j] = pardoned[i, j] * maxcs[i] / maxcs[j]

    weights = 1.0 - np.max(pardoned, axis=1)
    weights = np.clip(weights, 0.0, 1.0)
    max_weight = float(np.max(weights))
    if max_weight > eps:
        weights = weights / max_weight
    else:
        weights = np.ones(num_clients, dtype=np.float64)
    weights[np.isclose(weights, 1.0)] = 0.99
    weights = np.log((weights / np.maximum(1.0 - weights, eps)) + eps) + 0.5
    weights[~np.isfinite(weights)] = 1.0
    weights = np.clip(weights, 0.0, 1.0)
    return weights.astype(np.float64), pardoned


def aggregate_foolsgold_official(
    *,
    local_updates: dict[int, np.ndarray],
    history_updates: dict[int, np.ndarray],
) -> tuple[np.ndarray, dict[int, dict[str, float]], str]:
    if not local_updates:
        raise RuntimeError("no client updates available for FoolsGold aggregation")

    ordered = sorted((int(cid), np.asarray(update, dtype=np.float64)) for cid, update in local_updates.items())
    client_ids = [cid for cid, _ in ordered]
    stack = np.stack([update for _, update in ordered], axis=0)
    history_stack = np.stack(
        [
            np.asarray(history_updates.get(cid, np.zeros_like(update)), dtype=np.float64) + update
            for cid, update in ordered
        ],
        axis=0,
    )

    weights, pardoned = compute_foolsgold_weights(history_stack)
    diagnostics: dict[int, dict[str, float]] = {}
    for idx, cid in enumerate(client_ids):
        diagnostics[cid] = {
            "trust_weight": float(weights[idx]),
            "history_update_norm": float(np.linalg.norm(history_stack[idx])),
            "round_update_norm": float(np.linalg.norm(stack[idx])),
            "max_peer_similarity": float(np.max(pardoned[idx])) if pardoned.shape[1] > 0 else 0.0,
        }

    global_update = np.dot(stack.T, weights)
    return np.asarray(global_update, dtype=np.float64), diagnostics, "history_weighted"


def is_adaptive_attack_type(attack_type: str) -> bool:
    return str(attack_type).strip() in {"adaptive_benign_mimic", "adaptive_alie_like"}


def normalize_vector(vec: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    arr = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm <= float(eps):
        return np.zeros_like(arr)
    return arr / norm


def orthogonal_component(vec: np.ndarray, ref: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    arr = np.asarray(vec, dtype=np.float64)
    ref_arr = np.asarray(ref, dtype=np.float64)
    ref_norm_sq = float(np.dot(ref_arr, ref_arr))
    if ref_norm_sq <= float(eps):
        return arr.copy()
    return arr - (float(np.dot(arr, ref_arr)) / ref_norm_sq) * ref_arr


def copy_update_map(local_updates: dict[int, np.ndarray]) -> dict[int, np.ndarray]:
    return {
        int(cid): np.asarray(update, dtype=np.float64).copy()
        for cid, update in local_updates.items()
    }


def compute_alie_z_max(total_clients: int, num_poisoned: int) -> float:
    total = max(int(total_clients), 1)
    poisoned = max(0, min(int(num_poisoned), max(total - 1, 0)))
    clean = max(total - poisoned, 1)
    supporters_needed = max((total // 2 + 1) - poisoned, 0)
    if supporters_needed >= clean:
        return 0.0
    support_prob = (clean - supporters_needed) / max(clean, 1)
    support_prob = min(max(float(support_prob), 1e-3), 1.0 - 1e-3)
    return max(float(statistics.NormalDist().inv_cdf(support_prob)), 0.0)


def build_adaptive_alie_like_attack(
    *,
    local_updates: dict[int, np.ndarray],
    poisoned_clients: set[int],
    attack_scale: float,
    rng: np.random.Generator,
) -> dict[int, np.ndarray]:
    if not local_updates or not poisoned_clients:
        return copy_update_map(local_updates)

    clean_updates = [
        np.asarray(update, dtype=np.float64)
        for cid, update in local_updates.items()
        if int(cid) not in poisoned_clients
    ]
    if not clean_updates:
        return copy_update_map(local_updates)

    clean_stack = np.stack(clean_updates, axis=0)
    clean_mean = np.mean(clean_stack, axis=0)
    clean_std = np.std(clean_stack, axis=0, ddof=0)
    if float(np.linalg.norm(clean_std)) <= 1e-12:
        return build_adaptive_benign_mimic_attack(
            local_updates=local_updates,
            poisoned_clients=poisoned_clients,
            attack_scale=attack_scale,
            rng=rng,
        )

    poisoned_stack = np.stack(
        [np.asarray(local_updates[int(cid)], dtype=np.float64) for cid in sorted(poisoned_clients)],
        axis=0,
    )
    harmful_anchor = -np.mean(poisoned_stack, axis=0)
    harmful_sign = np.sign(harmful_anchor)
    fallback_sign = -np.sign(clean_mean)
    harmful_sign = np.where(harmful_sign != 0.0, harmful_sign, fallback_sign)
    harmful_sign = np.where(harmful_sign != 0.0, harmful_sign, -1.0)

    variance_budget = min(max(float(attack_scale), 0.0), 0.5)
    z_value = max(compute_alie_z_max(len(local_updates), len(poisoned_clients)), 0.35 + 2.0 * variance_budget)
    z_value = min(z_value, 1.5)
    template = clean_mean + z_value * clean_std * harmful_sign
    jitter_scale = variance_budget * 0.03

    attacked: dict[int, np.ndarray] = {}
    for cid, update in local_updates.items():
        update_arr = np.asarray(update, dtype=np.float64)
        if int(cid) not in poisoned_clients:
            attacked[int(cid)] = update_arr.copy()
            continue
        jitter = rng.normal(0.0, 1.0, size=template.shape)
        attacked[int(cid)] = template + jitter_scale * clean_std * jitter
    return attacked


def build_adaptive_benign_mimic_attack(
    *,
    local_updates: dict[int, np.ndarray],
    poisoned_clients: set[int],
    attack_scale: float,
    rng: np.random.Generator,
) -> dict[int, np.ndarray]:
    if not local_updates or not poisoned_clients:
        return copy_update_map(local_updates)

    clean_updates = [
        np.asarray(update, dtype=np.float64)
        for cid, update in local_updates.items()
        if int(cid) not in poisoned_clients
    ]
    ref_update = aggregate_mean(clean_updates if clean_updates else local_updates.values())
    ref_update = np.asarray(ref_update, dtype=np.float64)
    ref_norm = float(np.linalg.norm(ref_update))
    if ref_norm <= 1e-12:
        return copy_update_map(local_updates)

    poisoned_stack = np.stack(
        [np.asarray(local_updates[int(cid)], dtype=np.float64) for cid in sorted(poisoned_clients)],
        axis=0,
    )
    harmful_anchor = -np.mean(poisoned_stack, axis=0)
    anchor_orth = orthogonal_component(harmful_anchor, ref_update)
    anchor_dir = normalize_vector(anchor_orth)
    if float(np.linalg.norm(anchor_dir)) <= 1e-12:
        noise = orthogonal_component(rng.normal(0.0, 1.0, size=ref_update.shape), ref_update)
        anchor_dir = normalize_vector(noise)
    if float(np.linalg.norm(anchor_dir)) <= 1e-12:
        return copy_update_map(local_updates)

    mimic_scale = 1.0 + min(max(float(attack_scale), 0.0), 0.5)
    orth_strength = min(max(float(attack_scale), 0.1) * 3.0, 1.25)
    residual_weight = 0.20
    jitter_weight = 0.05
    attacked: dict[int, np.ndarray] = {}

    for cid, update in local_updates.items():
        update_arr = np.asarray(update, dtype=np.float64)
        if int(cid) not in poisoned_clients:
            attacked[int(cid)] = update_arr.copy()
            continue
        harmful_residual = orthogonal_component(-update_arr, ref_update)
        direction = anchor_dir.copy()
        harmful_dir = normalize_vector(harmful_residual)
        if float(np.linalg.norm(harmful_dir)) > 1e-12:
            direction = normalize_vector(direction + residual_weight * harmful_dir)
        noise = orthogonal_component(rng.normal(0.0, 1.0, size=ref_update.shape), ref_update)
        noise_dir = normalize_vector(noise)
        if float(np.linalg.norm(noise_dir)) > 1e-12:
            direction = normalize_vector(direction + jitter_weight * noise_dir)
        if float(np.linalg.norm(direction)) <= 1e-12:
            direction = anchor_dir.copy()
        attacked[int(cid)] = mimic_scale * ref_update + orth_strength * ref_norm * direction
    return attacked


def apply_adaptive_group_attack(
    *,
    local_updates: dict[int, np.ndarray],
    poisoned_clients: set[int],
    attack_type: str,
    attack_scale: float,
    rng: np.random.Generator,
) -> dict[int, np.ndarray]:
    if attack_type == "adaptive_benign_mimic":
        return build_adaptive_benign_mimic_attack(
            local_updates=local_updates,
            poisoned_clients=poisoned_clients,
            attack_scale=attack_scale,
            rng=rng,
        )
    if attack_type == "adaptive_alie_like":
        return build_adaptive_alie_like_attack(
            local_updates=local_updates,
            poisoned_clients=poisoned_clients,
            attack_scale=attack_scale,
            rng=rng,
        )
    raise KeyError(f"unknown adaptive attack type: {attack_type}")


def select_kept_clients(
    trust_rows: list[dict[str, Any]],
    *,
    trust_threshold: float,
    min_keep_per_group: int = 0,
    group_floor_policy: str = "static",
    group_floor_min_trust_mass: float = 0.0,
) -> tuple[dict[int, bool], list[dict[str, Any]]]:
    keep = {
        int(row["client_id"]): float(row["trust_norm"]) >= float(trust_threshold)
        for row in trust_rows
    }
    diagnostics: list[dict[str, Any]] = []
    if int(min_keep_per_group) <= 0:
        return keep, diagnostics

    grouped_rows: dict[str, list[dict[str, Any]]] = {}
    for row in trust_rows:
        group_name = str(row["group"])
        grouped_rows.setdefault(group_name, []).append(row)

    for group_name, rows in grouped_rows.items():
        kept_now = sum(1 for row in rows if keep[int(row["client_id"])])
        trust_mass = float(sum(max(float(row["trust_norm"]), 0.0) for row in rows))
        max_trust = float(max(float(row["trust_norm"]) for row in rows))
        floor_allowed = True
        if group_floor_policy == "static":
            floor_allowed = True
        elif group_floor_policy == "conditional_trust_mass":
            floor_allowed = trust_mass >= float(group_floor_min_trust_mass)
        else:
            raise KeyError(f"unknown group_floor_policy: {group_floor_policy}")

        selected_by_floor: list[int] = []
        if kept_now >= int(min_keep_per_group):
            diagnostics.append(
                {
                    "group": group_name,
                    "kept_before_floor": int(kept_now),
                    "trust_mass": trust_mass,
                    "max_trust": max_trust,
                    "floor_allowed": bool(floor_allowed),
                    "floor_applied": False,
                    "selected_by_floor": selected_by_floor,
                }
            )
            continue
        if floor_allowed:
            ranked = sorted(
                rows,
                key=lambda x: (
                    float(x["trust_norm"]),
                    float(x["val_f1"]),
                    -float(x["update_norm"]),
                    -int(x["client_id"]),
                ),
                reverse=True,
            )
            need = max(int(min_keep_per_group) - kept_now, 0)
            for row in ranked:
                cid = int(row["client_id"])
                if keep[cid]:
                    continue
                keep[cid] = True
                selected_by_floor.append(cid)
                if len(selected_by_floor) >= need:
                    break
        diagnostics.append(
            {
                "group": group_name,
                "kept_before_floor": int(kept_now),
                "trust_mass": trust_mass,
                "max_trust": max_trust,
                "floor_allowed": bool(floor_allowed),
                "floor_applied": bool(selected_by_floor),
                "selected_by_floor": selected_by_floor,
            }
        )
    return keep, diagnostics


def configure_tuning_mode(model: nn.Module, tuning_mode: str) -> dict[str, int | float | str]:
    mode = resolve_tuning_mode(tuning_mode)

    for p in model.parameters():
        p.requires_grad = False

    if mode.name == "head_only":
        for p in model.classifier.parameters():
            p.requires_grad = True
    elif mode.name == "adapter_ft":
        for module in [model.adapter_down, model.adapter_up, model.classifier]:
            for p in module.parameters():
                p.requires_grad = True
    elif mode.name == "full_ft":
        for p in model.parameters():
            p.requires_grad = True
    else:
        raise KeyError(f"unknown tuning mode: {mode.name}")

    total_params = int(sum(p.numel() for p in model.parameters()))
    trainable_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    return {
        "tuning_mode": mode.name,
        "trainable_ratio_hint": mode.trainable_ratio,
        "comm_multiplier_hint": mode.comm_multiplier,
        "total_params": total_params,
        "trainable_params": trainable_params,
        "trainable_ratio_actual": float(trainable_params / max(total_params, 1)),
    }


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    paths = resolve_suite_paths(
        project_root=args.project_root,
        output_root=Path(args.project_root) / "paper_hitrust" / "runs",
        run_name=str(cfg["run_name"]),
    )

    graph_file = resolve_repo_local_path(str(cfg["graph_file"]), args.project_root)
    graph = torch.load(graph_file, weights_only=False, map_location="cpu")
    x = graph.x_norm.float()
    edge_index = graph.edge_index.long()
    y = graph.y.long()
    flow_mask = graph.window_idx >= 0

    if hasattr(graph, "temporal_train_mask") and hasattr(graph, "val_mask") and hasattr(graph, "test_mask"):
        train_mask = graph.temporal_train_mask.clone().bool()
        val_mask = graph.val_mask.clone().bool()
        test_mask = graph.test_mask.clone().bool()
    else:
        train_mask, val_mask, test_mask = temporal_split(graph.window_idx)
    train_mask &= flow_mask
    val_mask &= flow_mask
    test_mask &= flow_mask

    num_clients = int(cfg.get("num_clients", 10))
    partition_mode = str(cfg.get("partition_mode", "topology_noniid"))
    seed = int(cfg.get("seed", 42))
    rounds = int(cfg.get("rounds", 5))
    local_epochs = int(cfg.get("local_epochs", 1))
    lr = float(cfg.get("lr", 0.01))
    hidden_dim = int(cfg.get("hidden_dim", 32))
    adapter_dim = int(cfg.get("adapter_dim", 8))
    aggregation = str(cfg.get("aggregation", "hierarchical"))
    poison_frac = float(cfg.get("poison_frac", 0.0))
    poison_type = str(cfg.get("poison_type", "none"))
    poison_scale = float(cfg.get("poison_scale", 0.0))
    trust_mode = str(cfg.get("trust_mode", "static"))
    trust_threshold = float(cfg.get("trust_threshold", 0.35))
    min_keep_per_group = int(cfg.get("min_keep_per_group", 0))
    group_floor_policy = str(cfg.get("group_floor_policy", "static"))
    group_floor_min_trust_mass = float(cfg.get("group_floor_min_trust_mass", 0.0))
    num_groups = int(cfg.get("num_groups", 3))
    tuning_mode = str(cfg.get("tuning_mode", "adapter_ft"))
    global_warmup_epochs = int(cfg.get("global_warmup_epochs", 8))
    backbone = str(cfg.get("backbone", "feature_mlp"))
    fedtruth_like_iterations = int(cfg.get("fedtruth_like_iterations", 4))
    fedtruth_like_temperature = float(cfg.get("fedtruth_like_temperature", 4.0))
    flshield_like_num_clusters = int(cfg.get("flshield_like_num_clusters", 2))
    flshield_like_cluster_iterations = int(cfg.get("flshield_like_cluster_iterations", 6))
    foolsgold_use_history = safe_bool(cfg.get("foolsgold_use_history", True), True)
    rfa_max_iter = int(cfg.get("rfa_max_iter", 100))
    rfa_tolerance = float(cfg.get("rfa_tolerance", 1e-6))
    server_root_size = int(cfg.get("server_root_size", 96))
    server_root_seed = int(cfg.get("server_root_seed", 314))
    server_root_local_epochs = int(cfg.get("server_root_local_epochs", local_epochs))
    server_root_lr = float(cfg.get("server_root_lr", lr))
    server_root_selection = str(cfg.get("server_root_selection", "balanced_label"))
    temporal_reputation_decay = float(cfg.get("temporal_reputation_decay", 0.7))
    temporal_history_decay = float(cfg.get("temporal_history_decay", 0.8))
    temporal_server_cosine_floor = float(cfg.get("temporal_server_cosine_floor", -0.1))
    temporal_root_drift_scale = float(cfg.get("temporal_root_drift_scale", 0.12))
    temporal_anchor_blend_min = float(cfg.get("temporal_anchor_blend_min", 0.2))
    temporal_anchor_blend_max = float(cfg.get("temporal_anchor_blend_max", 0.6))
    temporal_peer_topk = int(cfg.get("temporal_peer_topk", 2))
    temporal_score_weights = dict(cfg.get("temporal_score_weights", {}))
    temporal_use_layerwise = safe_bool(cfg.get("temporal_use_layerwise", trust_mode == "temporal_rootguard_v2"), trust_mode == "temporal_rootguard_v2")
    temporal_use_behavioral_probe = safe_bool(cfg.get("temporal_use_behavioral_probe", trust_mode == "temporal_rootguard_v2"), trust_mode == "temporal_rootguard_v2")
    temporal_use_soft_weighting = safe_bool(cfg.get("temporal_use_soft_weighting", trust_mode == "temporal_rootguard_v2"), trust_mode == "temporal_rootguard_v2")
    temporal_behavior_probe_mix = float(cfg.get("temporal_behavior_probe_mix", 0.12))
    temporal_behavior_probe_scale = float(cfg.get("temporal_behavior_probe_scale", 0.10))
    temporal_soft_weight_power = float(cfg.get("temporal_soft_weight_power", 1.5))
    temporal_weight_floor = float(cfg.get("temporal_weight_floor", 0.05 if trust_mode == "temporal_rootguard_v2" else 0.01))
    temporal_hard_reject_floor = float(cfg.get("temporal_hard_reject_floor", 0.08 if trust_mode == "temporal_rootguard_v2" else trust_threshold))
    temporal_redemption_mix = float(cfg.get("temporal_redemption_mix", 0.35 if trust_mode == "temporal_rootguard_v2" else 0.0))
    temporal_camouflage_peer_threshold = float(cfg.get("temporal_camouflage_peer_threshold", 0.90 if trust_mode == "temporal_rootguard_v2" else 1.5))
    temporal_camouflage_server_cosine_max = float(cfg.get("temporal_camouflage_server_cosine_max", 0.05 if trust_mode == "temporal_rootguard_v2" else -1.0))
    temporal_camouflage_layerwise_max = float(cfg.get("temporal_camouflage_layerwise_max", 0.10 if trust_mode == "temporal_rootguard_v2" else -1.0))
    temporal_camouflage_similarity_threshold = float(cfg.get("temporal_camouflage_similarity_threshold", 0.95 if trust_mode == "temporal_rootguard_v2" else 1.1))
    temporal_camouflage_min_redundant_peers = int(cfg.get("temporal_camouflage_min_redundant_peers", 2 if trust_mode == "temporal_rootguard_v2" else 99))
    temporal_camouflage_cluster_server_cosine_max = float(cfg.get("temporal_camouflage_cluster_server_cosine_max", 0.25 if trust_mode == "temporal_rootguard_v2" else -1.0))

    torch.manual_seed(seed)
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    client_views, partition_manifest = build_client_views(
        graph=graph,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        num_clients=num_clients,
        partition_mode=partition_mode,
        seed=seed,
        num_groups=num_groups,
    )
    active_views = [view for view in client_views if int(view["train_nodes"]) > 0]
    if not active_views:
        raise RuntimeError("no client has local train nodes under the current partition")
    active_client_ids = [int(view["client_id"]) for view in active_views]
    poisoned_clients = mark_poisoned_clients(
        num_clients,
        poison_frac,
        rng=rng,
        candidate_ids=active_client_ids,
    )
    partition_manifest["active_clients"] = active_client_ids
    partition_manifest["poisoned_clients"] = summarize_poisoned_ids(poisoned_clients)

    model = build_model(backbone=backbone, in_dim=x.shape[1], hidden_dim=hidden_dim, adapter_dim=adapter_dim)
    state_layout = build_state_layout(model)
    global_warmup_train(
        model=model,
        x=x,
        edge_index=edge_index,
        y=y,
        mask=train_mask,
        epochs=global_warmup_epochs,
        lr=lr,
    )
    tuning_info = configure_tuning_mode(model, tuning_mode=tuning_mode)
    trust_trace: list[dict[str, Any]] = []
    round_rows: list[dict[str, Any]] = []
    prev_updates: dict[int, np.ndarray] = {}
    foolsgold_history: dict[int, np.ndarray] = {}
    temporal_reputation: dict[int, float] = {}
    temporal_update_ema: dict[int, np.ndarray] = {}
    temporal_root_prob_ema: dict[int, np.ndarray] = {}
    temporal_weight_ema: dict[int, float] = {}
    prev_global_update: np.ndarray | None = None
    server_root_mask = None
    server_root_info: dict[str, Any] | None = None
    root_probe_x = None
    if aggregation == "fltrust_like" or trust_mode in {"temporal_rootguard", "temporal_rootguard_v2"}:
        server_root_mask = build_server_root_mask(
            train_mask=train_mask,
            y=y,
            root_size=server_root_size,
            seed=server_root_seed,
            selection=server_root_selection,
        )
        server_root_info = {
            "selection": server_root_selection,
            "seed": int(server_root_seed),
            "root_size": int(server_root_mask.sum().item()),
            "positive_nodes": int(((y == 1) & server_root_mask).sum().item()),
            "negative_nodes": int(((y == 0) & server_root_mask).sum().item()),
            "local_epochs": int(server_root_local_epochs),
            "lr": float(server_root_lr),
            "source": "global_train_subset",
        }
        if temporal_use_behavioral_probe and trust_mode in {"temporal_rootguard", "temporal_rootguard_v2"}:
            root_probe_x = build_behavioral_probe_features(
                x,
                mask=server_root_mask,
                mix=temporal_behavior_probe_mix,
                scale=temporal_behavior_probe_scale,
            )

    for round_id in range(1, rounds + 1):
        base_state = state_to_numpy(model)
        raw_local_updates: dict[int, np.ndarray] = {}
        local_models: dict[int, nn.Module] = {}
        for view in active_views:
            cid = int(view["client_id"])
            trained = local_train(
                model=model,
                x=view["x"],
                edge_index=view["edge_index"],
                y=view["y"],
                mask=view["train_mask"],
                epochs=local_epochs,
                lr=lr,
            )
            update = state_to_numpy(trained) - base_state
            raw_local_updates[cid] = update
            local_models[cid] = trained

        if is_adaptive_attack_type(poison_type):
            local_updates = apply_adaptive_group_attack(
                local_updates=raw_local_updates,
                poisoned_clients=poisoned_clients,
                attack_type=poison_type,
                attack_scale=poison_scale,
                rng=rng,
            )
        else:
            local_updates = {}
            for cid, update in raw_local_updates.items():
                attacked_update = np.asarray(update, dtype=np.float64).copy()
                if cid in poisoned_clients:
                    attacked_update = apply_attack(
                        attacked_update,
                        attack_type=poison_type,
                        attack_scale=poison_scale,
                        rng=rng,
                    )
                local_updates[cid] = attacked_update

        if not local_updates:
            raise RuntimeError("no local updates were produced")

        update_norms = {cid: float(np.linalg.norm(upd)) for cid, upd in local_updates.items()}
        client_eval: dict[int, dict[str, Any]] = {}
        for cid, local_model in local_models.items():
            local_state = numpy_to_state_like(model, base_state + local_updates[cid])
            local_model.load_state_dict(local_state)
            threshold, val_metrics = find_best_threshold(local_model, x=x, edge_index=edge_index, y=y, mask=val_mask)
            client_eval[cid] = {
                "threshold": float(threshold),
                "val_metrics": val_metrics,
            }

        trust_rows: list[dict[str, Any]] = []
        keep: dict[int, bool]
        floor_diagnostics: list[dict[str, Any]]
        aggregation_mode = aggregation
        if aggregation == "fltrust_like":
            if server_root_mask is None:
                raise RuntimeError("server_root_mask was not prepared for fltrust_like aggregation")
            server_model = local_train(
                model=model,
                x=x,
                edge_index=edge_index,
                y=y,
                mask=server_root_mask,
                epochs=server_root_local_epochs,
                lr=server_root_lr,
            )
            server_update = state_to_numpy(server_model) - base_state
            global_update, fltrust_diag, aggregation_mode = aggregate_fltrust_like(
                local_updates=local_updates,
                server_update=server_update,
            )
            for view in active_views:
                cid = int(view["client_id"])
                eval_row = client_eval[cid]
                diag = fltrust_diag[cid]
                trust_weight = float(diag["trust_weight"])
                trust_rows.append(
                    {
                        "round": round_id,
                        "client_id": cid,
                        "group": str(view["group_name"]),
                        "is_poisoned": bool(cid in poisoned_clients),
                        "owned_ip_count": len(view["owned_ip_indices"]),
                        "best_val_threshold": float(eval_row["threshold"]),
                        "trust_raw": trust_weight,
                        "trust_norm": trust_weight,
                        "val_f1": float(eval_row["val_metrics"]["f1"]),
                        "similarity": float(diag["server_cosine"]),
                        "stability": 0.0,
                        "update_norm": update_norms[cid],
                        "server_cosine": float(diag["server_cosine"]),
                        "server_update_norm": float(diag["server_update_norm"]),
                        "normalized_update_norm": float(diag["normalized_update_norm"]),
                    }
                )
                prev_updates[cid] = local_updates[cid].copy()
            keep = {int(row["client_id"]): float(row["trust_norm"]) > 0.0 for row in trust_rows}
            floor_diagnostics = []
        elif aggregation == "fedtruth_like":
            global_update, fedtruth_diag, aggregation_mode = aggregate_fedtruth_like(
                local_updates=local_updates,
                iterations=fedtruth_like_iterations,
                temperature=fedtruth_like_temperature,
            )
            for view in active_views:
                cid = int(view["client_id"])
                eval_row = client_eval[cid]
                diag = fedtruth_diag[cid]
                truth_weight = float(diag["truth_weight"])
                trust_rows.append(
                    {
                        "round": round_id,
                        "client_id": cid,
                        "group": str(view["group_name"]),
                        "is_poisoned": bool(cid in poisoned_clients),
                        "owned_ip_count": len(view["owned_ip_indices"]),
                        "best_val_threshold": float(eval_row["threshold"]),
                        "trust_raw": truth_weight,
                        "trust_norm": truth_weight,
                        "val_f1": float(eval_row["val_metrics"]["f1"]),
                        "similarity": float(diag["truth_cosine"]),
                        "stability": 0.0,
                        "update_norm": update_norms[cid],
                        "truth_weight": float(diag["truth_weight"]),
                        "truth_distance": float(diag["truth_distance"]),
                        "truth_cosine": float(diag["truth_cosine"]),
                        "truth_update_norm": float(diag["truth_update_norm"]),
                        "distance_scale": float(diag["distance_scale"]),
                    }
                )
                prev_updates[cid] = local_updates[cid].copy()
            keep = {int(row["client_id"]): True for row in trust_rows}
            floor_diagnostics = []
        elif aggregation == "flshield_like":
            global_update, flshield_diag, selected_client_ids, cluster_rows, aggregation_mode = aggregate_flshield_like(
                local_updates=local_updates,
                model=model,
                base_state=base_state,
                x=x,
                edge_index=edge_index,
                y=y,
                mask=val_mask,
                num_clusters=flshield_like_num_clusters,
                cluster_iterations=flshield_like_cluster_iterations,
            )
            selected_client_set = {int(cid) for cid in selected_client_ids}
            for view in active_views:
                cid = int(view["client_id"])
                eval_row = client_eval[cid]
                diag = flshield_diag[cid]
                trust_rows.append(
                    {
                        "round": round_id,
                        "client_id": cid,
                        "group": str(view["group_name"]),
                        "is_poisoned": bool(cid in poisoned_clients),
                        "owned_ip_count": len(view["owned_ip_indices"]),
                        "best_val_threshold": float(eval_row["threshold"]),
                        "trust_raw": float(diag["cluster_val_f1"]),
                        "trust_norm": 1.0 if bool(diag["selected_client"]) else 0.0,
                        "val_f1": float(eval_row["val_metrics"]["f1"]),
                        "similarity": float(diag["centroid_cosine"]),
                        "stability": 0.0,
                        "update_norm": update_norms[cid],
                        "cluster_id": int(diag["cluster_id"]),
                        "cluster_val_f1": float(diag["cluster_val_f1"]),
                        "cluster_size": int(diag["cluster_size"]),
                        "centroid_cosine": float(diag["centroid_cosine"]),
                        "distance_to_centroid": float(diag["distance_to_centroid"]),
                        "selected_cluster": bool(diag["selected_cluster"]),
                    }
                )
                prev_updates[cid] = local_updates[cid].copy()
            keep = {int(row["client_id"]): int(row["client_id"]) in selected_client_set for row in trust_rows}
            floor_diagnostics = [
                {
                    "aggregation": "flshield_like",
                    "clusters": cluster_rows,
                    "selected_client_ids": sorted(selected_client_set),
                }
            ]
        elif aggregation == "foolsgold":
            history_view = foolsgold_history if foolsgold_use_history else {}
            global_update, foolsgold_diag, aggregation_mode = aggregate_foolsgold_official(
                local_updates=local_updates,
                history_updates=history_view,
            )
            for view in active_views:
                cid = int(view["client_id"])
                eval_row = client_eval[cid]
                diag = foolsgold_diag[cid]
                trust_rows.append(
                    {
                        "round": round_id,
                        "client_id": cid,
                        "group": str(view["group_name"]),
                        "is_poisoned": bool(cid in poisoned_clients),
                        "owned_ip_count": len(view["owned_ip_indices"]),
                        "best_val_threshold": float(eval_row["threshold"]),
                        "trust_raw": float(diag["trust_weight"]),
                        "trust_norm": float(diag["trust_weight"]),
                        "val_f1": float(eval_row["val_metrics"]["f1"]),
                        "similarity": float(diag["max_peer_similarity"]),
                        "stability": 0.0,
                        "update_norm": update_norms[cid],
                        "history_update_norm": float(diag["history_update_norm"]),
                        "round_update_norm": float(diag["round_update_norm"]),
                        "max_peer_similarity": float(diag["max_peer_similarity"]),
                    }
                )
                if foolsgold_use_history:
                    prev_history = foolsgold_history.get(cid)
                    if prev_history is None:
                        foolsgold_history[cid] = np.asarray(local_updates[cid], dtype=np.float64).copy()
                    else:
                        foolsgold_history[cid] = prev_history + np.asarray(local_updates[cid], dtype=np.float64)
                prev_updates[cid] = local_updates[cid].copy()
            keep = {int(row["client_id"]): float(row["trust_norm"]) > 0.0 for row in trust_rows}
            floor_diagnostics = []
        else:
            mean_update = aggregate_mean(local_updates.values())
            if trust_mode in {"temporal_rootguard", "temporal_rootguard_v2"}:
                if server_root_mask is None:
                    raise RuntimeError("server_root_mask was not prepared for temporal_rootguard trust mode")
                use_temporal_v2 = trust_mode == "temporal_rootguard_v2"
                server_model = local_train(
                    model=model,
                    x=x,
                    edge_index=edge_index,
                    y=y,
                    mask=server_root_mask,
                    epochs=server_root_local_epochs,
                    lr=server_root_lr,
                )
                server_update = state_to_numpy(server_model) - base_state
                server_root_probs = predict_positive_probs(
                    server_model,
                    x=x,
                    edge_index=edge_index,
                    mask=server_root_mask,
                )
                server_probe_probs = None
                if temporal_use_behavioral_probe and root_probe_x is not None:
                    server_probe_probs = predict_positive_probs(
                        server_model,
                        x=root_probe_x,
                        edge_index=edge_index,
                        mask=server_root_mask,
                    )
                root_prob_cache: dict[int, np.ndarray] = {}
                score_cfg = {
                    "server_cosine": 0.35,
                    "history_cosine": 0.20,
                    "global_alignment": 0.10,
                    "root_f1": 0.10,
                    "val_f1": 0.05,
                    "stability": 0.10,
                    "server_misalignment_penalty": 0.20,
                    "root_prob_drift_penalty": 0.10,
                    "history_residual_penalty": 0.10,
                    "peer_redundancy_penalty": 0.20,
                    "layerwise_server_cosine": 0.15 if use_temporal_v2 else 0.0,
                    "behavior_alignment": 0.12 if use_temporal_v2 else 0.0,
                    "behavior_probe_alignment": 0.10 if use_temporal_v2 else 0.0,
                    "behavior_shift_alignment": 0.10 if use_temporal_v2 else 0.0,
                    "layer_profile_penalty": 0.12 if use_temporal_v2 else 0.0,
                    "layer_concentration_penalty": 0.08 if use_temporal_v2 else 0.0,
                }
                for key, value in temporal_score_weights.items():
                    score_cfg[str(key)] = float(value)
                ordered_peer = sorted((int(cid), np.asarray(update, dtype=np.float64)) for cid, update in local_updates.items())
                peer_client_ids = [cid for cid, _ in ordered_peer]
                peer_stack = np.stack([update for _cid, update in ordered_peer], axis=0)
                peer_normed, _ = normalize_update_stack(peer_stack)
                peer_similarity_matrix = peer_normed @ peer_normed.T
                np.fill_diagonal(peer_similarity_matrix, -1.0)
                peer_similarity_by_client = {
                    int(cid): peer_similarity_matrix[idx].copy()
                    for idx, cid in enumerate(peer_client_ids)
                }

                for view in active_views:
                    cid = int(view["client_id"])
                    eval_row = client_eval[cid]
                    val_metrics = eval_row["val_metrics"]
                    local_model = local_models[cid]
                    root_threshold, root_metrics = find_best_threshold(
                        local_model,
                        x=x,
                        edge_index=edge_index,
                        y=y,
                        mask=server_root_mask,
                    )
                    root_probs = predict_positive_probs(
                        local_model,
                        x=x,
                        edge_index=edge_index,
                        mask=server_root_mask,
                    )
                    root_prob_cache[cid] = root_probs
                    behavior_metrics = {
                        "behavior_alignment": 1.0,
                        "behavior_probe_alignment": 1.0,
                        "behavior_shift_alignment": 1.0,
                        "behavior_probe_instability": 0.0,
                    }
                    if temporal_use_behavioral_probe and root_probe_x is not None and server_probe_probs is not None:
                        local_probe_probs = predict_positive_probs(
                            local_model,
                            x=root_probe_x,
                            edge_index=edge_index,
                            mask=server_root_mask,
                        )
                        behavior_metrics = compute_behavioral_probe_metrics(
                            root_probs=root_probs,
                            probe_probs=local_probe_probs,
                            server_root_probs=server_root_probs,
                            server_probe_probs=server_probe_probs,
                        )

                    similarity = 1.0 - float(
                        np.linalg.norm(local_updates[cid] - mean_update)
                        / max(np.linalg.norm(mean_update), 1e-6)
                    )
                    similarity = max(-1.0, min(1.0, similarity))
                    prev = prev_updates.get(cid)
                    stability = 1.0 if prev is None else 1.0 - float(
                        np.linalg.norm(local_updates[cid] - prev) / max(np.linalg.norm(prev), 1e-6)
                    )
                    stability = max(-1.0, min(1.0, stability))

                    server_cosine = cosine_similarity(local_updates[cid], server_update)
                    history_update = temporal_update_ema.get(cid)
                    history_cosine = 1.0 if history_update is None else cosine_similarity(local_updates[cid], history_update)
                    history_cosine = max(-1.0, min(1.0, history_cosine))
                    history_residual = 0.0
                    if history_update is not None:
                        history_residual = float(
                            np.linalg.norm(local_updates[cid] - history_update)
                            / max(np.linalg.norm(history_update), 1e-6)
                        )
                    history_residual = min(max(history_residual, 0.0), 1.5)

                    root_prob_prev = temporal_root_prob_ema.get(cid)
                    root_prob_drift = 0.0
                    if root_prob_prev is not None and root_prob_prev.shape == root_probs.shape:
                        root_prob_drift = float(np.mean(np.abs(root_probs - root_prob_prev)))
                    root_prob_drift_penalty = min(
                        max(root_prob_drift / max(temporal_root_drift_scale, 1e-6), 0.0),
                        1.5,
                    )
                    peer_similarities = np.asarray(peer_similarity_by_client.get(cid, np.empty(0)), dtype=np.float64)
                    peer_topk_similarity = 0.0
                    if peer_similarities.size > 0:
                        positive_peer = np.sort(peer_similarities[peer_similarities > -0.5])[::-1]
                        topk = positive_peer[: max(1, min(int(temporal_peer_topk), int(positive_peer.size)))]
                        if topk.size > 0:
                            peer_topk_similarity = float(np.mean(topk))
                    peer_high_similarity_count = int(
                        np.sum(peer_similarities >= float(temporal_camouflage_similarity_threshold))
                    ) if peer_similarities.size > 0 else 0
                    peer_redundancy_penalty = max(0.0, peer_topk_similarity - max(server_cosine, 0.0))
                    layer_metrics = {
                        "layerwise_server_cosine": max(server_cosine, 0.0),
                        "layerwise_low_align_mass": 0.0,
                        "layerwise_residual": 0.0,
                        "layer_profile_shift": 0.0,
                        "layer_concentration": 0.0,
                        "layer_anchor_concentration": 0.0,
                        "layer_concentration_delta": 0.0,
                    }
                    if temporal_use_layerwise:
                        layer_metrics = compute_layerwise_alignment_metrics(
                            local_updates[cid],
                            server_update,
                            state_layout=state_layout,
                        )
                    camouflage_diag = compute_temporal_camouflage_flags(
                        use_temporal_v2=use_temporal_v2,
                        peer_redundancy_penalty=peer_redundancy_penalty,
                        server_cosine=server_cosine,
                        layerwise_server_cosine=float(layer_metrics["layerwise_server_cosine"]),
                        peer_high_similarity_count=peer_high_similarity_count,
                        peer_topk_similarity=peer_topk_similarity,
                        temporal_camouflage_peer_threshold=temporal_camouflage_peer_threshold,
                        temporal_camouflage_server_cosine_max=temporal_camouflage_server_cosine_max,
                        temporal_camouflage_layerwise_max=temporal_camouflage_layerwise_max,
                        temporal_camouflage_similarity_threshold=temporal_camouflage_similarity_threshold,
                        temporal_camouflage_min_redundant_peers=temporal_camouflage_min_redundant_peers,
                        temporal_camouflage_cluster_server_cosine_max=temporal_camouflage_cluster_server_cosine_max,
                    )
                    camouflage_flag = bool(camouflage_diag["camouflage_flag"])

                    global_alignment = 0.0 if prev_global_update is None else cosine_similarity(
                        local_updates[cid],
                        prev_global_update,
                    )
                    positive_server = max(server_cosine, 0.0)
                    positive_history = max(history_cosine, 0.0)
                    positive_global = max(global_alignment, 0.0)
                    server_misalignment_penalty = max(-server_cosine, 0.0)
                    prev_rep = float(temporal_reputation.get(cid, positive_server))
                    instant_score = (
                        score_cfg["server_cosine"] * positive_server
                        + score_cfg["history_cosine"] * positive_history
                        + score_cfg["global_alignment"] * positive_global
                        + score_cfg["root_f1"] * float(root_metrics["f1"])
                        + score_cfg["val_f1"] * float(val_metrics["f1"])
                        + score_cfg["stability"] * max(stability, 0.0)
                        + score_cfg["layerwise_server_cosine"] * max(float(layer_metrics["layerwise_server_cosine"]), 0.0)
                        + score_cfg["behavior_alignment"] * max(float(behavior_metrics["behavior_alignment"]), 0.0)
                        + score_cfg["behavior_probe_alignment"] * max(float(behavior_metrics["behavior_probe_alignment"]), 0.0)
                        + score_cfg["behavior_shift_alignment"] * max(float(behavior_metrics["behavior_shift_alignment"]), 0.0)
                        - score_cfg["server_misalignment_penalty"] * server_misalignment_penalty
                        - score_cfg["root_prob_drift_penalty"] * root_prob_drift_penalty
                        - score_cfg["history_residual_penalty"] * history_residual
                        - score_cfg["peer_redundancy_penalty"] * peer_redundancy_penalty
                        - score_cfg["layer_profile_penalty"] * float(layer_metrics["layer_profile_shift"])
                        - score_cfg["layer_concentration_penalty"] * float(layer_metrics["layer_concentration_delta"])
                    )
                    trust_raw = float(instant_score)
                    if round_id > 1:
                        trust_raw = float(
                            temporal_reputation_decay * prev_rep
                            + (1.0 - temporal_reputation_decay) * instant_score
                        )
                    trusted_anchor = bool(server_cosine >= temporal_server_cosine_floor)
                    trust_rows.append(
                        {
                            "round": round_id,
                            "client_id": cid,
                            "group": str(view["group_name"]),
                            "is_poisoned": bool(cid in poisoned_clients),
                            "owned_ip_count": len(view["owned_ip_indices"]),
                            "best_val_threshold": float(eval_row["threshold"]),
                            "trust_raw": trust_raw,
                            "val_f1": float(val_metrics["f1"]),
                            "similarity": similarity,
                            "stability": stability,
                            "update_norm": update_norms[cid],
                            "root_threshold": float(root_threshold),
                            "root_f1": float(root_metrics["f1"]),
                            "root_accuracy": float(root_metrics["accuracy"]),
                            "root_prob_drift": float(root_prob_drift),
                            "root_prob_drift_penalty": float(root_prob_drift_penalty),
                            "peer_topk_similarity": float(peer_topk_similarity),
                            "peer_high_similarity_count": int(peer_high_similarity_count),
                            "peer_redundancy_penalty": float(peer_redundancy_penalty),
                            "server_cosine": float(server_cosine),
                            "history_cosine": float(history_cosine),
                            "history_residual": float(history_residual),
                            "global_alignment": float(global_alignment),
                            "layerwise_server_cosine": float(layer_metrics["layerwise_server_cosine"]),
                            "layerwise_low_align_mass": float(layer_metrics["layerwise_low_align_mass"]),
                            "layerwise_residual": float(layer_metrics["layerwise_residual"]),
                            "layer_profile_shift": float(layer_metrics["layer_profile_shift"]),
                            "layer_concentration": float(layer_metrics["layer_concentration"]),
                            "layer_concentration_delta": float(layer_metrics["layer_concentration_delta"]),
                            "behavior_alignment": float(behavior_metrics["behavior_alignment"]),
                            "behavior_probe_alignment": float(behavior_metrics["behavior_probe_alignment"]),
                            "behavior_shift_alignment": float(behavior_metrics["behavior_shift_alignment"]),
                            "behavior_probe_instability": float(behavior_metrics["behavior_probe_instability"]),
                            "camouflage_use_temporal_v2": bool(camouflage_diag["camouflage_use_temporal_v2"]),
                            "camouflage_pair_flag": bool(camouflage_diag["camouflage_pair_flag"]),
                            "camouflage_cluster_flag": bool(camouflage_diag["camouflage_cluster_flag"]),
                            "camouflage_flag": bool(camouflage_flag),
                            "instant_score": float(instant_score),
                            "reputation_prev": float(prev_rep),
                            "trusted_anchor": trusted_anchor,
                        }
                    )
                    prev_updates[cid] = local_updates[cid].copy()

                trust_rows = normalize_scores(trust_rows)
                raw_keep, floor_diagnostics = select_kept_clients(
                    trust_rows,
                    trust_threshold=trust_threshold,
                    min_keep_per_group=min_keep_per_group,
                    group_floor_policy=group_floor_policy,
                    group_floor_min_trust_mass=group_floor_min_trust_mass,
                )
                keep = {}
                for row in trust_rows:
                    cid = int(row["client_id"])
                    camouflage_diag = compute_temporal_camouflage_flags(
                        use_temporal_v2=use_temporal_v2,
                        peer_redundancy_penalty=float(row.get("peer_redundancy_penalty", 0.0)),
                        server_cosine=float(row.get("server_cosine", 0.0)),
                        layerwise_server_cosine=float(row.get("layerwise_server_cosine", 1.0)),
                        peer_high_similarity_count=int(row.get("peer_high_similarity_count", 0)),
                        peer_topk_similarity=float(row.get("peer_topk_similarity", 0.0)),
                        temporal_camouflage_peer_threshold=temporal_camouflage_peer_threshold,
                        temporal_camouflage_server_cosine_max=temporal_camouflage_server_cosine_max,
                        temporal_camouflage_layerwise_max=temporal_camouflage_layerwise_max,
                        temporal_camouflage_similarity_threshold=temporal_camouflage_similarity_threshold,
                        temporal_camouflage_min_redundant_peers=temporal_camouflage_min_redundant_peers,
                        temporal_camouflage_cluster_server_cosine_max=temporal_camouflage_cluster_server_cosine_max,
                    )
                    row["camouflage_use_temporal_v2"] = bool(camouflage_diag["camouflage_use_temporal_v2"])
                    row["camouflage_pair_flag"] = bool(camouflage_diag["camouflage_pair_flag"])
                    row["camouflage_cluster_flag"] = bool(camouflage_diag["camouflage_cluster_flag"])
                    row["camouflage_flag"] = bool(camouflage_diag["camouflage_flag"])
                    if use_temporal_v2 and temporal_use_soft_weighting:
                        redemption_prev = float(temporal_weight_ema.get(cid, 0.0))
                        behavior_alignment = float(row.get("behavior_alignment", 1.0))
                        layer_profile_shift = float(row.get("layer_profile_shift", 0.0))
                        soft_eligible = bool(raw_keep[cid]) or (
                            redemption_prev >= float(temporal_weight_floor)
                            and behavior_alignment >= 0.60
                            and layer_profile_shift <= 0.45
                        )
                        keep[cid] = (
                            bool(row["trusted_anchor"])
                            and float(row["trust_norm"]) >= float(temporal_hard_reject_floor)
                            and bool(soft_eligible)
                            and not bool(row["camouflage_flag"])
                        )
                    else:
                        keep[cid] = bool(raw_keep[cid] and bool(row["trusted_anchor"]))

                grouped_updates: dict[str, list[np.ndarray]] = {}
                grouped_weights: dict[str, list[float]] = {}
                accepted_root_mass = 0.0
                accepted_weight_mass = 0.0
                accepted_count = 0
                for row in trust_rows:
                    cid = int(row["client_id"])
                    passed_threshold = float(row["trust_norm"]) >= float(trust_threshold)
                    row["passed_threshold"] = bool(passed_threshold)
                    redemption_prev = float(temporal_weight_ema.get(cid, 0.0))
                    soft_weight = 0.0
                    if bool(row["camouflage_flag"]):
                        soft_weight = 0.0
                    elif bool(row["trusted_anchor"]) and float(row["trust_norm"]) >= float(temporal_hard_reject_floor):
                        behavior_alignment = float(row.get("behavior_alignment", 1.0))
                        layer_profile_shift = float(row.get("layer_profile_shift", 0.0))
                        if passed_threshold:
                            margin = max(
                                (float(row["trust_norm"]) - float(trust_threshold))
                                / max(1.0 - float(trust_threshold), 1e-6),
                                0.0,
                            )
                            soft_weight = float(temporal_weight_floor) + (1.0 - float(temporal_weight_floor)) * (
                                margin ** max(float(temporal_soft_weight_power), 1e-6)
                            )
                        elif use_temporal_v2 and temporal_use_soft_weighting:
                            soft_weight = float(temporal_weight_floor) * min(max(redemption_prev, 0.0), 1.0)
                            if behavior_alignment < 0.75 or layer_profile_shift > 0.35:
                                soft_weight *= 0.25
                        if use_temporal_v2 and temporal_use_soft_weighting and soft_weight > 0.0:
                            behavior_gate = max(behavior_alignment, 0.20)
                            soft_weight *= behavior_gate
                            soft_weight = (
                                (1.0 - float(temporal_redemption_mix)) * soft_weight
                                + float(temporal_redemption_mix) * redemption_prev
                            )
                    elif bool(row["trusted_anchor"]) and float(temporal_redemption_mix) > 0.0:
                        soft_weight = float(temporal_redemption_mix) * redemption_prev * 0.5
                    row["soft_weight"] = float(max(soft_weight, 0.0))
                    row["selected_by_floor"] = bool(raw_keep[cid] and not passed_threshold and row["soft_weight"] > 0.0)
                    row["kept_final"] = bool(keep[cid] and row["soft_weight"] > 0.0)
                    if not keep[cid]:
                        continue
                    group_name = str(row["group"])
                    weight = max(float(row["soft_weight"]), 0.0)
                    if use_temporal_v2:
                        weight *= max(float(row["server_cosine"]), 0.05)
                        weight *= max(1.0 - float(row.get("layer_profile_shift", 0.0)), 0.2)
                        weight *= max(float(row.get("behavior_alignment", 1.0)), 0.2)
                    else:
                        weight *= max(float(row["server_cosine"]), 0.05)
                    if weight <= 0.0:
                        row["kept_final"] = False
                        continue
                    accepted_count += 1
                    accepted_root_mass += float(weight) * max(float(row["server_cosine"]), 0.0)
                    accepted_weight_mass += float(weight)
                    grouped_updates.setdefault(group_name, []).append(local_updates[cid])
                    grouped_weights.setdefault(group_name, []).append(weight)

                if grouped_updates:
                    if aggregation == "hierarchical":
                        client_update, _ = aggregate_hierarchical(grouped_updates, grouped_weights)
                    elif aggregation == "mean":
                        flat = [u for arr in grouped_updates.values() for u in arr]
                        w = [w for arr in grouped_weights.values() for w in arr]
                        client_update = aggregate_mean(flat, w)
                    elif aggregation == "rfa":
                        flat = [u for arr in grouped_updates.values() for u in arr]
                        w = [w for arr in grouped_weights.values() for w in arr]
                        client_update = aggregate_rfa_geometric_median(
                            flat,
                            w,
                            max_iter=rfa_max_iter,
                            tol=rfa_tolerance,
                        )
                    elif aggregation == "median":
                        flat = [u for arr in grouped_updates.values() for u in arr]
                        client_update = aggregate_median(flat)
                    elif aggregation == "krum":
                        flat = [u for arr in grouped_updates.values() for u in arr]
                        client_update = aggregate_krum_proxy(flat)
                    else:
                        raise KeyError(f"unknown aggregation: {aggregation}")

                    blend_min = min(max(float(temporal_anchor_blend_min), 0.0), 1.0)
                    blend_max = min(max(float(temporal_anchor_blend_max), blend_min), 1.0)
                    mean_positive_root = accepted_root_mass / max(accepted_weight_mass, 1e-12)
                    anchor_blend = blend_max - (blend_max - blend_min) * min(max(mean_positive_root, 0.0), 1.0)
                    global_update = anchor_blend * server_update + (1.0 - anchor_blend) * client_update
                    aggregation_mode = f"temporal_rootguard_{aggregation}"
                    floor_diagnostics = list(floor_diagnostics) + [
                        {
                            "aggregation": trust_mode,
                            "accepted_count": int(accepted_count),
                            "accepted_root_mass": float(accepted_root_mass),
                            "accepted_weight_mass": float(accepted_weight_mass),
                            "anchor_blend": float(anchor_blend),
                        }
                    ]
                else:
                    global_update = server_update.copy()
                    aggregation_mode = "temporal_rootguard_server_fallback"
                    keep = {int(row["client_id"]): False for row in trust_rows}
                    for row in trust_rows:
                        row["selected_by_floor"] = False
                        row["kept_final"] = False
                    floor_diagnostics = list(floor_diagnostics) + [
                        {
                            "aggregation": trust_mode,
                            "accepted_count": 0,
                            "accepted_root_mass": 0.0,
                            "accepted_weight_mass": 0.0,
                            "anchor_blend": 1.0,
                            "fallback": "server_root_only",
                        }
                    ]

                for row in trust_rows:
                    cid = int(row["client_id"])
                    if not bool(row["trusted_anchor"]):
                        continue
                    temporal_reputation[cid] = float(row["trust_raw"])
                    temporal_weight_ema[cid] = float(
                        (temporal_history_decay * temporal_weight_ema.get(cid, float(row["soft_weight"])))
                        + ((1.0 - temporal_history_decay) * float(row["soft_weight"]))
                    )
                    temporal_update_ema[cid] = ema_blend(
                        temporal_update_ema.get(cid),
                        local_updates[cid],
                        decay=temporal_history_decay,
                    )
                    temporal_root_prob_ema[cid] = ema_blend(
                        temporal_root_prob_ema.get(cid),
                        root_prob_cache[cid],
                        decay=temporal_history_decay,
                    )
            else:
                for view in active_views:
                    cid = int(view["client_id"])
                    eval_row = client_eval[cid]
                    val_metrics = eval_row["val_metrics"]
                    similarity = 1.0 - float(
                        np.linalg.norm(local_updates[cid] - mean_update)
                        / max(np.linalg.norm(mean_update), 1e-6)
                    )
                    similarity = max(-1.0, min(1.0, similarity))
                    prev = prev_updates.get(cid)
                    stability = 1.0 if prev is None else 1.0 - float(
                        np.linalg.norm(local_updates[cid] - prev) / max(np.linalg.norm(prev), 1e-6)
                    )
                    stability = max(-1.0, min(1.0, stability))
                    trust_raw = compute_trust_score(
                        val_gain=val_metrics["f1"],
                        similarity=similarity,
                        stability=stability,
                        calibration_penalty=max(0.0, 1.0 - val_metrics["accuracy"]),
                        norm_penalty=min(1.0, update_norms[cid] / max(statistics.mean(update_norms.values()), 1e-6)),
                    )
                    trust_rows.append(
                        {
                            "round": round_id,
                            "client_id": cid,
                            "group": str(view["group_name"]),
                            "is_poisoned": bool(cid in poisoned_clients),
                            "owned_ip_count": len(view["owned_ip_indices"]),
                            "best_val_threshold": float(eval_row["threshold"]),
                            "trust_raw": trust_raw,
                            "val_f1": val_metrics["f1"],
                            "similarity": similarity,
                            "stability": stability,
                            "update_norm": update_norms[cid],
                        }
                    )
                    prev_updates[cid] = local_updates[cid].copy()

                trust_rows = normalize_scores(trust_rows)
                keep, floor_diagnostics = select_kept_clients(
                    trust_rows,
                    trust_threshold=trust_threshold,
                    min_keep_per_group=min_keep_per_group,
                    group_floor_policy=group_floor_policy,
                    group_floor_min_trust_mass=group_floor_min_trust_mass,
                )
                grouped_updates: dict[str, list[np.ndarray]] = {}
                grouped_weights: dict[str, list[float]] = {}
                for row in trust_rows:
                    cid = int(row["client_id"])
                    passed_threshold = float(row["trust_norm"]) >= float(trust_threshold)
                    row["passed_threshold"] = bool(passed_threshold)
                    row["selected_by_floor"] = bool(keep[cid] and not passed_threshold)
                    row["kept_final"] = bool(keep[cid])
                    if not keep[cid]:
                        continue
                    group_name = str(row["group"])
                    grouped_updates.setdefault(group_name, []).append(local_updates[cid])
                    grouped_weights.setdefault(group_name, []).append(max(float(row["trust_norm"]), 0.01))
                if not grouped_updates:
                    for row in trust_rows:
                        cid = int(row["client_id"])
                        group_name = str(row["group"])
                        grouped_updates.setdefault(group_name, []).append(local_updates[cid])
                        grouped_weights.setdefault(group_name, []).append(1.0)

                if aggregation == "hierarchical":
                    global_update, _ = aggregate_hierarchical(grouped_updates, grouped_weights)
                elif aggregation == "mean":
                    flat = [u for arr in grouped_updates.values() for u in arr]
                    w = [w for arr in grouped_weights.values() for w in arr]
                    global_update = aggregate_mean(flat, w)
                elif aggregation == "rfa":
                    flat = [u for arr in grouped_updates.values() for u in arr]
                    w = [w for arr in grouped_weights.values() for w in arr]
                    global_update = aggregate_rfa_geometric_median(
                        flat,
                        w,
                        max_iter=rfa_max_iter,
                        tol=rfa_tolerance,
                    )
                elif aggregation == "median":
                    flat = [u for arr in grouped_updates.values() for u in arr]
                    global_update = aggregate_median(flat)
                elif aggregation == "krum":
                    flat = [u for arr in grouped_updates.values() for u in arr]
                    global_update = aggregate_krum_proxy(flat)
                else:
                    raise KeyError(f"unknown aggregation: {aggregation}")

        for row in trust_rows:
            cid = int(row["client_id"])
            row.setdefault("passed_threshold", bool(keep[cid]))
            row.setdefault("selected_by_floor", False)
            row.setdefault("kept_final", bool(keep[cid]))
            keep[cid] = bool(row["kept_final"])

        prev_global_update = np.asarray(global_update, dtype=np.float64).copy()
        model.load_state_dict(numpy_to_state_like(model, base_state + global_update))
        th, val_metrics = find_best_threshold(model, x=x, edge_index=edge_index, y=y, mask=val_mask)
        model.eval()
        with torch.no_grad():
            test_logits = model(x, edge_index)
            test_probs = F.softmax(test_logits[test_mask], dim=1)[:, 1]
        test_metrics = evaluate_probs(probs=test_probs, y_true=y[test_mask], threshold=th)
        kept_client_ids = sorted(int(cid) for cid, is_kept in keep.items() if is_kept)
        round_rows.append(
            {
                "round": round_id,
                "val_f1": val_metrics["f1"],
                "test_f1": test_metrics["f1"],
                "test_recall": test_metrics["recall"],
                "test_fpr": test_metrics["fpr"],
                "kept_clients": int(len(kept_client_ids)),
                "kept_client_ids": kept_client_ids,
                "kept_groups": sorted({str(r["group"]) for r in trust_rows if keep[int(r["client_id"])]}),
                "kept_poisoned_clients": int(sum(1 for r in trust_rows if r["is_poisoned"] and keep[int(r["client_id"])])),
                "group_floor_diagnostics": floor_diagnostics,
                "aggregation_mode": aggregation_mode,
                "trust_weight_mass": float(sum(float(r["trust_norm"]) for r in trust_rows)),
            }
        )
        trust_trace.extend(trust_rows)

    summary = {
        "timestamp_utc": timestamp_utc(),
        "config": cfg,
        "graph_file": str(graph_file),
        "dataset_info": {
            "dataset_name": str(getattr(graph, "dataset_name", "") or ""),
            "dataset_variant": str(getattr(graph, "dataset_variant", "") or ""),
            "dataset_source": str(getattr(graph, "dataset_source", "") or ""),
            "split_scheme": str(getattr(graph, "split_scheme", "") or ""),
        },
        "graph_stats": {
            "num_nodes": int(graph.num_nodes),
            "num_edges": int(graph.num_edges),
            "flow_nodes": int(flow_mask.sum().item()),
            "train_nodes": int(train_mask.sum().item()),
            "val_nodes": int(val_mask.sum().item()),
            "test_nodes": int(test_mask.sum().item()),
        },
        "warmup": {
            "global_warmup_epochs": int(global_warmup_epochs),
        },
        "model_info": {
            "backbone": backbone,
        },
        "partition_info": {
            "partition_mode": partition_mode,
            "num_clients": int(num_clients),
            "active_clients": int(len(active_views)),
            "manifest_file": str(partition_manifest.get("manifest_file", "")),
            "topology_type": str(partition_manifest.get("topology_type", "")),
            "load_profile": str(partition_manifest.get("load_profile", "")),
            "bot_type_mode": str(partition_manifest.get("bot_type_mode", "")),
        },
        "poisoned_clients": summarize_poisoned_ids(poisoned_clients),
        "tuning_info": tuning_info,
        "trust_filter": {
            "trust_mode": trust_mode,
            "trust_threshold": float(trust_threshold),
            "min_keep_per_group": int(min_keep_per_group),
            "group_floor_policy": group_floor_policy,
            "group_floor_min_trust_mass": float(group_floor_min_trust_mass),
            "temporal_reputation_decay": float(temporal_reputation_decay),
            "temporal_history_decay": float(temporal_history_decay),
            "temporal_server_cosine_floor": float(temporal_server_cosine_floor),
            "temporal_root_drift_scale": float(temporal_root_drift_scale),
            "temporal_anchor_blend_min": float(temporal_anchor_blend_min),
            "temporal_anchor_blend_max": float(temporal_anchor_blend_max),
            "temporal_peer_topk": int(temporal_peer_topk),
            "temporal_use_layerwise": bool(temporal_use_layerwise),
            "temporal_use_behavioral_probe": bool(temporal_use_behavioral_probe),
            "temporal_use_soft_weighting": bool(temporal_use_soft_weighting),
            "temporal_behavior_probe_mix": float(temporal_behavior_probe_mix),
            "temporal_behavior_probe_scale": float(temporal_behavior_probe_scale),
            "temporal_soft_weight_power": float(temporal_soft_weight_power),
            "temporal_weight_floor": float(temporal_weight_floor),
            "temporal_hard_reject_floor": float(temporal_hard_reject_floor),
            "temporal_redemption_mix": float(temporal_redemption_mix),
            "temporal_camouflage_peer_threshold": float(temporal_camouflage_peer_threshold),
            "temporal_camouflage_server_cosine_max": float(temporal_camouflage_server_cosine_max),
            "temporal_camouflage_layerwise_max": float(temporal_camouflage_layerwise_max),
            "temporal_camouflage_similarity_threshold": float(temporal_camouflage_similarity_threshold),
            "temporal_camouflage_min_redundant_peers": int(temporal_camouflage_min_redundant_peers),
            "temporal_camouflage_cluster_server_cosine_max": float(temporal_camouflage_cluster_server_cosine_max),
            "temporal_score_weights": {str(k): float(v) for k, v in temporal_score_weights.items()},
        },
        "server_root": server_root_info,
        "comm_cost": {
            "tuning_mode": tuning_info["tuning_mode"],
            "bytes_per_client_per_round_est": int(tuning_info["trainable_params"]) * 4,
            "bytes_per_round_est": int(tuning_info["trainable_params"]) * 4 * int(len(active_views)),
            "total_bytes_est": int(tuning_info["trainable_params"]) * 4 * int(len(active_views)) * int(rounds),
        },
        "round_rows": round_rows,
        "final_metrics": round_rows[-1],
    }
    save_json(paths.run_dir / "summary.json", summary)
    save_json(paths.run_dir / "trust_trace.json", {"rows": trust_trace})
    save_json(paths.run_dir / "client_partition.json", partition_manifest)
    print(f"[OK] real fed pilot completed: {paths.run_dir}")


if __name__ == "__main__":
    main()
