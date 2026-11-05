import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import sample_data, family, source_store, suite_api, inspector, release_catalog, command_bus


class PublicSamplesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        sample_data.generate(self.root / "Samples")
        self.patches = [
            patch.object(sample_data, "ROOT", self.root),
            patch.object(family, "ROOT", self.root),
            patch.object(family, "DB", self.root / "family.sqlite"),
            patch.object(source_store, "ROOT", self.root),
            patch.object(suite_api, "ROOT", self.root),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_samples_load_idempotently_without_replacing_existing_person(self):
        with family.connect() as db:
            db.execute(
                "INSERT INTO people VALUES(?,?,0)",
                ("P001_Private", "Unchanged private profile"),
            )
        first = sample_data.create()
        second = sample_data.create()
        self.assertFalse(first["already_loaded"])
        self.assertTrue(second["already_loaded"])
        with family.connect() as db:
            self.assertEqual(
                db.execute(
                    "SELECT label FROM people WHERE id=?", ("P001_Private",)
                ).fetchone()[0],
                "Unchanged private profile",
            )
            self.assertEqual(
                db.execute("SELECT count(*) FROM sample_profiles").fetchone()[0], 4
            )

    def test_checksum_failure_happens_before_person_creation(self):
        (self.root / "Samples/Profiles/DEMO_Alex/synthetic.vcf").write_text("changed")
        with self.assertRaises(ValueError):
            sample_data.create()
        with family.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM people").fetchone()[0], 0)

    def test_private_extra_file_never_enters_sample_manifest(self):
        folder = self.root / "Samples"
        (folder / "private-note.txt").write_text("do not publish")
        sample_data.refresh_manifest(folder)
        self.assertNotIn(
            "private-note.txt",
            [r["path"] for r in sample_data.validate(folder)["files"]],
        )

    def test_synthetic_profiles_cannot_run_health_inference(self):
        sample_data.create()
        with self.assertRaisesRegex(ValueError, "Synthetic sample profile"):
            suite_api.start({"person": "DEMO_Alex", "task": "pharmcat", "inputs": {}})

    def test_support_index_is_not_reported_as_invalid_dna(self):
        p = self.root / "test.bai"
        p.write_bytes(b"BAI\x01\x00\x00")
        r = inspector.inspect(p)
        self.assertEqual(r["color"], "gray")
        self.assertEqual(r["called_points"], 0)

    def test_catalog_exposes_public_relative_metadata_and_typed_commands(self):
        r = release_catalog.snapshot()
        self.assertGreater(len(r["items"]), 60)
        self.assertNotIn("control.json", json.dumps(r))
        self.assertFalse(any(x["runtime_verified"] for x in r["items"]))
        names = {x["id"] for x in command_bus.definitions()}
        self.assertTrue(
            {
                "sample.create",
                "sample.info",
                "app.versions",
                "menu.samples",
                "menu.versions",
            }
            <= names
        )

    def test_public_presentation_rejects_private_paths_and_changed_images(self):
        import public_package, hashlib

        app = self.root / "DNA_Software/Launcher"
        folder = app / "Public"
        folder.mkdir(parents=True)
        manifest = folder / "presentation-manifest.json"
        manifest.write_text(
            json.dumps(
                {"files": [{"path": "DNA_Archiv/private.txt", "sha256": "0" * 64}]}
            )
        )
        with (
            patch.object(public_package, "HERE", app),
            patch.object(public_package, "ROOT", self.root),
        ):
            with self.assertRaisesRegex(ValueError, "Unapproved"):
                list(public_package.presentation_entries())
            image = folder / "docs/images/test.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"changed image")
            manifest.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "path": "docs/images/test.png",
                                "sha256": hashlib.sha256(b"approved").hexdigest(),
                            }
                        ]
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                list(public_package.presentation_entries())


if __name__ == "__main__":
    unittest.main()
