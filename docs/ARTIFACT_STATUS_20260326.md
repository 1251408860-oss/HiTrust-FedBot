# HiTrust-FedBot Artifact Status (2026-03-26)

## Reviewer Reproduction Matrix

| Target | Public status | Reviewer entry point | Notes |
| --- | --- | --- | --- |
| Environment and path smoke test | supported | `python core_experiments/internal/run_hitrust_suite.py --config core_experiments/configs_hitrust/smoke_topology_noniid.json` | Confirms the packaged environment and repo-local path resolution |
| Artifact layout and checksum verification | supported | `bash core_experiments/reproduce/verify_artifact_bundle.sh` | Confirms that the released files, manifest references, and shell entry points are intact |
| Paper reruns from released derived graphs | supported | `bash core_experiments/reproduce/reproduce_reviewer_bundle.sh` | Uses bundled internal scenario graphs already shipped in the repository |
| Auxiliary external validation on public NSL-KDD | supported | `bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh` | Public cross-domain stress test, not a same-distribution public bot benchmark |
| Conditional trust-mass floor hardening package | supported | `bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh` | Targeted mitigation for the identified failure mode |
| Direct inspection of precomputed evidence | supported | inspect `paper_hitrust/tables/`, `paper_hitrust/figures/`, and `paper_hitrust/runs/` | The release already includes the paper-facing outputs |
| Rebuild internal pilot graphs from upstream private raw traces | not supported in the public release | not available | The private raw collection traces are not redistributed |

## Relation to the Ca-Bench Release Pattern

Ca-Bench solves reviewer reproducibility by making the public artifact surface self-contained and easy to verify. HiTrust-FedBot now mirrors that pattern on the public side through:

- a single reviewer verification entry point
- a committed SHA-256 manifest for the released artifact surface
- a maintainer-side packaging script that produces a GitHub-Release-ready tarball and checksum
- an explicit supported-versus-unsupported reproduction table

The remaining difference is structural rather than editorial: HiTrust-FedBot still has a private-data boundary upstream of the released internal pilot graphs, so full raw-data regeneration is not a truthful public claim.

## Maintainer Release Steps

1. Refresh the checksum manifest:

```bash
bash core_experiments/reproduce/generate_reviewer_checksums.sh
```

2. Verify the full reviewer bundle:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

3. Create the release tarball and release checksum:

```bash
bash core_experiments/reproduce/package_reviewer_release.sh 20260326
```

4. Upload the generated `dist/*.tar.gz` and `dist/*.sha256` files to a GitHub Release.
