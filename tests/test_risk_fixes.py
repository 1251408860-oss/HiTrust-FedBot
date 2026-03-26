from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = ROOT / "core_experiments" / "internal"
sys.path.insert(0, str(INTERNAL))

from attack_injection import mark_poisoned_clients  # noqa: E402
from run_real_fed_pilot import build_client_views, load_config, select_kept_clients  # noqa: E402


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

        keep_default = select_kept_clients(rows, trust_threshold=0.35, min_keep_per_group=0)
        self.assertFalse(keep_default[0])
        self.assertFalse(keep_default[1])
        self.assertTrue(keep_default[2])
        self.assertTrue(keep_default[3])

        keep_group_floor = select_kept_clients(rows, trust_threshold=0.35, min_keep_per_group=1)
        self.assertFalse(keep_group_floor[0])
        self.assertTrue(keep_group_floor[1])
        self.assertTrue(keep_group_floor[2])
        self.assertTrue(keep_group_floor[3])


if __name__ == "__main__":
    unittest.main()
