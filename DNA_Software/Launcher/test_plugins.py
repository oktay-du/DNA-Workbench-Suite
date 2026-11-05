import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import plugin_hub as hub, visual_tools as visual, on_demand as demand


class PluginTests(unittest.TestCase):
    def test_unknown_project_cannot_run(self):
        with self.assertRaises(ValueError):
            hub.submit({"id": "discovery-arbitrary", "action": "install"})

    def test_restricted_license_checked_before_download(self):
        with patch.object(
            hub.network_io,
            "open_https",
            side_effect=AssertionError("Must not contact network"),
        ):
            with self.assertRaisesRegex(ValueError, "Stanford"):
                hub.archive("rfmix")

    def test_sources_not_executable_recipes(self):
        for row in hub.audit()["projects"]:
            self.assertNotIn("command", row)
            self.assertRegex(row["commit"], "^[a-f0-9]{40}$")
            self.assertNotEqual(row["id"], "vestige")

    def test_recipes_cover_selected_scientific_tools(self):
        for tool in ["peddy", "whatshap", "truvari", "nextflow", "sarek", "pgsc-calc"]:
            self.assertNotEqual(demand.TOOLS[tool][2], "manual")

    def test_visual_metadata_versions_and_not_vestige(self):
        for tool in ["pycirclize", "dnafeaturesviewer"]:
            self.assertEqual(visual.LOCK[tool]["kind"], "pip")
        self.assertFalse(any("vestige" in x["url"].lower() for x in visual.CURATED))

    def test_gff_labels_and_strand(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.gff"
            path.write_text(
                "1\tdemo\tgene\t10\t25\t.\t-\t.\tID=gene_a;Name=Example%20gene\n"
            )
            rows, _ = visual.records(path, "1", 1, 100)
            self.assertEqual(rows[0]["label"], "Example gene")
            self.assertEqual(rows[0]["strand"], -1)

    def test_busy_plugin_queue_does_not_duplicate_installs(self):
        with patch.dict(hub.ACTIVE, {"busy": {}}):
            with self.assertRaisesRegex(ValueError, "already"):
                hub.submit({"id": "peddy", "action": "probe"})

    def test_cached_source_hash_checked_before_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = hub.project("pycirclize")
            path = root / ("pycirclize-" + row["commit"] + ".zip")
            path.write_bytes(b"changed")
            with patch.object(hub, "SOURCES", root), patch.object(hub, "STATE", root):
                hub.atomic(
                    root / "source-pycirclize.json",
                    {"path": str(path), "sha256": "wrong"},
                )
                with self.assertRaisesRegex(ValueError, "checksum"):
                    hub.archive("pycirclize")


if __name__ == "__main__":
    unittest.main()
