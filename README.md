# HiTrust-FedBot

This repository contains the reviewer-facing artifact package for the HiTrust-FedBot study on hierarchical and trust-aware federated Web bot detection under congested edge environments. The current public evidence base spans same-task public Ca-Bench validation on `scenario_e` and `scenario_h`, a full matched adaptive public `2 x 2` matrix over those scenarios, two non-Ca-Bench public raw-data chains (Westermo and LITNET-2020 UDP-flood), matched `sign_flip` attack-family extensions on both public raw-data chains, matched public baseline/provenance comparisons, a public `scenario_h` single-host deployment/runtime package, an auxiliary public NSL-KDD validation path, and a maintainer-side confidential raw-to-graph audit for the released internal bundle.

## Reviewer Start Here

```bash
cd /path/to/HiTrust-FedBot
conda env create -f environment.yml
conda activate hitrust-fedbot

bash core_experiments/reproduce/verify_artifact_bundle.sh
bash core_experiments/reproduce/reproduce_public_paper_bundle.sh
```

`reproduce_public_paper_bundle.sh` is the main reviewer-facing rerun for the current paper package. It rebuilds the public paper-facing tables, figures, and runs in:

- `paper_hitrust/tables/`
- `paper_hitrust/figures/`
- `paper_hitrust/runs/`

It also refreshes the generated public graph/meta outputs under `data_hitrust/public_benchmarks/`.

If you only want a lighter sanity rerun, use:

```bash
bash core_experiments/reproduce/reproduce_reviewer_bundle.sh
```

The light reviewer bundle is not the full paper rerun. It covers the smoke path, optional public Ca-Bench reruns, the NSL-KDD path, and the conditional-floor package.

## Full Public Paper Reproduction Coverage

| Paper claim area | Main script(s) inside the full bundle | Main regenerated outputs |
| --- | --- | --- |
| Same-task public Ca-Bench mainline | `reproduce_public_cabench_validation.sh`, `reproduce_public_cabench_scenario_h_validation.sh` | `paper_hitrust/tables/public_cabench_scenario_e_update_noise_baseline_comparison.json`, `paper_hitrust/tables/public_cabench_scenario_h_update_noise_baseline_comparison.json` |
| Non-Ca-Bench public raw-data width | `reproduce_public_westermo_validation.sh`, `reproduce_public_westermo_sign_flip_validation.sh`, `reproduce_public_litnet2020_udp_validation.sh`, `reproduce_public_litnet2020_udp_sign_flip_validation.sh` | `paper_hitrust/tables/public_westermo_*`, `paper_hitrust/tables/public_litnet2020_udp_*` |
| Adaptive robustness width | `reproduce_public_adaptive_full_matrix_validation.sh` | `paper_hitrust/tables/public_cabench_scenario_{e,h}_adaptive_*_comparison.json` |
| Hardest-setting attack extension | `reproduce_public_cabench_scenario_h_attack_extension.sh` | `paper_hitrust/tables/public_cabench_scenario_h_colluding_update_noise_comparison.json`, `paper_hitrust/tables/public_cabench_scenario_h_multi_round_stealth_comparison.json` |
| Deployment/runtime evidence | `reproduce_public_server_deployment_runtime_package.sh` | `paper_hitrust/tables/public_cabench_scenario_h_deployment_runtime_package.json` |
| Cross-dataset summary figure | `reproduce_cross_dataset_frontier_summary.sh` | `paper_hitrust/tables/cross_dataset_f1_kp_kc_frontier_summary.json`, `paper_hitrust/figures/cross_dataset_f1_kp_kc_frontier_summary.png` |
| Optional auxiliary evidence | `reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh`, `reproduce_public_nslkdd_validation.sh` | `paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json`, `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json` |

Useful toggles for the full public bundle:

- `VERIFY_FIRST=0`: skip the initial bundle verification step
- `INCLUDE_FLTRUST_SENSITIVITY=0`: skip the FLTrust-like sensitivity package
- `INCLUDE_NSLKDD=0`: skip the auxiliary NSL-KDD path

## Entry Point Guide

| Goal | Entry point | When to use it |
| --- | --- | --- |
| Full public paper-facing rerun | `bash core_experiments/reproduce/reproduce_public_paper_bundle.sh` | Main reviewer command for rebuilding the paper-facing public evidence |
| Light reviewer sanity rerun | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` | Faster artifact check; not a full paper rerun |
| Inspect shipped evidence only | inspect `paper_hitrust/tables/`, `paper_hitrust/figures/`, and `paper_hitrust/runs/` | When you want to read the delivered outputs without rerunning |
| Maintainer-only internal raw audit | `bash core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh` | Only when preserved private traces are available locally |

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

## Reproducibility Boundary

The public release supports paper-level reruns from the released derived graphs, reruns of the same-task public Ca-Bench `scenario_e` and `scenario_h` paths, reruns of the public Westermo `update_noise` and `sign_flip` paths, reruns of the public LITNET-2020 UDP-flood `update_noise` and `sign_flip` paths, both the two-anchor adaptive rerun and the full matched adaptive `2 x 2` matrix rerun, the public `scenario_h` runtime benchmark, runtime-scaling package, and single-host deployment/runtime package, reruns of the auxiliary public NSL-KDD path, and reruns of the conditional hardening package. It still does not redistribute the private raw traces behind the internal pilot scenarios. However, maintainers who hold those preserved traces can run `core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh`, which rebuilds all five released internal graphs and checks them against the shipped bundle with exact tensor/hash agreement. That boundary is documented consistently in `RELEASE_CHECKLIST.md`, `docs/DATA_AVAILABILITY_20260324.md`, and `docs/ARTIFACT_STATUS_20260326.md`.

## Additional Documentation

Module-specific execution details are documented in `core_experiments/README.md`, `data_hitrust/README.md`, and `paper_hitrust/README.md`. Release notes and submission-side support files remain under `docs/`, including `docs/INTERNAL_BOOTSTRAP_RAW_AUDIT_20260408.md`, `docs/RUNTIME_SCALING_NOTE_20260408.md`, and `docs/REFERENCE_BASELINE_PROVENANCE_20260407.md`.
