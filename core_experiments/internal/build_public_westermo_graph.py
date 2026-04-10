#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

WESTERMO_DATASET_SOURCE = "github_repo:westermo/network-traffic-dataset@ba85578e19169c2380d2789266f6c42cd0627e00"
RAW_URLS = {
    "output_bottom.zip": "https://raw.githubusercontent.com/westermo/network-traffic-dataset/main/data/reduced/flows/output_bottom.zip",
    "output_left.zip": "https://raw.githubusercontent.com/westermo/network-traffic-dataset/main/data/reduced/flows/output_left.zip",
    "output_right.zip": "https://raw.githubusercontent.com/westermo/network-traffic-dataset/main/data/reduced/flows/output_right.zip",
}
LABEL_COLUMNS = {
    "nst": ("NST_B_Label", "NST_M_Label", "nst_binary"),
    "it": ("IT_B_Label", "IT_M_Label", "it_binary"),
}
DROP_COLUMNS = [
    "sAddress",
    "rAddress",
    "sMACs",
    "rMACs",
    "sIPs",
    "rIPs",
    "startDate",
    "endDate",
    "start",
    "end",
    "startOffset",
    "endOffset",
    "IT_B_Label",
    "IT_M_Label",
    "NST_B_Label",
    "NST_M_Label",
]
CATEGORICAL_COLUMNS = ["protocol", "capture_view"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a public Westermo flow graph for HiTrust external validation")
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--output-graph", default="")
    p.add_argument("--output-manifest", default="")
    p.add_argument("--output-summary", default="")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-size", type=int, default=10000)
    p.add_argument("--val-size", type=int, default=2500)
    p.add_argument("--test-size", type=int, default=5000)
    p.add_argument("--label-strategy", choices=sorted(LABEL_COLUMNS.keys()), default="nst")
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
            with urllib.request.urlopen(url, timeout=600) as resp:
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
    with zipfile.ZipFile(zip_path) as zf:
        members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not members:
            raise RuntimeError(f"zip file has no csv member: {zip_path}")
        member = members[0]
        output_file = csv_root / Path(member).name
        if output_file.exists():
            return output_file
        output_file.write_bytes(zf.read(member))
        return output_file


def load_frames(csv_files: list[Path], *, label_column: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        frame = pd.read_csv(csv_file)
        capture_name = csv_file.stem.replace("output_", "")
        frame["capture_view"] = capture_name
        frame["label"] = pd.to_numeric(frame[label_column], errors="coerce").fillna(0).astype(int)
        frame["source_owner"] = frame["sIPs"].astype(str)
        frames.append(frame)
    combined = pd.concat(frames, axis=0, ignore_index=True)
    combined["label"] = (combined["label"] != 0).astype(int)
    return combined


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


def assign_owners(df: pd.DataFrame, *, owner_bucket_size: int, seed: int) -> tuple[list[str], dict[str, str], dict[str, int], np.ndarray]:
    rng = np.random.default_rng(seed)
    owner_by_row = np.empty(len(df), dtype=object)
    role_by_owner: dict[str, str] = {}
    label_by_owner: dict[str, int] = {}
    owner_names: list[str] = []

    grouped = df.groupby("source_owner", sort=True).indices
    bucket_size = max(int(owner_bucket_size), 1)
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
    data_root = project_root / "data_hitrust" / "public_benchmarks" / "westermo"
    raw_root = data_root / "raw"
    csv_root = raw_root / "extracted_flows"
    graph_root = data_root / "graphs"
    meta_root = data_root / "meta"
    graph_root.mkdir(parents=True, exist_ok=True)
    meta_root.mkdir(parents=True, exist_ok=True)

    label_column, label_text_column, label_source = LABEL_COLUMNS[str(args.label_strategy)]
    variant_token = str(args.label_strategy).lower()
    output_graph = (
        Path(args.output_graph).resolve()
        if str(args.output_graph).strip()
        else graph_root / f"westermo_{variant_token}_public_graph.pt"
    )
    output_manifest = (
        Path(args.output_manifest).resolve()
        if str(args.output_manifest).strip()
        else meta_root / f"westermo_{variant_token}_public_manifest.json"
    )
    output_summary = (
        Path(args.output_summary).resolve()
        if str(args.output_summary).strip()
        else meta_root / f"westermo_{variant_token}_public_build_summary.json"
    )

    csv_files: list[Path] = []
    for name, url in RAW_URLS.items():
        zip_path = raw_root / name
        ensure_download(url, zip_path)
        csv_files.append(ensure_extract(zip_path, csv_root))

    combined_raw = load_frames(csv_files, label_column=label_column)
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

    feature_df = combined.drop(columns=[col for col in DROP_COLUMNS if col in combined.columns] + ["split", "label", "source_owner"]).copy()
    categorical_columns = [col for col in CATEGORICAL_COLUMNS if col in feature_df.columns]
    numeric_columns = [col for col in feature_df.columns if col not in categorical_columns]
    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0.0).astype(np.float32)
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

    dataset_variant = f"reduced_flows_{variant_token}_sampled_public_graph"
    split_scheme = "stratified_random_train_val_test_from_reduced_flow_csv"
    manifest = {
        "dataset_name": "Westermo Network Traffic Dataset",
        "dataset_variant": dataset_variant,
        "dataset_source": WESTERMO_DATASET_SOURCE,
        "split_scheme": split_scheme,
        "seed": int(args.seed),
        "label_strategy": variant_token,
        "label_column": label_column,
        "label_text_column": label_text_column,
        "topology": {
            "type": "public_benchmark",
            "source": "westermo_reduced_flows",
        },
        "run_config": {
            "load_profile": "public_benchmark",
            "bot_type_mode": f"industrial_intrusion_{variant_token}",
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
        target_ip="public_westermo",
        delta_t=1.0,
        n_windows=int(len(combined)),
        feature_names=feature_names,
        feature_index={name: idx for idx, name in enumerate(feature_names)},
        label_source=f"westermo_{label_source}",
    )
    apply_graph_contract(
        data,
        project_root=project_root,
        dataset_name="Westermo Network Traffic Dataset",
        dataset_variant=dataset_variant,
        dataset_source=WESTERMO_DATASET_SOURCE,
        split_scheme=split_scheme,
        manifest_file=output_manifest,
        manifest_metadata=manifest,
        graph_source_kind="external_public_dataset",
    )
    validate_graph_contract(data)
    output_graph.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, output_graph)

    summary = {
        "dataset_name": "Westermo Network Traffic Dataset",
        "dataset_variant": dataset_variant,
        "dataset_source": WESTERMO_DATASET_SOURCE,
        "label_strategy": variant_token,
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
        "capture_counts": {str(k): int(v) for k, v in combined["capture_view"].value_counts().to_dict().items()},
        "protocol_counts": {str(k): int(v) for k, v in combined["protocol"].value_counts().to_dict().items()},
    }
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_graph}")
    print(f"[OK] wrote {output_manifest}")
    print(f"[OK] wrote {output_summary}")


if __name__ == "__main__":
    main()
