# Artifact Release Notes (2026-03-24)

This repository now includes a reproducible auxiliary public-benchmark validation path in addition to the main topology-aware pilot scenarios.

## Environment

- Recommended Python: `/home/user/miniconda3/envs/DL/bin/python`
- Core packages used in the artifact path:
  - `torch`
  - `torch_geometric`
  - `scikit-learn`
  - `pandas`
  - `matplotlib`
  - `scipy`

## Public External Validation

Reproduce the public NSL-KDD auxiliary validation with:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

This script performs four steps:

1. Downloads the public NSL-KDD train/test files from a public mirror.
2. Builds a feature-similarity graph compatible with the existing GraphSAGE federated pipeline.
3. Re-runs the trust-aware, keep-all, and standard aggregation baselines.
4. Rebuilds the paper tables and figures for the public validation section.

## Conditional-Floor Hardening Validation

Reproduce the conditional trust-mass floor validation with:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh
```

This script reproduces the targeted hardening package used in the manuscript:

1. Re-runs the `scenario_h` clean, sign-flip, and update-noise seed sweeps for both the static and conditional-floor variants.
2. Re-runs the held-out `scenario_e + update_noise@0.4` comparison.
3. Re-runs the auxiliary public NSL-KDD `update_noise@0.4` comparison.
4. Rebuilds the comparison tables and figures used to discuss the conditional floor as a targeted extension rather than as a universal replacement.

## Key Outputs

- Public graph:
  - `data_hitrust/public_benchmarks/nsl_kdd/graphs/nsl_kdd_public_graph.pt`
- Data build summary:
  - `data_hitrust/public_benchmarks/nsl_kdd/meta/nsl_kdd_public_build_summary.json`
- Trust-aware vs keep-all report:
  - `paper_hitrust/tables/public_nslkdd_trust_vs_keepall_seed_comparison.json`
  - `paper_hitrust/figures/public_nslkdd_trust_vs_keepall_seed_comparison.png`
- Update-noise baseline comparison:
  - `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json`
  - `paper_hitrust/figures/public_nslkdd_update_noise_baseline_comparison.png`
- Conditional-floor hardening comparisons:
  - `paper_hitrust/tables/scenario_h_update_noise_condfloor_comparison.json`
  - `paper_hitrust/figures/scenario_h_update_noise_condfloor_comparison.png`
  - `paper_hitrust/tables/scenario_e_update_noise_condfloor_comparison.json`
  - `paper_hitrust/figures/scenario_e_update_noise_condfloor_comparison.png`
  - `paper_hitrust/tables/public_nslkdd_update_noise_condfloor_comparison.json`
  - `paper_hitrust/figures/public_nslkdd_update_noise_condfloor_comparison.png`

## Intended Paper Use

This public benchmark is an auxiliary external-validation point. It is not a replacement for the main topology-aware pilot scenarios. The appropriate interpretation is:

- the trust-aware mechanism transfers to a public cyber-security dataset;
- the main security gain is reduced retained poisoned participation;
- accuracy should be discussed as near-neutral on average rather than universally improved.

The conditional trust-mass floor should be interpreted more narrowly:

- it is a targeted hardening for the identified small-group-collapse failure mode on the topology-aware mainline;
- it is near-neutral on the held-out `scenario_e` validation;
- its public NSL-KDD behavior is mixed, so it should not be presented as a universal replacement for the static trust-aware mainline.
