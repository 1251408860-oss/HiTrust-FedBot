#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55}"

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

SWEEP_ARGS=()
if [[ "${SKIP_EXISTING:-1}" == "1" ]]; then
  SWEEP_ARGS+=(--skip-existing)
fi

"$PY_BIN" core_experiments/internal/build_public_cabench_graph.py \
  --project-root "$REPO_ROOT" \
  --scenario-name "scenario_h_mimic_heavy_overlap" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  --python-bin "$PY_BIN"

mkdir -p core_experiments/configs_hitrust/seed_sweeps_runtime_benchmark

for cfg in \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_runtimebench.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_runtimebench.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_runtimebench.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_runtime_benchmark" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_runtimebench \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_runtimebench \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_runtimebench
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_runtime_comparison_report.py \
  --method-specs "static=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_runtimebench_seed_stats.json,condfloor=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_runtimebench_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_runtimebench_seed_stats.json" \
  --title-prefix Public-CaBench-scenario-h-server-runtime \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_server_runtime_benchmark.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_server_runtime_benchmark.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_server_runtime_benchmark.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_server_runtime_benchmark.png"

echo "[OK] Public server runtime benchmark artifact reproduced."
