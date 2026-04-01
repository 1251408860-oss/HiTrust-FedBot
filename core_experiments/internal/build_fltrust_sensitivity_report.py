#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


LABEL_PATTERN = re.compile(r"^root(?P<root>\d+)_e(?P<epochs>\d+)$")


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


def parse_label(label: str) -> tuple[int, int]:
    match = LABEL_PATTERN.fullmatch(str(label).strip())
    if not match:
        raise ValueError(f"invalid sensitivity label: {label}")
    return int(match.group("root")), int(match.group("epochs"))


def build_rows(specs: list[tuple[str, Path]]) -> list[dict]:
    rows: list[dict] = []
    for label, path in specs:
        root_size, local_epochs = parse_label(label)
        obj = load_json(path)
        rows.append(
            {
                "label": label,
                "source_file": str(path),
                "server_root_size": int(root_size),
                "server_root_local_epochs": int(local_epochs),
                "test_f1_mean": float(obj["stats"]["test_f1"]["mean"]),
                "test_f1_std": float(obj["stats"]["test_f1"]["std"]),
                "test_fpr_mean": float(obj["stats"]["test_fpr"]["mean"]),
                "test_fpr_std": float(obj["stats"]["test_fpr"]["std"]),
                "kept_clients_mean": float(obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
                "kept_poisoned_clients_mean": float(obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
                "kept_poisoned_clients_std": float(obj["stats"].get("kept_poisoned_clients", {}).get("std", 0.0)),
                "n": int(obj["stats"]["test_f1"]["n"]),
            }
        )
    return sorted(rows, key=lambda x: (int(x["server_root_size"]), int(x["server_root_local_epochs"])))


def build_reference_rows(specs: list[tuple[str, Path]]) -> list[dict]:
    rows: list[dict] = []
    for label, path in specs:
        obj = load_json(path)
        rows.append(
            {
                "label": str(label),
                "source_file": str(path),
                "test_f1_mean": float(obj["stats"]["test_f1"]["mean"]),
                "test_fpr_mean": float(obj["stats"]["test_fpr"]["mean"]),
                "kept_poisoned_clients_mean": float(obj["stats"].get("kept_poisoned_clients", {}).get("mean", 0.0)),
                "kept_clients_mean": float(obj["stats"].get("kept_clients", {}).get("mean", 0.0)),
                "n": int(obj["stats"]["test_f1"]["n"]),
            }
        )
    return rows


def select_best_rows(rows: list[dict]) -> dict:
    best_f1 = max(rows, key=lambda x: (float(x["test_f1_mean"]), -float(x["kept_poisoned_clients_mean"]), -float(x["test_fpr_mean"])))
    best_security = min(rows, key=lambda x: (float(x["kept_poisoned_clients_mean"]), -float(x["test_f1_mean"]), float(x["test_fpr_mean"])))
    return {
        "best_by_f1": dict(best_f1),
        "best_by_retained_poisoned": dict(best_security),
    }


def plot_rows(
    *,
    rows: list[dict],
    reference_rows: list[dict],
    output_file: Path,
    title_prefix: str,
) -> None:
    epochs_values = sorted({int(row["server_root_local_epochs"]) for row in rows})
    root_sizes = sorted({int(row["server_root_size"]) for row in rows})
    colors = {
        1: "tab:blue",
        2: "tab:orange",
        3: "tab:green",
    }

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.3))
    y_specs = [
        ("test_f1_mean", "Test F1", (0.0, 1.02)),
        ("test_fpr_mean", "Test FPR", None),
        ("kept_poisoned_clients_mean", "Retained Poisoned", None),
    ]

    for ax, (field, title, y_lim) in zip(axes, y_specs):
        for local_epochs in epochs_values:
            subset = [row for row in rows if int(row["server_root_local_epochs"]) == int(local_epochs)]
            subset = sorted(subset, key=lambda x: int(x["server_root_size"]))
            xs = [int(row["server_root_size"]) for row in subset]
            ys = [float(row[field]) for row in subset]
            ax.plot(xs, ys, marker="o", linewidth=2, color=colors.get(local_epochs, None), label=f"root epochs={local_epochs}")
        for ref in reference_rows:
            ax.axhline(float(ref[field]), linestyle="--", linewidth=1.2, alpha=0.75, label=str(ref["label"]))
        ax.set_xticks(root_sizes, [str(x) for x in root_sizes])
        ax.set_xlabel("server_root_size")
        ax.set_title(f"{title_prefix} {title}")
        ax.grid(alpha=0.25)
        if y_lim is not None:
            ax.set_ylim(*y_lim)

    handles, labels = axes[0].get_legend_handles_labels()
    uniq: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        uniq.setdefault(label, handle)
    fig.legend(list(uniq.values()), list(uniq.keys()), loc="lower center", ncol=min(len(uniq), 5), frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a FLTrust-like sensitivity report from seed stats files")
    parser.add_argument("--method-specs", required=True, help="CSV of root48_e1=/path/to/seed_stats.json")
    parser.add_argument("--reference-specs", default="", help="Optional CSV of baseline_label=/path/to/seed_stats.json")
    parser.add_argument("--title-prefix", default="FLTrust-like Sensitivity")
    parser.add_argument("--output-table", required=True)
    parser.add_argument("--output-figure", required=True)
    args = parser.parse_args()

    rows = build_rows(parse_specs(args.method_specs))
    reference_rows = build_reference_rows(parse_specs(args.reference_specs))
    summary = {
        "title_prefix": str(args.title_prefix),
        "rows": rows,
        "reference_rows": reference_rows,
    }
    summary.update(select_best_rows(rows))

    output_table = Path(args.output_table).resolve()
    output_table.parent.mkdir(parents=True, exist_ok=True)
    output_table.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plot_rows(
        rows=rows,
        reference_rows=reference_rows,
        output_file=Path(args.output_figure).resolve(),
        title_prefix=str(args.title_prefix),
    )
    print(f"[OK] wrote {output_table}")
    print(f"[OK] wrote {Path(args.output_figure).resolve()}")


if __name__ == "__main__":
    main()
