from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArtifactReleaseTests(unittest.TestCase):
    def test_release_status_files_exist(self) -> None:
        required = [
            ROOT / "docs" / "ARTIFACT_STATUS_20260326.md",
            ROOT / "docs" / "EXPERIMENT_DESIGN_CONTRACT_20260407.md",
            ROOT / "docs" / "reviewer_bundle_sha256_20260326.txt",
            ROOT / "core_experiments" / "reproduce" / "generate_reviewer_checksums.sh",
            ROOT / "core_experiments" / "reproduce" / "verify_artifact_bundle.sh",
            ROOT / "core_experiments" / "reproduce" / "package_reviewer_release.sh",
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))

    def test_artifact_manifest_paths_exist(self) -> None:
        manifest = json.loads(
            (ROOT / "paper_hitrust" / "artifact_manifest_20260324.json").read_text(encoding="utf-8")
        )
        refs: list[str] = []

        def walk(obj: object) -> None:
            if isinstance(obj, dict):
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)
            elif isinstance(obj, str) and ("/" in obj or obj.endswith((".json", ".png", ".pt", ".sh", ".md", ".yml", ".txt"))):
                refs.append(obj)

        walk(manifest)
        self.assertGreater(len(refs), 10)
        for ref in refs:
            self.assertTrue((ROOT / ref).exists(), ref)

    def test_checksum_manifest_points_to_existing_files(self) -> None:
        manifest_path = ROOT / "docs" / "reviewer_bundle_sha256_20260326.txt"
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(lines), 20)

        for line in lines:
            checksum, relpath = line.split("  ", 1)
            self.assertEqual(len(checksum), 64)
            self.assertTrue((ROOT / relpath).exists(), relpath)

    def test_release_boundary_is_explicit(self) -> None:
        text = (ROOT / "docs" / "ARTIFACT_STATUS_20260326.md").read_text(encoding="utf-8").lower()
        self.assertIn("not supported", text)
        self.assertIn("private raw", text)
        self.assertIn("derived graphs", text)


if __name__ == "__main__":
    unittest.main()
