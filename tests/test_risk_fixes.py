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
from run_real_fed_pilot import (  # noqa: E402
    aggregate_foolsgold_official,
    aggregate_fltrust_like,
    build_adaptive_alie_like_attack,
    build_client_views,
    build_server_root_mask,
    compute_foolsgold_weights,
    is_adaptive_attack_type,
    load_config,
    select_kept_clients,
)


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

    def test_is_adaptive_attack_type_includes_adaptive_alie_like(self) -> None:
        self.assertTrue(is_adaptive_attack_type("adaptive_benign_mimic"))
        self.assertTrue(is_adaptive_attack_type("adaptive_alie_like"))
        self.assertFalse(is_adaptive_attack_type("update_noise"))

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
