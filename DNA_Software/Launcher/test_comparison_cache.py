import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
import family, source_store, matching, comparison_cache


class ComparisonCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(family, "DB", self.root / "family.sqlite"),
            patch.object(family, "ROOT", self.root),
            patch.object(source_store, "ROOT", self.root),
            patch.object(
                matching, "people", return_value=[{"id": "a"}, {"id": "b"}, {"id": "c"}]
            ),
            patch.object(source_store, "listing", return_value=[]),
            patch.object(
                matching.family_verification, "source_person", side_effect=lambda x: x
            ),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)", [(x, x) for x in ["a", "b", "c"]]
            )

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def compute(self, r):
        # A tool may lazily create its evidence schema during its first actual run.
        with family.connect() as db:
            matching.family_verification.init(db)
        return {
            "pair": r["a"] + "-" + r.get("b", ""),
            "notes": ["synthetic test output"],
        }

    def test_same_pair_runs_only_once_and_switching_back_reuses(self):
        with patch.object(
            matching, "compute_analysis", side_effect=self.compute
        ) as compute:
            a = matching.analysis({"a": "a", "b": "b"})
            b = matching.analysis({"a": "a", "b": "b"})
            self.assertEqual(compute.call_count, 1)
            self.assertTrue(b["saved_result"]["reused"])
            self.assertEqual(a["saved_result"]["job"], b["saved_result"]["job"])
            matching.analysis({"a": "a", "b": "c"})
            self.assertEqual(compute.call_count, 2)
            matching.analysis({"a": "a", "b": "b"})
            self.assertEqual(compute.call_count, 2)

    def test_explicit_rerun_and_evidence_change_require_new_run(self):
        with patch.object(
            matching, "compute_analysis", side_effect=self.compute
        ) as compute:
            matching.analysis({"a": "a", "b": "b"})
            matching.analysis({"a": "a", "b": "b", "rerun": True})
            self.assertEqual(compute.call_count, 2)
            with family.connect() as db:
                db.execute(
                    "INSERT INTO links VALUES(?,?,?,?)",
                    ("b", "a", "father", "synthetic"),
                )
            self.assertIsNone(comparison_cache.saved({"a": "a", "b": "b"}))

    def test_lookup_never_runs_first_analysis(self):
        with patch.object(
            matching, "compute_analysis", side_effect=AssertionError("No automatic run")
        ):
            self.assertIsNone(comparison_cache.saved({"a": "a", "b": "c"}))

    def test_tampered_result_not_reused(self):
        with patch.object(matching, "compute_analysis", side_effect=self.compute):
            result = matching.analysis({"a": "a", "b": "b"})
        (
            self.root
            / "Projects/Launcher/a"
            / result["saved_result"]["job"]
            / "Results/comparison.json"
        ).write_text("{}")
        self.assertIsNone(comparison_cache.saved({"a": "a", "b": "b"}))


if __name__ == "__main__":
    unittest.main()
