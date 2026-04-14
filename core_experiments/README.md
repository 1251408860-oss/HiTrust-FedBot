# `core_experiments/`

This directory contains the executable code, configuration files, and reproduction entry points used by the HiTrust-FedBot artifact.

## Main Subdirectories

- `configs_hitrust/`: runnable experiment configs, seed sweeps, and grid manifests
- `internal/`: implementation code for training, trust scoring, aggregation, graph building, and table generation
- `reproduce/`: reviewer-facing shell entry points for the main reproduction paths

## Reviewer-First Entry Points

Full public paper-facing rerun:

```bash
bash core_experiments/reproduce/reproduce_public_paper_bundle.sh
```

This is the main reviewer command for rebuilding the current public paper package. It runs bundle verification, the Ca-Bench `scenario_e` / `scenario_h` mainlines, the Westermo and LITNET-2020 raw-data chains with both promoted attack families, the full adaptive `2 x 2` matrix, the `scenario_h` attack-extension package, the single-host deployment/runtime package, and the cross-dataset frontier summary. By default it also includes the FLTrust-like sensitivity package and the auxiliary NSL-KDD path.

Useful toggles:

```bash
VERIFY_FIRST=0 bash core_experiments/reproduce/reproduce_public_paper_bundle.sh
INCLUDE_FLTRUST_SENSITIVITY=0 bash core_experiments/reproduce/reproduce_public_paper_bundle.sh
INCLUDE_NSLKDD=0 bash core_experiments/reproduce/reproduce_public_paper_bundle.sh
```

Light reviewer bundle:

```bash
bash core_experiments/reproduce/reproduce_reviewer_bundle.sh
```

This is a quicker artifact sanity path, not the full paper rerun. It covers the smoke path, optional public Ca-Bench reruns, the NSL-KDD path, and the conditional-floor package.

## Standalone Entry Points

Smoke test:

```bash
python core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json
```

Same-task public held-out validation (`scenario_e`):

```bash
bash core_experiments/reproduce/reproduce_public_cabench_validation.sh
```

The public Ca-Bench same-task reruns now default to a 20-seed primary sweep (`11..222`) and skip already-completed runs unless `SKIP_EXISTING=0` is set.

Same-task public hardest validation (`scenario_h`):

```bash
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh
```

Non-Ca-Bench public raw-data validation (Westermo `update_noise` and supportive `sign_flip`):

```bash
bash core_experiments/reproduce/reproduce_public_westermo_validation.sh
bash core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh
```

The Westermo reruns use matched 20-seed public sweeps by default and rebuild the paired comparison tables used for the paper-facing non-Ca-Bench evidence.

Non-Ca-Bench public raw-data validation (LITNET-2020 UDP-flood `update_noise` and supportive `sign_flip`):

```bash
bash core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh
bash core_experiments/reproduce/reproduce_public_litnet2020_udp_sign_flip_validation.sh
```

The LITNET-2020 reruns default to matched 20-seed sweeps. The `update_noise` entry point rebuilds the main trust-vs-baseline comparison and the `condfloor`-focused comparison, while the `sign_flip` entry point widens the same raw-data chain to a second non-adaptive attack family.

Cross-dataset F1 / KP / KC frontier summary:

```bash
bash core_experiments/reproduce/reproduce_cross_dataset_frontier_summary.sh
```

This figure aggregates the primary public non-adaptive tables into a single cross-dataset bubble-frontier plot with `KP` on the x-axis, `F1` on the y-axis, and bubble area proportional to `KC`.

Public hardest attack-extension validation (`scenario_h` targeted/colluding/multi-round):

```bash
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh
```

Promoted matched adaptive validation (`scenario_h + adaptive_benign_mimic`, `scenario_e + adaptive_alie_like`):

```bash
bash core_experiments/reproduce/reproduce_public_adaptive_matched_validation.sh
```

Full matched adaptive `2 x 2` matrix validation:

```bash
bash core_experiments/reproduce/reproduce_public_adaptive_full_matrix_validation.sh
```

This wrapper rebuilds all four public adaptive scenario/attack combinations with matched 20-seed sweeps: `scenario_h + adaptive_benign_mimic`, `scenario_h + adaptive_alie_like`, `scenario_e + adaptive_benign_mimic`, and `scenario_e + adaptive_alie_like`.

FLTrust-like sensitivity on public hardest `scenario_h`:

```bash
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh
```

Single-host deployment/runtime package on public hardest `scenario_h`:

```bash
bash core_experiments/reproduce/reproduce_public_server_deployment_runtime_package.sh
```

This entry point aggregates the `10/20/40/80`-client runtime seed sweeps into the paper-facing deployment/runtime summary with wall-clock time, local training time, client evaluation time, server-round time, bytes per round, and peak RSS.

Auxiliary cross-domain validation:

```bash
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

The auxiliary NSL-KDD rerun follows the same 10-seed default sweep and supports `SKIP_EXISTING=1` for incremental backfills.

The local experiment semantics are defined in `docs/EXPERIMENT_DESIGN_CONTRACT_20260407.md`. Method provenance, benchmark tiering, attack families, and primary versus exploratory statistics now come from `core_experiments/internal/experiment_registry.py` rather than from filename conventions alone.

Conditional-floor hardening:

```bash
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh
```

Artifact integrity verification:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

The verification entry point hashes only immutable release files. The public rerun scripts regenerate outputs in `data_hitrust/public_benchmarks/*/{graphs,meta}`, `paper_hitrust/runs`, `paper_hitrust/tables`, and `paper_hitrust/figures`, so those paths are validated by presence and manifest references rather than by fixed output checksums.

Bundled reviewer rerun:

```bash
bash core_experiments/reproduce/reproduce_reviewer_bundle.sh
```

The bundled rerun keeps the public Ca-Bench paths opt-in by default. Set `WITH_PUBLIC_CABENCH=1` when you explicitly want to include the same-task public scenario reruns, but use `reproduce_public_paper_bundle.sh` when you want the full paper-facing public rebuild.

Maintainer packaging for a GitHub Release:

```bash
bash core_experiments/reproduce/package_reviewer_release.sh 20260326
```
