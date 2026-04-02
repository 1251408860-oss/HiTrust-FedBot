#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111}"
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

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h

for cfg in \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_clean.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_clean_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_fedtruth_like_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_flshield_like_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_centered_clipping_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_rfa_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_mean_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_median_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_cabench_scenario_h_krum_sage_update_noise_frac0p4_keepall.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_cabench_scenario_h" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_cabench_scenario_h_hierarchical_sage_clean \
  public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4 \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4 \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor \
  public_cabench_scenario_h_hierarchical_sage_clean_keepall \
  public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4_keepall \
  public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall \
  public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4 \
  public_cabench_scenario_h_fedtruth_like_sage_update_noise_frac0p4 \
  public_cabench_scenario_h_flshield_like_sage_update_noise_frac0p4 \
  public_cabench_scenario_h_centered_clipping_sage_update_noise_frac0p4_keepall \
  public_cabench_scenario_h_rfa_sage_update_noise_frac0p4_keepall \
  public_cabench_scenario_h_mean_sage_update_noise_frac0p4_keepall \
  public_cabench_scenario_h_median_sage_update_noise_frac0p4_keepall \
  public_cabench_scenario_h_krum_sage_update_noise_frac0p4_keepall
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_no_trust_baseline_report.py \
  --trust-clean-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_clean_seed_stats.json" \
  --trust-sign-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4_seed_stats.json" \
  --trust-update-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_seed_stats.json" \
  --keepall-clean-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_clean_keepall_seed_stats.json" \
  --keepall-sign-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_sign_flip_frac0p4_keepall_seed_stats.json" \
  --keepall-update-file "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --scenario-label "Public-CaBench-ScenarioH" \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_trust_vs_keepall_seed_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "trust_aware=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_seed_stats.json,fedtruth_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fedtruth_like_sage_update_noise_frac0p4_seed_stats.json,flshield_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_flshield_like_sage_update_noise_frac0p4_seed_stats.json,hier_keepall=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json,centered_clipping=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_centered_clipping_sage_update_noise_frac0p4_keepall_seed_stats.json,rfa=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_rfa_sage_update_noise_frac0p4_keepall_seed_stats.json,mean=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_mean_sage_update_noise_frac0p4_keepall_seed_stats.json,median=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_median_sage_update_noise_frac0p4_keepall_seed_stats.json,krum=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_krum_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference trust_aware \
  --title-prefix Public-CaBench-ScenarioH_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_update_noise_baseline_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_update_noise_baseline_comparison.png"

cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_update_noise_baseline_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_update_noise_baseline_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_condfloor_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference condfloor \
  --title-prefix Public-CaBench-ScenarioH_condfloor_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_cabench_scenario_h_update_noise_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_update_noise_condfloor_comparison.png"

cp "$REPO_ROOT/paper_hitrust/figures/public_cabench_scenario_h_update_noise_condfloor_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_cabench_scenario_h_update_noise_condfloor_comparison.png"

echo "[OK] Public Ca-Bench scenario_h same-task external validation artifact reproduced."
