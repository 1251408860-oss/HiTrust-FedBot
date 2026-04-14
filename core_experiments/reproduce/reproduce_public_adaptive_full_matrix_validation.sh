#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SEEDS="${SEEDS:-11,22,33,44,55,66,77,88,99,111,122,133,144,155,166,177,188,199,211,222}"

SEEDS="$SEEDS" \
  "$SCRIPT_DIR/reproduce_public_adaptive_matched_validation.sh"

ATTACK_NAME="adaptive_alie_like" REFERENCE_LABEL="temporal_rootguard_v2" SEEDS="$SEEDS" \
  "$SCRIPT_DIR/reproduce_public_cabench_scenario_h_adaptive_validation.sh"

ATTACK_NAME="adaptive_benign_mimic" REFERENCE_LABEL="temporal_rootguard_v2" SEEDS="$SEEDS" \
  "$SCRIPT_DIR/reproduce_public_cabench_scenario_e_adaptive_validation.sh"

echo "[OK] Public adaptive full 2x2 matched validation reproduced."
