# ARC Baseline Note (2026-04-02)

This note records the new `ARC+mean` baseline that was added after the Centered Clipping refresh.

## What Was Added

- `ARC+mean` is implemented as an `arc_mean` aggregation branch in `core_experiments/internal/run_real_fed_pilot.py`.
- The ARC pre-aggregation step is implemented in `core_experiments/internal/hierarchical_aggregation.py` following the current ByzFL / ICLR 2025 ARC rule.
- Public update-noise comparison configs were added for public `scenario_e`, public `scenario_h`, and public `NSL-KDD`.

## Current Summary

- Public `scenario_e + update_noise@0.4` (`20` seeds):
  - `ARC+mean`: `F1 = 0.9877`, `FPR = 0.0188`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9875`, `FPR = 0.0208`, retained poisoned clients `0.1`, kept clients `6.1`
- Public `scenario_h + update_noise@0.4` (`20` seeds):
  - `ARC+mean`: `F1 = 0.9753`, `FPR = 0.0274`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.9703`, `FPR = 0.0442`, retained poisoned clients `0.3`, kept clients `6.3`
- Public `NSL-KDD + update_noise@0.4` (`10` seeds):
  - `ARC+mean`: `F1 = 0.7585`, `FPR = 0.0547`, retained poisoned clients `4.0`, kept clients `10.0`
  - Trust-aware mainline: `F1 = 0.7952`, `FPR = 0.0772`, retained poisoned clients `0.7`, kept clients `6.7`

## Interpretation

`ARC+mean` is useful because it is a stronger modern heterogeneity-aware non-adaptive comparator than the older mean / median / Krum family, especially on public `scenario_h`. However, like Centered Clipping, it still retains all poisoned clients. This means it strengthens the paper's main engineering claim rather than weakening it: robust aggregation and adaptive pre-aggregation can improve predictive metrics without solving explicit poisoned-participation control.

## Submission Use

- Mention `ARC+mean` as a modern heterogeneity-aware pre-aggregation comparator in the non-adaptive baseline bundle.
- Use it together with Centered Clipping to show that strong non-abstaining aggregation is still not the same as explicit participation control.
- Do not over-claim that the paper universally outperforms ARC on standard predictive metrics; the correct story is still about operating points.
