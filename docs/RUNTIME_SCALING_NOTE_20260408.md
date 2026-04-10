# Runtime Scaling Note (2026-04-08)

This note records the updated server-side runtime evidence for the public hardest-setting path.

## Entry Point

- script:
  - `core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh`
- output table:
  - `paper_hitrust/tables/public_cabench_scenario_h_server_runtime_scaling.json`
- output figure:
  - `paper_hitrust/figures/public_cabench_scenario_h_server_runtime_scaling.png`

## Scope

- dataset / setting:
  - public Ca-Bench `scenario_h + update_noise@0.4`
- methods:
  - static
  - `condfloor`
  - keep-all
- seeds:
  - `11,22,33,44,55`
- configured active-client counts:
  - `10`
  - `20`
  - `40`

## Main Observations

- static line:
  - server-round mean rises from `29.6 ms` to `52.5 ms` to `102.7 ms`
  - aggregation mean rises from `0.71 ms` to `1.22 ms` to `2.40 ms`
  - round wall-clock mean rises from `56.3 ms` to `97.5 ms` to `207.0 ms`
  - peak RSS stays in a narrow `822.7-823.4 MB` band

- `condfloor` line:
  - server-round mean rises from `29.4 ms` to `52.2 ms` to `106.9 ms`
  - aggregation mean remains within `0.65-2.45 ms`
  - peak RSS stays within `822.6-827.9 MB`

- keep-all line:
  - server-round mean rises from `28.0 ms` to `53.6 ms` to `100.8 ms`
  - aggregation mean remains within `0.65-2.44 ms`
  - peak RSS stays within `821.1-825.4 MB`

## Interpretation

The runtime story is now stronger than the earlier reviewer-scale `10`-client table because it includes explicit client-count scaling and peak memory. The remaining limitation is that this is still a single-host server-side study rather than a distributed multi-host latency benchmark.
