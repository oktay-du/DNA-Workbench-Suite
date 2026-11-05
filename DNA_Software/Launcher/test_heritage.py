import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import heritage


class HeritageTests(unittest.TestCase):
    def test_catalog_many_places_and_original_summaries(self):
        data = heritage.catalog()
        self.assertGreater(len(data["places"]), 200)
        self.assertGreater(sum(p["curated"] for p in data["places"]), 50)
        de = next(p for p in data["places"] if p["id"] == "de")
        self.assertIn("half-timbered", de["architecture"])
        self.assertTrue(de["photos"])

    def test_photos_have_visible_credit_metadata_and_safe_paths(self):
        for place in heritage.catalog()["places"]:
            for photo in place["photos"]:
                for key in [
                    "author",
                    "license",
                    "license_url",
                    "source",
                    "sha256",
                    "caption",
                ]:
                    self.assertTrue(photo[key])
                self.assertTrue(heritage.photo_path(photo["id"]).is_file())

    def test_traversal_not_a_photo(self):
        for name in ["../family.sqlite", "de-castle/../x", "C:\\x", "unknown"]:
            with self.assertRaises(ValueError):
                heritage.photo_path(name)

    def test_no_result_is_pending_not_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = heritage.statuses([{"id": "P001_Test"}], [], Path(tmp))[
                "P001_Test"
            ]["ancestry"]
            self.assertEqual(state["state"], "pending")
            self.assertEqual(state["label"], "Still in progress")
            self.assertIn("no ongoing", state["detail"])

    def test_trait_only_does_not_complete_ancestry(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = heritage.statuses(
                [{"id": "P001_Test"}],
                [
                    {
                        "person": "P001_Test",
                        "data": {"traits": {"eyes": {}}, "regions": []},
                    }
                ],
                Path(tmp),
            )["P001_Test"]
            self.assertEqual(state["ancestry"]["state"], "pending")
            self.assertEqual(state["traits"]["state"], "available")

    def test_result_for_other_person_does_not_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = [
                {
                    "person": "OTHER",
                    "data": {"regions": [{"name": "DE", "percent": 100}]},
                }
            ]
            state = heritage.statuses([{"id": "P001_Test"}], result, Path(tmp))[
                "P001_Test"
            ]["ancestry"]
            self.assertEqual(state["state"], "pending")

    def test_stale_job_not_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Projects/Launcher/P001_Test/a/status.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps({"task": "rfmix", "status": "Running", "pid": 12345})
            )
            with patch.object(heritage, "process_alive", return_value=False):
                self.assertEqual(
                    heritage.statuses([{"id": "P001_Test"}], [], Path(tmp))[
                        "P001_Test"
                    ]["ancestry"]["state"],
                    "pending",
                )

    def test_active_job_is_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Projects/Launcher/P001_Test/a/status.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps({"task": "rfmix", "status": "Running", "pid": 12345})
            )
            with patch.object(heritage, "process_alive", return_value=True):
                self.assertEqual(
                    heritage.statuses([{"id": "P001_Test"}], [], Path(tmp))[
                        "P001_Test"
                    ]["ancestry"]["state"],
                    "running",
                )


if __name__ == "__main__":
    unittest.main()
