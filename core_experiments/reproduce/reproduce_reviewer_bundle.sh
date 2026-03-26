#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_BIN="${PY_BIN:-python}"

cd "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/run_hitrust_suite.py \
  --config core_experiments/configs_hitrust/smoke_topology_noniid.json \
  --project-root "$REPO_ROOT"

bash core_experiments/reproduce/reproduce_public_nslkdd_validation.sh
bash core_experiments/reproduce/reproduce_conditional_floor_validation.sh

echo "[OK] Reviewer bundle reproduction completed."
