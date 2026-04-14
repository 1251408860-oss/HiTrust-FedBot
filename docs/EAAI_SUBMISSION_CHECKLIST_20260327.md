# EAAI Submission Checklist (updated 2026-04-14)

This checklist is for preparing a double-anonymized EAAI submission package from the current artifact repository.

## 1. Manuscript Package Split

- Main manuscript file contains no author names, affiliations, emails, or acknowledgements.
- Title page is uploaded separately (`EAAI_TITLE_PAGE_TEMPLATE_20260327.md` as template).
- Highlights are uploaded separately (`EAAI_HIGHLIGHTS_TEMPLATE_20260327.md` as template).
- Data availability is uploaded separately (`EAAI_DATA_AVAILABILITY_TEMPLATE_20260327.md` as template).
- Current working drafts for this round are `EAAI_COVER_LETTER_DRAFT_20260402.md`, `EAAI_TITLE_PAGE_DRAFT_20260402.md`, and `EAAI_HIGHLIGHTS_DRAFT_20260402.md`.

## 2. Current EAAI Author-Guide Reminders

Checked against the current EAAI guide on `2026-04-14`.

- Abstract should stay within `250` words and clearly state the engineering problem, the artificial-intelligence contribution, and the main findings.
- Do not use undefined abbreviations in the title or abstract.
- Highlights should be prepared as a separate file; use `3-5` bullets and keep each bullet within `85` characters.
- Keep author identities and affiliations on the separate title page only for double-anonymized review.
- If generative artificial-intelligence tools were used in manuscript writing or language polishing, add the required disclosure in the submission workflow and package notes.

## 3. Anonymous-Main-File Checks

Run:

```bash
bash core_experiments/reproduce/check_anonymization_leaks.sh
```

Expected result:

- no email patterns in submission-facing markdown
- no explicit author or affiliation metadata lines in the blinded manuscript package

If false positives appear, add a regex line to `docs/anonymization_allowlist.txt` with a short comment.

## 4. Reproducibility and Artifact Checks

Run:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

Recommended public validation commands:

```bash
bash core_experiments/reproduce/reproduce_public_cabench_validation.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh
bash core_experiments/reproduce/reproduce_public_westermo_validation.sh
bash core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh
bash core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh
bash core_experiments/reproduce/reproduce_public_litnet2020_udp_sign_flip_validation.sh
bash core_experiments/reproduce/reproduce_public_adaptive_matched_validation.sh
bash core_experiments/reproduce/reproduce_public_adaptive_full_matrix_validation.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh
bash core_experiments/reproduce/reproduce_public_server_runtime_benchmark.sh
bash core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh
bash core_experiments/reproduce/reproduce_public_server_deployment_runtime_package.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

## 5. Required Narrative Constraints

- Treat trust-aware filtering as a conservative defense control.
- Treat FLTrust-like and FLShield-like as covered trust-bootstrapping comparators, not as the paper's proposed method.
- Treat Centered Clipping, CAF, and `ARC+mean` as aggregation-only comparators; if they look strong on F1 or FPR, also state that they do not perform explicit poisoned-participation control.
- Report security gain primarily as reduced retained poisoned participation.
- Keep predictive-performance claims near-neutral; do not claim universal F1 improvement.
- State that NSL-KDD is auxiliary cross-domain validation.
- State that Ca-Bench public scenario validation is same-task external evidence.
- State that Westermo and LITNET-2020 are public raw-data evidence chains, not auxiliary footnotes.
- State that Westermo `update_noise` and LITNET-2020 `update_noise` remain the main non-Ca-Bench operating-point tables.
- State that Westermo `sign_flip` and LITNET-2020 `sign_flip` are supportive second-attack-family evidence that broadens public width without changing the conservative claim boundary.
- State that the internal pilot raw traces are still not publicly redistributed, but the repository now includes a maintainer-side exact-match raw audit for the released internal graph bundle.
- State that the primary non-adaptive public claims use matched 20-seed paired evaluation.
- State that all four public adaptive scenario/attack combinations now have matched 20-seed reruns.
- State that `scenario_h + adaptive_benign_mimic@0.4` and `scenario_e + adaptive_alie_like@0.4` remain the two main-text adaptive anchors.
- State that `scenario_h + adaptive_alie_like@0.4` and `scenario_e + adaptive_benign_mimic@0.4` are supportive matched evidence that broadens adaptive width without creating a universal-win claim.
- State that conditional floor is a targeted hardening for the identified hardest-setting failure mode, not a universal default.
- If runtime or latency is reported, state that the repository now includes a 5-seed single-host deployment/runtime package over `10/20/40/80` clients with wall-clock time, local training time, client evaluation time, server-round time, bytes per round, and peak RSS; do not describe it as a distributed end-to-end benchmark.

## 6. Upload-Order Sanity Check

1. Main anonymized manuscript
2. Title page
3. Highlights
4. Data-availability statement
5. Optional cover letter
6. Optional response-to-editor note on related manuscript separation
