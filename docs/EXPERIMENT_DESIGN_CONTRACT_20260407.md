# Experiment Design Contract (2026-04-07)

This document records the local experiment contract that now governs the next-round HiTrust-FedBot evaluation.

## 1. Method Registry

Method semantics are now defined locally in `core_experiments/internal/experiment_registry.py` instead of being inferred only from config filenames.

The main split is:

- `reference_baseline`
  - classical or paper-spec comparators such as `mean`, `median`, `krum`, `rfa`, `centered_clipping`, `caf`, `arc_mean`
  - official-code anchor where available, currently `foolsgold`
- `task_adapted_baseline`
  - `fltrust_like`
  - `fedtruth_like`
  - `flshield_like`
- `proposed_method`
  - `hitrust_static`
- `proposed_hardening`
  - `hitrust_condfloor`
  - `temporal_rootguard`
  - `temporal_rootguard_v2`

This is the boundary that supports reviewer-visible provenance. `fltrust_like` remains explicitly adapted, not a strict FLTrust reproduction.

## 2. Benchmark Registry

Benchmarks are now classified locally as:

- `public_cabench_scenario_e`
  - same-task public
  - primary evidence
- `public_cabench_scenario_h`
  - same-task public
  - primary evidence
- `public_nslkdd`
  - cross-domain auxiliary
  - exploratory evidence
- `internal_bootstrap`
  - supporting evidence only

Candidate future public raw-data paths are also reserved:

- `public_westermo`
- `public_fml_network`
- `public_generic_flow`

## 3. Attack Registry

The local attack contract now includes:

- `update_noise`
- `sign_flip`
- `targeted_label_flip`
- `colluding_update_noise`
- `adaptive_benign_mimic`
- `adaptive_alie_like`
- `multi_round_stealth`

The point of this registry is not just naming. It drives whether a run is treated as `primary` or `exploratory` by default.

## 4. Stats Plan Contract

The registry maps each run to a stats family:

- `primary`
  - default for same-task public evidence on primary attack families
  - recommended seed count: `20`
  - correction: `Holm-Bonferroni`
- `promoted`
  - explicit promotion for adaptive public paths that have been rerun to matched 20-seed depth
  - current promoted paths: `public_cabench_scenario_h + adaptive_benign_mimic` and `public_cabench_scenario_e + adaptive_alie_like`
  - recommended seed count: `20`
  - correction: `Holm-Bonferroni`
- `exploratory`
  - default for auxiliary or supporting evidence
  - recommended seed count: `10`
  - correction: `BH-FDR`

Primary endpoints remain:

- `test_f1`
- `test_fpr`
- `kept_poisoned_clients`
- `kept_clients`

`core_experiments/internal/summarize_real_seed_sweep.py` now records whether the observed sweep meets the recommended seed count. `core_experiments/internal/build_method_comparison_report.py` now emits corrected p-values and paired effect sizes.

## 5. Generic Public Flow Adapter

To keep Ca-Bench from remaining the only realistic public path, the repository now includes:

- `core_experiments/internal/build_public_flow_benchmark_graph.py`

This script converts one or more public CSV flow files into the local graph schema contract. It is meant for next-step public datasets such as Westermo- or FML-Network-style flow tables.

Example shape:

```bash
python3 core_experiments/internal/build_public_flow_benchmark_graph.py \
  --project-root "$REPO_ROOT" \
  --input-pattern "$REPO_ROOT/data_hitrust/public_benchmarks/westermo/raw/**/*.csv" \
  --dataset-name "Westermo Network Traffic Dataset" \
  --dataset-variant "westermo_public_flow_graph" \
  --dataset-source "github_repo:westermo/network-traffic-dataset" \
  --output-graph "$REPO_ROOT/data_hitrust/public_benchmarks/westermo/graphs/westermo_public_graph.pt" \
  --output-manifest "$REPO_ROOT/data_hitrust/public_benchmarks/westermo/meta/westermo_public_manifest.json" \
  --output-summary "$REPO_ROOT/data_hitrust/public_benchmarks/westermo/meta/westermo_public_build_summary.json"
```

The adapter is intentionally local-contract-first:

- it emits HiTrust graph metadata
- it does not depend on external builder code
- it treats upstream public corpora as raw inputs only

## 6. Practical Interpretation

The repository should now be read as:

- local experiment framework
- local graph contract
- local method and benchmark registry
- local stats-plan contract
- optional external public data adapters

It should not be read as a thin wrapper around Ca-Bench or as a paper artifact whose experimental semantics are encoded only in ad hoc filenames.
