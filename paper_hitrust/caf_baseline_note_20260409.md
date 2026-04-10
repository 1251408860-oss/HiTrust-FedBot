# CAF Baseline Note (2026-04-09)

This note records the new CAF baseline that was added after the matched 20-seed public baseline expansion.

## What Was Added

- `caf` is now implemented as an aggregation branch in `core_experiments/internal/run_real_fed_pilot.py`.
- The local CAF implementation follows the official ByzFL `CAF` definition exposed in the official toolkit documentation.
- Public update-noise comparison configs were added for public `scenario_e`, public `scenario_h`, and public Westermo.
- The three primary non-adaptive public rerun entry points now rebuild the baseline comparison tables with CAF included.

## Current Summary

- Public `scenario_e + update_noise@0.4` (`20` seeds):
  - CAF: `F1 = 0.9876`, `FPR = 0.0221`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9875`, `FPR = 0.0208`, retained poisoned clients `0.1`, kept clients `6.1`
- Public `scenario_h + update_noise@0.4` (`20` seeds):
  - CAF: `F1 = 0.9746`, `FPR = 0.0279`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9703`, `FPR = 0.0442`, retained poisoned clients `0.3`, kept clients `6.3`
  - `condfloor`: `F1 = 0.9746`, `FPR = 0.0307`, retained poisoned clients `0.0`, kept clients `6.0`
- Public Westermo `update_noise@0.4` (`20` seeds):
  - CAF: `F1 = 0.6211`, `FPR = 0.0093`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.6147`, `FPR = 0.0224`, retained poisoned clients `0.1`, kept clients `6.1`
  - `condfloor`: `F1 = 0.6159`, `FPR = 0.0190`, retained poisoned clients `0.05`, kept clients `6.05`

## Interpretation

CAF is useful for the paper because it strengthens the modern-robust-aggregation side of the comparison without changing the main engineering conclusion.

- On public `scenario_h`, CAF reaches a predictive operating point close to the strongest aggregation-only baselines, but it still retains all `4.0` poisoned clients.
- On public Westermo, CAF reaches a stronger predictive operating point than the trust-aware line on `F1` and `FPR`, yet again retains all `4.0` poisoned clients.
- This sharpens the same message already visible with Centered Clipping and `ARC+mean`: stronger aggregation alone is not the same thing as explicit poisoned-participation control.

## Submission Use

- Mention CAF as part of the modern non-adaptive baseline bundle.
- Use CAF together with Centered Clipping and `ARC+mean` to show that modern robust aggregation can improve predictive metrics while still failing to reduce retained poisoned participation.
- Do not rewrite the paper around universal superiority over CAF; the evidence still supports an operating-point interpretation rather than a universal dominance claim.
