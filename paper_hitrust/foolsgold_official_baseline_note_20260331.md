# Official FoolsGold Baseline Note (2026-03-31)

This note records how the official FoolsGold baseline should be positioned after integrating it into the public adaptive comparison suite.

## 1. Why It Was Added

- The earlier adaptive public story relied mainly on task-adapted FLTrust-like and FLShield-like comparators.
- That left an obvious reviewer angle: the strongest adaptive baselines were still partly engineered for the current graph-federated setting.
- To reduce that risk, the repository now includes an official-code FoolsGold port for the adaptive public comparisons.

## 2. Implementation Scope

- The aggregation mode is `foolsgold` in `core_experiments/internal/run_real_fed_pilot.py`.
- The weight computation follows the official FoolsGold history-based similarity rule:
  - accumulate per-client update history across rounds
  - compute pairwise cosine similarity on accumulated histories
  - apply the official pardoning and logit-rescaling steps
  - weight current-round updates with the resulting client weights
- In this repository it is used as an adaptive public comparator, not as a grouped semantic-coverage method.

Primary sources:

- Official repository: `https://github.com/DistributedML/FoolsGold`
- Paper: `https://www.cs.ubc.ca/~bestchai/papers/foolsgold-raid2020.pdf`

## 3. Current Public Adaptive Results

### 3.1 `scenario_h + adaptive_benign_mimic@0.4`

Source files:

- `paper_hitrust/tables/public_cabench_scenario_h_foolsgold_sage_adaptive_benign_mimic_frac0p4_seed_stats.json`
- `paper_hitrust/tables/public_cabench_scenario_h_adaptive_benign_mimic_comparison.json`

Observed 10-seed means:

- `foolsgold`: `F1=0.9736`, `FPR=0.0150`, `kept_poisoned=0.0`, `kept_clients=1.4`
- `temporal_rootguard`: `F1=0.9760`, `FPR=0.0159`, `kept_poisoned=0.0`, `kept_clients=2.6`
- `fltrust_like`: `F1=0.9749`, `FPR=0.0193`, `kept_poisoned=1.6`, `kept_clients=4.5`
- `flshield_like`: `F1=0.9777`, `FPR=0.0206`, `kept_poisoned=2.4`, `kept_clients=5.5`

Interpretation:

- FoolsGold reaches the same `0.0` retained-poison level as the strongest proposed hardening.
- It does so with much harsher abstention, usually near single-client participation.
- This makes it a useful official abstention anchor, not a better overall operating point.

### 3.2 `scenario_e + adaptive_benign_mimic@0.4`

Source files:

- `paper_hitrust/tables/public_cabench_scenario_e_foolsgold_sage_adaptive_benign_mimic_frac0p4_seed_stats.json`
- `paper_hitrust/tables/public_cabench_scenario_e_adaptive_benign_mimic_comparison.json`

Observed 10-seed means:

- `foolsgold`: `F1=0.9789`, `FPR=0.0117`, `kept_poisoned=0.0`, `kept_clients=1.4`
- `temporal_rootguard_v2`: `F1=0.9892`, `FPR=0.0157`, `kept_poisoned=2.0`, `kept_clients=4.7`
- `temporal_rootguard`: `F1=0.9888`, `FPR=0.0182`, `kept_poisoned=2.8`, `kept_clients=6.4`

Interpretation:

- FoolsGold is stricter on retained-poison control than the proposed hardening.
- However, it pays for that strictness with about one absolute F1 point loss and much lower client retention.
- This is strong evidence that the adaptive story should be framed as a frontier of trade-offs, not universal dominance.

### 3.3 `adaptive_alie_like` second adaptive family

Source files:

- `paper_hitrust/tables/public_cabench_scenario_h_adaptive_alie_like_comparison.json`
- `paper_hitrust/tables/public_cabench_scenario_e_adaptive_alie_like_comparison.json`

Observed 10-seed means:

- `scenario_h foolsgold`: `F1=0.9752`, `FPR=0.0156`, `kept_poisoned=0.0`, `kept_clients=1.3`
- `scenario_h temporal_rootguard_v2`: `F1=0.9763`, `FPR=0.0190`, `kept_poisoned=0.8`, `kept_clients=3.5`
- `scenario_e foolsgold`: `F1=0.9795`, `FPR=0.0170`, `kept_poisoned=0.0`, `kept_clients=1.6`
- `scenario_e temporal_rootguard_v2`: `F1=0.9891`, `FPR=0.0139`, `kept_poisoned=0.4`, `kept_clients=3.3`

Interpretation:

- The same pattern persists under a second adaptive geometry.
- FoolsGold gives the cleanest retained-poison result, but usually at the cost of near-single-client abstention.
- `temporal_rootguard_v2` is better read as a more balanced operating point rather than a universally dominant adaptive defense.

## 4. Recommended Manuscript Positioning

Use the following framing consistently:

- The adaptive public suite now includes an official-code comparator, which materially reduces the "all modern baselines are engineered" criticism.
- FoolsGold should not be used to argue that the proposed method is universally best on retained-poison control.
- Instead, FoolsGold helps show that zero retained-poison is achievable by much harsher abstention.
- The proposed adaptive hardening should therefore be positioned as a more moderate engineering control on the poisoning-retention versus abstention frontier.

## 5. What To Claim

Supported:

- "The adaptive public suite now includes an official FoolsGold comparator in addition to the task-adapted FLTrust-like and FLShield-like baselines."
- "Official FoolsGold reaches `0.0` retained poisoned clients in the current adaptive public suite, but usually with only `1.3-1.6` kept clients."
- "The proposed adaptive hardening offers a less extreme abstention profile, especially on external `scenario_e`."

Not supported:

- "The proposed hardening dominates all adaptive baselines."
- "FoolsGold is weaker than the proposed method on poisoning suppression."
- "The adaptive problem is solved."
