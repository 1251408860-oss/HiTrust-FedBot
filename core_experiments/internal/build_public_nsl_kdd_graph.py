#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import time
import urllib.request
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

NSL_COLUMNS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]
RAW_URLS = {
    "train20": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B_20Percent.txt",
    "test": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest%2B.txt",
}
NSL_DATASET_SOURCE = "public_github_mirror:defcom17/NSL_KDD"
CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a public NSL-KDD graph for HiTrust external validation")
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--output-graph", default="")
    p.add_argument("--output-manifest", default="")
    p.add_argument("--output-summary", default="")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-size", type=int, default=8000)
    p.add_argument("--val-size", type=int, default=2000)
    p.add_argument("--test-size", type=int, default=4000)
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


def load_split_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=NSL_COLUMNS)
    df["label"] = (df["label"].astype(str) != "normal").astype(int)
    return df


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


def split_train_val(df: pd.DataFrame, *, train_size: int, val_size: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    total = int(train_size) + int(val_size)
    sampled = stratified_sample(df, size=total, seed=seed)
    train_df, val_df = train_test_split(
        sampled,
        train_size=int(train_size),
        random_state=int(seed),
        stratify=sampled["label"],
    )
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True)


def sanitize_token(text: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", str(text).strip())
    return token.strip("_") or "unknown"


def assign_owners(df: pd.DataFrame, *, owner_bucket_size: int, seed: int) -> tuple[list[str], dict[str, str], dict[str, int], np.ndarray]:
    rng = np.random.default_rng(seed)
    owner_by_row = np.empty(len(df), dtype=object)
    role_by_owner: dict[str, str] = {}
    label_by_owner: dict[str, int] = {}
    owner_names: list[str] = []

    grouped = df.groupby(["protocol_type", "service"], sort=True).indices
    for (protocol, service), raw_indices in grouped.items():
        indices = np.asarray(list(raw_indices), dtype=np.int64)
        rng.shuffle(indices)
        safe_protocol = sanitize_token(protocol)
        safe_service = sanitize_token(service)
        for bucket_id, start in enumerate(range(0, len(indices), int(owner_bucket_size))):
            chunk = indices[start : start + int(owner_bucket_size)]
            owner_name = f"owner_{safe_protocol}_{safe_service}_b{bucket_id:03d}"
            owner_by_row[chunk] = owner_name
            owner_names.append(owner_name)
            role_by_owner[owner_name] = f"proto:{safe_protocol}"
            majority = int(df.iloc[chunk]["label"].mean() >= 0.5)
            label_by_owner[owner_name] = majority

    missing = np.where(pd.isna(owner_by_row))[0]
    if len(missing) > 0:
        raise RuntimeError(f"owner assignment failed for rows: {missing[:10].tolist()}")
    return owner_names, role_by_owner, label_by_owner, owner_by_row


def build_knn_edges(x_norm: np.ndarray, *, k: int) -> torch.Tensor:
    model = NearestNeighbors(n_neighbors=int(k) + 1, metric="euclidean", n_jobs=-1)
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
    data_root = project_root / "data_hitrust" / "public_benchmarks" / "nsl_kdd"
    raw_root = data_root / "raw"
    graph_root = data_root / "graphs"
    meta_root = data_root / "meta"
    graph_root.mkdir(parents=True, exist_ok=True)
    meta_root.mkdir(parents=True, exist_ok=True)

    output_graph = Path(args.output_graph).resolve() if str(args.output_graph).strip() else graph_root / "nsl_kdd_public_graph.pt"
    output_manifest = Path(args.output_manifest).resolve() if str(args.output_manifest).strip() else meta_root / "nsl_kdd_public_manifest.json"
    output_summary = Path(args.output_summary).resolve() if str(args.output_summary).strip() else meta_root / "nsl_kdd_public_build_summary.json"

    train_path = raw_root / "KDDTrain+_20Percent.txt"
    test_path = raw_root / "KDDTest+.txt"
    ensure_download(RAW_URLS["train20"], train_path)
    ensure_download(RAW_URLS["test"], test_path)

    train_df_raw = load_split_frame(train_path)
    test_df_raw = load_split_frame(test_path)
    train_df, val_df = split_train_val(
        train_df_raw,
        train_size=int(args.train_size),
        val_size=int(args.val_size),
        seed=int(args.seed),
    )
    test_df = stratified_sample(test_df_raw, size=int(args.test_size), seed=int(args.seed) + 17)

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

    feature_df = combined.drop(columns=["label", "difficulty", "split"]).copy()
    feature_df = pd.get_dummies(feature_df, columns=CATEGORICAL_COLUMNS, dtype=np.float32)
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

    manifest = {
        "dataset_name": "NSL-KDD",
        "dataset_variant": "KDDTrain+_20Percent + KDDTest+",
        "dataset_source": NSL_DATASET_SOURCE,
        "split_scheme": "official_train_test_with_sampled_train_val",
        "seed": int(args.seed),
        "topology": {
            "type": "public_benchmark",
            "source": "nsl_kdd",
        },
        "run_config": {
            "load_profile": "public_benchmark",
            "bot_type_mode": "intrusion_binary",
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
        target_ip="public_nsl_kdd",
        delta_t=1.0,
        n_windows=int(len(combined)),
        feature_names=feature_names,
        feature_index={name: idx for idx, name in enumerate(feature_names)},
        label_source="nsl_kdd_binary",
    )
    apply_graph_contract(
        data,
        project_root=project_root,
        dataset_name="NSL-KDD",
        dataset_variant="train20_test_public_graph",
        dataset_source=NSL_DATASET_SOURCE,
        split_scheme="official_train_test_with_sampled_train_val",
        manifest_file=output_manifest,
        manifest_metadata=manifest,
        graph_source_kind="external_public_dataset",
    )
    validate_graph_contract(data)
    output_graph.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, output_graph)

    summary = {
        "dataset_name": "NSL-KDD",
        "dataset_source": NSL_DATASET_SOURCE,
        "output_graph": repo_relative_path(output_graph, project_root),
        "manifest_file": repo_relative_path(output_manifest, project_root),
        "seed": int(args.seed),
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
        "rows": int(len(combined)),
        "num_features": int(len(feature_names)),
        "num_edges": int(edge_index.shape[1]),
        "num_owners": int(len(owner_list)),
        "num_protocol_roles": int(len(set(role_by_owner.values()))),
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
        "protocol_counts": {str(k): int(v) for k, v in combined["protocol_type"].value_counts().to_dict().items()},
    }
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_graph}")
    print(f"[OK] wrote {output_manifest}")
    print(f"[OK] wrote {output_summary}")


if __name__ == "__main__":
    main()
