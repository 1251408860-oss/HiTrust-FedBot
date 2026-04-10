#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path

import torch

from graph_contract import (
    GRAPH_CONTRACT_VERSION,
    apply_graph_contract,
    graph_stats,
    repo_relative_path,
    validate_graph_contract,
)

CABENCH_RELEASE_ASSET_URL = (
    "https://github.com/1251408860-oss/Ca-Bench/releases/download/data-v1/real_collection.tar.gz"
)
CABENCH_RELEASE_SHA256_URL = (
    "https://github.com/1251408860-oss/Ca-Bench/releases/download/data-v1/real_collection.tar.gz.sha256"
)
CABENCH_DATASET_SOURCE = "github_release:1251408860-oss/Ca-Bench@data-v1"
CABENCH_UPSTREAM_COMMIT = "666af74e55f03c321557b2f2f83feb4f0950dd2d"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a same-task public Ca-Bench graph for HiTrust external validation"
    )
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--scenario-name", default="scenario_e_three_tier_high2")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--delta-t", type=float, default=1.0)
    p.add_argument("--target-ip", default="10.0.0.100")
    p.add_argument("--python-bin", default="")
    p.add_argument("--force-rebuild", action="store_true")
    p.add_argument("--skip-sha256-check", action="store_true")
    p.add_argument("--output-graph", default="")
    p.add_argument("--output-manifest", default="")
    p.add_argument("--output-summary", default="")
    p.add_argument("--refresh-builder-from-upstream", action="store_true")
    p.add_argument("--builder-commit", default=CABENCH_UPSTREAM_COMMIT)
    return p.parse_args()


def ensure_download(url: str, output_file: Path, *, retries: int = 4) -> None:
    if output_file.exists() and output_file.stat().st_size > 0:
        return
    output_file.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hitrust-fedbot-artifact"})
            with urllib.request.urlopen(req, timeout=900) as resp:
                output_file.write_bytes(resp.read())
            if output_file.stat().st_size <= 0:
                raise RuntimeError(f"downloaded empty file: {output_file}")
            return
        except Exception as exc:  # pragma: no cover - network path
            last_error = exc
            if output_file.exists():
                output_file.unlink()
            if attempt < retries:
                time.sleep(2 * attempt)
    assert last_error is not None
    raise last_error


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_expected_sha256(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        token = text.split()[0].strip().lower()
        if len(token) == 64 and all(ch in "0123456789abcdef" for ch in token):
            return token
    raise RuntimeError(f"failed to parse sha256 from {path}")


def ensure_release_archive(
    *,
    raw_root: Path,
    skip_sha256_check: bool,
) -> tuple[Path, str | None]:
    archive_file = raw_root / "real_collection.tar.gz"
    sha_file = raw_root / "real_collection.tar.gz.sha256"
    ensure_download(CABENCH_RELEASE_ASSET_URL, archive_file)
    if skip_sha256_check:
        return archive_file, None
    ensure_download(CABENCH_RELEASE_SHA256_URL, sha_file)
    expected = parse_expected_sha256(sha_file)
    observed = file_sha256(archive_file)
    if observed != expected:
        # One retry in case of interrupted partial download.
        if archive_file.exists():
            archive_file.unlink()
        ensure_download(CABENCH_RELEASE_ASSET_URL, archive_file)
        observed = file_sha256(archive_file)
    if observed != expected:
        raise RuntimeError(
            f"sha256 mismatch for {archive_file}: expected={expected}, observed={observed}"
        )
    return archive_file, expected


def safe_extract_member(tf: tarfile.TarFile, member: tarfile.TarInfo, target_root: Path) -> None:
    target_path = (target_root / member.name).resolve()
    root = target_root.resolve()
    if root not in target_path.parents and target_path != root:
        raise RuntimeError(f"blocked unsafe tar member path: {member.name}")
    tf.extract(member, path=target_root)


def extract_scenario_archive(
    *,
    archive_file: Path,
    extract_root: Path,
    scenario_name: str,
) -> tuple[Path, Path]:
    scenario_prefix = f"mininet_testbed/real_collection/{scenario_name}/"
    scenario_root = extract_root / "mininet_testbed" / "real_collection" / scenario_name
    pcap_file = scenario_root / "full_arena_v2.pcap"
    manifest_file = scenario_root / "arena_manifest_v2.json"
    if pcap_file.exists() and manifest_file.exists():
        return pcap_file, manifest_file

    extract_root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_file, "r:gz") as tf:
        members = [m for m in tf.getmembers() if m.name.startswith(scenario_prefix)]
        if not members:
            raise RuntimeError(
                f"scenario '{scenario_name}' not found in archive: {archive_file}"
            )
        for member in members:
            safe_extract_member(tf, member, extract_root)

    if not pcap_file.exists():
        raise RuntimeError(f"missing pcap after extraction: {pcap_file}")
    if not manifest_file.exists():
        raise RuntimeError(f"missing manifest after extraction: {manifest_file}")
    return pcap_file, manifest_file


def raw_github_url(builder_commit: str, suffix: str) -> str:
    return f"https://raw.githubusercontent.com/1251408860-oss/Ca-Bench/{builder_commit}/{suffix}"


def ensure_builder_tools(
    tools_root: Path,
    *,
    refresh_builder_from_upstream: bool,
    builder_commit: str,
) -> tuple[Path, Path]:
    build_graph_file = tools_root / "build_graph_v2.py"
    submission_common_file = tools_root / "internal" / "submission_common.py"
    if refresh_builder_from_upstream:
        if build_graph_file.exists():
            build_graph_file.unlink()
        if submission_common_file.exists():
            submission_common_file.unlink()
        ensure_download(raw_github_url(builder_commit, "core_experiments/build_graph_v2.py"), build_graph_file)
        ensure_download(
            raw_github_url(builder_commit, "core_experiments/internal/submission_common.py"),
            submission_common_file,
        )
    if not build_graph_file.exists() or not submission_common_file.exists():
        raise RuntimeError(
            "vendored Ca-Bench builder files are missing; restore "
            "data_hitrust/public_benchmarks/cabench_v1/tools or rerun with "
            "--refresh-builder-from-upstream"
        )
    return build_graph_file, submission_common_file


def enrich_graph_metadata(
    *,
    project_root: Path,
    graph_file: Path,
    scenario_name: str,
    scenario_manifest_file: Path,
    scenario_manifest: dict[str, object],
    build_graph_file: Path,
) -> dict[str, object]:
    graph = torch.load(graph_file, weights_only=False, map_location="cpu")
    apply_graph_contract(
        graph,
        project_root=project_root,
        dataset_name="Ca-Bench",
        dataset_variant=f"{scenario_name}_public_data_v1",
        dataset_source=CABENCH_DATASET_SOURCE,
        split_scheme="random_flow_split_from_public_scenario_capture",
        manifest_file=scenario_manifest_file,
        manifest_metadata=scenario_manifest,
        graph_source_kind="external_public_dataset",
        builder_reference=build_graph_file,
    )
    validate_graph_contract(graph)
    torch.save(graph, graph_file)
    return graph_stats(graph)


def resolve_python_bin(arg_value: str) -> str:
    if str(arg_value).strip():
        return str(arg_value).strip()
    for candidate in ("python", "python3"):
        if shutil.which(candidate):
            return candidate
    raise RuntimeError("Neither python nor python3 is available for builder invocation.")


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    data_root = project_root / "data_hitrust" / "public_benchmarks" / "cabench_v1"
    raw_root = data_root / "raw"
    extract_root = raw_root / "real_collection"
    tools_root = data_root / "tools"
    meta_root = data_root / "meta"
    graphs_root = data_root / "graphs"
    meta_root.mkdir(parents=True, exist_ok=True)
    graphs_root.mkdir(parents=True, exist_ok=True)

    output_graph = (
        Path(args.output_graph).resolve()
        if str(args.output_graph).strip()
        else graphs_root / f"cabench_{args.scenario_name}_public_graph.pt"
    )
    output_manifest = (
        Path(args.output_manifest).resolve()
        if str(args.output_manifest).strip()
        else meta_root / f"cabench_{args.scenario_name}_public_manifest.json"
    )
    output_summary = (
        Path(args.output_summary).resolve()
        if str(args.output_summary).strip()
        else meta_root / f"cabench_{args.scenario_name}_public_build_summary.json"
    )

    archive_file, expected_sha256 = ensure_release_archive(
        raw_root=raw_root,
        skip_sha256_check=bool(args.skip_sha256_check),
    )
    pcap_file, scenario_manifest_file = extract_scenario_archive(
        archive_file=archive_file,
        extract_root=extract_root,
        scenario_name=str(args.scenario_name),
    )
    build_graph_file, _ = ensure_builder_tools(
        tools_root,
        refresh_builder_from_upstream=bool(args.refresh_builder_from_upstream),
        builder_commit=str(args.builder_commit).strip() or CABENCH_UPSTREAM_COMMIT,
    )

    should_build = bool(args.force_rebuild) or (not output_graph.exists())
    python_bin = resolve_python_bin(str(args.python_bin))
    if should_build:
        cmd = [
            python_bin,
            str(build_graph_file),
            "--pcap-file",
            str(pcap_file),
            "--manifest-file",
            str(scenario_manifest_file),
            "--output-file",
            str(output_graph),
            "--target-ip",
            str(args.target_ip),
            "--delta-t",
            str(args.delta_t),
            "--seed",
            str(args.seed),
        ]
        subprocess.run(cmd, cwd=str(tools_root), check=True)

    scenario_manifest = json.loads(scenario_manifest_file.read_text(encoding="utf-8"))
    stats = enrich_graph_metadata(
        project_root=project_root,
        graph_file=output_graph,
        scenario_name=str(args.scenario_name),
        scenario_manifest_file=scenario_manifest_file,
        scenario_manifest=scenario_manifest,
        build_graph_file=build_graph_file,
    )

    artifact_manifest = {
        "dataset_name": "Ca-Bench",
        "dataset_variant": f"{args.scenario_name}_public_data_v1",
        "dataset_source": CABENCH_DATASET_SOURCE,
        "release_asset_url": CABENCH_RELEASE_ASSET_URL,
        "scenario_name": str(args.scenario_name),
        "scenario_manifest_file": repo_relative_path(scenario_manifest_file, project_root),
        "topology": dict(scenario_manifest.get("topology", {})),
        "run_config": dict(scenario_manifest.get("run_config", {})),
        "roles": dict(scenario_manifest.get("roles", {})),
        "ip_labels": dict(scenario_manifest.get("ip_labels", {})),
        "graph_file": repo_relative_path(output_graph, project_root),
        "builder_reference": repo_relative_path(build_graph_file, project_root),
        "upstream_builder_commit": str(args.builder_commit).strip() or CABENCH_UPSTREAM_COMMIT,
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
    }
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(artifact_manifest, indent=2), encoding="utf-8")

    summary = {
        "dataset_name": "Ca-Bench",
        "dataset_variant": f"{args.scenario_name}_public_data_v1",
        "scenario_name": str(args.scenario_name),
        "graph_file": repo_relative_path(output_graph, project_root),
        "manifest_file": repo_relative_path(output_manifest, project_root),
        "scenario_manifest_file": repo_relative_path(scenario_manifest_file, project_root),
        "release_archive": repo_relative_path(archive_file, project_root),
        "release_archive_sha256": expected_sha256 or "",
        "seed": int(args.seed),
        "delta_t": float(args.delta_t),
        "target_ip": str(args.target_ip),
        "builder_reference": repo_relative_path(build_graph_file, project_root),
        "upstream_builder_commit": str(args.builder_commit).strip() or CABENCH_UPSTREAM_COMMIT,
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
        "graph_stats": stats,
    }
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[OK] wrote {output_graph}")
    print(f"[OK] wrote {output_manifest}")
    print(f"[OK] wrote {output_summary}")


if __name__ == "__main__":
    main()
