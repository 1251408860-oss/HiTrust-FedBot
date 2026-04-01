#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

METRICS = [
    ("test_f1", "F1"),
    ("test_fpr", "FPR"),
    ("kept_poisoned_clients", "Retained Poisoned"),
    ("kept_clients", "Retained Clients"),
]
SEED_PATTERN = re.compile(r"_seed(\d+)$")


def parse_specs(text: str) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, path = item.split("=", 1)
        out.append((label.strip(), Path(path).resolve()))
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_seed_key(run_name: str, fallback_index: int) -> str:
    match = SEED_PATTERN.search(str(run_name))
    if match:
        return str(match.group(1))
    return f"row_{fallback_index}"


def metric_values(obj: dict[str, Any], metric: str) -> list[float]:
    return [float(row.get(metric, 0.0)) for row in obj.get("rows", [])]


def stable_seed(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    acc = 0
    for idx, ch in enumerate(text.encode("utf-8"), start=1):
        acc = (acc + idx * int(ch)) % (2**31 - 1)
    return int(acc or 1)


def metric_seed_map(obj: dict[str, Any], metric: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for idx, row in enumerate(obj.get("rows", [])):
        seed_key = extract_seed_key(str(row.get("run_name", "")), idx)
        out[seed_key] = float(row.get(metric, 0.0))
    return out


def bootstrap_mean_ci(values: list[float], seed: int, num_bootstrap: int = 5000) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size <= 0:
        return 0.0, 0.0
    if arr.size == 1:
        val = float(arr[0])
        return val, val
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, arr.size, size=(int(num_bootstrap), int(arr.size)))
    boot = arr[idx].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return float(lo), float(hi)


def aligned_pairs(reference: dict[str, float], candidate: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    keys = sorted(set(reference) & set(candidate), key=lambda x: (len(str(x)), str(x)))
    if not keys:
        return np.asarray([], dtype=np.float64), np.asarray([], dtype=np.float64)
    ref = np.asarray([float(reference[k]) for k in keys], dtype=np.float64)
    cand = np.asarray([float(candidate[k]) for k in keys], dtype=np.float64)
    return ref, cand


def bootstrap_paired_diff_ci(
    reference: dict[str, float],
    candidate: dict[str, float],
    seed: int,
    num_bootstrap: int = 5000,
) -> tuple[float | None, float | None, float | None]:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size <= 0:
        return None, None, None
    diff = cand - ref
    observed = float(np.mean(diff))
    if diff.size == 1:
        return observed, observed, observed
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, diff.size, size=(int(num_bootstrap), int(diff.size)))
    boot = diff[idx].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return observed, float(lo), float(hi)


def paired_sign_flip_p_value(reference: dict[str, float], candidate: dict[str, float]) -> float | None:
    ref, cand = aligned_pairs(reference, candidate)
    if ref.size <= 0:
        return None
    diff = (cand - ref).astype(np.float64, copy=False)
    diff = diff[np.abs(diff) > 1e-12]
    if diff.size <= 0:
        return 1.0
    observed = float(abs(np.mean(diff)))
    if diff.size <= 18:
        total = 1 << int(diff.size)
        extreme = 0
        for mask in range(total):
            signs = np.ones(diff.size, dtype=np.float64)
            for bit in range(diff.size):
                if (mask >> bit) & 1:
                    signs[bit] = -1.0
            stat = float(abs(np.mean(signs * diff)))
            if stat + 1e-12 >= observed:
                extreme += 1
        return float(extreme / total)
    rng = np.random.default_rng(20260331)
    signs = rng.choice(np.asarray([-1.0, 1.0], dtype=np.float64), size=(50000, diff.size))
    boot = np.abs((signs * diff[None, :]).mean(axis=1))
    return float(np.mean(boot + 1e-12 >= observed))


def build_rows(specs: list[tuple[str, Path]], reference: str) -> list[dict[str, Any]]:
    objects = {label: load_json(path) for label, path in specs}
    ref_obj = objects[reference]
    ref_maps = {metric: metric_seed_map(ref_obj, metric) for metric, _ in METRICS}
    ref_f1_map = metric_seed_map(ref_obj, "test_f1")
    rows: list[dict[str, Any]] = []

    for label, path in specs:
        obj = objects[label]
        row: dict[str, Any] = {
            "label": label,
            "source_file": str(path),
            "n": int(obj["stats"]["test_f1"]["n"]),
        }
        method_maps = {metric: metric_seed_map(obj, metric) for metric, _ in METRICS}

        for metric, _metric_title in METRICS:
            values = metric_values(obj, metric)
            stats_obj = obj["stats"].get(metric, {"mean": 0.0, "std": 0.0, "n": len(values)})
            ci_low, ci_high = bootstrap_mean_ci(values, seed=stable_seed(label, metric))
            row[f"{metric}_mean"] = float(stats_obj.get("mean", 0.0))
            row[f"{metric}_std"] = float(stats_obj.get("std", 0.0))
            row[f"{metric}_ci95_low"] = float(ci_low)
            row[f"{metric}_ci95_high"] = float(ci_high)
            if label == reference:
                row[f"{metric}_paired_p_value_vs_reference"] = None
                row[f"{metric}_delta_mean_vs_reference"] = None
                row[f"{metric}_delta_ci95_low_vs_reference"] = None
                row[f"{metric}_delta_ci95_high_vs_reference"] = None
                row[f"{metric}_paired_n_vs_reference"] = None
            else:
                delta_mean, delta_low, delta_high = bootstrap_paired_diff_ci(
                    ref_maps[metric],
                    method_maps[metric],
                    seed=stable_seed(reference, label, metric),
                )
                ref_vals, cand_vals = aligned_pairs(ref_maps[metric], method_maps[metric])
                row[f"{metric}_paired_p_value_vs_reference"] = paired_sign_flip_p_value(
                    ref_maps[metric],
                    method_maps[metric],
                )
                row[f"{metric}_delta_mean_vs_reference"] = delta_mean
                row[f"{metric}_delta_ci95_low_vs_reference"] = delta_low
                row[f"{metric}_delta_ci95_high_vs_reference"] = delta_high
                row[f"{metric}_paired_n_vs_reference"] = int(min(ref_vals.size, cand_vals.size))

        if label == reference:
            row["f1_p_value_vs_reference"] = None
            row["f1_t_stat_vs_reference"] = None
            row["test_f1_paired_ttest_p_value_vs_reference"] = None
            row["test_f1_paired_ttest_t_stat_vs_reference"] = None
        else:
            ref_f1, cand_f1 = aligned_pairs(ref_f1_map, method_maps["test_f1"])
            if ref_f1.size >= 2 and cand_f1.size >= 2:
                t_stat, p_value = stats.ttest_rel(cand_f1, ref_f1)
                row["f1_p_value_vs_reference"] = float(p_value)
                row["f1_t_stat_vs_reference"] = float(t_stat)
                row["test_f1_paired_ttest_p_value_vs_reference"] = float(p_value)
                row["test_f1_paired_ttest_t_stat_vs_reference"] = float(t_stat)
            else:
                row["f1_p_value_vs_reference"] = None
                row["f1_t_stat_vs_reference"] = None
                row["test_f1_paired_ttest_p_value_vs_reference"] = None
                row["test_f1_paired_ttest_t_stat_vs_reference"] = None
        rows.append(row)
    return rows


def metric_error_bars(rows: list[dict[str, Any]], metric: str) -> np.ndarray:
    means = np.asarray([float(row[f"{metric}_mean"]) for row in rows], dtype=np.float64)
    lows = np.asarray([float(row[f"{metric}_ci95_low"]) for row in rows], dtype=np.float64)
    highs = np.asarray([float(row[f"{metric}_ci95_high"]) for row in rows], dtype=np.float64)
    lower = np.maximum(means - lows, 0.0)
    upper = np.maximum(highs - means, 0.0)
    return np.vstack([lower, upper])


def plot_rows(
    rows: list[dict[str, Any]],
    output_file: Path,
    title_prefix: str,
    include_kept_clients: bool = False,
) -> None:
    labels = [str(row["label"]) for row in rows]
    x = np.arange(len(labels))
    width = 0.7
    metrics = ["test_f1", "test_fpr", "kept_poisoned_clients"]
    if include_kept_clients:
        metrics.append("kept_clients")
    panel_titles = {
        "test_f1": "F1",
        "test_fpr": "FPR",
        "kept_poisoned_clients": "Retained Poisoned",
        "kept_clients": "Retained Clients",
    }
    fig, axes = plt.subplots(1, len(metrics), figsize=(4.4 * len(metrics), 4.2))
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        means = [float(row[f"{metric}_mean"]) for row in rows]
        yerr = metric_error_bars(rows, metric)
        ax.bar(x, means, width, yerr=yerr, capsize=4)
        ax.set_xticks(x, labels, rotation=15)
        ax.set_title(f"{title_prefix} {panel_titles[metric]}")
        ax.grid(axis="y", alpha=0.25)
        if metric == "test_f1":
            ax.set_ylim(0.0, 1.05)
        else:
            highs = [float(row[f"{metric}_ci95_high"]) for row in rows]
            upper = max(highs + [0.1])
            margin = 0.05 if metric == "test_fpr" else 0.5
            ax.set_ylim(0.0, upper + margin)

    fig.tight_layout()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=220)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Build a multi-method comparison report from seed stats files")
    p.add_argument("--method-specs", required=True, help="CSV label=/path/to/seed_stats.json")
    p.add_argument("--reference", required=True)
    p.add_argument("--title-prefix", default="Method Comparison")
    p.add_argument("--output-table", required=True)
    p.add_argument("--output-figure", required=True)
    p.add_argument("--include-kept-clients", action="store_true")
    args = p.parse_args()

    specs = parse_specs(args.method_specs)
    labels = [label for label, _ in specs]
    if args.reference not in labels:
        raise KeyError(f"reference label not found: {args.reference}")
    rows = build_rows(specs, reference=args.reference)

    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(
        json.dumps(
            {
                "reference": args.reference,
                "title_prefix": str(args.title_prefix),
                "include_kept_clients": bool(args.include_kept_clients),
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plot_rows(
        rows,
        Path(args.output_figure).resolve(),
        title_prefix=str(args.title_prefix),
        include_kept_clients=bool(args.include_kept_clients),
    )
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
