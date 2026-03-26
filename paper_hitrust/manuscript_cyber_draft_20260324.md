# HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering

Author identities, affiliations, and correspondence details are intentionally separated into the submission title page. See `docs/CYBERSECURITY_TITLE_PAGE_TEMPLATE_20260324.md`.

This draft consolidates the current strongest manuscript framing as of `2026-03-24` and is intended as the editable base for journal-template formatting.

## Abstract

Federated web bot detection in congested edge environments must tolerate topology heterogeneity, limited communication budgets, and adversarial client participation. In this setting, naive trust filtering is brittle: a strict filter can suppress poisoned updates, but it can also erase an entire semantic client group and destabilize the global detector. We present HiTrust-FedBot, a trust-aware hierarchical federated detection framework that combines grouped aggregation with a group-coverage-constrained trust filter. The framework is instantiated with a GraphSAGE backbone and evaluated on five topology-aware scenarios under clean training, sign-flip poisoning, and update-noise poisoning at a malicious-client fraction of 40%. On the challenging `scenario_h`, the GraphSAGE mainline reaches mean test F1 of `0.9785` in the clean setting, `0.9797` under sign-flip, and `0.9686` under update-noise across five seeds. On the harder `scenario_f`, the corresponding means are `0.9859`, `0.9840`, and `0.9867`. Relative to a FeatureMLP baseline, GraphSAGE yields significant gains on `scenario_h` in both clean (`p = 0.0095`) and sign-flip (`p = 3.70e-4`) conditions, whereas the smaller `scenario_g` shows no significant backbone gap (`p = 0.3739`). A communication study further shows that parameter-efficient tuning preserves performance while reducing total communication by `80.6%` to `97.9%` relative to full fine-tuning. A held-out `scenario_e` comparison shows that trust-aware filtering reduces retained poisoned clients from `4.0` to `0.2` under `update_noise@0.4` with only a small and non-significant mean-F1 change. An auxiliary public NSL-KDD validation further shows near-neutral mean F1 under poisoned training while reducing retained poisoned clients from `4.0` to `0.33`. Fixed-seed and conditional-hardening analyses show that the remaining worst-case variance arises from a fully poisoned small group under the static group-floor rule rather than from a general GraphSAGE instability. These results position HiTrust-FedBot as a conservative and interpretable security control for adversarial federated bot detection in edge-constrained environments.

**Keywords:** federated learning, bot detection, adversarial robustness, trust-aware aggregation, GraphSAGE, edge security

## 1. Introduction

Federated learning offers an appealing deployment model for web bot detection when raw traffic or graph data cannot be centralized due to privacy, bandwidth, or governance constraints [1,2]. However, realistic federated security systems must handle three sources of instability simultaneously: heterogeneous client data, constrained communication, and malicious client behavior. These pressures are particularly severe in graph-based bot detection, where structural heterogeneity is not noise to be averaged away but a central part of the detection signal.

Conventional robust federated aggregation focuses on suppressing malicious or low-quality updates [6-9]. That objective is necessary but incomplete in topology-aware cyber-security settings. When client populations are semantically partitioned, aggressive filtering may remove not only poisoned updates but also the only remaining representatives of a particular group. The global model then becomes better filtered but less representative. In practice, this creates a tension between robustness against poisoning and preservation of semantic coverage.

This paper addresses that tension with HiTrust-FedBot, a trust-aware hierarchical federated framework for web bot detection. The framework combines three design choices: client-level trust scoring, grouped hierarchical aggregation, and a group-coverage-constrained trust filter. The last component enforces a minimum retained-client floor per group, preventing the federation from silently discarding an entire semantic slice of the population. We study the method with both FeatureMLP and GraphSAGE backbones and show that the GraphSAGE instantiation is consistently stronger on the harder scenarios.

The paper makes four contributions.

- It introduces a grouped trust-aware aggregation pipeline tailored to topology-aware federated bot detection.
- It formalizes a group-coverage-constrained trust filter and shows why this design is more appropriate than a purely flat score-threshold rule in semantically partitioned federations.
- It demonstrates that GraphSAGE materially strengthens the defense on the harder topology-sensitive settings while preserving a practical communication profile under parameter-efficient tuning.
- It provides a mechanism-grounded analysis of the remaining failure mode through sensitivity, held-out validation, auxiliary public validation, and conditional hardening experiments.

## 2. Related Work

### 2.1 Federated cyber-security detection

Recent studies have applied federated learning to intrusion detection, malicious traffic classification, and related cyber-security monitoring tasks because these domains naturally involve distributed data ownership and privacy constraints [3-5]. A common finding in this literature is that federated deployment improves data locality but also amplifies statistical heterogeneity and non-IID effects [3,4]. Our setting is aligned with this line of work but focuses more specifically on graph-structured web bot detection in congested edge environments, where the challenge is not only client drift but also structural fragmentation across client partitions.

### 2.2 Robust federated learning under poisoning

A second body of work studies federated robustness under Byzantine, backdoor, and update-poisoning attacks, typically through robust aggregators, anomaly scoring, client selection, or trust-based defenses [6-9]. These methods are directly relevant because our threat model includes poisoned client updates. However, much of the robust federated learning literature is designed for flat client pools and does not explicitly account for semantic group coverage. In such settings, dropping all low-trust clients may be acceptable; in our setting, the same action may erase an entire group and distort the final detector. HiTrust-FedBot extends the trust-filtering perspective by coupling poisoning resistance with group-preservation constraints.

### 2.3 Graph learning for security analytics

Graph neural networks have become increasingly important in cyber-security tasks such as intrusion detection, social-bot analysis, fraud analysis, and anomalous behavior discovery because relational structure often contains information that feature-only models miss [10-12]. In particular, neighborhood aggregation methods such as GraphSAGE are attractive in distributed settings because they balance expressive structural learning with manageable model complexity [12,13]. Our experiments confirm that this structural advantage matters in the harder topology-aware scenarios: GraphSAGE substantially outperforms FeatureMLP on `scenario_h`, while the smaller `scenario_g` saturates for both backbones and therefore should not be overinterpreted.

### 2.4 Communication-efficient adaptation in federated systems

Communication-efficient federated optimization and parameter-efficient adaptation have also received considerable attention, especially for large or frequently updated models [1,14-16]. This literature motivates our comparison among `head_only`, `adapter_ft`, and `full_ft` tuning modes. Rather than treating communication as a purely systems-level add-on, we evaluate it jointly with adversarial robustness. The practical result is important: the strongest or near-strongest settings in our study do not require the highest communication budget.

### 2.5 Position of this work

HiTrust-FedBot sits at the intersection of these lines of work. It is a federated cyber-security detector, a poisoning-aware trust-filtering defense, a graph-based structural learner, and a communication-conscious adaptation study. The main distinction from prior trust-based robust federated methods is the explicit treatment of semantic group coverage as a first-class constraint. This design choice changes not only average-case behavior but also the interpretation of edge cases, which we analyze directly through sensitivity and fixed-seed mechanism experiments.

## 3. Method

### 3.1 Problem setting

We consider a federated bot-detection system with a central server and multiple edge clients. Each client trains locally on a traffic-derived graph partition and uploads model updates rather than raw data. Let the clients be partitioned into semantic groups induced by topology or role-aware partition metadata. The server must aggregate client updates while resisting poisoned participants and preserving useful group-level information.

### 3.2 Threat model

We consider malicious clients that participate in training and poison the federated update stream. Two attack types are studied in the main experiments:

- `sign_flip@0.4`: 40% of clients invert or directionally corrupt their model updates.
- `update_noise@0.4`: 40% of clients inject strong perturbation noise into the update stream.

The attacker does not need to compromise all clients. The operational question is whether the global model can remain effective when a minority of clients are malicious and when some semantic groups are smaller, structurally fragile, or more weakly represented than others.

### 3.3 Trust-aware hierarchical aggregation

HiTrust-FedBot assigns each participating client a trust score derived from validation behavior and update characteristics. Retained client updates are not aggregated in a single flat pool. Instead, updates are first aggregated within each semantic group, and the group-level aggregates are then combined into the final global update. This hierarchical structure reduces the risk that dominant groups overwhelm smaller ones and provides a natural interface for group-aware filtering.

### 3.4 Group-coverage-constrained trust filtering

The central design choice is the group-coverage-constrained trust filter. After threshold-based trust filtering, the server enforces a minimum retained-client floor per group, denoted `min_keep_per_group`. The repaired mainline used in this paper sets `min_keep_per_group = 1`. This rule prevents the silent disappearance of a group whose clients all receive low trust in a particular round.

The constraint introduces a controlled trade-off. If the floor is set too low, semantic coverage can collapse. If it is set too high, poisoned clients may survive filtering in compromised groups. We therefore treat `min_keep_per_group` as an interpretable security parameter rather than a purely empirical tuning detail.

Because a static floor can still preserve a fully compromised small group, we also evaluate a lightweight conditional variant in which the floor-repair step is skipped when a group's total normalized trust mass collapses below a small threshold. In the targeted hardening study reported later, this threshold is set to `0.10`, turning the floor into an abstaining coverage rule for near-zero-trust groups.

### 3.5 Backbone and adaptation modes

We evaluate FeatureMLP and GraphSAGE [13] backbones to distinguish feature-only and graph-structural learning. For GraphSAGE we further compare three adaptation regimes: `head_only`, `adapter_ft`, and `full_ft`. This design allows us to assess whether robustness improvements depend on communication-heavy full-model updates or can be retained under lighter adaptation.

## 4. Experimental Setup

### 4.1 Scenario family and attacks

Experiments are conducted on five topology-aware scenarios: `scenario_d_three_tier_low2`, `scenario_e_three_tier_high2`, `scenario_f_two_tier_high2`, `scenario_g_mimic_congest`, and `scenario_h_mimic_heavy_overlap`. We report clean training together with two poisoning settings: `sign_flip@0.4` and `update_noise@0.4`, where 40% of clients are malicious.

### 4.2 Metrics

We report test F1 as the primary accuracy metric, together with test recall, test false positive rate (FPR), retained poisoned clients after filtering, and estimated communication cost for tuning-mode comparison.

### 4.3 Evaluation protocol

The evaluation combines cross-scenario single-run summaries, dedicated five-seed sweeps on the hardest settings, a held-out `scenario_e` trust-aware-versus-keep-all comparison, an auxiliary three-seed public NSL-KDD validation, a backbone significance analysis, a communication study, a sensitivity sweep over `min_keep_per_group`, and a fixed-seed mechanism study centered on the worst-case `scenario_h + update_noise@0.4 + seed11` configuration.

## 5. Results

### 5.1 Overall robustness across scenarios

The single-run cross-scenario GraphSAGE matrix shows strong performance throughout the scenario family. Test F1 ranges from `0.9692` to `0.9966` in the clean setting, from `0.9696` to `0.9966` under sign-flip, and from `0.9705` to `0.9966` under update-noise. The most demanding case is `scenario_h`, where the GraphSAGE mainline reaches `F1 = 0.9692` in the clean setting, `0.9696` under sign-flip, and `0.9705` under update-noise. These results indicate that the repaired trust semantics preserve the mainline across heterogeneous topology regimes rather than merely on a narrow subset of scenarios.

At the five-seed level, the hardest settings remain strong. On `scenario_h`, mean F1 is `0.9785 +/- 0.0028` in the clean setting, `0.9797 +/- 0.0026` under sign-flip, and `0.9686 +/- 0.0130` under update-noise. On `scenario_f`, the corresponding means are `0.9859 +/- 0.0021`, `0.9840 +/- 0.0039`, and `0.9867 +/- 0.0019`. The only materially elevated variance appears in `scenario_h + update_noise@0.4`, which motivates the targeted mechanism study in Section 5.6.

![Cross-scenario F1 heatmap](figures_sage_main/cross_scenario_f1_heatmap.png)

### 5.2 Backbone comparison

GraphSAGE provides the clearest benefit in the structurally harder `scenario_h`. Across five seeds, FeatureMLP reaches mean F1 of `0.9417` in the clean setting and `0.9512` under sign-flip, whereas GraphSAGE reaches `0.9785` and `0.9797`, respectively. These gains are statistically significant, with `p = 0.0095` for the clean setting and `p = 3.70e-4` under sign-flip. The single-run comparison also shows a large false-positive-rate reduction, from `0.1931` to `0.0779` in the clean setting and from `0.1433` to `0.0530` under sign-flip.

The interpretation of `scenario_g` is different. After the refreshed five-seed sweep, the setting is better characterized as saturated rather than contradictory. Clean performance is `0.9975` for FeatureMLP and `1.0000` for GraphSAGE, while sign-flip performance is `1.0000` and `0.9988`, respectively; neither comparison is significant (`p = 0.3739`). Accordingly, `scenario_g` should be read as an easy regime in which both backbones approach ceiling performance, not as evidence against the structural value of GraphSAGE.

![Backbone comparison](figures_sage_main/backbone_comparison.png)

### 5.3 Communication-efficient tuning

The tuning study shows that strong robustness does not require the most expensive adaptation regime. Under `scenario_h + sign_flip@0.4`, `adapter_ft` reaches `F1 = 0.9696` and `FPR = 0.0530` while using only `19.45%` of the communication cost of `full_ft`. `head_only` reaches `F1 = 0.9692` while using `2.08%` of the full fine-tuning budget. By contrast, `full_ft` reaches `F1 = 0.9666` with a higher `FPR = 0.0935`.

Under `scenario_h + update_noise@0.4`, the three tuning modes are closer in F1, but the efficient modes remain highly competitive. `head_only` slightly exceeds `full_ft` in F1 (`0.9718` versus `0.9716`) while using only `2.08%` of the communication volume. `adapter_ft` remains within `0.0011` F1 of `full_ft` while reducing communication by `80.55%`. These results strengthen the deployment relevance of the framework: robust federated bot detection need not rely on communication-heavy full-model adaptation.

### 5.4 Held-out trust-aware versus keep-all validation

To strengthen the paper beyond the main `scenario_h` and `scenario_f` storyline, we added a dedicated five-seed trust-aware-versus-keep-all comparison on the distinct held-out `scenario_e_three_tier_high2` graph. This scenario differs from the mainline graphs in topology and load composition and therefore serves as a more external-style validation point rather than a duplicate robustness sweep.

In the clean setting, trust-aware filtering and keep-all are effectively tied (`F1 = 0.9881` versus `0.9881`). Under `sign_flip@0.4`, they again remain indistinguishable in mean F1 (`0.9896` versus `0.9895`), with trust-aware retaining slightly fewer poisoned clients (`3.8` versus `4.0`). Under `update_noise@0.4`, trust-aware reduces retained poisoned clients from `4.0` to `0.2` while incurring only a small and non-significant mean-F1 change (`0.9879` versus `0.9890`, `p = 0.6867`). This held-out comparison reinforces the conservative interpretation of the method: the primary benefit is sharply reducing poisoned participation at near-neutral accuracy cost, not universally boosting average F1.

![Scenario-E trust-aware versus keep-all](figures_sage_main/scenario_e_trust_vs_keepall_seed_comparison.png)

### 5.5 Auxiliary public-benchmark validation

To reduce the risk that the main results are dismissed as scenario-specific, we added an auxiliary public cyber-security benchmark based on NSL-KDD. Because NSL-KDD is a public intrusion dataset rather than a same-distribution public bot benchmark, we use it only as an auxiliary external validation point. The public records were converted into a feature-similarity graph so that the same GraphSAGE federated pipeline could be applied without changing the core training logic.

The public benchmark again supports the conservative interpretation of the method. In the clean setting, trust-aware filtering yields slightly lower mean F1 than keep-all (`0.7595` versus `0.7666`) but also lowers mean FPR (`0.0547` versus `0.0671`). Under `sign_flip@0.4`, mean F1 is effectively unchanged (`0.7587` versus `0.7583`) while retained poisoned clients fall from `4.0` to `2.33`. Under `update_noise@0.4`, mean F1 is effectively tied (`0.7882` versus `0.7882`), mean FPR drops from `0.0741` to `0.0629`, and retained poisoned clients drop sharply from `4.0` to `0.33`. Additional update-noise baselines show that trust-aware hierarchical aggregation matches hierarchical keep-all in F1 and exceeds the `mean`, `median`, and `krum` baselines in mean F1 on this public benchmark, while uniquely reducing retained poisoned participation.

![Public NSL-KDD trust-aware versus keep-all](figures_sage_main/public_nslkdd_trust_vs_keepall_seed_comparison.png)

### 5.6 Sensitivity and mechanism analysis

The sensitivity study over `min_keep_per_group` provides the main justification for the repaired trust semantics. In the clean setting, moving from `keep=0` to `keep=1` raises F1 from `0.9666` to `0.9692` and lowers FPR from `0.0935` to `0.0779`, while `keep=2` adds no further benefit. Under sign-flip, `keep=1` again provides the best trade-off with `F1 = 0.9696` and `FPR = 0.0530`, outperforming both `keep=0` and `keep=2`. Under update-noise, `keep=0` and `keep=1` are tied on average, whereas `keep=2` slightly improves mean F1 but begins to retain poisoned clients. Taken together, these results support `min_keep_per_group = 1` as the most defensible default operating point.

The fixed-seed mechanism study isolates the residual worst-case behavior in `scenario_h + update_noise@0.4`. In `seed11`, both clients in `role:benign_user` are poisoned. With `min_keep_per_group = 0`, the trust filter removes the entire benign group, retains no poisoned clients, and achieves `F1 = 0.9805` with `FPR = 0.0156`; however, this violates the semantic-coverage objective. With `min_keep_per_group = 1`, the group-floor rule forces one poisoned benign client to represent the group, producing the worst outcome, `F1 = 0.9496` and `FPR = 0.1028`, even though the retained client has `trust_norm = 0.0106`. With `min_keep_per_group = 2`, both poisoned benign clients are retained and performance partially recovers to `F1 = 0.9779` and `FPR = 0.0374`.

This result clarifies the mechanism behind the residual variance. The problem is not a general collapse of the GraphSAGE backbone. Instead, it is a narrow edge case of the group-floor rule under full poisoning of a small semantic group. Under the current hierarchical aggregator, two poisoned clients retained within the same small group can be less damaging than forcing one poisoned client to become that group's sole representative.

![min_keep_per_group sensitivity](figures_sage_main/min_keep_per_group_sensitivity.png)

![Seed11 keep-sweep mechanism](figures_sage_main/seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.png)

### 5.7 Conditional trust-mass floor hardening

We therefore implemented a lightweight conditional trust-mass floor that only repairs a filtered group when that group's total normalized trust mass is at least `0.10`. This directly targets the mechanism exposed above without changing the broader training pipeline. On `scenario_h` in the clean setting, mean F1 is nearly unchanged at `0.9776` versus `0.9785` for the static floor (`p = 0.6359`). Under `sign_flip@0.4`, the two variants are again effectively tied at `0.9797` mean F1 (`p = 0.9946`).

Under `update_noise@0.4`, however, the conditional rule materially improves the boundary case. Mean F1 rises from `0.9686` to `0.9766`, mean FPR drops from `0.0449` to `0.0231`, retained poisoned clients drop from `0.4` to `0.0`, and the seed-level F1 standard deviation shrinks from `0.0130` to `0.0050`. Most importantly, the worst previously identified seed is repaired: `seed11` moves from `F1 = 0.9496` and `FPR = 0.1028` under the static floor to `F1 = 0.9812` and `FPR = 0.0125` under the conditional rule, with no retained poisoned clients.

Broader validation suggests that this hardening should be treated as a targeted extension rather than as a universal replacement. On held-out `scenario_e + update_noise@0.4`, it is near-neutral to slightly positive (`F1 = 0.9891` versus `0.9879`) with the same low retained-poisoned count (`0.2`). On the auxiliary public NSL-KDD benchmark, by contrast, it further reduces retained poisoned clients (`0.0` versus `0.33`) and lowers mean FPR (`0.0569` versus `0.0629`), but also lowers mean F1 (`0.7611` versus `0.7882`). The conditional floor is therefore best interpreted as a topology-aware hardening for the identified small-group-collapse failure mode, not as the new universal mainline default.

## 6. Discussion

The updated evidence supports a more disciplined paper narrative than a broad "trust-aware filtering universally improves F1" claim. The stronger statement is that trust-aware grouped aggregation is effective across heterogeneous and adversarial federated bot-detection scenarios, and that GraphSAGE is the strongest tested instantiation in the harder topology-sensitive settings.

This distinction matters for publication quality. First, it aligns the paper with a method contribution rather than a model-brand claim. Second, it treats `scenario_g` appropriately as a saturation case rather than as inconvenient noise. Third, the held-out `scenario_e` and auxiliary public NSL-KDD results now show that the trust-aware mechanism remains useful outside the two central scenarios, but in the more honest sense of poisoned-retention reduction and false-positive control rather than universal F1 gain. Fourth, the fixed-seed study improves the credibility of the work precisely because it explains the remaining weak point instead of obscuring it.

The conditional trust-mass floor further shows that the principal boundary case is repairable with a small and interpretable change on the topology-aware mainline. At the same time, its mixed NSL-KDD behavior prevents overgeneralization. This is a useful outcome for a cyber-security paper: the method becomes more mature not because every new variant improves every benchmark, but because the paper can now explain what the hardening fixes, where it helps, and where its trade-off remains visible.

## 7. Limitations

The study still has four limitations.

- The experiments are conducted on topology-aware pilot scenarios together with one auxiliary public cyber-security benchmark rather than a live production deployment.
- The conditional trust-mass floor repairs the identified `scenario_h + update_noise@0.4` failure mode and remains near-neutral on held-out `scenario_e`, but its public NSL-KDD behavior is mixed, so it should be viewed as a targeted extension rather than a universally superior operating point.
- Although the new public NSL-KDD result improves external validity, it remains an auxiliary intrusion benchmark rather than a same-distribution public bot benchmark, so the external-validity question is strengthened but not closed.
- The baseline set now includes keep-all controls and classical robust aggregators, but it still does not exhaust newer dynamic abstention or personalized robust federated-learning defenses.

## 8. Conclusion

HiTrust-FedBot shows that adversarially robust federated web bot detection benefits from combining trust-aware filtering with structure-preserving grouped aggregation. The GraphSAGE mainline achieves strong performance across the harder topology-aware scenarios under both clean and poisoned training, while parameter-efficient tuning sharply reduces communication cost without sacrificing effectiveness. The additional sensitivity and fixed-seed analyses further show that the remaining worst-case behavior is not a general backbone instability but a specific boundary case of the group-floor design under full small-group poisoning. A lightweight conditional trust-mass floor then shows that this boundary case can be substantially repaired on the topology-aware mainline without degrading the cleaner settings, even though its broader auxiliary-benchmark behavior remains mixed. This makes the framework more mature methodologically while preserving the paper's conservative security-control framing.

## Acknowledgments

Institutional acknowledgments and any funding-specific acknowledgments should be restored on the identified title page or in the final journal template if applicable.

## Declarations

### Availability of data and materials

The derived topology-aware pilot graph artifacts used in the main experiments are included in the repository under `data_hitrust/bootstrap_graphs/graphs/`. These files are distributed as derived graph objects rather than as raw collection data. The auxiliary public NSL-KDD validation graph and metadata are included under `data_hitrust/public_benchmarks/nsl_kdd/` and can be regenerated with `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`.

### Code availability

The code, experiment configurations, run summaries, tables, figures, and reproduction scripts supporting this manuscript are included in the repository. The auxiliary public-benchmark validation can be reproduced with `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`. The targeted conditional-floor hardening validation can be reproduced with `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`.

### Competing interests

Competing-interest disclosures should be confirmed by all authors at submission. If no competing interests apply, the journal-form statement should read: `The authors declare that they have no competing interests.`

### Funding

Funding information should be confirmed by the authors at submission. If no external funding applies, the journal-form statement should read: `This research received no external funding.`

### Authors' contributions

Author-contribution roles should be inserted on the identified title page or in the journal submission system using a CRediT-style summary consistent with the final author list.

## References

[1] H. Brendan McMahan, Eider Moore, Daniel Ramage, Seth Hampson, and Blaise Aguera y Arcas. Communication-Efficient Learning of Deep Networks from Decentralized Data. In *Proceedings of the 20th International Conference on Artificial Intelligence and Statistics (AISTATS)*, PMLR 54, pages 1273-1282, 2017.

[2] Peter Kairouz et al. Advances and Open Problems in Federated Learning. *Foundations and Trends in Machine Learning*, 14(1-2):1-210, 2021.

[3] Jose L. Hernandez-Ramos, Georgios Karopoulos, Efstratios Chatzoglou, Vasileios Kouliaridis, Enrique Marmol, Aurora Gonzalez-Vidal, and Georgios Kambourakis. Intrusion Detection based on Federated Learning: a Systematic Review. *arXiv preprint arXiv:2308.09522*, 2023.

[4] Mohamed Amine Ferrag, Oussama Friha, Leandros Maglaras, Helge Janicke, and Lingyu Shu. Federated Deep Learning for Cyber Security in the Internet of Things: Concepts, Applications, and Experimental Analysis. *IEEE Access*, 9:138509-138542, 2021.

[5] Najet Hamdi. Federated Learning-Based Intrusion Detection System for Internet of Things. *International Journal of Information Security*, 22:1937-1948, 2023.

[6] Peva Blanchard, El Mahdi El Mhamdi, Rachid Guerraoui, and Julien Stainer. Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent. In *Advances in Neural Information Processing Systems 30 (NeurIPS)*, pages 119-129, 2017.

[7] Dong Yin, Yudong Chen, Ramchandran Kannan, and Peter Bartlett. Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates. In *Proceedings of the 35th International Conference on Machine Learning (ICML)*, PMLR 80, pages 5650-5659, 2018.

[8] Xiaoyu Cao, Minghong Fang, Jia Liu, and Neil Zhenqiang Gong. FLTrust: Byzantine-Robust Federated Learning via Trust Bootstrapping. In *Network and Distributed System Security Symposium (NDSS)*, 2021.

[9] Eugene Bagdasaryan, Andreas Veit, Yiqing Hua, Deborah Estrin, and Vitaly Shmatikov. How To Backdoor Federated Learning. In *Proceedings of the 23rd International Conference on Artificial Intelligence and Statistics (AISTATS)*, PMLR 108, pages 2938-2948, 2020.

[10] Tristan Bilot, Nour El Madhoun, Khaldoun Al Agha, and Anis Zouaoui. Graph Neural Networks for Intrusion Detection: A Survey. *IEEE Access*, 11:49114-49139, 2023.

[11] Feng Liu, Zhenyu Li, Chunfang Yang, Daofu Gong, Haoyu Lu, and Fenlin Liu. SEGCN: a Subgraph Encoding Based Graph Convolutional Network Model for Social Bot Detection. *Scientific Reports*, 14:4122, 2024.

[12] Zonghan Wu, Shirui Pan, Fengwen Chen, Guodong Long, Chengqi Zhang, and Philip S. Yu. A Comprehensive Survey on Graph Neural Networks. *IEEE Transactions on Neural Networks and Learning Systems*, 32(1):4-24, 2021.

[13] William L. Hamilton, Rex Ying, and Jure Leskovec. Inductive Representation Learning on Large Graphs. In *Advances in Neural Information Processing Systems 30 (NeurIPS)*, 2017.

[14] Keith Bonawitz et al. Towards Federated Learning at Scale: System Design. *Proceedings of Machine Learning and Systems*, 1, 2019.

[15] Neil Houlsby, Andrei Giurgiu, Stanislaw Jastrzebski, Bruna Morrone, Quentin de Laroussilhe, Andrea Gesmundo, Mona Attariyan, and Sylvain Gelly. Parameter-Efficient Transfer Learning for NLP. In *Proceedings of the 36th International Conference on Machine Learning (ICML)*, PMLR 97, pages 2790-2799, 2019.

[16] Daoyuan Chen, Liuyi Yao, Dawei Gao, Bolin Ding, and Yaliang Li. Efficient Personalized Federated Learning via Sparse Model-Adaptation. In *Proceedings of the 40th International Conference on Machine Learning (ICML)*, PMLR 202, pages 5234-5256, 2023.
