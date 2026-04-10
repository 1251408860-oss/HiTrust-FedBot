#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import ConnectionPatch, Ellipse
from matplotlib.ticker import FuncFormatter, MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


REPO_ROOT = Path(__file__).resolve().parent
TABLE_DIR = REPO_ROOT / "tables"

LABEL_MAP = {
    "trust_aware": "HiTrust",
    "static": "HiTrust",
    "condfloor": "HiTrust+CF",
    "hier_keepall": "Keep-all",
    "keepall": "Keep-all",
    "centered_clipping": "Centered Clip",
    "caf": "CAF",
    "arc_mean": "ARC+Mean",
    "rfa": "RFA",
    "mean": "Mean",
    "median": "Median",
    "krum": "Krum",
    "fltrust_like": "FLTrust-like",
    "flshield_like": "FLShield-like",
    "fedtruth_like": "FedTruth-like",
    "foolsgold": "FoolsGold",
    "temporal_rootguard": "TRG",
    "temporal_rootguard_v2": "TRG-v2",
    "no_layerwise": "w/o layerwise",
    "no_behavioral": "w/o behavioral",
    "no_soft_weighting": "w/o soft-weight",
    "no_peer_penalty": "w/o peer penalty",
    "feature_mlp": "FeatureMLP",
    "sage": "GraphSAGE",
    "head_only": "Head-only",
    "adapter_ft": "Adapter-FT",
    "full_ft": "Full-FT",
}

COLOR_MAP = {
    "trust_aware": "#5C89C8",
    "static": "#5C89C8",
    "condfloor": "#798899",
    "hier_keepall": "#B5BFCA",
    "keepall": "#B5BFCA",
    "centered_clipping": "#97A6B2",
    "caf": "#8FA7B7",
    "arc_mean": "#A4AFBA",
    "rfa": "#AEB7C0",
    "mean": "#C2C8CF",
    "median": "#BAC1C8",
    "krum": "#AFB7BF",
    "fltrust_like": "#88A2C2",
    "flshield_like": "#9FB6A0",
    "fedtruth_like": "#A397BF",
    "foolsgold": "#9A9A9A",
    "temporal_rootguard": "#7D9DBE",
    "temporal_rootguard_v2": "#6E7783",
    "no_layerwise": "#A8B8AA",
    "no_behavioral": "#B0A7C2",
    "no_soft_weighting": "#B8A37F",
    "no_peer_penalty": "#B08E8E",
    "feature_mlp": "#B4BEC9",
    "sage": "#5C89C8",
    "head_only": "#B5BFCA",
    "adapter_ft": "#5C89C8",
    "full_ft": "#AAB5C0",
    "server_static": "#5C89C8",
    "server_condfloor": "#798899",
    "server_keepall": "#B5BFCA",
}

EMPHASIZED = {
    "trust_aware",
    "static",
    "condfloor",
    "temporal_rootguard",
    "temporal_rootguard_v2",
    "sage",
    "adapter_ft",
}

METHOD_ORDER_HINT = {
    "condfloor": 0,
    "static": 1,
    "trust_aware": 1,
    "temporal_rootguard": 2,
    "temporal_rootguard_v2": 3,
    "fltrust_like": 4,
    "flshield_like": 5,
    "fedtruth_like": 6,
    "foolsgold": 7,
    "centered_clipping": 8,
    "caf": 9,
    "arc_mean": 10,
    "rfa": 11,
    "mean": 12,
    "median": 13,
    "krum": 14,
    "keepall": 15,
    "hier_keepall": 15,
}

METRIC_META = {
    "test_f1": {"title": "F1", "direction": "higher", "kind": "ratio"},
    "test_fpr": {"title": "FPR", "direction": "lower", "kind": "ratio"},
    "kept_poisoned_clients": {"title": "Retained Poisoned", "direction": "lower", "kind": "count"},
    "kept_clients": {"title": "Retained Clients", "direction": "higher", "kind": "count"},
}

PANEL_TAGS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
COUNT_ANNOTATION_LABELS = {
    "trust_aware",
    "static",
    "condfloor",
    "temporal_rootguard",
    "temporal_rootguard_v2",
    "keepall",
    "hier_keepall",
    "foolsgold",
    "fltrust_like",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export polished review figures from paper_hitrust tables.")
    parser.add_argument("--output-root", required=True, help="Desktop package root containing 主文图 / 补充图.")
    return parser.parse_args()


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
            "font.size": 9.0,
            "axes.titlesize": 10.0,
            "axes.labelsize": 9.2,
            "figure.titlesize": 10.5,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.edgecolor": "#1F1F1F",
            "axes.linewidth": 1.0,
            "axes.grid": False,
            "grid.color": "#C9CED4",
            "grid.alpha": 0.22,
            "grid.linewidth": 0.7,
            "xtick.color": "#1F1F1F",
            "ytick.color": "#1F1F1F",
            "text.color": "#1A1A1A",
            "axes.labelcolor": "#1A1A1A",
            "legend.frameon": False,
            "xtick.labelsize": 8.4,
            "ytick.labelsize": 8.4,
        }
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def short_label(label: str) -> str:
    return LABEL_MAP.get(str(label), str(label).replace("_", " "))


def method_color(label: str) -> str:
    return COLOR_MAP.get(str(label), "#607D8B")


def is_emphasized(label: str) -> bool:
    return str(label) in EMPHASIZED


def method_rank(row: dict[str, Any]) -> tuple[int, str]:
    label = str(row.get("label", ""))
    return int(METHOD_ORDER_HINT.get(label, 50)), short_label(label).lower()


def metric_mean(row: dict[str, Any], metric: str) -> float:
    return float(row.get(f"{metric}_mean", row.get(metric, 0.0)))


def metric_error(row: dict[str, Any], metric: str) -> tuple[float, float]:
    mean = metric_mean(row, metric)
    if f"{metric}_ci95_low" in row and f"{metric}_ci95_high" in row:
        low = max(mean - float(row.get(f"{metric}_ci95_low", mean)), 0.0)
        high = max(float(row.get(f"{metric}_ci95_high", mean)) - mean, 0.0)
        return low, high
    if f"{metric}_std" in row:
        std = max(float(row.get(f"{metric}_std", 0.0)), 0.0)
        return std, std
    return 0.0, 0.0


def metric_formatter(metric: str) -> FuncFormatter:
    if METRIC_META[metric]["kind"] == "count":
        return FuncFormatter(lambda x, _pos: f"{x:.1f}" if abs(x - round(x)) > 1e-6 else f"{int(round(x))}")
    return FuncFormatter(lambda x, _pos: f"{x:.2f}")


def metric_xlim(rows: list[dict[str, Any]], metric: str) -> tuple[float, float]:
    values = np.asarray([metric_mean(row, metric) for row in rows], dtype=np.float64)
    errors = np.asarray([metric_error(row, metric) for row in rows], dtype=np.float64)
    lows = values - errors[:, 0]
    highs = values + errors[:, 1]
    if METRIC_META[metric]["kind"] == "count":
        upper = float(np.max(highs)) if highs.size else 1.0
        if upper <= 4.1:
            upper = np.ceil((upper + 0.35) * 2.0) / 2.0
        else:
            upper = np.ceil(upper + 0.8)
        return 0.0, max(upper, 1.0)
    lower = float(np.min(lows)) if lows.size else 0.0
    upper = float(np.max(highs)) if highs.size else 1.0
    if metric == "test_f1":
        span = max(upper - lower, 0.012)
        lower = max(0.0, lower - max(0.008, span * 0.30))
        upper = min(1.0, upper + max(0.008, span * 0.22))
    else:
        upper = max(upper + max(0.005, upper * 0.12), 0.02)
        lower = 0.0
    if upper - lower < 0.02:
        pad = (0.02 - (upper - lower)) / 2.0
        lower = max(0.0, lower - pad)
        upper = min(1.0, upper + pad)
    return lower, upper


def finalize_figure(fig: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=260, bbox_inches="tight")
    plt.close(fig)


def add_panel_tag(ax: plt.Axes, idx: int) -> None:
    ax.text(
        -0.08,
        1.03,
        f"({PANEL_TAGS[idx]})",
        transform=ax.transAxes,
        fontsize=9.8,
        fontweight="bold",
        color="#1F1F1F",
        va="bottom",
    )


def add_header(fig: plt.Figure, context: str, note: str = "") -> None:
    fig.text(0.02, 0.985, context, ha="left", va="top", fontsize=9.8, color="#1A1A1A")
    if note:
        fig.text(0.98, 0.985, note, ha="right", va="top", fontsize=8.3, color="#5F6871")


def format_metric_value(metric: str, value: float) -> str:
    if METRIC_META[metric]["kind"] == "count":
        return f"{value:.1f}" if abs(value - round(value)) > 1e-6 else f"{int(round(value))}"
    return f"{value:.3f}"


def annotate_vertical_values(ax: plt.Axes, xs: list[float], values: list[float], metric: str) -> None:
    ymin, ymax = ax.get_ylim()
    offset = (ymax - ymin) * 0.02
    for x, value in zip(xs, values):
        ax.text(
            x,
            value + offset,
            format_metric_value(metric, value),
            ha="center",
            va="bottom",
            fontsize=7.2,
            color="#1A1A1A",
        )


def annotate_horizontal_values(
    ax: plt.Axes,
    ys: np.ndarray,
    values: list[float],
    metric: str,
    *,
    upper_errors: list[float] | None = None,
    selected_indices: set[int] | None = None,
    skip_zero: bool = False,
) -> None:
    xmin, xmax = ax.get_xlim()
    offset = (xmax - xmin) * 0.018
    for idx, (y, value) in enumerate(zip(ys, values)):
        if selected_indices is not None and idx not in selected_indices:
            continue
        if skip_zero and abs(value) < 1e-9:
            continue
        upper_err = 0.0 if upper_errors is None else float(upper_errors[idx])
        target_x = value + upper_err + offset
        place_left = target_x > xmax - offset * 0.5
        text_x = max(xmin + offset * 0.4, value - offset * 0.55) if place_left else target_x
        ax.text(
            text_x,
            y,
            format_metric_value(metric, value),
            ha="right" if place_left else "left",
            va="center",
            fontsize=7.2,
            color="#1A1A1A",
        )


def ablation_annotation_indices(labels: list[str], metric: str, values: list[float]) -> set[int]:
    selected = {
        idx
        for idx, label in enumerate(labels)
        if label in {"temporal_rootguard", "temporal_rootguard_v2", "no_peer_penalty"}
    }
    if metric == "kept_poisoned_clients":
        selected |= {idx for idx, value in enumerate(values) if value > 0.0}
    return selected


def color_ylabels(ax: plt.Axes, ordered_labels: list[str]) -> None:
    for tick, label in zip(ax.get_yticklabels(), ordered_labels):
        tick.set_color("#22313F")
        tick.set_fontweight("bold" if is_emphasized(label) else "normal")


def plot_comparison_table(
    *,
    table_name: str,
    output_path: Path,
    figure_title: str,
    metrics: list[str],
) -> None:
    rows = load_json(TABLE_DIR / table_name)["rows"]
    ordered = sorted(rows, key=method_rank)
    ordered_labels = [str(row["label"]) for row in ordered]
    y = np.arange(len(ordered))[::-1]
    height = max(3.0, 0.23 * len(ordered) + 1.1)
    width = 2.55 * len(metrics) + 1.9
    fig, axes = plt.subplots(1, len(metrics), figsize=(width, height), sharey=True)
    if len(metrics) == 1:
        axes = [axes]
    add_header(fig, figure_title, "mean ± 95% CI")

    for idx, (ax, metric) in enumerate(zip(axes, metrics)):
        add_panel_tag(ax, idx)
        for y_pos, row in zip(y, ordered):
            label = str(row["label"])
            mean = metric_mean(row, metric)
            low, high = metric_error(row, metric)
            color = method_color(label)
            ax.errorbar(
                mean,
                y_pos,
                xerr=np.asarray([[low], [high]], dtype=np.float64),
                fmt="s",
                color=color,
                ecolor="#1A1A1A",
                markersize=5.6 if is_emphasized(label) else 4.8,
                elinewidth=1.15,
                capsize=2.3,
                markeredgecolor="#111111",
                markeredgewidth=0.6,
                zorder=3,
            )
        ax.grid(axis="x")
        ax.set_title(METRIC_META[metric]["title"], pad=4)
        ax.set_xlim(*metric_xlim(ordered, metric))
        ax.xaxis.set_major_formatter(metric_formatter(metric))
        if METRIC_META[metric]["kind"] == "count":
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=False))
        else:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.tick_params(axis="x", labelsize=8.2)
        if idx == 0:
            ax.set_yticks(y, [short_label(label) for label in ordered_labels])
            color_ylabels(ax, ordered_labels)
            ax.tick_params(axis="y", pad=2)
        else:
            ax.tick_params(axis="y", length=0, labelleft=False)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        if metric in {"kept_poisoned_clients", "kept_clients"}:
            xmin, xmax = ax.get_xlim()
            offset = (xmax - xmin) * 0.018
            for y_pos, row in zip(y, ordered):
                label = str(row["label"])
                if label not in COUNT_ANNOTATION_LABELS:
                    continue
                mean = metric_mean(row, metric)
                if abs(mean) < 1e-9:
                    continue
                high = metric_error(row, metric)[1]
                target_x = mean + high + offset
                place_left = target_x > xmax - offset * 0.5
                ax.text(
                    max(xmin + offset * 0.35, mean - offset * 0.55) if place_left else target_x,
                    y_pos,
                    format_metric_value(metric, mean),
                    ha="right" if place_left else "left",
                    va="center",
                    fontsize=7.1,
                    color="#1A1A1A",
                )
    fig.tight_layout(rect=(0.02, 0.03, 1.0, 0.9), w_pad=1.2)
    finalize_figure(fig, output_path)


def plot_backbone_comparison(output_path: Path) -> None:
    rows = load_json(TABLE_DIR / "backbone_pilot_summary.json")["rows"]
    by_condition: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_condition.setdefault(str(row["condition"]), {})[str(row["backbone"])] = row
    conditions = [("clean", "Clean"), ("sign_flip_frac0p4", "Sign flip@0.4")]
    panels = [("test_f1", "F1"), ("test_fpr", "FPR")]

    fig, axes = plt.subplots(1, 2, figsize=(6.7, 2.95))
    add_header(fig, "Internal pilot: scenario H backbone comparison")
    x = np.arange(len(conditions))
    width = 0.28
    for idx, (ax, (metric, title)) in enumerate(zip(axes, panels)):
        add_panel_tag(ax, idx)
        feature_vals = []
        sage_vals = []
        for key, _display in conditions:
            feature_vals.append(float(by_condition[key]["feature_mlp"][metric]))
            sage_vals.append(float(by_condition[key]["sage"][metric]))
        ax.bar(x - width / 2, feature_vals, width=width, color=method_color("feature_mlp"), edgecolor="#111111", linewidth=0.75, label="FeatureMLP")
        ax.bar(x + width / 2, sage_vals, width=width, color=method_color("sage"), edgecolor="#111111", linewidth=0.75, label="GraphSAGE")
        ax.grid(axis="y")
        ax.set_title(title, pad=4)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        if metric == "test_f1":
            lower = max(0.85, min(feature_vals + sage_vals) - 0.02)
            upper = min(1.0, max(feature_vals + sage_vals) + 0.02)
        else:
            lower = 0.0
            upper = max(feature_vals + sage_vals) + 0.035
        ax.set_ylim(lower, upper)
        ax.yaxis.set_major_formatter(metric_formatter(metric))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.set_xticks(x, [label for _key, label in conditions])
        annotate_vertical_values(ax, list(x - width / 2), feature_vals, metric)
        annotate_vertical_values(ax, list(x + width / 2), sage_vals, metric)
    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=method_color("feature_mlp"), markeredgecolor="white", markersize=6.5, label="FeatureMLP"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=method_color("sage"), markeredgecolor="white", markersize=6.5, label="GraphSAGE"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.98), ncol=2, fontsize=8.2)
    fig.tight_layout(rect=(0.02, 0.02, 1.0, 0.88), w_pad=1.2)
    finalize_figure(fig, output_path)


def plot_trg_ablation_bars(output_path: Path) -> None:
    rows = load_json(TABLE_DIR / "public_cabench_scenario_h_temporal_rootguard_v2_ablation_comparison.json")["rows"]
    preferred = [
        "temporal_rootguard",
        "temporal_rootguard_v2",
        "no_layerwise",
        "no_behavioral",
        "no_soft_weighting",
        "no_peer_penalty",
    ]
    order = {label: idx for idx, label in enumerate(preferred)}
    ordered = sorted(rows, key=lambda row: order.get(str(row["label"]), 99))
    labels = [str(row["label"]) for row in ordered]
    y = np.arange(len(ordered))[::-1]
    metrics = ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"]

    fig, axes = plt.subplots(2, 2, figsize=(8.35, 4.75), sharey=True)
    add_header(fig, "Temporal RootGuard v2 ablation: public scenario H + adaptive benign mimic@0.4", "mean ± 95% CI")
    flat_axes = axes.flatten()
    for idx, (ax, metric) in enumerate(zip(flat_axes, metrics)):
        add_panel_tag(ax, idx)
        means = [metric_mean(row, metric) for row in ordered]
        errs = np.asarray([metric_error(row, metric) for row in ordered], dtype=np.float64)
        colors = [method_color(label) for label in labels]
        ax.barh(
            y,
            means,
            xerr=np.vstack([errs[:, 0], errs[:, 1]]),
            color=colors,
            edgecolor="#111111",
            linewidth=0.7,
            height=0.62,
            error_kw={"elinewidth": 1.0, "capsize": 2.0, "ecolor": "#111111"},
        )
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.set_title(METRIC_META[metric]["title"], pad=4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        ax.set_xlim(*metric_xlim(ordered, metric))
        ax.xaxis.set_major_formatter(metric_formatter(metric))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        if idx in (0, 2):
            ax.set_yticks(y, [short_label(label) for label in labels])
            color_ylabels(ax, labels)
        else:
            ax.tick_params(axis="y", length=0, labelleft=False)
        annotate_horizontal_values(
            ax,
            y,
            means,
            metric,
            upper_errors=errs[:, 1].tolist(),
            selected_indices=ablation_annotation_indices(labels, metric, means),
            skip_zero=metric == "kept_poisoned_clients",
        )
    fig.tight_layout(rect=(0.02, 0.03, 1.0, 0.9), w_pad=1.15, h_pad=1.25)
    finalize_figure(fig, output_path)


def plot_comm_tradeoff(output_path: Path) -> None:
    rows = sorted(load_json(TABLE_DIR / "comm_efficiency_sage_sign_flip_frac0p4_summary.json")["rows"], key=lambda row: float(row["bytes_vs_full_ft_ratio"]))
    labels = [str(row["tuning_mode"]) for row in rows]
    x = np.asarray([100.0 * float(row["bytes_vs_full_ft_ratio"]) for row in rows], dtype=np.float64)
    f1 = np.asarray([float(row["test_f1"]) for row in rows], dtype=np.float64)
    fpr = np.asarray([float(row["test_fpr"]) for row in rows], dtype=np.float64)
    colors = [method_color(label) for label in labels]
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 2.95), sharex=True)
    add_header(fig, "Communication-cost trade-off: scenario H + sign flip@0.4")
    offsets = {
        "head_only": (-14, 7),
        "adapter_ft": (-8, -10),
        "full_ft": (7, -7),
    }
    panels = [("test_f1", "F1", f1), ("test_fpr", "FPR", fpr)]
    for idx, (ax, (metric, title, values)) in enumerate(zip(axes, panels)):
        add_panel_tag(ax, idx)
        ax.plot(x, values, color="#AEB7C1", linewidth=1.8, zorder=1)
        for x_val, y_val, label, color, row in zip(x, values, labels, colors, rows):
            ax.scatter(x_val, y_val, s=56, marker="s", color=color, edgecolor="#111111", linewidth=0.65, zorder=3)
            dx, dy = offsets[label]
            note = short_label(label).replace("-FT", "")
            ax.annotate(
                note,
                (x_val, y_val),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="left" if dx >= 0 else "right",
                va="bottom" if dy >= 0 else "top",
                fontsize=8.1,
                color="#1A1A1A",
            )
        ax.set_title(title, pad=8)
        ax.set_xlabel("Comm. cost vs. Full-FT (%)")
        ax.grid(axis="both")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        if metric == "test_f1":
            ax.set_ylim(min(values) - 0.006, max(values) + 0.006)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: f"{val:.3f}"))
        else:
            ax.set_ylim(0.0, max(values) + 0.03)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: f"{val:.02f}"))
        ax.set_xlim(-3.5, max(x) + 10.0)
    fig.tight_layout(rect=(0.02, 0.02, 1.0, 0.88), w_pad=1.1)
    finalize_figure(fig, output_path)


def plot_runtime_scaling(output_path: Path) -> None:
    rows = load_json(TABLE_DIR / "public_cabench_scenario_h_server_runtime_scaling.json")["rows"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["label"]), []).append(row)
    for label in grouped:
        grouped[label].sort(key=lambda row: int(row["client_count"]))

    fig, axes = plt.subplots(2, 2, figsize=(7.55, 5.45), sharex=True)
    add_header(fig, "Public scenario H: runtime scaling", "update noise@0.4")
    specs = [
        ("server_round_ms", "Server round (ms)"),
        ("server_aggregation_ms", "Aggregation (ms)"),
        ("round_wall_clock_ms", "Round wall time (ms)"),
        ("process_peak_rss_mb", "Peak RSS (MB)"),
    ]
    order = [("static", "HiTrust"), ("condfloor", "HiTrust+CF"), ("keepall", "Keep-all")]
    inset_label_offsets = {"static": (3, -4), "condfloor": (3, 4), "keepall": (3, 0)}
    inset_min_spans = {
        "server_round_ms": 6.0,
        "server_aggregation_ms": 0.06,
        "round_wall_clock_ms": 7.5,
        "process_peak_rss_mb": 4.0,
    }
    for idx, (ax, (metric, title)) in enumerate(zip(axes.flatten(), specs)):
        add_panel_tag(ax, idx)
        series_bundle: list[tuple[str, np.ndarray, np.ndarray]] = []
        for label, legend_name in order:
            series = grouped.get(label, [])
            if not series:
                continue
            x = np.asarray([int(row["client_count"]) for row in series], dtype=np.float64)
            y = np.asarray([float(row[f"{metric}_mean"]) for row in series], dtype=np.float64)
            err = np.asarray([float(row.get(f"{metric}_std", 0.0)) for row in series], dtype=np.float64)
            series_bundle.append((label, x, y))
            ax.errorbar(
                x,
                y,
                yerr=err,
                marker="s",
                markersize=4.3,
                linewidth=1.5,
                color=COLOR_MAP[f"server_{label}"],
                ecolor="#1A1A1A",
                capsize=2.0,
                markeredgecolor="#111111",
                markeredgewidth=0.55,
                label=legend_name,
            )
        ax.set_title(title, pad=5)
        ax.grid(axis="both")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        if metric == "process_peak_rss_mb":
            ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: f"{val:.0f}"))
        else:
            ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _pos: f"{val:.0f}"))
        if series_bundle:
            inset_ax = inset_axes(
                ax,
                width="32%",
                height="28%",
                loc="lower left",
                bbox_to_anchor=(0.11, 0.13, 0.9, 0.9),
                bbox_transform=ax.transAxes,
                borderpad=0.0,
            )
            last_values = [y[-1] for _label, _x, y in series_bundle]
            x_low = min(x[-2] if len(x) > 1 else x[-1] for _label, x, _y in series_bundle) - 1.5
            x_high = max(x[-1] for _label, x, _y in series_bundle) + 0.5
            y_low = min(last_values)
            y_high = max(last_values)
            span = max(y_high - y_low, inset_min_spans[metric])
            pad = span * 0.32
            inset_ax.set_xlim(x_low, x_high)
            inset_ax.set_ylim(y_low - pad, y_high + pad)
            for label, x, y in series_bundle:
                inset_ax.plot(
                    x,
                    y,
                    marker="s",
                    markersize=3.3,
                    linewidth=1.1,
                    color=COLOR_MAP[f"server_{label}"],
                    markeredgecolor="#24313E",
                    markeredgewidth=0.4,
                    zorder=3,
                )
                dx, dy = inset_label_offsets[label]
                inset_ax.annotate(
                    f"{y[-1]:.1f}",
                    (x[-1], y[-1]),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=5.8,
                    color="#1F2A36",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.06, "alpha": 0.9},
                )
            inset_ax.grid(axis="both", alpha=0.12)
            inset_ax.tick_params(axis="both", which="both", labelbottom=False, labelleft=False, length=0)
            for spine in inset_ax.spines.values():
                spine.set_edgecolor("#96ABC6")
                spine.set_linewidth(0.75)
            inset_ax.set_facecolor("white")
            ellipse_height = max(span * 1.55, inset_min_spans[metric] * 1.2)
            ellipse = Ellipse(
                (x_high - 0.35, (y_low + y_high) / 2.0),
                width=1.9,
                height=ellipse_height,
                edgecolor="#96ABC6",
                facecolor="none",
                linewidth=0.85,
                alpha=0.95,
                zorder=2,
            )
            ax.add_patch(ellipse)
            connector = ConnectionPatch(
                xyA=(0.98, 0.98),
                coordsA=inset_ax.transAxes,
                xyB=(x_high - 0.95, (y_low + y_high) / 2.0 + ellipse_height * 0.22),
                coordsB=ax.transData,
                color="#96ABC6",
                linewidth=0.8,
                alpha=0.95,
            )
            ax.figure.add_artist(connector)
    for ax in axes[1]:
        ax.set_xlabel("Active clients")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=3, fontsize=8.1)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.82, bottom=0.11, wspace=0.13, hspace=0.22)
    finalize_figure(fig, output_path)


def plot_fltrust_sensitivity(output_path: Path) -> None:
    data = load_json(TABLE_DIR / "public_cabench_scenario_h_fltrust_like_sensitivity_report.json")
    rows = sorted(data["rows"], key=lambda row: (int(row["server_root_local_epochs"]), int(row["server_root_size"])))
    reference_rows = list(data.get("reference_rows", []))
    epochs = sorted({int(row["server_root_local_epochs"]) for row in rows})
    root_sizes = sorted({int(row["server_root_size"]) for row in rows})
    epoch_colors = {1: "#2B6EA6", 2: "#D4882A", 3: "#5AA469"}
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.95), sharex=True)
    add_header(fig, "FLTrust-like sensitivity: public scenario H + update noise@0.4")
    panels = [
        ("test_f1_mean", "F1", (0.95, 0.98)),
        ("test_fpr_mean", "FPR", None),
        ("kept_poisoned_clients_mean", "Retained Poisoned", None),
    ]
    for idx, (ax, (field, title, y_lim)) in enumerate(zip(axes, panels)):
        add_panel_tag(ax, idx)
        for epoch in epochs:
            subset = [row for row in rows if int(row["server_root_local_epochs"]) == epoch]
            subset.sort(key=lambda row: int(row["server_root_size"]))
            xs = [int(row["server_root_size"]) for row in subset]
            ys = [float(row[field]) for row in subset]
            ax.plot(xs, ys, marker="s", linewidth=1.4, markersize=4.0, color=epoch_colors.get(epoch, "#607D8B"), markeredgecolor="#111111", markeredgewidth=0.55, label=f"epochs={epoch}")
        for ref in reference_rows:
            ref_field = field.replace("_mean", "_mean")
            ax.axhline(float(ref.get(ref_field, 0.0)), linestyle="--", linewidth=1.0, color="#6E6E6E")
        ax.set_title(title, pad=5)
        ax.set_xticks(root_sizes, [str(x) for x in root_sizes])
        ax.set_xlabel("Server root size")
        ax.grid(axis="both")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.0)
        ax.spines["bottom"].set_linewidth(1.0)
        if y_lim is not None:
            ax.set_ylim(*y_lim)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.97), ncol=len(handles), fontsize=8.0)
    fig.tight_layout(rect=(0.02, 0.03, 1.0, 0.88), w_pad=1.25)
    finalize_figure(fig, output_path)


def build_plan(output_root: Path) -> list[dict[str, Any]]:
    main_dir = output_root / "主文图"
    supp_dir = output_root / "补充图"
    return [
        {
            "kind": "backbone",
            "output": main_dir / "Fig1_backbone_comparison.png",
        },
        {
            "kind": "comm",
            "output": main_dir / "Fig2_communication_tradeoff.png",
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_e_update_noise_baseline_comparison.json",
            "output": main_dir / "Fig3_public_cabench_scenario_e_update_noise.png",
            "title": "Public Ca-Bench scenario E + update noise@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_h_update_noise_baseline_comparison.json",
            "output": main_dir / "Fig4_public_cabench_scenario_h_update_noise.png",
            "title": "Public Ca-Bench scenario H + update noise@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_westermo_update_noise_baseline_comparison.json",
            "output": main_dir / "Fig5_public_westermo_update_noise.png",
            "title": "Public Westermo + update noise@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_westermo_sign_flip_baseline_comparison.json",
            "output": main_dir / "Fig6_public_westermo_sign_flip.png",
            "title": "Public Westermo + sign flip@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_h_adaptive_benign_mimic_comparison.json",
            "output": main_dir / "Fig7_public_cabench_scenario_h_adaptive_benign_mimic.png",
            "title": "Public Ca-Bench scenario H + adaptive benign mimic@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "trg_ablation",
            "output": main_dir / "Fig8_temporal_rootguard_v2_ablation.png",
        },
        {
            "kind": "runtime",
            "output": main_dir / "Fig9_server_runtime_scaling.png",
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_h_colluding_update_noise_comparison.json",
            "output": supp_dir / "FigS1_public_cabench_scenario_h_colluding_update_noise.png",
            "title": "Public Ca-Bench scenario H + colluding update noise@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_h_multi_round_stealth_comparison.json",
            "output": supp_dir / "FigS2_public_cabench_scenario_h_multi_round_stealth.png",
            "title": "Public Ca-Bench scenario H + multi-round stealth@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_e_adaptive_alie_like_comparison.json",
            "output": supp_dir / "FigS3_public_cabench_scenario_e_adaptive_alie_like.png",
            "title": "Public Ca-Bench scenario E + adaptive ALIE-like@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_h_adaptive_alie_like_comparison.json",
            "output": supp_dir / "FigS4_public_cabench_scenario_h_adaptive_alie_like.png",
            "title": "Public Ca-Bench scenario H + adaptive ALIE-like@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_cabench_scenario_e_adaptive_benign_mimic_comparison.json",
            "output": supp_dir / "FigS5_public_cabench_scenario_e_adaptive_benign_mimic.png",
            "title": "Public Ca-Bench scenario E + adaptive benign mimic@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients", "kept_clients"],
        },
        {
            "kind": "comparison",
            "table": "public_nslkdd_update_noise_baseline_comparison.json",
            "output": supp_dir / "FigS6_public_nslkdd_update_noise.png",
            "title": "NSL-KDD + update noise@0.4",
            "metrics": ["test_f1", "test_fpr", "kept_poisoned_clients"],
        },
        {
            "kind": "fltrust_sensitivity",
            "output": supp_dir / "FigS7_fltrust_like_sensitivity.png",
        },
    ]


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root).resolve()
    apply_style()
    plan = build_plan(output_root)
    for item in plan:
        kind = str(item["kind"])
        if kind == "backbone":
            plot_backbone_comparison(Path(item["output"]))
        elif kind == "comm":
            plot_comm_tradeoff(Path(item["output"]))
        elif kind == "comparison":
            plot_comparison_table(
                table_name=str(item["table"]),
                output_path=Path(item["output"]),
                figure_title=str(item["title"]),
                metrics=list(item["metrics"]),
            )
        elif kind == "trg_ablation":
            plot_trg_ablation_bars(Path(item["output"]))
        elif kind == "runtime":
            plot_runtime_scaling(Path(item["output"]))
        elif kind == "fltrust_sensitivity":
            plot_fltrust_sensitivity(Path(item["output"]))
        else:
            raise KeyError(f"unknown plot kind: {kind}")
        print(f"[OK] wrote {Path(item['output']).resolve()}")


if __name__ == "__main__":
    main()
