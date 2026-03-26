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

"$PY_BIN" core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json \
  --project-root "$REPO_ROOT"

bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh

echo "[OK] Reviewer bundle reproduction completed."
