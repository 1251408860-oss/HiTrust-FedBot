#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

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

cd "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/build_cross_dataset_frontier_summary.py \
  --project-root "$REPO_ROOT" \
  --output-table "paper_hitrust/tables/cross_dataset_f1_kp_kc_frontier_summary.json" \
  --output-figure "paper_hitrust/figures/cross_dataset_f1_kp_kc_frontier_summary.png"

echo "[OK] Cross-dataset frontier summary figure reproduced."
