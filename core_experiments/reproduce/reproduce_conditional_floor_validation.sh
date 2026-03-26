#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY_BIN="${PY_BIN:-/home/user/miniconda3/envs/DL/bin/python}"
MAIN_SEEDS="${MAIN_SEEDS:-11,22,33,44,55}"
PUBLIC_SEEDS="${PUBLIC_SEEDS:-11,22,33}"

cd "$REPO_ROOT"

if [ ! -f "$REPO_ROOT/data_hitrust/public_benchmarks/nsl_kdd/graphs/nsl_kdd_public_graph.pt" ]; then
  "$PY_BIN" core_experiments/internal/build_public_nsl_kdd_graph.py \
    --project-root "$REPO_ROOT" \
    --seed 42 \
    --train-size 8000 \
    --val-size 2000 \
    --test-size 4000 \
    --owner-bucket-size 128 \
    --knn-k 8
fi

mkdir -p \
  core_experiments/configs_hitrust/sweeps/scenario_h_condfloor_submission \
  core_experiments/configs_hitrust/sweeps/scenario_e_condfloor_submission \
  core_experiments/configs_hitrust/sweeps/public_nslkdd_condfloor_submission

for cfg in \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_clean.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_clean_condfloor.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4_condfloor.json \
  core_experiments/configs_hitrust/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_condfloor.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/sweeps/scenario_h_condfloor_submission" \
    --seeds "$MAIN_SEEDS"
done

for cfg in \
  core_experiments/configs_hitrust/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_condfloor.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/sweeps/scenario_e_condfloor_submission" \
    --seeds "$MAIN_SEEDS"
done

for cfg in \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_update_noise_frac0p4_condfloor.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/sweeps/public_nslkdd_condfloor_submission" \
    --seeds "$PUBLIC_SEEDS"
done

for prefix in \
  real_graph_pilot_h_scenario_h_sage_clean \
  real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4 \
  real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4 \
  real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_keepall \
  real_graph_pilot_h_scenario_h_sage_clean_condfloor \
  real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4_condfloor \
  real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_condfloor \
  real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4 \
  real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_keepall \
  real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_condfloor \
  public_nslkdd_hierarchical_sage_update_noise_frac0p4 \
  public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall \
  public_nslkdd_hierarchical_sage_update_noise_frac0p4_condfloor
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_clean_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_clean_seed_stats.json" \
  --reference condfloor \
  --title-prefix Scenario-H_clean \
  --output-table "$REPO_ROOT/paper_hitrust/tables/scenario_h_clean_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/scenario_h_clean_condfloor_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_sign_flip_frac0p4_seed_stats.json" \
  --reference condfloor \
  --title-prefix Scenario-H_sign-flip0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/scenario_h_sign_flip_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/scenario_h_sign_flip_condfloor_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_h_scenario_h_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference condfloor \
  --title-prefix Scenario-H_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/scenario_h_update_noise_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/scenario_h_update_noise_condfloor_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/real_graph_pilot_scenario_e_three_tier_high2_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference condfloor \
  --title-prefix Scenario-E_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/scenario_e_update_noise_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/scenario_e_update_noise_condfloor_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_condfloor_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference condfloor \
  --title-prefix Public-NSLKDD_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_update_noise_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_nslkdd_update_noise_condfloor_comparison.png"

for fig in \
  scenario_h_clean_condfloor_comparison.png \
  scenario_h_sign_flip_condfloor_comparison.png \
  scenario_h_update_noise_condfloor_comparison.png \
  scenario_e_update_noise_condfloor_comparison.png \
  public_nslkdd_update_noise_condfloor_comparison.png
do
  cp "$REPO_ROOT/paper_hitrust/figures/$fig" "$REPO_ROOT/paper_hitrust/figures_sage_main/$fig"
done

echo "[OK] Conditional-floor hardening validation reproduced."
