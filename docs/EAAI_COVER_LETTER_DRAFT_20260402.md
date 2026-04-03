# EAAI Cover Letter Draft (2026-04-02)

Dear Editor,

We submit the manuscript titled **"HiTrust-FedBot: Trust-Aware Hierarchical Federated Web Bot Detection with Group-Coverage-Constrained Filtering"** for consideration in *Engineering Applications of Artificial Intelligence*.

This submission fits EAAI because it is framed as an engineering AI system paper rather than a purely theoretical federated-learning robustness paper. The manuscript studies a deployment-motivated problem: privacy-sensitive, bandwidth-constrained federated web bot detection at the network edge, where non-IID client structure and malicious client participation must be handled jointly. The main AI contribution is an interpretable trust-aware hierarchical aggregation framework with explicit semantic-group coverage constraints and targeted hardening controls for identified failure regimes.

The evaluation is designed to support engineering relevance and reproducibility.

- Same-task public external validation is provided on Ca-Bench `scenario_e` and `scenario_h`.
- Key public claims are backed by matched 10-seed paired testing rather than single-run comparisons.
- The non-adaptive comparator set includes keep-all, mean, median, Krum, RFA, FLTrust-like, FLShield-like, FedTruth-like, and modern Centered Clipping and `ARC+mean` baselines.
- The adaptive suite includes an official FoolsGold comparator to expose the poisoning-retention versus abstention frontier.

The manuscript intentionally keeps its claims conservative. The main conclusion is not universal superiority on F1, but that the proposed controls occupy more practical operating points when retained poisoned participation is considered together with predictive quality and client retention. This conservative positioning is reflected consistently in the abstract, results, discussion, and submission-facing highlights.

The review manuscript is anonymized. Title-page metadata, highlights, and data-availability materials are prepared as separate files. The repository also includes reproduction scripts and artifact-verification checks for the submission package.

Sincerely,

[Corresponding Author Name]  
[Affiliation]  
[Email]  
[Date]
