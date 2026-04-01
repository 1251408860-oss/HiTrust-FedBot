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
  "docs/anonymization_allowlist.txt"
  "paper_hitrust/artifact_manifest_20260324.json"
)

append_find() {
  while IFS= read -r path; do
    paths+=("$path")
  done < <(find "$@" | sort)
}

append_find core_experiments -maxdepth 1 -type f -name '*.md'
append_find core_experiments/reproduce -type f ! -path '*/__pycache__/*' ! -name '*.pyc'
append_find core_experiments/internal -type f ! -path '*/__pycache__/*' ! -name '*.pyc'
append_find core_experiments/configs_hitrust -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -path 'core_experiments/configs_hitrust/seed_sweeps_*/*' ! -path 'core_experiments/configs_hitrust/sweeps/*/*'
append_find data_hitrust -maxdepth 1 -type f -name '*.md'
append_find data_hitrust/bootstrap -type f ! -path '*/__pycache__/*' ! -name '*.pyc'
append_find data_hitrust/bootstrap_graphs/graphs -type f -name '*.pt'
append_find data_hitrust/public_benchmarks/cabench_v1/tools -type f ! -path '*/__pycache__/*' ! -name '*.pyc'
append_find data_hitrust/public_benchmarks/nsl_kdd/raw -type f
append_find paper_hitrust -maxdepth 1 -type f -name '*.md'
append_find docs -maxdepth 1 -type f -name '*.md'

paths+=(
  "data_hitrust/public_benchmarks/cabench_v1/raw/real_collection.tar.gz"
  "data_hitrust/public_benchmarks/cabench_v1/raw/real_collection.tar.gz.sha256"
)

mapfile -t unique_paths < <(printf '%s\n' "${paths[@]}" | LC_ALL=C sort -u)

for path in "${unique_paths[@]}"; do
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
echo "[INFO] SHA-256 scope: static release files only"
echo "[INFO] Excluded mutable rerun outputs: data_hitrust/public_benchmarks/*/{graphs,meta}, core_experiments/configs_hitrust/seed_sweeps_*, core_experiments/configs_hitrust/sweeps/*, paper_hitrust/{runs,tables,figures}"
