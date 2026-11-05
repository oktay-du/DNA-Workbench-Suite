import importlib
import unittest, tempfile, contextlib, sqlite3, json
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, person_profile, profile_identity, profile_transfer, profile_documents


class ProfileTransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @contextlib.contextmanager
    def workspace(self, name):
        root = self.base / name
        root.mkdir(exist_ok=True)
        with contextlib.ExitStack() as stack:
            for mod in (family, source_store, suite_api, profile_transfer):
                stack.enter_context(patch.object(mod, "ROOT", root))
            stack.enter_context(patch.object(family, "DB", root / "family.sqlite"))
            yield root

    def create(self):
        p = source_store.new_person("Alex Test")
        with family.connect() as db:
            db.execute("INSERT INTO people VALUES(?,?,0)", (p, "Alex Test"))
        person_profile.save(
            p,
            {
                "name": "Alex Test",
                "birth_date": "2000-01-01",
                "notes": "Keep family details",
            },
        )
        source = self.base / "raw.vcf"
        source.write_text(
            "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\n1\t101\trs1\tA\tG\t60\tPASS\t.\tGT\t0/1\n"
        )
        source_store.import_batch(
            p,
            [str(source)],
            "Synthetic",
            "Test",
            storage_mode="copy",
            log=lambda _: None,
        )
        doc = self.base / "report.txt"
        doc.write_text(
            "Lactose intolerance: no symptoms reported.\nThis report is not a diagnosis.\nSex: unknown.\n"
        )
        profile_documents.index_file(
            p, doc, "Example laboratory", "2026-01-01", log=lambda _: None
        )
        profile_documents.add_fact(
            p, "Lactose intolerance", "No symptoms (self-reported)"
        )
        return p

    def test_uuid_stays_after_name_change_and_same_name_is_different_person(self):
        with self.workspace("a"):
            p = self.create()
            uid = person_profile.read(p)["identity"]["uuid"]
            person_profile.save(p, {"name": "Renamed"})
            self.assertEqual(person_profile.read(p)["identity"]["uuid"], uid)
            q = source_store.new_person("Renamed")
            with family.connect() as db:
                db.execute("INSERT INTO people VALUES(?,?,0)", (q, "Renamed"))
            self.assertNotEqual(profile_identity.ensure(q)["uuid"], uid)

    def test_roundtrip_new_workspace_restores_sources_reports_and_uuid(self):
        with self.workspace("a"):
            p = self.create()
            uid = profile_identity.ensure(p)["uuid"]
            out = profile_transfer.export_profile(
                p, self.base / "backup", log=lambda _: None
            )["folder"]
        with self.workspace("b"):
            check = profile_transfer.check_import(out, log=lambda _: None)
            self.assertFalse(check["conflict"])
            restored = profile_transfer.import_profile(
                out, check["token"], log=lambda _: None
            )
            pid = restored["person"]
            self.assertEqual(profile_identity.ensure(pid)["uuid"], uid)
            self.assertEqual(len(source_store.listing(pid)), 1)
            self.assertTrue(Path(source_store.listing(pid)[0]["path"]).is_file())
            self.assertTrue(profile_documents.search(pid, "lactose"))
            self.assertEqual(len(profile_documents.facts(pid)), 1)
            self.assertEqual(person_profile.read(pid)["notes"], "Keep family details")

    def test_existing_uuid_needs_confirm_and_new_local_edit_invalidates_check(self):
        with self.workspace("a"):
            p = self.create()
            out = profile_transfer.export_profile(
                p, self.base / "backup", log=lambda _: None
            )["folder"]
            check = profile_transfer.check_import(out, log=lambda _: None)
            self.assertTrue(check["conflict"])
            with self.assertRaisesRegex(ValueError, "confirmation"):
                profile_transfer.import_profile(out, check["token"], log=lambda _: None)
            person_profile.save(p, {"name": "Newer local name"})
            with self.assertRaisesRegex(ValueError, "changed after preview"):
                profile_transfer.import_profile(
                    out, check["token"], True, log=lambda _: None
                )
            self.assertEqual(person_profile.read(p)["name"], "Newer local name")

    def test_explicit_restore_keeps_pre_import_backup_and_family_stubs(self):
        with self.workspace("a"):
            p = self.create()
            q = family.placeholder("Parent Example")
            family.add_link(q, p, "father")
            out = profile_transfer.export_profile(
                p, self.base / "backup", log=lambda _: None
            )["folder"]
            person_profile.save(p, {"name": "Changed"})
            check = profile_transfer.check_import(out, log=lambda _: None)
            result = profile_transfer.import_profile(
                out, check["token"], True, log=lambda _: None
            )
            self.assertTrue(Path(result["pre_import_backup"]["folder"]).is_dir())
            self.assertEqual(person_profile.read(p)["name"], "Alex Test")
            with family.connect() as db:
                self.assertEqual(
                    db.execute("SELECT a FROM links WHERE b=?", (p,)).fetchone()[0], q
                )

    def test_tampering_or_traversal_rejected_before_import(self):
        with self.workspace("a"):
            p = self.create()
            out = Path(
                profile_transfer.export_profile(
                    p, self.base / "backup", log=lambda _: None
                )["folder"]
            )
            m = json.loads((out / "profile-transfer.json").read_text())
            file = out / m["files"][0]["path"]
            file.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum"):
                profile_transfer.check_import(out, log=lambda _: None)
            with self.assertRaises(ValueError):
                profile_transfer.valid_rel("../escape")

    def test_retrieval_is_profile_scoped_with_citations_and_no_automatic_diagnosis(
        self,
    ):
        with self.workspace("a"):
            p = self.create()
            q = family.placeholder("Other person")
            self.assertEqual(profile_documents.search(q, "lactose"), [])
            hits = profile_documents.search(p, "Laktose")
            self.assertTrue(hits)
            self.assertEqual(hits[0]["review"], "unreviewed_extraction")
            self.assertEqual(hits[0]["page"], 1)
            self.assertIn("no symptoms", hits[0]["quote"])
            self.assertEqual(person_profile.read(p).get("lactose_intolerance"), None)

    def test_english_is_default_but_explicit_german_is_kept(self):
        with self.workspace("a"):
            self.assertEqual(suite_api.settings()["language"], "en")
            suite_api.settings({"language": "de", "theme": "dark"})
            self.assertEqual(suite_api.settings()["language"], "de")

    def test_real_pdf_text_is_cited_without_changing_profile_diagnosis(self):
        try:
            importlib.import_module("pypdf")
        except ImportError:
            self.skipTest("Optional PDF reader not installed")
        import sample_data

        samples = self.base / "fixtures"
        sample_data.generate(samples)
        with self.workspace("a"):
            p = self.create()
            result = profile_documents.index_file(
                p,
                samples / "Results/synthetic-provider-report.pdf",
                "SYNTHETIC",
                log=lambda _: None,
            )
            self.assertEqual(result["status"], "indexed")
            hits = profile_documents.search(p, "lactose")
            self.assertTrue(any("Not a human test" in h["quote"] for h in hits))
            self.assertEqual(result["pages"], 1)

    def test_ai_quotes_manual_and_report_evidence_without_model(self):
        import local_ai

        with self.workspace("a"):
            p = self.create()
            with patch.object(local_ai, "ready", return_value=False):
                r = local_ai.chat(
                    {
                        "person": p,
                        "message": "Does this person have lactose intolerance?",
                        "language": "en",
                    }
                )
            self.assertEqual(r["mode"], "cited-local-evidence")
            self.assertIn("report.txt", r["answer"])
            self.assertIn("self-report", r["answer"])
            self.assertIn("not establish actual intolerance", r["answer"])

    def test_ai_sees_completed_analysis_and_pdf_claims_separately(self):
        import local_ai

        with self.workspace("a") as root:
            p = self.create()
            folder = root / "Projects/Launcher" / p / "job_test"
            (folder / "Results").mkdir(parents=True)
            (folder / "status.json").write_text(
                json.dumps(
                    {
                        "job": "job_test",
                        "person": p,
                        "status": "Complete",
                        "task": "pharmcat",
                        "finished": "2026-11-04",
                    }
                )
            )
            (folder / "Results/finding.txt").write_text(
                "Lactose genetic susceptibility prediction: example only, not a clinical diagnosis."
            )
            with patch.object(local_ai, "ready", return_value=False):
                r = local_ai.chat(
                    {
                        "person": p,
                        "message": "What evidence is there about lactose?",
                        "language": "en",
                    }
                )
            self.assertIn("Suite analysis output", r["answer"])
            self.assertIn("Imported report (unreviewed)", r["answer"])
            self.assertIn("no symptoms", r["answer"])

    def test_import_does_not_install_foreign_sqlite_triggers(self):
        with self.workspace("a"):
            p = self.create()
            out = Path(
                profile_transfer.export_profile(
                    p, self.base / "backup", log=lambda _: None
                )["folder"]
            )
            m = json.loads((out / "profile-transfer.json").read_text())
            entry = next(r for r in m["files"] if r["path"].endswith("/sources.sqlite"))
            db = sqlite3.connect(out / entry["path"])
            db.execute(
                "CREATE TRIGGER poison AFTER INSERT ON batches BEGIN DELETE FROM files; END"
            )
            db.commit()
            db.close()
            entry["sha256"] = profile_transfer.sha(out / entry["path"])
            entry["bytes"] = (out / entry["path"]).stat().st_size
            (out / "profile-transfer.json").write_text(json.dumps(m))
        with self.workspace("b"):
            check = profile_transfer.check_import(out, log=lambda _: None)
            r = profile_transfer.import_profile(out, check["token"], log=lambda _: None)
            self.assertEqual(len(source_store.listing(r["person"])), 1)
            db = source_store.connect(r["person"])
            self.assertFalse(
                db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='trigger'"
                ).fetchone()
            )
            db.close()


if __name__ == "__main__":
    unittest.main()
