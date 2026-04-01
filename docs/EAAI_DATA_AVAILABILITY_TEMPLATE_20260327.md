# EAAI Data Availability Template (2026-03-27)

## Data Availability Statement

The released artifact includes:

- derived topology-aware pilot scenario graphs under `data_hitrust/bootstrap_graphs/graphs/`
- same-task public Ca-Bench scenario package and generated validation graphs under `data_hitrust/public_benchmarks/cabench_v1/`
- auxiliary cross-domain public NSL-KDD graph artifacts under `data_hitrust/public_benchmarks/nsl_kdd/`
- reproducible scripts for public validation under `core_experiments/reproduce/`

The repository does **not** include upstream private raw collection traces used before deriving the internal pilot graphs. This boundary is explicit in `RELEASE_CHECKLIST.md` and `docs/ARTIFACT_STATUS_20260326.md`.

## Reproduction Entry Points

- `bash core_experiments/reproduce/reproduce_public_cabench_validation.sh`
- `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`
- `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh`
- `bash core_experiments/reproduce/verify_artifact_bundle.sh`
