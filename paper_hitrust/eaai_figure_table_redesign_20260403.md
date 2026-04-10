# EAAI Figure and Table Redesign Plan (2026-04-03)

This note defines a more EAAI-like figure/table package for the current HiTrust-FedBot manuscript round.

It is based on three constraints:

1. The paper should read like an engineering-AI systems paper, not a benchmark dump.
2. The main manuscript should contain a small number of readable, interpretable figures.
3. Framework diagrams and module diagrams should explain the method before the reader reaches the long result sections.

## Style Lessons from the Reference EAAI Papers

The strongest common visual patterns in the reference papers are:

- one large end-to-end framework figure early in the method section
- one additional pipeline or workflow figure that clarifies data flow or task setup
- one or two single-module explanation figures for the most novel internal blocks
- compact multi-panel result figures instead of many near-duplicate single-purpose plots
- short figure titles, with most explanation moved into the caption
- tables used for dense numerical evidence, while figures emphasize trend, mechanism, or operating-point interpretation

From the two concrete references inspected in this round:

- `Noise-aware-Graph-Neural-Networks-for-multimoda_2026_Engineering-Application.pdf`
  - uses a task-motivation figure before the full architecture
  - uses one clean overall framework figure and one graph-construction/module figure
  - uses a dense main-result table, then only a few high-value analysis figures
- `Data-driven-model-free-graph-multi-agent-deep-reinfo_2026_Engineering-Applic.pdf`
  - uses one overall framework figure and one single-structure GCN figure
  - keeps result figures focused on training behavior, operating distributions, and system behavior
  - uses tables for hyperparameters and main comparison evidence

These papers do not rely on many overloaded bar charts with long method names on the x-axis. Their visual language is cleaner and more hierarchical.

## Current Problems in the HiTrust-FedBot Figure Set

The current result plots under `paper_hitrust/figures/` have three main weaknesses:

- method labels are too long and frequently overlap
- titles repeat large scenario strings directly on the plot instead of moving context into captions
- multiple figures repeat the same visual grammar without building a coherent main-paper story

As a result, the current figure package is better suited to artifact support than to a polished journal manuscript.

## Target Main-Paper Figure Package

The main paper should be reorganized around the following eight figures:

### Fig. 1. Overall HiTrust-FedBot Framework

Type:
- framework figure

Placement:
- Section 3 or early Section 4

Purpose:
- explain the full training and deployment pipeline in one glance

Recommended content:
- edge clients with local graph partitions
- local GraphSAGE training
- client update upload
- server-side trust scoring
- group assignment and grouped retention
- hierarchical aggregation
- global model update and redistribution
- reported deployment outputs: predictive quality, retained poisoned clients, retained clients

Recommended layout:
- left-to-right
- 5 numbered stages
- one accent color for client-side computation, one accent color for server-side control

Caption emphasis:
- semantic-group preservation and poisoned-participation control are explicit design constraints, not side effects

### Fig. 2. Evaluation and Validation Workflow

Type:
- framework figure

Placement:
- near the start of the experimental section

Purpose:
- make the evidence hierarchy explicit

Recommended content:
- internal topology-aware pilots
- same-task public Ca-Bench `scenario_e`
- same-task public Ca-Bench `scenario_h`
- auxiliary public NSL-KDD transfer
- non-adaptive attacks and adaptive attacks
- matched public paired evaluation
- output metrics: `F1`, `FPR`, retained poisoned clients, retained total clients

Recommended layout:
- top-down or left-to-right flowchart
- three evidence tiers: internal, same-task public, auxiliary transfer

Caption emphasis:
- same-task public validation is the main external evidence, while NSL-KDD is auxiliary context only

### Fig. 3. Trust-Aware Hierarchical Aggregation and Coverage Filtering

Type:
- single-structure explanation figure

Placement:
- Section 4.2 or equivalent

Purpose:
- explain the most important core mechanism of the paper

Recommended content:
- client updates entering the server
- trust signals
- thresholding / trust normalization
- semantic grouping
- within-group aggregation
- minimum group coverage rule
- final group-level merge into a global update

Recommended layout:
- layered block diagram
- group boxes shown explicitly
- rejected vs retained clients visually separated

Caption emphasis:
- the method differs from flat robust aggregation because filtering and aggregation are coverage-aware and grouped

### Fig. 4. Hardening Mechanisms for Failure Regimes

Type:
- single-structure explanation figure

Placement:
- Section 4.3 or equivalent

Purpose:
- explain the two repairs without burying them in dense text

Recommended content:
- panel (a): `condfloor`
  - static group floor
  - low-trust group
  - conditional skip of floor repair
  - abstention when trust mass is too low
- panel (b): `temporal_rootguard` / `temporal_rootguard_v2`
  - multi-round trust smoothing
  - server-root anchor
  - drift penalty
  - peer redundancy penalty
  - final weighted keep / reject decision

Recommended layout:
- two subpanels in one figure
- use arrows and decision diamonds sparingly

Caption emphasis:
- these are targeted repairs for distinct failure regimes, not a claim of one universal defense

### Fig. 5. Main Non-Adaptive Public Comparison

Type:
- merged results figure

Placement:
- first main result figure

Purpose:
- replace several overlapping bar charts with one compact public comparison figure

Recommended content:
- three subpanels for:
  - public `scenario_e + update_noise@0.4`
  - public `scenario_h + update_noise@0.4`
  - public `NSL-KDD + update_noise@0.4`
- each subpanel should visualize:
  - `F1`
  - `FPR`
  - retained poisoned clients

Recommended methods shown:
- trust-aware
- `condfloor` where applicable
- `ARC+mean`
- Centered Clipping
- FLTrust-like
- keep-all

Methods such as mean / median / Krum / RFA should be moved to appendix or supplementary tables unless they are explicitly discussed in the paragraph.

Recommended visual form:
- horizontal grouped bars or Cleveland-dot style panels
- short labels only
- highlight the proposed line(s) in dark blue
- show non-proposed baselines in muted gray/teal/orange

Caption emphasis:
- strong aggregation baselines can match predictive metrics while still retaining poisoned clients

### Fig. 6. Adaptive Operating-Point Comparison

Type:
- merged results figure

Placement:
- adaptive result subsection

Purpose:
- replace multiple repetitive adaptive comparison bar charts with one figure that reveals the trade-off frontier

Recommended content:
- four subpanels:
  - `scenario_h + adaptive_benign_mimic@0.4`
  - `scenario_e + adaptive_benign_mimic@0.4`
  - `scenario_h + adaptive_alie_like@0.4`
  - `scenario_e + adaptive_alie_like@0.4`

Recommended methods shown:
- static trust-aware
- `condfloor` if included in the comparison
- `temporal_rootguard`
- `temporal_rootguard_v2`
- FLTrust-like
- FLShield-like
- official FoolsGold

Recommended visual form:
- scatter plot
- x-axis: retained poisoned clients
- y-axis: `F1`
- marker size or annotation: retained clients

This is closer to the actual paper narrative than four more long-label bar charts.

Caption emphasis:
- the adaptive story is about operating points on the poisoning-retention versus abstention frontier, not absolute dominance

### Fig. 7. Key Ablation and Sensitivity Figure

Type:
- merged analysis figure

Placement:
- late result section

Purpose:
- keep only the highest-value ablations in the main paper

Recommended content:
- panel (a): `scenario_h + update_noise@0.4` static vs `condfloor` vs keep-all vs FLTrust-like
- panel (b): `temporal_rootguard_v2` ablation on the most informative adaptive public case

Recommended visual form:
- two clean compact subpanels
- panel (a) can be a 3-metric grouped comparison
- panel (b) can be a coefficient/impact plot or short bar comparison

Caption emphasis:
- one panel explains the non-adaptive repair mechanism, the other explains what matters most in the adaptive repair

### Fig. 8. Communication and Deployment Efficiency Summary

Type:
- results figure

Placement:
- near the end of results or discussion

Purpose:
- preserve the engineering-AI deployment perspective

Recommended content:
- panel (a): communication cost versus `F1` for tuning modes
- panel (b): deployment-oriented metric summary or retained-client budget view

Recommended visual form:
- scatter or Pareto-style plot
- very small number of annotations

Caption emphasis:
- strong robustness does not require the heaviest communication regime

## Target Main-Paper Table Package

The main paper should be reduced to four dense tables.

### Table 1. Datasets, Scenarios, Attacks, and Evaluation Protocol

Should merge:
- dataset names
- scenario semantics
- attack families
- poison fractions
- seeds
- evaluation metrics

Purpose:
- remove setup duplication from the prose

### Table 2. Main Public Non-Adaptive Comparison

Should merge:
- `scenario_e`
- `scenario_h`
- auxiliary NSL-KDD

Columns:
- method
- `F1`
- `FPR`
- retained poisoned clients
- retained clients
- paired significance note where central to the claim

Purpose:
- this should be the main numerical anchor for the non-adaptive story

### Table 3. Adaptive Comparison Summary

Should merge:
- `scenario_e` and `scenario_h`
- both adaptive attacks

Columns:
- method
- `F1`
- `FPR`
- retained poisoned clients
- retained clients

Purpose:
- support the adaptive frontier story with compact numbers, while the figure shows the trade-off visually

### Table 4. Key Ablation / Sensitivity Summary

Should contain only:
- `condfloor` repair evidence in the hardest non-adaptive case
- `temporal_rootguard_v2` ablation essentials
- optionally one communication-efficiency line if it is cited in the discussion

## Current Figure-to-New-Figure Mapping

The following current figures are better treated as source artifacts for merged main-paper visuals rather than as direct manuscript figures:

- `figures/public_cabench_scenario_e_update_noise_baseline_comparison.png`
- `figures/public_cabench_scenario_h_update_noise_baseline_comparison.png`
- `figures/public_nslkdd_update_noise_baseline_comparison.png`
  - merge into new `Fig. 5`

- `figures/public_cabench_scenario_e_adaptive_alie_like_comparison.png`
- `figures/public_cabench_scenario_e_adaptive_benign_mimic_comparison.png`
- `figures/public_cabench_scenario_h_adaptive_alie_like_comparison.png`
- `figures/public_cabench_scenario_h_adaptive_benign_mimic_comparison.png`
  - merge into new `Fig. 6`

- `figures/public_cabench_scenario_h_update_noise_condfloor_comparison.png`
- `figures/public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.png`
  - merge into new `Fig. 7`

- `figures/comm_tradeoff.png`
- `figures/sage_comm_tradeoff.png`
  - merge/select into new `Fig. 8`

The following current figures should normally stay out of the main manuscript unless a paragraph directly depends on them:

- `figures/public_cabench_scenario_e_trust_vs_keepall_seed_comparison.png`
- `figures/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.png`
- `figures/public_nslkdd_trust_vs_keepall_seed_comparison.png`
- `figures/public_nslkdd_update_noise_condfloor_comparison.png`
- `figures/public_cabench_scenario_h_fltrust_like_sensitivity.png`
- `figures/seed11_keep_sweep_h_sage_update_noise_frac0p4_mechanism.png`
- most pilot-only diagnostic figures

These are more suitable as appendix, supplement, or artifact-side support.

## Visual Design Rules for the Redrawn Figures

To better match the reference EAAI papers, the new figure package should use the following rules:

- prefer white background with restrained colors
- use one primary highlight color for proposed methods
- use short method labels:
  - `Trust-aware`
  - `Condfloor`
  - `TRG`
  - `TRG-v2`
  - `ARC+Mean`
  - `Centered Clip`
  - `FLTrust-like`
  - `FLShield-like`
  - `FoolsGold`
  - `Keep-all`
- move long scenario strings from plot titles into captions
- use multi-panel labels `(a)`, `(b)`, `(c)`, `(d)`
- avoid more than five or six methods in one main-paper panel
- prefer horizontal comparison layouts when method names are long
- use tables for dense numbers and figures for mechanism or trade-off interpretation

## Recommended Manuscript Integration

Recommended chapter-to-figure placement:

- Section 3 or early Section 4:
  - Fig. 1
  - Fig. 2
- Method subsection:
  - Fig. 3
  - Fig. 4
- Results subsection:
  - Fig. 5
  - Fig. 6
  - Fig. 7
  - Fig. 8

This gives the paper:

- two framework figures
- two single-structure explanation figures
- four high-value result figures

which is much closer to the reference EAAI visual rhythm than the current artifact-heavy figure directory.

## Recommended Next Implementation Step

The next implementation round should do three concrete things:

1. redraw the four method diagrams as clean vector-style manuscript figures
2. replace the current long-label public comparison bar charts with merged main-paper figures
3. rewrite the result captions so that the figure titles stay short and the interpretation lives in the caption text

This is the smallest figure/table redesign that materially improves the current submission quality.
