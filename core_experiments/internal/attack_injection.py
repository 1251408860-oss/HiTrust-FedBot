#!/usr/bin/env python3
from __future__ import annotations

from typing import Iterable

import numpy as np


def apply_attack(
    update: np.ndarray,
    *,
    attack_type: str,
    attack_scale: float,
    rng: np.random.Generator,
) -> np.ndarray:
    out = np.asarray(update, dtype=np.float64).copy()
    scale = float(max(0.0, attack_scale))

    if attack_type == "none":
        return out
    if attack_type == "update_noise":
        return out + rng.normal(0.0, scale, size=out.shape)
    if attack_type == "sign_flip":
        return -out * max(scale, 1.0)
    if attack_type == "model_scaling":
        return out * (1.0 + max(scale, 0.1) * 5.0)
    if attack_type == "clean_label_camouflage":
        return out * (1.0 - min(scale, 0.9))
    if attack_type == "feature_camouflage":
        return np.roll(out, 1) * max(scale, 0.5)
    raise KeyError(f"unknown attack type: {attack_type}")


def mark_poisoned_clients(
    num_clients: int,
    poison_frac: float,
    *,
    rng: np.random.Generator | None = None,
    seed: int | None = None,
    candidate_ids: Iterable[int] | None = None,
) -> set[int]:
    if candidate_ids is None:
        pool = list(range(int(num_clients)))
    else:
        pool = sorted({int(x) for x in candidate_ids if 0 <= int(x) < int(num_clients)})
    n = int(round(float(poison_frac) * len(pool)))
    n = max(0, min(n, len(pool)))
    if n == 0 or not pool:
        return set()
    if rng is None:
        rng = np.random.default_rng(0 if seed is None else int(seed))
    picked = rng.choice(np.asarray(pool, dtype=np.int64), size=n, replace=False)
    return {int(x) for x in picked.tolist()}


def summarize_poisoned_ids(client_ids: Iterable[int]) -> list[int]:
    return sorted(int(x) for x in client_ids)
