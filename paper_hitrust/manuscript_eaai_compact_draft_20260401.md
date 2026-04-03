# HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering

Author identities, affiliations, and correspondence details should remain on the separate title page for submission formatting.

## Abstract

Edge-side web bot detection is a practical engineering-AI problem because raw graph-structured traffic data often cannot be centralized, yet deployed federated systems must handle non-IID clients, communication budgets, and malicious participants at the same time. We present HiTrust-FedBot, a trust-aware hierarchical federated GraphSAGE framework that treats semantic group coverage as an explicit engineering constraint and augments trust filtering with targeted hardening for identified failure modes. The evaluation covers internal topology-aware pilots, same-task public Ca-Bench `scenario_e` and `scenario_h` validation, and auxiliary public NSL-KDD transfer. Key public claims use matched 10-seed paired evaluation and compare against keep-all, classical robust aggregation, modern aggregation-only and pre-aggregation comparators (Centered Clipping and `ARC+mean`), task-adapted FLTrust-like and FLShield-like baselines, and official FoolsGold in the adaptive suite. On public `scenario_h + update_noise@0.4`, conditional-floor hardening reaches `F1 = 0.9763`, `FPR = 0.0221`, and `0.0` retained poisoned clients; by contrast, `ARC+mean` and Centered Clipping reach competitive predictive metrics (`F1 = 0.9780` and `0.9777`) while still retaining all `4.0` poisoned clients. On `scenario_e + adaptive_alie_like@0.4`, `temporal_rootguard_v2` reaches `F1 = 0.9891`, `FPR = 0.0139`, `0.4` retained poisoned clients, and `3.3` kept clients, whereas official FoolsGold achieves stricter poisoning suppression only through much harsher abstention. The results support a deployment-oriented conclusion: HiTrust-FedBot is best interpreted as an interpretable engineering control that yields practical operating points on the poisoning-retention versus abstention frontier, not as a universal Byzantine defense.

**Keywords:** federated learning, bot detection, GraphSAGE, adversarial robustness, trust-aware aggregation, edge security

## 1. Introduction

### 1.1 Background and Motivation

Web bot detection at the network edge is a concrete engineering AI problem: operators want a shared detector across multiple sites, but raw traffic records and graph-derived behavior traces are often too sensitive or too expensive to centralize. Federated learning is therefore attractive, yet a deployable system must satisfy more than average predictive accuracy. It must operate under communication limits, non-IID client structure, and the possibility that some participating sites or updates are malicious.

In topology-aware bot detection, these constraints are sharper than in flat iid classification. Relational structure is part of the signal, not something that can be averaged away without consequence. Different sites naturally emphasize different traffic roles, overlap patterns, and attack concentrations. As a result, a server that simply suppresses unusual updates may remove poisoned clients, but it may also remove the only remaining representatives of a semantically important subgroup.

This makes the server-side objective an engineering trade-off problem rather than a pure leaderboard problem. In practice, the system should reduce poisoned participation without silently collapsing minority but valid semantic groups, and it should do so without falling into unrealistic abstention regimes where almost no clients remain active. For an EAAI-facing paper, this distinction matters: the relevant contribution is not merely another robust federated rule, but a deployable AI system design that exposes and manages the operating trade-off explicitly.

This paper addresses that gap with HiTrust-FedBot, a trust-aware hierarchical federated bot detection framework built around grouped aggregation and group-coverage-constrained trust filtering. The framework is instantiated with a GraphSAGE backbone and evaluated not only on internal topology-aware pilot scenarios, but also on same-task public Ca-Bench validation with matched multi-seed statistics, plus auxiliary cross-domain NSL-KDD transfer. The resulting evidence supports a deliberately conservative narrative. The strongest claim is not universal F1 superiority over every baseline; it is that HiTrust-FedBot and its hardening variants occupy more useful operating points on the trade-off between retained poisoned participation and overly aggressive abstention. That interpretation remains intact even after adding stronger modern comparators such as Centered Clipping and `ARC+mean` to the non-adaptive public suite, and official FoolsGold to the adaptive suite.

### 1.2 Main Contributions

This paper makes four main contributions.

- It presents HiTrust-FedBot, a trust-aware hierarchical federated bot-detection framework that treats semantic group coverage as a first-class design constraint instead of relying on flat trust filtering alone.
- It evaluates the framework with a GraphSAGE backbone across internal topology-aware scenarios, same-task public Ca-Bench `scenario_e` and `scenario_h`, and auxiliary public NSL-KDD transfer, together with keep-all, classical robust aggregation, modern Centered Clipping and `ARC+mean` comparators, FLTrust-like, FLShield-like, and official FoolsGold baselines.
- It studies two practically important failure regimes: small-group collapse under non-adaptive poisoning and adaptive camouflage under defense-aware poisoning, and introduces targeted hardening variants for each regime instead of claiming a single universal defense.
- It supports the main public claims with matched 10-seed paired evaluation and frames the paper around an engineering objective that is better aligned with deployment: reducing retained poisoned participation while maintaining usable predictive quality and client retention.

## 2. Related Work

Federated learning has become an active direction in cyber-security detection because it allows multiple sites to learn a shared detector without exchanging raw data [3-5]. Existing studies have applied federated learning to intrusion detection, malicious traffic classification, and privacy-sensitive security monitoring, but they also report substantial non-IID effects across clients. Those effects are highly relevant in the present setting, where graph partitions derived from different traffic roles and topologies naturally induce heterogeneous client behavior.

A second line of work addresses poisoning and Byzantine robustness in federated learning [6-9]. Classical robust aggregators such as Krum, median, trimmed mean, and centered clipping [18] focus on suppressing malicious updates in flat client pools, while more recent pre-aggregation strategies such as ARC [19] explicitly target robustness under stronger heterogeneity. Trust-bootstrapping methods such as FLTrust emphasize alignment to a trusted server root [8], while sybil-oriented methods such as FoolsGold focus on the similarity structure of client histories [17]. These methods are directly relevant because our threat model includes poisoned clients and coordinated camouflage. However, most of them are still not designed for settings in which semantic group coverage is itself a deployment requirement. In topology-aware bot detection, dropping or clipping updates aggressively may improve aggregation quality while still leaving the system with the wrong active client population for deployment.

Graph learning has also become increasingly important in security analytics because relational structure often carries information that feature-only models miss [10-13]. This is particularly true for bot and attack behavior that emerges from interaction patterns rather than isolated flow attributes. GraphSAGE is attractive in the present setting because it offers a practical balance between structural expressiveness and deployment tractability [13]. In addition, communication-efficient adaptation remains a central concern in federated systems [1,14-16], which motivates comparing multiple tuning regimes instead of assuming that robust behavior requires full-model updates.

Against this background, HiTrust-FedBot occupies a specific position. It is not simply another robust aggregator or another graph-based detector. Its main design distinction is that poisoning resistance and semantic coverage are coupled explicitly. This choice changes the aggregation rule, the interpretation of failure modes, and the meaning of aggressive abstention. It also leads to a paper structure in which the strongest claims come from carefully chosen public hardest settings rather than from broad average-case accuracy claims.

## 3. Problem Setting

### 3.1 Federated Bot Detection Scenario

We consider a server-coordinated federated learning system for web bot detection. Each client corresponds to an edge site that observes a local traffic-derived graph partition. The client trains a local detector and uploads model updates, while the server aggregates these updates into a global model. The graph partitions are not assumed to be iid. Instead, they may differ in traffic load, role composition, attack concentration, and relational structure.

Let the active clients be partitioned into semantic groups according to topology- or role-aware metadata derived from the graph-building pipeline. This grouping reflects the fact that different clients may represent distinct traffic roles or structural contexts. The server must combine these local contributions into a global model while handling two competing requirements. First, it should reduce the influence of malicious or low-quality updates. Second, it should avoid silently removing all clients from a semantically meaningful subgroup when that subgroup remains relevant to deployment.

The core performance metrics therefore extend beyond standard classification accuracy. In addition to test F1 and false positive rate, the experiments track retained poisoned clients and retained total clients after filtering. These quantities expose the defense behavior directly. A method that appears strong on F1 but keeps many poisoned clients is operationally different from a method that achieves similar F1 while sharply reducing poisoned participation. Likewise, a method that removes nearly all clients may achieve strong poisoning suppression, but at the cost of an unrealistic operating point.

### 3.2 Threat Model and Research Objective

The threat model includes malicious clients that participate in training and poison the federated update stream. The main non-adaptive attacks are `sign_flip@0.4` and `update_noise@0.4`, both of which corrupt 40% of the active clients. The adaptive public analysis further includes two defense-aware attacks. `adaptive_benign_mimic` shifts poisoned updates toward the benign centroid to accumulate trust mass, while `adaptive_alie_like` keeps poisoned updates inside a benign coordinate-wise envelope while preserving coordinated directionality.

These attacks expose two different failure regimes. In the first regime, a static group floor can preserve a fully compromised small group. In the second regime, trust-based heuristics can be fooled by malicious updates that are intentionally made benign-looking. The research objective is therefore not simply to maximize F1 under all settings. The objective is to find practical aggregation and hardening rules that reduce poisoned participation while maintaining enough semantic coverage and enough predictive quality for real deployment.

This objective leads to the central research question of the paper: can a grouped trust-aware federated bot detector provide more balanced operating points than either keep-all aggregation or more aggressive adaptive defenses that reduce poisoning primarily by severe abstention? The proposed framework, the experimental design, and the interpretation of results are all organized around this question.

## 4. Proposed Method

### 4.1 Overall Framework

HiTrust-FedBot follows a server-coordinated federated workflow. A global model is initialized and warm-started on the server side. In each communication round, active clients train locally on their graph partitions and return model updates. The server then evaluates client behavior, derives trust-aware retention decisions, aggregates the retained updates within semantic groups, and finally combines the group-level aggregates into a global update.

The key design choice is that the server does not aggregate all retained updates in one flat pool. Instead, it first preserves group structure, then applies trust-aware filtering with explicit group-level logic, and only then performs hierarchical aggregation. This structure is intended to reduce two common failures of flat robust aggregation: the domination of large groups over small but useful groups, and the complete collapse of a minority semantic group after aggressive filtering.

The framework is instantiated in this paper with a GraphSAGE backbone. GraphSAGE is chosen because the target task is graph-based bot detection and the experiments show a clear benefit over a feature-only baseline in the harder topology-aware settings. The same framework, however, is not conceptually tied to GraphSAGE alone. The design is more general: grouped trust-aware aggregation plus interpretable hardening rules for specific failure regimes.

### 4.2 Trust-Aware Hierarchical Aggregation

For each round, the server derives trust-related signals from local validation behavior and update characteristics. These signals are normalized and used to decide which clients remain active in the aggregation step. The retained client updates are then grouped according to their assigned semantic group. Aggregation first occurs within each group, and the group-level updates are then combined into the final global update.

This hierarchical structure matters because the deployment setting is inherently structured. If aggregation is fully flat, dominant client populations can drown out minority but useful groups. A grouped hierarchy reduces that effect and makes the coverage decision explicit. It also provides a natural place to apply group-preservation logic after trust filtering.

The server further enforces a minimum retained-client floor per group in the repaired mainline. This floor prevents a group from disappearing silently when all of its members receive low trust in a single round. However, this repair introduces a trade-off. A static floor can preserve semantic coverage, but it can also force the system to keep a poisoned client when an entire small group is compromised. That observation motivates the first targeted hardening.

### 4.3 Hardening Strategies for Challenging Attack Regimes

The first hardening strategy is `condfloor`, designed for the non-adaptive small-group collapse mechanism. Instead of always enforcing the group floor, `condfloor` skips the repair step when a group’s total normalized trust mass falls below a small threshold. In effect, the system is allowed to abstain from representing a group that appears collectively untrustworthy. This is a narrow repair, not a universal new default, but it directly addresses the failure mode observed in the hardest non-adaptive public setting.

The second hardening strategy targets adaptive camouflage. In the `adaptive_benign_mimic` regime, poisoned updates are intentionally aligned with benign behavior, so a static threshold or static conditional floor is not enough. `temporal_rootguard` therefore combines multi-round trust smoothing, root-anchor blending against a deterministic trusted server update, a drift penalty relative to that anchor, and a peer-redundancy penalty that suppresses clusters of nearly identical suspicious updates. The variant also allows abstention by setting the group floor to zero in suspicious groups. `temporal_rootguard_v2` extends this operating mode with stronger layerwise and behavioral probes, but the experiments show that its main value lies in certain adaptive geometries rather than as a universal replacement.

To make the interpretation more rigorous, the adaptive public suite also includes three comparators beyond keep-all aggregation: task-adapted FLTrust-like, task-adapted FLShield-like, and official FoolsGold. These baselines are not included merely for leaderboard comparison. They are used to expose where the proposed hardening sits on the poisoning-retention versus abstention frontier. In particular, FoolsGold serves as an official-code anchor for a more aggressive sybil-style defense that can drive retained poisoned clients to zero in multiple adaptive settings while often collapsing to near-single-client participation.

## 5. Experimental Results

### 5.1 Experimental Setup

The experiments are conducted on five internal topology-aware pilot scenarios and two same-task public Ca-Bench scenarios. The internal scenarios are `scenario_d_three_tier_low2`, `scenario_e_three_tier_high2`, `scenario_f_two_tier_high2`, `scenario_g_mimic_congest`, and `scenario_h_mimic_heavy_overlap`. The public validation focuses on `scenario_e_three_tier_high2` and `scenario_h_mimic_heavy_overlap`, which offer a stronger task match than a cross-domain benchmark. To broaden the external evidence further, the paper also includes an auxiliary public NSL-KDD path converted into a feature-similarity graph.

The backbone comparison uses FeatureMLP and GraphSAGE. For GraphSAGE, three tuning modes are considered: `head_only`, `adapter_ft`, and `full_ft`. The reported metrics include test F1, test recall, test FPR, retained poisoned clients, retained total clients, and estimated communication cost. For the key public comparisons, the evaluation uses multi-seed sweeps and reports paired bootstrap confidence intervals together with matched-seed sign-flip tests and matched-seed paired t-tests. This is important because the paper’s strongest claims concern retained poisoned participation and abstention rather than small changes in average F1 alone.

The main public hardest non-adaptive setting is `scenario_h + update_noise@0.4`. The main adaptive public reference is `scenario_h + adaptive_benign_mimic@0.4`, and the adaptive evidence is broadened with `scenario_e + adaptive_benign_mimic@0.4`, `scenario_h + adaptive_alie_like@0.4`, and `scenario_e + adaptive_alie_like@0.4`. These choices are intended to separate distinct failure modes rather than to maximize the number of benchmark points.

### 5.2 Main Results on Internal and Public Benchmarks

The internal pilot results show that the GraphSAGE mainline remains strong across the harder topology-aware scenarios. In the single-run matrix, test F1 ranges from `0.9692` to `0.9966` in the clean setting, from `0.9696` to `0.9966` under sign-flip, and from `0.9705` to `0.9966` under update-noise. On `scenario_h`, the five-seed means remain strong at `0.9785` in the clean setting, `0.9797` under sign-flip, and `0.9686` under update-noise. These results indicate that the repaired trust semantics preserve the mainline in the internal topology-aware suite rather than only in a narrow favorable subset.

The backbone comparison further supports the choice of GraphSAGE. On the structurally harder `scenario_h`, FeatureMLP reaches mean F1 values of `0.9417` in the clean setting and `0.9512` under sign-flip, whereas GraphSAGE reaches `0.9785` and `0.9797`, respectively. These gains are statistically significant and are accompanied by substantial false-positive-rate reductions. The communication study also shows that strong performance does not require the most expensive update regime. Under `scenario_h + sign_flip@0.4`, `adapter_ft` reaches `F1 = 0.9696` while using only `19.45%` of the communication cost of `full_ft`, and `head_only` retains comparable F1 at an even lower communication budget.

The same-task public evidence clarifies the main contribution. On public `scenario_e + update_noise@0.4`, the trust-aware mainline reaches `F1 = 0.9882`, `FPR = 0.0179`, and `0.1` retained poisoned clients. The two strongest modern non-abstaining comparators in the same table, Centered Clipping and `ARC+mean`, reach `F1 = 0.9881` / `0.9875` and `FPR = 0.0228` / `0.0198`, but both still retain all `4.0` poisoned clients. Public `scenario_h + update_noise@0.4` is more revealing because it exposes the small-group floor failure directly. In the current 10-seed comparison, `condfloor` reaches `F1 = 0.9763`, `FPR = 0.0221`, and `0.0` retained poisoned clients, whereas keep-all reaches `F1 = 0.9746`, `FPR = 0.0274`, and retains all `4.0` poisoned clients. The modern `ARC+mean` and centered-clipping comparators reach `F1 = 0.9780` / `0.9777` and `FPR = 0.0215` / `0.0218`, slightly improving predictive metrics over the static trust-aware line, but both still retain all `4.0` poisoned clients because they are aggregation-only controls without explicit participation filtering. Relative to the FLTrust-like baseline, `condfloor` also reduces mean retained poisoned clients from `1.9` to `0.0`, with a paired sign-flip `p = 0.00391`, while the F1 difference remains non-significant. This is the strongest non-adaptive public evidence in the current repository because it isolates a concrete failure mechanism and shows that a lightweight targeted repair changes the security outcome materially.

The adaptive public results require a more careful interpretation. On `scenario_h + adaptive_benign_mimic@0.4`, the static line, `condfloor`, and keep-all all retain `4.0` poisoned clients on average. `temporal_rootguard` reduces this to `0.0`, improves FPR to `0.0159`, and keeps `F1 = 0.9760`, but only `2.6` clients remain on average. `FLTrust-like` and `FLShield-like` retain `1.6` and `2.4` poisoned clients, respectively, while official FoolsGold also reaches `0.0` retained poisoned clients but collapses to `1.4` kept clients with `F1 = 0.9736`. This result is important because it shows that zero retained-poison is not unique to the proposed hardening. It can also be achieved by a far more aggressive abstention profile.

The external same-task transfer on `scenario_e + adaptive_benign_mimic@0.4` provides a clearer balance story. `temporal_rootguard` reaches `F1 = 0.9888`, `FPR = 0.0182`, `2.8` retained poisoned clients, and `6.4` kept clients. The stronger `temporal_rootguard_v2` operating point reaches `F1 = 0.9892`, `FPR = 0.0157`, `2.0` retained poisoned clients, and `4.7` kept clients. By contrast, FoolsGold again reaches `0.0` retained poisoned clients, but it drops to `F1 = 0.9789` and only `1.4` kept clients. For the second adaptive family, the same pattern persists. On `scenario_h + adaptive_alie_like@0.4`, `temporal_rootguard_v2` reaches `F1 = 0.9763`, `FPR = 0.0190`, `0.8` retained poisoned clients, and `3.5` kept clients, whereas FoolsGold reaches `F1 = 0.9752`, `FPR = 0.0156`, `0.0` retained poisoned clients, and only `1.3` kept clients. On `scenario_e + adaptive_alie_like@0.4`, `temporal_rootguard_v2` reaches `F1 = 0.9891`, `FPR = 0.0139`, `0.4` retained poisoned clients, and `3.3` kept clients, while FoolsGold again drives retained poisoned clients to `0.0` at the cost of `F1 = 0.9795` and `1.6` kept clients.

Taken together, the public suite supports a conservative but meaningful conclusion. The framework is strongest when interpreted as a set of operating points. `condfloor` is the most compelling repair for the non-adaptive small-group collapse mechanism. `temporal_rootguard` and `temporal_rootguard_v2` offer more balanced adaptive operating points than the more aggressive official FoolsGold anchor, especially on the external `scenario_e` transfers. The evidence does not support a universal “best method” claim across all adaptive metrics.

### 5.3 Ablation, Sensitivity, and Baseline Comparison

The baseline analysis changes what can be claimed honestly. FLTrust-like is not weak in the current graph-federated setting. On public `scenario_h + update_noise@0.4`, the tuned `root192_e1` point reaches approximately `F1 = 0.9802`, `FPR = 0.0104`, and `1.0` retained poisoned clients. The modern non-adaptive comparators sharpen the same lesson in a different way: on the matched 10-seed `scenario_h + update_noise@0.4` comparison, `ARC+mean` reaches `F1 = 0.9780` and `FPR = 0.0215`, and Centered Clipping reaches `F1 = 0.9777` and `FPR = 0.0218`, yet both still retain all `4.0` poisoned clients. This means the proposed method should not be framed as universally better on standard accuracy metrics. Its stronger value lies in reducing retained poisoned participation under the topology-aware public hardest setting without requiring an F1-dominance story.

The ablation and sensitivity results reinforce the mechanism interpretation. The small-group collapse case on `scenario_h + update_noise@0.4` shows that the critical issue is not general model instability but the interaction between a static group floor and a fully compromised small group. The conditional-floor repair addresses exactly this issue. On the adaptive side, the `temporal_rootguard_v2` ablation indicates that the strongest visible benefit comes from the peer-redundancy and cluster-level rejection logic, while some of the other refinements contribute less visibly in the current public adaptive line. This is useful because it keeps the paper from over-claiming a large number of equally critical components.

The auxiliary NSL-KDD validation provides additional context. In the current 10-seed update-noise comparison, the trust-aware line reaches `F1 = 0.7952` with `0.7` retained poisoned clients, the `ARC+mean` comparator reaches `F1 = 0.7585`, the centered-clipping comparator reaches `F1 = 0.7642`, and both modern clipping-based baselines still retain all `4.0` poisoned clients. The FLTrust-like baseline reaches `F1 = 0.7557` with `1.7` retained poisoned clients. Although NSL-KDD is not a same-task benchmark, this contrast supports the broader claim that the grouped trust-aware line can remain competitive outside the exact Ca-Bench setting while preserving the main security interpretation.

## 6. Discussion

### 6.1 Security-Coverage Trade-off

The central lesson of the current evidence is that the main security claim does not live on average F1 alone. It lives on the relationship among test quality, retained poisoned participation, and retained total clients. This is why the public comparison scripts report paired statistics not only for F1 and FPR but also for retained poisoned clients and retained total clients. Without those quantities, a method that removes nearly every client and a method that preserves broader semantic coverage can appear superficially similar.

Centered Clipping and `ARC+mean` make this distinction concrete in the non-adaptive public suite. On `scenario_h + update_noise@0.4`, they reach better mean F1/FPR than the static trust-aware line (`0.9777` / `0.0218` and `0.9780` / `0.0215` versus `0.9723` / `0.0330`), but they still keep all `4.0` poisoned clients because they do not attempt explicit participation control. This is precisely why the paper's main engineering claim must remain tied to retained-poisoned-participation control rather than to accuracy alone.

This perspective also explains why the official FoolsGold baseline is valuable even though it does not strengthen the headline claim in a simple “ours is better” sense. FoolsGold shows that zero retained poisoned clients are achievable in multiple adaptive public settings. However, it typically achieves this by collapsing to about `1.3-1.6` kept clients. This exposes a much harsher abstention operating point. The proposed adaptive hardening variants, especially `temporal_rootguard_v2` in the external `scenario_e` transfers, occupy a more balanced point on that frontier. They do not always achieve the strictest poisoning suppression, but they do so while retaining substantially more clients and substantially better F1 in the external adaptive settings.

For an EAAI paper, this interpretation is a strength rather than a weakness. The paper is not trying to claim a new universal theory of Byzantine robustness. It is presenting an interpretable engineering framework for topology-aware federated bot detection and demonstrating, with same-task public evidence, where different controls are useful. Under that standard, the current evidence is strongest when the claims remain tied to the observed frontier rather than inflated into universal superiority statements.

### 6.2 Limitations and Practical Implications

The study still has several limitations. First, the main topology-aware pilot scenarios are derived internal graphs rather than a fully open end-to-end raw-data benchmark pipeline. Second, although the public evidence is much stronger than before, it still concentrates on two same-task public Ca-Bench scenarios and one auxiliary NSL-KDD path. Third, while the public suite now includes modern Centered Clipping and `ARC+mean` comparators together with an official FoolsGold comparator, the FLTrust-like and FLShield-like baselines remain task-adapted implementations in the current graph-federated environment rather than exact reproductions of their original release settings.

The adaptive story also remains incomplete. `temporal_rootguard` and `temporal_rootguard_v2` improve the balance between poisoning suppression and client retention, but they do not solve adaptive camouflage universally. In some settings, especially on `scenario_e`, the official FoolsGold comparator remains stricter on retained poisoned clients, albeit at a much more aggressive abstention point. This means the right conceptual picture is still a frontier of trade-offs rather than a settled winner.

From a deployment perspective, however, the results are already useful. The communication study suggests that strong robustness does not require the heaviest update regime. The grouped hierarchy provides an interpretable handle on semantic coverage. The hardening variants are linked to specific failure regimes rather than opaque heuristic stacking. These properties make the framework more attractive for real engineering use than a paper narrative based only on incremental average F1 gains.

## 7. Conclusion

HiTrust-FedBot should be read as an engineering AI system for federated bot detection rather than as a universal robust-federated-learning theorem. Across internal topology-aware pilots and matched 10-seed same-task public validation, the framework preserves strong predictive quality while making poisoned participation an explicit controllable quantity. The clearest non-adaptive result is the `condfloor` repair on public `scenario_h + update_noise@0.4`, which reduces retained poisoned clients to `0.0`. The stronger modern non-adaptive comparators, Centered Clipping and `ARC+mean`, show why this matters: they reach competitive or even better predictive metrics in some settings, yet still retain all poisoned clients because they improve aggregation without changing who remains active.

The adaptive suite reinforces the same engineering interpretation. `temporal_rootguard` and `temporal_rootguard_v2` do not dominate every baseline on every metric, but they occupy more practical operating points than official FoolsGold when retained poisoned participation, client retention, and predictive quality are considered together. For an EAAI submission, that is the right conclusion: the contribution is an interpretable and reproducible deployment-oriented framework, plus an evaluation protocol that makes the trade-off between predictive performance, poisoned participation, and abstention explicit. The most valuable next steps are to widen the same-task public evaluation surface, add one more modern heterogeneity-aware comparator such as CAF, and measure server-side runtime and latency overhead alongside the existing communication-cost analysis.

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

[17] Clement Fung, Chris J. M. Yoon, and Ivan Beschastnikh. The Limitations of Federated Learning in Sybil Settings. In *Proceedings of the 23rd International Symposium on Research in Attacks, Intrusions and Defenses (RAID)*, pages 301-316, 2020.

[18] Sai Praneeth Karimireddy, Lie He, and Martin Jaggi. Learning from History for Byzantine Robust Optimization. In *Proceedings of the 38th International Conference on Machine Learning (ICML)*, PMLR 139, pages 5311-5319, 2021.

[19] Youssef Allouah, Rachid Guerraoui, Nirupam Gupta, Ahmed Jellouli, Geovani Rizk, and John Stephan. Adaptive Gradient Clipping for Robust Federated Learning. In *International Conference on Learning Representations (ICLR)*, 2025.
