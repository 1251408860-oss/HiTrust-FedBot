#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).resolve().read_text(encoding="utf-8"))


def max_retained_poisoned_trust_norm(row: dict) -> float:
    retained = row.get("retained_poisoned_clients", [])
    if not retained:
        return 0.0
    return float(max(float(item.get("trust_norm", 0.0)) for item in retained))


def build_rows(obj: dict) -> list[dict]:
    rows = []
    for row in sorted(obj.get("rows", []), key=lambda x: int(x.get("min_keep_per_group", 0))):
        benign_total = int(row.get("benign_total_clients", 0))
        benign_kept = int(row.get("benign_kept_clients", 0))
        benign_kept_poisoned = int(row.get("benign_kept_poisoned_clients", 0))
        rows.append(
            {
                "run_name": str(row.get("run_name", "")),
                "seed": int(row.get("seed", 0)),
                "poison_type": str(row.get("poison_type", "")),
                "poison_frac": float(row.get("poison_frac", 0.0)),
                "min_keep_per_group": int(row.get("min_keep_per_group", 0)),
                "test_f1": float(row.get("test_f1", 0.0)),
                "test_fpr": float(row.get("test_fpr", 0.0)),
                "kept_clients": int(row.get("kept_clients", 0)),
                "kept_poisoned_clients": int(row.get("kept_poisoned_clients", 0)),
                "benign_total_clients": benign_total,
                "benign_kept_clients": benign_kept,
                "benign_dropped_clients": max(benign_total - benign_kept, 0),
                "benign_kept_poisoned_clients": benign_kept_poisoned,
                "benign_avg_trust_final_round": float(row.get("benign_avg_trust_final_round", 0.0)),
                "max_retained_poisoned_trust_norm": max_retained_poisoned_trust_norm(row),
                "retained_poisoned_groups": sorted({str(item.get("group", "")) for item in row.get("retained_poisoned_clients", [])}),
            }
        )
    return rows


def plot_rows(rows: list[dict], output_figure: Path) -> None:
    x = np.array([int(row["min_keep_per_group"]) for row in rows], dtype=int)
    f1 = np.array([float(row["test_f1"]) for row in rows], dtype=float)
    fpr = np.array([float(row["test_fpr"]) for row in rows], dtype=float)
    benign_kept = np.array([int(row["benign_kept_clients"]) for row in rows], dtype=float)
    benign_kept_poisoned = np.array([int(row["benign_kept_poisoned_clients"]) for row in rows], dtype=float)
    benign_total = np.array([int(row["benign_total_clients"]) for row in rows], dtype=float)
    benign_avg_trust = np.array([float(row["benign_avg_trust_final_round"]) for row in rows], dtype=float)
    retained_poisoned_trust = np.array([float(row["max_retained_poisoned_trust_norm"]) for row in rows], dtype=float)

    fig, axes = plt.subplots(1, 3, figsize=(13.8, 4.1))

    axes[0].plot(x, f1, marker="o", linewidth=2.0, label="Test F1")
    axes[0].plot(x, fpr, marker="s", linewidth=2.0, label="Test FPR")
    axes[0].set_xlabel("min_keep_per_group")
    axes[0].set_title("Seed-11 Accuracy / Error")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    width = 0.26
    axes[1].bar(x - width / 2, benign_kept, width, label="Benign kept")
    axes[1].bar(x + width / 2, benign_kept_poisoned, width, label="Benign kept + poisoned")
    axes[1].plot(x, benign_total, linestyle="--", color="tab:gray", linewidth=1.5, label="Benign total")
    axes[1].set_xlabel("min_keep_per_group")
    axes[1].set_ylim(0, max(float(np.max(benign_total)), 2.0) + 0.4)
    axes[1].set_title("Benign-Group Retention")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].legend()

    axes[2].plot(x, benign_avg_trust, marker="o", linewidth=2.0, label="Benign avg trust")
    axes[2].plot(x, retained_poisoned_trust, marker="^", linewidth=2.0, label="Retained poisoned trust")
    axes[2].set_xlabel("min_keep_per_group")
    axes[2].set_ylim(0.0, max(1.0, float(np.max(benign_avg_trust)), float(np.max(retained_poisoned_trust))) * 1.05)
    axes[2].set_title("Final-Round Trust")
    axes[2].grid(alpha=0.25)
    axes[2].legend()

    fig.tight_layout()
    output_figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_figure, dpi=220)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Build a fixed-seed min_keep mechanism summary and figure")
    p.add_argument("--diagnostics-file", required=True)
    p.add_argument("--output-table", required=True)
    p.add_argument("--output-figure", required=True)
    args = p.parse_args()

    rows = build_rows(load_json(args.diagnostics_file))
    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    plot_rows(rows, Path(args.output_figure).resolve())
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
