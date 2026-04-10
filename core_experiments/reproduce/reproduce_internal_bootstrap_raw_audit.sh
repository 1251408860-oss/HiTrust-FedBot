#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RAW_ROOT="${RAW_ROOT:-/home/user/workspace/Ca-Bench-temp/mininet_testbed/real_collection}"
MANIFEST_ROOT="${MANIFEST_ROOT:-$REPO_ROOT/data_hitrust/bootstrap/manifests}"
BUILDER_ROOT="${BUILDER_ROOT:-$REPO_ROOT/data_hitrust/public_benchmarks/cabench_v1/tools}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-$REPO_ROOT/paper_hitrust/artifacts/internal_bootstrap_raw_audit}"

if [[ -n "${PY_BIN:-}" ]]; then
  :
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
else
  echo "[FAIL] Neither python nor python3 is available." >&2
  exit 1
fi

mkdir -p "$ARTIFACT_ROOT"
cd "$REPO_ROOT"

SCENARIO_INDEX="$ARTIFACT_ROOT/scenario_index.json"
PARTITION_AUDIT="$ARTIFACT_ROOT/partition_audit.json"
RAW_BUILD_ROOT="$ARTIFACT_ROOT/rebuilt_raw"
NORMALIZED_ROOT="$ARTIFACT_ROOT/rebuilt_normalized"
REBUILT_INDEX="$ARTIFACT_ROOT/rebuilt_normalized_graph_index.json"
COMPARE_REPORT="$ARTIFACT_ROOT/internal_bootstrap_raw_audit_report.json"

"$PY_BIN" core_experiments/internal/build_scenario_index.py \
  --source-root "$RAW_ROOT" \
  --output-file "$SCENARIO_INDEX"

"$PY_BIN" core_experiments/internal/build_partition_audit_from_index.py \
  --scenario-index "$SCENARIO_INDEX" \
  --output-file "$PARTITION_AUDIT" \
  --partition-mode topology_noniid \
  --num-clients 10 \
  --seed 42

BUILD_ARGS=()
if [[ "${SKIP_EXISTING:-0}" == "1" ]]; then
  BUILD_ARGS+=(--skip-existing)
fi

"$PY_BIN" core_experiments/internal/build_bootstrap_graphs.py \
  --scenario-index "$SCENARIO_INDEX" \
  --legacy-project-root "$BUILDER_ROOT" \
  --python-bin "$PY_BIN" \
  --output-root "$RAW_BUILD_ROOT" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  "${BUILD_ARGS[@]}"

"$PY_BIN" core_experiments/internal/normalize_bootstrap_graphs.py \
  --graphs-root "$RAW_BUILD_ROOT/graphs" \
  --manifest-root "$MANIFEST_ROOT" \
  --output-root "$NORMALIZED_ROOT" \
  --project-root "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/build_graph_index.py \
  --graphs-root "$NORMALIZED_ROOT" \
  --output-file "$REBUILT_INDEX"

"$PY_BIN" core_experiments/internal/compare_bootstrap_graphs.py \
  --released-root "$REPO_ROOT/data_hitrust/bootstrap_graphs/graphs" \
  --rebuilt-root "$NORMALIZED_ROOT" \
  --output-file "$COMPARE_REPORT"

echo "[OK] Internal bootstrap raw audit reproduced at $ARTIFACT_ROOT"
