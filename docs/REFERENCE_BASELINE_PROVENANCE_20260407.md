# Reference Baseline Provenance (2026-04-07)

This note records the reviewer-visible provenance anchors for the reference baseline bundle after the local registry update.

## Official-Code Anchor

- `foolsgold`
  - upstream repository: `https://github.com/DistributedML/FoolsGold`
  - pinned upstream commit: `0aa55114296a2d3c2bcb6f544a6fae31e8e7b8b4`
  - local provenance kind: `official_code_port`
  - interpretation: the repository implementation is intended to stay close to the official history-similarity rule and is the only current reference baseline in the bundle explicitly anchored to an official project repository.

## Official Toolkit Semantics

The following baselines remain local reimplementations in this repository, but their semantic anchor is now fixed to the ByzFL benchmark toolkit:

- upstream toolkit: `https://github.com/LPD-EPFL/byzfl`
- pinned upstream tag: `v0.0.11`
- pinned upstream commit: `5830978d991a0900748f7ce901dc3ca532081b26`

Mapped components:

- `mean`
  - upstream component: `Average`
- `median`
  - upstream component: `Median`
- `krum`
  - upstream component: `Krum`
- `rfa`
  - upstream component: `GeometricMedian`
- `centered_clipping`
  - upstream component: `CenteredClipping`
- `arc_mean`
  - upstream component: `ARC+Average`

The newer CAF baseline is also anchored to the official ByzFL toolkit surface, but through the official documentation page because the current repository records it as a toolkit-semantic reference rather than as a pinned vendored copy:

- `caf`
  - upstream component: `CAF`
  - upstream documentation: `https://byzfl.epfl.ch/aggregators/classes/caf.html`

## Adapted Comparator Anchors

The trust-bootstrapping comparators remain task-adapted for the current graph-federated setting, but their reviewer-visible upstream anchors are now explicit as well:

- `fltrust_like`
  - author code archive: `https://people.duke.edu/~zg70/code/fltrust.zip`
  - local provenance kind: `task_adapted_reimplementation`
  - official source kind: `author_code_archive_semantic_anchor`
  - upstream component: `server-root trust weighting`
  - interpretation: the local implementation is aligned to the original FLTrust trust-weighting semantics and author-released code archive, but it is still not a bit-for-bit recreation of the original image-FL release environment.

- `flshield_like`
  - upstream repository: `https://github.com/ehsanul9511/FLShield`
  - pinned upstream commit: `afe4474440f0b88b8f1d09ab5cf5a75fd7230e6a`
  - local provenance kind: `task_adapted_reimplementation`
  - official source kind: `official_repository_semantic_anchor`
  - upstream component: `validation-guided clustered client filtering`
  - interpretation: the local implementation is aligned to the official FLShield repository semantics while remaining adapted to the current graph-federated evaluation setting.

## Important Boundary

- The ByzFL pin is a provenance anchor for method semantics, not a claim that the local code is a direct vendored copy.
- The comparison tables now carry:
  - `official_source_kind`
  - `upstream_name`
  - `upstream_url`
  - `upstream_commit`
  - `upstream_tag`
  - `upstream_component`

This makes the artifact-level distinction explicit:

- `official_code_port`
  - used where the repo is intentionally tied to an official upstream implementation
- `paper_spec_reimplementation`
  - used where the repo keeps a local implementation but now exposes a pinned official semantic anchor
- `author_code_archive_semantic_anchor`
  - used where the repo keeps a local task adaptation but exposes the original author code archive as the semantic anchor
- `official_repository_semantic_anchor`
  - used where the repo keeps a local task adaptation but exposes a fixed official repository commit as the semantic anchor
