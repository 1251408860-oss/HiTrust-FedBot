#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DATE_TAG="${1:-20260326}"
DIST_DIR="$REPO_ROOT/dist"
BUNDLE_NAME="HiTrust-FedBot_artifact_${DATE_TAG}"
ARCHIVE_PATH="$DIST_DIR/${BUNDLE_NAME}.tar.gz"
CHECKSUM_PATH="$DIST_DIR/${BUNDLE_NAME}.sha256"

cd "$REPO_ROOT"

bash core_experiments/reproduce/verify_artifact_bundle.sh

mkdir -p "$DIST_DIR"
rm -f "$ARCHIVE_PATH" "$CHECKSUM_PATH"

tar \
  --exclude-vcs \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.mypy_cache' \
  --exclude='dist' \
  --exclude='paper_hitrust/logs' \
  --exclude='paper_hitrust/figures_sage_main' \
  --exclude='data_hitrust/bootstrap_graphs/logs' \
  -czf "$ARCHIVE_PATH" \
  README.md \
  RELEASE_CHECKLIST.md \
  environment.yml \
  requirements_artifact.txt \
  docs \
  core_experiments \
  data_hitrust \
  paper_hitrust \
  tests \
  .gitignore

(cd "$DIST_DIR" && sha256sum "${BUNDLE_NAME}.tar.gz" > "$(basename "$CHECKSUM_PATH")")

echo "[OK] Created $ARCHIVE_PATH"
echo "[OK] Created $CHECKSUM_PATH"
echo "[INFO] Upload both files to a GitHub Release to match the Ca-Bench-style reviewer delivery pattern."
