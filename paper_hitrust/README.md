# `paper_hitrust/`

This directory contains paper-facing outputs and manuscript-support materials.

## Main Contents

- `runs/`: precomputed experimental run outputs
- `tables/`: JSON summaries used to support paper claims
- `figures/`: paper-ready figures referenced by the manuscript workflow
- `artifact_manifest_20260324.json`: compact manifest of artifact-side deliverables
- manuscript-support markdown files for Chinese and English paper drafting

## Reviewer Use

Reviewers who want to inspect delivered evidence without re-running the full pipelines should start from:

- `tables/`
- `figures/`
- `artifact_manifest_20260324.json`

The release-facing integrity metadata is stored alongside the paper artifact:

- `docs/ARTIFACT_STATUS_20260326.md`
- `docs/reviewer_bundle_sha256_20260326.txt`
- `core_experiments/reproduce/verify_artifact_bundle.sh`
