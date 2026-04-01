#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ATTACK_NAME="adaptive_alie_like" REFERENCE_LABEL="temporal_rootguard_v2" \
  "$SCRIPT_DIR/reproduce_public_cabench_scenario_e_adaptive_validation.sh"
