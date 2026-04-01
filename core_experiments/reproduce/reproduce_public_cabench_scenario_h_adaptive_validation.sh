#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111}"
SCENARIO_NAME="scenario_h_mimic_heavy_overlap"
ATTACK_NAME="${ATTACK_NAME:-adaptive_benign_mimic}"
REFERENCE_LABEL="${REFERENCE_LABEL:-condfloor}"

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

SWEEP_ARGS=()
if [[ "${SKIP_EXISTING:-1}" == "1" ]]; then
  SWEEP_ARGS+=(--skip-existing)
fi

cd "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/build_public_cabench_graph.py \
  --project-root "$REPO_ROOT" \
  --scenario-name "$SCENARIO_NAME" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  --python-bin "$PY_BIN"

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_adaptive

for cfg in \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_condfloor.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_foolsgold_sage_${ATTACK_NAME}_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_${ATTACK_NAME}_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_flshield_like_sage_${ATTACK_NAME}_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_sage_${ATTACK_NAME}_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_${ATTACK_NAME}_frac0p4.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_adaptive" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4 \
  public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_condfloor \
  public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_keepall \
  public_cabench_scenario_h_foolsgold_sage_${ATTACK_NAME}_frac0p4 \
  public_cabench_scenario_h_fltrust_like_sage_${ATTACK_NAME}_frac0p4 \
  public_cabench_scenario_h_flshield_like_sage_${ATTACK_NAME}_frac0p4 \
  public_cabench_scenario_h_temporal_rootguard_sage_${ATTACK_NAME}_frac0p4 \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_${ATTACK_NAME}_frac0p4
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,foolsgold=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_foolsgold_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,flshield_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_flshield_like_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,temporal_rootguard=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,temporal_rootguard_v2=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_${ATTACK_NAME}_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_${ATTACK_NAME}_frac0p4_keepall_seed_stats.json" \
  --reference "$REFERENCE_LABEL" \
  --title-prefix "Public-CaBench-ScenarioH_${ATTACK_NAME}0p4" \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_${ATTACK_NAME}_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_${ATTACK_NAME}_comparison.png" \
  --include-kept-clients

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_${ATTACK_NAME}_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_${ATTACK_NAME}_comparison.png"

echo "[OK] Public Ca-Bench scenario_h ${ATTACK_NAME} validation reproduced."
