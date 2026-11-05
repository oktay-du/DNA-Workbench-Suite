import base64, importlib.util, json, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import family, person_profile, source_store, creative_exports


class ProfileExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(family, "DB", self.root / "family.sqlite"),
            patch.object(family, "ROOT", self.root),
            patch.object(source_store, "ROOT", self.root),
            patch.object(creative_exports, "ROOT", self.root),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)",
                [("p", "Test Person"), ("q", "Other Person")],
            )

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_metadata_preserves_family_graph_and_evidence(self):
        family.add_link("q", "p", "father")
        person_profile.save(
            "p", {"name": "New Name", "residence": "Berlin", "chromosomes": "XX"}
        )
        self.assertEqual(person_profile.read("p")["name"], "New Name")
        with family.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM links").fetchone()[0], 1)
        with self.assertRaises(ValueError):
            person_profile.save("p", {"birth_date": "2020-99-01"})

    def test_empty_profile_photo_is_local(self):
        photo = (
            "data:image/png;base64,"
            + base64.b64encode(b"\x89PNG\r\n\x1a\nTEST").decode()
        )
        person_profile.photo("p", photo)
        self.assertEqual(person_profile.read("p")["photo"], photo)
        with self.assertRaises(ValueError):
            person_profile.photo("p", "data:image/svg+xml;base64,PHN2Zz4=")

    def test_duplicate_names_and_indices_are_preserved(self):
        paths = []
        for folder, text in [("a", "one"), ("b", "two")]:
            d = self.root / folder
            d.mkdir()
            f = d / "sample.vcf.gz"
            f.write_text(text)
            paths.append(str(f))
        index = self.root / "a/sample.vcf.gz.tbi"
        index.write_text("index")
        paths.insert(1, str(index))
        result = source_store.import_batch(
            "p", paths, "Test", "Batch", storage_mode="copy", log=lambda _: None
        )
        names = [Path(x["target"]).name for x in result["operations"]]
        self.assertEqual(
            names, ["001-sample.vcf.gz", "001-sample.vcf.gz.tbi", "002-sample.vcf.gz"]
        )
        self.assertEqual(len(set(names)), 3)

    def test_fastq_is_contiguous_and_quality_gated(self):
        p = self.root / "read.fastq"
        p.write_text(
            "@low\n"
            + "A" * 40
            + "\n+\n"
            + "!" * 40
            + "\n@high\n"
            + "ACGT" * 10
            + "\n+\n"
            + "I" * 40
            + "\n"
        )
        seq, meta = creative_exports.read_sequence(p)
        self.assertEqual(seq, ("ACGT" * 10)[:30])
        self.assertEqual(meta["read_number"], 2)
        self.assertEqual(meta["minimum_phred"], 40)
        with self.assertRaises(ValueError):
            creative_exports.read_sequence(self.root / "snps.vcf")

    @unittest.skipUnless(
        importlib.util.find_spec("reportlab") and importlib.util.find_spec("pypdf"),
        "Optional PDF packages not installed",
    )
    def test_unsupported_report_does_not_invent_result(self):
        from reportlab.pdfgen import canvas

        p = self.root / "report.pdf"
        c = canvas.Canvas(str(p))
        c.drawString(50, 700, "No personal haplogroup result available")
        c.save()
        with self.assertRaises(ValueError):
            creative_exports.report(p, "p", "maternal")

    @unittest.skipUnless(
        importlib.util.find_spec("reportlab") and importlib.util.find_spec("pypdf"),
        "Optional PDF packages not installed",
    )
    def test_neanderthal_percentile_is_not_fraction(self):
        from reportlab.pdfgen import canvas

        p = self.root / "report.pdf"
        c = canvas.Canvas(str(p))
        c.drawString(50, 700, "We found 236 variants in your DNA.")
        c.drawString(
            50, 680, "You have more Neanderthal DNA than 45% of other customers."
        )
        c.drawString(50, 660, "Your ancestry is less than ~2 percent.")
        c.save()
        result = creative_exports.report(p, "p", "archaic")
        self.assertEqual(result["variant_copies"], 236)
        self.assertEqual(result["customer_percentile"], 45)
        self.assertTrue(result["dna_fraction_statement"].startswith("<"))

    def test_avatar_pack_is_preparation_and_ancestry_opt_in(self):
        photo = (
            "data:image/png;base64,"
            + base64.b64encode(b"\x89PNG\r\n\x1a\nTEST").decode()
        )
        person_profile.photo("p", photo)
        with patch(
            "visual_store.listing",
            return_value=[{"person": "p", "data": {"regions": [{"label": "Example"}]}}],
        ):
            creative_exports.avatar_pack("p", {}, self.root / "avatar", lambda _: None)
        data = json.loads((self.root / "avatar/avatar-design.json").read_text())
        self.assertEqual(data["ancestry_reports"], [])
        self.assertIn("Requires an image", data["render_status"])
        self.assertTrue(zipfile.is_zipfile(self.root / "avatar/Avatar_Design_Pack.zip"))

    def test_global_jobs_keep_real_owner_and_progress(self):
        import suite_api

        for person, status in [("p", "Running"), ("q", "Complete")]:
            folder = self.root / "Projects/Launcher" / person / "same-job-id"
            folder.mkdir(parents=True)
            (folder / "status.json").write_text(
                json.dumps(
                    {
                        "person": "wrong",
                        "status": status,
                        "started": "2026-11-03",
                        "title": "Fixture",
                    }
                )
            )
            (folder / "auftrag.log").write_text("Fixture activity\n")
            if person == "p":
                (folder / "inspection-status.json").write_text(
                    json.dumps({"completed": 2, "total": 5})
                )
        with patch.object(suite_api, "ROOT", self.root):
            rows = suite_api.all_jobs()
            self.assertEqual([x["person"] for x in rows], ["p", "q"])
            self.assertEqual(rows[0]["progress"]["percent"], 40)
            self.assertIsNone(rows[1]["progress"])
            self.assertEqual(rows[0]["profile_name"], "Test Person")

    def test_storybook_only_suggests_explicitly_registered_reports(self):
        import workflow_sources

        folder = self.root / "DNA_Archiv/01_Originaldownloads/p/23andMe"
        folder.mkdir(parents=True)
        path = folder / "Person Maternal Haplogroup Report.pdf"
        path.write_bytes(b"fixture")
        plan = workflow_sources.plan(self.root, "p", "storybook", [])
        self.assertNotIn("maternal_report", plan["inputs"])
        with patch(
            "profile_documents.listing",
            return_value=[{"path": str(path), "available": True}],
        ):
            plan = workflow_sources.plan(self.root, "p", "storybook", [])
        self.assertEqual(plan["inputs"]["maternal_report"], str(path))


if __name__ == "__main__":
    unittest.main()
