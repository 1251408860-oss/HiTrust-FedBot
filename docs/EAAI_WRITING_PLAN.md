# EAAI Writing Plan

## 1. Purpose

This document is the writing blueprint for submitting **HiTrust-FedBot** to
*Engineering Applications of Artificial Intelligence* (EAAI).

It is not a generic paper-writing template. It is tailored to the current
repository state as of `2026-04-14`, including:

- the main draft:
  - `paper_hitrust/manuscript_eaai_compact_draft_20260401.md`
- the current experiment assessment:
  - `docs/EAAI_EXPERIMENT_EVALUATION_20260414.md`
- the paper-facing artifact surface:
  - `paper_hitrust/artifact_manifest_20260324.json`
- the reviewer-facing reproduction boundary:
  - `docs/ARTIFACT_STATUS_20260326.md`
  - `docs/DATA_AVAILABILITY_20260324.md`
  - `core_experiments/reproduce/verify_artifact_bundle.sh`

The goal of this plan is to turn the current draft into a manuscript that fits
EAAI as an **engineering AI systems paper** rather than a pure robust-FL
algorithm paper.

## 2. EAAI-Oriented Positioning

### 2.1 Journal Fit

The manuscript should be framed for EAAI around the following journal-facing
idea:

> HiTrust-FedBot is an interpretable, deployment-oriented AI framework for
> federated web bot detection under non-IID structure, poisoned participation,
> semantic coverage constraints, and practical runtime limits.

The paper should repeatedly demonstrate two things:

- the **AI contribution**:
  - trust-aware hierarchical federated bot detection with targeted hardening
    for specific failure modes
- the **engineering contribution**:
  - a deployable evaluation protocol that measures predictive quality,
    retained poisoned participation, retained clients, and runtime cost under
    reproducible public evidence

### 2.2 Official-Guide Constraints To Respect

These points should be checked again at submission time against the official
EAAI guide, but the current working assumptions are:

- abstract: at most `250` words
- keywords: `1-6`
- title and abstract should avoid undefined abbreviations
- article should be prepared in the journal's required submission format
- highlights should be supplied
- anonymization must remain consistent in the review version

Working note:

- confirm the current official instructions before final upload:
  - https://www.sciencedirect.com/journal/engineering-applications-of-artificial-intelligence/publish/guide-for-authors

## 3. Central Claim Architecture

### 3.1 One-Sentence Thesis

The manuscript should be built around one sentence:

> HiTrust-FedBot improves deployment-relevant operating points for federated
> bot detection by explicitly managing the trade-off among predictive quality,
> poisoned participation, semantic group coverage, abstention, and engineering
> cost.

### 3.2 What The Paper Should Claim

The paper should claim:

- the framework is useful for **edge federated bot detection**
- the framework is **interpretable**
- the framework addresses **specific observed failure modes**
- the evaluation now supports a **public, reviewer-auditable engineering story**
- the strongest value is a **deployment frontier**, not leaderboard dominance

### 3.3 What The Paper Must Not Claim

The paper should not claim:

- universal superiority on `F1`
- universal robustness under all poisoning regimes
- fully public end-to-end raw-data regeneration for the internal pilot bundle
- exact reproduction of original FLTrust or FLShield release settings
- distributed multi-host deployment benchmarking

### 3.4 Non-Negotiable Claim Boundary

The manuscript should explicitly maintain this boundary:

- primary paper claims come from:
  - same-task public Ca-Bench `scenario_e`
  - same-task public Ca-Bench `scenario_h`
  - public Westermo raw-data chain
  - public LITNET-2020 UDP-flood raw-data chain
  - public adaptive matched suite
  - public single-host runtime package
- internal pilot scenarios remain:
  - supportive
  - audit-backed
  - not fully public raw-data reproducible

## 4. Recommended Evidence Hierarchy

The evidence stack should be organized in three layers.

### 4.1 Layer 1: Primary Public Claims

These are the main paper claims and should receive the most narrative weight:

- public Ca-Bench `scenario_h + update_noise@0.4`
- public Ca-Bench `scenario_e + update_noise@0.4`
- cross-dataset frontier summary over the main public non-adaptive lines

Why:

- same task
- public
- directly reproducible
- easy for EAAI reviewers to interpret

### 4.2 Layer 2: Width Evidence

These should show that the paper is not a single-benchmark story:

- Westermo `update_noise@0.4`
- Westermo `sign_flip@0.4`
- LITNET-2020 UDP-flood `update_noise@0.4`
- LITNET-2020 UDP-flood `sign_flip@0.4`
- adaptive public `2 x 2` matrix
- public `scenario_h` attack-extension package
- auxiliary NSL-KDD transfer path

Interpretation rule:

- these results widen the evidence surface
- they should usually be described as **frontier evidence** or **width
  evidence**, not as a string of universal wins

### 4.3 Layer 3: Engineering Evidence

This layer is what makes the paper more EAAI-like and less benchmark-like:

- communication/tuning-cost evidence
- single-host deployment/runtime package over `10/20/40/80` clients
- artifact verification and reproduction surface
- pinned baseline provenance and audit notes

## 5. Recommended Manuscript Structure

The current draft structure is already close to a usable EAAI structure. The
final paper should keep the current major sections but tighten the emphasis
within them.

### 5.1 Title

Current working title:

- `HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering`

Acceptable alternatives if a more engineering-oriented framing is preferred:

- `HiTrust-FedBot: An Interpretable Federated Bot Detection Framework for Edge Deployment under Poisoned Participation`
- `HiTrust-FedBot: Trust-Aware Federated Web Bot Detection with Explicit Coverage and Poison-Participation Control`

Title guidance:

- avoid unexplained abbreviations
- keep the task and engineering deployment setting visible
- avoid titles that sound like a universal robust-FL theorem

### 5.2 Abstract

The abstract should be rewritten last, after the main claims and main figures
are fixed.

Required six-part order:

1. engineering problem
2. limitation of existing methods
3. HiTrust-FedBot contribution
4. evaluation surface
5. strongest quantitative result
6. engineering interpretation

The abstract should clearly separate:

- what is the AI method contribution
- what is the engineering application contribution

The abstract should report only a few headline numbers. The strongest candidate
is still the public Ca-Bench `scenario_h + update_noise@0.4` `condfloor`
result.

### 5.3 Introduction

The introduction should complete four tasks:

- define the engineering application
- explain why average prediction metrics are insufficient
- explain the gap in current robust federated methods
- state the paper's contributions with a conservative claim boundary

Recommended introduction flow:

1. edge bot detection and federated constraints
2. non-IID structure plus malicious participation plus semantic coverage
3. why flat robust aggregation or trust bootstrapping alone is insufficient
4. what HiTrust-FedBot contributes
5. what the paper claims, and what it does not claim

### 5.4 Related Work

Organize related work by problem family, not by paper chronology:

- federated learning for security detection
- Byzantine and poisoning robustness in federated learning
- graph learning for security analytics
- engineering gap:
  - semantic coverage
  - deployment-oriented evaluation
  - reproducible public evidence

The final paragraph of related work should say explicitly:

- this paper is not just another robust aggregation rule
- its distinguishing feature is the joint treatment of poisoned participation,
  semantic coverage, abstention, and deployment cost

### 5.5 Problem Setting

This section should stay concise and system-oriented.

It must define:

- what a client is
- what a graph partition is
- what semantic groups are
- what the threat model includes
- why retained poisoned clients and retained clients are part of the objective

The research objective should be stated as a deployment problem:

- not simply maximizing `F1`
- but finding practical operating points under security and coverage constraints

### 5.6 Proposed Method

The method section should be written as an engineering pipeline, not a formula
dump.

It should answer:

- what the framework does
- why grouped hierarchy is needed
- what trust-aware filtering does
- what each hardening variant repairs
- which failure mode each hardening addresses

For each variant, explicitly say whether it is:

- a mainline
- a targeted repair
- a supportive adaptive control

`condfloor` should always be described as:

- a targeted repair for small-group collapse

`temporal_rootguard` and `temporal_rootguard_v2` should always be described as:

- targeted adaptive controls
- not universal replacements

### 5.7 Experimental Setup

This section should be rewritten so that reviewers can understand the evidence
hierarchy without reading the repository.

It should clearly separate:

- internal topology-aware pilots
- same-task public Ca-Bench validation
- public raw-data validation chains:
  - Westermo
  - LITNET-2020 UDP-flood
- auxiliary public NSL-KDD
- adaptive public suite
- runtime and deployment package

It should also define:

- seeds
- matched evaluation
- multiplicity correction
- primary endpoints
- supportive endpoints
- baseline families

### 5.8 Results

Results should be ordered by claim importance, not by chronology.

Recommended order:

1. public Ca-Bench `scenario_h + update_noise@0.4`
2. public Ca-Bench `scenario_e + update_noise@0.4`
3. Westermo `update_noise@0.4`
4. LITNET-2020 UDP-flood `update_noise@0.4`
5. cross-dataset frontier figure
6. adaptive anchor cases
7. supportive width evidence
8. runtime and deployment evidence

Every result subsection should follow the same pattern:

1. why this setting matters
2. the key numbers
3. what claim it supports
4. what claim it does not support

### 5.9 Discussion

The discussion should convert experimental findings into engineering meaning.

It should contain three pillars:

- security versus coverage trade-off
- limitations and practical interpretation
- engineering cost and deployment scope

The discussion should repeatedly reinforce:

- deployment frontier, not universal dominance
- practical operating points, not single-metric leadership
- targeted repair logic, not heuristic stacking

### 5.10 Conclusion

The conclusion should not introduce any new evidence.

It should:

- restate the engineering problem
- restate the main public evidence surface
- restate the strongest supported deployment-oriented conclusion
- state the bounded reproducibility story honestly

## 6. Section-By-Section Writing Targets

### 6.1 Abstract Target

Target length:

- `190-230` words

Core content checklist:

- engineering AI problem
- trust-aware hierarchical method
- targeted hardening
- public evidence breadth
- one strongest result
- deployment interpretation

### 6.2 Introduction Target

Target length:

- `900-1300` words

Checklist:

- real engineering deployment scenario
- why graph structure matters
- why malicious participation matters
- why coverage and abstention matter
- contributions listed in exactly `4` bullets

### 6.3 Related Work Target

Target length:

- `700-1000` words

Checklist:

- no literature laundry list
- every paragraph ends in a gap relevant to the present paper

### 6.4 Problem Setting Target

Target length:

- `500-800` words

Checklist:

- formally defines retained poisoned clients and retained clients as part of
  evaluation meaning

### 6.5 Method Target

Target length:

- `1200-1800` words

Checklist:

- interpretable pipeline description
- one architecture figure
- one failure-mode explanation for each hardening

### 6.6 Experimental Setup Target

Target length:

- `900-1300` words

Checklist:

- public versus private boundary is explicit
- baseline provenance boundary is explicit
- primary versus supportive claims are explicit

### 6.7 Results Target

Target length:

- `1800-2600` words

Checklist:

- public same-task main results receive the largest share
- internal results do not dominate the section
- adaptive results do not displace the main public non-adaptive story

### 6.8 Discussion Target

Target length:

- `900-1400` words

Checklist:

- must sound like EAAI, not NeurIPS rebuttal text

### 6.9 Conclusion Target

Target length:

- `250-450` words

Checklist:

- compact
- claim-disciplined
- no exaggerated novelty language

## 7. Primary Figure And Table Plan

### 7.1 Main Paper Figures

The paper should keep the main figure set small and disciplined.

Recommended main figures:

1. cross-dataset frontier summary
   - `paper_hitrust/figures_eaai/cross_dataset_f1_kp_kc_frontier_summary.png`
2. public Ca-Bench `scenario_h` main comparison
   - `paper_hitrust/figures/public_cabench_scenario_h_update_noise_condfloor_comparison.png`
3. public Ca-Bench `scenario_e` main comparison
   - `paper_hitrust/figures/public_cabench_scenario_e_update_noise_baseline_comparison.png`
4. one adaptive anchor figure
   - likely `scenario_e + adaptive_alie_like` or `scenario_h + adaptive_benign_mimic`
5. deployment/runtime package figure
   - `paper_hitrust/figures/public_cabench_scenario_h_deployment_runtime_package.png`

Optional additional figure if space permits:

- public Westermo or LITNET representative comparison

### 7.2 Main Paper Tables

Recommended main tables:

1. experimental setup / evidence layers table
2. public Ca-Bench `scenario_h` main table
3. public Ca-Bench `scenario_e` main table
4. Westermo plus LITNET summary table
5. adaptive anchor table
6. runtime/deployment summary table

### 7.3 What Should Move To Supplementary Material

The following should normally not dominate the main paper:

- large seed-statistics files
- full baseline provenance detail
- all sensitivity grids
- all ablation raw outputs
- all internal-pilot detail tables
- every adaptive width table

## 8. Repository-To-Manuscript Mapping

Use the repository structure as a writing discipline tool.

### 8.1 Main Draft Inputs

- main manuscript:
  - `paper_hitrust/manuscript_eaai_compact_draft_20260401.md`
- paper artifact surface:
  - `paper_hitrust/artifact_manifest_20260324.json`
- paper-facing artifact description:
  - `paper_hitrust/README.md`

### 8.2 Review And Submission Support Files

- experiment readiness assessment:
  - `docs/EAAI_EXPERIMENT_EVALUATION_20260414.md`
- highlights draft:
  - `docs/EAAI_HIGHLIGHTS_DRAFT_20260402.md`
- cover letter draft:
  - `docs/EAAI_COVER_LETTER_DRAFT_20260402.md`
- title page draft:
  - `docs/EAAI_TITLE_PAGE_DRAFT_20260402.md`

### 8.3 Reproducibility Boundary Files

- artifact status:
  - `docs/ARTIFACT_STATUS_20260326.md`
- data availability:
  - `docs/DATA_AVAILABILITY_20260324.md`
- reviewer verification:
  - `core_experiments/reproduce/verify_artifact_bundle.sh`

These files should remain aligned with the wording in the manuscript.

## 9. Language Rules

### 9.1 Preferred Vocabulary

Use these phrases repeatedly:

- deployment-oriented
- operating point
- retained poisoned participation
- retained clients
- semantic group coverage
- abstention
- targeted hardening
- failure mode
- public evidence surface
- reviewer-auditable
- engineering control
- frontier

### 9.2 Disallowed Or High-Risk Vocabulary

Avoid or sharply limit:

- state of the art
- universally superior
- robust under all attacks
- significantly better in every setting
- complete end-to-end public reproducibility
- universally optimal
- solved adaptive poisoning

### 9.3 Preferred Result Interpretation Sentences

Good sentence patterns:

- "These results support a deployment-oriented interpretation rather than a universal dominance claim."
- "The value of this table is width evidence, not a new headline win."
- "The method improves the operating point by reducing retained poisoned participation while avoiding severe abstention."
- "`condfloor` should be read as a targeted repair for the identified small-group-collapse mechanism."
- "The adaptive controls occupy more practical operating points than aggressive abstention baselines."

## 10. Required Package Components Around The Manuscript

### 10.1 Highlights

EAAI highlights should be short and concrete.

Recommended working version:

- Trust-aware federated bot detection preserves semantic group coverage
- Matched public tests expose poison-retention versus abstention trade-offs
- Westermo and LITNET add two public raw-data evidence chains
- Adaptive controls improve practical operating points under camouflage
- Single-host runtime keeps aggregation under 7.1 ms at 80 clients

### 10.2 Cover Letter

The cover letter should emphasize:

- why the paper fits EAAI
- what the AI contribution is
- what the engineering application is
- what the public evidence and reproducibility surface are

It should not read like a long result dump.

### 10.3 Title Page

The title page should be separate from the anonymized review manuscript and
contain:

- title
- author list
- affiliations
- corresponding author details
- acknowledgements if required by the journal workflow

### 10.4 Data Availability Statement

The data availability statement must stay consistent with the repository:

- public data paths are reproducible
- internal pilot raw traces are not publicly redistributed
- internal graph bundle is audit-backed but not publicly raw-data-rebuildable

### 10.5 Graphical Abstract

If submitted, the graphical abstract should show:

- edge bot-detection problem
- trust-aware hierarchical pipeline
- public evidence stack
- deployment frontier

It should be a clean system diagram, not a decorative poster.

## 11. Revision Workflow

The manuscript should not be revised linearly from top to bottom.

Recommended order:

1. lock main claims
2. lock main figures and tables
3. rewrite results
4. rewrite discussion
5. rewrite abstract
6. rewrite introduction
7. compress related work
8. finalize conclusion
9. finalize highlights and cover letter

Reason:

- the paper should be claim-driven and figure-driven
- not background-driven

## 12. One-Week Execution Plan

### Day 1

- freeze the exact main claim boundary
- freeze the main figure set
- freeze the main table set
- mark all results as:
  - primary
  - width evidence
  - supportive only

### Day 2

- rewrite the main public non-adaptive results
- rewrite the cross-dataset frontier interpretation

### Day 3

- rewrite adaptive, ablation, and sensitivity into a supportive layer
- remove any universal-dominance language

### Day 4

- rewrite discussion and limitations
- strengthen engineering-cost interpretation

### Day 5

- rewrite abstract and introduction
- tighten contribution bullets

### Day 6

- finalize title, highlights, cover letter, and data availability wording
- review anonymization

### Day 7

- full read-through
- consistency check against artifact files
- submission packaging

## 13. Final Acceptance-Risk Checklist

Before submission, confirm all of the following are true:

- the abstract separates AI and engineering contributions
- the introduction defines the deployment problem clearly
- the strongest claims are tied to public evidence
- the internal raw-data boundary is stated honestly
- `condfloor` is described as a targeted repair, not a universal new default
- `temporal_rootguard` and `temporal_rootguard_v2` are described as frontier
  controls, not universal winners
- the runtime package is described as single-host deployment profiling, not a
  distributed systems benchmark
- the manuscript does not overclaim baseline reproduction fidelity
- all key figures and tables cited in the text are present in the artifact
  surface
- the wording in the manuscript, cover letter, and data availability statement
  is consistent

## 14. Final Standard For This Paper

The paper is ready for EAAI when it satisfies this standard:

> The manuscript presents HiTrust-FedBot as an interpretable engineering AI
> system for federated bot detection, supports its main claims with public
> same-task and public raw-data evidence, uses adaptive and ablation results as
> supportive frontier evidence, reports deployment-oriented runtime behavior,
> and keeps the reproducibility boundary explicit and honest.
