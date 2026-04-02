#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111}"

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

"$PY_BIN" core_experiments/internal/build_public_nsl_kdd_graph.py \
  --project-root "$REPO_ROOT" \
  --seed 42 \
  --train-size 8000 \
  --val-size 2000 \
  --test-size 4000 \
  --owner-bucket-size 128 \
  --knn-k 8

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_nslkdd

for cfg in \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_clean.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_sign_flip_frac0p4.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_clean_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_sign_flip_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_fltrust_like_sage_update_noise_frac0p4.json \
  core_experiments/configs_hitrust/public_nslkdd_centered_clipping_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_rfa_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_mean_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_median_sage_update_noise_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_nslkdd_krum_sage_update_noise_frac0p4_keepall.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_nslkdd" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_nslkdd_hierarchical_sage_clean \
  public_nslkdd_hierarchical_sage_sign_flip_frac0p4 \
  public_nslkdd_hierarchical_sage_update_noise_frac0p4 \
  public_nslkdd_hierarchical_sage_clean_keepall \
  public_nslkdd_hierarchical_sage_sign_flip_frac0p4_keepall \
  public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall \
  public_nslkdd_fltrust_like_sage_update_noise_frac0p4 \
  public_nslkdd_centered_clipping_sage_update_noise_frac0p4_keepall \
  public_nslkdd_rfa_sage_update_noise_frac0p4_keepall \
  public_nslkdd_mean_sage_update_noise_frac0p4_keepall \
  public_nslkdd_median_sage_update_noise_frac0p4_keepall \
  public_nslkdd_krum_sage_update_noise_frac0p4_keepall
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_no_trust_baseline_report.py \
  --trust-clean-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_clean_seed_stats.json" \
  --trust-sign-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_sign_flip_frac0p4_seed_stats.json" \
  --trust-update-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_seed_stats.json" \
  --keepall-clean-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_clean_keepall_seed_stats.json" \
  --keepall-sign-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_sign_flip_frac0p4_keepall_seed_stats.json" \
  --keepall-update-file "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --scenario-label "Public-NSL-KDD" \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_trust_vs_keepall_seed_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_nslkdd_trust_vs_keepall_seed_comparison.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_nslkdd_trust_vs_keepall_seed_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_nslkdd_trust_vs_keepall_seed_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "trust_aware=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_fltrust_like_sage_update_noise_frac0p4_seed_stats.json,hier_keepall=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_hierarchical_sage_update_noise_frac0p4_keepall_seed_stats.json,centered_clipping=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_centered_clipping_sage_update_noise_frac0p4_keepall_seed_stats.json,rfa=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_rfa_sage_update_noise_frac0p4_keepall_seed_stats.json,mean=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_mean_sage_update_noise_frac0p4_keepall_seed_stats.json,median=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_median_sage_update_noise_frac0p4_keepall_seed_stats.json,krum=$REPO_ROOT/paper_hitrust/tables/public_nslkdd_krum_sage_update_noise_frac0p4_keepall_seed_stats.json" \
  --reference trust_aware \
  --title-prefix Public-NSL-KDD_update-noise0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_nslkdd_update_noise_baseline_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_nslkdd_update_noise_baseline_comparison.png"

cp "$REPO_ROOT/paper_hitrust/figures/public_nslkdd_update_noise_baseline_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_nslkdd_update_noise_baseline_comparison.png"

echo "[OK] Public NSL-KDD external validation artifact reproduced."
