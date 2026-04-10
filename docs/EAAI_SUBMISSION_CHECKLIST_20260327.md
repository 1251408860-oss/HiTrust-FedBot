# EAAI Submission Checklist (2026-03-27)

This checklist is for preparing a double-anonymized EAAI submission package from the current artifact repository.

## 1. Manuscript Package Split

- Main manuscript file (for review) contains no author names, affiliations, emails, or acknowledgements.
- Title page is uploaded as a separate file (`EAAI_TITLE_PAGE_TEMPLATE_20260327.md` as template).
- Highlights are uploaded as a separate file (`EAAI_HIGHLIGHTS_TEMPLATE_20260327.md` as template).
- Current working drafts for this submission round are `EAAI_COVER_LETTER_DRAFT_20260402.md`, `EAAI_TITLE_PAGE_DRAFT_20260402.md`, and `EAAI_HIGHLIGHTS_DRAFT_20260402.md`.

## 2. Anonymous-Main-File Checks

Run:

```bash
bash core_experiments/reproduce/check_anonymization_leaks.sh
```

Expected result:

- no email patterns in submission-facing markdown
- no explicit author/affiliation metadata lines in blinded manuscript package

If false positives appear, add a regex line to `docs/anonymization_allowlist.txt` with a short comment.

## 3. Reproducibility/Artifact Checks

Run:

```bash
bash core_experiments/reproduce/verify_artifact_bundle.sh
```

Recommended public external-validation commands:

```bash
bash core_experiments/reproduce/reproduce_public_cabench_validation.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh
bash core_experiments/reproduce/reproduce_public_westermo_validation.sh
bash core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh
bash core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh
bash core_experiments/reproduce/reproduce_public_adaptive_matched_validation.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh
bash core_experiments/reproduce/reproduce_public_server_runtime_benchmark.sh
bash core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

## 4. Required Narrative Constraints

- Treat trust-aware filtering as a conservative defense control.
- Treat FLTrust-like and FLShield-like as covered trust-bootstrapping comparators, not as the paper's proposed method.
- Treat Centered Clipping and CAF as modern aggregation-only comparators; if they appear strong on F1/FPR, also state that they retain all poisoned clients because they do not perform explicit participation control.
- Report security gain primarily as reduced poisoned participation.
- Keep accuracy claims near-neutral; do not claim universal F1 improvement.
- State that NSL-KDD is cross-domain auxiliary validation.
- State that Ca-Bench public scenario validation is same-task external evidence.
- State that Westermo and LITNET-2020 are public raw-data evidence chains, not auxiliary footnotes.
- State that Westermo `update_noise` is the main non-Ca-Bench public claim surface, Westermo `sign_flip` is supportive second-attack-family evidence, and LITNET-2020 UDP-flood is a matched 20-seed collapse-stress raw-data path rather than a same-task benchmark replacement.
- State that the internal pilot raw traces are still not publicly redistributed, but the repository now includes a maintainer-side exact-match raw audit for the released internal graph bundle.
- State that the primary non-adaptive public claims use matched 20-seed paired evaluation.
- State that `scenario_h + adaptive_benign_mimic@0.4` and `scenario_e + adaptive_alie_like@0.4` are now promoted matched 20-seed adaptive evidence, while the remaining adaptive public paths stay exploratory 10-seed evidence.
- State that conditional floor is a targeted hardening for the identified hardest-setting failure mode, not a universal default.
- If runtime/latency is reported, state that the repository now includes a 5-seed public `scenario_h` server-side scaling study over `10/20/40` clients with peak RSS, but not a distributed end-to-end deployment benchmark.

## 5. Upload-Order Sanity Check

1. Main anonymized manuscript
2. Title page
3. Highlights
4. Data-availability statement
5. Optional cover letter
6. Optional response-to-editor note on related manuscript separation
