#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55}"
CLIENT_COUNTS="${CLIENT_COUNTS:-10,20,40,80}"

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

"$PY_BIN" core_experiments/internal/build_public_cabench_graph.py \
  --project-root "$REPO_ROOT" \
  --scenario-name "scenario_h_mimic_heavy_overlap" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  --python-bin "$PY_BIN"

CONFIG_DIR="$REPO_ROOT/core_experiments/configs_hitrust/runtime_scaling_generated"
SERIES_INDEX="$CONFIG_DIR/runtime_scaling_index.json"
mkdir -p "$CONFIG_DIR"

"$PY_BIN" core_experiments/internal/generate_runtime_scaling_configs.py \
  --base-configs "static=$REPO_ROOT/core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_runtimebench.json,condfloor=$REPO_ROOT/core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_runtimebench.json,keepall=$REPO_ROOT/core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_runtimebench.json" \
  --client-counts "$CLIENT_COUNTS" \
  --output-dir "$CONFIG_DIR" \
  --output-index "$SERIES_INDEX"

SWEEP_ARGS=()
if [[ "${SKIP_EXISTING:-1}" == "1" ]]; then
  SWEEP_ARGS+=(--skip-existing)
fi

mapfile -t CONFIG_FILES < <("$PY_BIN" - <<PY
import json
from pathlib import Path

index = json.loads(Path("$SERIES_INDEX").read_text(encoding="utf-8"))
for row in index.get("rows", []):
    print(str(row["config_file"]))
PY
)

for cfg in "${CONFIG_FILES[@]}"
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$CONFIG_DIR" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for cfg in "${CONFIG_FILES[@]}"
do
  prefix="$(basename "$cfg" .json)"
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_runtime_scaling_report.py \
  --series-index "$SERIES_INDEX" \
  --stats-dir "$REPO_ROOT/paper_hitrust/tables" \
  --title-prefix Public-CaBench-scenario-h-server-runtime-scaling \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_server_runtime_scaling.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_server_runtime_scaling.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_server_runtime_scaling.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_server_runtime_scaling.png"

echo "[OK] Public server runtime scaling artifact reproduced."
