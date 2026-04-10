#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from torch_geometric.data import Data

from graph_contract import GRAPH_CONTRACT_VERSION, apply_graph_contract, graph_stats, validate_graph_contract

AUTO_LABEL_COLUMNS = [
    "label",
    "attack",
    "attack_label",
    "is_attack",
    "anomaly",
    "malicious",
    "bot",
    "target",
    "class",
]
AUTO_SPLIT_COLUMNS = ["split", "dataset_split", "partition", "fold"]
AUTO_OWNER_COLUMNS = ["src_ip", "source_ip", "source", "owner", "device_id", "client_id", "host"]
NEGATIVE_LABEL_TOKENS = {"0", "0.0", "false", "normal", "benign", "clean"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a public tabular flow graph under the local HiTrust graph contract")
    p.add_argument("--project-root", default=str(Path(__file__).resolve().parents[2]))
    p.add_argument("--input-pattern", required=True, help="Comma-separated glob(s) for CSV files")
    p.add_argument("--dataset-name", required=True)
    p.add_argument("--dataset-variant", required=True)
    p.add_argument("--dataset-source", required=True)
    p.add_argument("--output-graph", required=True)
    p.add_argument("--output-manifest", required=True)
    p.add_argument("--output-summary", required=True)
    p.add_argument("--label-column", default="")
    p.add_argument("--split-column", default="")
    p.add_argument("--owner-column", default="")
    p.add_argument("--categorical-columns", default="")
    p.add_argument("--drop-columns", default="")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--val-frac", type=float, default=0.2)
    p.add_argument("--test-frac", type=float, default=0.2)
    p.add_argument("--owner-bucket-size", type=int, default=128)
    p.add_argument("--knn-k", type=int, default=8)
    p.add_argument("--positive-labels", default="1,true,attack,malicious,bot,anomaly,intrusion")
    return p.parse_args()


def parse_csv_patterns(text: str, project_root: Path) -> list[Path]:
    out: list[Path] = []
    for raw_pattern in [item.strip() for item in str(text).split(",") if item.strip()]:
        pattern_path = Path(raw_pattern)
        pattern_text = str(pattern_path if pattern_path.is_absolute() else (project_root / raw_pattern))
        out.extend(Path(match).resolve() for match in glob.glob(pattern_text, recursive=True))
    unique = sorted({path for path in out if path.suffix.lower() == ".csv"})
    if not unique:
        raise RuntimeError(f"no csv files matched input pattern: {text}")
    return unique


def sanitize_token(text: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", str(text).strip())
    return token.strip("_") or "unknown"


def detect_column(columns: list[str], preferred: str, candidates: list[str]) -> str:
    if str(preferred).strip():
        if preferred in columns:
            return str(preferred)
        lowered = {str(col).lower(): str(col) for col in columns}
        if preferred.lower() in lowered:
            return lowered[preferred.lower()]
        raise KeyError(f"column not found: {preferred}")
    lowered = {str(col).lower(): str(col) for col in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    raise KeyError(f"failed to detect column from candidates: {candidates}")


def normalize_labels(series: pd.Series, positive_labels: set[str]) -> np.ndarray:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(np.int64).to_numpy()
    if pd.api.types.is_numeric_dtype(series):
        return (pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float) != 0.0).astype(np.int64).to_numpy()
    tokens = series.astype(str).str.strip().str.lower()
    return tokens.isin(positive_labels).astype(np.int64).to_numpy()


def normalize_split_value(value: Any) -> str:
    token = str(value).strip().lower()
    if token in {"train", "tr", "training"}:
        return "train"
    if token in {"val", "valid", "validation", "dev"}:
        return "val"
    if token in {"test", "te", "testing"}:
        return "test"
    return ""


def build_split_column(df: pd.DataFrame, *, split_column: str, seed: int, val_frac: float, test_frac: float) -> pd.Series:
    if split_column:
        split_tokens = df[split_column].map(normalize_split_value)
        if split_tokens.isin(["train", "val", "test"]).all():
            return split_tokens
        raise RuntimeError(f"unsupported values in split column: {split_column}")

    labels = df["__label__"].astype(int).to_numpy()
    indices = np.arange(len(df))
    test_frac = min(max(float(test_frac), 0.0), 0.8)
    val_frac = min(max(float(val_frac), 0.0), 0.8)
    if len(df) < 3 or (test_frac + val_frac) <= 0.0:
        return pd.Series(["train"] * len(df), index=df.index)

    train_idx, test_idx = train_test_split(
        indices,
        test_size=float(test_frac),
        random_state=int(seed),
        stratify=labels if len(np.unique(labels)) > 1 else None,
    )
    val_size_relative = val_frac / max(1.0 - test_frac, 1e-6)
    if val_size_relative <= 0.0:
        val_idx = np.asarray([], dtype=np.int64)
    else:
        train_idx, val_idx = train_test_split(
            train_idx,
            test_size=float(min(max(val_size_relative, 0.0), 0.8)),
            random_state=int(seed) + 17,
            stratify=labels[train_idx] if len(np.unique(labels[train_idx])) > 1 else None,
        )
    split = np.full(len(df), "train", dtype=object)
    split[test_idx] = "test"
    split[val_idx] = "val"
    return pd.Series(split, index=df.index)


def assign_owners(df: pd.DataFrame, *, owner_column: str, owner_bucket_size: int, seed: int) -> tuple[list[str], dict[str, str], dict[str, int], np.ndarray]:
    rng = np.random.default_rng(seed)
    owner_by_row = np.empty(len(df), dtype=object)
    owner_names: list[str] = []
    role_by_owner: dict[str, str] = {}
    label_by_owner: dict[str, int] = {}
    bucket_size = max(int(owner_bucket_size), 1)
    grouped = df.groupby(owner_column, sort=True).indices
    for raw_owner, raw_indices in grouped.items():
        indices = np.asarray(list(raw_indices), dtype=np.int64)
        rng.shuffle(indices)
        safe_owner = sanitize_token(raw_owner)
        for bucket_id, start in enumerate(range(0, len(indices), bucket_size)):
            chunk = indices[start : start + bucket_size]
            owner_name = f"owner_{safe_owner}_b{bucket_id:03d}"
            owner_by_row[chunk] = owner_name
            owner_names.append(owner_name)
            role_by_owner[owner_name] = f"source:{safe_owner}"
            label_by_owner[owner_name] = int(df.iloc[chunk]["__label__"].mean() >= 0.5)
    if pd.isna(owner_by_row).any():
        raise RuntimeError("owner assignment left unassigned rows")
    return sorted(owner_names), role_by_owner, label_by_owner, owner_by_row


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
    if not rows:
        rows = [(0, 0)]
    return torch.tensor(rows, dtype=torch.long).t().contiguous()


def build_feature_frame(
    df: pd.DataFrame,
    *,
    label_column: str,
    split_column: str,
    owner_column: str,
    drop_columns: list[str],
    categorical_columns: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    exclude = {
        str(label_column),
        str(split_column),
        str(owner_column),
        "__label__",
        "__split__",
        "__source_file__",
    }
    exclude.update(str(col) for col in drop_columns if str(col).strip())

    feature_cols = [col for col in df.columns if str(col) not in exclude]
    if not feature_cols:
        raise RuntimeError("no feature columns remain after exclusions")

    feature_df = df.loc[:, feature_cols].copy()
    if not categorical_columns:
        categorical_columns = [
            str(col)
            for col in feature_df.columns
            if pd.api.types.is_object_dtype(feature_df[col]) or pd.api.types.is_bool_dtype(feature_df[col])
        ]
    numeric_columns = [str(col) for col in feature_df.columns if str(col) not in set(categorical_columns)]
    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0.0).astype(np.float32)
    for column in categorical_columns:
        feature_df[column] = feature_df[column].astype(str).fillna("unknown")
    feature_df = pd.get_dummies(feature_df, columns=categorical_columns, dtype=np.float32)
    return feature_df, [str(col) for col in feature_df.columns]


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_files = parse_csv_patterns(str(args.input_pattern), project_root)
    frames = []
    for csv_file in input_files:
        frame = pd.read_csv(csv_file)
        frame["__source_file__"] = csv_file.name
        frames.append(frame)
    combined = pd.concat(frames, axis=0, ignore_index=True)

    label_column = detect_column(list(combined.columns), str(args.label_column), AUTO_LABEL_COLUMNS)
    split_column = ""
    if str(args.split_column).strip():
        split_column = detect_column(list(combined.columns), str(args.split_column), AUTO_SPLIT_COLUMNS)
    elif any(candidate in {str(col).lower() for col in combined.columns} for candidate in AUTO_SPLIT_COLUMNS):
        split_column = detect_column(list(combined.columns), "", AUTO_SPLIT_COLUMNS)
    owner_column = ""
    if str(args.owner_column).strip():
        owner_column = detect_column(list(combined.columns), str(args.owner_column), AUTO_OWNER_COLUMNS)
    else:
        lowered = {str(col).lower(): str(col) for col in combined.columns}
        for candidate in AUTO_OWNER_COLUMNS:
            if candidate in lowered:
                owner_column = lowered[candidate]
                break
    if not owner_column:
        owner_column = "__source_file__"

    positive_labels = {
        token.strip().lower()
        for token in str(args.positive_labels).split(",")
        if token.strip()
    }
    positive_labels |= {token for token in positive_labels if token not in NEGATIVE_LABEL_TOKENS}
    combined["__label__"] = normalize_labels(combined[label_column], positive_labels)
    combined["__split__"] = build_split_column(
        combined,
        split_column=split_column,
        seed=int(args.seed),
        val_frac=float(args.val_frac),
        test_frac=float(args.test_frac),
    )

    categorical_columns = [item.strip() for item in str(args.categorical_columns).split(",") if item.strip()]
    drop_columns = [item.strip() for item in str(args.drop_columns).split(",") if item.strip()]
    feature_df, feature_names = build_feature_frame(
        combined,
        label_column=label_column,
        split_column="__split__",
        owner_column=owner_column,
        drop_columns=drop_columns,
        categorical_columns=categorical_columns,
    )

    owner_names, role_by_owner, label_by_owner, owner_by_row = assign_owners(
        combined.assign(**{owner_column: combined[owner_column].astype(str)}),
        owner_column=owner_column,
        owner_bucket_size=int(args.owner_bucket_size),
        seed=int(args.seed),
    )
    owner_index = {name: idx for idx, name in enumerate(owner_names)}
    owner_map_by_row_name = np.asarray(owner_by_row, dtype=object)
    ip_idx = np.asarray([owner_index[str(name)] for name in owner_map_by_row_name], dtype=np.int64)

    x_raw = feature_df.to_numpy(dtype=np.float32)
    train_mask_np = combined["__split__"].to_numpy() == "train"
    val_mask_np = combined["__split__"].to_numpy() == "val"
    test_mask_np = combined["__split__"].to_numpy() == "test"
    scaler = StandardScaler()
    scaler.fit(x_raw[train_mask_np] if np.any(train_mask_np) else x_raw)
    x_norm = scaler.transform(x_raw).astype(np.float32)

    edge_index = build_knn_edges(x_norm, k=int(args.knn_k))
    edge_index_undirected = torch.cat([edge_index, edge_index.flip(0)], dim=1)
    edge_type = torch.zeros(edge_index.shape[1], dtype=torch.long)
    edge_type_undirected = torch.zeros(edge_index_undirected.shape[1], dtype=torch.long)

    manifest = {
        "dataset_name": str(args.dataset_name),
        "dataset_variant": str(args.dataset_variant),
        "dataset_source": str(args.dataset_source),
        "split_scheme": "csv_split_column" if split_column else "stratified_random_split",
        "seed": int(args.seed),
        "topology": {
            "type": "public_benchmark",
            "source": sanitize_token(str(args.dataset_name)).lower(),
        },
        "run_config": {
            "load_profile": "public_benchmark",
            "bot_type_mode": "external_flow_binary",
        },
        "roles": {name: role_by_owner[name] for name in owner_names},
        "ip_labels": {name: int(label_by_owner[name]) for name in owner_names},
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
    }

    data = Data(
        x=torch.from_numpy(x_raw),
        x_norm=torch.from_numpy(x_norm),
        edge_index=edge_index,
        edge_type=edge_type,
        edge_index_undirected=edge_index_undirected,
        edge_type_undirected=edge_type_undirected,
        y=torch.from_numpy(combined["__label__"].to_numpy(dtype=np.int64)),
        window_idx=torch.arange(len(combined), dtype=torch.long),
        ip_idx=torch.from_numpy(ip_idx),
        train_mask=torch.from_numpy(train_mask_np),
        val_mask=torch.from_numpy(val_mask_np),
        test_mask=torch.from_numpy(test_mask_np),
        temporal_train_mask=torch.from_numpy(train_mask_np),
        temporal_test_mask=torch.from_numpy(test_mask_np),
        feat_mean=torch.from_numpy(scaler.mean_.astype(np.float32)),
        feat_std=torch.from_numpy(np.maximum(scaler.scale_, 1e-6).astype(np.float32)),
        source_ips=owner_names,
        target_ip=sanitize_token(str(args.dataset_name)).lower(),
        delta_t=1.0,
        n_windows=int(len(combined)),
        feature_names=feature_names,
        feature_index={name: idx for idx, name in enumerate(feature_names)},
        label_source=f"{sanitize_token(label_column).lower()}_binary",
    )

    output_manifest = Path(args.output_manifest).resolve()
    output_graph = Path(args.output_graph).resolve()
    output_summary = Path(args.output_summary).resolve()
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_graph.parent.mkdir(parents=True, exist_ok=True)
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    apply_graph_contract(
        data,
        project_root=project_root,
        dataset_name=str(args.dataset_name),
        dataset_variant=str(args.dataset_variant),
        dataset_source=str(args.dataset_source),
        split_scheme=str(manifest["split_scheme"]),
        manifest_file=output_manifest,
        manifest_metadata=manifest,
        graph_source_kind="external_public_dataset",
    )
    validate_graph_contract(data)
    torch.save(data, output_graph)

    summary = {
        "dataset_name": str(args.dataset_name),
        "dataset_variant": str(args.dataset_variant),
        "dataset_source": str(args.dataset_source),
        "input_files": [str(path) for path in input_files],
        "label_column": str(label_column),
        "split_column": str(split_column),
        "owner_column": str(owner_column),
        "seed": int(args.seed),
        "graph_contract_version": GRAPH_CONTRACT_VERSION,
        "graph_stats": graph_stats(data),
    }
    output_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[OK] wrote {output_graph}")
    print(f"[OK] wrote {output_manifest}")
    print(f"[OK] wrote {output_summary}")


if __name__ == "__main__":
    main()
