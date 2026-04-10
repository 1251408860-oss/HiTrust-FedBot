#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222}"

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

"$PY_BIN" core_experiments/internal/build_public_westermo_graph.py \
  --project-root "$REPO_ROOT" \
  --seed 42 \
  --label-strategy nst \
  --train-size 10000 \
  --val-size 2500 \
  --test-size 5000 \
  --owner-bucket-size 128 \
  --knn-k 8

mkdir -p core_experiments/configs_hitrust/seed_sweeps_public_westermo_sign_flip

for cfg in \
  core_experiments/configs_hitrust/public_westermo_hierarchical_sage_sign_flip_frac0p4.json \
  core_experiments/configs_hitrust/public_westermo_hierarchical_sage_sign_flip_frac0p4_condfloor.json \
  core_experiments/configs_hitrust/public_westermo_hierarchical_sage_sign_flip_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_westermo_fltrust_like_sage_sign_flip_frac0p4.json \
  core_experiments/configs_hitrust/public_westermo_centered_clipping_sage_sign_flip_frac0p4_keepall.json \
  core_experiments/configs_hitrust/public_westermo_arc_mean_sage_sign_flip_frac0p4_keepall.json
do
  "$PY_BIN" core_experiments/internal/sweep_real_graph_seeds.py \
    --base-config "$cfg" \
    --runner "$REPO_ROOT/core_experiments/internal/run_real_fed_pilot.py" \
    --python-bin "$PY_BIN" \
    --project-root "$REPO_ROOT" \
    --output-dir "$REPO_ROOT/core_experiments/configs_hitrust/seed_sweeps_public_westermo_sign_flip" \
    --seeds "$SEEDS" \
    "${SWEEP_ARGS[@]}"
done

for prefix in \
  public_westermo_hierarchical_sage_sign_flip_frac0p4 \
  public_westermo_hierarchical_sage_sign_flip_frac0p4_condfloor \
  public_westermo_hierarchical_sage_sign_flip_frac0p4_keepall \
  public_westermo_fltrust_like_sage_sign_flip_frac0p4 \
  public_westermo_centered_clipping_sage_sign_flip_frac0p4_keepall \
  public_westermo_arc_mean_sage_sign_flip_frac0p4_keepall
do
  "$PY_BIN" core_experiments/internal/summarize_real_seed_sweep.py \
    --runs-root "$REPO_ROOT/paper_hitrust/runs" \
    --run-prefix "$prefix" \
    --output-file "$REPO_ROOT/paper_hitrust/tables/${prefix}_seed_stats.json"
done

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "trust_aware=$REPO_ROOT/paper_hitrust/tables/public_westermo_hierarchical_sage_sign_flip_frac0p4_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_westermo_fltrust_like_sage_sign_flip_frac0p4_seed_stats.json,hier_keepall=$REPO_ROOT/paper_hitrust/tables/public_westermo_hierarchical_sage_sign_flip_frac0p4_keepall_seed_stats.json,centered_clipping=$REPO_ROOT/paper_hitrust/tables/public_westermo_centered_clipping_sage_sign_flip_frac0p4_keepall_seed_stats.json,arc_mean=$REPO_ROOT/paper_hitrust/tables/public_westermo_arc_mean_sage_sign_flip_frac0p4_keepall_seed_stats.json" \
  --reference trust_aware \
  --title-prefix Public-Westermo_sign-flip0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_westermo_sign_flip_baseline_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_westermo_sign_flip_baseline_comparison.png"

"$PY_BIN" core_experiments/internal/build_method_comparison_report.py \
  --method-specs "condfloor=$REPO_ROOT/paper_hitrust/tables/public_westermo_hierarchical_sage_sign_flip_frac0p4_condfloor_seed_stats.json,fltrust_like=$REPO_ROOT/paper_hitrust/tables/public_westermo_fltrust_like_sage_sign_flip_frac0p4_seed_stats.json,static=$REPO_ROOT/paper_hitrust/tables/public_westermo_hierarchical_sage_sign_flip_frac0p4_seed_stats.json,keepall=$REPO_ROOT/paper_hitrust/tables/public_westermo_hierarchical_sage_sign_flip_frac0p4_keepall_seed_stats.json" \
  --reference condfloor \
  --title-prefix Public-Westermo_condfloor_sign-flip0p4 \
  --output-table "$REPO_ROOT/paper_hitrust/tables/public_westermo_sign_flip_condfloor_comparison.json" \
  --output-figure "$REPO_ROOT/paper_hitrust/figures/public_westermo_sign_flip_condfloor_comparison.png"

mkdir -p "$REPO_ROOT/paper_hitrust/figures_sage_main"
cp "$REPO_ROOT/paper_hitrust/figures/public_westermo_sign_flip_baseline_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_westermo_sign_flip_baseline_comparison.png"
cp "$REPO_ROOT/paper_hitrust/figures/public_westermo_sign_flip_condfloor_comparison.png" \
  "$REPO_ROOT/paper_hitrust/figures_sage_main/public_westermo_sign_flip_condfloor_comparison.png"

echo "[OK] Public Westermo sign-flip validation artifact reproduced."
