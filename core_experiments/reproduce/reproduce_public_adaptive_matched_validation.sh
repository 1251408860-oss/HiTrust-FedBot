#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222}"

REFERENCE_LABEL="temporal_rootguard_v2" ATTACK_NAME="adaptive_benign_mimic" SEEDS="$SEEDS" \
  "$SCRIPT_DIR/reproduce_public_cabench_scenario_h_adaptive_validation.sh"

SEEDS="$SEEDS" \
  "$SCRIPT_DIR/reproduce_public_cabench_scenario_e_adaptive_alie_like_validation.sh"

echo "[OK] Promoted matched adaptive public validation reproduced."
