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

## Reproduction Scripts

- Public auxiliary validation:
  - `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`
- Conditional-floor hardening validation:
  - `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`
