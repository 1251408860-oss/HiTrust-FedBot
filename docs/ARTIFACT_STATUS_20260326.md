# HiTrust-FedBot Artifact Status (updated 2026-03-30)

## Reviewer Reproduction Matrix

| Target | Public status | Reviewer entry point | Notes |
| --- | --- | --- | --- |
| Environment and path smoke test | supported | `python core_experiments/internal/run_hitrust_suite.py --config core_experiments/configs_hitrust/smoke_topology_noniid.json` | Confirms the packaged environment and repo-local path resolution |
| Artifact layout and static checksum verification | supported | `bash core_experiments/reproduce/verify_artifact_bundle.sh` | Confirms that the immutable release files, manifest references, and shell entry points are intact |
| Paper reruns from released derived graphs | supported | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` | Uses bundled internal scenario graphs already shipped in the repository |
| Same-task public held-out validation on Ca-Bench `scenario_e` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_validation.sh` | Public topology-aware bot-detection scenario with cleaner transfer semantics than NSL-KDD |
| Same-task public hardest validation on Ca-Bench `scenario_h` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh` | Public hardest-setting stress point used for the main FLTrust-like and hardening discussion |
| FLTrust-like sensitivity on public `scenario_h` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh` | Rebuilds the trusted-root sensitivity grid used to qualify the FLTrust-like comparison |
| Auxiliary external validation on public NSL-KDD | supported | `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` | Public cross-domain stress test, not a same-distribution public bot benchmark |
| Conditional trust-mass floor hardening package | supported | `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh` | Targeted mitigation for the identified failure mode |
| Anonymous submission leakage scan | supported | `bash core_experiments/reproduce/check_anonymization_leaks.sh` | Heuristic scan for emails/author-affiliation metadata fields in submission-facing markdown |
| Direct inspection of precomputed evidence | supported | inspect `paper_hitrust/tables/`, `paper_hitrust/figures/`, and `paper_hitrust/runs/` | The release already includes the paper-facing outputs |
| Rebuild internal pilot graphs from upstream private raw traces | not supported in the public release | not available | The private raw collection traces are not redistributed |

## Relation to the Ca-Bench Release Pattern

Ca-Bench solves reviewer reproducibility by making the public artifact surface self-contained and easy to verify. HiTrust-FedBot now mirrors that pattern on the public side through:

- a single reviewer verification entry point
- a committed SHA-256 manifest for the immutable release surface
- a maintainer-side packaging script that produces a GitHub-Release-ready tarball and checksum
- an anonymization leak scanner for the submission-facing markdown package
- an explicit supported-versus-unsupported reproduction table

Mutable reviewer outputs are handled differently on purpose. Public reruns rewrite `data_hitrust/public_benchmarks/*/{graphs,meta}` and `paper_hitrust/{runs,tables,figures}` in place, so those directories are verified by layout and manifest references rather than by frozen output checksums.

The remaining difference from a fully public benchmark release is structural rather than editorial: HiTrust-FedBot still has a private-data boundary upstream of the released internal pilot graphs, so full raw-data regeneration is not a truthful public claim.

## Maintainer Release Steps

1. Refresh the static checksum manifest:

```bash
bash core_experiments/reproduce/generate_reviewer_checksums.sh
```

2. Verify the full reviewer bundle:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

The verification step should be run before any public reruns, or from a fresh clone, if you want the shipped derived outputs to remain directly comparable to the repository state.

3. Create the release tarball and release checksum:

```bash
bash core_experiments/reproduce/package_reviewer_release.sh 20260326
```

4. Upload the generated `dist/*.tar.gz` and `dist/*.sha256` files to a GitHub Release.
