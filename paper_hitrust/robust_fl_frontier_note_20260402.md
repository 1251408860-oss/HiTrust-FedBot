# Frontier Robust FL Baseline Note (2026-04-02)

This note records the post-cleanup review of more recent Byzantine-robust federated learning baseline options after the public validation suite was expanded to matched public sweeps.

## What Changed Locally

- Primary non-adaptive rerun entry points now use matched 20-seed sweeps for public `scenario_e`, public `scenario_h`, Westermo `update_noise`, and Westermo `sign_flip`, while the auxiliary public `NSL-KDD` path remains 10-seed and the adaptive public suite now has two promoted matched 20-seed paths: `scenario_h + adaptive_benign_mimic` and `scenario_e + adaptive_alie_like`.
- `trust_vs_keepall` reports now use matched-seed paired testing instead of an independent-sample t-test.
- The current baseline bundle already spans keep-all, mean, median, Krum, RFA, Centered Clipping, CAF, `ARC+mean`, FLTrust-like, FLShield-like, FedTruth-like, and official FoolsGold.
- Centered Clipping, CAF, and `ARC+mean` are now included in the matched 20-seed public `scenario_e` and public `scenario_h` update-noise comparison tables, while Centered Clipping and `ARC+mean` remain in the matched 10-seed auxiliary public `NSL-KDD` update-noise table.

## Frontier Baseline Review

The current robust FL tooling ecosystem has moved beyond only the classical mean / median / Krum family. The most practical modern benchmark stack I found is the ByzFL benchmark toolkit, which currently exposes:

- robust aggregators such as Centered Clipping, CAF, and SMEA
- pre-aggregators such as ARC
- benchmark helpers for running consistent FL robustness comparisons under shared settings

For this repository, the main implication is not that the paper must block on another full baseline wave before submission. The current bundle is already strong enough for an EAAI-facing engineering paper once the claims stay conservative. Centered Clipping was the lowest-risk missing aggregation comparator and has now been integrated, `ARC+mean` was added next as the lowest-risk heterogeneity-aware modern pre-aggregation comparator, and CAF has now been added as the stronger modern aggregation-side reviewer anchor. If a reviewer explicitly asks for a further modern robust-FL comparator beyond this point, the next additions should be:

1. SMEA
2. only after that, a second broader modern method if a revision round demands extra breadth

The new Centered Clipping, CAF, and `ARC+mean` results are useful precisely because they sharpen the current paper narrative: on public `scenario_h + update_noise@0.4` they reach strong predictive metrics, but they still retain all poisoned clients because they are aggregation-side controls without explicit participation filtering. The Westermo update-noise table now shows the same thing with CAF on a second public raw-data path. SMEA remains the stronger next "revision-round" candidate, but it would require more careful task-matched tuning and interpretation because this project is not a flat iid federated benchmark.

## Submission Guidance

- Do not rewrite the paper around "universal state-of-the-art robustness".
- Keep the main non-adaptive claim centered on poisoning-retention reduction under matched predictive quality.
- Keep the adaptive claim centered on operating points along the poisoning-retention versus abstention frontier.
- Treat Centered Clipping, CAF, and `ARC+mean` as the modern non-adaptive comparators that close the most obvious reviewer gap.
- Treat SMEA as targeted revision ammunition, not as a prerequisite for the current submission round.
