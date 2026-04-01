#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55}"
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

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_temporal_rootguard_v2

for cfg in \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_sage_adaptive_benign_mimic_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_layerwise.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_behavioral.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_soft_weighting.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_peer_penalty.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_temporal_rootguard_v2" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_cabench_scenario_h_temporal_rootguard_sage_adaptive_benign_mimic_frac0p4 \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4 \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_layerwise \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_behavioral \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_soft_weighting \
  public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_peer_penalty
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "temporal_rootguard=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_sage_adaptive_benign_mimic_frac0p4_seed_stats.json,temporal_rootguard_v2=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_seed_stats.json,no_layerwise=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_layerwise_seed_stats.json,no_behavioral=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_behavioral_seed_stats.json,no_soft_weighting=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_soft_weighting_seed_stats.json,no_peer_penalty=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_sage_adaptive_benign_mimic_frac0p4_no_peer_penalty_seed_stats.json" \
  --reference temporal_rootguard_v2 \
  --title-prefix Public-CaBench-ScenarioH_temporal-rootguard-v2-ablation_adaptive-benign-mimic0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.png" \
  --include-kept-clients

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.png"

echo "[OK] Public Ca-Bench scenario_h temporal_rootguard_v2 ablation reproduced."
