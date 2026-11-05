# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Required Notice: Copyright 2026 Oktay Du / OD — DNA Workbench
import tempfile, unittest, hashlib
from pathlib import Path
from unittest.mock import patch
import optional_assets as a


class AssetTests(unittest.TestCase):
    def test_rights_review_is_required_before_accessing_any_file(self):
        with patch.object(a, "plan", side_effect=AssertionError("No consent")):
            with self.assertRaises(ValueError):
                a.stage({"rights_reviewed": False})

    def test_known_hash_move_is_verified_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "ROOT", Path(tmp)):
            root = Path(tmp)
            src = root / "obtained.zip"
            src.write_bytes(b"synthetic installer bytes")
            dest = root / "Downloads/asset.zip"
            row = {
                "id": "asset",
                "expected_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                "cache_path": str(dest),
                "staging_folder": str(root / "manual"),
                "license": "Test only",
            }
            with patch.object(a, "plan", return_value=row):
                r = a.stage(
                    {
                        "asset": "asset",
                        "file": str(src),
                        "mode": "move",
                        "rights_reviewed": True,
                    }
                )
            self.assertFalse(src.exists())
            self.assertTrue(dest.exists())
            self.assertFalse(r["installed"])
            self.assertFalse(r["executed"])

    def test_mismatch_preserves_source_and_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "ROOT", Path(tmp)):
            src = Path(tmp) / "input"
            src.write_bytes(b"different")
            dest = Path(tmp) / "cache"
            dest.write_bytes(b"existing")
            with patch.object(a, "plan", return_value={"expected_sha256": "0" * 64}):
                with self.assertRaises(ValueError):
                    a.stage(
                        {
                            "asset": "asset",
                            "file": str(src),
                            "mode": "move",
                            "rights_reviewed": True,
                        }
                    )
            self.assertEqual(src.read_bytes(), b"different")
            self.assertEqual(dest.read_bytes(), b"existing")

    def test_unknown_hash_is_quarantined_not_registered_as_installed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "ROOT", Path(tmp)):
            root = Path(tmp)
            src = root / "unknown.exe"
            src.write_bytes(b"not executable")
            row = {
                "id": "asset",
                "expected_sha256": None,
                "staging_folder": str(root / "manual"),
                "license": "Unknown",
            }
            with patch.object(a, "plan", return_value=row):
                r = a.stage(
                    {
                        "asset": "asset",
                        "file": str(src),
                        "mode": "copy",
                        "rights_reviewed": True,
                    }
                )
            self.assertTrue(src.exists())
            self.assertTrue(Path(r["path"]).is_relative_to(root / "manual"))
            self.assertFalse(r["executed"])

    def test_asset_ids_cannot_define_unregistered_paths(self):
        with self.assertRaises(ValueError):
            a.plan("../outside")
