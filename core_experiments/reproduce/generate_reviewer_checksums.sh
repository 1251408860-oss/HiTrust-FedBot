#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_FILE="${1:-docs/reviewer_bundle_sha256_20260326.txt}"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "$TMP_FILE"
}

trap cleanup EXIT

cd "$REPO_ROOT"

paths=(
  "README.md"
  "RELEASE_CHECKLIST.md"
  "environment.yml"
  "requirements_artifact.txt"
  "core_experiments/README.md"
  "data_hitrust/README.md"
  "paper_hitrust/README.md"
  "docs/ARTIFACT_RELEASE_20260324.md"
  "docs/DATA_AVAILABILITY_20260324.md"
  "docs/ARTIFACT_STATUS_20260326.md"
  "paper_hitrust/artifact_manifest_20260324.json"
)

append_files() {
  local root="$1"
  while IFS= read -r path; do
    paths+=("$path")
  done < <(find "$root" -type f | sort)
}

append_files "core_experiments/reproduce"
append_files "data_hitrust/bootstrap"
append_files "data_hitrust/bootstrap_graphs/graphs"
append_files "data_hitrust/public_benchmarks"
append_files "paper_hitrust/tables"
append_files "paper_hitrust/figures"
append_files "paper_hitrust/runs"

for path in "${paths[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "[ERROR] Missing expected file: $path" >&2
    exit 1
  fi
  sha256sum "$path" >> "$TMP_FILE"
done

mkdir -p "$(dirname "$OUT_FILE")"
mv "$TMP_FILE" "$OUT_FILE"
trap - EXIT

echo "[OK] Wrote checksum manifest to $OUT_FILE"
