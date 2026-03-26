#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import numpy as np


def build_partition_audit(
    *,
    num_clients: int,
    partition_mode: str,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, Any]] = []
    sizes = []
    ratios = []

    for cid in range(int(num_clients)):
        base = 800 if partition_mode == "iid_lite" else 650
        spread = 60 if partition_mode == "iid_lite" else 220
        train_nodes = int(max(120, base + rng.integers(-spread, spread + 1)))
        benign = int(max(20, train_nodes * rng.uniform(0.20, 0.55)))
        attack = int(max(20, train_nodes - benign))
        delay_ms = float(rng.choice([5.0, 8.0, 12.0, 15.0]))
        bw_mbps = float(rng.choice([4.0, 6.0, 8.0, 10.0, 12.0]))

        row = {
            "client_id": cid,
            "partition_mode": partition_mode,
            "train_nodes": train_nodes,
            "benign": benign,
            "attack": attack,
            "attack_ratio": float(attack / max(train_nodes, 1)),
            "mean_delay_ms": delay_ms,
            "mean_bw_mbps": bw_mbps,
        }
        rows.append(row)
        sizes.append(float(train_nodes))
        ratios.append(float(row["attack_ratio"]))

    size_mean = float(np.mean(sizes)) if sizes else 0.0
    size_cv = float(np.std(sizes) / size_mean) if size_mean > 0 else 0.0
    ratio_std = float(np.std(ratios)) if ratios else 0.0

    return {
        "partition_mode": partition_mode,
        "num_clients": int(num_clients),
        "seed": int(seed),
        "clients": rows,
        "train_size_cv": size_cv,
        "attack_ratio_std": ratio_std,
    }


def _parse_delay_ms(value: str) -> float:
    text = str(value).strip().lower()
    if text.endswith("ms"):
        text = text[:-2]
    try:
        return float(text)
    except Exception:
        return 0.0


def build_partition_audit_from_scenario_index(
    *,
    scenario_index: dict[str, Any],
    num_clients: int,
    partition_mode: str,
    seed: int,
) -> dict[str, Any]:
    rows = list(scenario_index.get("rows", []))
    if not rows:
        raise ValueError("scenario index has no rows")

    rng = np.random.default_rng(int(seed))
    clients: list[dict[str, Any]] = []
    sizes = []
    ratios = []

    by_topology: dict[str, list[dict[str, Any]]] = {}
    by_load: dict[str, list[dict[str, Any]]] = {}
    by_attack: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_topology.setdefault(str(row.get("topology_type", "unknown")), []).append(row)
        by_load.setdefault(str(row.get("load_profile", "unknown")), []).append(row)
        by_attack.setdefault(str(row.get("bot_type_mode", "unknown")), []).append(row)

    topology_keys = sorted(by_topology)
    load_keys = sorted(by_load)
    attack_keys = sorted(by_attack)

    for cid in range(int(num_clients)):
        if partition_mode == "topology_noniid":
            key = topology_keys[cid % len(topology_keys)]
            pool = by_topology[key]
        elif partition_mode == "load_noniid":
            key = load_keys[cid % len(load_keys)]
            pool = by_load[key]
        elif partition_mode == "attack_noniid":
            key = attack_keys[cid % len(attack_keys)]
            pool = by_attack[key]
        else:
            key = "mixed"
            pool = rows

        picked = pool[cid % len(pool)]
        users = int(picked.get("users", 0))
        bots = int(picked.get("bots", 0))
        base_nodes = max(users + bots, 1) * int(rng.integers(18, 34))
        train_nodes = int(base_nodes + rng.integers(-50, 51))
        benign = int(max(20, train_nodes * (users / max(users + bots, 1))))
        attack = int(max(20, train_nodes - benign))

        client = {
            "client_id": cid,
            "partition_mode": partition_mode,
            "group_key": key,
            "source_scenario": str(picked.get("scenario_name", "")),
            "train_nodes": train_nodes,
            "benign": benign,
            "attack": attack,
            "attack_ratio": float(attack / max(train_nodes, 1)),
            "mean_delay_ms": _parse_delay_ms(str(picked.get("delay", ""))),
            "mean_bw_mbps": float(picked.get("core_bw_mbps", 0.0)),
            "load_profile": str(picked.get("load_profile", "")),
            "topology_type": str(picked.get("topology_type", "")),
        }
        clients.append(client)
        sizes.append(float(train_nodes))
        ratios.append(float(client["attack_ratio"]))

    size_mean = float(np.mean(sizes)) if sizes else 0.0
    size_cv = float(np.std(sizes) / size_mean) if size_mean > 0 else 0.0
    ratio_std = float(np.std(ratios)) if ratios else 0.0

    return {
        "partition_mode": partition_mode,
        "num_clients": int(num_clients),
        "seed": int(seed),
        "source_num_scenarios": int(scenario_index.get("num_scenarios", len(rows))),
        "clients": clients,
        "train_size_cv": size_cv,
        "attack_ratio_std": ratio_std,
    }
