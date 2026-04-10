#!/usr/bin/env python3
from __future__ import annotations

from typing import Iterable

import numpy as np

METRIC_DIRECTIONS = {
    "test_f1": "higher_is_better",
    "test_recall": "higher_is_better",
    "test_fpr": "lower_is_better",
    "kept_poisoned_clients": "lower_is_better",
    "kept_clients": "higher_is_better",
}


def metric_direction(metric: str) -> str:
    return str(METRIC_DIRECTIONS.get(str(metric), "higher_is_better"))


def aligned_pairs(reference: dict[str, float], candidate: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    keys = sorted(set(reference) & set(candidate), key=lambda x: (len(str(x)), str(x)))
    if not keys:
        return np.asarray([], dtype=np.float64), np.asarray([], dtype=np.float64)
    ref = np.asarray([float(reference[k]) for k in keys], dtype=np.float64)
    cand = np.asarray([float(candidate[k]) for k in keys], dtype=np.float64)
    return ref, cand


def paired_mean_diff(reference: dict[str, float], candidate: dict[str, float]) -> float | None:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size <= 0:
        return None
    return float(np.mean(cand - ref))


def paired_effect_size_dz(reference: dict[str, float], candidate: dict[str, float]) -> float | None:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size < 2:
        return None
    diff = (cand - ref).astype(np.float64, copy=False)
    std = float(np.std(diff, ddof=1))
    if std <= 1e-12:
        return None
    return float(np.mean(diff) / std)


def holm_bonferroni(p_values: Iterable[float | None]) -> list[float | None]:
    values = list(p_values)
    indexed = [(idx, float(value)) for idx, value in enumerate(values) if value is not None]
    if not indexed:
        return [None for _ in values]
    m = len(indexed)
    ranked = sorted(indexed, key=lambda item: item[1])
    corrected: dict[int, float] = {}
    running = 0.0
    for order, (idx, value) in enumerate(ranked, start=1):
        adjusted = min(1.0, value * (m - order + 1))
        running = max(running, adjusted)
        corrected[idx] = min(max(running, 0.0), 1.0)
    return [corrected.get(idx) for idx in range(len(values))]


def correct_p_values(p_values: Iterable[float | None], method: str) -> list[float | None]:
    values = list(p_values)
    if str(method) == "holm_bonferroni":
        return holm_bonferroni(values)
    if str(method) == "bh_fdr":
        return benjamini_hochberg(values)
    raise KeyError(f"unknown p-value correction method: {method}")


def benjamini_hochberg(p_values: list[float | None]) -> list[float | None]:
    indexed = [(idx, float(value)) for idx, value in enumerate(p_values) if value is not None]
    if not indexed:
        return [None for _ in p_values]
    m = len(indexed)
    ranked = sorted(indexed, key=lambda item: item[1], reverse=True)
    running = 1.0
    corrected: dict[int, float] = {}
    for reverse_rank, (idx, value) in enumerate(ranked, start=1):
        rank = m - reverse_rank + 1
        adjusted = min(running, value * m / max(rank, 1))
        running = adjusted
        corrected[idx] = min(max(adjusted, 0.0), 1.0)
    return [corrected.get(idx) for idx in range(len(p_values))]
