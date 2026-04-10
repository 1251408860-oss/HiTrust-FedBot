# HiTrust Graph Schema Contract (2026-04-07)

HiTrust-FedBot now treats external corpora such as Ca-Bench and NSL-KDD as data inputs only. The runtime contract for graph artifacts is defined locally in `core_experiments/internal/graph_contract.py`.

## Required Graph Fields

Every graph consumed by `core_experiments/internal/run_real_fed_pilot.py` must provide:

- node features: `x`, `x_norm`
- graph structure: `edge_index`
- labels and flow ownership: `y`, `window_idx`, `ip_idx`, `source_ips`
- split masks: `train_mask`, `val_mask`, `test_mask`, `temporal_train_mask`, `temporal_test_mask`
- metadata: `dataset_name`, `dataset_variant`, `dataset_source`, `split_scheme`, `target_ip`, `delta_t`, `n_windows`

## Provenance Rules

- Repo-local files are stored as repository-relative paths rather than environment-specific absolute paths.
- Optional manifest support uses `manifest_file` plus embedded `manifest_metadata` with `topology`, `run_config`, `roles`, and `ip_labels`.
- `graph_contract_version` is currently `hitrust_graph_v1`.
- `graph_source_kind` distinguishes released bootstrap graphs from external public datasets.
- Public Ca-Bench reruns use the vendored builder under `data_hitrust/public_benchmarks/cabench_v1/tools/`.

## Design Boundary

The local runtime must not depend on an upstream moving branch for graph semantics. Upstream projects may still supply:

- released data archives
- published manifests
- historical builder source copied into this repository

They do not define the active graph contract used by HiTrust-FedBot.
