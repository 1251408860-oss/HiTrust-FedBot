# EAAI Experiment Evaluation (2026-04-14)

## 1. Executive Summary

This document evaluates the current HiTrust-FedBot experimental package specifically from the perspective of an *Engineering Applications of Artificial Intelligence* submission.

The current experimental surface is now strong enough to support an EAAI submission. The work no longer depends on a single benchmark, a single attack family, or a single metric. Instead, it presents a coherent engineering-AI evidence stack consisting of:

- internal topology-aware pilot scenarios
- same-task public Ca-Bench validation on `scenario_e` and `scenario_h`
- two public raw-data chains outside Ca-Bench: Westermo and LITNET-2020 UDP-flood
- a full matched 20-seed adaptive public `2 x 2` matrix
- a 5-seed single-host deployment/runtime package over `10/20/40/80` clients
- artifact verification, fixed provenance anchors, and a maintainer-side exact-match raw audit for the released internal graph bundle

The strongest claim supported by the current experiments is not universal dominance on F1. The strongest claim is that HiTrust-FedBot and its targeted hardening variants occupy practical operating points on the trade-off among predictive quality, retained poisoned participation, and abstention, while remaining reproducible and deployment-oriented.

## 2. Overall Assessment

### 2.1 Summary Judgment

The experiment package is now in a strong submission-ready state for EAAI.

If judged only on the experimental surface, the package supports an estimated EAAI acceptance probability of roughly `84%–87%`.

If judged more realistically at the manuscript level, including novelty framing, reviewer interpretation risk, and venue fit, the current estimate is roughly `81%–84%`, with a midpoint judgment around `82%`.

### 2.2 High-Level Scores

- experimental completeness: `9.0/10`
- evidence credibility: `8.8/10`
- EAAI fit: `8.7/10`
- perceived novelty from experiments alone: `8.0/10`
- reproducibility and auditability: `9.0/10`

## 3. What Has Been Completed

### 3.1 Evidence Surface

The repository now contains all of the following experiment layers:

- five internal topology-aware pilot scenarios
- two same-task public Ca-Bench scenarios
- public Westermo raw-data chain
- public LITNET-2020 UDP-flood raw-data chain
- auxiliary public NSL-KDD transfer path
- supportive second attack-family reruns on Westermo and LITNET
- public adaptive matched 20-seed `2 x 2` matrix
- public hardest-setting single-host deployment/runtime scaling package

This is materially stronger than a paper that depends only on Ca-Bench or only on synthetic internal graphs.

### 3.2 Reproducibility Surface

The artifact and release surface is now unusually strong for this submission type:

- static release checksum manifest is present
- reviewer artifact verification passes
- shell entry points are explicit and scoped
- public adaptive suite is fully rebuildable
- public runtime package is rebuildable
- private internal raw traces are still not redistributed, but an exact-match maintainer-side raw audit now exists

This does not fully remove the private-data limitation, but it significantly reduces the credibility risk compared with a non-auditable private internal pipeline.

## 4. Primary Non-Adaptive Same-Task Public Evidence

### 4.1 Public Ca-Bench `scenario_h + update_noise@0.4`

The strongest single non-adaptive result remains the conditional-floor repair:

- `condfloor`: `F1=0.9746`, `FPR=0.0307`, `KP=0.0`, `KC=6.0`
- `trust_aware` static line: `F1=0.9703`, `FPR=0.0442`, `KP=0.3`, `KC=6.3`
- `keepall`: `F1=0.9725`, `FPR=0.0374`, `KP=4.0`, `KC=10.0`

Interpretation:

- this is the best current evidence for the paper's targeted repair story
- the security gain is operationally meaningful because retained poisoned clients drop to zero
- the result does not rely on an F1-only narrative

Why this table matters:

- it directly supports the paper's core engineering claim
- it justifies `condfloor` as a failure-mode repair rather than as an arbitrary extra variant
- it survives comparison against modern clipping-based or aggregation-based baselines that still retain all poisoned clients

### 4.2 Public Ca-Bench `scenario_e + update_noise@0.4`

The `scenario_e` same-task public result remains useful as the more stable operating-point case:

- `trust_aware`: `F1=0.9875`, `FPR=0.0208`, `KP=0.1`, `KC=6.1`
- `keepall`: `F1=0.9877`, `FPR=0.0222`, `KP=4.0`, `KC=10.0`
- `ARC+mean`: `F1=0.9877`, `FPR=0.0188`, `KP=4.0`, `KC=10.0`
- `CAF`: `F1=0.9876`, `FPR=0.0221`, `KP=4.0`, `KC=10.0`

Interpretation:

- this table shows that the proposed line remains competitive on predictive quality
- modern baselines can match or slightly edge certain pure prediction metrics
- but they still do not perform explicit poisoned-participation control

This is important because it prevents the paper from reading like a one-table anomaly centered only on `scenario_h`.

## 5. Public Raw-Data External Evidence

### 5.1 Westermo `update_noise@0.4`

This path is one of the strongest external reinforcements:

- `trust_aware`: `F1=0.6147`, `KP=0.1`, `KC=6.1`
- `condfloor`: `F1=0.6159`, `KP=0.05`, `KC=6.05`
- `keepall`: `F1=0.6196`, `KP=4.0`, `KC=10.0`
- `fltrust_like`: `F1=0.6213`, `KP=1.85`, `KC=3.9`

Interpretation:

- the raw-data chain confirms that the poisoned-participation control story is not unique to Ca-Bench
- `condfloor` slightly improves the security point relative to the static line
- stronger pure-F1 baselines still sit at much weaker security-retention points

### 5.2 LITNET-2020 UDP-flood `update_noise@0.4`

This is a harsher and more valuable external stress point:

- `trust_aware`: `F1=0.5447`, `KP=0.85`, `KC=6.85`
- `condfloor`: `F1=0.5856`, `KP=0.4`, `KC=6.4`
- `keepall`: `F1=0.5446`, `KP=4.0`, `KC=10.0`
- `fltrust_like`: `F1=0.6244`, `KP=1.75`, `KC=5.65`
- `ARC+mean`: `F1=0.6217`, `KP=4.0`, `KC=10.0`

Interpretation:

- this table is not a universal-win table
- it is valuable precisely because it shows the harshest operating-point tension
- `condfloor` meaningfully lowers retained poison while improving over the static line
- higher-F1 alternatives still retain more poisoned clients or much broader unsafe participation

This table is especially important for credibility because it demonstrates that the paper is not hiding difficult public cases.

## 6. Supportive Second Attack-Family Width Evidence

### 6.1 Westermo `sign_flip@0.4`

- `trust_aware`: `F1=0.6215`, `KP=2.8`, `KC=7.05`
- `condfloor`: `F1=0.6217`, `KP=2.9`, `KC=7.25`
- `fltrust_like`: `F1=0.6203`, `KP=2.05`, `KC=4.15`
- `keepall`: `F1=0.6200`, `KP=4.0`, `KC=10.0`

Interpretation:

- this path broadens attack-family coverage
- it does not create a strong new dominance story
- that is acceptable, because the correct use of this table is width evidence rather than a headline claim

### 6.2 LITNET-2020 UDP-flood `sign_flip@0.4`

- `trust_aware`: `F1=0.6201`, `KP=2.85`, `KC=6.9`
- `condfloor`: `F1=0.6231`, `KP=3.05`, `KC=6.95`
- `fltrust_like`: `F1=0.6229`, `KP=0.9`, `KC=5.4`
- `ARC+mean`: `F1=0.6255`, `KP=4.0`, `KC=10.0`

Interpretation:

- again, this is a width table, not a headline table
- it reinforces the paper's “frontier, not universal dominance” interpretation
- including it helps the paper look honest and less benchmark-optimized

## 7. Adaptive Evidence

### 7.1 Why the Adaptive Suite Is Much Stronger Now

The adaptive package is now materially stronger because all four public scenario/attack combinations have matched 20-seed reruns:

- `scenario_h + adaptive_benign_mimic`
- `scenario_h + adaptive_alie_like`
- `scenario_e + adaptive_benign_mimic`
- `scenario_e + adaptive_alie_like`

This changes the adaptive story from “a couple of promoted examples” into a real matched matrix.

### 7.2 Main Adaptive Strengths

#### `scenario_e + adaptive_benign_mimic`

- `temporal_rootguard_v2`: `F1=0.9888`, `FPR=0.0182`, `KP=1.75`, `KC=4.10`
- `static`: `F1=0.9872`, `KP=4.0`, `KC=6.95`
- `condfloor`: `F1=0.9871`, `KP=4.0`, `KC=6.8`
- `keepall`: `F1=0.9870`, `KP=4.0`, `KC=10.0`
- `foolsgold`: `F1=0.9778`, `KP=0.0`, `KC=1.3`

Interpretation:

- this is one of the clearest adaptive wins for `temporal_rootguard_v2`
- it improves the operating point meaningfully against static, condfloor, and keepall
- FoolsGold remains stricter on poison retention, but at a much harsher abstention point and materially worse F1

#### `scenario_e + adaptive_alie_like`

- `temporal_rootguard_v2`: `F1=0.9884`, `FPR=0.0168`, `KP=0.6`, `KC=3.15`
- `temporal_rootguard`: `F1=0.9883`, `KP=1.2`, `KC=5.0`
- `static`: `F1=0.9865`, `KP=3.8`, `KC=6.65`
- `condfloor`: `F1=0.9870`, `KP=3.6`, `KC=6.6`
- `foolsgold`: `F1=0.9783`, `KP=0.0`, `KC=1.6`

Interpretation:

- this table supports the adaptive engineering story well
- `temporal_rootguard_v2` holds a practical middle ground between unsafe broad retention and severe abstention

### 7.3 Supportive Adaptive Width Evidence

#### `scenario_h + adaptive_benign_mimic`

- `temporal_rootguard_v2`: `F1=0.9744`, `FPR=0.0190`, `KP=0.0`, `KC=1.9`
- `temporal_rootguard`: `F1=0.9748`, `KP=0.35`, `KC=2.4`
- `flshield_like`: `F1=0.9760`, `KP=2.6`, `KC=6.1`
- `static`: `F1=0.9750`, `KP=4.0`, `KC=7.25`

Interpretation:

- this is useful but not a universal dominance table
- `temporal_rootguard_v2` is strongest on poison suppression
- it pays for that with lower client retention
- this is still good evidence for a frontier interpretation

#### `scenario_h + adaptive_alie_like`

- `temporal_rootguard_v2`: `F1=0.9748`, `FPR=0.0190`, `KP=0.8`, `KC=2.85`
- `temporal_rootguard`: `F1=0.9751`, `KP=1.6`, `KC=3.8`
- `flshield_like`: `F1=0.9769`, `KP=2.6`, `KC=5.05`
- `static`: `F1=0.9752`, `KP=3.65`, `KC=7.35`
- `foolsgold`: `F1=0.9698`, `KP=0.0`, `KC=1.6`

Interpretation:

- this is exactly the kind of table that should be presented as supportive width evidence
- it shows that the adaptive control logic occupies a meaningful operating point
- it does not justify universal adaptive dominance language

## 8. Runtime and Deployment Evidence

### 8.1 Current Runtime Package

The current single-host deployment/runtime package now covers `10/20/40/80` clients.

For the static line:

- `10` clients: wall `56.34 ms`, server `29.64 ms`, aggregation `0.71 ms`
- `20` clients: wall `97.47 ms`, server `52.45 ms`, aggregation `1.22 ms`
- `40` clients: wall `207.0 ms`, server `102.67 ms`, aggregation `2.40 ms`
- `80` clients: wall `504.36 ms`, server `266.08 ms`, aggregation `7.04 ms`

Other key observations:

- bytes per round scale linearly from `24.14 KiB` to `193.13 KiB`
- peak RSS remains around `823–830 MB`
- aggregation remains only about `2.2%–2.6%` of server round time
- `condfloor` and keep-all remain in the same timing band

### 8.2 Why This Matters for EAAI

This evidence is important because it makes the paper look like an engineering-AI system paper rather than a pure robust-FL method paper.

The current runtime package is strong enough to support claims about:

- measured local deployment cost
- cost scaling over a moderate client-count range
- the fact that trust-aware control logic does not dominate measured server time

It is not sufficient to support claims about:

- distributed latency
- multi-host deployment
- WAN-scale end-to-end systems benchmarking

As long as the paper keeps that boundary explicit, the runtime evidence is a net positive.

## 9. Auxiliary and Internal Evidence

### 9.1 NSL-KDD

NSL-KDD remains correctly positioned as auxiliary cross-domain context:

- `trust_aware`: `F1=0.7952`, `KP=0.7`, `KC=6.7`
- `ARC+mean`: `F1=0.7585`, `KP=4.0`, `KC=10.0`
- `centered_clipping`: `F1=0.7642`, `KP=4.0`, `KC=10.0`
- `fltrust_like`: `F1=0.7557`, `KP=1.7`, `KC=5.1`

This is supportive and useful, but it should not be promoted to headline same-task evidence.

### 9.2 Internal Topology-Aware Pilots

The internal pilots are still important because they provide the mechanism-discovery context for:

- semantic group collapse
- adaptive camouflage
- the motivation for grouped trust-aware filtering

The main limitation remains unchanged:

- the private raw traces are not redistributed publicly

The current exact-match maintainer-side raw audit substantially reduces credibility risk, but it does not fully remove the public-data boundary.

## 10. Main Strengths of the Experimental Package

- The package is no longer benchmark-fragile.
- The main claim is supported by same-task public evidence, not only internal data.
- Raw-data chains outside Ca-Bench prevent the paper from reading as Ca-Bench-specific.
- Adaptive evidence is now complete enough to look deliberate rather than cherry-picked.
- Runtime evidence now supports a real engineering-cost paragraph.
- Paired 20-seed evaluation with multiplicity correction strengthens credibility.
- The artifact surface is much stronger than the average security/FL submission.

## 11. Remaining Weaknesses and Risks

- The strongest claim still depends on careful operating-point framing rather than universal dominance.
- Some external tables, especially LITNET `sign_flip`, are width evidence rather than superiority evidence.
- The internal raw-data pipeline is still not fully public.
- The runtime package is still single-host only.
- FLTrust-like and FLShield-like are still task-adapted comparators, not bit-for-bit original reproductions.
- A reviewer who wants a cleaner theorem-style novelty story may still judge the work as a systems-style integration paper rather than a sharp new robust-FL algorithmic leap.

## 12. Submission Implications for EAAI

### 12.1 What the Experiments Support Safely

The experiments safely support the following EAAI-style claim:

HiTrust-FedBot is an interpretable, trust-aware engineering AI framework for federated bot detection that exposes and manages the trade-off among predictive quality, retained poisoned participation, and abstention, with same-task public validation, public raw-data width evidence, matched adaptive stress evaluation, and measured deployment/runtime cost.

### 12.2 What the Experiments Do Not Support Safely

The experiments do not safely support:

- universal superiority over all baselines on all metrics
- a general theorem of Byzantine robustness
- a fully public end-to-end internal-data regeneration claim
- a distributed systems benchmarking claim

## 13. Final Probability Estimate

### 13.1 Experiment-Only Estimate

If the decision were based only on the experimental package, the current estimate would be:

- `84%–87%`

### 13.2 Realistic Submission Estimate

Including manuscript framing, reviewer interpretation, and venue-fit uncertainty, the current estimate is:

- `81%–84%`
- midpoint judgment: about `82%`

## 14. Final Conclusion

The current experiment package is strong enough for EAAI.

Its value lies in breadth, consistency, and engineering relevance rather than in a single universal-win table. The package is now strongest when presented as a reproducible engineering-AI system with explicit operating-point control, not as a universal robust-federated-learning breakthrough.

That is the correct framing, and the current experiments support it.
