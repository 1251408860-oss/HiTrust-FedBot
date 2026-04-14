# Runtime Scaling Note (updated 2026-04-14)

This note records the current single-host runtime evidence for the public hardest-setting path. The older scaling table still exists, but the paper-facing runtime story now comes from the deployment/runtime package built on top of the same `10/20/40/80`-client seed runs.

## Primary Entry Point

- script: `core_experiments/reproduce/reproduce_public_server_deployment_runtime_package.sh`
- output table: `paper_hitrust/tables/public_cabench_scenario_h_deployment_runtime_package.json`
- output figure: `paper_hitrust/figures/public_cabench_scenario_h_deployment_runtime_package.png`
- paper-ready copy: `paper_hitrust/figures_sage_main/public_cabench_scenario_h_deployment_runtime_package.png`

## Upstream Seed Data

- seed-run driver: `core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh`
- scaling table: `paper_hitrust/tables/public_cabench_scenario_h_server_runtime_scaling.json`
- scaling figure: `paper_hitrust/figures/public_cabench_scenario_h_server_runtime_scaling.png`

## Scope

- dataset / setting: public Ca-Bench `scenario_h + update_noise@0.4`
- methods: static, `condfloor`, keep-all
- seeds: `11,22,33,44,55`
- active-client counts: `10`, `20`, `40`, `80`
- reported runtime fields: round wall clock, local training, client evaluation, server round, aggregation, bytes per round, and peak RSS

## Main Observations

- Static line:
  - round wall clock rises from `56.34` to `97.47` to `207.0` to `504.36 ms`
  - local training rises from `26.19` to `44.28` to `102.98` to `235.51 ms`
  - client evaluation rises from `25.09` to `47.58` to `96.37` to `253.61 ms`
  - server round rises from `29.64` to `52.45` to `102.67` to `266.08 ms`
  - aggregation rises from `0.71` to `1.22` to `2.40` to `7.04 ms`
  - peak RSS stays near `830 MB`
  - bytes per round scale linearly from `24.14` to `48.28` to `96.56` to `193.12 KiB`

- `condfloor` and keep-all lines:
  - remain in the same timing band as the static line through `80` clients
  - keep aggregation within about `0.65-7.04 ms`
  - keep peak RSS within roughly `821-830 MB`
  - preserve the same near-linear bytes-per-round scaling

## Interpretation

The new package is stronger than the earlier reviewer-scale runtime note because it exposes where time is spent, not only that server-side cost scales with client count. Aggregation remains a small part of the measured server round, about `2.2%-2.6%` across the tested client counts, which supports the claim that the trust-aware control logic does not dominate the measured runtime. The remaining limitation is unchanged: this is still a single-host deployment/runtime study, not a distributed multi-host latency benchmark.
