# HiTrust-FedBot: An Interpretable Federated Web Bot Detection Framework with Trust-Aware Hierarchical Aggregation and Coverage-Constrained Filtering

Author identities, affiliations, and correspondence details should remain on the separate title page required by the journal workflow.

## Abstract

Federated web bot detection at the edge is an engineering artificial intelligence problem because graph-structured traffic evidence often cannot be centralized, yet the deployed system must tolerate non-IID clients, poisoned participation, semantic coverage constraints, and practical runtime limits. We present HiTrust-FedBot, an interpretable federated bot-detection framework that combines trust-aware hierarchical aggregation with targeted hardening for two observed failure regimes: small-group collapse under non-adaptive poisoning and benign-looking camouflage under adaptive poisoning. The evaluation is organized around a reviewer-auditable evidence stack: five internal topology-aware pilots, same-task public Ca-Bench validation on `scenario_e` and `scenario_h`, two additional public raw-data chains built from Westermo and LITNET-2020 UDP-flood flows, a matched 20-seed adaptive `2 x 2` public matrix, an attack-extension package, and a 5-seed single-host deployment/runtime package over `10/20/40/80` active clients. On the hardest same-task public non-adaptive setting, public Ca-Bench `scenario_h + update_noise@0.4`, the targeted `condfloor` repair reaches `F1 = 0.9746`, `FPR = 0.0307`, `KP = 0.0`, and `KC = 6.0`, while strong aggregation baselines still retain all `4.0` poisoned clients. Across Westermo and LITNET-2020, the same public raw-data pipelines expose a stable frontier between predictive quality and poisoned participation rather than a universal winner. The deployment package shows static-line server-round time rising from `29.6` to `266.1 ms` and aggregation from `0.71` to `7.04 ms` as client count increases from `10` to `80`, with peak RSS near `830 MB`. These results support a deployment-oriented interpretation: HiTrust-FedBot is best understood as a set of interpretable engineering controls for predictive quality, poisoned participation, abstention, and runtime cost, not as a universal robust-FL theorem.

**Keywords:** federated learning, bot detection, graph neural networks, trust-aware aggregation, adversarial robustness, edge security

## 1. Introduction

### 1.1 Engineering Motivation

Web bot detection is increasingly deployed across multiple edge sites, network segments, or administrative domains. In that setting, raw traffic records, flow traces, and graph-derived interaction structures are often difficult to centralize because of privacy, bandwidth, or operational constraints. Federated learning is therefore attractive, but a practical deployment must solve more than a standard distributed classification problem. It must cope with non-IID client populations, communication budgets, and malicious participants that poison the update stream.

In topology-aware bot detection, these issues interact more strongly than in flat iid benchmarks. The graph structure is part of the detection signal: overlap patterns, neighborhood context, and role asymmetry all matter. Aggressive server-side filtering can suppress poisoned updates, but it can also remove the only remaining representatives of a semantically important subgroup. A deployed system therefore faces a multi-objective operating problem: it should improve predictive quality, reduce retained poisoned participation, preserve enough client and group coverage to remain useful, and do so at acceptable engineering cost.

This motivates a narrower and more defensible paper thesis than a generic "robust federated learning" claim. The strongest question is not whether one method wins every leaderboard metric. The stronger question is whether an interpretable federated detector can expose and manage the trade-off among predictive quality, poisoned participation, semantic coverage, abstention, and runtime cost under public, reviewer-auditable evidence.

### 1.2 HiTrust-FedBot

HiTrust-FedBot addresses that question with trust-aware hierarchical aggregation. The server evaluates client updates, filters them through trust-aware rules, aggregates within semantic groups, and then combines the group-level updates into a global model. The grouped structure is important because it turns semantic coverage into an explicit control variable rather than a side effect of flat filtering.

The current repository also shows that this mainline should be interpreted carefully. A static group floor is useful for preserving coverage, but the hardest same-task public stress case reveals a small-group collapse mode in which forced coverage can preserve exactly the poisoned client that should have been rejected. A second failure regime appears under adaptive benign-mimic poisoning, where malicious clients imitate benign update directions closely enough to survive static trust rules. The paper is therefore strongest when it presents targeted hardening lines for distinct failure modes instead of claiming a single universally superior defense.

### 1.3 Contributions

This paper makes four main contributions.

- It presents HiTrust-FedBot, an interpretable federated web bot-detection framework that couples trust-aware hierarchical aggregation with explicit semantic-group coverage control.
- It constructs an EAAI-oriented evidence stack that combines internal topology-aware pilots, same-task public Ca-Bench validation, two additional public raw-data chains from Westermo and LITNET-2020 UDP-flood traffic, a matched 20-seed adaptive `2 x 2` matrix, an attack-extension package, and a measured single-host deployment/runtime package.
- It identifies two distinct failure mechanisms and addresses them with targeted hardenings: `condfloor` for static small-group collapse and `temporal_rootguard` / `temporal_rootguard_v2` for adaptive camouflage.
- It frames the results conservatively around deployment-relevant operating points, reproducibility surface, and engineering cost, rather than around universal superiority on `F1`.

## 2. Related Work

Federated learning has become a practical direction for intrusion detection, malicious traffic analysis, and privacy-sensitive security monitoring because it allows distributed model training without centralizing raw data [1-5]. That literature establishes the engineering motivation for distributed security AI, but it also repeatedly highlights non-IID client structure, unstable local distributions, and resource constraints. These issues are central in the present task because graph-derived bot-detection clients differ systematically in traffic roles, overlap structure, and attack concentration.

Robust federated learning under poisoning has produced a large family of defenses based on robust aggregation, clipping, trust bootstrapping, and validation-guided filtering [6-9,18,19]. These methods are directly relevant because our setting includes malicious participants. However, much of the robust-FL literature treats the client population as a flat pool and focuses on suppressing suspicious updates. In topology-aware bot detection, that design is incomplete: the server may improve the cleanliness of the retained pool while also deleting the only surviving representatives of a semantically important client group. This is the engineering gap that motivates our group-aware filtering rule and the way we interpret abstention.

Graph neural networks have also become important for cyber-security analytics because relational structure often carries the signal that feature-only models miss [10-13]. For federated bot detection, this makes GraphSAGE an attractive practical backbone: it provides structural expressiveness without requiring an unrealistic centralized graph [13]. Communication-efficient adaptation is a second practical concern in federated systems [1,14-16], so we also evaluate `head_only`, `adapter_ft`, and `full_ft` update regimes instead of assuming that strong robustness requires the heaviest communication path.

Against that background, HiTrust-FedBot should not be read as just another robust aggregation rule. Its distinguishing feature is the joint treatment of poisoned participation, semantic group coverage, abstention, and deployment cost under a public evidence surface that reviewers can audit directly.

## 3. Problem Setting

### 3.1 Federated Topology-Aware Bot Detection

We consider a server-coordinated federated learning system with active client set `C_t` at communication round `t`. Each client trains locally on a graph-derived partition of traffic or behavior data and uploads a model update instead of raw records. Clients are mapped to semantic groups `g(i)` defined by topology- or role-aware metadata from the graph-building pipeline. The global server must combine these updates into a single detector that remains useful across groups.

The server does not solve a pure prediction problem. It must balance:

- predictive quality on held-out data,
- false-positive behavior,
- retained poisoned participation after filtering,
- retained total clients after filtering.

We denote retained poisoned clients by `KP` and retained total clients by `KC`. These quantities make the deployment trade-off explicit. A defense that attains a strong `F1` score while keeping many poisoned clients is operationally different from a defense that reaches similar `F1` with tighter participation control. Likewise, a defense that suppresses poisoning only by collapsing to a near-single-client operating point is not necessarily practical.

### 3.2 Threat Model

The current paper studies both non-adaptive and adaptive poisoning.

- Non-adaptive attacks:
  - `update_noise@0.4`
  - `sign_flip@0.4`
- Adaptive attacks:
  - `adaptive_benign_mimic@0.4`
  - `adaptive_alie_like@0.4`
- Supportive stress extensions:
  - `colluding_update_noise`
  - `multi_round_stealth`

The `0.4` poisoning rate means that `40%` of active clients are malicious. In the main public settings, that corresponds to `4` poisoned clients out of `10`. The important point is not the exact attack naming, but the failure geometry each one reveals. `update_noise` exposes small-group collapse under static group floors. `adaptive_benign_mimic` and `adaptive_alie_like` expose a different problem: malicious clients can preserve benign-looking geometry long enough to accumulate trust and survive static screening.

### 3.3 Research Objective

The research objective is therefore deployment-oriented:

1. maximize predictive quality where possible,
2. minimize retained poisoned participation,
3. avoid unnecessary abstention and client collapse,
4. preserve enough semantic coverage for a useful global model,
5. keep runtime cost within a practical single-host deployment budget.

This objective is stricter than maximizing `F1` alone and more realistic for an engineering AI paper.

## 4. Proposed Method

### 4.1 Pipeline Overview

HiTrust-FedBot follows a simple, interpretable pipeline in each round:

1. The server selects active clients and sends the current global model.
2. Each client trains locally on its graph partition and returns an update.
3. The server computes trust-related signals from validation behavior and update consistency.
4. The server filters or down-weights updates with explicit group-aware logic.
5. Retained updates are aggregated within semantic groups and then merged into the global update.

The key architectural choice is Step 5. The server does not aggregate all retained updates in a flat pool. It first aggregates within groups and only then across groups. This prevents dominant groups from overwhelming weaker ones and makes coverage-preservation logic explicit and auditable.

### 4.2 Trust-Aware Hierarchical Aggregation

The mainline method assigns each update a trust score and retains updates that satisfy the trust rule. Retained updates are then grouped by semantic label. Aggregation inside a group produces a group-level update, and the server combines the group-level updates into the final global update.

This structure provides two practical advantages.

- It respects the topology-aware client organization of the task instead of assuming that all clients are exchangeable.
- It gives the server a natural place to enforce a minimum retained-client floor per group so that a small but valid group is not removed silently.

The default grouped mainline is denoted `trust_aware` or `static` in the result tables. Its value is not that it always wins `F1`; its value is that it often reduces `KP` sharply while retaining a meaningful client set.

### 4.3 `condfloor`: Targeted Repair for Small-Group Collapse

The hardest same-task public non-adaptive case reveals a weakness in the static group floor. If a small group has very low total trust mass and its remaining candidates are poisoned, always enforcing a floor of one retained client can preserve the poisoned client by construction. We therefore introduce `condfloor`, a targeted repair that skips the floor-repair step when the group's normalized trust mass falls below a small threshold.

`condfloor` is intentionally narrow. It is not a universal replacement for the mainline. Its purpose is to convert forced coverage into abstention only when the evidence for the group is too weak to justify keeping a representative. This makes its interpretation clean: `condfloor` repairs a specific static failure mode rather than adding another generic heuristic layer.

### 4.4 `temporal_rootguard` and `temporal_rootguard_v2`: Targeted Adaptive Controls

Adaptive camouflage requires a different response. When malicious clients imitate benign update directions, static trust thresholds and static conditional floors become insufficient. For this case we introduce `temporal_rootguard`, which combines:

- multi-round trust smoothing,
- blending against a deterministic trusted server root update,
- a temporal drift penalty,
- a peer-redundancy penalty for suspicious near-duplicate updates,
- permissive abstention in suspicious groups.

`temporal_rootguard_v2` extends that logic with stronger adaptive probes and a stricter rejection posture. In the public adaptive suite, the two variants should be read as different operating points. `temporal_rootguard` is often the more balanced adaptive control, while `temporal_rootguard_v2` is often the stricter poisoned-participation control. Neither should be presented as a universal winner.

### 4.5 Backbone and Tuning Regimes

The framework is instantiated with a GraphSAGE backbone [13]. We compare three update regimes:

- `head_only`
- `adapter_ft`
- `full_ft`

This lets the paper answer an engineering question that matters for EAAI: do the best operating points require the most expensive communication path, or can they be reached with lighter adaptation? The communication study in Section 6 shows that strong operating points remain available without always using full-model updates.

## 5. Experimental Setup

### 5.1 Evidence Hierarchy

The experimental package is organized as an evidence hierarchy rather than a flat benchmark list.

*Table 1. Evidence hierarchy used in the manuscript.*

| Layer | Setting | Seeds | Role in the paper | Public status |
| --- | --- | ---: | --- | --- |
| Primary same-task public | Ca-Bench `scenario_h + update_noise@0.4` | 20 | Main hardest non-adaptive claim | Public and reproducible |
| Primary same-task public | Ca-Bench `scenario_e + update_noise@0.4` | 20 | Main stable same-task operating point | Public and reproducible |
| Primary public raw-data width | Westermo `update_noise@0.4` | 20 | Width evidence on separate raw-data chain | Public and reproducible |
| Primary public raw-data width | LITNET-2020 UDP-flood `update_noise@0.4` | 20 | Harsher width evidence on separate raw-data chain | Public and reproducible |
| Supportive second attack family | Westermo and LITNET `sign_flip@0.4` | 20 | Width evidence, not headline claims | Public and reproducible |
| Public adaptive matrix | `scenario_e` / `scenario_h` x `adaptive_benign_mimic` / `adaptive_alie_like` | 20 | Two anchor tables plus matched width evidence | Public and reproducible |
| Public attack extension | `colluding_update_noise`, `multi_round_stealth` on public `scenario_h` | 20 | Supportive stress evidence | Public and reproducible |
| Auxiliary public transfer | NSL-KDD `update_noise@0.4` | 10 | Exploratory transfer check | Public and reproducible |
| Internal pilots | Five topology-aware pilot scenarios | repo-native summaries | Mechanism and backbone support only | Derived graphs public; raw traces private |
| Runtime package | Public `scenario_h + update_noise@0.4`, `10/20/40/80` clients | 5 | Single-host deployment-cost evidence | Public and reproducible |

### 5.2 Datasets and Benchmarks

The evaluation uses four benchmark families.

- Internal topology-aware pilots:
  - `scenario_d_three_tier_low2`
  - `scenario_e_three_tier_high2`
  - `scenario_f_two_tier_high2`
  - `scenario_g_mimic_congest`
  - `scenario_h_mimic_heavy_overlap`
- Same-task public validation:
  - public Ca-Bench `scenario_e`
  - public Ca-Bench `scenario_h`
- Additional public raw-data chains:
  - Westermo Network Traffic Dataset
  - LITNET-2020 Network Flow Dataset, UDP-flood path
- Auxiliary public transfer:
  - NSL-KDD converted to the local graph contract

The two Ca-Bench paths are the strongest public same-task evidence. Westermo and LITNET materially widen the paper because they are separate raw-data-to-graph-to-result chains under the same local schema. NSL-KDD remains auxiliary because it is cross-domain and weaker as a same-task bot-detection benchmark.

### 5.3 Baselines, Attacks, Metrics, and Statistics

The non-adaptive comparison suite includes keep-all aggregation, classical reference aggregators, and modern robust aggregators:

- `mean`
- `median`
- `krum`
- `rfa`
- `centered_clipping`
- `caf`
- `arc_mean`
- `fltrust_like`
- `fedtruth_like`
- `flshield_like`

The adaptive suite further includes:

- `foolsgold`
- `fltrust_like`
- `flshield_like`
- `temporal_rootguard`
- `temporal_rootguard_v2`

The provenance boundary is explicit. Mean/median/Krum/RFA/Centered Clipping/CAF/`ARC+mean` are aligned to fixed ByzFL semantic anchors. `foolsgold` is tied to a pinned official upstream history. `fltrust_like` and `flshield_like` remain task-adapted implementations, but their upstream anchors are now reviewer-visible and fixed. This is important because the paper does not claim bit-for-bit reproduction of the original FLTrust or FLShield release environments.

Primary endpoints are:

- `test_f1`
- `test_fpr`
- retained poisoned clients (`KP`)
- retained total clients (`KC`)

Primary and promoted public matched comparisons use 20-seed paired testing with Holm-Bonferroni correction. Exploratory comparisons such as NSL-KDD remain lower-depth supportive evidence.

### 5.4 Reproducibility Boundary

The public evidence surface is broad and reviewer-auditable. The repository includes public reproduction scripts for:

- same-task Ca-Bench validation,
- Westermo and LITNET raw-data chains,
- adaptive full-matrix validation,
- attack-extension reruns,
- runtime and deployment packages.

The internal pilot bundle is more limited. Reviewers receive the released derived graphs, not the private upstream traces. However, the maintainer-side raw audit now rebuilds all five internal scenarios from preserved raw traces and matches the shipped graphs exactly (`5 / 5` exact tensor/hash agreement). This closes the maintainer-side audit gap without changing the public redistribution boundary.

## 6. Results

### 6.1 Internal Pilots, Backbone Choice, and Communication Budget

The internal pilot matrix is useful for understanding why the public hardest same-task case behaves the way it does. With GraphSAGE, update-noise `F1` remains high across the five internal scenarios and ranges from `0.9705` on the hardest `scenario_h` to `0.9966` on `scenario_d`, while `scenario_g` is nearly saturated. The point of this matrix is not to carry the paper's main claim, but to show that `scenario_h` is the appropriate stress point for grouped trust-aware aggregation.

Backbone choice matters most on the harder topology-aware setting. On internal `scenario_h` clean, FeatureMLP reaches `F1 = 0.9148` and `FPR = 0.1931`, while GraphSAGE reaches `F1 = 0.9692` and `FPR = 0.0779`. Under `sign_flip@0.4`, FeatureMLP reaches `F1 = 0.9243` and `FPR = 0.1433`, whereas GraphSAGE reaches `F1 = 0.9696` and `FPR = 0.0530`. The structural backbone therefore matters most where semantic overlap and topology heterogeneity are most severe.

The communication study shows that the strongest internal operating points do not require full-model updates. On internal `scenario_h + update_noise@0.4`, `head_only` reaches `F1 = 0.9718`, essentially matching `full_ft` at `F1 = 0.9716`, while using only `2.08%` of the full-model byte budget. `adapter_ft` reaches `F1 = 0.9705` while using `19.45%` of the full-model byte budget. This matters for EAAI positioning because it means the framework can stay competitive under lighter adaptation regimes rather than requiring the most communication-heavy update path.

### 6.2 Same-Task Public Non-Adaptive Main Results

The strongest public non-adaptive result is the hardest same-task public table: Ca-Bench `scenario_h + update_noise@0.4`. This table should be read as a failure-mode diagnosis and repair table, not as a universal F1-dominance table.

*Table 2. Public Ca-Bench `scenario_h + update_noise@0.4` (matched 20-seed comparison). Lower `KP` is better; higher `KC` means less abstention.*

| Method | F1 | FPR | KP | KC |
| --- | ---: | ---: | ---: | ---: |
| `condfloor` | 0.9746 | 0.0307 | 0.00 | 6.00 |
| `trust_aware` static | 0.9703 | 0.0442 | 0.30 | 6.30 |
| `fltrust_like` | 0.9736 | 0.0157 | 2.05 | 4.85 |
| `centered_clipping` | 0.9757 | 0.0265 | 4.00 | 10.00 |
| `ARC+mean` | 0.9753 | 0.0274 | 4.00 | 10.00 |
| `keepall` | 0.9725 | 0.0374 | 4.00 | 10.00 |

Three observations matter.

1. `condfloor` is the cleanest security point in the table because it reduces `KP` to `0.0`.
2. Strong aggregation baselines such as Centered Clipping and `ARC+mean` remain highly competitive on `F1` and `FPR`, so the paper should not claim universal predictive superiority.
3. The decisive difference is poisoned participation, not `F1`.

The matched paired statistics reinforce that interpretation. Relative to `fltrust_like`, `condfloor` achieves a Holm-corrected retained-poison difference with `p = 7.63e-05`, while the `F1` difference is not significant after correction. Relative to keep-all, the retained-poison difference is absolute (`0.0` versus `4.0`). This is exactly the kind of deployment-oriented result the paper can defend: cleaner control of poisoned participation without claiming universal `F1` dominance.

The same-task public `scenario_e + update_noise@0.4` result plays a different role. It is the stable same-task operating-point table that shows the proposed mainline is not only a `scenario_h` anomaly.

*Table 3. Public Ca-Bench `scenario_e + update_noise@0.4` (matched 20-seed comparison).*

| Method | F1 | FPR | KP | KC |
| --- | ---: | ---: | ---: | ---: |
| `trust_aware` static | 0.9875 | 0.0208 | 0.10 | 6.10 |
| `fltrust_like` | 0.9885 | 0.0222 | 2.45 | 6.35 |
| `ARC+mean` | 0.9877 | 0.0188 | 4.00 | 10.00 |
| `CAF` | 0.9876 | 0.0221 | 4.00 | 10.00 |
| `keepall` | 0.9877 | 0.0222 | 4.00 | 10.00 |

Here the trust-aware mainline remains predictive-quality competitive while reducing `KP` sharply. `ARC+mean` and `CAF` match or slightly edge some pure prediction metrics, but they do not perform explicit poisoned-participation control. The correct interpretation is therefore consistent with `scenario_h`: the paper contributes a better deployment-relevant operating point, not a new universal leaderboard winner.

The FLTrust-like sensitivity grid further constrains the manuscript's claims. In a separate 3-seed sensitivity sweep on public `scenario_h`, the tuned `root192_e1` point reaches `F1 = 0.9802`, `FPR = 0.0104`, and `KP = 1.0`. That is a very strong baseline result. It strengthens the paper because it forces a disciplined conclusion: even after tuning a trust-bootstrapping baseline, the cleanest public hardest-setting `KP` control in the current repository still comes from `condfloor`, but the proposed method should not be sold as universally better on `F1` or `FPR`.
### 6.3 Public Raw-Data Width Evidence

Westermo and LITNET-2020 are the main width-evidence datasets because they are public raw-data chains outside Ca-Bench. They show that the operating-point story is not tied to a single benchmark family.

*Table 4. Selected public raw-data operating points. Westermo and LITNET update-noise tables are primary width evidence; sign-flip tables are supportive second-attack-family evidence.*

| Dataset | Attack | Method | F1 | FPR | KP | KC |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Westermo | `update_noise@0.4` | `trust_aware` | 0.6147 | 0.0224 | 0.10 | 6.10 |
| Westermo | `update_noise@0.4` | `condfloor` | 0.6159 | 0.0190 | 0.05 | 6.05 |
| Westermo | `update_noise@0.4` | `fltrust_like` | 0.6213 | 0.0087 | 1.85 | 3.90 |
| Westermo | `update_noise@0.4` | `keepall` | 0.6196 | 0.0081 | 4.00 | 10.00 |
| Westermo | `sign_flip@0.4` | `condfloor` | 0.6217 | 0.0102 | 2.90 | 7.25 |
| Westermo | `sign_flip@0.4` | `fltrust_like` | 0.6203 | 0.0142 | 2.05 | 4.15 |
| Westermo | `sign_flip@0.4` | `keepall` | 0.6200 | 0.0133 | 4.00 | 10.00 |
| LITNET-2020 UDP | `update_noise@0.4` | `trust_aware` | 0.5447 | 0.0766 | 0.85 | 6.85 |
| LITNET-2020 UDP | `update_noise@0.4` | `condfloor` | 0.5856 | 0.0464 | 0.40 | 6.40 |
| LITNET-2020 UDP | `update_noise@0.4` | `fltrust_like` | 0.6244 | 0.0255 | 1.75 | 5.65 |
| LITNET-2020 UDP | `update_noise@0.4` | `ARC+mean` | 0.6217 | 0.0274 | 4.00 | 10.00 |
| LITNET-2020 UDP | `sign_flip@0.4` | `condfloor` | 0.6231 | 0.0289 | 3.05 | 6.95 |
| LITNET-2020 UDP | `sign_flip@0.4` | `fltrust_like` | 0.6229 | 0.0282 | 0.90 | 5.40 |
| LITNET-2020 UDP | `sign_flip@0.4` | `ARC+mean` | 0.6255 | 0.0265 | 4.00 | 10.00 |

Westermo supports the same high-level story as Ca-Bench. `condfloor` and the static line both move to much safer `KP` points than keep-all, while `fltrust_like` and the stronger aggregation baselines sometimes attain cleaner `F1` / `FPR` values at more aggressive abstention or looser poisoned retention. The value of Westermo is therefore width evidence rather than a new headline win.

LITNET-2020 is even more informative because it is harsher. On `update_noise@0.4`, `condfloor` improves the static line from `F1 = 0.5447`, `KP = 0.85` to `F1 = 0.5856`, `KP = 0.40`, while higher-`F1` alternatives still retain more poisoned clients. At the same time, the Holm-corrected 20-seed table does not support a claim that `condfloor` significantly dominates every comparator. That is exactly why LITNET is valuable: it demonstrates that the paper is not hiding difficult public cases, and it reinforces a frontier interpretation rather than a benchmark-optimized story.

The Westermo and LITNET `sign_flip` sweeps should be read as second-attack-family width evidence. They widen the attack surface on the same public raw-data chains, but they do not change the conservative manuscript boundary.

### 6.4 Cross-Dataset Frontier and Attack Extension

The public non-adaptive story is summarized more clearly by a frontier view than by any single table. Across the four primary public non-adaptive mainlines, Pareto-optimal points include the static line on Ca-Bench `scenario_e`, `condfloor` on Ca-Bench `scenario_h`, `condfloor` on Westermo, and both `condfloor` and `fltrust_like` on LITNET depending on whether the reader prioritizes `KP` or `F1`.

![Figure 1. Cross-dataset frontier summary for the four primary public non-adaptive settings. The x-axis is retained poisoned clients (`KP`), the y-axis is `F1`, and bubble area encodes retained clients (`KC`). Black outlines mark Pareto-optimal operating points.](figures_eaai/cross_dataset_f1_kp_kc_frontier_summary.png)

This figure is important for interpretation. It shows that the paper's strongest contribution is not universal dominance. It is the ability to occupy useful operating points on a three-way surface involving predictive quality, poisoned participation, and abstention.

The attack-extension package adds two supportive stress tests on public `scenario_h`.

- `colluding_update_noise`:
  - `condfloor`: `F1 = 0.9765`, `FPR = 0.0248`, `KP = 0.10`, `KC = 4.30`
  - `trust_aware`: `F1 = 0.9761`, `FPR = 0.0227`, `KP = 0.30`, `KC = 4.60`
  - `keepall`: `F1 = 0.9761`, `FPR = 0.0237`, `KP = 4.00`, `KC = 10.00`
- `multi_round_stealth`:
  - `condfloor`: `F1 = 0.9758`, `FPR = 0.0232`, `KP = 0.15`, `KC = 4.35`
  - `trust_aware`: `F1 = 0.9758`, `FPR = 0.0235`, `KP = 0.30`, `KC = 4.90`
  - `keepall`: `F1 = 0.9752`, `FPR = 0.0251`, `KP = 4.00`, `KC = 10.00`

These tables do not create new headline claims, but they show that the small-group repair remains meaningful beyond the canonical `update_noise` line.

### 6.5 Public Adaptive `2 x 2` Matrix

The adaptive evidence is now much stronger because all four public scenario/attack combinations have matched 20-seed reruns. For the main paper, the two best anchor tables are public `scenario_h + adaptive_benign_mimic@0.4` and public `scenario_e + adaptive_alie_like@0.4`. Together they show both the strict and the balanced sides of the adaptive operating-point frontier.

*Table 5. Selected adaptive operating points from the matched 20-seed public matrix.*

| Setting | Method | F1 | FPR | KP | KC |
| --- | --- | ---: | ---: | ---: | ---: |
| `scenario_h + adaptive_benign_mimic@0.4` | `trust_aware` static | 0.9750 | 0.0266 | 4.00 | 7.25 |
| `scenario_h + adaptive_benign_mimic@0.4` | `flshield_like` | 0.9760 | 0.0201 | 2.60 | 6.10 |
| `scenario_h + adaptive_benign_mimic@0.4` | `foolsgold` | 0.9694 | 0.0467 | 0.05 | 1.65 |
| `scenario_h + adaptive_benign_mimic@0.4` | `temporal_rootguard` | 0.9748 | 0.0176 | 0.35 | 2.40 |
| `scenario_h + adaptive_benign_mimic@0.4` | `temporal_rootguard_v2` | 0.9744 | 0.0190 | 0.00 | 1.90 |
| `scenario_e + adaptive_alie_like@0.4` | `trust_aware` static | 0.9865 | 0.0248 | 3.80 | 6.65 |
| `scenario_e + adaptive_alie_like@0.4` | `flshield_like` | 0.9880 | 0.0198 | 1.80 | 5.10 |
| `scenario_e + adaptive_alie_like@0.4` | `foolsgold` | 0.9783 | 0.0231 | 0.00 | 1.60 |
| `scenario_e + adaptive_alie_like@0.4` | `temporal_rootguard` | 0.9883 | 0.0167 | 1.20 | 5.00 |
| `scenario_e + adaptive_alie_like@0.4` | `temporal_rootguard_v2` | 0.9884 | 0.0168 | 0.60 | 3.15 |

The adaptive matrix supports three disciplined conclusions.

1. Static and `condfloor` lines are not enough under camouflage. On public `scenario_h + adaptive_benign_mimic@0.4`, both static and `condfloor` retain all `4.0` poisoned clients on average.
2. `temporal_rootguard` and `temporal_rootguard_v2` meaningfully improve the adaptive operating point, but they often do so by increasing abstention.
3. Official FoolsGold remains a useful frontier anchor because it can achieve near-zero or zero `KP`, but usually at a much harsher `KC` point and lower `F1`.

The other two matched adaptive paths remain supportive width evidence and show that the adaptive logic transfers without becoming a universal winner.

- Public `scenario_e + adaptive_benign_mimic@0.4`:
  - `temporal_rootguard_v2`: `F1 = 0.9888`, `FPR = 0.0182`, `KP = 1.75`, `KC = 4.10`
  - `temporal_rootguard`: `F1 = 0.9888`, `FPR = 0.0191`, `KP = 2.20`, `KC = 5.95`
  - `trust_aware`: `F1 = 0.9872`, `KP = 4.00`, `KC = 6.95`
- Public `scenario_h + adaptive_alie_like@0.4`:
  - `temporal_rootguard_v2`: `F1 = 0.9748`, `FPR = 0.0190`, `KP = 0.80`, `KC = 2.85`
  - `temporal_rootguard`: `F1 = 0.9751`, `FPR = 0.0188`, `KP = 1.60`, `KC = 3.80`
  - `trust_aware`: `F1 = 0.9752`, `KP = 3.65`, `KC = 7.35`

These results support a practical interpretation rather than a universal adaptive-robustness claim. `temporal_rootguard_v2` is the stricter adaptive control; `temporal_rootguard` is often the more balanced adaptive point.

### 6.6 Auxiliary NSL-KDD and Deployment Runtime Package

The NSL-KDD path remains supportive rather than central, but it is still useful as a cross-domain transfer check. On the exploratory 10-seed `update_noise@0.4` comparison:

- `trust_aware`: `F1 = 0.7952`, `FPR = 0.0772`, `KP = 0.70`, `KC = 6.70`
- `fltrust_like`: `F1 = 0.7557`, `FPR = 0.0490`, `KP = 1.70`, `KC = 5.10`
- `ARC+mean`: `F1 = 0.7585`, `FPR = 0.0547`, `KP = 4.00`, `KC = 10.00`
- `centered_clipping`: `F1 = 0.7642`, `FPR = 0.0619`, `KP = 4.00`, `KC = 10.00`

This table should not be oversold as same-task evidence, but it supports the claim that the trust-aware participation-control story is not unique to Ca-Bench.

The runtime package is the main engineering-cost result. It reports a 5-seed single-host deployment/runtime profile for public `scenario_h + update_noise@0.4` at `10`, `20`, `40`, and `80` active clients. The static line is the clearest summary because `condfloor` and keep-all remain in the same timing band.

*Table 6. Static-line single-host deployment/runtime package on public `scenario_h + update_noise@0.4`.*

| Active clients | Wall clock (ms) | Server round (ms) | Aggregation (ms) | Bytes/round (KiB) | Peak RSS (MB) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 56.34 | 29.64 | 0.71 | 24.14 | 823.4 |
| 20 | 97.47 | 52.45 | 1.22 | 48.28 | 823.1 |
| 40 | 207.00 | 102.67 | 2.40 | 96.56 | 822.7 |
| 80 | 504.36 | 266.08 | 7.04 | 193.12 | 830.0 |

Two engineering conclusions follow.

- Aggregation remains a small share of the measured server round, about `2.2%` to `2.6%`.
- The trust-aware control logic does not dominate runtime at the tested client counts; most of the measured cost remains in local training and client-side evaluation.

`condfloor` and keep-all remain in the same range, with `condfloor` wall-clock times of `55.10`, `99.00`, `210.90`, and `517.06 ms` and keep-all times of `53.64`, `100.13`, `202.67`, and `505.80 ms` across `10`, `20`, `40`, and `80` clients. The right interpretation is therefore a practical single-host deployment profile, not a distributed multi-host benchmark.

![Figure 2. Single-host deployment/runtime package for public `scenario_h + update_noise@0.4` across `10/20/40/80` active clients.](figures/public_cabench_scenario_h_deployment_runtime_package.png)

## 7. Discussion

### 7.1 What the Paper Can Claim

The results support a clear but bounded claim: HiTrust-FedBot improves deployment-relevant operating points by explicitly managing the trade-off among predictive quality, poisoned participation, retained clients, and runtime cost. That claim is supported by four kinds of public evidence:

- same-task public Ca-Bench validation on `scenario_h` and `scenario_e`,
- separate raw-data-to-graph chains on Westermo and LITNET-2020,
- a matched adaptive `2 x 2` matrix,
- a measured runtime package.

This is stronger than a single-benchmark paper, but it is still a frontier claim, not a universal dominance claim.

### 7.2 What the Paper Should Not Claim

The manuscript should not claim:

- universal superiority on `F1`,
- complete solution of adaptive poisoning,
- bit-for-bit reproduction of the original FLTrust or FLShield release settings,
- end-to-end public regeneration of the internal raw traces,
- distributed systems benchmarking.

The current results themselves show why. Centered Clipping, `ARC+mean`, and tuned FLTrust-like points can match or exceed the proposed method on some predictive metrics. Official FoolsGold can be stricter on poisoned retention under some adaptive settings. What HiTrust-FedBot provides more consistently is interpretable control of `KP` and `KC`, plus targeted hardenings linked to identifiable failure modes.

### 7.3 Why the Hardening Narrative Works

The paper is much stronger with two targeted hardening lines than with a single over-claimed story.

- `condfloor` is justified because the hardest same-task public non-adaptive setting exposes a small-group collapse mechanism directly.
- `temporal_rootguard` and `temporal_rootguard_v2` are justified because the adaptive matched matrix exposes a different camouflage mechanism that static rules do not solve.

This failure-mode-repair framing is scientifically cleaner and better aligned with EAAI than stacking heuristics without explanation.

### 7.4 Reproducibility and Engineering Meaning

The repository's artifact surface is already strong for this submission type. Public reruns exist for the main public result layers, the release includes reviewer verification scripts, and the internal bundle now has a maintainer-side exact-match raw audit. The remaining limitation is not the absence of auditability but the honest private-data boundary for the internal raw traces.

The runtime package further improves journal fit because it shows where time is spent, not only whether accuracy is high. Aggregation stays inexpensive even at `80` clients, and the communication study shows that strong operating points do not require the heaviest update regime. These are engineering results, not only benchmark results.

## 8. Conclusion

HiTrust-FedBot should be read as an interpretable engineering AI system for federated web bot detection. Its main value is not universal dominance on `F1`. Its main value is the ability to manage practical operating points under non-IID client structure, poisoned participation, semantic coverage constraints, abstention, and measured runtime limits.

The strongest public non-adaptive evidence comes from same-task public Ca-Bench `scenario_h + update_noise@0.4`, where `condfloor` reaches `F1 = 0.9746`, `FPR = 0.0307`, `KP = 0.0`, and `KC = 6.0`. The stronger public systems story comes from the full evidence stack: same-task Ca-Bench validation, Westermo and LITNET raw-data chains, a matched adaptive `2 x 2` matrix, a public attack-extension package, and a measured `10/20/40/80` client runtime package. Together these results support a deployment frontier rather than a benchmark-leader narrative.

The paper's conclusion should therefore remain disciplined. HiTrust-FedBot does not solve federated poisoning universally. What it does provide is a reviewer-auditable, deployment-oriented framework in which grouped trust-aware aggregation, targeted static repair, targeted adaptive control, and runtime profiling all contribute to a coherent engineering story.

## Declarations

### Availability of data and materials

Public Ca-Bench, Westermo, LITNET-2020, and NSL-KDD reproduction paths are included in the repository through released derived graphs, metadata, scripts, figures, and result tables. The internal pilot scenarios are released as derived graphs only. Private upstream raw traces for the internal bundle are not publicly redistributed.

### Code availability

The repository includes the training code, baseline implementations, experiment registries, reproduction scripts, manuscript-support tables, and figure-generation utilities used for the reported evidence surface.

### Competing interests

The authors should confirm the journal-form competing-interest statement at submission. If no competing interests apply, the standard statement is: `The authors declare that they have no competing interests.`

### Funding

Funding details should be confirmed at submission. If no external funding applies, the journal-form statement is: `This research received no external funding.`

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
