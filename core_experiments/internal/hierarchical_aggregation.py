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


def aggregate_rfa_geometric_median(
    updates: Iterable[np.ndarray],
    weights: Iterable[float] | None = None,
    *,
    max_iter: int = 100,
    tol: float = 1e-6,
    eps: float = 1e-12,
) -> np.ndarray:
    stack = _stack(updates)
    if weights is None:
        base_weights = np.full(stack.shape[0], 1.0 / max(stack.shape[0], 1), dtype=np.float64)
    else:
        base_weights = np.asarray(list(weights), dtype=np.float64)
        if base_weights.shape[0] != stack.shape[0]:
            raise ValueError("weights length must match the number of updates")
        weight_sum = float(np.sum(base_weights))
        if weight_sum <= float(eps):
            raise ValueError("weights must contain positive mass")
        base_weights = base_weights / weight_sum

    estimate = aggregate_mean(stack, base_weights)
    for _ in range(max(int(max_iter), 1)):
        distances = np.linalg.norm(stack - estimate[None, :], axis=1)
        close_mask = distances <= float(eps)
        if np.any(close_mask):
            close_weights = base_weights[close_mask]
            close_weight_sum = float(np.sum(close_weights))
            if close_weight_sum > float(eps):
                return aggregate_mean(stack[close_mask], close_weights)
            return np.asarray(stack[np.where(close_mask)[0][0]], dtype=np.float64)
        reweighted = base_weights / np.maximum(distances, float(eps))
        reweighted = reweighted / max(float(np.sum(reweighted)), float(eps))
        updated = aggregate_mean(stack, reweighted)
        delta = float(np.linalg.norm(updated - estimate))
        estimate = updated
        if delta <= float(tol) * max(float(np.linalg.norm(estimate)), 1.0):
            break
    return np.asarray(estimate, dtype=np.float64)


def aggregate_centered_clipping(
    updates: Iterable[np.ndarray],
    weights: Iterable[float] | None = None,
    *,
    clip_radius: float | None = None,
    clip_ratio: float = 2.0,
    num_iterations: int = 10,
    initial_center: np.ndarray | None = None,
    eps: float = 1e-12,
) -> np.ndarray:
    stack = _stack(updates)
    if weights is None:
        base_weights = np.full(stack.shape[0], 1.0 / max(stack.shape[0], 1), dtype=np.float64)
    else:
        base_weights = np.asarray(list(weights), dtype=np.float64)
        if base_weights.shape[0] != stack.shape[0]:
            raise ValueError("weights length must match the number of updates")
        weight_sum = float(np.sum(base_weights))
        if weight_sum <= float(eps):
            raise ValueError("weights must contain positive mass")
        base_weights = base_weights / weight_sum
    if initial_center is None:
        center = np.zeros(stack.shape[1], dtype=np.float64)
    else:
        center = np.asarray(initial_center, dtype=np.float64).reshape(-1)
        if center.shape[0] != stack.shape[1]:
            raise ValueError("initial_center shape must match update dimension")

    if clip_radius is None or clip_radius <= 0.0:
        norms = np.linalg.norm(stack - center[None, :], axis=1)
        nonzero = norms[norms > float(eps)]
        base_radius = float(np.median(nonzero)) if nonzero.size > 0 else 0.0
        if base_radius <= float(eps):
            base_radius = float(np.mean(norms)) if norms.size > 0 else 0.0
        if base_radius <= float(eps):
            base_radius = 1.0
        clip_radius = max(base_radius * max(float(clip_ratio), float(eps)), float(eps))

    for _ in range(max(int(num_iterations), 1)):
        residuals = stack - center[None, :]
        norms = np.linalg.norm(residuals, axis=1)
        scales = np.minimum(1.0, float(clip_radius) / np.maximum(norms, float(eps)))
        clipped_mean = np.tensordot(base_weights, residuals * scales[:, None], axes=1)
        updated = center + clipped_mean
        delta = float(np.linalg.norm(updated - center))
        center = updated
        if delta <= 1e-6 * max(float(np.linalg.norm(center)), 1.0):
            break
    return np.asarray(center, dtype=np.float64)


def aggregate_caf(
    updates: Iterable[np.ndarray],
    weights: Iterable[float] | None = None,
    *,
    f: int = 0,
    max_iter: int | None = None,
    power_max_iter: int = 1,
    eps: float = 1e-12,
) -> np.ndarray:
    stack = _stack(updates)
    num_updates, dim = stack.shape
    if num_updates <= 1:
        return np.asarray(stack[0], dtype=np.float64)

    faulty = min(max(int(f), 0), max(num_updates - 1, 0))
    if weights is None:
        coeffs = np.ones(num_updates, dtype=np.float64)
    else:
        base_weights = np.asarray(list(weights), dtype=np.float64)
        if base_weights.shape[0] != num_updates:
            raise ValueError("weights length must match the number of updates")
        weight_sum = float(np.sum(base_weights))
        if weight_sum <= float(eps):
            raise ValueError("weights must contain positive mass")
        coeffs = (float(num_updates) * base_weights) / weight_sum

    total_mass = float(np.sum(coeffs))
    target_mass = max(float(num_updates - 2 * faulty), float(eps))
    if total_mass <= target_mass + float(eps):
        return aggregate_mean(stack, coeffs)

    max_rounds = int(max_iter) if max_iter is not None else int(num_updates)
    max_rounds = max(max_rounds, 1)
    best_agg = aggregate_mean(stack, coeffs)
    best_lambda = float("inf")

    for _ in range(max_rounds):
        total_mass = float(np.sum(coeffs))
        if total_mass <= target_mass + float(eps):
            break

        mean = aggregate_mean(stack, coeffs)
        centered = stack - mean[None, :]
        centered_norms = np.linalg.norm(centered, axis=1)
        start_idx = int(np.argmax(centered_norms))
        start_vec = np.asarray(centered[start_idx], dtype=np.float64)
        start_norm = float(np.linalg.norm(start_vec))
        if start_norm <= float(eps):
            break
        direction = start_vec / start_norm

        for _ in range(max(int(power_max_iter), 1)):
            projection = centered @ direction
            next_direction = centered.T @ (coeffs * projection)
            next_norm = float(np.linalg.norm(next_direction))
            if next_norm <= float(eps):
                break
            direction = next_direction / next_norm

        projection = centered @ direction
        cov_direction = centered.T @ (coeffs * projection) / max(total_mass, float(eps))
        leading_value = float(direction @ cov_direction)
        if leading_value < best_lambda:
            best_lambda = leading_value
            best_agg = np.asarray(mean, dtype=np.float64)

        scores = np.square(projection)
        worst_idx = int(np.argmax(scores))
        remove_mass = min(float(coeffs[worst_idx]), total_mass - target_mass)
        if remove_mass <= float(eps):
            break
        coeffs[worst_idx] = max(float(coeffs[worst_idx] - remove_mass), 0.0)

    return np.asarray(best_agg, dtype=np.float64)


def preaggregate_arc(
    updates: Iterable[np.ndarray],
    *,
    f: int = 0,
    eps: float = 1e-12,
) -> tuple[np.ndarray, dict[str, object]]:
    stack = _stack(updates)
    num_updates = int(stack.shape[0])
    faulty = int(max(f, 0))
    if faulty >= num_updates + 1:
        raise ValueError(f"f must be smaller than len(vectors)+1, but got f={faulty} and len(vectors)={num_updates}")

    norms = np.linalg.norm(stack, axis=1)
    order = np.argsort(norms)
    num_clipped = int((2 * faulty / max(num_updates, 1)) * (num_updates - faulty))
    cut_off = max(num_updates - num_clipped, 1)
    clipping_threshold = float(norms[order[cut_off - 1]]) if num_updates > 0 else 0.0
    clipped_indices = [int(idx) for idx in order[cut_off:]]

    out = np.asarray(stack, dtype=np.float64).copy()
    for idx in clipped_indices:
        norm = float(norms[idx])
        if norm > max(clipping_threshold, float(eps)):
            out[idx] *= clipping_threshold / norm

    diagnostics: dict[str, object] = {
        "faulty_budget": int(faulty),
        "num_updates": int(num_updates),
        "num_clipped": int(len(clipped_indices)),
        "clipping_threshold": float(clipping_threshold),
        "original_norms": [float(x) for x in norms.tolist()],
        "clipped_norms": [float(x) for x in np.linalg.norm(out, axis=1).tolist()],
        "clipped_indices": clipped_indices,
    }
    return out, diagnostics


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
