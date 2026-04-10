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
- `robust_fl_frontier_note_20260402.md`: manuscript-facing note on more recent robust-FL baseline options after the public baseline refresh
- `caf_baseline_note_20260409.md`: manuscript-facing note for the new CAF baseline added to the primary public non-adaptive suite
- `../docs/REFERENCE_BASELINE_PROVENANCE_20260407.md`: reviewer-facing provenance note for the pinned reference baseline bundle

Current manuscript-support files kept in the repo include:

- `manuscript_eaai_compact_draft_20260401.md`
- `fltrust_like_baseline_note_20260330.md`
- `foolsgold_official_baseline_note_20260331.md`
- `robust_fl_frontier_note_20260402.md`
- `centered_clipping_baseline_note_20260402.md`
- `caf_baseline_note_20260409.md`
- `arc_baseline_note_20260402.md`

Key public-evidence files for the current manuscript round include:

- `tables/public_cabench_scenario_e_update_noise_baseline_comparison.json`
- `tables/public_cabench_scenario_h_update_noise_baseline_comparison.json`
- `tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json`
- `tables/public_cabench_scenario_h_colluding_update_noise_comparison.json`
- `tables/public_cabench_scenario_h_multi_round_stealth_comparison.json`
- `tables/public_westermo_update_noise_baseline_comparison.json`
- `tables/public_westermo_update_noise_condfloor_comparison.json`
- `tables/public_westermo_sign_flip_baseline_comparison.json`
- `tables/public_westermo_sign_flip_condfloor_comparison.json`
- `tables/public_litnet2020_udp_update_noise_baseline_comparison.json`
- `tables/public_litnet2020_udp_update_noise_condfloor_comparison.json`
- `tables/cross_dataset_f1_kp_kc_frontier_summary.json`
- `tables/public_cabench_scenario_h_adaptive_benign_mimic_comparison.json`
- `tables/public_cabench_scenario_e_adaptive_alie_like_comparison.json`
- `tables/public_cabench_scenario_h_server_runtime_benchmark.json`
- `tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json`
- `tables/public_nslkdd_update_noise_baseline_comparison.json`

The public comparison artifacts are maintained from matched-seed summaries. The current primary non-adaptive rerun entry points use matched 20-seed public sweeps for Ca-Bench `scenario_e`, Ca-Bench `scenario_h`, Westermo `update_noise`, Westermo `sign_flip`, and LITNET-2020 UDP-flood `update_noise`, and rebuild the trust-vs-keepall tables with matched-seed paired testing. The Westermo `sign_flip` rerun remains supportive attack-family-width evidence rather than a replacement for the 20-seed Westermo `update_noise` mainline, while the LITNET-2020 rerun is positioned as an additional raw-data-chain stress point rather than as a stronger same-task benchmark. A promoted adaptive rerun entry point now rebuilds matched 20-seed public `scenario_h + adaptive_benign_mimic@0.4` and `scenario_e + adaptive_alie_like@0.4` comparisons; the remaining adaptive paths stay 10-seed exploratory sweeps.

The non-adaptive update-noise comparison tables now also include modern Centered Clipping, CAF, and `ARC+mean` comparators, which are useful for separating strong aggregation metrics from explicit poisoned-participation control.

The strongest current paper-facing public story is no longer Ca-Bench alone. Same-task Ca-Bench `scenario_h` remains the main hardest-setting stress point, but the Westermo and LITNET-2020 raw-data chains are now part of the primary public evidence because they show the same retained-poisoned-participation frontier under separate public raw-data to graph pipelines. Westermo also has a second non-adaptive attack-family check through the `sign_flip` comparison package, while LITNET-2020 exposes a harsher small-group-collapse regime that makes the `condfloor` repair easier to justify conservatively.

A separate 5-seed runtime benchmark now reports `server_round_ms`, `server_aggregation_ms`, `client_eval_ms`, `global_eval_ms`, `local_training_ms`, `round_wall_clock_ms`, `bytes_per_round_est`, and `active_clients` for the public `scenario_h + update_noise@0.4` static / `condfloor` / keep-all lines. The new LITNET-2020 matched-seed tables also retain `server_round_ms`, `round_wall_clock_ms`, `process_peak_rss_mb`, and `bytes_per_round_est`, giving a second public measured-cost slice even though the dedicated scaling package remains on public `scenario_h`. This is intended as a minimal engineering-cost benchmark, not as a large-client scaling study.

For paper-facing summary use, the repository now also includes `figures/cross_dataset_f1_kp_kc_frontier_summary.png`, which compresses the main public non-adaptive evidence into a four-panel cross-dataset frontier view with `F1`, retained poisoned clients (`KP`), and retained clients (`KC`) shown simultaneously.

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
- `docs/EAAI_COVER_LETTER_DRAFT_20260402.md`
- `docs/EAAI_TITLE_PAGE_DRAFT_20260402.md`
- `docs/EAAI_HIGHLIGHTS_DRAFT_20260402.md`
