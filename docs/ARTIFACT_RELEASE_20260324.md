# Artifact Release Notes (2026-03-24)

This repository now includes reproducible same-task public-benchmark validation paths for Ca-Bench `scenario_e` and `scenario_h`, a public-hardest FLTrust-like sensitivity path on `scenario_h`, and an auxiliary cross-domain public-benchmark path (NSL-KDD), in addition to the main topology-aware pilot scenarios.

## Environment

- Recommended Python: `/home/user/miniconda3/envs/DL/bin/python`
- Core packages used in the artifact path:
  - `torch`
  - `torch_geometric`
  - `scikit-learn`
  - `pandas`
  - `matplotlib`
  - `scipy`

## Public Same-Task External Validation (Ca-Bench `scenario_e`)

Reproduce the public same-task scenario validation with:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_cabench_validation.sh
```

This script performs four steps:

1. Downloads and integrity-checks the public `Ca-Bench data-v1` release archive.
2. Builds a graph from the public `scenario_e_three_tier_high2` capture with the released Ca-Bench graph builder.
3. Re-runs trust-aware, keep-all, and standard aggregation baselines on the same-task public scenario.
4. Rebuilds the paper tables and figures for this same-task external-validation section.

## Public Same-Task Hardest Validation (Ca-Bench `scenario_h`)

Reproduce the public same-task hardest-setting validation with:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh
```

This script performs five steps:

1. Downloads and integrity-checks the public `Ca-Bench data-v1` release archive if needed.
2. Builds a graph from the public `scenario_h_mimic_heavy_overlap` capture with the released Ca-Bench graph builder.
3. Re-runs trust-aware, conditional-floor, FLTrust-like, keep-all, and classical aggregation baselines on the same-task public hardest scenario.
4. Rebuilds the baseline-comparison and conditional-hardening tables and figures used in the manuscript.
5. Refreshes the shipped `paper_hitrust` outputs for the public hardest-setting discussion.

## FLTrust-like Sensitivity on Public `scenario_h`

Reproduce the trusted-root sensitivity sweep with:

```bash
cd /home/user/workspace/HiTrust-FedBot
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh
```

This script performs three steps:

1. Reuses or rebuilds the public `scenario_h` Ca-Bench graph.
2. Re-runs the six shipped FLTrust-like sensitivity points over trusted-root size and local server epochs.
3. Rebuilds the sensitivity table and figure used to qualify the FLTrust-like manuscript comparison.

## Public Auxiliary Validation (NSL-KDD)

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
- Public same-task Ca-Bench graph:
  - `data_hitrust/public_benchmarks/cabench_v1/graphs/cabench_scenario_e_three_tier_high2_public_graph.pt`
- Public same-task hardest Ca-Bench graph:
  - `data_hitrust/public_benchmarks/cabench_v1/graphs/cabench_scenario_h_mimic_heavy_overlap_public_graph.pt`
- Data build summary:
  - `data_hitrust/public_benchmarks/nsl_kdd/meta/nsl_kdd_public_build_summary.json`
- Same-task data build summary:
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_e_three_tier_high2_public_build_summary.json`
- Same-task hardest data build summary:
  - `data_hitrust/public_benchmarks/cabench_v1/meta/cabench_scenario_h_mimic_heavy_overlap_public_build_summary.json`
- Same-task trust-aware vs keep-all report:
  - `paper_hitrust/tables/public_cabench_scenario_e_trust_vs_keepall_seed_comparison.json`
  - `paper_hitrust/figures/public_cabench_scenario_e_trust_vs_keepall_seed_comparison.png`
- Same-task update-noise baseline comparison:
  - `paper_hitrust/tables/public_cabench_scenario_e_update_noise_baseline_comparison.json`
  - `paper_hitrust/figures/public_cabench_scenario_e_update_noise_baseline_comparison.png`
- Same-task hardest trust-aware vs keep-all report:
  - `paper_hitrust/tables/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.json`
  - `paper_hitrust/figures/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.png`
- Same-task hardest update-noise baseline comparison:
  - `paper_hitrust/tables/public_cabench_scenario_h_update_noise_baseline_comparison.json`
  - `paper_hitrust/figures/public_cabench_scenario_h_update_noise_baseline_comparison.png`
- Same-task hardest conditional-floor comparison:
  - `paper_hitrust/tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json`
  - `paper_hitrust/figures/public_cabench_scenario_h_update_noise_condfloor_comparison.png`
- Same-task hardest FLTrust-like sensitivity outputs:
  - `paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json`
  - `paper_hitrust/figures/public_cabench_scenario_h_fltrust_like_sensitivity.png`
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

## Checksum Boundary

`docs/reviewer_bundle_sha256_20260326.txt` now hashes the static release surface only. The reviewer rerun scripts intentionally overwrite generated public graphs, build summaries, run directories, tables, and figures under:

- `data_hitrust/public_benchmarks/*/{graphs,meta}`
- `paper_hitrust/{runs,tables,figures}`

Those paths are therefore verified by directory layout and manifest references rather than by frozen output checksums.

## Intended Paper Use

The same-task Ca-Bench public scenarios are the stronger external points for task transfer, while NSL-KDD remains an auxiliary cross-domain point. Neither path replaces the main topology-aware pilot scenarios. The appropriate interpretation is:

- the trust-aware mechanism transfers to same-task public graph settings and to an auxiliary public cyber-security dataset;
- the strongest claim is reduced retained poisoned participation rather than universal mean-F1 gains;
- FLTrust-like should be discussed as a competitive trust-bootstrapping baseline whose tuned points still retain poisoned clients on the hardest public setting.

The conditional trust-mass floor should be interpreted more narrowly:

- it is a targeted hardening for the identified small-group-collapse failure mode, especially on the same-task public hardest `scenario_h` setting;
- it is not the new default operating point for every benchmark;
- its broader behavior must still be discussed as targeted hardening rather than as a universal replacement for the static trust-aware mainline.
