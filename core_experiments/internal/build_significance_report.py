#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from stats_contract import aligned_pairs, correct_p_values, paired_effect_size_dz


def mean_std(values: list[float]) -> dict[str, float]:
    if not values:
        return {"n": 0, "mean": 0.0, "std": 0.0}
    if len(values) == 1:
        return {"n": 1, "mean": values[0], "std": 0.0}
    return {"n": len(values), "mean": statistics.mean(values), "std": statistics.stdev(values)}


def parse_group_specs(text: str) -> list[tuple[str, str]]:
    out = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, prefix = item.split("=", 1)
        out.append((label.strip(), prefix.strip()))
    return out


def paired_sign_flip_p_value(reference: dict[str, float], candidate: dict[str, float]) -> float | None:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size <= 0:
        return None
    diff = (cand - ref)
    diff = diff[abs(diff) > 1e-12]
    if diff.size <= 0:
        return 1.0
    observed = abs(float(diff.mean()))
    if diff.size <= 18:
        total = 1 << int(diff.size)
        extreme = 0
        for mask in range(total):
            signed = diff.copy()
            for bit in range(diff.size):
                if (mask >> bit) & 1:
                    signed[bit] *= -1.0
            if abs(float(signed.mean())) + 1e-12 >= observed:
                extreme += 1
        return float(extreme / total)
    return None


def load_metric_values(runs_root: Path, prefix: str, metric: str) -> tuple[list[float], dict[str, float]]:
    values: list[float] = []
    seed_map: dict[str, float] = {}
    for summary_file in sorted(runs_root.glob(f"{prefix}_seed*/summary.json")):
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        value = float(obj["final_metrics"][metric])
        values.append(value)
        seed_token = summary_file.parent.name.rsplit("_seed", 1)[-1]
        seed_map[str(seed_token)] = value
    return values, seed_map


def main() -> None:
    p = argparse.ArgumentParser(description="Build a paired significance report over seed sweeps")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--group-specs", required=True, help="CSV of label=run_prefix")
    p.add_argument("--reference", required=True)
    p.add_argument("--metric", default="test_f1")
    p.add_argument("--output-file", required=True)
    p.add_argument("--correction-method", default="holm_bonferroni", choices=["holm_bonferroni", "bh_fdr"])
    args = p.parse_args()

    runs_root = Path(args.runs_root).resolve()
    groups = parse_group_specs(args.group_specs)
    values_by_label: dict[str, list[float]] = {}
    seed_maps_by_label: dict[str, dict[str, float]] = {}
    for label, prefix in groups:
        values, seed_map = load_metric_values(runs_root, prefix, args.metric)
        values_by_label[label] = values
        seed_maps_by_label[label] = seed_map
    if args.reference not in values_by_label:
        raise KeyError(f"reference label not found: {args.reference}")
    ref_map = seed_maps_by_label[args.reference]

    rows: list[dict[str, Any]] = []
    pending: list[float] = []
    pending_idx: list[int] = []
    for idx, (label, _prefix) in enumerate(groups):
        vals = values_by_label[label]
        row = {"label": label, args.metric: mean_std(vals)}
        if label == args.reference:
            row["paired_sign_flip_p_value_vs_reference"] = None
            row["paired_sign_flip_p_value_corrected_vs_reference"] = None
            row["effect_size_dz_vs_reference"] = None
            row["paired_n_vs_reference"] = None
        else:
            cand_map = seed_maps_by_label[label]
            ref_vals, cand_vals = aligned_pairs(ref_map, cand_map)
            raw_p = paired_sign_flip_p_value(ref_map, cand_map)
            row["paired_sign_flip_p_value_vs_reference"] = raw_p
            row["paired_sign_flip_p_value_corrected_vs_reference"] = None
            row["effect_size_dz_vs_reference"] = paired_effect_size_dz(ref_map, cand_map)
            row["paired_n_vs_reference"] = int(min(ref_vals.size, cand_vals.size))
            if raw_p is not None:
                pending.append(float(raw_p))
                pending_idx.append(idx)
        rows.append(row)

    corrected = correct_p_values(pending, str(args.correction_method)) if pending else []
    for row_idx, corrected_p in zip(pending_idx, corrected):
        rows[row_idx]["paired_sign_flip_p_value_corrected_vs_reference"] = corrected_p

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(
            {
                "metric": args.metric,
                "reference": args.reference,
                "correction_method": str(args.correction_method),
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
