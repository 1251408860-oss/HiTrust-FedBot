# `data_hitrust/`

This directory contains the bundled derived data artifacts used by the released HiTrust-FedBot repository.

## Contents

- `bootstrap_graphs/graphs/`: derived topology-aware pilot-scenario graph objects used by the main paper pipeline
- `bootstrap/manifests/`: repo-local manifest snapshots used to keep released bootstrap graphs self-contained
- `public_benchmarks/cabench_v1/`: same-task public `scenario_e` / `scenario_h` captures, helper tooling, and generated Ca-Bench graph objects
- `public_benchmarks/westermo/`: public Westermo flow archives, generated graph objects, and build metadata for the non-Ca-Bench raw-data chain
- `public_benchmarks/litnet2020/`: public LITNET-2020 UDP-flood archive, generated graph objects, and build metadata for the second non-Ca-Bench raw-data chain
- `public_benchmarks/nsl_kdd/`: auxiliary public-benchmark files, metadata, and the built graph object used for GraphSAGE-based validation

## Data-Release Boundary

The repository ships derived graph artifacts required to run the released code. It does not ship upstream private raw collection traces used before graph derivation for the internal pilot scenarios.

The released graph artifacts now follow a repo-local contract. Repo-internal references such as manifest files and builder locations are stored as repository-relative paths, the public Ca-Bench helper builder is vendored under `data_hitrust/public_benchmarks/cabench_v1/tools/` rather than fetched from an upstream moving branch during normal reruns, and the Westermo / LITNET-2020 builders write pinned-source manifests under their respective `public_benchmarks/*/meta/` directories.

Reviewers can verify the integrity of the bundled public artifact surface with:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

The SHA-256 manifest used by that script hashes immutable release files only. Generated public-benchmark graphs and build summaries under `public_benchmarks/*/{graphs,meta}` are treated as mutable rerun outputs because the public validation scripts rebuild them in place.
