# `data_hitrust/`

This directory contains the bundled derived data artifacts used by the released HiTrust-FedBot repository.

## Contents

- `bootstrap_graphs/graphs/`: derived topology-aware pilot-scenario graph objects used by the main paper pipeline
- `public_benchmarks/cabench_v1/`: same-task public `scenario_e` / `scenario_h` captures, helper tooling, and generated Ca-Bench graph objects
- `public_benchmarks/nsl_kdd/`: auxiliary public-benchmark files, metadata, and the built graph object used for GraphSAGE-based validation

## Data-Release Boundary

The repository ships derived graph artifacts required to run the released code. It does not ship upstream private raw collection traces used before graph derivation for the internal pilot scenarios.

Reviewers can verify the integrity of the bundled public artifact surface with:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

The SHA-256 manifest used by that script hashes immutable release files only. Generated public-benchmark graphs and build summaries under `public_benchmarks/*/{graphs,meta}` are treated as mutable rerun outputs because the public validation scripts rebuild them in place.
