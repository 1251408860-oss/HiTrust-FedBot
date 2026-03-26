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
from hierarchical_aggregation import aggregate_hierarchical, aggregate_krum_proxy, aggregate_mean, aggregate_median
from hitrust_common import resolve_suite_paths, save_json, timestamp_utc
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

    graph_file = Path(str(cfg["graph_file"]))
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
    trust_threshold = float(cfg.get("trust_threshold", 0.35))
    min_keep_per_group = int(cfg.get("min_keep_per_group", 0))
    group_floor_policy = str(cfg.get("group_floor_policy", "static"))
    group_floor_min_trust_mass = float(cfg.get("group_floor_min_trust_mass", 0.0))
    num_groups = int(cfg.get("num_groups", 3))
    tuning_mode = str(cfg.get("tuning_mode", "adapter_ft"))
    global_warmup_epochs = int(cfg.get("global_warmup_epochs", 8))
    backbone = str(cfg.get("backbone", "feature_mlp"))

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

    for round_id in range(1, rounds + 1):
        base_state = state_to_numpy(model)
        local_updates: dict[int, np.ndarray] = {}
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
            if cid in poisoned_clients:
                update = apply_attack(update, attack_type=poison_type, attack_scale=poison_scale, rng=rng)
            local_updates[cid] = update
            local_models[cid] = trained

        if not local_updates:
            raise RuntimeError("no local updates were produced")

        mean_update = aggregate_mean(local_updates.values())
        update_norms = {cid: float(np.linalg.norm(upd)) for cid, upd in local_updates.items()}
        trust_rows: list[dict[str, Any]] = []
        for view in active_views:
            cid = int(view["client_id"])
            local_model = local_models[cid]
            local_state = numpy_to_state_like(model, base_state + local_updates[cid])
            local_model.load_state_dict(local_state)
            threshold, val_metrics = find_best_threshold(local_model, x=x, edge_index=edge_index, y=y, mask=val_mask)
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
                    "best_val_threshold": threshold,
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
        for row in trust_rows:
            cid = int(row["client_id"])
            passed_threshold = float(row["trust_norm"]) >= float(trust_threshold)
            row["passed_threshold"] = bool(passed_threshold)
            row["selected_by_floor"] = bool(keep[cid] and not passed_threshold)
            row["kept_final"] = bool(keep[cid])
        grouped_updates: dict[str, list[np.ndarray]] = {}
        grouped_weights: dict[str, list[float]] = {}
        for row in trust_rows:
            cid = int(row["client_id"])
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
        elif aggregation == "median":
            flat = [u for arr in grouped_updates.values() for u in arr]
            global_update = aggregate_median(flat)
        elif aggregation == "krum":
            flat = [u for arr in grouped_updates.values() for u in arr]
            global_update = aggregate_krum_proxy(flat)
        else:
            raise KeyError(f"unknown aggregation: {aggregation}")

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
            "trust_threshold": float(trust_threshold),
            "min_keep_per_group": int(min_keep_per_group),
            "group_floor_policy": group_floor_policy,
            "group_floor_min_trust_mass": float(group_floor_min_trust_mass),
        },
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
