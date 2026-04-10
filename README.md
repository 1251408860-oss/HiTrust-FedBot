# HiTrust-FedBot

This repository contains the reviewer-facing artifact package for the HiTrust-FedBot study on hierarchical and trust-aware federated Web bot detection under congested edge environments. The current evidence base spans topology-aware pilot scenarios, a maintainer-side confidential raw-to-graph audit for the released internal bundle, same-task public Ca-Bench validation on `scenario_e` and `scenario_h`, two non-Ca-Bench public raw-data chains (Westermo and LITNET-2020 UDP-flood), a Westermo `sign_flip` attack-family extension, matched public baseline/provenance comparisons, a public `scenario_h` server-runtime scaling package, and an auxiliary public NSL-KDD validation path.

## Repository Navigation & Artifact Mapping

| Path | Role in the release |
| --- | --- |
| `core_experiments/` | Main codebase, configs, and reviewer-facing reproduction scripts |
| `data_hitrust/` | Released derived internal graphs plus public Ca-Bench, Westermo, LITNET-2020, and NSL-KDD graph artifacts |
| `paper_hitrust/` | Bundled runs, tables, figures, and manuscript-support materials |
| `environment.yml` | Recommended Conda environment for the public artifact path |
| `RELEASE_CHECKLIST.md` | Release-scope checklist and interpretation constraints |
| `docs/ARTIFACT_STATUS_20260326.md` | Supported versus unsupported reviewer reproduction matrix |

## Global Environment Overview

The artifact was prepared and verified in a Linux/WSL workflow with Python `3.10.19` and the Conda environment name `hitrust-fedbot`. The recommended setup entry is `environment.yml`, while `requirements_artifact.txt` is retained as an exact package freeze from the working environment. No private software dependency is required for the public artifact path. Same-task Ca-Bench public scenarios, the Westermo and LITNET-2020 raw-data paths, and the auxiliary NSL-KDD validation can all be rebuilt from public mirrors when needed.

## Quick Start

```bash
cd /path/to/HiTrust-FedBot
conda env create -f environment.yml
conda activate hitrust-fedbot

bash core_experiments/reproduce/verify_artifact_bundle.sh
python3 core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

The verification script checks the released layout, validates manifest references, syntax-checks the reviewer shell entry points, and verifies the committed SHA-256 manifest for the static release surface. Public reruns overwrite generated graphs, runs, tables, and figures in place, so the mutable evidence directories are validated by presence rather than by content hash. Run verification before rerunning experiments, or use a fresh clone if you want to compare against the shipped derived outputs.

## Main Reproduction Paths

Reviewers usually choose one of the following public entry points depending on how much of the artifact they want to rerun.

| Scope | Entry point |
| --- | --- |
| Smoke test | `python3 core_experiments/internal/run_hitrust_suite.py --config core_experiments/configs_hitrust/smoke_topology_noniid.json` |
| Same-task public held-out validation (Ca-Bench `scenario_e`) | `bash core_experiments/reproduce/reproduce_public_cabench_validation.sh` |
| Same-task public hardest validation (Ca-Bench `scenario_h`) | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh` |
| Non-Ca-Bench public raw-data validation (Westermo `update_noise`) | `bash core_experiments/reproduce/reproduce_public_westermo_validation.sh` |
| Non-Ca-Bench public second attack-family validation (Westermo `sign_flip`) | `bash core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh` |
| Non-Ca-Bench public raw-data validation (LITNET-2020 UDP-flood `update_noise`) | `bash core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh` |
| Cross-dataset F1 / KP / KC frontier summary figure | `bash core_experiments/reproduce/reproduce_cross_dataset_frontier_summary.sh` |
| Public `scenario_h` non-adaptive attack-extension package | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh` |
| Minimal public `scenario_h` server runtime benchmark | `bash core_experiments/reproduce/reproduce_public_server_runtime_benchmark.sh` |
| Public `scenario_h` server runtime scaling (10/20/40 clients) | `bash core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh` |
| FLTrust-like sensitivity on public hardest `scenario_h` | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh` |
| Auxiliary external validation on NSL-KDD | `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` |
| Conditional trust-mass floor hardening package | `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh` |
| Maintainer-only internal raw audit (private traces required) | `bash core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh` |
| Supported bundled public rerun | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` |

The bundled rerun keeps the public Ca-Bench paths opt-in. Use `WITH_PUBLIC_CABENCH=1 bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` when you explicitly want those same-task public scenario reruns as part of the bundle flow.

For maintainers, `bash core_experiments/reproduce/package_reviewer_release.sh 20260326` creates a GitHub-Release-ready tarball and matching checksum file under `dist/`.

## Released Artifact Surface

The repository already ships the internal scenario graphs under `data_hitrust/bootstrap_graphs/graphs/`, generated public-benchmark outputs under `data_hitrust/public_benchmarks/`, and the paper-facing runs, tables, and figures under `paper_hitrust/`. Reviewers who prefer to inspect the delivered evidence before rerunning anything should start from `paper_hitrust/artifact_manifest_20260324.json`, `paper_hitrust/tables/`, and `paper_hitrust/figures/`.

The committed checksum manifest in `docs/reviewer_bundle_sha256_20260326.txt` intentionally covers only immutable release files such as source code, configs, docs, manuscript-support markdown, and released static inputs. It does not hash mutable derived outputs under `data_hitrust/public_benchmarks/*/{graphs,meta}` or `paper_hitrust/{runs,tables,figures}`, because those locations are rewritten by the public rerun scripts.

## Reproducibility Boundary

The public release supports paper-level reruns from the released derived graphs, reruns of the same-task public Ca-Bench `scenario_e` and `scenario_h` paths, reruns of the public Westermo `update_noise` and `sign_flip` paths, reruns of the public LITNET-2020 UDP-flood `update_noise` path, the public `scenario_h` runtime benchmark and runtime-scaling package, reruns of the auxiliary public NSL-KDD path, and reruns of the conditional hardening package. It still does not redistribute the private raw traces behind the internal pilot scenarios. However, maintainers who hold those preserved traces can now run `core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh`, which rebuilds all five released internal graphs and checks them against the shipped bundle with exact tensor/hash agreement. That boundary is documented consistently in `RELEASE_CHECKLIST.md`, `docs/DATA_AVAILABILITY_20260324.md`, and `docs/ARTIFACT_STATUS_20260326.md`.

## Additional Documentation

Module-specific execution details are documented in `core_experiments/README.md`, `data_hitrust/README.md`, and `paper_hitrust/README.md`. Release notes and submission-side support files remain under `docs/`, including `docs/INTERNAL_BOOTSTRAP_RAW_AUDIT_20260408.md`, `docs/RUNTIME_SCALING_NOTE_20260408.md`, and `docs/REFERENCE_BASELINE_PROVENANCE_20260407.md`.
