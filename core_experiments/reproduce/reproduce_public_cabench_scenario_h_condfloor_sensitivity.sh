#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCENARIO_NAME="scenario_h_mimic_heavy_overlap"

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

GRID_ARGS=()
if [[ "${SKIP_EXISTING:-1}" == "1" ]]; then
  GRID_ARGS+=(--skip-existing)
fi

cd "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/build_public_cabench_graph.py \
  --project-root "$REPO_ROOT" \
  --scenario-name "$SCENARIO_NAME" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  --python-bin "$PY_BIN"

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_condfloor_sensitivity

"$PY_BIN" core_experiments/internal/sweep_real_config_grid.py \
  --base-config "$REPO_ROOT/core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor.json" \
  --grid-file "$REPO_ROOT/core_experiments/configs_hitrust/public_cabench_scenario_h_condfloor_sensitivity_grid.json" \
  --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
  --python-bin "$PY_BIN" \
  --project-root "$REPO_ROOT" \
  --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_condfloor_sensitivity" \
  "${GRID_ARGS[@]}"

"$PY_BIN" core_experiments/internal/summarize_real_config_grid.py \
  --manifest-file "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_condfloor_sensitivity/grid_manifest.json" \
  --runs-root "$REPO_ROOT/paper_hitrust/runs" \
  --output-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_condfloor_sensitivity_grid_summary.json"

"$PY_BIN" core_experiments/internal/build_condfloor_sensitivity_report.py \
  --grid-summary-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_condfloor_sensitivity_grid_summary.json" \
  --title-prefix Public-CaBench-ScenarioH_condfloor-sensitivity \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_condfloor_sensitivity_report.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_condfloor_sensitivity.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_condfloor_sensitivity.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_condfloor_sensitivity.png"

echo "[OK] Public Ca-Bench scenario_h condfloor sensitivity reproduced."
