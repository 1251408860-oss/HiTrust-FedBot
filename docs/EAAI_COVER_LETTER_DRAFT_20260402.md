# EAAI Cover Letter Draft (updated 2026-04-09)

Dear Editor,

We submit the manuscript titled **"HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering"** for consideration in *Engineering Applications of Artificial Intelligence*.

This submission fits EAAI because it is framed as an engineering AI system paper rather than a purely theoretical federated-learning robustness paper. The manuscript studies a deployment-motivated problem: privacy-sensitive, bandwidth-constrained federated web bot detection at the network edge, where non-IID client structure and malicious client participation must be handled jointly. The main AI contribution is an interpretable trust-aware hierarchical aggregation framework with explicit semantic-group coverage constraints and targeted hardening controls for identified failure regimes.

The evaluation is designed to support engineering relevance and reproducibility.

- Same-task public external validation is provided on Ca-Bench `scenario_e` and `scenario_h`, and two non-Ca-Bench public raw-data evidence chains are provided on Westermo industrial intrusion traffic and LITNET-2020 UDP-flood flows.
- The Westermo raw-data chain is widened beyond a single non-adaptive attack family, with a mainline `update_noise@0.4` table and a supportive matched 20-seed `sign_flip@0.4` rerun.
- The matched 20-seed LITNET-2020 UDP-flood `update_noise@0.4` table adds a third public raw-data result path and exposes a harsher small-group-collapse regime without forcing a stronger universal-dominance claim.
- The released internal pilot bundle is now paired with a maintainer-side confidential raw-to-graph audit that exactly rebuilds all five shipped internal graphs from the preserved traces.
- The primary non-adaptive public claims are backed by matched 20-seed paired testing with multiplicity correction rather than single-run comparisons.
- The non-adaptive comparator set includes keep-all, mean, median, Krum, RFA, FLTrust-like, FLShield-like, FedTruth-like, and modern Centered Clipping, CAF, and `ARC+mean` baselines.
- The adaptive suite includes an official FoolsGold comparator to expose the poisoning-retention versus abstention frontier, and two adaptive public paths are now promoted to matched 20-seed paired evidence: `scenario_h + adaptive_benign_mimic@0.4` and `scenario_e + adaptive_alie_like@0.4`. The remaining adaptive paths stay exploratory 10-seed evidence.
- The reference baseline bundle now exposes pinned reviewer-visible provenance, including an official FoolsGold upstream commit, ByzFL semantic anchors for the main aggregation baselines, the original FLTrust author code archive, and a fixed official FLShield commit.
- A 5-seed server-side runtime scaling package over `10/20/40` clients with peak RSS is included to quantify aggregation-side engineering cost beyond the earlier 10-client reviewer scale.

The manuscript intentionally keeps its claims conservative. The main conclusion is not universal superiority on F1, but that the proposed controls occupy more practical operating points when retained poisoned participation is considered together with predictive quality and client retention. This conservative positioning is reflected consistently in the abstract, results, discussion, and submission-facing highlights.

The review manuscript is anonymized. Title-page metadata, highlights, and data-availability materials are prepared as separate files. The repository also includes reproduction scripts and artifact-verification checks for the submission package.

Sincerely,

[Corresponding Author Name]  
[Affiliation]  
[Email]  
[Date]
