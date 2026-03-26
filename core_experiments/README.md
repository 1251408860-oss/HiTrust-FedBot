# `core_experiments/`

This directory contains the executable code, configuration files, and reproduction entry points used by the HiTrust-FedBot artifact.

## Main Subdirectories

- `configs_hitrust/`: runnable experiment configs, seed sweeps, and grid manifests
- `internal/`: implementation code for training, trust scoring, aggregation, graph building, and table generation
- `reproduce/`: reviewer-facing shell entry points for the main reproduction paths

## Recommended Entry Points

Smoke test:

```bash
python core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

Auxiliary public validation:

```bash
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

Conditional-floor hardening:

```bash
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh
```
