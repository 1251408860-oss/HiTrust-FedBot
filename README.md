# HiTrust-FedBot

Hierarchical and trust-aware federated Web bot detection under congested edge environments.

This repository is released as a reviewer-facing artifact package for the HiTrust-FedBot study. It contains the code, bundled derived data artifacts, precomputed paper outputs, and reproduction scripts used to support the current manuscript.

## Repository Navigation and Artifact Mapping

| Path | Role in the release | What a reviewer should expect |
| --- | --- | --- |
| `README.md` | Repository landing page | Entry point for installation, reproduction, and artifact structure |
| `environment.yml` | Suggested conda environment | Minimal reproducible environment for the main artifact path |
| `requirements_artifact.txt` | Exact package freeze from the working environment | Optional fallback when matching the packaged environment more closely |
| `RELEASE_CHECKLIST.md` | Release-facing sanity checklist | What is included, excluded, and how the release should be interpreted |
| `core_experiments/` | Executable code, configs, and reproduction scripts | Main place to inspect runnable pipelines |
| `data_hitrust/` | Bundled derived graph artifacts and benchmark data | Main pilot graphs and auxiliary public validation graph |
| `paper_hitrust/` | Precomputed runs, tables, figures, and manuscript support files | Delivered paper-facing outputs already bundled in the repository |
| `docs/` | Supporting notes for artifact and submission packaging | Artifact scope, data availability, and manuscript-support notes |
| `tests/` | Focused regression tests | Small checks for recent risk-fix behavior |

## Global Environment Overview

The artifact was prepared and verified in a Linux/WSL workflow with:

- Python `3.10.19`
- Conda environment name: `hitrust-fedbot`
- Recommended entry file: `environment.yml`
- Exact environment freeze: `requirements_artifact.txt`

The repository does not require external private dependencies. The public auxiliary validation path downloads NSL-KDD from a public mirror when reproduced from scratch.

## Bundled Artifact Scope

The repository already includes the main derived outputs referenced by the current paper workflow:

- topology-aware bootstrap graph artifacts under `data_hitrust/bootstrap_graphs/graphs/`
- auxiliary public NSL-KDD graph under `data_hitrust/public_benchmarks/nsl_kdd/graphs/`
- paper tables under `paper_hitrust/tables/`
- paper figures under `paper_hitrust/figures/`
- precomputed run outputs under `paper_hitrust/runs/`

This means a reviewer can inspect the delivered evidence directly before deciding whether to rerun the pipelines.

## Quick Installation

Create the recommended conda environment:

```bash
cd /path/to/HiTrust-FedBot
conda env create -f environment.yml
conda activate hitrust-fedbot
```

If needed, the exact freeze used during packaging is also available:

```bash
pip install -r requirements_artifact.txt
```

## Reviewer-First Reproduction Paths

Suggested execution order:

1. Run the smoke test to verify the environment and artifact plumbing.
2. Reproduce the auxiliary public NSL-KDD validation.
3. Reproduce the conditional trust-mass floor hardening package.

Smoke test:

```bash
cd /path/to/HiTrust-FedBot
python core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

Auxiliary public validation:

```bash
cd /path/to/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

Targeted hardening validation:

```bash
cd /path/to/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh
```

## Delivered Paper Outputs

The most directly inspectable paper-facing artifacts are:

- `paper_hitrust/tables/public_nslkdd_trust_vs_keepall_seed_comparison.json`
- `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json`
- `paper_hitrust/tables/scenario_h_update_noise_condfloor_comparison.json`
- `paper_hitrust/figures/public_nslkdd_trust_vs_keepall_seed_comparison.png`
- `paper_hitrust/figures/scenario_h_update_noise_condfloor_comparison.png`
- `paper_hitrust/artifact_manifest_20260324.json`

## Interpretation Boundary

This artifact should be read with the same framing as the manuscript:

- the main value of trust-aware filtering is reducing poisoned participation
- semantic group coverage is treated as a first-class concern
- the auxiliary NSL-KDD path is a cross-domain stress test, not a same-distribution public bot benchmark
- conditional trust-mass floor is a targeted hardening for the identified principal failure mode, not a universal replacement

## Additional Documentation

- `core_experiments/README.md`
- `data_hitrust/README.md`
- `paper_hitrust/README.md`
- `docs/ARTIFACT_RELEASE_20260324.md`
- `docs/DATA_AVAILABILITY_20260324.md`
- `docs/CYBERSECURITY_SUBMISSION_CHECKLIST_20260324.md`
