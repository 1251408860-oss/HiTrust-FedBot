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

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_server_runtime_scaling.sh"

"$PY_BIN" core_experiments/internal/build_deployment_runtime_report.py \
  --series-index "$REPO_ROOT/core_experiments/configs_hitrust/runtime_scaling_generated/runtime_scaling_index.json" \
  --stats-dir "$REPO_ROOT/paper_hitrust/tables" \
  --title-prefix Public-CaBench-scenario-h-deployment-runtime-package \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_deployment_runtime_package.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_deployment_runtime_package.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_deployment_runtime_package.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_deployment_runtime_package.png"

echo "[OK] Public single-host deployment runtime package reproduced."
