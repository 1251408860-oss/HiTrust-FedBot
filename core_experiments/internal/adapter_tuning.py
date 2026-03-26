#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TuningMode:
    name: str
    trainable_ratio: float
    comm_multiplier: float


TUNING_MODES = {
    "head_only": TuningMode(name="head_only", trainable_ratio=0.03, comm_multiplier=0.08),
    "adapter_ft": TuningMode(name="adapter_ft", trainable_ratio=0.12, comm_multiplier=0.20),
    "full_ft": TuningMode(name="full_ft", trainable_ratio=1.00, comm_multiplier=1.00),
}


def resolve_tuning_mode(name: str) -> TuningMode:
    if name not in TUNING_MODES:
        raise KeyError(f"unknown tuning mode: {name}")
    return TUNING_MODES[name]
