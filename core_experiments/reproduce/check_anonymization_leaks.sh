#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ALLOWLIST_FILE="${ALLOWLIST_FILE:-$REPO_ROOT/docs/anonymization_allowlist.txt}"

cd "$REPO_ROOT"

python3 - "$REPO_ROOT" "$ALLOWLIST_FILE" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
allowlist_file = Path(sys.argv[2]).resolve()

scan_roots = [
    repo_root / "paper_hitrust",
    repo_root / "docs",
    repo_root / "README.md",
    repo_root / "core_experiments" / "README.md",
]

exclude_paths = {
    "paper_hitrust/runs",
    "paper_hitrust/tables",
    "paper_hitrust/figures",
    "paper_hitrust/figures_sage_main",
    "paper_hitrust/logs",
    "docs/reviewer_bundle_sha256_20260326.txt",
    "docs/CYBERSECURITY_COVER_LETTER_20260324.md",
    "docs/CYBERSECURITY_TITLE_PAGE_TEMPLATE_20260324.md",
    "docs/EAAI_TITLE_PAGE_TEMPLATE_20260327.md",
}

text_suffixes = {".md", ".txt", ".yml", ".yaml", ".json", ".sh", ".py"}
patterns = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"orcid\.org/[0-9Xx-]{15,}", re.IGNORECASE),
    re.compile(
        r"^\s*(Author|Authors|作者|通讯作者|Corresponding\s+author|Affiliation|Affiliations|单位|机构)\s*[:：]",
        re.IGNORECASE,
    ),
]

allow_rules: list[re.Pattern[str]] = []
if allowlist_file.exists():
    for raw in allowlist_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        allow_rules.append(re.compile(line))


def is_excluded(path: Path) -> bool:
    rel = path.relative_to(repo_root).as_posix()
    for item in exclude_paths:
        if rel == item or rel.startswith(f"{item}/"):
            return True
    return False


def iter_files(root: Path):
    if root.is_file():
        if not is_excluded(root) and root.suffix.lower() in text_suffixes:
            yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        if path.suffix.lower() not in text_suffixes:
            continue
        yield path


hits: list[str] = []
for root in scan_roots:
    if not root.exists():
        continue
    for path in iter_files(root):
        rel = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            if not any(p.search(line) for p in patterns):
                continue
            rec = f"{rel}:{idx}:{line.strip()}"
            if any(rule.search(rec) for rule in allow_rules):
                continue
            hits.append(rec)

if hits:
    print("[FAIL] Potential anonymization leaks found:")
    for row in hits:
        print(row)
    raise SystemExit(1)

print("[OK] No anonymization leaks detected in the scanned submission-facing files.")
PY
