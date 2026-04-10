from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = ROOT / "core_experiments" / "internal"
sys.path.insert(0, str(INTERNAL))

from attack_injection import mark_poisoned_clients  # noqa: E402
from build_no_trust_baseline_report import build_condition_row  # noqa: E402
from experiment_registry import PRIMARY_SEEDS_20, build_experiment_contract  # noqa: E402
from run_real_fed_pilot import (  # noqa: E402
    aggregate_foolsgold_official,
    aggregate_fltrust_like,
    build_adaptive_alie_like_attack,
    build_targeted_label_flip_labels,
    build_client_views,
    build_server_root_mask,
    compute_foolsgold_weights,
    is_adaptive_attack_type,
    load_config,
    select_kept_clients,
)
from hierarchical_aggregation import aggregate_caf, aggregate_centered_clipping, aggregate_rfa_geometric_median, preaggregate_arc  # noqa: E402
from stats_contract import correct_p_values  # noqa: E402


class RiskFixTests(unittest.TestCase):
    def test_load_config_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            payload = {"run_name": "bom_ok", "seed": 7}
            path.write_text(json.dumps(payload), encoding="utf-8-sig")
            self.assertEqual(load_config(path), payload)

    def test_mark_poisoned_clients_is_seeded_and_varies_by_seed(self) -> None:
        picked_a = mark_poisoned_clients(10, 0.5, seed=1)
        picked_b = mark_poisoned_clients(10, 0.5, seed=1)
        picked_c = mark_poisoned_clients(10, 0.5, seed=2)
        self.assertEqual(picked_a, picked_b)
        self.assertEqual(len(picked_a), 5)
        self.assertNotEqual(picked_a, picked_c)

    def test_build_client_views_is_local_and_manifest_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "arena_manifest_v2.json"
            manifest = {
                "topology": {"type": "three_tier"},
                "run_config": {"load_profile": "high", "bot_type_mode": "mixed"},
                "ip_labels": {
                    "10.0.0.10": 0,
                    "10.0.0.30": 1,
                },
                "roles": {
                    "10.0.0.10": "benign_user",
                    "10.0.0.30": "bot:mimic",
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            graph = SimpleNamespace(
                x_norm=torch.randn(5, 3),
                y=torch.tensor([0, 0, 0, 1, 1], dtype=torch.long),
                edge_index=torch.tensor([[1, 2, 3, 4], [0, 0, 0, 0]], dtype=torch.long),
                ip_idx=torch.tensor([-1, 0, 0, 1, 1], dtype=torch.long),
                window_idx=torch.tensor([-1, 0, 1, 0, 1], dtype=torch.long),
                source_ips=["10.0.0.10", "10.0.0.30"],
                manifest_file=str(manifest_path),
                num_nodes=5,
            )
            train_mask = torch.tensor([False, True, True, True, True], dtype=torch.bool)
            val_mask = torch.zeros(5, dtype=torch.bool)
            test_mask = torch.zeros(5, dtype=torch.bool)

            views, manifest_obj = build_client_views(
                graph=graph,
                train_mask=train_mask,
                val_mask=val_mask,
                test_mask=test_mask,
                num_clients=2,
                partition_mode="topology_noniid",
                seed=42,
                num_groups=2,
            )

            self.assertEqual(views[0]["global_node_ids"].tolist(), [0, 1, 2])
            self.assertEqual(views[1]["global_node_ids"].tolist(), [0, 3, 4])
            self.assertEqual(manifest_obj["manifest_file"], str(manifest_path))
            self.assertEqual(manifest_obj["clients"][0]["owned_ips"], ["10.0.0.10"])
            self.assertEqual(manifest_obj["clients"][1]["owned_ips"], ["10.0.0.30"])
            self.assertNotEqual(manifest_obj["clients"][0]["group_name"], "group_0")
            self.assertIn("role_counts", manifest_obj["clients"][0])

    def test_select_kept_clients_can_preserve_group_coverage(self) -> None:
        rows = [
            {"client_id": 0, "group": "role:benign_user", "trust_norm": 0.10, "val_f1": 0.96, "update_norm": 0.50},
            {"client_id": 1, "group": "role:benign_user", "trust_norm": 0.12, "val_f1": 0.95, "update_norm": 0.52},
            {"client_id": 2, "group": "role:bot:mimic", "trust_norm": 0.90, "val_f1": 0.94, "update_norm": 0.48},
            {"client_id": 3, "group": "role:bot:mimic", "trust_norm": 0.80, "val_f1": 0.93, "update_norm": 0.47},
        ]

        keep_default, _ = select_kept_clients(rows, trust_threshold=0.35, min_keep_per_group=0)
        self.assertFalse(keep_default[0])
        self.assertFalse(keep_default[1])
        self.assertTrue(keep_default[2])
        self.assertTrue(keep_default[3])

        keep_group_floor, _ = select_kept_clients(rows, trust_threshold=0.35, min_keep_per_group=1)
        self.assertFalse(keep_group_floor[0])
        self.assertTrue(keep_group_floor[1])
        self.assertTrue(keep_group_floor[2])
        self.assertTrue(keep_group_floor[3])

    def test_build_server_root_mask_can_balance_labels(self) -> None:
        train_mask = torch.tensor([True, True, True, True, True, True], dtype=torch.bool)
        y = torch.tensor([1, 1, 1, 0, 0, 0], dtype=torch.long)

        root_mask = build_server_root_mask(
            train_mask=train_mask,
            y=y,
            root_size=4,
            seed=7,
            selection="balanced_label",
        )

        self.assertEqual(int(root_mask.sum().item()), 4)
        self.assertEqual(int((y[root_mask] == 1).sum().item()), 2)
        self.assertEqual(int((y[root_mask] == 0).sum().item()), 2)

    def test_aggregate_fltrust_like_rejects_negative_alignment(self) -> None:
        global_update, diagnostics, mode = aggregate_fltrust_like(
            local_updates={
                0: torch.tensor([1.0, 0.0], dtype=torch.float64).numpy(),
                1: torch.tensor([-1.0, 0.0], dtype=torch.float64).numpy(),
            },
            server_update=torch.tensor([2.0, 0.0], dtype=torch.float64).numpy(),
        )

        self.assertEqual(mode, "trusted_clients")
        self.assertAlmostEqual(float(diagnostics[0]["trust_weight"]), 1.0, places=6)
        self.assertAlmostEqual(float(diagnostics[1]["trust_weight"]), 0.0, places=6)
        self.assertAlmostEqual(float(global_update[0]), 2.0, places=6)
        self.assertAlmostEqual(float(global_update[1]), 0.0, places=6)

    def test_compute_foolsgold_weights_downweights_sybil_pair(self) -> None:
        history_stack = np.asarray(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.8, 0.8, 0.0],
                [0.8, 0.8, 0.0],
            ],
            dtype=np.float64,
        )

        weights, pardoned = compute_foolsgold_weights(history_stack)

        self.assertEqual(weights.shape, (4,))
        self.assertEqual(pardoned.shape, (4, 4))
        self.assertGreater(float(weights[0]), 0.0)
        self.assertGreater(float(weights[1]), 0.0)
        self.assertLess(float(weights[2]), 1e-6)
        self.assertLess(float(weights[3]), 1e-6)

    def test_aggregate_foolsgold_official_uses_history_weighting(self) -> None:
        local_updates = {
            0: np.asarray([1.0, 0.0], dtype=np.float64),
            1: np.asarray([0.0, 1.0], dtype=np.float64),
            2: np.asarray([0.9, 0.9], dtype=np.float64),
            3: np.asarray([0.9, 0.9], dtype=np.float64),
        }
        history_updates = {
            0: np.asarray([3.0, 0.0], dtype=np.float64),
            1: np.asarray([0.0, 3.0], dtype=np.float64),
            2: np.asarray([2.7, 2.7], dtype=np.float64),
            3: np.asarray([2.7, 2.7], dtype=np.float64),
        }

        global_update, diagnostics, mode = aggregate_foolsgold_official(
            local_updates=local_updates,
            history_updates=history_updates,
        )

        self.assertEqual(mode, "history_weighted")
        self.assertGreater(float(diagnostics[0]["trust_weight"]), 0.0)
        self.assertGreater(float(diagnostics[1]["trust_weight"]), 0.0)
        self.assertLess(float(diagnostics[2]["trust_weight"]), 1e-6)
        self.assertLess(float(diagnostics[3]["trust_weight"]), 1e-6)
        self.assertAlmostEqual(float(global_update[0]), 1.0, places=6)
        self.assertAlmostEqual(float(global_update[1]), 1.0, places=6)

    def test_aggregate_rfa_geometric_median_downweights_outlier(self) -> None:
        updates = [
            np.asarray([0.0, 0.0], dtype=np.float64),
            np.asarray([0.1, -0.1], dtype=np.float64),
            np.asarray([-0.1, 0.1], dtype=np.float64),
            np.asarray([10.0, 10.0], dtype=np.float64),
        ]
        global_update = aggregate_rfa_geometric_median(updates)

        self.assertLess(float(np.linalg.norm(global_update)), 0.5)
        self.assertLess(float(np.linalg.norm(global_update - updates[0])), 0.5)

    def test_aggregate_centered_clipping_clips_far_outlier(self) -> None:
        updates = [
            np.asarray([0.0, 0.0], dtype=np.float64),
            np.asarray([0.1, -0.1], dtype=np.float64),
            np.asarray([-0.1, 0.1], dtype=np.float64),
            np.asarray([10.0, 10.0], dtype=np.float64),
        ]
        global_update = aggregate_centered_clipping(
            updates,
            clip_radius=0.5,
            num_iterations=10,
        )

        self.assertLess(float(np.linalg.norm(global_update)), 1.0)
        self.assertLess(float(np.linalg.norm(global_update - updates[0])), 1.0)

    def test_aggregate_caf_downweights_far_outlier(self) -> None:
        updates = [
            np.asarray([0.0, 0.0], dtype=np.float64),
            np.asarray([0.1, -0.1], dtype=np.float64),
            np.asarray([-0.1, 0.1], dtype=np.float64),
            np.asarray([10.0, 10.0], dtype=np.float64),
        ]
        global_update = aggregate_caf(
            updates,
            f=1,
            max_iter=4,
            power_max_iter=2,
        )

        self.assertLess(float(np.linalg.norm(global_update)), 1.0)
        self.assertLess(float(np.linalg.norm(global_update - updates[0])), 1.0)

    def test_preaggregate_arc_clips_only_largest_norms(self) -> None:
        updates = [
            np.asarray([1.0, 0.0], dtype=np.float64),
            np.asarray([2.0, 0.0], dtype=np.float64),
            np.asarray([10.0, 0.0], dtype=np.float64),
        ]
        clipped, diagnostics = preaggregate_arc(updates, f=1)

        self.assertEqual(diagnostics["faulty_budget"], 1)
        self.assertEqual(diagnostics["num_clipped"], 1)
        self.assertAlmostEqual(float(diagnostics["clipping_threshold"]), 2.0, places=6)
        self.assertTrue(np.allclose(clipped[0], updates[0]))
        self.assertTrue(np.allclose(clipped[1], updates[1]))
        self.assertTrue(np.allclose(clipped[2], np.asarray([2.0, 0.0], dtype=np.float64)))

    def test_is_adaptive_attack_type_includes_adaptive_alie_like(self) -> None:
        self.assertTrue(is_adaptive_attack_type("adaptive_benign_mimic"))
        self.assertTrue(is_adaptive_attack_type("adaptive_alie_like"))
        self.assertTrue(is_adaptive_attack_type("multi_round_stealth"))
        self.assertFalse(is_adaptive_attack_type("update_noise"))

    def test_build_targeted_label_flip_labels_prefers_positive_examples(self) -> None:
        y = torch.tensor([0, 1, 1, 0, 1], dtype=torch.long)
        mask = torch.tensor([False, True, True, False, True], dtype=torch.bool)
        flipped = build_targeted_label_flip_labels(
            y=y,
            mask=mask,
            attack_scale=1.0,
            rng=np.random.default_rng(7),
        )

        self.assertEqual(int(flipped[1].item()), 0)
        self.assertEqual(int(flipped[2].item()), 0)
        self.assertEqual(int(flipped[4].item()), 0)
        self.assertEqual(int(flipped[0].item()), 0)

    def test_experiment_contract_marks_public_same_task_as_primary(self) -> None:
        cfg = {
            "run_name": "public_cabench_scenario_h_fltrust_like_sage_update_noise_frac0p4",
            "aggregation": "fltrust_like",
            "poison_type": "update_noise",
        }
        dataset_info = {
            "dataset_name": "Ca-Bench",
            "dataset_variant": "scenario_h_public_data_v1",
            "dataset_source": "github_release:1251408860-oss/Ca-Bench@data-v1",
            "graph_source_kind": "external_public_dataset",
        }

        contract = build_experiment_contract(
            cfg=cfg,
            dataset_info=dataset_info,
            graph_file="data_hitrust/public_benchmarks/cabench_v1/graphs/cabench_scenario_h_public_graph.pt",
            run_name=cfg["run_name"],
        )

        self.assertEqual(contract["method"]["method_key"], "fltrust_like")
        self.assertEqual(contract["method"]["method_family"], "task_adapted_baseline")
        self.assertEqual(contract["benchmark"]["benchmark_key"], "public_cabench_scenario_h")
        self.assertEqual(contract["stats_plan"]["family"], "primary")
        self.assertEqual(contract["stats_plan"]["recommended_seed_count"], len(PRIMARY_SEEDS_20))

    def test_experiment_contract_marks_nslkdd_as_exploratory(self) -> None:
        cfg = {
            "run_name": "public_nslkdd_hierarchical_sage_update_noise_frac0p4",
            "aggregation": "hierarchical",
            "poison_type": "update_noise",
            "trust_threshold": 0.35,
        }
        dataset_info = {
            "dataset_name": "NSL-KDD",
            "dataset_variant": "train20_test_public_graph",
            "dataset_source": "public_github_mirror:defcom17/NSL_KDD",
            "graph_source_kind": "external_public_dataset",
        }

        contract = build_experiment_contract(
            cfg=cfg,
            dataset_info=dataset_info,
            graph_file="data_hitrust/public_benchmarks/nsl_kdd/graphs/nsl_kdd_public_graph.pt",
            run_name=cfg["run_name"],
        )

        self.assertEqual(contract["method"]["method_key"], "hitrust_static")
        self.assertEqual(contract["benchmark"]["benchmark_key"], "public_nslkdd")
        self.assertEqual(contract["stats_plan"]["family"], "exploratory")
        self.assertEqual(contract["stats_plan"]["correction_method"], "bh_fdr")

    def test_holm_correction_is_monotone_and_bounded(self) -> None:
        corrected = correct_p_values([0.01, 0.02, 0.2], "holm_bonferroni")
        self.assertEqual(len(corrected), 3)
        self.assertGreaterEqual(float(corrected[0]), 0.01)
        self.assertGreaterEqual(float(corrected[1]), float(corrected[0]))
        self.assertLessEqual(float(corrected[2]), 1.0)

    def test_build_condition_row_uses_matched_seed_paired_test(self) -> None:
        trust_obj = {
            "rows": [
                {"run_name": "trust_seed22", "test_f1": 0.91, "test_fpr": 0.05},
                {"run_name": "trust_seed11", "test_f1": 0.80, "test_fpr": 0.07},
                {"run_name": "trust_seed33", "test_f1": 0.50, "test_fpr": 0.20},
            ],
            "stats": {
                "test_f1": {"mean": 0.7366666666666667, "std": 0.2159475249020514, "n": 3},
                "test_fpr": {"mean": 0.10666666666666667, "std": 0.08137703743892898, "n": 3},
                "kept_clients": {"mean": 6.0, "std": 1.0, "n": 3},
                "kept_poisoned_clients": {"mean": 0.5, "std": 0.5, "n": 3},
            },
        }
        keepall_obj = {
            "rows": [
                {"run_name": "keepall_seed11", "test_f1": 0.10, "test_fpr": 0.15},
                {"run_name": "keepall_seed22", "test_f1": 0.26, "test_fpr": 0.14},
                {"run_name": "keepall_seed44", "test_f1": 0.99, "test_fpr": 0.01},
            ],
            "stats": {
                "test_f1": {"mean": 0.45, "std": 0.4709922167966118, "n": 3},
                "test_fpr": {"mean": 0.1, "std": 0.07810249675906655, "n": 3},
                "kept_clients": {"mean": 10.0, "std": 0.0, "n": 3},
                "kept_poisoned_clients": {"mean": 4.0, "std": 0.0, "n": 3},
            },
        }

        row = build_condition_row("update_noise_frac0p4", trust_obj, keepall_obj)

        self.assertEqual(row["f1_test_type_trust_vs_keepall"], "paired_ttest")
        self.assertEqual(row["f1_paired_n_trust_vs_keepall"], 2)
        self.assertAlmostEqual(row["f1_sign_flip_p_value_trust_vs_keepall"], 0.5, places=6)
        self.assertIsNotNone(row["f1_t_stat_trust_vs_keepall"])
        self.assertIsNotNone(row["f1_p_value_trust_vs_keepall"])
        self.assertGreater(float(row["f1_t_stat_trust_vs_keepall"]), 0.0)
        self.assertLess(float(row["f1_p_value_trust_vs_keepall"]), 0.1)

    def test_build_adaptive_alie_like_attack_is_coordinated(self) -> None:
        local_updates = {
            0: np.asarray([1.00, 0.70, -0.50], dtype=np.float64),
            1: np.asarray([0.92, 0.65, -0.46], dtype=np.float64),
            2: np.asarray([1.06, 0.76, -0.54], dtype=np.float64),
            3: np.asarray([0.22, -0.82, 0.35], dtype=np.float64),
            4: np.asarray([0.18, -0.75, 0.40], dtype=np.float64),
        }
        poisoned_clients = {3, 4}
        attacked = build_adaptive_alie_like_attack(
            local_updates=local_updates,
            poisoned_clients=poisoned_clients,
            attack_scale=0.2,
            rng=np.random.default_rng(7),
        )

        clean_stack = np.stack([local_updates[cid] for cid in [0, 1, 2]], axis=0)
        clean_mean = np.mean(clean_stack, axis=0)
        clean_std = np.std(clean_stack, axis=0, ddof=0)
        harmful_sign = np.sign(-np.mean(np.stack([local_updates[3], local_updates[4]], axis=0), axis=0))

        self.assertTrue(np.allclose(attacked[0], local_updates[0]))
        self.assertTrue(np.allclose(attacked[1], local_updates[1]))
        self.assertTrue(np.allclose(attacked[2], local_updates[2]))
        for cid in poisoned_clients:
            self.assertFalse(np.allclose(attacked[cid], local_updates[cid]))
            self.assertTrue(np.all(np.abs(attacked[cid] - clean_mean) <= 0.9 * clean_std + 1e-8))
            self.assertTrue(np.all(np.sign(attacked[cid] - clean_mean) == harmful_sign))

        poisoned_cosine = float(
            np.dot(attacked[3], attacked[4])
            / max(np.linalg.norm(attacked[3]) * np.linalg.norm(attacked[4]), 1e-12)
        )
        self.assertGreater(poisoned_cosine, 0.999)


if __name__ == "__main__":
    unittest.main()
