# EAAI Submission Checklist (2026-03-27)

This checklist is for preparing a double-anonymized EAAI submission package from the current artifact repository.

## 1. Manuscript Package Split

- Main manuscript file (for review) contains no author names, affiliations, emails, or acknowledgements.
- Title page is uploaded as a separate file (`EAAI_TITLE_PAGE_TEMPLATE_20260327.md` as template).
- Highlights are uploaded as a separate file (`EAAI_HIGHLIGHTS_TEMPLATE_20260327.md` as template).

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
bash core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh
bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
```

## 4. Required Narrative Constraints

- Treat trust-aware filtering as a conservative defense control.
- Treat FLTrust-like as a covered trust-bootstrapping baseline, not as the paper's proposed method.
- Report security gain primarily as reduced poisoned participation.
- Keep accuracy claims near-neutral; do not claim universal F1 improvement.
- State that NSL-KDD is cross-domain auxiliary validation.
- State that Ca-Bench public scenario validation is same-task external evidence.
- State that conditional floor is a targeted hardening for the identified hardest-setting failure mode, not a universal default.

## 5. Upload-Order Sanity Check

1. Main anonymized manuscript
2. Title page
3. Highlights
4. Data-availability statement
5. Optional response-to-editor note on related manuscript separation
