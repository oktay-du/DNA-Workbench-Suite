import time
import unittest

import command_bus
import suite_api


class MenuSnapshotTests(unittest.TestCase):
    def setUp(self):
        command_bus._DEFINITIONS = None
        command_bus._DEFINITIONS_TOKEN = None
        command_bus.REQUESTS.clear()

    def test_definitions_are_reused_until_the_catalog_changes(self):
        started = time.perf_counter()
        first = command_bus.definitions()
        built = time.perf_counter() - started
        started = time.perf_counter()
        second = command_bus.definitions()
        reused = time.perf_counter() - started
        self.assertIs(first, second)
        self.assertGreater(built, reused)
        self.assertLess(reused, 0.01)
        command_bus._DEFINITIONS_TOKEN = None
        third = command_bus.definitions()
        self.assertIsNot(third, first)
        self.assertEqual([item["id"] for item in first], [item["id"] for item in third])

    def test_snapshot_omits_an_unchanged_catalog(self):
        full = suite_api.snapshot()
        self.assertIn("catalog", full)
        self.assertTrue(full["catalog_token"])
        same = suite_api.snapshot(catalog_token=full["catalog_token"])
        self.assertNotIn("catalog", same)
        self.assertEqual(same["catalog_token"], full["catalog_token"])
        self.assertIn("people", same)
        self.assertIn("catalog", suite_api.snapshot(catalog_token="stale"))

    def test_repeat_snapshot_command_skips_schema_rebuild(self):
        command_bus.definitions()
        started = time.perf_counter()
        result = command_bus.execute("workspace.snapshot", {})["result"]
        self.assertLess(time.perf_counter() - started, 0.5)
        self.assertIn("catalog", result)
        slim = command_bus.execute(
            "workspace.snapshot",
            {"catalog_token": result["catalog_token"]},
        )["result"]
        self.assertNotIn("catalog", slim)
        self.assertEqual(slim["people"], result["people"])


if __name__ == "__main__":
    unittest.main()
