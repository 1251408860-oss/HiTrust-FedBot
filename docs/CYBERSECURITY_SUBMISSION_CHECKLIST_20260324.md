# Cybersecurity Submission Checklist (2026-03-24)

This checklist is intended to help finalize the current repository draft for submission to *Cybersecurity*.

Official references consulted:

- SpringerOpen declarations guidance:
  - `https://www.springeropen.com/about/declarations`
- Springer pre-submission page for *Cybersecurity*:
  - `https://link.springer.com/pre-submission?journalId=42400`

## Manuscript package

- Main polished manuscript:
  - `paper_hitrust/manuscript_cyber_submission_polished_20260323.md`
- Full working draft:
  - `paper_hitrust/manuscript_cyber_submission_full_20260323.md`
- Title-page template:
  - `docs/CYBERSECURITY_TITLE_PAGE_TEMPLATE_20260324.md`
- Cover-letter draft:
  - `docs/CYBERSECURITY_COVER_LETTER_20260324.md`

## Experimental support package

- Core tables and figures:
  - `paper_hitrust/tables/`
  - `paper_hitrust/figures_sage_main/`
- Artifact manifest:
  - `paper_hitrust/artifact_manifest_20260324.json`
- Artifact notes:
  - `docs/ARTIFACT_RELEASE_20260324.md`
- Data-availability notes:
  - `docs/DATA_AVAILABILITY_20260324.md`

## Reproducibility scripts

- Public auxiliary validation:
  - `core_experiments/reproduce/reproduce_public_nslkdd_validation.sh`
- Conditional-floor hardening validation:
  - `core_experiments/reproduce/reproduce_conditional_floor_validation.sh`

## Author-supplied items still requiring confirmation

- Final author names and affiliations
- Corresponding-author email and postal affiliation
- Funding statement
- Competing-interest declaration
- Author-contribution roles
- Final acknowledgment text

## Final technical checks

- Confirm that the manuscript title, abstract, and conclusion all retain the conservative framing:
  - trust-aware filtering is a conservative security control
  - the principal gain is reducing poisoned participation
  - accuracy is near-neutral on average rather than universally improved
- Keep `conditional trust-mass floor` positioned as a targeted hardening, not as a universal replacement.
- Decide which mechanism and auxiliary-validation figures remain in the main paper versus supplementary material.
- Normalize references and headings to the journal template at final export.

## Recommended submission structure

1. Title page
2. Main manuscript
3. Supplementary artifact / reproducibility note
4. Cover letter
