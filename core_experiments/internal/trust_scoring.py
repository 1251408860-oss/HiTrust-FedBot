#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def compute_trust_score(
    *,
    val_gain: float,
    similarity: float,
    stability: float,
    calibration_penalty: float,
    norm_penalty: float,
    weights: dict[str, float] | None = None,
) -> float:
    cfg = {
        "val_gain": 0.45,
        "similarity": 0.25,
        "stability": 0.20,
        "calibration_penalty": 0.05,
        "norm_penalty": 0.05,
    }
    if weights:
        cfg.update(weights)
    score = (
        cfg["val_gain"] * float(val_gain)
        + cfg["similarity"] * float(similarity)
        + cfg["stability"] * float(stability)
        - cfg["calibration_penalty"] * float(calibration_penalty)
        - cfg["norm_penalty"] * float(norm_penalty)
    )
    return float(score)


def normalize_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return rows
    vals = [float(r["trust_raw"]) for r in rows]
    lo = min(vals)
    hi = max(vals)
    span = max(hi - lo, 1e-12)
    out = []
    for row in rows:
        item = dict(row)
        item["trust_norm"] = float((float(item["trust_raw"]) - lo) / span)
        out.append(item)
    return out
