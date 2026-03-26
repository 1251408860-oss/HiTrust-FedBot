#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


TABLE_FILES = {
    "cross_scenario": "cross_scenario_sage_full_matrix.json",
    "backbone_h_clean": "backbone_clean_f1_significance.json",
    "backbone_h_sign": "backbone_sign_flip_frac0p4_f1_significance.json",
    "backbone_g_clean": "scenario_g_backbone_clean_f1_significance.json",
    "backbone_g_sign": "scenario_g_backbone_sign_flip_frac0p4_f1_significance.json",
    "scenario_g_backbone_seed": "scenario_g_backbone_seed_comparison.json",
    "comm_clean": "real_graph_pilot_h_scenario_h_sage_tuning_modes.json",
    "comm_sign": "tuning_modes_sage_sign_flip_frac0p4_summary.json",
    "comm_noise": "tuning_modes_sage_update_noise_frac0p4_summary.json",
    "aggregation": "aggregation_sign_flip_frac0p4_sage_group_stats.json",
    "min_keep": "min_keep_per_group_sage_sensitivity.json",
    "scenario_h_trust": "scenario_h_trust_vs_keepall_seed_comparison.json",
    "scenario_e_trust": "scenario_e_trust_vs_keepall_seed_comparison.json",
    "public_trust": "public_nslkdd_trust_vs_keepall_seed_comparison.json",
    "scenario_h_condfloor_clean": "scenario_h_clean_condfloor_comparison.json",
    "scenario_h_condfloor_sign": "scenario_h_sign_flip_condfloor_comparison.json",
    "scenario_h_condfloor_noise": "scenario_h_update_noise_condfloor_comparison.json",
    "scenario_e_condfloor_noise": "scenario_e_update_noise_condfloor_comparison.json",
    "public_condfloor_noise": "public_nslkdd_update_noise_condfloor_comparison.json",
    "public_baseline_noise": "public_nslkdd_update_noise_baseline_comparison.json",
}


NAVY = "#1D4E89"
TEAL = "#2A9D8F"
RUST = "#C76D2D"
SLATE = "#6B7280"
AMBER = "#D8A13B"
ROSE = "#B6535F"
LIGHT_GRID = "#D8DEE9"
SOFT_BG = "#F7F9FC"
HEAT_LOW = "#FCF7E8"
HEAT_MID = "#72B7B2"
HEAT_HIGH = "#1D3A7C"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#334155",
            "axes.labelcolor": "#0F172A",
            "axes.titlesize": 15,
            "axes.titleweight": "semibold",
            "axes.labelsize": 11.5,
            "xtick.color": "#0F172A",
            "ytick.color": "#0F172A",
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "font.size": 10.5,
            "font.family": "DejaVu Sans",
            "grid.color": LIGHT_GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.45,
            "axes.grid": False,
            "legend.frameon": False,
            "legend.fontsize": 10,
            "savefig.bbox": "tight",
        }
    )


def add_panel_tag(ax, tag: str) -> None:
    ax.text(
        -0.12,
        1.06,
        tag,
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        color="#0F172A",
        va="bottom",
    )


def shorten_condition(raw: str) -> str:
    mapping = {
        "clean": "Clean",
        "sign_flip_frac0p4": "Sign-flip@0.4",
        "update_noise_frac0p4": "Update-noise@0.4",
        "sage_clean": "Clean",
        "sage_sign_flip_frac0p4": "Sign-flip@0.4",
        "sage_update_noise_frac0p4": "Update-noise@0.4",
    }
    return mapping.get(raw, raw)


def short_scenario(raw: str) -> str:
    mapping = {
        "scenario_d_three_tier_low2": "D  three-tier",
        "scenario_e_three_tier_high2": "E  held-out",
        "scenario_f_two_tier_high2": "F  two-tier",
        "scenario_g_mimic_congest": "G  mimic",
        "scenario_h_mimic_heavy_overlap": "H  stress",
    }
    return mapping.get(raw, raw)


def pretty_label(raw: str) -> str:
    mapping = {
        "feature_mlp": "FeatureMLP",
        "sage": "GraphSAGE",
        "head_only": "Head-only",
        "adapter_ft": "Adapter-FT",
        "full_ft": "Full-FT",
        "trust_aware": "Trust-aware",
        "keep_all": "Keep-all",
        "hier_keepall": "Hier keep-all",
        "condfloor": "CondFloor",
        "static": "Static floor",
        "keepall": "Keep-all",
        "hierarchical": "Hierarchical",
        "mean": "Mean",
        "median": "Median",
        "krum": "Krum",
    }
    return mapping.get(raw, raw.replace("_", " ").title())


def ci95(std: float, n: int) -> float:
    if n <= 1:
        return 0.0
    t_lookup = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571}
    t_crit = t_lookup.get(n, 1.96)
    return t_crit * std / math.sqrt(n)


def finish_figure(fig: plt.Figure, output_path: Path) -> None:
    fig.tight_layout()
    fig.savefig(output_path, dpi=320)
    plt.close(fig)


def horizontal_dumbbell(
    ax: plt.Axes,
    rows: list[dict],
    *,
    left_key: str,
    right_key: str,
    title: str,
    higher_better: bool,
    show_p: bool = False,
) -> None:
    y = np.arange(len(rows))[::-1]
    for yi, row in zip(y, rows):
        left = row[left_key]["mean"]
        right = row[right_key]["mean"]
        left_err = row[left_key]["err"]
        right_err = row[right_key]["err"]
        ax.plot([left, right], [yi, yi], color="#CBD5E1", linewidth=2.2, zorder=1)
        ax.errorbar(left, yi, xerr=left_err, fmt="o", color=SLATE, markersize=7, capsize=3, linewidth=1.2, zorder=3)
        ax.errorbar(right, yi, xerr=right_err, fmt="D", color=NAVY, markersize=7, capsize=3, linewidth=1.2, zorder=3)
        delta = right - left
        sign = "+" if delta >= 0 else ""
        label = f"{sign}{delta:.3f}"
        if show_p and row.get("p_value") is not None:
            p_val = row["p_value"]
            if p_val < 1e-3:
                label += f"  (p<{1e-3:g})"
            else:
                label += f"  (p={p_val:.3f})"
        ax.text(max(left, right) + row["text_offset"], yi + 0.05, label, fontsize=9.5, color="#334155")
    ax.set_yticks(y, [row["label"] for row in rows])
    ax.grid(axis="x")
    ax.set_title(title, fontsize=12.8, pad=8)


def plot_cross_scenario_heatmap(table_dir: Path, output_dir: Path) -> None:
    obj = load_json(table_dir / TABLE_FILES["cross_scenario"])
    scenario_order = [
        "scenario_d_three_tier_low2",
        "scenario_e_three_tier_high2",
        "scenario_f_two_tier_high2",
        "scenario_g_mimic_congest",
        "scenario_h_mimic_heavy_overlap",
    ]
    condition_order = ["sage_clean", "sage_sign_flip_frac0p4", "sage_update_noise_frac0p4"]
    cell = {(row["scenario_name"], row["condition"]): float(row["test_f1"]) for row in obj["rows"]}
    matrix = np.array([[cell[(s, c)] for c in condition_order] for s in scenario_order], dtype=float)

    fig, ax = plt.subplots(figsize=(7.6, 4.9))
    cmap = LinearSegmentedColormap.from_list("paper_heat", [HEAT_LOW, HEAT_MID, HEAT_HIGH])
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))
    ax.set_xticks(range(len(condition_order)), [shorten_condition(c) for c in condition_order])
    ax.set_yticks(range(len(scenario_order)), [short_scenario(s) for s in scenario_order])
    ax.set_title("GraphSAGE Mainline Across Topology-Aware Scenarios")
    ax.set_xlabel("Training condition")
    ax.set_ylabel("Scenario family")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=9.5, color="#111827")
    ax.set_xticks(np.arange(-0.5, matrix.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, matrix.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    for idx, scenario in enumerate(scenario_order):
        if scenario.endswith("high2"):
            ax.get_yticklabels()[idx].set_fontweight("bold")
            ax.get_yticklabels()[idx].set_color(TEAL)
        if scenario.endswith("heavy_overlap"):
            ax.get_yticklabels()[idx].set_fontweight("bold")
            ax.get_yticklabels()[idx].set_color(RUST)
    cbar = fig.colorbar(im, ax=ax, shrink=0.88, pad=0.02)
    cbar.set_label("Test F1")
    finish_figure(fig, output_dir / "cross_scenario_f1_heatmap.png")


def plot_backbone_comparison(table_dir: Path, output_dir: Path) -> None:
    h_clean = load_json(table_dir / TABLE_FILES["backbone_h_clean"])
    h_sign = load_json(table_dir / TABLE_FILES["backbone_h_sign"])
    g_clean = load_json(table_dir / TABLE_FILES["backbone_g_clean"])
    g_sign = load_json(table_dir / TABLE_FILES["backbone_g_sign"])

    def row_from_sig(sig_obj: dict, label: str) -> dict:
        values = {row["label"]: row["test_f1"] for row in sig_obj["rows"]}
        ref_row = next(row for row in sig_obj["rows"] if row["label"] != sig_obj["reference"])
        return {
            "label": label,
            "feature": {
                "mean": float(values["feature_mlp"]["mean"]),
                "err": ci95(float(values["feature_mlp"]["std"]), int(values["feature_mlp"]["n"])),
            },
            "sage": {
                "mean": float(values["sage"]["mean"]),
                "err": ci95(float(values["sage"]["std"]), int(values["sage"]["n"])),
            },
            "p_value": ref_row["p_value_vs_reference"],
            "text_offset": 0.0015,
        }

    stress_rows = [row_from_sig(h_clean, "Clean"), row_from_sig(h_sign, "Sign-flip@0.4")]
    boundary_rows = [row_from_sig(g_clean, "Clean"), row_from_sig(g_sign, "Sign-flip@0.4")]

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.5), sharex=False)
    horizontal_dumbbell(
        axes[0],
        stress_rows,
        left_key="feature",
        right_key="sage",
        title="Stress case: scenario_h",
        higher_better=True,
        show_p=True,
    )
    axes[0].set_xlim(0.935, 0.985)
    axes[0].set_xlabel("Test F1")
    add_panel_tag(axes[0], "A")

    horizontal_dumbbell(
        axes[1],
        boundary_rows,
        left_key="feature",
        right_key="sage",
        title="Boundary case: scenario_g",
        higher_better=True,
        show_p=True,
    )
    axes[1].set_xlim(0.994, 1.0015)
    axes[1].set_xlabel("Test F1")
    add_panel_tag(axes[1], "B")

    legend_handles = [
        Line2D([0], [0], marker="o", color=SLATE, linestyle="None", markersize=7, label="FeatureMLP"),
        Line2D([0], [0], marker="D", color=NAVY, linestyle="None", markersize=7, label="GraphSAGE"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=2, bbox_to_anchor=(0.52, 1.03))
    finish_figure(fig, output_dir / "backbone_comparison.png")


def plot_comm_tradeoff(table_dir: Path, output_dir: Path) -> None:
    sources = [
        ("clean", load_json(table_dir / TABLE_FILES["comm_clean"])),
        ("sign_flip_frac0p4", load_json(table_dir / TABLE_FILES["comm_sign"])),
        ("update_noise_frac0p4", load_json(table_dir / TABLE_FILES["comm_noise"])),
    ]
    rows: list[dict] = []
    for condition, obj in sources:
        for row in obj["rows"]:
            item = dict(row)
            item["condition"] = condition
            rows.append(item)

    cond_colors = {"clean": NAVY, "sign_flip_frac0p4": AMBER, "update_noise_frac0p4": TEAL}
    mode_markers = {"head_only": "o", "adapter_ft": "D", "full_ft": "s"}
    order = {"head_only": 0, "adapter_ft": 1, "full_ft": 2}

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6), sharex=True)
    for ax, metric, ylabel in zip(axes, ["test_f1", "test_fpr"], ["Test F1", "Test FPR"]):
        for condition, _ in sources:
            series = sorted(
                [row for row in rows if row["condition"] == condition],
                key=lambda x: order[str(x["tuning_mode"])],
            )
            xs = [float(r["total_bytes_est"]) for r in series]
            ys = [float(r[metric]) for r in series]
            ax.plot(xs, ys, color=cond_colors[condition], linewidth=1.6, alpha=0.8, zorder=1)
            for row in series:
                ax.scatter(
                    float(row["total_bytes_est"]),
                    float(row[metric]),
                    s=86,
                    marker=mode_markers[str(row["tuning_mode"])],
                    color=cond_colors[condition],
                    edgecolor="white",
                    linewidth=0.9,
                    zorder=3,
                )
        ax.set_xscale("log")
        ax.grid(axis="both")
        ax.set_xlabel("Total communication bytes (log scale)")
        ax.set_ylabel(ylabel)
        ax.set_facecolor(SOFT_BG)

    axes[0].set_title("Accuracy vs communication")
    axes[1].set_title("False-positive rate vs communication")
    axes[0].annotate(
        "Adapter-FT sweet spot",
        xy=(123600, 0.9696),
        xytext=(220000, 0.9709),
        arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.0},
        fontsize=9.5,
        color="#334155",
    )
    axes[1].annotate(
        "Full-FT is not consistently better",
        xy=(635600, 0.0935),
        xytext=(160000, 0.102),
        arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.0},
        fontsize=9.3,
        color="#334155",
    )
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")

    cond_legend = [
        Line2D([0], [0], color=color, lw=2, label=shorten_condition(cond))
        for cond, color in cond_colors.items()
    ]
    mode_legend = [
        Line2D([0], [0], marker=marker, color="#475569", linestyle="None", markersize=7, label=pretty_label(mode))
        for mode, marker in mode_markers.items()
    ]
    fig.legend(handles=cond_legend + mode_legend, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.05))
    finish_figure(fig, output_dir / "comm_tradeoff.png")


def plot_trust_vs_keepall(json_path: Path, output_dir: Path) -> None:
    obj = load_json(json_path)
    rows = obj["rows"]
    conditions = [shorten_condition(r["condition"]) for r in rows][::-1]
    y = np.arange(len(rows))

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.8), sharey=True)
    metrics = [
        ("test_f1_mean", "test_f1_std", "Test F1", True),
        ("test_fpr_mean", "test_fpr_std", "Test FPR", False),
        ("kept_poisoned_clients_mean", None, "Retained poisoned", False),
    ]
    for ax, (metric_key, std_key, title, higher_better) in zip(axes, metrics):
        trust_vals = [float(r["trust_aware"][metric_key]) for r in rows][::-1]
        keep_vals = [float(r["keep_all"][metric_key]) for r in rows][::-1]
        if std_key is not None:
            trust_err = [ci95(float(r["trust_aware"][std_key]), int(r["trust_aware"]["n"])) for r in rows][::-1]
            keep_err = [ci95(float(r["keep_all"][std_key]), int(r["keep_all"]["n"])) for r in rows][::-1]
        else:
            trust_err = [0.0] * len(rows)
            keep_err = [0.0] * len(rows)
        for yi, t_val, k_val, t_err, k_err in zip(y, trust_vals, keep_vals, trust_err, keep_err):
            ax.plot([k_val, t_val], [yi, yi], color="#CBD5E1", linewidth=2.1, zorder=1)
            ax.errorbar(k_val, yi, xerr=k_err, fmt="o", color=RUST, markersize=7, capsize=3, linewidth=1.2, zorder=3)
            ax.errorbar(t_val, yi, xerr=t_err, fmt="D", color=TEAL, markersize=7, capsize=3, linewidth=1.2, zorder=3)
        ax.set_title(title, fontsize=13.2, pad=8)
        ax.grid(axis="x")
        ax.set_facecolor(SOFT_BG)
        if "Retained poisoned" not in title:
            hint = "Higher is better" if higher_better else "Lower is better"
            ax.text(0.98, 1.015, hint, transform=ax.transAxes, ha="right", va="bottom", fontsize=9.3, color="#475569")

    delta_labels = [float(r["delta_trust_minus_keepall"]["kept_poisoned_clients"]) for r in rows][::-1]
    p_values = [r["f1_p_value_trust_vs_keepall"] for r in rows][::-1]
    trust_f1 = [float(r["trust_aware"]["test_f1_mean"]) for r in rows][::-1]
    trust_kept = [float(r["trust_aware"]["kept_poisoned_clients_mean"]) for r in rows][::-1]

    for yi, f1, p_val in zip(y, trust_f1, p_values):
        axes[0].text(f1 + 0.0008, yi + 0.08, f"p={p_val:.3f}", fontsize=8.8, color="#475569")
    for yi, val, delta in zip(y, trust_kept, delta_labels):
        sign = "+" if delta >= 0 else ""
        axes[2].text(max(val, 0.0) + 0.12, yi + 0.08, f"{sign}{delta:.1f}", fontsize=8.8, color="#475569")

    axes[0].set_yticks(y, conditions)
    axes[0].set_xlim(min(min(trust_f1), min([float(r["keep_all"]["test_f1_mean"]) for r in rows])) - 0.0035, max(trust_f1) + 0.0045)
    fpr_all = [float(r["trust_aware"]["test_fpr_mean"]) for r in rows] + [float(r["keep_all"]["test_fpr_mean"]) for r in rows]
    axes[1].set_xlim(max(0.0, min(fpr_all) - 0.006), max(fpr_all) + 0.012)
    kept_all = [float(r["trust_aware"]["kept_poisoned_clients_mean"]) for r in rows] + [float(r["keep_all"]["kept_poisoned_clients_mean"]) for r in rows]
    axes[2].set_xlim(-0.15, max(kept_all) + 0.75)

    title = obj["scenario_label"].replace("Scenario-", "Scenario-")
    fig.suptitle(f"{title}: Trust-aware filtering vs Keep-all", y=1.02, fontsize=16, fontweight="semibold")
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")
    add_panel_tag(axes[2], "C")
    legend_handles = [
        Line2D([0], [0], marker="D", color=TEAL, linestyle="None", markersize=7, label="Trust-aware"),
        Line2D([0], [0], marker="o", color=RUST, linestyle="None", markersize=7, label="Keep-all"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=2, bbox_to_anchor=(0.52, 1.08))
    finish_figure(fig, output_dir / f"{json_path.stem}.png")


def plot_condfloor_comparison(json_path: Path, output_dir: Path) -> None:
    obj = load_json(json_path)
    rows = obj["rows"][::-1]
    y = np.arange(len(rows))
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.8), sharey=True)
    metrics = [
        ("test_f1_mean", "test_f1_std", "Test F1", True),
        ("test_fpr_mean", "test_fpr_std", "Test FPR", False),
        ("kept_poisoned_clients_mean", None, "Retained poisoned", False),
    ]
    colors = {"condfloor": TEAL, "static": SLATE, "keepall": RUST}

    for ax, (metric_key, std_key, title, higher_better) in zip(axes, metrics):
        values = [float(r[metric_key]) for r in rows]
        if std_key is not None:
            errs = [ci95(float(r[std_key]), int(r["n"])) for r in rows]
        else:
            errs = [0.0] * len(rows)
        for yi, row, value, err in zip(y, rows, values, errs):
            color = colors[row["label"]]
            marker = "D" if row["label"] == obj.get("reference") else "o"
            ax.errorbar(value, yi, xerr=err, fmt=marker, color=color, markersize=7, capsize=3, linewidth=1.2, zorder=3)
            ax.plot([0, value], [yi, yi], color=color, alpha=0.18, linewidth=3.0, zorder=1)
            if row.get("f1_p_value_vs_reference") is not None and metric_key == "test_f1_mean":
                ax.text(value + 0.0012, yi + 0.08, f"p={row['f1_p_value_vs_reference']:.3f}", fontsize=8.8, color="#475569")
        ax.set_title(title, fontsize=13.2, pad=8)
        ax.grid(axis="x")
        ax.set_facecolor(SOFT_BG)
        if "Retained poisoned" not in title:
            hint = "Higher is better" if higher_better else "Lower is better"
            ax.text(0.98, 1.015, hint, transform=ax.transAxes, ha="right", va="bottom", fontsize=9.3, color="#475569")

    axes[0].set_yticks(y, [pretty_label(r["label"]) for r in rows])
    axes[0].set_xlim(min(float(r["test_f1_mean"]) for r in rows) - 0.01, max(float(r["test_f1_mean"]) for r in rows) + 0.012)
    fpr_all = [float(r["test_fpr_mean"]) for r in rows]
    axes[1].set_xlim(max(0.0, min(fpr_all) - 0.015), max(fpr_all) + 0.05)
    kept_all = [float(r["kept_poisoned_clients_mean"]) for r in rows]
    axes[2].set_xlim(-0.2, max(kept_all) + 0.8)

    fig.suptitle(obj["title_prefix"].replace("_", " "), y=1.02, fontsize=16, fontweight="semibold")
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")
    add_panel_tag(axes[2], "C")
    finish_figure(fig, output_dir / f"{json_path.stem}.png")


def plot_aggregation_comparison(table_dir: Path, output_dir: Path) -> None:
    obj = load_json(table_dir / TABLE_FILES["aggregation"])
    preferred_order = ["hierarchical", "mean", "median", "krum"]
    rows = sorted(obj["rows"], key=lambda r: preferred_order.index(str(r["aggregation"])))
    y = np.arange(len(rows))[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.6), sharey=True)
    for ax, metric_key, std_key, title, higher_better in [
        (axes[0], "test_f1_mean", "test_f1_std", "Test F1", True),
        (axes[1], "test_fpr_mean", "test_fpr_std", "Test FPR", False),
    ]:
        for yi, row in zip(y, rows):
            color = NAVY if row["aggregation"] == "hierarchical" else (TEAL if row["aggregation"] == "mean" else SLATE)
            value = float(row[metric_key])
            err = ci95(float(row[std_key]), int(row["n"]))
            ax.errorbar(value, yi, xerr=err, fmt="o", color=color, markersize=7, capsize=3, linewidth=1.2)
            ax.plot([0, value], [yi, yi], color=color, alpha=0.18, linewidth=3.0)
        ax.set_title(title, fontsize=13.5, pad=8)
        ax.grid(axis="x")
        ax.set_facecolor(SOFT_BG)
        hint = "Higher is better" if higher_better else "Lower is better"
        ax.text(0.98, 1.02, hint, transform=ax.transAxes, ha="right", va="bottom", fontsize=9.3, color="#475569")
    axes[0].set_yticks(y, [pretty_label(r["aggregation"]) for r in rows])
    axes[0].set_xlim(0.972, 0.9825)
    axes[1].set_xlim(0.0, 0.055)
    axes[0].set_xlabel("Mean ±95% CI")
    axes[1].set_xlabel("Mean ±95% CI")
    fig.suptitle("Aggregators under Sign-flip@0.4", y=1.02, fontsize=16, fontweight="semibold")
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")
    finish_figure(fig, output_dir / "aggregation_sign_flip_comparison.png")


def plot_min_keep_sensitivity(table_dir: Path, output_dir: Path) -> None:
    obj = load_json(table_dir / TABLE_FILES["min_keep"])
    conditions = ["clean", "sign_flip_frac0p4", "update_noise_frac0p4"]
    colors = {"clean": NAVY, "sign_flip_frac0p4": AMBER, "update_noise_frac0p4": TEAL}
    data = {cond: sorted([r for r in obj["rows"] if r["condition"] == cond], key=lambda x: int(x["min_keep_per_group"])) for cond in conditions}

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.6), sharex=True)
    metrics = [
        ("test_f1", "Test F1"),
        ("test_fpr", "Test FPR"),
        ("kept_poisoned_clients", "Retained poisoned clients"),
    ]
    for ax, (metric, title) in zip(axes, metrics):
        ax.axvspan(0.88, 1.12, color="#E2E8F0", alpha=0.65, zorder=0)
        for cond in conditions:
            xs = [int(r["min_keep_per_group"]) for r in data[cond]]
            ys = [float(r[metric]) for r in data[cond]]
            ax.plot(xs, ys, color=colors[cond], marker="o", linewidth=2.1, markersize=6.5, label=shorten_condition(cond))
        ax.set_title(title, fontsize=13.5, pad=8)
        ax.grid(axis="y")
        ax.set_facecolor(SOFT_BG)
        ax.set_xticks([0, 1, 2])
        ax.set_xlabel("min_keep_per_group")
        ax.text(1.0, 0.03 if metric != "test_f1" else 0.97, "default", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=9.0, color="#475569")
    axes[0].set_ylim(0.9662, 0.9715)
    axes[1].set_ylim(0.05, 0.0955)
    axes[2].set_ylim(-0.05, 4.25)
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")
    add_panel_tag(axes[2], "C")
    legend_handles = [
        Line2D([0], [0], color=colors["clean"], marker="o", linewidth=2.1, markersize=6.5, label="Clean"),
        Line2D([0], [0], color=colors["sign_flip_frac0p4"], marker="o", linewidth=2.1, markersize=6.5, label="Sign-flip@0.4"),
        Line2D([0], [0], color=colors["update_noise_frac0p4"], marker="o", linewidth=2.1, markersize=6.5, label="Update-noise@0.4"),
    ]
    fig.legend(handles=legend_handles, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Group-floor sensitivity and the static default", y=1.06, fontsize=15.5, fontweight="semibold")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(output_dir / "min_keep_per_group_sensitivity.png", dpi=320)
    plt.close(fig)


def plot_public_baseline(json_path: Path, output_dir: Path) -> None:
    obj = load_json(json_path)
    rows = obj["rows"][::-1]
    y = np.arange(len(rows))
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 5.0), sharey=True)
    metrics = [
        ("test_f1_mean", "test_f1_std", "Test F1", True),
        ("test_fpr_mean", "test_fpr_std", "Test FPR", False),
        ("kept_poisoned_clients_mean", None, "Retained poisoned", False),
    ]
    for ax, (metric_key, std_key, title, higher_better) in zip(axes, metrics):
        for yi, row in zip(y, rows):
            label = row["label"]
            color = TEAL if label == obj["reference"] else (RUST if label == "hier_keepall" else SLATE)
            value = float(row[metric_key])
            err = ci95(float(row[std_key]), int(row["n"])) if std_key is not None else 0.0
            ax.errorbar(value, yi, xerr=err, fmt="D" if label == obj["reference"] else "o", color=color, markersize=7, capsize=3, linewidth=1.2)
            ax.plot([0, value], [yi, yi], color=color, alpha=0.18, linewidth=3.0)
            if metric_key == "test_f1_mean" and row.get("f1_p_value_vs_reference") is not None:
                ax.text(value + 0.003, yi + 0.08, f"p={row['f1_p_value_vs_reference']:.3f}", fontsize=8.5, color="#475569")
        ax.set_title(title, fontsize=13.2, pad=8)
        ax.grid(axis="x")
        ax.set_facecolor(SOFT_BG)
        if "Retained poisoned" not in title:
            hint = "Higher is better" if higher_better else "Lower is better"
            ax.text(0.98, 1.015, hint, transform=ax.transAxes, ha="right", va="bottom", fontsize=9.3, color="#475569")
    axes[0].set_yticks(y, [pretty_label(r["label"]) for r in rows])
    axes[0].set_xlim(0.73, 0.81)
    axes[1].set_xlim(0.03, 0.10)
    axes[2].set_xlim(0.0, 4.4)
    add_panel_tag(axes[0], "A")
    add_panel_tag(axes[1], "B")
    add_panel_tag(axes[2], "C")
    fig.suptitle("Public NSL-KDD: harder baseline comparison", y=1.02, fontsize=16, fontweight="semibold")
    finish_figure(fig, output_dir / f"{json_path.stem}.png")


def maybe_copy_tree(src: Path, dst: Path) -> None:
    if not dst.exists():
        ensure_dir(dst)
    for file in src.glob("*.png"):
        shutil.copy2(file, dst / file.name)


def main() -> None:
    apply_style()
    parser = argparse.ArgumentParser(description="Generate richer, paper-style figures for Cybersecurity draft.")
    parser.add_argument("--table-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mirror-dir", default="")
    args = parser.parse_args()

    table_dir = Path(args.table_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)

    plot_cross_scenario_heatmap(table_dir, output_dir)
    plot_backbone_comparison(table_dir, output_dir)
    plot_comm_tradeoff(table_dir, output_dir)
    plot_aggregation_comparison(table_dir, output_dir)
    plot_min_keep_sensitivity(table_dir, output_dir)

    for key in ["scenario_h_trust", "scenario_e_trust", "public_trust"]:
        plot_trust_vs_keepall(table_dir / TABLE_FILES[key], output_dir)

    for key in [
        "scenario_h_condfloor_clean",
        "scenario_h_condfloor_sign",
        "scenario_h_condfloor_noise",
        "scenario_e_condfloor_noise",
        "public_condfloor_noise",
    ]:
        plot_condfloor_comparison(table_dir / TABLE_FILES[key], output_dir)

    plot_public_baseline(table_dir / TABLE_FILES["public_baseline_noise"], output_dir)

    if str(args.mirror_dir).strip():
        maybe_copy_tree(output_dir, Path(args.mirror_dir).resolve())

    print(f"[OK] wrote richer figures to {output_dir}")


if __name__ == "__main__":
    main()
