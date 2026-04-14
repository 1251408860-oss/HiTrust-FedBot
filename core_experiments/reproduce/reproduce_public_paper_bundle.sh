#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

VERIFY_FIRST="${VERIFY_FIRST:-1}"
INCLUDE_NSLKDD="${INCLUDE_NSLKDD:-1}"
INCLUDE_FLTRUST_SENSITIVITY="${INCLUDE_FLTRUST_SENSITIVITY:-1}"

cd "$REPO_ROOT"

if [[ "$VERIFY_FIRST" == "1" ]]; then
  bash "$REPO_ROOT/core_experiments/reproduce/verify_artifact_bundle.sh"
fi

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_cabench_validation.sh"
bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_cabench_scenario_h_validation.sh"

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_westermo_validation.sh"
bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_westermo_sign_flip_validation.sh"

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_litnet2020_udp_validation.sh"
bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_litnet2020_udp_sign_flip_validation.sh"

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_adaptive_full_matrix_validation.sh"
bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_cabench_scenario_h_attack_extension.sh"

if [[ "$INCLUDE_FLTRUST_SENSITIVITY" == "1" ]]; then
  bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_cabench_scenario_h_fltrust_sensitivity.sh"
fi

if [[ "$INCLUDE_NSLKDD" == "1" ]]; then
  bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_nslkdd_validation.sh"
fi

bash "$REPO_ROOT/core_experiments/reproduce/reproduce_public_server_deployment_runtime_package.sh"
bash "$REPO_ROOT/core_experiments/reproduce/reproduce_cross_dataset_frontier_summary.sh"

echo "[OK] Full public paper-facing reproduction completed."
