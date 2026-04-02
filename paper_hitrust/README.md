# `paper_hitrust/`

This directory contains paper-facing outputs and manuscript-support materials.

## Main Contents

- `runs/`: precomputed experimental run outputs
- `tables/`: JSON summaries used to support paper claims
- `figures/`: paper-ready figures referenced by the manuscript workflow
- `artifact_manifest_20260324.json`: compact manifest of artifact-side deliverables
- current manuscript-support markdown files for the release-facing paper narrative
- `fltrust_like_baseline_note_20260330.md`: manuscript-facing positioning note for the new FLTrust-like baseline and sensitivity evidence
- `foolsgold_official_baseline_note_20260331.md`: manuscript-facing positioning note for the official FoolsGold adaptive baseline
- `robust_fl_frontier_note_20260402.md`: manuscript-facing note on more recent robust-FL baseline options after the public 10-seed refresh

Current manuscript-support files kept in the repo include:

- `manuscript_eaai_compact_draft_20260401.md`
- `fltrust_like_baseline_note_20260330.md`
- `foolsgold_official_baseline_note_20260331.md`
- `robust_fl_frontier_note_20260402.md`

Key public-evidence files for the current manuscript round include:

- `tables/public_cabench_scenario_e_update_noise_baseline_comparison.json`
- `tables/public_cabench_scenario_h_update_noise_baseline_comparison.json`
- `tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json`
- `tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json`
- `tables/public_nslkdd_update_noise_baseline_comparison.json`

The public comparison artifacts are maintained from matched-seed summaries. The current rerun entry points default to 10-seed public sweeps and rebuild the trust-vs-keepall tables with matched-seed paired testing.

## Reviewer Use

Reviewers who want to inspect delivered evidence without re-running the full pipelines should start from:

- `tables/`
- `figures/`
- `artifact_manifest_20260324.json`

The release-facing integrity metadata is stored alongside the paper artifact:

- `docs/ARTIFACT_STATUS_20260326.md`
- `docs/reviewer_bundle_sha256_20260326.txt`
- `core_experiments/reproduce/verify_artifact_bundle.sh`

The checksum manifest covers the static release surface only. Precomputed outputs under `runs/`, `tables/`, and `figures/` are intentionally treated as mutable derived evidence because the reviewer rerun scripts rebuild them in place.

Submission-anonymization support scripts and templates are available under:

- `core_experiments/reproduce/check_anonymization_leaks.sh`
- `docs/EAAI_SUBMISSION_CHECKLIST_20260327.md`
- `docs/EAAI_TITLE_PAGE_TEMPLATE_20260327.md`
- `docs/EAAI_HIGHLIGHTS_TEMPLATE_20260327.md`
