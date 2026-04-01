# Data Availability Notes (2026-03-24)

## Internal Scenario Graphs

The main paper scenarios are stored as derived graph artifacts under:

- `data_hitrust/bootstrap_graphs/graphs/`

These files are generated from the local collection pipeline used for the HiTrust-FedBot pilot scenarios.
Raw collection traces are not distributed in this artifact package; the released files are the derived graph objects used by the training pipeline.

## Public Auxiliary Benchmark

The repository now includes a public auxiliary benchmark path based on NSL-KDD.

- Raw public mirror used by the build script:
  - `https://github.com/defcom17/NSL_KDD`
- Local derived graph output:
  - `data_hitrust/public_benchmarks/nsl_kdd/graphs/nsl_kdd_public_graph.pt`
- Local metadata:
  - `data_hitrust/public_benchmarks/nsl_kdd/meta/nsl_kdd_public_manifest.json`
  - `data_hitrust/public_benchmarks/nsl_kdd/meta/nsl_kdd_public_build_summary.json`

The public validation graph is a feature-similarity graph built from the public NSL-KDD records to make the benchmark compatible with the GraphSAGE federated pipeline.

## Public Same-Task Scenario Validation

The repository now also includes same-task public external-validation paths based on the public `Ca-Bench` `data-v1` release.

- Public release source:
  - `https://github.com/1251408860-oss/Ca-Bench/releases/tag/data-v1`
- Raw archive used by the build script:
  - `data_hitrust/public_benchmarks/cabench_v1/raw/real_collection.tar.gz`
- Local generated graph outputs:
  - `data_hitrust/public_benchmarks/cabench_v1/graphs/cabench_scenario_e_three_tier_high2_public_graph.pt`
  - `data_hitrust/public_benchmarks/cabench_v1/graphs/cabench_scenario_h_mimic_heavy_overlap_public_graph.pt`
- Local metadata:
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_e_three_tier_high2_public_manifest.json`
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_e_three_tier_high2_public_build_summary.json`
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_h_mimic_heavy_overlap_public_manifest.json`
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_h_mimic_heavy_overlap_public_build_summary.json`

## Reproduction Scripts

- Public same-task external validation:
  - `core_experiments/reproduce/reproduce_public_cabench_validation.sh`
- Public same-task hardest validation:
  - `core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh`
- Public same-task hardest FLTrust-like sensitivity:
  - `core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh`
- Public auxiliary validation:
  - `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`
- Conditional-floor hardening validation:
  - `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`
