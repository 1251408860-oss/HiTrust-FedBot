#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"expected dict in {p}")
    return data


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def resolve_repo_local_path(path_value: str | Path, project_root: str | Path) -> Path:
    raw = str(path_value).strip()
    project = Path(project_root).resolve()
    if not raw:
        return project

    path = Path(raw)
    if path.exists():
        return path.resolve()

    if not path.is_absolute():
        candidate = (project / path).resolve()
        if candidate.exists():
            return candidate

    parts = list(path.parts)
    anchor_names = {
        project.name,
        "core_experiments",
        "data_hitrust",
        "paper_hitrust",
        "docs",
        "tests",
    }
    for idx, part in enumerate(parts):
        if part in anchor_names:
            if part == project.name:
                suffix = parts[idx + 1 :]
            else:
                suffix = parts[idx:]
            candidate = project.joinpath(*suffix).resolve()
            return candidate

    return path.resolve()


@dataclass
class SuitePaths:
    project_root: Path
    output_root: Path
    run_dir: Path


def resolve_suite_paths(project_root: str | Path, output_root: str | Path, run_name: str) -> SuitePaths:
    project = Path(project_root).resolve()
    output = ensure_dir(output_root).resolve()
    run_dir = ensure_dir(output / run_name)
    return SuitePaths(project_root=project, output_root=output, run_dir=run_dir)
