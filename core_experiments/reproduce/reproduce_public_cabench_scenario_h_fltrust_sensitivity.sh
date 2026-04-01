#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33}"
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

cd "$REPO_ROOT"

"$PY_BIN" core_experiments/internal/build_public_cabench_graph.py \
  --project-root "$REPO_ROOT" \
  --scenario-name "$SCENARIO_NAME" \
  --seed 42 \
  --delta-t 1.0 \
  --target-ip 10.0.0.100 \
  --python-bin "$PY_BIN"

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_fltrust_sensitivity

for cfg in \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e1.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e2.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e1.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e2.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e1.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e2.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h_fltrust_sensitivity" \
    --seeds "$SEEDS"
done

for prefix in \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e1 \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e2 \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e1 \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e2 \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e1 \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e2
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_fltrust_sensitivity_report.py \
  --method-specs "root48_e1=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e1_seed_stats.json,root48_e2=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root48_e2_seed_stats.json,root96_e1=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e1_seed_stats.json,root96_e2=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root96_e2_seed_stats.json,root192_e1=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e1_seed_stats.json,root192_e2=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_root192_e2_seed_stats.json" \
  --reference-specs "trust_aware=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_seed_stats.json,condfloor=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --title-prefix "Public-CaBench-ScenarioH_FLTrust-like_sensitivity" \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sensitivity_report.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_fltrust_like_sensitivity.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_fltrust_like_sensitivity.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_fltrust_like_sensitivity.png"

echo "[OK] Public Ca-Bench scenario_h FLTrust-like sensitivity reproduced."
