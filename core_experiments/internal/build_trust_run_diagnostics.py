#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


def mean_or_zero(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build trust-filter diagnostics for a family of real pilot runs")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--run-prefix", default="")
    p.add_argument("--run-glob", default="")
    p.add_argument("--output-file", required=True)
    return p.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def final_round_rows(trust_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not trust_rows:
        return []
    max_round = max(int(row["round"]) for row in trust_rows)
    return [row for row in trust_rows if int(row["round"]) == max_round]


def main() -> None:
    args = parse_args()
    runs_root = Path(args.runs_root).resolve()
    rows = []
    run_glob = str(args.run_glob).strip()
    run_prefix = str(args.run_prefix).strip()
    if not run_glob and not run_prefix:
        raise ValueError("either --run-prefix or --run-glob must be provided")
    summary_paths = (
        sorted(runs_root.glob(run_glob))
        if run_glob
        else sorted(runs_root.glob(f"{run_prefix}_seed*/summary.json"))
    )

    for summary_file in summary_paths:
        run_dir = summary_file.parent
        summary = load_json(summary_file)
        trust = load_json(run_dir / "trust_trace.json")
        partition = load_json(run_dir / "client_partition.json")

        trust_rows = list(trust.get("rows", []))
        final_rows = final_round_rows(trust_rows)
        final_round = max((int(row["round"]) for row in final_rows), default=0)
        final_round_info = next(
            (row for row in summary.get("round_rows", []) if int(row.get("round", 0)) == final_round),
            {},
        )
        kept_client_ids = [int(x) for x in final_round_info.get("kept_client_ids", [])]
        kept_set = set(kept_client_ids)
        poisoned_set = {int(x) for x in summary.get("poisoned_clients", [])}

        group_by_client = {
            int(row["client_id"]): str(row.get("group_name", "unknown"))
            for row in partition.get("clients", [])
        }
        final_by_client = {int(row["client_id"]): row for row in final_rows}

        group_partition_counts = Counter(group_by_client.values())
        group_poisoned_counts = Counter(group_by_client[cid] for cid in poisoned_set if cid in group_by_client)
        group_kept_counts = Counter(group_by_client[cid] for cid in kept_set if cid in group_by_client)
        group_kept_poisoned_counts = Counter(
            group_by_client[cid]
            for cid in kept_set
            if cid in poisoned_set and cid in group_by_client
        )

        avg_trust_by_group: dict[str, float] = {}
        for group_name in sorted(group_partition_counts):
            vals = [
                float(row["trust_norm"])
                for row in final_rows
                if str(row.get("group")) == group_name
            ]
            avg_trust_by_group[group_name] = mean_or_zero(vals)

        kept_poisoned_rows = []
        for cid in sorted(kept_set & poisoned_set):
            row = final_by_client.get(cid)
            if row is None:
                continue
            kept_poisoned_rows.append(
                {
                    "client_id": cid,
                    "group": str(row["group"]),
                    "trust_norm": float(row["trust_norm"]),
                    "val_f1": float(row["val_f1"]),
                    "update_norm": float(row["update_norm"]),
                }
            )

        dropped_clean_rows = []
        for cid, row in sorted(final_by_client.items()):
            if cid in kept_set or cid in poisoned_set:
                continue
            dropped_clean_rows.append(
                {
                    "client_id": cid,
                    "group": str(row["group"]),
                    "trust_norm": float(row["trust_norm"]),
                    "val_f1": float(row["val_f1"]),
                    "update_norm": float(row["update_norm"]),
                }
            )
        dropped_clean_rows.sort(key=lambda x: (x["trust_norm"], x["val_f1"]), reverse=True)

        benign_rows = [row for row in final_rows if str(row.get("group")) == "role:benign_user"]
        benign_kept = [row for row in benign_rows if int(row["client_id"]) in kept_set]
        benign_kept_poisoned = [
            row for row in benign_rows if int(row["client_id"]) in kept_set and bool(row["is_poisoned"])
        ]

        final_metrics = dict(summary.get("final_metrics", {}))
        rows.append(
            {
                "run_name": str(summary["config"]["run_name"]),
                "seed": int(summary["config"]["seed"]),
                "poison_type": str(summary["config"]["poison_type"]),
                "poison_frac": float(summary["config"]["poison_frac"]),
                "min_keep_per_group": int(summary["config"].get("min_keep_per_group", 0)),
                "test_f1": float(final_metrics.get("test_f1", 0.0)),
                "test_recall": float(final_metrics.get("test_recall", 0.0)),
                "test_fpr": float(final_metrics.get("test_fpr", 0.0)),
                "kept_clients": int(final_metrics.get("kept_clients", 0)),
                "kept_poisoned_clients": int(final_metrics.get("kept_poisoned_clients", 0)),
                "poisoned_clients": sorted(poisoned_set),
                "kept_client_ids": kept_client_ids,
                "group_partition_counts": dict(sorted(group_partition_counts.items())),
                "group_poisoned_counts": dict(sorted(group_poisoned_counts.items())),
                "group_kept_counts": dict(sorted(group_kept_counts.items())),
                "group_kept_poisoned_counts": dict(sorted(group_kept_poisoned_counts.items())),
                "group_avg_trust_final_round": avg_trust_by_group,
                "benign_total_clients": len(benign_rows),
                "benign_kept_clients": len(benign_kept),
                "benign_kept_poisoned_clients": len(benign_kept_poisoned),
                "benign_avg_trust_final_round": mean_or_zero([float(row["trust_norm"]) for row in benign_rows]),
                "retained_poisoned_clients": kept_poisoned_rows,
                "top_dropped_clean_clients": dropped_clean_rows[:3],
            }
        )

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
