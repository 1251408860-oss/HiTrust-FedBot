# HiTrust-FedBot

This repository contains the reviewer-facing artifact package for the HiTrust-FedBot study on hierarchical and trust-aware federated Web bot detection under congested edge environments. The public release bundles the executable code, released derived graph artifacts, precomputed paper outputs, and reviewer scripts needed for the supported reproduction path.

## Repository Navigation & Artifact Mapping

| Path | Role in the release |
| --- | --- |
| `core_experiments/` | Main codebase, configs, and reviewer-facing reproduction scripts |
| `data_hitrust/` | Released derived internal graphs and the auxiliary public NSL-KDD graph |
| `paper_hitrust/` | Bundled runs, tables, figures, and manuscript-support materials |
| `environment.yml` | Recommended Conda environment for the public artifact path |
| `RELEASE_CHECKLIST.md` | Release-scope checklist and interpretation constraints |
| `docs/ARTIFACT_STATUS_20260326.md` | Supported versus unsupported reviewer reproduction matrix |

## Global Environment Overview

The artifact was prepared and verified in a Linux/WSL workflow with Python `3.10.19` and the Conda environment name `hitrust-fedbot`. The recommended setup entry is `environment.yml`, while `requirements_artifact.txt` is retained as an exact package freeze from the working environment. No private software dependency is required for the public artifact path. The auxiliary NSL-KDD validation can be rebuilt from a public mirror when needed, but the repository already includes the released derived graph used by the paper workflow.

## Quick Start

```bash
cd /path/to/HiTrust-FedBot
conda env create -f environment.yml
conda activate hitrust-fedbot

bash core_experiments/reproduce/verify_artifact_bundle.sh
python3 core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

The verification script checks the released layout, validates manifest references, syntax-checks the reviewer shell entry points, and verifies the committed SHA-256 manifest. The smoke test then confirms that the packaged environment and repo-local path handling are working.

## Main Reproduction Paths

Reviewers usually choose one of the following public entry points depending on how much of the artifact they want to rerun.

| Scope | Entry point |
| --- | --- |
| Smoke test | `python3 core_experiments/internal/run_hitrust_suite.py --config core_experiments/configs_hitrust/smoke_topology_noniid.json` |
| Auxiliary external validation on NSL-KDD | `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` |
| Conditional trust-mass floor hardening package | `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh` |
| Supported bundled public rerun | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` |

For maintainers, `bash core_experiments/reproduce/package_reviewer_release.sh 20260326` creates a GitHub-Release-ready tarball and matching checksum file under `dist/`.

## Released Artifact Surface

The repository already ships the internal scenario graphs under `data_hitrust/bootstrap_graphs/graphs/`, the public NSL-KDD graph under `data_hitrust/public_benchmarks/nsl_kdd/graphs/`, and the paper-facing runs, tables, and figures under `paper_hitrust/`. Reviewers who prefer to inspect the delivered evidence before rerunning anything should start from `paper_hitrust/artifact_manifest_20260324.json`, `paper_hitrust/tables/`, and `paper_hitrust/figures/`.

## Reproducibility Boundary

The public release supports paper-level reruns from the released derived graphs, reruns of the auxiliary public NSL-KDD path, and reruns of the conditional hardening package. It does not support rebuilding the internal pilot graphs from upstream private raw collection traces. That boundary is intentional and is documented consistently in `RELEASE_CHECKLIST.md`, `docs/DATA_AVAILABILITY_20260324.md`, and `docs/ARTIFACT_STATUS_20260326.md`.

## Additional Documentation

Module-specific execution details are documented in `core_experiments/README.md`, `data_hitrust/README.md`, and `paper_hitrust/README.md`. Release notes and submission-side support files remain under `docs/`.
