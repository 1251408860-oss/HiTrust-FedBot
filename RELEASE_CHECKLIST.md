# HiTrust-FedBot Release Checklist

This file summarizes what is intentionally included in the public repository and how the artifact should be used.

## Included in the Repository

- executable code under `core_experiments/`
- bundled derived pilot-scenario graphs under `data_hitrust/bootstrap_graphs/graphs/`
- same-task public Ca-Bench scenario package and generated `scenario_e` / `scenario_h` graphs under `data_hitrust/public_benchmarks/cabench_v1/`
- bundled auxiliary public NSL-KDD graph under `data_hitrust/public_benchmarks/nsl_kdd/graphs/`
- precomputed run outputs under `paper_hitrust/runs/`
- paper tables under `paper_hitrust/tables/`
- paper figures under `paper_hitrust/figures/`
- manuscript-support documents under `paper_hitrust/` and `docs/`
- exact package snapshot in `requirements_artifact.txt`
- suggested conda environment in `environment.yml`
- reviewer checksum manifest in `docs/reviewer_bundle_sha256_20260326.txt`
- reviewer integrity notes in `docs/ARTIFACT_STATUS_20260326.md`
- EAAI submission templates and checklist under `docs/EAAI_*_20260327.md`
- maintainer packaging script in `core_experiments/reproduce/package_reviewer_release.sh`
- reviewer integrity verification script in `core_experiments/reproduce/verify_artifact_bundle.sh`

## Intentionally Excluded from Version Control

- Python cache directories
- local build logs
- duplicate figure mirror directory `paper_hitrust/figures_sage_main/`
- private raw collection traces used upstream of the released derived pilot graphs

## Reviewer-Facing Entry Order

1. Read `README.md`
2. Inspect `RELEASE_CHECKLIST.md`
3. Inspect `docs/ARTIFACT_STATUS_20260326.md`
4. Create the environment from `environment.yml`
5. Run `bash core_experiments/reproduce/verify_artifact_bundle.sh`
6. Run the smoke test
7. Reproduce the same-task public `scenario_e` validation if needed
8. Reproduce the same-task public `scenario_h` validation if needed
9. Reproduce the public `scenario_h` FLTrust-like sensitivity if needed
10. Reproduce the public auxiliary validation if needed
11. Reproduce the conditional-floor hardening package if needed
12. Optionally run `core_experiments/reproduce/reproduce_reviewer_bundle.sh`

## Paper-Interpretation Constraints

The repository is aligned with the current manuscript framing:

- trust-aware filtering should not be described as universally improving F1
- the primary security gain is reducing retained poisoned participation
- semantic group coverage is part of the problem definition, not an afterthought
- NSL-KDD is an auxiliary external-validation point
- same-task public Ca-Bench `scenario_h` is the strongest public hardest-setting stress point in the current repo
- same-task public Ca-Bench `scenario_e` is a cleaner held-out transfer point than NSL-KDD for task transfer
- the FLTrust-like line is an engineered trust-bootstrapping baseline, not a bit-for-bit replication of the original FLTrust release
- conditional trust-mass floor is a targeted hardening for the principal hardest-setting failure mode, not a universal default

## Reproduction Boundary

- The public repository supports rerunning the released paper artifact from bundled derived graphs.
- The checksum manifest covers immutable release files only.
- Mutable rerun outputs under `data_hitrust/public_benchmarks/*/{graphs,meta}`, `paper_hitrust/{runs,tables,figures}`, and generated seed-sweep config directories are expected to change when reviewer scripts are rerun.
- The repository does not support reconstructing the internal pilot graphs from private upstream raw collection traces, because those traces are not part of the public release.

## Ca-Bench-Style Hardening

- `core_experiments/reproduce/generate_reviewer_checksums.sh` refreshes the SHA-256 manifest for the static public artifact surface.
- `core_experiments/reproduce/verify_artifact_bundle.sh` checks release completeness before a reviewer rerun and verifies mutable evidence directories by layout rather than by output checksums.
- `core_experiments/reproduce/check_anonymization_leaks.sh` scans submission-facing markdown for obvious anonymization leaks.
- `core_experiments/reproduce/package_reviewer_release.sh` creates a GitHub-Release-ready tarball and checksum file for maintainers.
- This matches the Ca-Bench-style reviewer delivery pattern for the public artifact surface, while still keeping the private raw-data boundary explicit.

## Minimal Release Sanity Checks

- `README.md` points to the correct environment and reproduction scripts
- `environment.yml` and `requirements_artifact.txt` are both present
- bundled internal graphs, both public Ca-Bench graphs, tables, figures, and runs exist in the expected directories
- logs and duplicate figure mirrors are not tracked
- the public repository does not contain obvious secrets or private credentials
