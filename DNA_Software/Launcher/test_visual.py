import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import family, visual_store


class VisualTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.patches = [
            patch.object(family, "DB", self.base / "family.sqlite"),
            patch.object(family, "ROOT", self.base),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.execute(
                "INSERT INTO people VALUES(?,?,1)", ("DEMO", "Synthetische Testperson")
            )
        self.r = {
            "person": "DEMO",
            "provider": "TEST",
            "model": "Synthetic, not a DNA model",
            "version": "test1",
            "regions": [{"name": "Testregion", "percent": 60, "lat": 50, "lon": 10}],
            "traits": {
                "eyes": {
                    "probabilities": {"brown": 0.7, "blue": 0.3},
                    "evidence": "Synthetischer Test",
                }
            },
        }

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_roundtrip_versions(self):
        visual_store.save(self.r)
        visual_store.save(self.r)
        rows = visual_store.listing()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["data"]["person"], "DEMO")
        self.assertEqual(rows[0]["sha256"], rows[1]["sha256"])

    def test_bad_probability_rejected(self):
        self.r["traits"]["eyes"]["probabilities"]["brown"] = 0.9
        with self.assertRaises(ValueError):
            visual_store.save(self.r)

    def test_unknown_traits_not_invented(self):
        self.assertNotIn("nose", visual_store.validate(self.r)["traits"])

    def test_bad_coordinates_rejected(self):
        self.r["regions"][0]["lat"] = 100
        with self.assertRaises(ValueError):
            visual_store.save(self.r)

    def test_overlapping_percent_rejected(self):
        self.r["regions"] *= 2
        with self.assertRaises(ValueError):
            visual_store.save(self.r)

    def test_nan_rejected(self):
        self.r["regions"][0]["percent"] = float("nan")
        with self.assertRaises(ValueError):
            visual_store.save(self.r)

    def test_missing_evidence_rejected(self):
        self.r["traits"]["eyes"]["evidence"] = ""
        with self.assertRaises(ValueError):
            visual_store.save(self.r)

    def test_wrong_person_rejected(self):
        self.r["person"] = "FOREIGN"
        with self.assertRaises(ValueError):
            visual_store.save(self.r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
