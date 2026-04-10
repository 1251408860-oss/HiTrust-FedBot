#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from torch_geometric.data import Data

from graph_contract import (
    GRAPH_CONTRACT_VERSION,
    apply_graph_contract,
    graph_stats,
    repo_relative_path,
    validate_graph_contract,
)

LITNET2020_DATASET_SOURCE = (
    "github_repo:Grigaliunas/electronics9050800@7b366c83d3c255d0507f706c7796af4f21a37bc8"
)
RAW_URL = (
    "https://raw.githubusercontent.com/Grigaliunas/electronics9050800/"
    "7b366c83d3c255d0507f706c7796af4f21a37bc8/dataset/UDP_FLOOD_FLOWS.zip"
)
RAW_ZIP_NAME = "UDP_FLOOD_FLOWS.zip"
RAW_CSV_NAME = "UDP_FLOOD_FLOWS.csv"
TOTAL_COLUMNS = 85


def parse_args():
    import argparse

    p = argparse.ArgumentParser(description="Build a public LITNET-2020 flow graph for HiTrust external validation")
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--output-graph", default="")
    p.add_argument("--output-manifest", default="")
    p.add_argument("--output-summary", default="")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-size", type=int, default=10000)
    p.add_argument("--val-size", type=int, default=2500)
    p.add_argument("--test-size", type=int, default=5000)
    p.add_argument("--owner-bucket-size", type=int, default=128)
    p.add_argument("--knn-k", type=int, default=8)
    return p.parse_args()


def ensure_download(url: str, output_file: Path) -> None:
    if output_file.exists():
        return
    output_file.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=900) as resp:
                output_file.write_bytes(resp.read())
            return
        except Exception as exc:  # pragma: no cover - network path
            last_error = exc
            if output_file.exists():
                output_file.unlink()
            if attempt < 3:
                time.sleep(2 * attempt)
    assert last_error is not None
    raise last_error


def ensure_extract(zip_path: Path, csv_root: Path) -> Path:
    csv_root.mkdir(parents=True, exist_ok=True)
    output_file = csv_root / RAW_CSV_NAME
    if output_file.exists():
        return output_file
    with zipfile.ZipFile(zip_path) as zf:
        members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not members:
            raise RuntimeError(f"zip file has no csv member: {zip_path}")
        output_file.write_bytes(zf.read(members[0]))
    return output_file


def build_column_names() -> list[str]:
    names = [f"feature_{idx:02d}" for idx in range(TOTAL_COLUMNS)]
    overrides = {
        0: "record_id",
        13: "duration_seconds",
        14: "source_ip",
        15: "destination_ip",
        16: "source_port",
        17: "destination_port",
        18: "protocol",
        80: "label_text_a",
        81: "label_text_b",
        82: "label_text_c",
        83: "attack_family",
        84: "binary_label",
    }
    for idx, name in overrides.items():
        names[idx] = name
    return names


DROP_COLUMNS = (
    ["record_id"]
    + [f"feature_{idx:02d}" for idx in range(1, 13)]
    + [f"feature_{idx:02d}" for idx in range(39, 57)]
    + ["source_ip", "destination_ip", "label_text_a", "label_text_b", "label_text_c", "attack_family"]
)
CATEGORICAL_COLUMNS = [
    "protocol",
    "feature_19",
    "feature_20",
    "feature_21",
    "feature_22",
    "feature_23",
    "feature_24",
]


def load_frame(csv_file: Path) -> pd.DataFrame:
    frame = pd.read_csv(csv_file, header=None, names=build_column_names(), quoting=csv.QUOTE_MINIMAL)
    frame["binary_label"] = pd.to_numeric(frame["binary_label"], errors="coerce").fillna(0).astype(int)
    frame["label"] = (frame["binary_label"] != 0).astype(int)
    frame["source_owner"] = frame["source_ip"].astype(str)
    frame["capture_view"] = "udp_flood"
    return frame


def stratified_sample(df: pd.DataFrame, size: int, *, seed: int) -> pd.DataFrame:
    if size <= 0 or size >= len(df):
        return df.copy().reset_index(drop=True)
    sampled, _ = train_test_split(
        df,
        train_size=int(size),
        random_state=int(seed),
        stratify=df["label"],
    )
    return sampled.reset_index(drop=True)


def split_train_val_test(
    df: pd.DataFrame,
    *,
    train_size: int,
    val_size: int,
    test_size: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    total = int(train_size) + int(val_size) + int(test_size)
    sampled = stratified_sample(df, size=total, seed=seed)
    train_df, holdout = train_test_split(
        sampled,
        train_size=int(train_size),
        random_state=int(seed),
        stratify=sampled["label"],
    )
    holdout = holdout.reset_index(drop=True)
    val_fraction = float(val_size) / max(float(val_size + test_size), 1.0)
    val_df, test_df = train_test_split(
        holdout,
        train_size=val_fraction,
        random_state=int(seed) + 17,
        stratify=holdout["label"],
    )
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def sanitize_token(text: str) -> str:
    out = "".join(ch if ch.isalnum() else "_" for ch in str(text).strip())
    out = out.strip("_")
    return out or "unknown"


def assign_owners(
    df: pd.DataFrame,
    *,
    owner_bucket_size: int,
    seed: int,
) -> tuple[list[str], dict[str, str], dict[str, int], np.ndarray]:
    rng = np.random.default_rng(seed)
    owner_by_row = np.empty(len(df), dtype=object)
    role_by_owner: dict[str, str] = {}
    label_by_owner: dict[str, int] = {}
    owner_names: list[str] = []
    bucket_size = max(int(owner_bucket_size), 1)
    grouped = df.groupby("source_owner", sort=True).indices
    for raw_owner, raw_indices in grouped.items():
        indices = np.asarray(list(raw_indices), dtype=np.int64)
        rng.shuffle(indices)
        safe_owner = sanitize_token(raw_owner)
        for bucket_id, start in enumerate(range(0, len(indices), bucket_size)):
            chunk = indices[start : start + bucket_size]
            owner_name = f"owner_{safe_owner}_b{bucket_id:03d}"
            owner_by_row[chunk] = owner_name
            owner_names.append(owner_name)
            role_by_owner[owner_name] = f"source_ip:{raw_owner}"
            label_by_owner[owner_name] = int(df.iloc[chunk]["label"].mean() >= 0.5)
    missing = np.where(pd.isna(owner_by_row))[0]
    if len(missing) > 0:
        raise RuntimeError(f"owner assignment failed for rows: {missing[:10].tolist()}")
    return owner_names, role_by_owner, label_by_owner, owner_by_row


def build_knn_edges(x_norm: np.ndarray, *, k: int) -> torch.Tensor:
    neighbors = min(max(int(k), 1), max(int(x_norm.shape[0]) - 1, 1))
    model = NearestNeighbors(n_neighbors=neighbors + 1, metric="euclidean", n_jobs=-1)
    model.fit(x_norm)
    indices = model.kneighbors(x_norm, return_distance=False)
    edges: set[tuple[int, int]] = set()
    for src, nbrs in enumerate(indices):
        for dst in nbrs[1:]:
            a = int(src)
            b = int(dst)
            if a == b:
                continue
            if a > b:
                a, b = b, a
            edges.add((a, b))
    rows = sorted(edges)
    return torch.tensor(rows, dtype=torch.long).t().contiguous()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    data_root = project_root / "data_hitrust" / "public_benchmarks" / "litnet2020"
    raw_root = data_root / "raw"
    csv_root = raw_root / "extracted_flows"
    graph_root = data_root / "graphs"
    meta_root = data_root / "meta"
    graph_root.mkdir(parents=True, exist_ok=True)
    meta_root.mkdir(parents=True, exist_ok=True)

    output_graph = (
        Path(args.output_graph).resolve()
        if str(args.output_graph).strip()
        else graph_root / "litnet2020_udp_flood_public_graph.pt"
    )
    output_manifest = (
        Path(args.output_manifest).resolve()
        if str(args.output_manifest).strip()
        else meta_root / "litnet2020_udp_flood_public_manifest.json"
    )
    output_summary = (
        Path(args.output_summary).resolve()
        if str(args.output_summary).strip()
        else meta_root / "litnet2020_udp_flood_public_build_summary.json"
    )

    zip_path = raw_root / RAW_ZIP_NAME
    ensure_download(RAW_URL, zip_path)
    csv_file = ensure_extract(zip_path, csv_root)

    combined_raw = load_frame(csv_file)
    train_df, val_df, test_df = split_train_val_test(
        combined_raw,
        train_size=int(args.train_size),
        val_size=int(args.val_size),
        test_size=int(args.test_size),
        seed=int(args.seed),
    )
    train_df["split"] = "train"
    val_df["split"] = "val"
    test_df["split"] = "test"
    combined = pd.concat([train_df, val_df, test_df], axis=0, ignore_index=True)

    owner_names, role_by_owner, label_by_owner, owner_by_row = assign_owners(
        combined,
        owner_bucket_size=int(args.owner_bucket_size),
        seed=int(args.seed),
    )
    owner_list = sorted(set(owner_names))
    owner_index = {name: idx for idx, name in enumerate(owner_list)}
    ip_idx = np.asarray([owner_index[str(name)] for name in owner_by_row], dtype=np.int64)

    feature_df = combined.drop(
        columns=[col for col in DROP_COLUMNS if col in combined.columns] + ["split", "label", "binary_label", "source_owner"]
    ).copy()
    categorical_columns = [col for col in CATEGORICAL_COLUMNS if col in feature_df.columns]
    numeric_columns = [col for col in feature_df.columns if col not in categorical_columns]
    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0.0).astype(np.float32)
    for column in categorical_columns:
        feature_df[column] = feature_df[column].astype(str)
    feature_df = pd.get_dummies(feature_df, columns=categorical_columns, dtype=np.float32)
    feature_df = feature_df.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    feature_names = [str(col) for col in feature_df.columns]

    train_mask_np = combined["split"].to_numpy() == "train"
    val_mask_np = combined["split"].to_numpy() == "val"
    test_mask_np = combined["split"].to_numpy() == "test"

    x_raw = feature_df.to_numpy(dtype=np.float32)
    scaler = StandardScaler()
    scaler.fit(x_raw[train_mask_np])
    x_norm = scaler.transform(x_raw).astype(np.float32)

    edge_index = build_knn_edges(x_norm, k=int(args.knn_k))
    edge_index_undirected = torch.cat([edge_index, edge_index.flip(0)], dim=1)
    edge_type = torch.zeros(edge_index.shape[1], dtype=torch.long)
    edge_type_undirected = torch.zeros(edge_index_undirected.shape[1], dtype=torch.long)

    dataset_variant = "udp_flood_sampled_public_graph"
    split_scheme = "stratified_random_train_val_test_from_litnet_udp_flood_flow_csv"
    manifest = {
        "dataset_name": "LITNET-2020 Network Flow Dataset",
        "dataset_variant": dataset_variant,
        "dataset_source": LITNET2020_DATASET_SOURCE,
        "split_scheme": split_scheme,
        "seed": int(args.seed),
        "source_archive": RAW_ZIP_NAME,
        "topology": {
            "type": "public_benchmark",
            "source": "litnet2020_udp_flood_flows",
        },
        "run_config": {
            "load_profile": "public_benchmark",
            "bot_type_mode": "network_intrusion_udp_flood",
        },
        "roles": {name: role_by_owner[name] for name in owner_list},
        "ip_labels": {name: int(label_by_owner[name]) for name in owner_list},
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
    }
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    data = Data(
        x=torch.from_numpy(x_raw),
        x_norm=torch.from_numpy(x_norm),
        edge_index=edge_index,
        edge_type=edge_type,
        edge_index_undirected=edge_index_undirected,
        edge_type_undirected=edge_type_undirected,
        y=torch.from_numpy(combined["label"].to_numpy(dtype=np.int64)),
        window_idx=torch.arange(len(combined), dtype=torch.long),
        ip_idx=torch.from_numpy(ip_idx),
        train_mask=torch.from_numpy(train_mask_np),
        val_mask=torch.from_numpy(val_mask_np),
        test_mask=torch.from_numpy(test_mask_np),
        temporal_train_mask=torch.from_numpy(train_mask_np),
        temporal_test_mask=torch.from_numpy(test_mask_np),
        feat_mean=torch.from_numpy(scaler.mean_.astype(np.float32)),
        feat_std=torch.from_numpy(np.maximum(scaler.scale_, 1e-6).astype(np.float32)),
        source_ips=owner_list,
        target_ip="public_litnet2020",
        delta_t=1.0,
        n_windows=int(len(combined)),
        feature_names=feature_names,
        feature_index={name: idx for idx, name in enumerate(feature_names)},
        label_source="litnet2020_binary_udp_flood",
    )
    apply_graph_contract(
        data,
        project_root=project_root,
        dataset_name="LITNET-2020 Network Flow Dataset",
        dataset_variant=dataset_variant,
        dataset_source=LITNET2020_DATASET_SOURCE,
        split_scheme=split_scheme,
        manifest_file=output_manifest,
        manifest_metadata=manifest,
        graph_source_kind="external_public_dataset",
    )
    validate_graph_contract(data)
    output_graph.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, output_graph)

    summary = {
        "dataset_name": "LITNET-2020 Network Flow Dataset",
        "dataset_variant": dataset_variant,
        "dataset_source": LITNET2020_DATASET_SOURCE,
        "output_graph": repo_relative_path(output_graph, project_root),
        "manifest_file": repo_relative_path(output_manifest, project_root),
        "seed": int(args.seed),
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
        "rows": int(len(combined)),
        "num_features": int(len(feature_names)),
        "num_edges": int(edge_index.shape[1]),
        "num_owners": int(len(owner_list)),
        "graph_stats": graph_stats(data),
        "split_counts": {
            "train": int(train_mask_np.sum()),
            "val": int(val_mask_np.sum()),
            "test": int(test_mask_np.sum()),
        },
        "label_counts": {
            "normal": int((combined["label"] == 0).sum()),
            "attack": int((combined["label"] == 1).sum()),
        },
        "attack_rate": float(combined["label"].mean()),
        "owner_bucket_size": int(args.owner_bucket_size),
        "knn_k": int(args.knn_k),
        "protocol_counts": {str(k): int(v) for k, v in combined["protocol"].value_counts().to_dict().items()},
        "source_archive": RAW_ZIP_NAME,
    }
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_graph}")
    print(f"[OK] wrote {output_manifest}")
    print(f"[OK] wrote {output_summary}")


if __name__ == "__main__":
    main()
