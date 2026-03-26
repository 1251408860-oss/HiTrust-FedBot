# HiTrust-FedBot

Hierarchical and trust-aware federated Web bot detection under congested edge environments.

This repository is organized as a paper artifact and reviewer-facing reproduction package for the HiTrust-FedBot study.

## Reviewer Quick Start

Recommended environment:

- Python environment used in the artifact path: `/home/user/miniconda3/envs/DL`
- Full package freeze: `requirements_artifact.txt`

Suggested first steps:

1. Run the smoke test to confirm the local environment and artifact plumbing.
2. Reproduce the auxiliary public NSL-KDD validation.
3. Reproduce the conditional-floor hardening package.

Smoke test:

```bash
cd /home/user/workspace/HiTrust-FedBot
/home/user/miniconda3/envs/DL/bin/python \
  core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

Auxiliary public validation:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

Targeted hardening validation:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh
```

## Repository Layout

- `core_experiments/`: experimental code, configs, sweeps, and reproduction scripts
- `data_hitrust/`: scenario graphs, public-benchmark data, and metadata
- `paper_hitrust/`: precomputed runs, tables, figures, and manuscript-support artifacts
- `docs/`: artifact-release notes and submission-support documents
- `tests/`: focused regression tests for recent risk fixes

## Included Artifact Outputs

The repository already contains the prebuilt artifacts used by the paper workflow, including:

- topology-aware bootstrap graph files under `data_hitrust/bootstrap_graphs/graphs/`
- auxiliary public NSL-KDD graph under `data_hitrust/public_benchmarks/nsl_kdd/graphs/`
- paper tables under `paper_hitrust/tables/`
- paper figures under `paper_hitrust/figures/`

These files are kept in the repository so reviewers can inspect the delivered results directly before deciding whether to rerun the full pipelines.

## Reproduction Scope

This codebase is the method-paper branch. Its primary claims are organized around:

- reducing poisoned participation under trust-aware filtering
- preserving semantic group coverage under topology-aware federation
- diagnosing the principal failure mode of static group floors
- validating conditional trust-mass floor as a targeted hardening rather than a universal replacement

The public NSL-KDD path is included as an auxiliary external-validation stress test. It is not intended to replace the main topology-aware pilot scenarios.

## Supporting Documents

- Artifact notes: `docs/ARTIFACT_RELEASE_20260324.md`
- Data availability notes: `docs/DATA_AVAILABILITY_20260324.md`
- Submission checklist: `docs/CYBERSECURITY_SUBMISSION_CHECKLIST_20260324.md`
- Cover-letter draft: `docs/CYBERSECURITY_COVER_LETTER_20260324.md`
- Title-page template: `docs/CYBERSECURITY_TITLE_PAGE_TEMPLATE_20260324.md`
