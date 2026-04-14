# HiTrust-FedBot Artifact Status (updated 2026-04-14)

## Reviewer Reproduction Matrix

| Target | Public status | Reviewer entry point | Notes |
| --- | --- | --- | --- |
| Environment and path smoke test | supported | `python core_experiments/internal/run_hitrust_suite.py --config core_experiments/configs_hitrust/smoke_topology_noniid.json` | Confirms the packaged environment and repo-local path resolution |
| Artifact layout and static checksum verification | supported | `bash core_experiments/reproduce/verify_artifact_bundle.sh` | Confirms that the immutable release files, manifest references, and shell entry points are intact |
| Full public paper-facing rerun | supported | `bash core_experiments/reproduce/reproduce_public_paper_bundle.sh` | Rebuilds the full public paper-facing table and figure package from the supported public rerun paths and writes outputs under `paper_hitrust/` |
| Light reviewer bundle rerun | supported | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` | Uses bundled internal scenario graphs already shipped in the repository; public Ca-Bench reruns stay opt-in via `WITH_PUBLIC_CABENCH=1`; this is a sanity-oriented subset rather than the full paper rerun |
| Same-task public held-out validation on Ca-Bench `scenario_e` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_validation.sh` | Public topology-aware bot-detection scenario built with the vendored Ca-Bench helper pinned to a fixed upstream commit |
| Same-task public hardest validation on Ca-Bench `scenario_h` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh` | Public hardest-setting stress point built under the same repo-local graph contract as the rest of the release |
| Non-Ca-Bench public raw-data validation on Westermo | supported | `bash core_experiments/reproduce/reproduce_public_westermo_validation.sh` | Public raw-data to local graph-contract to result-table chain used as a second primary public evidence path |
| Non-Ca-Bench public second attack-family validation on Westermo `sign_flip` | supported | `bash core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh` | Supportive matched 20-seed second-attack-family sweep on the same public raw-data chain |
| Non-Ca-Bench public raw-data validation on LITNET-2020 UDP-flood | supported | `bash core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh` | Additional matched 20-seed public raw-data to local graph-contract to result-table chain used as a third primary public evidence path |
| Non-Ca-Bench public second attack-family validation on LITNET-2020 UDP-flood `sign_flip` | supported | `bash core_experiments/reproduce/reproduce_public_litnet2020_udp_sign_flip_validation.sh` | Supportive matched 20-seed second-attack-family sweep on the same public raw-data chain |
| Cross-dataset F1 / KP / KC frontier summary figure | supported | `bash core_experiments/reproduce/reproduce_cross_dataset_frontier_summary.sh` | Rebuilds the four-panel cross-dataset public frontier summary from the released comparison tables |
| Public `scenario_h` attack-extension package | supported | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh` | Rebuilds the 20-seed `colluding_update_noise` and `multi_round_stealth` stress-point package |
| Promoted matched adaptive validation | supported | `bash core_experiments/reproduce/reproduce_public_adaptive_matched_validation.sh` | Rebuilds the matched 20-seed `scenario_h + adaptive_benign_mimic@0.4` and `scenario_e + adaptive_alie_like@0.4` tables |
| Full matched adaptive `2 x 2` matrix validation | supported | `bash core_experiments/reproduce/reproduce_public_adaptive_full_matrix_validation.sh` | Rebuilds all four public adaptive scenario/attack combinations with matched 20-seed sweeps |
| Minimal public `scenario_h` server runtime benchmark | supported | `bash core_experiments/reproduce/reproduce_public_server_runtime_benchmark.sh` | Rebuilds the dedicated `runtimebench` runs and the server-runtime comparison table/figure |
| Public `scenario_h` server runtime scaling | supported | `bash core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh` | Rebuilds the 5-seed `10/20/40/80`-client timing and peak-RSS scaling table/figure |
| Public `scenario_h` single-host deployment/runtime package | supported | `bash core_experiments/reproduce/reproduce_public_server_deployment_runtime_package.sh` | Rebuilds the paper-facing single-host deployment/runtime summary from the 5-seed `10/20/40/80`-client runtime runs |
| FLTrust-like sensitivity on public `scenario_h` | supported | `bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh` | Rebuilds the trusted-root sensitivity grid used to qualify the FLTrust-like comparison |
| Auxiliary external validation on public NSL-KDD | supported | `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` | Public cross-domain stress test, not a same-distribution public bot benchmark |
| Conditional trust-mass floor hardening package | supported | `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh` | Targeted mitigation for the identified failure mode |
| Maintainer-side internal raw audit from local private traces | maintainer-only supported | `bash core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh` | Rebuilds all five released internal graphs and verifies exact tensor/hash agreement against the shipped bundle |
| Direct inspection of precomputed evidence | supported | inspect `paper_hitrust/tables/`, `paper_hitrust/figures/`, and `paper_hitrust/runs/` | The release already includes the paper-facing outputs |
| Public rebuild of internal pilot graphs from redistributed private raw traces | not supported in the public release | not available | The private raw collection traces are not redistributed; use the maintainer-side raw-audit path when those traces are available locally |

## Relation to the Ca-Bench Release Pattern

Ca-Bench solves reviewer reproducibility by making the public artifact surface self-contained and easy to verify. HiTrust-FedBot now mirrors that pattern on the public side through:

- a single reviewer verification entry point
- a committed SHA-256 manifest for the immutable release surface
- a maintainer-side packaging script that produces a GitHub-Release-ready tarball and checksum
- an explicit supported-versus-unsupported reproduction table
- a vendored public Ca-Bench builder pinned to a fixed upstream commit rather than a moving upstream branch
- a repo-local graph contract documented in `docs/GRAPH_SCHEMA_CONTRACT_20260407.md`
- two non-Ca-Bench public raw-data validation chains under `data_hitrust/public_benchmarks/westermo/` and `data_hitrust/public_benchmarks/litnet2020/`
- a promoted matched adaptive rerun entry point for the two public adaptive paths carried into the main paper package
- a full matched adaptive `2 x 2` rerun entry point covering both public scenarios and both adaptive attack families
- second Westermo and LITNET attack-family rerun entry points plus a minimal runtime benchmark, a `10/20/40/80`-client runtime scaling package, and a paper-facing single-host deployment/runtime package for the public hardest scenario
- a maintainer-side confidential raw-audit script that exactly rebuilds the released internal graph bundle when the preserved private traces are available locally

Mutable reviewer outputs are handled differently on purpose. Public reruns rewrite `data_hitrust/public_benchmarks/*/{graphs,meta}` and `paper_hitrust/{runs,tables,figures}` in place, so those directories are verified by layout and manifest references rather than by frozen output checksums.

The remaining difference from a fully public benchmark release is now narrower but still structural rather than editorial: HiTrust-FedBot still has a private-data boundary upstream of the released internal pilot graphs, so public raw-data regeneration is not a truthful claim. The new maintainer-side audit path shows that the released internal bundle can nevertheless be regenerated exactly from the preserved private traces. The public evidence is materially broader than in the earlier artifact round because it no longer relies on Ca-Bench alone and now includes two non-Ca-Bench raw-data paths, second-attack-family sweeps on both public raw-data chains, and a single-host deployment/runtime package, but it is still a bounded public evidence surface rather than a complete end-to-end opening of the internal pipeline.

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
