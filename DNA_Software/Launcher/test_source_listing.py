import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import source_store, profile_pipeline


class SourceListingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patch = patch.object(source_store, "ROOT", self.root)
        self.patch.start()
        present = self.root / "Profiles/P1/present.txt"
        present.parent.mkdir(parents=True)
        present.write_text("synthetic", encoding="utf-8")
        db = source_store.connect("P1")
        db.execute(
            "INSERT INTO batches VALUES(?,?,?,?,?,?,?)",
            ("older", "synthetic", "older", "GRCh37", "Unknown", "", "2020-01-01"),
        )
        db.execute(
            "INSERT INTO batches VALUES(?,?,?,?,?,?,?)",
            ("newer", "synthetic", "newer", "GRCh38", "chip", "", "2024-01-01"),
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS file_annotations(file_id TEXT PRIMARY KEY,origin TEXT,lifecycle TEXT,payload TEXT,updated TEXT)"
        )
        rows = [
            ("keep", "newer", "bbbb", "b.txt", "Profiles/P1/present.txt", True),
            ("gone", "newer", "aaaa", "a.txt", "Profiles/P1/missing.txt", False),
            ("old", "older", "cccc", "z.txt", "Profiles/P1/old.txt", False),
            ("hidden", "newer", "dddd", "hidden.txt", "Profiles/P1/hidden.txt", False),
        ]
        for file_id, batch, sha, name, stored, _present in rows:
            db.execute(
                "INSERT INTO blobs VALUES(?,?,?,?,?,?)",
                (sha, stored, 4, "text", "", ""),
            )
            db.execute(
                "INSERT INTO files VALUES(?,?,?,?,?,?,?,?)",
                (file_id, batch, sha, name, name, "Non-indexed", 0, "t"),
            )
        db.execute(
            "INSERT INTO file_tombstones VALUES(?,?,?)",
            ("hidden", "t", "removed"),
        )
        db.execute(
            "INSERT INTO archive_payloads VALUES(?,?,?,?)",
            ("parent-sha", "keep", "member.txt", "t"),
        )
        db.execute(
            "INSERT INTO file_annotations VALUES(?,?,?,?,?)",
            (
                "keep",
                "compared",
                "reviewed",
                json.dumps(
                    {
                        "source": {"status": "analyzed", "called": 12, "stats": {}},
                        "comparisons": [{"status": "consistent"}],
                    }
                ),
                "t",
            ),
        )
        db.execute(
            "INSERT INTO inspections VALUES(?,?,?)",
            (
                "bbbb",
                json.dumps(
                    {
                        "build": "GRCh38",
                        "measurement": "chip",
                        "color": "green",
                        "verified": True,
                        "qc_supported_points": 9,
                        "called_points": 10,
                        "issues": ["note"],
                        "provider": "synthetic",
                        "producer": "fixture",
                        "profile": {},
                        "versions": ["1"],
                        "data_scope": {"summary": "synthetic scope"},
                        "x_called": 0,
                        "y_called": 0,
                        "x_heterozygous": 0,
                    }
                ),
                "t",
            ),
        )
        db.execute(
            "INSERT INTO source_metadata VALUES(?,?,?)",
            (
                "keep",
                json.dumps(
                    {
                        "declared_version": "v1",
                        "measurement": "chip",
                        "provenance": "user-declared",
                        "source_root_sha256": "root-sha",
                        "operation": "copy",
                    }
                ),
                "t",
            ),
        )
        db.commit()
        db.close()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_listing_keeps_annotations_order_and_tombstones(self):
        rows = source_store.listing("P1")
        self.assertEqual([row["id"] for row in rows], ["gone", "keep", "old"])
        keep = rows[1]
        self.assertTrue(keep["available"])
        self.assertFalse(rows[0]["available"])
        self.assertEqual(keep["container_member"], "member.txt")
        self.assertFalse(keep["independent_measurement"])
        self.assertEqual(keep["origin"], "compared")
        self.assertEqual(keep["lifecycle"], "reviewed")
        self.assertEqual(keep["comparison_status"], "SNP compliance supported")
        self.assertEqual(keep["called_points"], 12)
        self.assertIsNone(keep["qc_points"])
        self.assertEqual(keep["qc_color"], "green")
        self.assertTrue(keep["qc_verified"])
        self.assertEqual(keep["qc_issues"], "note")
        self.assertEqual(keep["detected_provider"], "synthetic")
        self.assertEqual(keep["profile"]["chromosomes"], "Undetermined")
        self.assertEqual(keep["declared_version"], "v1")
        self.assertEqual(keep["source_root_sha256"], "root-sha")
        self.assertEqual(keep["derived_operation"], "copy")
        self.assertEqual(keep["scope_summary"], "synthetic scope")
        self.assertEqual(keep["build"], "GRCh38")
        self.assertEqual(rows[2]["build"], "GRCh37")
        self.assertEqual(rows[2]["qc_color"], "orange")
        self.assertEqual(
            rows[2]["scope_summary"], "Not yet checked with the data scope check"
        )

    def test_summary_reuses_a_listing_it_was_given(self):
        rows = source_store.listing("P1")
        with patch.object(
            source_store, "listing", side_effect=AssertionError("listed again")
        ):
            state = profile_pipeline.summary("P1", rows)
        self.assertEqual(state["sets"], [])
        self.assertEqual(state["refresh"], {})


if __name__ == "__main__":
    unittest.main()
