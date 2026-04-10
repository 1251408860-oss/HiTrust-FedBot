#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

REGISTRY_VERSION = "hitrust_experiment_registry_v1"

PRIMARY_SEEDS_20 = [
    11,
    22,
    33,
    44,
    55,
    66,
    77,
    88,
    99,
    111,
    122,
    133,
    144,
    155,
    166,
    177,
    188,
    199,
    211,
    222,
]
EXPLORATORY_SEEDS_10 = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
PRIMARY_ENDPOINTS = [
    "test_f1",
    "test_fpr",
    "kept_poisoned_clients",
    "kept_clients",
]
PROMOTED_MATCHED_PAIRS: dict[tuple[str, str], dict[str, Any]] = {
    ("public_cabench_scenario_h", "adaptive_benign_mimic"): {
        "family": "promoted",
        "recommended_seed_count": len(PRIMARY_SEEDS_20),
        "recommended_seeds": list(PRIMARY_SEEDS_20),
        "correction_method": "holm_bonferroni",
        "promotion_note": "Promoted adaptive public reference.",
    },
    ("public_cabench_scenario_e", "adaptive_alie_like"): {
        "family": "promoted",
        "recommended_seed_count": len(PRIMARY_SEEDS_20),
        "recommended_seeds": list(PRIMARY_SEEDS_20),
        "correction_method": "holm_bonferroni",
        "promotion_note": "Promoted adaptive external transfer.",
    },
}

METHOD_REGISTRY: dict[str, dict[str, Any]] = {
    "hitrust_static": {
        "label": "trust_aware",
        "method_family": "proposed_method",
        "provenance_kind": "repo_native",
        "reference_grade": False,
        "claim_role": "mainline",
        "notes": "Static grouped trust-aware aggregation.",
    },
    "hitrust_condfloor": {
        "label": "condfloor",
        "method_family": "proposed_hardening",
        "provenance_kind": "repo_native",
        "reference_grade": False,
        "claim_role": "targeted_repair",
        "notes": "Conditional trust-mass floor repair for small-group collapse.",
    },
    "temporal_rootguard": {
        "label": "temporal_rootguard",
        "method_family": "proposed_adaptive_hardening",
        "provenance_kind": "repo_native",
        "reference_grade": False,
        "claim_role": "adaptive_operating_point",
        "notes": "Temporal reputation and server-root-aware adaptive hardening.",
    },
    "temporal_rootguard_v2": {
        "label": "temporal_rootguard_v2",
        "method_family": "proposed_adaptive_hardening",
        "provenance_kind": "repo_native",
        "reference_grade": False,
        "claim_role": "adaptive_operating_point",
        "notes": "Extended temporal hardening with layerwise and behavioral probes.",
    },
    "hierarchical_keepall": {
        "label": "hier_keepall",
        "method_family": "repo_ablation",
        "provenance_kind": "repo_native",
        "reference_grade": False,
        "claim_role": "keep_all_control",
        "notes": "Hierarchical aggregation with trust filtering disabled.",
    },
    "fltrust_like": {
        "label": "fltrust_like",
        "method_family": "task_adapted_baseline",
        "provenance_kind": "task_adapted_reimplementation",
        "reference_grade": False,
        "claim_role": "adapted_comparator",
        "upstream_name": "FLTrust",
        "upstream_url": "https://people.duke.edu/~zg70/code/fltrust.zip",
        "upstream_commit": "",
        "upstream_tag": "",
        "upstream_component": "server-root trust weighting",
        "official_source_kind": "author_code_archive_semantic_anchor",
        "notes": "Adapted trust-bootstrap comparator aligned to the original author code archive and paper semantics, not a strict reference reproduction.",
    },
    "fedtruth_like": {
        "label": "fedtruth_like",
        "method_family": "task_adapted_baseline",
        "provenance_kind": "task_adapted_reimplementation",
        "reference_grade": False,
        "claim_role": "adapted_comparator",
        "notes": "Task-adapted comparator for truth-style robust aggregation.",
    },
    "flshield_like": {
        "label": "flshield_like",
        "method_family": "task_adapted_baseline",
        "provenance_kind": "task_adapted_reimplementation",
        "reference_grade": False,
        "claim_role": "adapted_comparator",
        "upstream_name": "FLShield",
        "upstream_url": "https://github.com/ehsanul9511/FLShield",
        "upstream_commit": "afe4474440f0b88b8f1d09ab5cf5a75fd7230e6a",
        "upstream_tag": "",
        "upstream_component": "validation-guided clustered client filtering",
        "official_source_kind": "official_repository_semantic_anchor",
        "notes": "Task-adapted clustered filtering comparator aligned to the official FLShield repository semantics, not a strict reference reproduction.",
    },
    "foolsgold": {
        "label": "foolsgold",
        "method_family": "reference_baseline",
        "provenance_kind": "official_code_port",
        "reference_grade": True,
        "claim_role": "reference_anchor",
        "upstream_name": "FoolsGold",
        "upstream_url": "https://github.com/DistributedML/FoolsGold",
        "upstream_commit": "0aa55114296a2d3c2bcb6f544a6fae31e8e7b8b4",
        "upstream_tag": "",
        "upstream_component": "official_repository",
        "official_source_kind": "official_repository",
        "notes": "Official-code history-similarity baseline.",
    },
    "centered_clipping": {
        "label": "centered_clipping",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "robust_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "CenteredClipping",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Paper-spec robust clipping baseline.",
    },
    "caf": {
        "label": "caf",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "modern_robust_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://byzfl.epfl.ch/aggregators/classes/caf.html",
        "upstream_commit": "",
        "upstream_tag": "",
        "upstream_component": "CAF",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Covariance-bound Agnostic Filter aggregation baseline.",
    },
    "arc_mean": {
        "label": "arc_mean",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "modern_preaggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "ARC+Average",
        "official_source_kind": "official_toolkit_reference",
        "notes": "ARC pre-aggregation followed by mean aggregation.",
    },
    "rfa": {
        "label": "rfa",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "classical_robust_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "GeometricMedian",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Geometric median robust aggregation.",
    },
    "mean": {
        "label": "mean",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "classical_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "Average",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Unfiltered mean aggregation baseline.",
    },
    "median": {
        "label": "median",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "classical_robust_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "Median",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Coordinate-wise median baseline.",
    },
    "krum": {
        "label": "krum",
        "method_family": "reference_baseline",
        "provenance_kind": "paper_spec_reimplementation",
        "reference_grade": True,
        "claim_role": "classical_robust_aggregation",
        "upstream_name": "ByzFL",
        "upstream_url": "https://github.com/LPD-EPFL/byzfl",
        "upstream_commit": "5830978d991a0900748f7ce901dc3ca532081b26",
        "upstream_tag": "v0.0.11",
        "upstream_component": "Krum",
        "official_source_kind": "official_toolkit_reference",
        "notes": "Krum-style proxy baseline.",
    },
}

ATTACK_REGISTRY: dict[str, dict[str, Any]] = {
    "none": {
        "label": "clean",
        "attack_family": "clean",
        "adaptive": False,
        "coordination": "none",
        "stats_priority": "exploratory",
    },
    "update_noise": {
        "label": "update_noise",
        "attack_family": "non_adaptive_update_poisoning",
        "adaptive": False,
        "coordination": "independent",
        "stats_priority": "primary",
    },
    "sign_flip": {
        "label": "sign_flip",
        "attack_family": "non_adaptive_update_poisoning",
        "adaptive": False,
        "coordination": "independent",
        "stats_priority": "primary",
    },
    "targeted_label_flip": {
        "label": "targeted_label_flip",
        "attack_family": "training_data_poisoning",
        "adaptive": False,
        "coordination": "independent",
        "stats_priority": "primary",
    },
    "colluding_update_noise": {
        "label": "colluding_update_noise",
        "attack_family": "coordinated_update_poisoning",
        "adaptive": False,
        "coordination": "colluding",
        "stats_priority": "primary",
    },
    "adaptive_benign_mimic": {
        "label": "adaptive_benign_mimic",
        "attack_family": "defense_aware_poisoning",
        "adaptive": True,
        "coordination": "colluding",
        "stats_priority": "exploratory",
    },
    "adaptive_alie_like": {
        "label": "adaptive_alie_like",
        "attack_family": "defense_aware_poisoning",
        "adaptive": True,
        "coordination": "colluding",
        "stats_priority": "exploratory",
    },
    "multi_round_stealth": {
        "label": "multi_round_stealth",
        "attack_family": "temporal_stealth_poisoning",
        "adaptive": True,
        "coordination": "colluding",
        "stats_priority": "primary",
    },
}

BENCHMARK_REGISTRY: dict[str, dict[str, Any]] = {
    "internal_bootstrap": {
        "dataset_scope": "internal_derived",
        "task_relation": "internal_supporting",
        "evidence_tier": "supporting",
    },
    "public_cabench_scenario_e": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "same_task_public",
        "evidence_tier": "primary",
    },
    "public_cabench_scenario_h": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "same_task_public",
        "evidence_tier": "primary",
    },
    "public_nslkdd": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "cross_domain_auxiliary",
        "evidence_tier": "auxiliary",
    },
    "public_westermo": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "same_modality_public",
        "evidence_tier": "primary",
    },
    "public_litnet2020": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "same_modality_public",
        "evidence_tier": "primary",
    },
    "public_fml_network": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "same_modality_public",
        "evidence_tier": "primary_candidate",
    },
    "public_generic_flow": {
        "dataset_scope": "public_raw_to_graph",
        "task_relation": "external_public",
        "evidence_tier": "candidate",
    },
    "unknown": {
        "dataset_scope": "unknown",
        "task_relation": "unknown",
        "evidence_tier": "candidate",
    },
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def resolve_method_key(cfg: dict[str, Any]) -> str:
    aggregation = str(cfg.get("aggregation", "hierarchical")).strip()
    trust_mode = str(cfg.get("trust_mode", "static")).strip()
    trust_threshold = _safe_float(cfg.get("trust_threshold", 0.35), 0.35)
    min_keep_per_group = _safe_int(cfg.get("min_keep_per_group", 0), 0)
    group_floor_policy = str(cfg.get("group_floor_policy", "static")).strip()

    if aggregation == "hierarchical":
        if trust_mode == "temporal_rootguard_v2":
            return "temporal_rootguard_v2"
        if trust_mode == "temporal_rootguard":
            return "temporal_rootguard"
        if trust_threshold <= 0.0 and min_keep_per_group <= 0:
            return "hierarchical_keepall"
        if group_floor_policy == "conditional_trust_mass":
            return "hitrust_condfloor"
        return "hitrust_static"
    if aggregation in METHOD_REGISTRY:
        return aggregation
    return aggregation or "unknown"


def get_method_metadata(method_key: str) -> dict[str, Any]:
    obj = dict(METHOD_REGISTRY.get(str(method_key), {}))
    obj.setdefault("label", str(method_key))
    obj.setdefault("method_family", "unknown")
    obj.setdefault("provenance_kind", "unknown")
    obj.setdefault("reference_grade", False)
    obj["method_key"] = str(method_key)
    obj["registry_version"] = REGISTRY_VERSION
    return obj


def resolve_attack_key(attack_type: str) -> str:
    key = str(attack_type or "none").strip() or "none"
    if key in ATTACK_REGISTRY:
        return key
    return "none" if key == "clean" else key


def get_attack_metadata(attack_key: str) -> dict[str, Any]:
    obj = dict(ATTACK_REGISTRY.get(str(attack_key), {}))
    obj.setdefault("label", str(attack_key))
    obj.setdefault("attack_family", "unknown")
    obj.setdefault("adaptive", False)
    obj.setdefault("coordination", "unknown")
    obj.setdefault("stats_priority", "exploratory")
    obj["attack_key"] = str(attack_key)
    obj["registry_version"] = REGISTRY_VERSION
    return obj


def resolve_benchmark_key(
    *,
    dataset_name: str = "",
    dataset_variant: str = "",
    dataset_source: str = "",
    graph_source_kind: str = "",
    graph_file: str = "",
    run_name: str = "",
) -> str:
    dataset_name_l = str(dataset_name).strip().lower()
    dataset_variant_l = str(dataset_variant).strip().lower()
    dataset_source_l = str(dataset_source).strip().lower()
    graph_source_kind_l = str(graph_source_kind).strip().lower()
    graph_file_l = str(graph_file).strip().lower().replace("\\", "/")
    run_name_l = str(run_name).strip().lower()
    joined = " | ".join(
        [
            dataset_name_l,
            dataset_variant_l,
            dataset_source_l,
            graph_source_kind_l,
            graph_file_l,
            run_name_l,
        ]
    )
    if "nsl" in joined:
        return "public_nslkdd"
    if "westermo" in joined:
        return "public_westermo"
    if "litnet" in joined:
        return "public_litnet2020"
    if "fml-network" in joined or "flnet" in joined or "fml_network" in joined:
        return "public_fml_network"
    if "cabench" in joined or "ca-bench" in joined:
        if "scenario_h" in joined or "mimic_heavy_overlap" in joined:
            return "public_cabench_scenario_h"
        if "scenario_e" in joined or "three_tier_high2" in joined:
            return "public_cabench_scenario_e"
    if "bootstrap" in joined or "real_graph_pilot" in joined or graph_source_kind_l == "internal_bootstrap_graph":
        return "internal_bootstrap"
    if "public" in graph_source_kind_l and "dataset" in graph_source_kind_l:
        return "public_generic_flow"
    return "unknown"


def get_benchmark_metadata(benchmark_key: str) -> dict[str, Any]:
    obj = dict(BENCHMARK_REGISTRY.get(str(benchmark_key), {}))
    obj.setdefault("dataset_scope", "unknown")
    obj.setdefault("task_relation", "unknown")
    obj.setdefault("evidence_tier", "candidate")
    obj["benchmark_key"] = str(benchmark_key)
    obj["registry_version"] = REGISTRY_VERSION
    return obj


def build_stats_plan(*, benchmark_key: str, attack_key: str) -> dict[str, Any]:
    benchmark = get_benchmark_metadata(benchmark_key)
    attack = get_attack_metadata(attack_key)
    evidence_tier = str(benchmark.get("evidence_tier", "candidate"))
    attack_priority = str(attack.get("stats_priority", "exploratory"))
    override = PROMOTED_MATCHED_PAIRS.get((str(benchmark_key), str(attack_key)))

    if isinstance(override, dict):
        family = str(override.get("family", "promoted"))
        recommended_seed_count = int(override.get("recommended_seed_count", len(PRIMARY_SEEDS_20)))
        correction_method = str(override.get("correction_method", "holm_bonferroni"))
        recommended_seeds = list(override.get("recommended_seeds", PRIMARY_SEEDS_20))
    elif evidence_tier == "primary" and attack_priority == "primary":
        family = "primary"
        recommended_seed_count = len(PRIMARY_SEEDS_20)
        correction_method = "holm_bonferroni"
        recommended_seeds = list(PRIMARY_SEEDS_20)
    else:
        family = "exploratory"
        recommended_seed_count = len(EXPLORATORY_SEEDS_10)
        correction_method = "bh_fdr"
        recommended_seeds = list(EXPLORATORY_SEEDS_10)

    return {
        "family": family,
        "recommended_seed_count": int(recommended_seed_count),
        "recommended_seeds": recommended_seeds,
        "primary_endpoints": list(PRIMARY_ENDPOINTS),
        "correction_method": correction_method,
        "promotion_note": str(override.get("promotion_note", "")) if isinstance(override, dict) else "",
        "registry_version": REGISTRY_VERSION,
    }


def build_experiment_contract(
    *,
    cfg: dict[str, Any],
    dataset_info: dict[str, Any] | None = None,
    graph_file: str = "",
    run_name: str = "",
) -> dict[str, Any]:
    dataset_info = dict(dataset_info or {})
    method_key = resolve_method_key(cfg)
    attack_key = resolve_attack_key(str(cfg.get("poison_type", "none")))
    benchmark_key = resolve_benchmark_key(
        dataset_name=str(dataset_info.get("dataset_name", "")),
        dataset_variant=str(dataset_info.get("dataset_variant", "")),
        dataset_source=str(dataset_info.get("dataset_source", "")),
        graph_source_kind=str(dataset_info.get("graph_source_kind", "")),
        graph_file=graph_file,
        run_name=run_name or str(cfg.get("run_name", "")),
    )
    return {
        "registry_version": REGISTRY_VERSION,
        "method": get_method_metadata(method_key),
        "attack": get_attack_metadata(attack_key),
        "benchmark": get_benchmark_metadata(benchmark_key),
        "stats_plan": build_stats_plan(benchmark_key=benchmark_key, attack_key=attack_key),
    }
