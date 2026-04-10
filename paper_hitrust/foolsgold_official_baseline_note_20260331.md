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

Observed matched 20-seed means:

- `foolsgold`: `F1=0.9694`, `FPR=0.0467`, `kept_poisoned=0.05`, `kept_clients=1.65`
- `temporal_rootguard`: `F1=0.9748`, `FPR=0.0176`, `kept_poisoned=0.35`, `kept_clients=2.4`
- `temporal_rootguard_v2`: `F1=0.9744`, `FPR=0.0190`, `kept_poisoned=0.0`, `kept_clients=1.9`
- `fltrust_like`: `F1=0.9745`, `FPR=0.0217`, `kept_poisoned=1.55`, `kept_clients=3.8`
- `flshield_like`: `F1=0.9760`, `FPR=0.0201`, `kept_poisoned=2.6`, `kept_clients=6.1`

Interpretation:

- FoolsGold still acts as the strictest official abstention anchor on retained-poison control.
- The promoted 20-seed rerun makes the trade-off clearer: `temporal_rootguard` and `temporal_rootguard_v2` keep meaningfully better predictive quality while retaining only `2.4` or `1.9` clients instead of collapsing closer to the `1.65`-client FoolsGold operating point.
- This is still not a dominance result, but it is stronger matched-seed evidence than the earlier 10-seed exploratory table.

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

Observed means:

- `scenario_h foolsgold` (10 seeds): `F1=0.9752`, `FPR=0.0156`, `kept_poisoned=0.0`, `kept_clients=1.3`
- `scenario_h temporal_rootguard_v2` (10 seeds): `F1=0.9763`, `FPR=0.0190`, `kept_poisoned=0.8`, `kept_clients=3.5`
- `scenario_e foolsgold` (matched 20 seeds): `F1=0.9783`, `FPR=0.0231`, `kept_poisoned=0.0`, `kept_clients=1.6`
- `scenario_e temporal_rootguard_v2` (matched 20 seeds): `F1=0.9884`, `FPR=0.0168`, `kept_poisoned=0.6`, `kept_clients=3.15`

Interpretation:

- The same pattern persists under a second adaptive geometry.
- On the promoted 20-seed `scenario_e + adaptive_alie_like` table, FoolsGold remains stricter on retained-poison means, but `temporal_rootguard_v2` keeps a much stronger operating point on F1 and retained clients.
- The released paired table now keeps multiplicity-corrected separation on F1 for `scenario_e`, while the retained-client and retained-poison gaps do not separate after Holm correction. That is still the right evidence shape for a frontier claim rather than a universal dominance claim.

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
