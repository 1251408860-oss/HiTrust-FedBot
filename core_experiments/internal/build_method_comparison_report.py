#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


def parse_specs(text: str) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        label, path = item.split("=", 1)
        out.append((label.strip(), Path(path).resolve()))
    return out


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(specs: list[tuple[str, Path]], reference: str) -> list[dict]:
    objects = {label: load_json(path) for label, path in specs}
    ref_obj = objects[reference]
    ref_f1 = [float(row["test_f1"]) for row in ref_obj.get("rows", [])]
    rows = []
    for label, path in specs:
        obj = objects[label]
        vals_f1 = [float(row["test_f1"]) for row in obj.get("rows", [])]
        vals_fpr = [float(row["test_fpr"]) for row in obj.get("rows", [])]
        vals_kept_poisoned = [float(row.get("kept_poisoned_clients", 0)) for row in obj.get("rows", [])]
        p_value = None
        t_stat = None
        if label != reference and len(ref_f1) >= 2 and len(vals_f1) >= 2:
            t_stat, p_value = stats.ttest_ind(ref_f1, vals_f1, equal_var=False)
            p_value = float(p_value)
            t_stat = float(t_stat)
        rows.append(
            {
                "label": label,
                "source_file": str(path),
                "test_f1_mean": float(obj["stats"]["test_f1"]["mean"]),
                "test_f1_std": float(obj["stats"]["test_f1"]["std"]),
                "test_fpr_mean": float(obj["stats"]["test_fpr"]["mean"]),
                "test_fpr_std": float(obj["stats"]["test_fpr"]["std"]),
                "kept_poisoned_clients_mean": float(obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
                "kept_poisoned_clients_std": float(obj["stats"].get("kept_poisoned_clients", {}).get("std", 0.0)),
                "kept_clients_mean": float(obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
                "n": int(obj["stats"]["test_f1"]["n"]),
                "f1_p_value_vs_reference": p_value,
                "f1_t_stat_vs_reference": t_stat,
            }
        )
    return rows


def plot_rows(rows: list[dict], output_file: Path, title_prefix: str) -> None:
    labels = [str(row["label"]) for row in rows]
    x = np.arange(len(labels))
    width = 0.7
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

    f1 = [float(row["test_f1_mean"]) for row in rows]
    f1_std = [float(row["test_f1_std"]) for row in rows]
    fpr = [float(row["test_fpr_mean"]) for row in rows]
    fpr_std = [float(row["test_fpr_std"]) for row in rows]
    kept_poisoned = [float(row["kept_poisoned_clients_mean"]) for row in rows]
    kept_poisoned_std = [float(row["kept_poisoned_clients_std"]) for row in rows]

    axes[0].bar(x, f1, width, yerr=f1_std, capsize=4)
    axes[0].set_xticks(x, labels, rotation=15)
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_title(f"{title_prefix} F1")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x, fpr, width, yerr=fpr_std, capsize=4)
    axes[1].set_xticks(x, labels, rotation=15)
    axes[1].set_ylim(0.0, max(fpr) + max(fpr_std + [0.01]) + 0.05)
    axes[1].set_title(f"{title_prefix} FPR")
    axes[1].grid(axis="y", alpha=0.25)

    axes[2].bar(x, kept_poisoned, width, yerr=kept_poisoned_std, capsize=4)
    axes[2].set_xticks(x, labels, rotation=15)
    axes[2].set_ylim(0.0, max(kept_poisoned) + max(kept_poisoned_std + [0.25]) + 0.5)
    axes[2].set_title(f"{title_prefix} Retained Poisoned")
    axes[2].grid(axis="y", alpha=0.25)

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
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plot_rows(rows, Path(args.output_figure).resolve(), title_prefix=str(args.title_prefix))
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
