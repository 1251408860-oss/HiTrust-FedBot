# `data_hitrust/`

This directory contains the bundled derived data artifacts used by the released HiTrust-FedBot repository.

## Contents

- `bootstrap_graphs/graphs/`: derived topology-aware pilot-scenario graph objects used by the main paper pipeline
- `public_benchmarks/nsl_kdd/`: auxiliary public-benchmark files, metadata, and the built graph object used for GraphSAGE-based validation

## Data-Release Boundary

The repository ships derived graph artifacts required to run the released code. It does not ship upstream private raw collection traces used before graph derivation for the internal pilot scenarios.
