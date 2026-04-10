# EAAI Highlights Draft (updated 2026-04-09)

- We propose a trust-aware hierarchical federated GraphSAGE framework for topology-aware web bot detection under edge deployment constraints.
- Primary public evidence uses matched 20-seed paired evaluation on Ca-Bench `scenario_e`, Ca-Bench `scenario_h`, Westermo, and LITNET-2020 UDP-flood public raw-data chains.
- A maintainer-side confidential audit exactly rebuilds the five released internal pilot graphs from preserved private raw traces.
- On public `scenario_h + update_noise@0.4`, `condfloor` reaches `F1 = 0.9746`, `FPR = 0.0307`, and `0.0` retained poisoned clients.
- Modern CAF, `ARC+mean`, and Centered Clipping comparators reach strong `scenario_h` predictive metrics but still retain all `4.0` poisoned clients.
- On the matched 20-seed LITNET-2020 UDP-flood table, `condfloor` reaches `F1 = 0.5856`, `FPR = 0.0464`, and `0.4` retained poisoned clients, while higher-F1 baselines retain `1.75-4.0` poisoned clients.
- Promoted matched 20-seed adaptive evidence shows `temporal_rootguard_v2` reaching `F1 = 0.9884`, `FPR = 0.0168`, and `0.6` retained poisoned clients on `scenario_e + adaptive_alie_like@0.4`, while official FoolsGold drops to `F1 = 0.9783` and only `1.6` kept clients.
- A matched 20-seed Westermo `sign_flip@0.4` sweep broadens public attack-family coverage without changing the conservative claim boundary.
- A 5-seed public `scenario_h` runtime study scales server-round time from `29.6 ms` to `52.5 ms` to `102.7 ms` across `10/20/40` clients while peak RSS stays near `823 MB`.
