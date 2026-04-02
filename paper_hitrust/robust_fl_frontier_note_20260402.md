# Frontier Robust FL Baseline Note (2026-04-02)

This note records the post-cleanup review of more recent Byzantine-robust federated learning baseline options after the public validation suite was expanded to matched 10-seed sweeps.

## What Changed Locally

- Public `scenario_e`, public `scenario_h`, and auxiliary public `NSL-KDD` rerun entry points now default to the same 10-seed sweep: `11,22,33,44,55,66,77,88,99,111`.
- `trust_vs_keepall` reports now use matched-seed paired testing instead of an independent-sample t-test.
- The current baseline bundle already spans keep-all, mean, median, Krum, RFA, FLTrust-like, FLShield-like, FedTruth-like, and official FoolsGold.

## Frontier Baseline Review

The current robust FL tooling ecosystem has moved beyond only the classical mean / median / Krum family. The most practical modern benchmark stack I found is the ByzFL benchmark toolkit, which currently exposes:

- robust aggregators such as Centered Clipping, CAF, and SMEA
- pre-aggregators such as ARC
- benchmark helpers for running consistent FL robustness comparisons under shared settings

For this repository, the main implication is not that the paper must block on another full baseline wave before submission. The current bundle is already strong enough for an EAAI-facing engineering paper once the claims stay conservative. The implication is that, if a reviewer explicitly asks for a more current robust-FL comparator, the lowest-risk next additions are:

1. Centered Clipping first
2. one heterogeneity-aware modern method from the ByzFL stack such as ARC or CAF

Centered Clipping is the most realistic next addition because it is aggregation-local and can be slotted into the existing update aggregation path without redesigning the trust or grouping logic. ARC / CAF are stronger "revision-round" candidates, but they would require more careful task-matched tuning and interpretation because this project is not a flat iid federated benchmark.

## Submission Guidance

- Do not rewrite the paper around "universal state-of-the-art robustness".
- Keep the main non-adaptive claim centered on poisoning-retention reduction under matched predictive quality.
- Keep the adaptive claim centered on operating points along the poisoning-retention versus abstention frontier.
- Treat newer robust FL baselines as targeted revision ammunition, not as a prerequisite for the current submission round.
