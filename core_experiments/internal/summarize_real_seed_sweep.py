#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any

from experiment_registry import build_experiment_contract

SEED_PATTERN = re.compile(r"_seed(\d+)$")


def mean_std(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"n": 0, "mean": 0.0, "std": 0.0}
    if len(vals) == 1:
        return {"n": 1, "mean": vals[0], "std": 0.0}
    return {"n": len(vals), "mean": statistics.mean(vals), "std": statistics.stdev(vals)}


def extract_seed(run_name: str, fallback_index: int) -> int:
    match = SEED_PATTERN.search(str(run_name))
    if match:
        return int(match.group(1))
    return int(fallback_index)


def load_summary_contract(obj: dict[str, Any]) -> dict[str, Any]:
    rebuilt = build_experiment_contract(
        cfg=dict(obj.get("config", {}) or {}),
        dataset_info=dict(obj.get("dataset_info", {}) or {}),
        graph_file=str(obj.get("graph_file", "")),
        run_name=str(obj.get("config", {}).get("run_name", obj.get("run_name", ""))),
    )
    existing = obj.get("experiment_contract")
    if isinstance(existing, dict) and existing:
        merged = dict(existing)
        for key in ("registry_version", "method", "attack", "benchmark", "stats_plan"):
            merged[key] = rebuilt.get(key)
        return merged
    return rebuilt


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize a real graph seed sweep")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--run-prefix", required=True)
    p.add_argument("--output-file", required=True)
    args = p.parse_args()

    runs_root = Path(args.runs_root)
    rows: list[dict[str, Any]] = []
    contracts: list[dict[str, Any]] = []
    f1: list[float] = []
    recall: list[float] = []
    fpr: list[float] = []
    kept_clients: list[float] = []
    kept_poisoned_clients: list[float] = []
    local_training_ms: list[float] = []
    attack_simulation_ms: list[float] = []
    client_eval_ms: list[float] = []
    server_aggregation_ms: list[float] = []
    global_eval_ms: list[float] = []
    server_round_ms: list[float] = []
    round_wall_clock_ms: list[float] = []
    process_rss_mb: list[float] = []
    process_peak_rss_mb: list[float] = []
    bytes_per_round_est: list[float] = []
    active_clients: list[float] = []
    pattern = re.compile(rf"^{re.escape(str(args.run_prefix))}_seed\d+$")
    for idx, summary_file in enumerate(sorted(runs_root.glob(f"{args.run_prefix}_seed*/summary.json"))):
        if not pattern.fullmatch(summary_file.parent.name):
            continue
        obj = json.loads(summary_file.read_text(encoding="utf-8"))
        final = obj["final_metrics"]
        timing = dict(obj.get("timing", {}) or {})
        resource_usage = dict(obj.get("resource_usage", {}) or {})
        comm_cost = dict(obj.get("comm_cost", {}) or {})
        partition_info = dict(obj.get("partition_info", {}) or {})
        contract = load_summary_contract(obj)
        method = dict(contract.get("method", {}) or {})
        attack = dict(contract.get("attack", {}) or {})
        benchmark = dict(contract.get("benchmark", {}) or {})
        contracts.append(contract)
        row = {
            "run_name": summary_file.parent.name,
            "seed": extract_seed(summary_file.parent.name, idx),
            "test_f1": float(final["test_f1"]),
            "test_recall": float(final["test_recall"]),
            "test_fpr": float(final["test_fpr"]),
            "kept_clients": float(final.get("kept_clients", 0)),
            "kept_poisoned_clients": float(final.get("kept_poisoned_clients", 0)),
            "local_training_ms_mean": float(dict(timing.get("local_training_ms", {}) or {}).get("mean", 0.0)),
            "attack_simulation_ms_mean": float(dict(timing.get("attack_simulation_ms", {}) or {}).get("mean", 0.0)),
            "client_eval_ms_mean": float(dict(timing.get("client_eval_ms", {}) or {}).get("mean", 0.0)),
            "server_aggregation_ms_mean": float(dict(timing.get("server_aggregation_ms", {}) or {}).get("mean", 0.0)),
            "global_eval_ms_mean": float(dict(timing.get("global_eval_ms", {}) or {}).get("mean", 0.0)),
            "server_round_ms_mean": float(dict(timing.get("server_round_ms", {}) or {}).get("mean", 0.0)),
            "round_wall_clock_ms_mean": float(dict(timing.get("round_wall_clock_ms", {}) or {}).get("mean", 0.0)),
            "process_rss_mb_mean": float(dict(resource_usage.get("process_rss_mb", {}) or {}).get("mean", 0.0)),
            "process_peak_rss_mb_mean": float(
                dict(resource_usage.get("process_peak_rss_mb", {}) or {}).get("mean", 0.0)
            ),
            "bytes_per_round_est": float(comm_cost.get("bytes_per_round_est", 0.0)),
            "active_clients": float(partition_info.get("active_clients", 0.0)),
            "method_key": str(method.get("method_key", "")),
            "attack_key": str(attack.get("attack_key", "")),
            "benchmark_key": str(benchmark.get("benchmark_key", "")),
        }
        rows.append(row)
        f1.append(float(row["test_f1"]))
        recall.append(float(row["test_recall"]))
        fpr.append(float(row["test_fpr"]))
        kept_clients.append(float(row["kept_clients"]))
        kept_poisoned_clients.append(float(row["kept_poisoned_clients"]))
        local_training_ms.append(float(row["local_training_ms_mean"]))
        attack_simulation_ms.append(float(row["attack_simulation_ms_mean"]))
        client_eval_ms.append(float(row["client_eval_ms_mean"]))
        server_aggregation_ms.append(float(row["server_aggregation_ms_mean"]))
        global_eval_ms.append(float(row["global_eval_ms_mean"]))
        server_round_ms.append(float(row["server_round_ms_mean"]))
        round_wall_clock_ms.append(float(row["round_wall_clock_ms_mean"]))
        process_rss_mb.append(float(row["process_rss_mb_mean"]))
        process_peak_rss_mb.append(float(row["process_peak_rss_mb_mean"]))
        bytes_per_round_est.append(float(row["bytes_per_round_est"]))
        active_clients.append(float(row["active_clients"]))

    contract = contracts[0] if contracts else {}
    stats_plan = dict(contract.get("stats_plan", {}) or {})
    observed_seeds = sorted({int(row["seed"]) for row in rows})
    recommended_seed_count = int(stats_plan.get("recommended_seed_count", 0) or 0)

    out = {
        "run_prefix": str(args.run_prefix),
        "experiment_contract": contract,
        "seed_plan": {
            "observed_seeds": observed_seeds,
            "observed_seed_count": int(len(observed_seeds)),
            "recommended_seed_count": recommended_seed_count,
            "meets_recommended_seed_count": bool(len(observed_seeds) >= recommended_seed_count if recommended_seed_count > 0 else False),
            "family": str(stats_plan.get("family", "")),
            "correction_method": str(stats_plan.get("correction_method", "")),
        },
        "rows": rows,
        "stats": {
            "test_f1": mean_std(f1),
            "test_recall": mean_std(recall),
            "test_fpr": mean_std(fpr),
            "kept_clients": mean_std(kept_clients),
            "kept_poisoned_clients": mean_std(kept_poisoned_clients),
            "local_training_ms": mean_std(local_training_ms),
            "attack_simulation_ms": mean_std(attack_simulation_ms),
            "client_eval_ms": mean_std(client_eval_ms),
            "server_aggregation_ms": mean_std(server_aggregation_ms),
            "global_eval_ms": mean_std(global_eval_ms),
            "server_round_ms": mean_std(server_round_ms),
            "round_wall_clock_ms": mean_std(round_wall_clock_ms),
            "process_rss_mb": mean_std(process_rss_mb),
            "process_peak_rss_mb": mean_std(process_peak_rss_mb),
            "bytes_per_round_est": mean_std(bytes_per_round_est),
            "active_clients": mean_std(active_clients),
        },
    }
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_file}")


if __name__ == "__main__":
    main()
