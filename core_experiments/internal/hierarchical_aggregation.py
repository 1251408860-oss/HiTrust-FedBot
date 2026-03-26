#!/usr/bin/env python3
from __future__ import annotations

from typing import Iterable

import numpy as np


def _stack(updates: Iterable[np.ndarray]) -> np.ndarray:
    arr = [np.asarray(u, dtype=np.float64) for u in updates]
    if not arr:
        raise ValueError("no updates to aggregate")
    return np.stack(arr, axis=0)


def aggregate_mean(updates: Iterable[np.ndarray], weights: Iterable[float] | None = None) -> np.ndarray:
    stack = _stack(updates)
    if weights is None:
        return np.mean(stack, axis=0)
    w = np.asarray(list(weights), dtype=np.float64)
    w = w / max(np.sum(w), 1e-12)
    return np.tensordot(w, stack, axes=1)


def aggregate_median(updates: Iterable[np.ndarray]) -> np.ndarray:
    stack = _stack(updates)
    return np.median(stack, axis=0)


def aggregate_krum_proxy(updates: Iterable[np.ndarray]) -> np.ndarray:
    stack = _stack(updates)
    dists = np.zeros(stack.shape[0], dtype=np.float64)
    for i in range(stack.shape[0]):
        for j in range(stack.shape[0]):
            if i == j:
                continue
            dists[i] += float(np.linalg.norm(stack[i] - stack[j]))
    return stack[int(np.argmin(dists))]


def aggregate_hierarchical(
    grouped_updates: dict[str, list[np.ndarray]],
    grouped_weights: dict[str, list[float]] | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    group_results: dict[str, np.ndarray] = {}
    for group_name, updates in grouped_updates.items():
        weights = None if grouped_weights is None else grouped_weights.get(group_name)
        group_results[group_name] = aggregate_mean(updates, weights)
    final = aggregate_mean(group_results.values())
    return final, group_results
