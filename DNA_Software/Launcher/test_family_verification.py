import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import family, family_verification as fv


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.patches = [
            patch.object(family, "DB", self.base / "family.sqlite"),
            patch.object(family, "ROOT", self.base),
            patch.object(fv.source_store, "ROOT", self.base),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)", [(x, x) for x in ["a", "b", "c"]]
            )
        self.r = {
            "text": "#FID1 IID1 FID2 IID2 NSNP HETHET IBS0 KINSHIP\n0 S1 0 S2 120000 .2 .001 .249",
            "mapping": {"S1": "a", "S2": "b"},
            "build": "GRCh38",
            "note": "Synthetic test; not real DNA",
        }

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_steps_not_ancestry(self):
        for kind in family.STEP:
            family.add_link("a", "b", kind)
        self.assertEqual(family.lineage("b", "father"), ["b"])
        self.assertEqual(fv.expected("a", "b"), set())

    def test_step_and_parent_conflict(self):
        family.add_link("a", "b", "father")
        with self.assertRaises(ValueError):
            family.add_link("a", "b", "stepfather")

    def test_pair_is_symmetric(self):
        fv.import_king(self.r)
        r = next(x for x in fv.verify("b")["comparisons"] if x["person"] == "a")
        self.assertAlmostEqual(r["relatedness_percent"], 49.8)

    def test_marker_concordance_not_relatedness(self):
        with patch.object(
            fv,
            "marker_comparison",
            return_value={"concordance_percent": 99, "common_snps": 10000},
        ):
            r = fv.verify("a")["comparisons"][0]
        self.assertIsNone(r["relatedness_percent"])
        self.assertEqual(r["marker_comparison"]["concordance_percent"], 99)

    def test_half_sibling_degree(self):
        family.add_link("a", "b", "halfbrother")
        self.assertEqual(fv.expected("a", "b"), {2})

    def test_king_degree_interpretation(self):
        for phi, degree in [
            (0.5, 0),
            (0.25, 1),
            (0.125, 2),
            (0.0625, 3),
            (0.001, None),
        ]:
            self.assertEqual(fv.degree(phi)[0], degree)

    def test_import_and_check(self):
        family.add_link("a", "b", "father")
        fv.import_king(self.r)
        r = fv.verify("a")["comparisons"][0]
        self.assertAlmostEqual(r["relatedness_percent"], 49.8)
        self.assertEqual(r["degree"], 1)
        self.assertIn("not clearly confirmed", r["pedigree_check"])

    def test_pedigree_mismatch(self):
        family.add_link("a", "b", "halfbrother")
        fv.import_king(self.r)
        self.assertIn(
            "does not fit", fv.verify("a")["comparisons"][0]["pedigree_check"]
        )

    def test_low_marker_count_no_percentage(self):
        self.r["text"] = self.r["text"].replace("120000", "50")
        fv.import_king(self.r)
        self.assertIsNone(fv.verify("a")["comparisons"][0]["relatedness_percent"])

    def test_changed_source_stale(self):
        fv.import_king(self.r)
        with patch.object(fv, "signature", return_value="changed"):
            self.assertIsNone(fv.verify("a")["comparisons"][0]["relatedness_percent"])

    def test_mapping_duplicates_blocked(self):
        self.r["mapping"]["S2"] = "a"
        with self.assertRaises(ValueError):
            fv.import_king(self.r)

    def test_missing_no_fabricated_percent(self):
        self.assertIsNone(fv.verify("a")["comparisons"][0]["relatedness_percent"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
