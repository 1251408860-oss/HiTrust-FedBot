# FLTrust-like Baseline Note (2026-03-30)

This note records the current repository-side evidence for the FLTrust-like baseline and how it should be used in the EAAI manuscript narrative.

## 1. Implementation Scope

- The repo now includes a `fltrust_like` aggregation mode in `core_experiments/internal/run_real_fed_pilot.py`.
- The implementation is intentionally described as "FLTrust-like" rather than an exact FLTrust reproduction.
- The current mechanism uses:
  - a deterministic trusted server root subset from the global training split
  - a server update trained on that root subset each round
  - trust weights `ReLU(cos(client_update, server_update))`
  - client-update norm alignment to the server-update norm before weighted aggregation

This is close enough to count as a modern trust-bootstrapping baseline, but it should not be overstated as a bit-for-bit reproduction of the original FLTrust release setting.

## 2. Current Public-Benchmark Results

### 2.1 Same-task public hardest scenario_h, default FLTrust-like

Source files:

- `paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_seed_stats.json`
- `paper_hitrust/tables/public_cabench_scenario_h_update_noise_baseline_comparison.json`
- `paper_hitrust/tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json`

Observed 3-seed means:

- `default FLTrust-like (root96_e1)`: `F1=0.9775`, `FPR=0.0218`, `kept_poisoned=1.3333`
- `trust_aware static floor`: `F1=0.9693`, `FPR=0.0415`, `kept_poisoned=0.3333`
- `condfloor`: `F1=0.9798`, `FPR=0.0114`, `kept_poisoned=0.0`
- `keepall`: `F1=0.9766`, `FPR=0.0073`, `kept_poisoned=4.0`

Interpretation:

- Default FLTrust-like is not weak on F1.
- However, it still retains materially more poisoned clients than the trust-aware mainline and much more than condfloor.

### 2.2 scenario_h FLTrust-like sensitivity

Source files:

- `paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json`
- `paper_hitrust/figures/public_cabench_scenario_h_fltrust_like_sensitivity.png`

Sensitivity grid:

- `server_root_size in {48, 96, 192}`
- `server_root_local_epochs in {1, 2}`

Observed 3-seed means:

- `root48_e1`: `F1=0.9772`, `FPR=0.0104`, `kept_poisoned=2.0`
- `root48_e2`: `F1=0.9777`, `FPR=0.0177`, `kept_poisoned=1.6667`
- `root96_e1`: `F1=0.9775`, `FPR=0.0218`, `kept_poisoned=1.3333`
- `root96_e2`: `F1=0.9791`, `FPR=0.0177`, `kept_poisoned=1.3333`
- `root192_e1`: `F1=0.9802`, `FPR=0.0104`, `kept_poisoned=1.0`
- `root192_e2`: `F1=0.9803`, `FPR=0.0135`, `kept_poisoned=1.6667`

Key point:

- Tuning can make FLTrust-like very competitive on `F1/FPR`.
- Even the strongest security-oriented tuned point, `root192_e1`, still keeps `1.0` poisoned clients on average.
- `condfloor` remains the only current public hardest-setting result in this repo with `kept_poisoned=0.0`.

This is the most useful manuscript-level conclusion from the FLTrust-like line.

### 2.3 Public scenario_e and public NSL-KDD, default FLTrust-like

Source files:

- `paper_hitrust/tables/public_cabench_scenario_e_update_noise_baseline_comparison.json`
- `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json`

Observed 3-seed means:

- `public scenario_e FLTrust-like`: `F1=0.9919`, `FPR=0.0134`, `kept_poisoned=3.0`
- `public scenario_e trust_aware`: `F1=0.9868`, `FPR=0.0103`, `kept_poisoned=0.3333`
- `public NSL-KDD FLTrust-like`: `F1=0.7566`, `FPR=0.0544`, `kept_poisoned=2.3333`
- `public NSL-KDD trust_aware`: `F1=0.7882`, `FPR=0.0629`, `kept_poisoned=0.3333`

Interpretation:

- On `scenario_e`, FLTrust-like can post high F1 but still keeps many poisoned clients.
- On `NSL-KDD`, FLTrust-like is not only looser on poisoned retention, but also worse on F1 than the trust-aware mainline.

## 3. Recommended Manuscript Positioning

Use the following framing consistently:

- The paper now covers a modern trust-bootstrapping baseline through the `FLTrust-like` implementation.
- The baseline comparison does not support a "universal F1 superiority" claim for the proposed method.
- The strongest defensible claim is that the proposed line reduces retained poisoned participation more reliably under the topology-aware public hardest setting.
- `condfloor` should be framed as a targeted hardening for the identified hardest-setting failure mode, not as a universal replacement for all settings.

## 4. Suggested Wording

### 4.1 Baseline paragraph

"We additionally implemented an FLTrust-like trust-bootstrapping baseline in the current graph-federated setting, using a deterministic trusted server root subset, cosine-ReLU trust weighting, and server-norm update alignment. We treat this baseline as an engineered FLTrust-like comparison rather than an exact reproduction of the original FLTrust release setting."

### 4.2 Results paragraph

"On the same-task public hardest Ca-Bench scenario_h under `update_noise@0.4`, the default FLTrust-like baseline achieved `F1=0.9775` with `kept_poisoned=1.33`, while the tuned `root192_e1` variant reached `F1=0.9802` and `FPR=0.0104` but still retained `1.0` poisoned clients on average. In contrast, the conditional-floor hardening achieved `F1=0.9798` with `kept_poisoned=0.0`. This indicates that the main security differentiator is not universal F1 improvement, but tighter control of poisoned participation under the hardest topology-aware public setting."

### 4.3 Discussion paragraph

"The FLTrust-like sensitivity results sharpen the interpretation of our method. A larger trusted root can make trust-bootstrapping highly competitive on F1 and FPR, so the contribution should not be framed as dominance on standard accuracy metrics. Instead, the differentiating value lies in reducing retained poisoned clients, especially when the same-task public hardest setting exposes a concentrated failure mode in group-preserving trust defenses."

## 5. What Not To Claim

Avoid the following claims:

- "Our method universally outperforms FLTrust on F1."
- "Conditional floor is the new default defense for all benchmarks."
- "FLTrust-like fails completely in our setting."

Those statements are not supported by the current evidence.

## 6. Strongest Current Claim

The strongest honest claim supported by the current repo is:

"After adding a modern FLTrust-like trust-bootstrapping baseline and tuning it on the same-task public hardest setting, the proposed hardening still provides the cleanest poisoned-participation control (`0.0` retained poisoned clients), while tuned FLTrust-like remains competitive on F1/FPR but continues to retain poisoned clients."
