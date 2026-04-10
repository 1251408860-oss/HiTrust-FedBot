# Internal Bootstrap Raw Audit (2026-04-08)

This note records the maintainer-side audit path for the released internal bootstrap graph bundle.

## Purpose

The public release still does not redistribute the private raw traces behind the five internal pilot scenarios. However, the repository now includes a confidential maintainer-side script that rebuilds those graphs from the preserved raw traces and checks them against the shipped bundle.

## Entry Point

- script:
  - `core_experiments/reproduce/reproduce_internal_bootstrap_raw_audit.sh`
- expected local raw root:
  - `/home/user/workspace/Ca-Bench-temp/mininet_testbed/real_collection`
- local output root:
  - `paper_hitrust/artifacts/internal_bootstrap_raw_audit/`

## Current Audit Result

The current audit rebuild reproduces all five released scenarios:

- `scenario_d_three_tier_low2`
- `scenario_e_three_tier_high2`
- `scenario_f_two_tier_high2`
- `scenario_g_mimic_congest`
- `scenario_h_mimic_heavy_overlap`

Observed result:

- `5 / 5` scenario graphs rebuilt successfully
- `5 / 5` scenario graphs passed exact tensor/hash agreement against `data_hitrust/bootstrap_graphs/graphs/`
- both released and rebuilt graphs passed the local `hitrust_graph_v1` contract validation

## Boundary

This closes the maintainer-side raw-to-graph audit gap for the internal bundle, but it does not change the public redistribution boundary. Reviewers still receive the released derived graphs rather than the private upstream traces.
