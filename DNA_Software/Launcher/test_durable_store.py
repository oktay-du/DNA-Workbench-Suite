"""Fault injection for small portable state writes, not a filesystem certification.

Copyright 2026 Oktay Du / OD. PolyForm Noncommercial 1.0.0.
"""

from pathlib import Path
import concurrent.futures
import json
import tempfile
import unittest
from unittest.mock import patch

import durable_store


class DurableStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"
        durable_store.write(self.path, {"version": 1})

    def tearDown(self):
        self.tmp.cleanup()

    def test_failed_flush_or_replace_preserves_live_state(self):
        for target in ("fsync", "replace"):
            with patch.object(
                durable_store.os, target, side_effect=OSError("simulated disconnect")
            ):
                with self.assertRaises(OSError):
                    durable_store.write(self.path, {"version": 2})
            self.assertEqual(json.loads(self.path.read_text())["version"], 1)
            self.assertEqual(list(self.path.parent.glob("*.partial")), [])

    def test_transient_windows_reader_lock_is_retried(self):
        replace = durable_store.os.replace
        attempts = []

        def busy_then_replace(source, destination):
            attempts.append(destination)
            if len(attempts) < 3:
                raise PermissionError("Synthetic sharing violation")
            return replace(source, destination)

        with (
            patch.object(durable_store.os, "replace", side_effect=busy_then_replace),
            patch.object(durable_store.time, "sleep"),
        ):
            durable_store.write(self.path, {"version": 2})
        self.assertEqual(len(attempts), 3)
        self.assertEqual(json.loads(self.path.read_text())["version"], 2)
        self.assertEqual(list(self.path.parent.glob("*.partial")), [])

    def test_persistent_permission_denial_preserves_old_state_and_cleans_temp(self):
        with (
            patch.object(
                durable_store.os,
                "replace",
                side_effect=PermissionError("Synthetic ACL denial"),
            ) as replace,
            patch.object(durable_store.time, "sleep"),
        ):
            with self.assertRaises(PermissionError):
                durable_store.write(self.path, {"version": 2})
        self.assertEqual(replace.call_count, 7)
        self.assertEqual(json.loads(self.path.read_text())["version"], 1)
        self.assertEqual(list(self.path.parent.glob("*.partial")), [])

    def test_one_validated_backup_retained_and_identical_save_does_not_replace_it(self):
        durable_store.write(self.path, {"version": 2}, backup=True)
        backup = self.path.with_name("state.json.bak")
        self.assertEqual(json.loads(backup.read_text())["version"], 1)
        durable_store.write(self.path, {"version": 2}, backup=True)
        self.assertEqual(json.loads(backup.read_text())["version"], 1)
        durable_store.write(self.path, {"version": 3}, backup=True)
        self.assertEqual(json.loads(backup.read_text())["version"], 2)
        self.assertEqual(len(list(self.path.parent.glob("*.bak"))), 1)

    def test_nonfinite_data_and_corrupt_previous_state_are_not_silently_replaced(self):
        with self.assertRaises(ValueError):
            durable_store.write(self.path, {"value": float("nan")})
        self.path.write_text("truncated", encoding="utf-8")
        with self.assertRaises(ValueError):
            durable_store.write(self.path, {}, backup=True)
        self.assertEqual(self.path.read_text(), "truncated")

    def test_concurrent_threads_produce_complete_json(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            list(
                pool.map(
                    lambda x: durable_store.write(self.path, {"version": x}), range(25)
                )
            )
        self.assertIn(json.loads(self.path.read_text())["version"], range(25))
        self.assertEqual(list(self.path.parent.glob("*.partial")), [])


if __name__ == "__main__":
    unittest.main()
