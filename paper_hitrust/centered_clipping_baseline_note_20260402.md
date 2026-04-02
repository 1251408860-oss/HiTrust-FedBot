# Centered Clipping Baseline Note (2026-04-02)

This note records the new Centered Clipping baseline that was added after the matched 10-seed public refresh.

## What Was Added

- `centered_clipping` is now implemented in `core_experiments/internal/hierarchical_aggregation.py` and wired into `run_real_fed_pilot.py`.
- Public update-noise comparison configs were added for:
  - `public_cabench_scenario_e_centered_clipping_sage_update_noise_frac0p4_keepall.json`
  - `public_cabench_scenario_h_centered_clipping_sage_update_noise_frac0p4_keepall.json`
  - `public_nslkdd_centered_clipping_sage_update_noise_frac0p4_keepall.json`
- The three public rerun entry points now rebuild the baseline comparison tables with Centered Clipping included.

## 10-Seed Summary

- Public `scenario_e + update_noise@0.4`:
  - Centered Clipping: `F1 = 0.9881`, `FPR = 0.0228`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9882`, `FPR = 0.0179`, retained poisoned clients `0.1`, kept clients `6.1`
- Public `scenario_h + update_noise@0.4`:
  - Centered Clipping: `F1 = 0.9777`, `FPR = 0.0218`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9723`, `FPR = 0.0330`, retained poisoned clients `0.2`, kept clients `6.2`
- Public `NSL-KDD + update_noise@0.4`:
  - Centered Clipping: `F1 = 0.7642`, `FPR = 0.0619`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.7952`, `FPR = 0.0772`, retained poisoned clients `0.7`, kept clients `6.7`

## Interpretation

The new baseline is useful, but not because it overturns the paper story. It sharpens the correct story.

- On public `scenario_h`, Centered Clipping is a stronger aggregation-only comparator than the previous classical mean / median / Krum bundle on predictive metrics.
- However, it still retains all poisoned clients because it does not perform explicit participation control.
- This means the strongest defensible claim remains the same: the proposed engineering value is not universal F1 dominance, but better operating points on the trade-off between predictive quality and retained poisoned participation.

## Submission Use

- Mention Centered Clipping in the non-adaptive baseline list.
- Use it to show that strong robust aggregation is not the same thing as poisoned-participation control.
- Do not rewrite the paper around "beating Centered Clipping everywhere"; that is not what the current evidence supports.
