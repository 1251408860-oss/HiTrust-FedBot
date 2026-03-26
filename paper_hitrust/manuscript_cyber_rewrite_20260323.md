# Manuscript Rewrite for Cyber Submission

## Recommended Title

1. HiTrust-FedBot: Group-Coverage-Constrained Trust Filtering for Robust Federated Web Bot Detection in Congested Edge Environments
2. Trust-Aware Hierarchical Federated Web Bot Detection Under Poisoning and Edge Congestion
3. Robust Federated Bot Detection with Group-Coverage-Constrained Trust Aggregation

## Recommended Paper Framing

This paper should be framed as a security-defense paper rather than only a backbone-comparison paper. The core contribution is the trust-aware hierarchical defense with an explicit group-coverage constraint, while GraphSAGE is the strongest main instantiation of that defense. The manuscript should avoid claiming that GraphSAGE is universally superior in every scenario. A more defensible claim is that the proposed defense remains strong across heterogeneous and attack-heavy settings, and that GraphSAGE consistently strengthens the method in structurally demanding scenarios.

## Rewritten Abstract

Federated web bot detection in congested edge environments must tolerate heterogeneous client topology, partial observability, and adversarial client updates. These constraints make standard trust filtering brittle: an aggressive filter can suppress poisoned clients, but it can also remove entire semantic groups and destabilize the global model. We present HiTrust-FedBot, a trust-aware hierarchical federated detection framework that couples grouped aggregation with a group-coverage-constrained trust filter. The method is designed to preserve group representation while still rejecting low-trust updates under poisoning. We instantiate the framework with a GraphSAGE backbone and evaluate it on five topology-aware scenarios under clean training and two attack settings, sign-flip and update-noise poisoning at 40% malicious-client fraction. On the challenging `scenario_h`, the GraphSAGE mainline reaches mean test F1 of `0.9785` in clean training, `0.9797` under sign-flip, and `0.9686` under update-noise across five seeds. On the harder `scenario_f`, the corresponding means are `0.9859`, `0.9840`, and `0.9867`. Compared with the FeatureMLP baseline, GraphSAGE yields significant gains on `scenario_h` in both clean (`p = 0.0095`) and sign-flip (`p = 3.70e-4`) conditions, while the small saturated `scenario_g` shows no significant backbone gap (`p = 0.3739`). A communication study further shows that parameter-efficient tuning retains accuracy while reducing total communication by `80.6%` to `97.9%` relative to full fine-tuning. Additional sensitivity and fixed-seed mechanism analyses show that the remaining worst-case variance is caused by a fully poisoned small group under the group-floor rule, rather than by a general collapse of the GraphSAGE backbone.

## Contributions

- We introduce a trust-aware hierarchical federated bot-detection framework for congested edge environments, with explicit grouping of client updates before global aggregation.
- We formalize a group-coverage-constrained trust filter that prevents semantic groups from being erased by a purely score-driven filter.
- We show that a GraphSAGE instantiation of the framework significantly outperforms the FeatureMLP baseline on the structurally harder settings, especially `scenario_h`.
- We provide robustness, communication, sensitivity, and fixed-seed mechanism studies that explain both the strengths of the method and its residual edge-case failure mode.

## Claim Discipline for the Paper

### Claims to make

- The main method is robust across multiple topology-aware scenarios and remains strong under `sign_flip@0.4` and `update_noise@0.4`.
- GraphSAGE materially strengthens the method in the harder scenarios, especially `scenario_h`, and does not show evidence of systemic instability after the trust-semantics repair.
- `min_keep_per_group = 1` is supported as the best average compromise between semantic coverage and poisoned-client retention.
- The residual variance under `scenario_h + update_noise@0.4` comes from a specific small-group fully-poisoned edge case under the group-floor rule.

### Claims to avoid

- Do not claim that GraphSAGE dominates FeatureMLP in every scenario.
- Do not claim that `scenario_g` is evidence that GraphSAGE is weaker; the updated seed sweep shows saturation and no significant backbone difference.
- Do not describe `min_keep_per_group = 1` as an arbitrary heuristic. It is now experimentally supported, but it still has a pathological edge case that should be stated openly.

## Drop-In Results Rewrite

### Overall Robustness

Across the five topology-aware scenarios, the GraphSAGE-based HiTrust-FedBot mainline remained consistently strong under both clean and adversarial training. The single-run cross-scenario matrix shows test F1 ranging from `0.9692` to `0.9966` in the clean condition, from `0.9705` to `0.9966` under `sign_flip@0.4`, and from `0.9705` to `0.9966` under `update_noise@0.4`. The most demanding case is `scenario_h_mimic_heavy_overlap`, where the single-run GraphSAGE system achieves `F1 = 0.9692` in clean training, `0.9696` under sign-flip, and `0.9705` under update-noise. Seed sweeps confirm that these results are stable on average: on `scenario_h`, the five-seed means are `0.9785 ± 0.0028` for clean training, `0.9797 ± 0.0026` under sign-flip, and `0.9686 ± 0.0130` under update-noise. On the harder `scenario_f`, the corresponding means remain high at `0.9859 ± 0.0021`, `0.9840 ± 0.0039`, and `0.9867 ± 0.0019`, indicating that the repaired trust semantics preserve the mainline behavior even in the more challenging two-tier setting.

### Backbone Comparison

The backbone comparison should be presented as a robustness comparison rather than a pure architecture contest. On `scenario_h`, GraphSAGE substantially improves over the FeatureMLP baseline. In the five-seed clean setting, FeatureMLP reaches mean `F1 = 0.9417`, whereas GraphSAGE reaches `0.9785`, with a significant difference (`p = 0.0095`). Under `sign_flip@0.4`, FeatureMLP reaches `0.9512`, while GraphSAGE reaches `0.9797`, again with a significant difference (`p = 3.70e-4`). The single-run deltas on `scenario_h` also show large false-positive-rate reductions, from `0.1931` to `0.0779` in the clean setting and from `0.1433` to `0.0530` under sign-flip. By contrast, `scenario_g` is now better described as a small, saturated scenario in which both backbones are near ceiling. There, the updated five-seed sweep shows no significant difference in clean training or under sign-flip (`p = 0.3739` in both cases), so the manuscript should treat `scenario_g` as an easy-setting saturation case rather than as a counterexample to the GraphSAGE story.

### Parameter-Efficient Tuning and Communication

The tuning study shows that stronger performance does not require the highest communication cost. Under `scenario_h + sign_flip@0.4`, adapter tuning achieves `F1 = 0.9696` while using only `19.45%` of the full fine-tuning communication budget, corresponding to an `80.55%` byte reduction. Head-only tuning reaches `F1 = 0.9692` with only `2.08%` of the full fine-tuning communication budget, corresponding to a `97.92%` byte reduction. Full fine-tuning is not the strongest setting in this attack regime, reaching `F1 = 0.9666` with a higher `FPR = 0.0935`. Under `scenario_h + update_noise@0.4`, the three tuning modes are closer, but the efficient modes remain competitive: head-only slightly exceeds full fine-tuning in F1 (`0.9718` versus `0.9716`) with `97.92%` fewer bytes, while adapter tuning stays within `0.0011` F1 of full fine-tuning with `80.55%` fewer bytes. These results support a practical manuscript claim: HiTrust-FedBot does not require expensive full-model adaptation to remain effective under attack.

### Aggregation Behavior

The aggregation study under `scenario_h + sign_flip@0.4` shows that the hierarchical aggregator is competitive at the top end of the design space. Hierarchical aggregation reaches mean `F1 = 0.9797` with mean `FPR = 0.0212`, while simple mean aggregation is numerically close in F1 (`0.9794`) and slightly lower in FPR (`0.0181`). Median and Krum-like aggregation are weaker on average, both around `F1 ≈ 0.976`. The manuscript should therefore avoid overstating hierarchical dominance over every alternative aggregator. A defensible statement is that hierarchical aggregation remains a strong and stable choice because it aligns with the grouped trust-filter design and preserves semantic structure while matching or exceeding the more robust baselines in F1.

### Sensitivity and Mechanism Analysis

The sensitivity analysis now provides a stronger justification for the repaired trust semantics. Averaged over the `scenario_h` runs, `min_keep_per_group = 1` is the best compromise. In clean training, moving from `keep0` to `keep1` raises F1 from `0.9666` to `0.9692` and lowers FPR from `0.0935` to `0.0779`, while `keep2` offers no additional gain. Under `sign_flip@0.4`, `keep1` again gives the best balance, with `F1 = 0.9696` and `FPR = 0.0530`, outperforming both `keep0` and `keep2`. Under `update_noise@0.4`, `keep0` and `keep1` are tied on average (`F1 = 0.9705`, `FPR = 0.0685`), whereas `keep2` yields a marginally higher mean F1 (`0.9712`) at the cost of starting to retain poisoned clients. This makes `keep1` the most defensible default because it repairs the group-coverage failure without broadly relaxing the trust filter.

The new fixed-seed mechanism study clarifies the remaining worst-case variance. In the pathological `scenario_h + update_noise@0.4 + seed11` case, both clients in `role:benign_user` are poisoned. With `min_keep_per_group = 0`, the trust filter removes the entire benign group, retains no poisoned clients, and reaches `F1 = 0.9805` with `FPR = 0.0156`, but this violates the intended semantic-coverage objective. With `min_keep_per_group = 1`, the floor rule forces one poisoned benign client to represent the group, producing the worst outcome, `F1 = 0.9496` and `FPR = 0.1028`, even though the retained client has extremely low trust (`trust_norm = 0.0106`). With `min_keep_per_group = 2`, both poisoned benign clients are retained and performance partly recovers to `F1 = 0.9779` and `FPR = 0.0374`. This recovery is consistent with the hierarchical aggregator: it first averages updates within each group and only then averages across groups, so retaining two poisoned clients in the same small group can dilute the damage relative to forcing a single poisoned client to become the group’s sole representative. The manuscript should use this experiment to argue that the residual failure mode is a narrow edge case of the group-floor rule under full small-group poisoning, not a general instability of the GraphSAGE backbone.

## Rewritten Discussion Paragraph

Taken together, the updated experiments show that the repaired GraphSAGE mainline is both stronger and more interpretable than the earlier draft suggested. The method performs best in the structurally difficult scenarios, preserves high F1 under both clean and poisoned training, and no longer supports the earlier claim that `scenario_g` is a stable GraphSAGE weakness. At the same time, the additional mechanism study prevents overclaiming: the group-coverage floor introduces a real trade-off in rare seeds where a small semantic group is fully poisoned. This is exactly the kind of nuanced result that strengthens a cyber-security paper, because it shows not only that the defense works, but also when and why its remaining failure mode appears.

## Limitations and Threats to Validity

- The experiments are built on topology-aware bootstrapped scenarios rather than on a live production deployment.
- The residual worst-case behavior under `scenario_h + update_noise@0.4` shows that a semantic coverage floor can still retain poisoned updates when a small group is fully compromised.
- The current defense does not yet include a conditional abstention rule for groups whose trust mass collapses nearly to zero.
- Some conclusions, especially the communication comparison, are based on scenario-specific studies and should not be framed as universal laws across all federated bot-detection settings.

## Rewritten Conclusion

This work shows that robust federated web bot detection in congested edge environments benefits from combining trust-aware filtering with structure-preserving aggregation. HiTrust-FedBot uses a group-coverage-constrained trust filter to avoid the destructive behavior of purely score-based filtering, and its GraphSAGE instantiation achieves strong performance across the harder topology-aware scenarios under both clean and poisoned training. The updated experiments also sharpen the paper’s main message: the remaining variance is not evidence of backbone collapse, but of a specific edge case in which a fully poisoned small group interacts with the group-floor rule. This makes the method both effective and analytically transparent. A natural next step is to replace the static group floor with a conditional coverage rule that can abstain when an entire group’s trust mass collapses, preserving the semantic objective without forcing a low-trust poisoned representative into the final aggregation.

## Short Cover-Letter Style Summary

The strongest submission angle is: this paper proposes a practically motivated defense for adversarial federated bot detection under congested edge heterogeneity, validates it across multiple topology-aware scenarios, and backs its claims with both average-case robustness and edge-case mechanism analysis. The key novelty is not merely the use of GraphSAGE, but the combination of hierarchical trust aggregation, group-aware coverage preservation, and explicit diagnosis of the trade-off that this design introduces under full small-group poisoning.
