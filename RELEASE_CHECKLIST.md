# HiTrust-FedBot Release Checklist

This file summarizes what is intentionally included in the public repository and how the artifact should be used.

## Included in the Repository

- executable code under `core_experiments/`
- bundled derived pilot-scenario graphs under `data_hitrust/bootstrap_graphs/graphs/`
- bundled auxiliary public NSL-KDD graph under `data_hitrust/public_benchmarks/nsl_kdd/graphs/`
- precomputed run outputs under `paper_hitrust/runs/`
- paper tables under `paper_hitrust/tables/`
- paper figures under `paper_hitrust/figures/`
- manuscript-support documents under `paper_hitrust/` and `docs/`
- exact package snapshot in `requirements_artifact.txt`
- suggested conda environment in `environment.yml`

## Intentionally Excluded from Version Control

- Python cache directories
- local build logs
- duplicate figure mirror directory `paper_hitrust/figures_sage_main/`
- private raw collection traces used upstream of the released derived pilot graphs

## Reviewer-Facing Entry Order

1. Read `README.md`
2. Inspect `RELEASE_CHECKLIST.md`
3. Create the environment from `environment.yml`
4. Run the smoke test
5. Reproduce the public auxiliary validation if needed
6. Reproduce the conditional-floor hardening package if needed
7. Optionally run `core_experiments/reproduce/reproduce_reviewer_bundle.sh`

## Paper-Interpretation Constraints

The repository is aligned with the current manuscript framing:

- trust-aware filtering should not be described as universally improving F1
- the primary security gain is reducing poisoned participation
- semantic group coverage is part of the problem definition, not an afterthought
- NSL-KDD is an auxiliary external-validation point
- conditional trust-mass floor is a targeted hardening for the principal failure mode

## Reproduction Boundary

- The public repository supports rerunning the released paper artifact from bundled derived graphs.
- The repository does not support reconstructing the internal pilot graphs from private upstream raw collection traces, because those traces are not part of the public release.

## Minimal Release Sanity Checks

- `README.md` points to the correct environment and reproduction scripts
- `environment.yml` and `requirements_artifact.txt` are both present
- bundled graphs, tables, figures, and runs exist in the expected directories
- logs and duplicate figure mirrors are not tracked
- the public repository does not contain obvious secrets or private credentials
