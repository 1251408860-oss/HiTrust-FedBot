# HiTrust-FedBot: Group-Coverage-Constrained Trust Filtering for Robust Federated Web Bot Detection in Congested Edge Environments

Author identities, affiliations, and correspondence details are intentionally separated into the submission title page. See `docs/CYBERSECURITY_TITLE_PAGE_TEMPLATE_20260324.md`.

## Abstract

Federated web bot detection in congested edge environments must tolerate heterogeneous client topology, partial observability, limited communication budgets, and adversarial client updates. These constraints make naive trust filtering brittle: a strict filter can suppress poisoned clients, but it can also remove entire semantic groups and destabilize the global model. We present HiTrust-FedBot, a trust-aware hierarchical federated detection framework that couples grouped aggregation with a group-coverage-constrained trust filter. The method is designed to preserve group representation while still rejecting low-trust updates under poisoning. We instantiate the framework with a GraphSAGE backbone and evaluate it on five topology-aware scenarios under clean training and two attack settings, sign-flip and update-noise poisoning at a 40% malicious-client fraction. On the challenging `scenario_h`, the GraphSAGE mainline reaches mean test F1 of `0.9785` in clean training, `0.9797` under sign-flip, and `0.9686` under update-noise across five seeds. On the harder `scenario_f`, the corresponding means are `0.9859`, `0.9840`, and `0.9867`. Compared with a FeatureMLP baseline, GraphSAGE yields significant gains on `scenario_h` in both clean (`p = 0.0095`) and sign-flip (`p = 3.70e-4`) conditions, while the small saturated `scenario_g` shows no significant backbone gap (`p = 0.3739`). A communication study further shows that parameter-efficient tuning retains accuracy while reducing total communication by `80.6%` to `97.9%` relative to full fine-tuning. A held-out `scenario_e` trust-aware-versus-keep-all comparison further shows that under `update-noise@0.4`, trust-aware filtering reduces retained poisoned clients from `4.0` to `0.2` with only a small and non-significant mean-F1 change (`0.9879` versus `0.9890`, `p = 0.6867`). An auxiliary public NSL-KDD validation further shows near-neutral mean F1 under poisoned training while reducing retained poisoned clients from `4.0` to `0.33` under `update_noise@0.4`. Additional sensitivity and fixed-seed mechanism analyses show that the remaining worst-case variance is caused by a fully poisoned small group under the group-floor rule, rather than by a general collapse of the GraphSAGE backbone.

**Keywords:** federated learning, bot detection, adversarial robustness, trust filtering, GraphSAGE, edge intelligence

## 1. Introduction

Web bot detection is increasingly deployed across distributed and bandwidth-constrained edge environments where centralized data collection is undesirable or infeasible. Federated learning provides a natural training mechanism for such settings, but realistic deployments must handle three coupled difficulties. First, edge clients do not observe identically distributed traffic or graph structure. Second, communication budgets are limited, so the system cannot assume heavy global synchronization or unrestricted full-model updates. Third, the federated process itself becomes a new attack surface, allowing malicious clients to manipulate updates and poison the global model.

These issues are especially acute for graph-structured bot detection. Topology matters, but topology also amplifies heterogeneity: clients can represent different structural neighborhoods, user roles, or traffic subregions. A purely score-based trust filter can remove suspicious clients, yet it can also erase an entire semantic slice of the federation if all clients from that slice receive low trust in the same round. In such a case, the global model may become robust against one kind of poisoning while simultaneously becoming under-representative of the underlying traffic population.

This paper studies that trade-off in the context of trust-aware hierarchical federated bot detection. Our core position is that the defense should not be framed as a generic graph-model comparison alone. The main contribution is a grouped, trust-aware aggregation pipeline with an explicit group-coverage constraint. GraphSAGE is the strongest instantiation we evaluate, but the paper's real novelty is the security mechanism that coordinates trust filtering, grouped aggregation, and communication-efficient tuning under adversarial edge heterogeneity.

The experimental results support five main claims. First, the GraphSAGE-based HiTrust-FedBot mainline remains strong across multiple topology-aware scenarios under both clean and poisoned training. Second, GraphSAGE materially strengthens the defense on structurally harder settings such as `scenario_h`, where it significantly outperforms a FeatureMLP baseline. Third, parameter-efficient tuning preserves most or all of the performance while substantially lowering communication cost. Fourth, a held-out `scenario_e` trust-aware-versus-keep-all comparison shows that the method's practical value lies in reducing poisoned participation at near-neutral accuracy cost rather than in universally boosting F1. Fifth, the remaining worst-case behavior is not evidence of backbone instability; instead, it is a narrow mechanism-level edge case in which a fully poisoned small group interacts with the group-floor rule.

The rest of the paper is organized as follows. Section 2 defines the system and threat model and introduces the trust-aware hierarchical defense. Section 3 describes the experimental protocol. Section 4 presents the main results, including robustness, backbone comparison, communication, and mechanism studies. Section 5 discusses interpretation and limitations. Section 6 concludes the paper.

## 2. Method

### 2.1 System setting

We consider federated bot detection over a set of edge clients, where each client locally trains on its own traffic-derived graph partition. The server coordinates training over multiple rounds and aggregates client updates without centralizing raw data. Because client observations are topologically non-IID, client updates are grouped into semantically meaningful partitions before global aggregation.

### 2.2 Threat model

We consider malicious clients that participate in training and poison the federated update stream. Two attack types are studied in the main experiments:

- `sign_flip@0.4`: 40% of clients invert or directionally corrupt their model updates.
- `update_noise@0.4`: 40% of clients inject strong perturbation noise into the update stream.

The attacker does not need to compromise all clients. The more realistic security question is whether the global model can remain effective when a minority of clients are malicious and when some semantic groups are much smaller or structurally more fragile than others.

### 2.3 Trust-aware hierarchical aggregation

HiTrust-FedBot first computes per-client trust signals from validation behavior and update characteristics, then filters or downweights clients before aggregation. Rather than aggregating all retained updates in one flat pool, the method first aggregates within semantic groups and then aggregates across groups. This grouped structure helps preserve heterogeneous information that would otherwise be washed out by a single global mean.

The grouped design matters operationally as well as statistically. In a congested edge setting, different groups can correspond to different subgraphs, traffic modes, or role distributions. A defense that only keeps whichever clients have the highest trust scores may improve local robustness in one round while collapsing representation for an entire part of the federation.

### 2.4 Group-coverage-constrained trust filtering

The key mechanism introduced in this work is a group-coverage-constrained trust filter. After trust scoring, the filter enforces a minimum retained-client floor per group, denoted `min_keep_per_group`. This constraint prevents a group from disappearing solely because all of its trust scores fall below the round threshold. In the repaired mainline used in this paper, the default setting is `min_keep_per_group = 1`.

This mechanism introduces a principled trade-off. A larger floor protects semantic coverage but also raises the chance of retaining poisoned clients in a compromised group. A smaller floor improves strict filtering but may eliminate a semantically important group. The paper therefore treats `min_keep_per_group` not as a cosmetic hyperparameter, but as a central robustness design choice that requires explicit empirical justification.

Because the fixed floor can still preserve a fully compromised small group, we also evaluate a lightweight conditional hardening in which the floor-repair step is skipped when a group's total normalized trust mass collapses below a small threshold. In the targeted experiment reported later, this threshold is set to `0.10`, turning the floor into an abstaining coverage rule for near-zero-trust groups rather than an unconditional repair.

### 2.5 Backbone and tuning modes

We evaluate two backbone families:

- `FeatureMLP`, which uses per-node or per-client feature information without explicit graph neighborhood propagation.
- `GraphSAGE`, which adds graph-structure-aware message passing and is expected to be more useful in the topology-heavy scenarios.

For GraphSAGE we also compare three tuning modes:

- `head_only`
- `adapter_ft`
- `full_ft`

This comparison allows us to study whether robustness gains require expensive end-to-end fine-tuning or can be retained under communication-efficient adaptation.

## 3. Experimental Setup

### 3.1 Scenario family

We evaluate five topology-aware real-graph pilot scenarios:

- `scenario_d_three_tier_low2`
- `scenario_e_three_tier_high2`
- `scenario_f_two_tier_high2`
- `scenario_g_mimic_congest`
- `scenario_h_mimic_heavy_overlap`

The scenarios differ in topology, overlap pattern, and congestion difficulty. Among them, `scenario_h` is the most important stress case for semantic overlap, while `scenario_f` is the harder two-tier setting. `scenario_g` is comparatively small and easy, which becomes important when interpreting near-saturation results.

### 3.2 Metrics

We report:

- test F1 as the main detection metric
- test recall
- test false positive rate (FPR)
- kept poisoned clients after trust filtering
- estimated communication bytes for tuning-mode comparison

### 3.3 Reproducibility protocol

Main claims are supported by both single-run cross-scenario summaries and dedicated seed sweeps on the critical settings. The most important five-seed studies cover `scenario_h`, `scenario_f`, a held-out `scenario_e` trust-aware-versus-keep-all comparison, and the re-evaluated `scenario_g` backbone comparison. We also add an auxiliary three-seed public NSL-KDD validation together with standard aggregation baselines under `update_noise@0.4`. Additional sensitivity sweeps vary `min_keep_per_group`, and a fixed-seed mechanism study isolates the worst-case `seed11` behavior under `scenario_h + update_noise@0.4`.

## 4. Results

### 4.1 Cross-scenario GraphSAGE robustness

Table 1 summarizes the single-run GraphSAGE mainline across the five scenarios.

| Scenario | Clean F1 | Sign-flip@0.4 F1 | Update-noise@0.4 F1 |
| --- | ---: | ---: | ---: |
| `scenario_d` | 0.9966 | 0.9966 | 0.9966 |
| `scenario_e` | 0.9826 | 0.9835 | 0.9835 |
| `scenario_f` | 0.9743 | 0.9720 | 0.9767 |
| `scenario_g` | 0.9756 | 0.9756 | 0.9938 |
| `scenario_h` | 0.9692 | 0.9696 | 0.9705 |

The cross-scenario picture is favorable. Even under both poisoning types, the GraphSAGE mainline remains in a narrow high-performance range and does not show a broad failure trend in the topology-heavy settings.

![Cross-scenario F1 heatmap](figures_sage_main/cross_scenario_f1_heatmap.png)

### 4.2 Five-seed robustness on the hard scenarios

Table 2 reports the five-seed GraphSAGE summary for the hardest scenarios.

| Scenario | Condition | Mean F1 | Std | Mean FPR |
| --- | --- | ---: | ---: | ---: |
| `scenario_h` | clean | 0.9785 | 0.0028 | 0.0243 |
| `scenario_h` | sign-flip@0.4 | 0.9797 | 0.0026 | 0.0212 |
| `scenario_h` | update-noise@0.4 | 0.9686 | 0.0130 | 0.0449 |
| `scenario_f` | clean | 0.9859 | 0.0021 | 0.0142 |
| `scenario_f` | sign-flip@0.4 | 0.9840 | 0.0039 | 0.0160 |
| `scenario_f` | update-noise@0.4 | 0.9867 | 0.0019 | 0.0136 |

Two points matter here. First, the repaired trust semantics preserve strong mean performance in both scenarios. Second, only `scenario_h + update-noise@0.4` shows visibly larger variance, which motivates the mechanism analysis later in this section.

### 4.3 Backbone comparison

GraphSAGE materially improves over FeatureMLP in the structurally harder setting. On `scenario_h`, the five-seed mean F1 rises from `0.9417` to `0.9785` in clean training and from `0.9512` to `0.9797` under sign-flip. These gains are statistically significant, with `p = 0.0095` for clean training and `p = 3.70e-4` under sign-flip.

At the same time, the updated paper should be careful not to overclaim. `scenario_g` no longer supports the earlier narrative that FeatureMLP clearly beats GraphSAGE there. The refreshed five-seed study shows near-saturated performance for both backbones:

- clean: FeatureMLP `0.9975`, GraphSAGE `1.0000`, `p = 0.3739`
- sign-flip@0.4: FeatureMLP `1.0000`, GraphSAGE `0.9988`, `p = 0.3739`

Thus, `scenario_g` should be described as a small saturated case with no significant backbone gap rather than as a stable GraphSAGE exception.

![Backbone comparison](figures_sage_main/backbone_comparison.png)

### 4.4 Tuning modes and communication efficiency

Table 3 summarizes the GraphSAGE tuning comparison on `scenario_h`.

| Condition | Tuning mode | F1 | FPR | Total bytes | Relative bytes vs full FT |
| --- | --- | ---: | ---: | ---: | ---: |
| sign-flip@0.4 | `head_only` | 0.9692 | 0.0748 | 13,200 | 2.08% |
| sign-flip@0.4 | `adapter_ft` | 0.9696 | 0.0530 | 123,600 | 19.45% |
| sign-flip@0.4 | `full_ft` | 0.9666 | 0.0935 | 635,600 | 100.00% |
| update-noise@0.4 | `head_only` | 0.9718 | 0.0592 | 13,200 | 2.08% |
| update-noise@0.4 | `adapter_ft` | 0.9705 | 0.0685 | 123,600 | 19.45% |
| update-noise@0.4 | `full_ft` | 0.9716 | 0.0467 | 635,600 | 100.00% |

These results support a practical claim for cyber-security deployment: the proposed defense does not depend on communication-heavy full-model fine-tuning. Under sign-flip, adapter tuning is better than full fine-tuning in both F1 and FPR while using only `19.45%` of the communication budget. Under update-noise, head-only tuning slightly exceeds full fine-tuning in F1 while using only `2.08%` of the bytes.

### 4.5 Aggregation comparison

Under `scenario_h + sign-flip@0.4`, hierarchical aggregation reaches mean `F1 = 0.9797` and mean `FPR = 0.0212`. Mean aggregation is numerically close in F1 (`0.9794`) and slightly lower in FPR (`0.0181`), while median and Krum-like aggregation are weaker at roughly `F1 = 0.976`.

The correct interpretation is not that hierarchical aggregation dominates every alternative on every metric, but that it remains a strong top-tier choice while aligning naturally with grouped trust filtering and semantic coverage preservation.

### 4.6 Sensitivity of `min_keep_per_group`

Table 4 shows the sensitivity sweep for the group-floor parameter.

| Condition | keep=0 F1 / FPR | keep=1 F1 / FPR | keep=2 F1 / FPR | Best interpretation |
| --- | --- | --- | --- | --- |
| clean | 0.9666 / 0.0935 | 0.9692 / 0.0779 | 0.9692 / 0.0779 | `keep=1` repairs coverage with no extra gain from `keep=2` |
| sign-flip@0.4 | 0.9692 / 0.0748 | 0.9696 / 0.0530 | 0.9685 / 0.0810 | `keep=1` is the best trade-off |
| update-noise@0.4 | 0.9705 / 0.0685 | 0.9705 / 0.0685 | 0.9712 / 0.0654 | `keep=2` starts retaining poisoned clients |

This is why `min_keep_per_group = 1` remains the mainline default. It is the most defensible compromise between semantic coverage and poisoning leakage. The parameter is no longer a hand-waved heuristic; it is now supported by an explicit sensitivity study.

![min_keep_per_group sensitivity](figures_sage_main/min_keep_per_group_sensitivity.png)

### 4.7 Held-out trust-aware versus keep-all validation on `scenario_e`

To strengthen external-facing credibility beyond the two central scenarios, we added a dedicated five-seed trust-aware-versus-keep-all comparison on the distinct `scenario_e_three_tier_high2` graph. This is a meaningful held-out validation point because `scenario_e` is not one of the two scenarios used to anchor the mainline robustness narrative and has a different topology/load composition.

| Condition | Trust-aware F1 / FPR | Keep-all F1 / FPR | Trust-aware kept poisoned | Keep-all kept poisoned | Interpretation |
| --- | --- | --- | ---: | ---: | --- |
| clean | 0.9881 / 0.0123 | 0.9881 / 0.0117 | 0.0 | 0.0 | effectively tied |
| sign-flip@0.4 | 0.9896 / 0.0216 | 0.9895 / 0.0204 | 3.8 | 4.0 | effectively tied, slightly fewer poisoned retained |
| update-noise@0.4 | 0.9879 / 0.0123 | 0.9890 / 0.0130 | 0.2 | 4.0 | near-neutral F1 cost, much lower poisoned retention |

The pattern matches the revised paper narrative. Trust-aware filtering is not a universal average-case F1 booster. Instead, it behaves as a conservative security control: on `scenario_e + update-noise@0.4`, it cuts retained poisoned clients from `4.0` to `0.2` while the mean-F1 gap remains small and non-significant (`p = 0.6867`). This is useful because it shows that the security benefit generalizes beyond `scenario_h` and `scenario_f` without requiring an exaggerated accuracy claim.

![Scenario-E trust-aware versus keep-all](figures_sage_main/scenario_e_trust_vs_keepall_seed_comparison.png)

### 4.8 Auxiliary public-benchmark validation on NSL-KDD

To complement the in-house scenario family with a public benchmark, we added an auxiliary external-validation experiment based on NSL-KDD. Because NSL-KDD is a public intrusion dataset rather than a same-distribution public bot benchmark, we use it only as auxiliary external validation rather than as a substitute for the topology-aware bot scenarios. The public records were converted into a feature-similarity graph and then passed through the same GraphSAGE federated pipeline. This still provides a public cyber-security dataset on which the trust-aware mechanism can be stress-tested under the same poisoned-update protocol.

The public results again support the paper's revised security-control framing. In the clean setting, trust-aware filtering reaches mean `F1 = 0.7595` versus `0.7666` for keep-all, but lowers mean `FPR` from `0.0671` to `0.0547`. Under `sign_flip@0.4`, mean F1 is effectively unchanged (`0.7587` versus `0.7583`) while retained poisoned clients fall from `4.0` to `2.33`. Under `update_noise@0.4`, mean F1 is again effectively tied (`0.7882` versus `0.7882`), mean `FPR` decreases from `0.0741` to `0.0629`, and retained poisoned clients decrease sharply from `4.0` to `0.33`. We further compare update-noise performance against standard aggregation baselines. Trust-aware hierarchical aggregation matches hierarchical keep-all in F1, exceeds `mean`, `median`, and `krum` in mean F1 on this public benchmark, and is the only tested method in this comparison that materially reduces retained poisoned participation.

![Public NSL-KDD trust-aware versus keep-all](figures_sage_main/public_nslkdd_trust_vs_keepall_seed_comparison.png)

### 4.9 Fixed-seed mechanism analysis of the worst case

The remaining question is why `scenario_h + update-noise@0.4` still shows higher variance than the other settings. The fixed-seed mechanism study isolates `seed11`, the worst seed in the five-seed sweep.

| `seed11` setting | F1 | FPR | Kept poisoned clients | Benign group retained |
| --- | ---: | ---: | ---: | ---: |
| `keep=0` | 0.9805 | 0.0156 | 0 | 0 / 2 |
| `keep=1` | 0.9496 | 0.1028 | 1 | 1 / 2 |
| `keep=2` | 0.9779 | 0.0374 | 2 | 2 / 2 |

This table clarifies the mechanism. In `seed11`, both clients in `role:benign_user` are poisoned. With `keep=0`, the system drops the entire benign group and therefore avoids poisoned retention, but it violates the group-coverage objective. With `keep=1`, the group-floor rule forces one poisoned benign client to become the sole representative of the group, producing the worst result. The retained client's final-round `trust_norm` is only `0.0106`, which confirms that the problem is not that the client looked healthy, but that the floor rule preserved it despite extremely low trust. With `keep=2`, both poisoned benign clients are retained and the result partially recovers. Under the current hierarchical aggregation scheme, this is plausible because two poisoned clients in the same small group are first averaged together before the global inter-group average, whereas a single poisoned representative can disproportionately define that group's contribution.

The most important conclusion is therefore methodological: the residual failure mode is a boundary case of the group-floor design under full small-group poisoning, not a sign that GraphSAGE itself is unstable.

![Seed11 keep-sweep mechanism](figures_sage_main/seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.png)

### 4.10 Conditional trust-mass floor hardening

The mechanism analysis suggests a small but meaningful fix: preserve the group floor only when the affected group's trust mass has not collapsed near zero. We therefore implemented a conditional trust-mass floor that only repairs a filtered group when that group's total normalized trust mass is at least `0.10`.

This hardening is near-neutral in the easier settings. On `scenario_h` clean training, the conditional variant reaches mean `F1 = 0.9776` versus `0.9785` for the static floor (`p = 0.6359`). Under `sign_flip@0.4`, the two variants are effectively tied at mean `F1 = 0.9797` (`p = 0.9946`), with nearly identical FPR and retained-poisoned behavior.

Under `update_noise@0.4`, however, the conditional rule repairs the precise failure mode identified above. Mean F1 increases from `0.9686` to `0.9766`, mean FPR decreases from `0.0449` to `0.0231`, retained poisoned clients decrease from `0.4` to `0.0`, and the seed-level F1 standard deviation drops from `0.0130` to `0.0050`. The improvement is especially clear in the previously worst seed: `seed11` improves from `F1 = 0.9496` and `FPR = 0.1028` under the static floor to `F1 = 0.9812` and `FPR = 0.0125`, while retaining no poisoned clients.

Broader checks suggest that this should remain a targeted hardening rather than a universal replacement. On held-out `scenario_e + update_noise@0.4`, the conditional rule is near-neutral to slightly positive (`F1 = 0.9891` versus `0.9879`) with the same low retained-poisoned count (`0.2`). On the auxiliary public NSL-KDD benchmark, however, it is more conservative: retained poisoned clients drop from `0.33` to `0.0` and mean FPR drops from `0.0629` to `0.0569`, but mean F1 also decreases from `0.7882` to `0.7611`. This does not justify rewriting the whole paper around the conditional rule, but it does show that the remaining edge-case weakness is patchable with a simple and interpretable modification in the topology-aware mainline.

## 5. Discussion

The updated experiments sharpen the paper's message in three useful ways.

First, the mainline story is now stronger and cleaner. GraphSAGE is robust across the multi-scenario benchmark, especially in the more topology-sensitive cases. The strongest claim is no longer "GraphSAGE wins everywhere," but rather "the proposed trust-aware grouped defense is robust, and GraphSAGE is its strongest instantiation on the harder scenarios."

Second, the communication result makes the system more publication-worthy from a cyber-security deployment perspective. It is easier to argue practical relevance when the best or near-best results do not depend on the most expensive fine-tuning regime.

Third, the new `scenario_e` held-out comparison and auxiliary public NSL-KDD validation make the claims more publication-safe. Together they show that the trust-aware mechanism remains useful off the mainline scenarios, but in the more honest sense of poisoned-retention reduction and false-positive control rather than universal F1 improvement.

Fourth, the mechanism study improves credibility. Security papers are often weakened by unexplained variance or by overly polished narratives that do not survive deeper scrutiny. Here, the additional fixed-seed analysis makes the remaining weakness explicit and interpretable: the design can still fail when a small semantic group is fully poisoned and a static coverage floor insists on preserving that group. The new conditional trust-mass floor then shows that this weakness is not fatal to the overall method and can be substantially repaired on the topology-aware mainline, even though the same hardening is not uniformly beneficial on the auxiliary public benchmark.

## 6. Limitations

- The evaluation now includes topology-aware pilot benchmarks plus one auxiliary public cyber-security dataset, but it is still not a live production deployment.
- The conditional trust-mass floor now repairs the identified `scenario_h + update-noise@0.4` edge case and remains near-neutral on held-out `scenario_e`, but its auxiliary public NSL-KDD behavior is mixed, so it should currently be treated as a targeted extension rather than a universal replacement.
- The scenario family is already useful and nontrivial, and the new public NSL-KDD result improves external validity, but broader cross-dataset validation would still strengthen the paper further because `NSL-KDD` is not a same-distribution public bot benchmark.
- The stronger comparison set now includes keep-all controls, public auxiliary validation, and classical robust aggregators, but it still does not exhaust newer dynamic abstention or personalized robust-FL defenses.

## 7. Conclusion

HiTrust-FedBot shows that robust federated web bot detection in congested edge environments benefits from combining trust-aware filtering with structure-preserving grouped aggregation. The GraphSAGE-based mainline achieves strong performance across the harder topology-aware scenarios under both clean and poisoned training, while parameter-efficient tuning substantially reduces communication cost without sacrificing effectiveness. The additional sensitivity and fixed-seed studies make the remaining trade-off explicit: preserving semantic group coverage is valuable, but a static group floor can become harmful when a small group is fully poisoned. The conditional trust-mass hardening added here further shows that this edge case can be substantially repaired with a small and interpretable modification on the topology-aware mainline, improving the maturity of the method without changing its core security-control framing.

## 8. Declarations

### 8.1 Availability of data and materials

The derived topology-aware pilot graph artifacts used in the main experiments are included in the repository under `data_hitrust/bootstrap_graphs/graphs/`. These artifacts are distributed as derived graph objects rather than as raw collection data. The auxiliary public NSL-KDD validation graph and metadata are included under `data_hitrust/public_benchmarks/nsl_kdd/` and can be regenerated with `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`.

### 8.2 Code availability

The code, experiment configurations, run summaries, tables, figures, and reproduction scripts supporting this manuscript are included in the repository. The auxiliary public-benchmark validation can be reproduced with `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`. The targeted conditional-floor hardening validation can be reproduced with `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`.

### 8.3 Competing interests

Competing-interest disclosures should be confirmed by all authors at submission. If no competing interests apply, the journal-form statement should read: `The authors declare that they have no competing interests.`

### 8.4 Funding

Funding information should be confirmed by the authors at submission. If no external funding applies, the journal-form statement should read: `This research received no external funding.`

### 8.5 Authors' contributions

Author-contribution roles should be inserted on the identified title page or in the journal submission system using a CRediT-style summary consistent with the final author list.

### 8.6 Acknowledgments

Institutional acknowledgments and any funding-specific acknowledgments should be restored on the identified title page or in the final journal template if applicable.

## 9. Reproducibility and Artifact Map

Main manuscript-supporting files in this repository:

- Main rewrite notes: `paper_hitrust/manuscript_cyber_rewrite_20260323.md`
- This full draft: `paper_hitrust/manuscript_cyber_submission_full_20260323.md`
- Cross-scenario matrix: `paper_hitrust/tables/cross_scenario_sage_full_matrix.json`
- Hard-scenario seed summary: `paper_hitrust/tables/hard_case_sage_seed_summary.json`
- Backbone summary: `paper_hitrust/tables/backbone_pilot_summary.json`
- Backbone delta table: `paper_hitrust/tables/cross_scenario_backbone_delta.json`
- Scenario G seed comparison: `paper_hitrust/tables/scenario_g_backbone_seed_comparison.json`
- Scenario G significance: `paper_hitrust/tables/scenario_g_backbone_clean_f1_significance.json`
- Scenario G significance: `paper_hitrust/tables/scenario_g_backbone_sign_flip_frac0p4_f1_significance.json`
- Scenario E trust-vs-keep-all comparison: `paper_hitrust/tables/scenario_e_trust_vs_keepall_seed_comparison.json`
- Scenario E clean seed stats: `paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_clean_seed_stats.json`
- Scenario E sign-flip seed stats: `paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_sign_flip_frac0p4_seed_stats.json`
- Scenario E update-noise seed stats: `paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_seed_stats.json`
- Public NSL-KDD build summary: `data_hitrust/public_benchmarks/nsl_kdd/meta/nsl_kdd_public_build_summary.json`
- Public NSL-KDD trust-vs-keep-all comparison: `paper_hitrust/tables/public_nslkdd_trust_vs_keepall_seed_comparison.json`
- Public NSL-KDD update-noise baseline comparison: `paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json`
- Conditional-floor hardening script: `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`
- Scenario-H conditional-floor comparison: `paper_hitrust/tables/scenario_h_update_noise_condfloor_comparison.json`
- Scenario-E conditional-floor comparison: `paper_hitrust/tables/scenario_e_update_noise_condfloor_comparison.json`
- Public NSL-KDD conditional-floor comparison: `paper_hitrust/tables/public_nslkdd_update_noise_condfloor_comparison.json`
- Artifact release notes: `docs/ARTIFACT_RELEASE_20260324.md`
- Artifact manifest: `paper_hitrust/artifact_manifest_20260324.json`
- Group-floor sensitivity: `paper_hitrust/tables/min_keep_per_group_sage_sensitivity.json`
- Update-noise trust diagnosis: `paper_hitrust/tables/scenario_h_sage_update_noise_frac0p4_trust_diagnosis_summary.json`
- Fixed-seed keep sweep summary: `paper_hitrust/tables/seed11_keep_sweep_h_sage_update_noise_frac0p4_summary.json`
- Fixed-seed keep sweep diagnostics: `paper_hitrust/tables/seed11_keep_sweep_h_sage_update_noise_frac0p4_trust_diagnostics.json`
- Fixed-seed keep sweep mechanism table: `paper_hitrust/tables/seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.json`

## 10. Submission Package Notes

- Suggested submission-support files are prepared under `docs/`, including a title-page template, a cover-letter draft, and a journal-oriented checklist.
- Remaining author-supplied items are limited to the final author list, affiliations, corresponding-author details, contribution roles, and the final funding / competing-interest confirmations.
- Bibliography and section content are now aligned with the polished submission draft; the remaining formatting work is primarily journal-template normalization.
- Figure placement can now be finalized by choosing which mechanism and auxiliary-validation figures stay in the main paper versus supplementary material.
