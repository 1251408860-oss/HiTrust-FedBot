# Related Work Citation Framework

This file is a drafting aid for [manuscript_cyber_submission_polished_20260323.md](/home/user/workspace/HiTrust-FedBot/paper_hitrust/manuscript_cyber_submission_polished_20260323.md). Replace all placeholder tags before submission.

## Placeholder Map

- `RW-FEDSEC-*`
  Intended topic: federated cyber-security detection, intrusion detection, malicious traffic analysis, abuse or bot detection with privacy-preserving training.
  Recommended count: 3-4 citations.
  Best mix: 1 survey or broad systems paper, 1-2 application papers, 1 recent cyber-security FL paper.
  Suggested search keywords: `federated intrusion detection`, `federated bot detection`, `federated malicious traffic classification`, `privacy-preserving cyber security federated learning`.

- `RW-ROBUSTFL-*`
  Intended topic: robust federated learning under Byzantine, poisoning, or backdoor attacks.
  Recommended count: 4-5 citations.
  Best mix: 1 foundational robust FL paper, 1 trust-based defense paper, 1 poisoning-defense paper, 1 recent survey or benchmark paper.
  Suggested search keywords: `Byzantine robust federated learning`, `poisoning defense federated learning`, `trust-aware federated aggregation`, `backdoor federated learning defense`.

- `RW-GNNSEC-*`
  Intended topic: graph neural networks for cyber-security analytics such as bot detection, fraud detection, abuse graph mining, anomaly detection.
  Recommended count: 3-4 citations.
  Best mix: 1 application survey, 2 domain papers closely aligned with graph-based detection, 1 paper connecting graph structure to security classification.
  Suggested search keywords: `graph neural network bot detection`, `GNN cyber security anomaly detection`, `graph-based abuse detection`, `graph fraud detection security`.

- `RW-GNN-*`
  Intended topic: general graph representation learning and GraphSAGE-style neighborhood aggregation.
  Recommended count: 2 citations.
  Best mix: 1 GraphSAGE paper, 1 general graph learning reference.
  Suggested search keywords: `GraphSAGE`, `inductive representation learning on large graphs`.

- `RW-COMM-*`
  Intended topic: communication-efficient federated optimization.
  Recommended count: 2 citations.
  Best mix: 1 classical communication-efficient FL paper, 1 recent systems-level communication paper.
  Suggested search keywords: `communication efficient federated learning`, `federated optimization communication cost`.

- `RW-PEFT-*`
  Intended topic: parameter-efficient fine-tuning or lightweight adaptation in federated or distributed settings.
  Recommended count: 2 citations.
  Best mix: 1 adapter or PEFT paper, 1 federated adaptation paper if available.
  Suggested search keywords: `parameter efficient fine tuning federated learning`, `adapter federated learning`, `lightweight adaptation edge models`.

## Recommended Related Work Structure

### 1. Federated cyber-security detection

Core claim to support:
Federated learning is already used for distributed security analytics, but prior work often emphasizes data decentralization more than topology-aware semantic coverage.

Good citation mix:
- one broad FL-for-security survey
- one intrusion or malicious-traffic paper
- one bot or abuse detection paper

### 2. Robust federated learning under poisoning

Core claim to support:
Existing defenses focus on robust aggregation, anomaly rejection, or trust scoring, but usually operate on a flat client pool.

Good citation mix:
- one classical robust aggregation paper
- one Byzantine or poisoning-defense paper
- one trust-scoring or client-selection defense
- one recent survey or benchmark

### 3. Graph learning for security

Core claim to support:
Graph structure is important for cyber-security detection tasks, which justifies using GraphSAGE rather than a purely feature-based baseline.

Good citation mix:
- one graph-security survey or overview
- one graph-based abuse/bot/fraud paper
- one GraphSAGE or inductive graph-learning reference

### 4. Communication-efficient adaptation

Core claim to support:
Deployment relevance depends not only on robustness but also on communication cost, motivating PEFT-style tuning comparisons.

Good citation mix:
- one communication-efficient FL paper
- one PEFT paper
- one edge or distributed adaptation paper if available

## Suggested Citation Density

- Introduction: 4-6 citations total.
- Related Work: 10-14 citations total.
- Method: 1-2 citations if you mention GraphSAGE or robust FL assumptions again.
- Discussion: optional 1-2 citations only if contrasting with prior robust FL literature.

## Minimal Submission-Safe Replacement Plan

If time is limited, prioritize replacement in this order:

1. Replace all `RW-ROBUSTFL-*` tags.
2. Replace all `RW-FEDSEC-*` tags.
3. Replace all `RW-GNNSEC-*` and `RW-GNN-*` tags.
4. Replace all `RW-COMM-*` and `RW-PEFT-*` tags.

## Journal-Style Guidance

- Prefer primary papers and high-quality surveys over blog posts or workshop-only drafts when possible.
- Keep the related-work section comparative rather than encyclopedic.
- Use citations to support specific contrasts:
  flat robust aggregation versus group-aware trust filtering,
  feature-only federated detection versus graph-structured detection,
  communication-heavy adaptation versus parameter-efficient tuning.
- Avoid citation dumping. Each paragraph should support one narrow argumentative move.
