#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CHECKSUM_FILE="docs/reviewer_bundle_sha256_20260326.txt"
missing=0

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

required_files=(
  "README.md"
  "RELEASE_CHECKLIST.md"
  "environment.yml"
  "requirements_artifact.txt"
  "core_experiments/README.md"
  "core_experiments/reproduce/reproduce_public_nslkdd_validation.sh"
  "core_experiments/reproduce/reproduce_conditional_floor_validation.sh"
  "core_experiments/reproduce/reproduce_reviewer_bundle.sh"
  "core_experiments/reproduce/generate_reviewer_checksums.sh"
  "core_experiments/reproduce/package_reviewer_release.sh"
  "docs/ARTIFACT_RELEASE_20260324.md"
  "docs/DATA_AVAILABILITY_20260324.md"
  "docs/ARTIFACT_STATUS_20260326.md"
  "docs/reviewer_bundle_sha256_20260326.txt"
  "data_hitrust/README.md"
  "paper_hitrust/README.md"
  "paper_hitrust/artifact_manifest_20260324.json"
)

required_dirs=(
  "data_hitrust/bootstrap_graphs/graphs"
  "data_hitrust/public_benchmarks/nsl_kdd/graphs"
  "paper_hitrust/tables"
  "paper_hitrust/figures"
  "paper_hitrust/runs"
)

for path in "${required_files[@]}"; do
  if [[ -f "$path" ]]; then
    echo "[OK] file: $path"
  else
    echo "[MISS] file: $path" >&2
    missing=1
  fi
done

for path in "${required_dirs[@]}"; do
  if [[ -d "$path" ]]; then
    echo "[OK] dir:  $path"
  else
    echo "[MISS] dir:  $path" >&2
    missing=1
  fi
done

for path in core_experiments/reproduce/*.sh; do
  bash -n "$path"
done
echo "[OK] shell syntax: core_experiments/reproduce/*.sh"

"$PY_BIN" - <<'PY'
import json
import sys
from pathlib import Path

root = Path(".")
manifest_path = root / "paper_hitrust" / "artifact_manifest_20260324.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
missing = []

def walk(obj):
    if isinstance(obj, dict):
        for value in obj.values():
            walk(value)
    elif isinstance(obj, list):
        for value in obj:
            walk(value)
    elif isinstance(obj, str) and ("/" in obj or obj.endswith((".json", ".png", ".pt", ".sh", ".md", ".yml", ".txt"))):
        if not (root / obj).exists():
            missing.append(obj)

walk(manifest)

if missing:
    print("[MISS] artifact manifest references:")
    for item in missing:
        print(item)
    sys.exit(1)

print("[OK] artifact manifest references resolved")
PY

if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c "$CHECKSUM_FILE"
else
  echo "[WARN] sha256sum is unavailable; skipped checksum verification"
fi

graph_count="$(find data_hitrust/bootstrap_graphs/graphs -maxdepth 1 -type f -name '*.pt' | wc -l | tr -d ' ')"
public_graph_count="$(find data_hitrust/public_benchmarks/nsl_kdd/graphs -maxdepth 1 -type f -name '*.pt' | wc -l | tr -d ' ')"
table_count="$(find paper_hitrust/tables -type f | wc -l | tr -d ' ')"
figure_count="$(find paper_hitrust/figures -type f | wc -l | tr -d ' ')"
run_count="$(find paper_hitrust/runs -type f | wc -l | tr -d ' ')"

echo "[INFO] bootstrap graph files: $graph_count"
echo "[INFO] public graph files:    $public_graph_count"
echo "[INFO] paper tables:          $table_count"
echo "[INFO] paper figures:         $figure_count"
echo "[INFO] paper run files:       $run_count"

if [[ "$graph_count" -lt 5 || "$public_graph_count" -lt 1 || "$table_count" -lt 1 || "$figure_count" -lt 1 || "$run_count" -lt 1 ]]; then
  echo "[FAIL] artifact bundle appears incomplete" >&2
  exit 1
fi

if [[ "$missing" -ne 0 ]]; then
  echo "[FAIL] required release files are missing" >&2
  exit 1
fi

echo "[OK] Reviewer artifact bundle verification completed."
