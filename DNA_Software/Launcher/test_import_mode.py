import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import source_store as store


class ImportModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.p = patch.object(store, "ROOT", self.root / "suite")
        self.p.start()
        store.ROOT.mkdir()
        self.source = self.root / "input.txt"
        self.source.write_text("rsid\tchromosome\tposition\tgenotype\nrs1\t1\t10\tAG\n")

    def tearDown(self):
        self.p.stop()
        self.temp.cleanup()

    def load(self, mode):
        return store.import_batch(
            "P001_Ich",
            [str(self.source)],
            "Test",
            "Synthetic",
            storage_mode=mode,
            log=lambda x: None,
        )

    def test_copy_keeps_source(self):
        result = self.load("copy")
        self.assertTrue(self.source.exists())
        self.assertEqual(result["operations"][0]["actual"], "copy")

    def test_move_has_one_durable_file(self):
        content = self.source.read_bytes()
        result = self.load("move")
        self.assertFalse(self.source.exists())
        self.assertEqual(Path(result["operations"][0]["target"]).read_bytes(), content)

    def test_deduplicated_move_does_not_store_second_blob(self):
        first = self.load("copy")
        second = self.load("move")
        self.assertFalse(self.source.exists())
        self.assertEqual(
            first["operations"][0]["target"], second["operations"][0]["target"]
        )
        self.assertEqual(len(list(store.ROOT.rglob("*.importing"))), 0)

    def test_changed_registered_file_keeps_source(self):
        result = self.load("copy")
        Path(result["operations"][0]["target"]).write_text("bad")
        with self.assertRaises(ValueError):
            self.load("move")
        self.assertTrue(self.source.exists())

    def test_explicit_archive_move_goes_into_managed_profile(self):
        path = store.ROOT / "DNA_Archiv/01_Originaldownloads/P001_Ich/test.txt"
        path.parent.mkdir(parents=True)
        self.source.replace(path)
        self.source = path
        result = self.load("move")
        self.assertFalse(path.exists())
        self.assertTrue(
            Path(result["operations"][0]["target"]).is_relative_to(
                store.ROOT / "Profiles/P001_Ich/Sources"
            )
        )

    def test_invalid_mode_does_not_remove_anything(self):
        with self.assertRaises(ValueError):
            self.load("unknown")
        self.assertTrue(self.source.exists())

    def test_cancel_during_move_verification_restores_source(self):
        original_replace = Path.replace
        cancelled = [False]
        content = self.source.read_bytes()

        def replace(path, target):
            result = original_replace(path, target)
            if path == self.source:
                cancelled[0] = True
            return result

        with patch.object(Path, "replace", replace):
            with self.assertRaises(InterruptedError):
                store.import_batch(
                    "P001_Ich",
                    [str(self.source)],
                    "Test",
                    "Synthetic",
                    storage_mode="move",
                    cancel=lambda: cancelled[0],
                    log=lambda x: None,
                )
        self.assertEqual(self.source.read_bytes(), content)
        self.assertEqual(store.listing("P001_Ich"), [])


if __name__ == "__main__":
    unittest.main()
