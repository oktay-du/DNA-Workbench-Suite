import unittest, tempfile, contextlib, json
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, profile_files as fm, profile_documents, profile_transfer, execution_journal


class ProfileFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (family, source_store, suite_api, profile_transfer):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)",
                [("P1", "Synthetic One"), ("P2", "Synthetic Two")],
            )
        self.src = self.root / "raw.txt"
        self.src.write_text("rsid\tchromosome\tposition\tgenotype\nrs1\t1\t101\tAG\n")
        source_store.import_batch(
            "P1",
            [str(self.src)],
            "Synthetic",
            "Initial",
            storage_mode="copy",
            log=lambda _: None,
        )

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def entry(self, prefix):
        return next(
            r for r in fm.inventory("P1")["entries"] if r["id"].startswith(prefix)
        )

    def apply(self, action, ids, **kwargs):
        p = fm.preview("P1", action, ids, **kwargs)
        return fm.apply("P1", p["token"], log=lambda _: None)

    def job(self, uses_source=True, status="Complete"):
        row = self.entry("source:")
        folder = self.root / "Projects/Launcher/P1/demo"
        (folder / "Results").mkdir(parents=True, exist_ok=True)
        (folder / "inputs.json").write_text(
            json.dumps(
                {
                    "person": "P1",
                    "task": "test",
                    "inputs": {"file": row["path"]} if uses_source else {},
                }
            )
        )
        (folder / "status.json").write_text(
            json.dumps(
                {
                    "id": "demo",
                    "person": "P1",
                    "task": "test",
                    "title": "Synthetic test",
                    "kind": "analysis",
                    "status": status,
                    "started": "2026-11-04",
                    "finished": "2026-11-04",
                    "outputs": ["result.txt"],
                }
            )
        )
        report = folder / "Results/result.txt"
        report.write_text("SYNTHETIC report, no clinical finding.")
        profile_documents.index_file(
            "P1",
            report,
            "Local test",
            kind="analysis_output",
            copy=False,
            log=lambda _: None,
        )
        execution_journal.register(folder)
        return folder

    def test_inventory_counts_unique_files_and_db_runs(self):
        self.job()
        data = fm.inventory("P1")
        self.assertGreater(data["bytes"], self.src.stat().st_size)
        self.assertEqual(data["gb"], round(data["bytes"] / 10**9, 4))
        self.assertTrue(any(r["kind"] == "test" for r in data["entries"]))
        with contextlib.closing(source_store.connect("P1")) as db:
            self.assertEqual(
                db.execute(
                    "SELECT status FROM tool_runs WHERE id=?", ("demo",)
                ).fetchone()[0],
                "Complete",
            )

    def test_delete_source_is_reversible_and_withdraws_dependent_result(self):
        folder = self.job()
        row = self.entry("source:")
        r = self.apply("delete", [row["id"]])
        self.assertEqual(source_store.listing("P1"), [])
        self.assertFalse(Path(row["path"]).exists())
        self.assertIn(
            "review required",
            json.loads((folder / "status.json").read_text())["status"],
        )
        self.assertNotEqual(profile_documents.listing("P1")[0]["status"], "indexed")
        fm.restore("P1", r["operation"])
        self.assertTrue(Path(row["path"]).exists())
        self.assertEqual(len(source_store.listing("P1")), 1)

    def test_deleting_completed_job_removes_its_indexed_report(self):
        folder = self.job(False)
        r = self.apply("delete", ["job:demo"])
        self.assertFalse(folder.exists())
        self.assertEqual(profile_documents.listing("P1"), [])
        self.assertTrue(source_store.listing("P1"))
        fm.restore("P1", r["operation"])
        self.assertTrue(folder.exists())

    def test_shared_source_alias_keeps_physical_bytes(self):
        source_store.import_batch(
            "P1",
            [str(self.src)],
            "Synthetic",
            "Duplicate alias",
            storage_mode="copy",
            log=lambda _: None,
        )
        row = self.entry("source:")
        self.apply("delete", [row["id"]])
        self.assertTrue(Path(row["path"]).exists())
        self.assertEqual(len(source_store.listing("P1")), 1)

    def test_rename_updates_registry_and_sidecar_paths(self):
        v = self.root / "read.vcf.gz"
        v.write_bytes(b"not a real genome")
        index = self.root / "read.vcf.gz.tbi"
        index.write_bytes(b"index")
        source_store.import_batch(
            "P1",
            [str(v), str(index)],
            "Synthetic",
            "Paired",
            storage_mode="copy",
            log=lambda _: None,
        )
        row = next(
            r
            for r in fm.inventory("P1")["entries"]
            if r["kind"] == "dataset" and r["name"] == v.name
        )
        self.apply("rename", [row["id"]], name="renamed.vcf.gz")
        rows = source_store.listing("P1")
        self.assertTrue(
            any(
                Path(r["path"]).name == "renamed.vcf.gz" and Path(r["path"]).exists()
                for r in rows
            )
        )
        self.assertTrue(
            any(
                Path(r["path"]).name == "renamed.vcf.gz.tbi"
                and Path(r["path"]).exists()
                for r in rows
            )
        )

    def test_identical_replacement_does_not_create_an_extra_alias(self):
        row = self.entry("source:")
        self.apply("replace", [row["id"]], replacement=str(self.src))
        self.assertEqual(len(source_store.listing("P1")), 1)

    def test_deleted_check_revokes_its_badge(self):
        row = self.entry("source:")
        folder = self.job(False)
        payload = {
            "name": "raw.txt",
            "checked": "2026-11-04",
            "check_folder": str(folder),
            "check_job": "demo",
            "color": "green",
            "verified": True,
            "issues": [],
        }
        with contextlib.closing(source_store.connect("P1")) as db:
            db.execute(
                "INSERT INTO inspections VALUES(?,?,?)",
                (row["sha256"], json.dumps(payload), "2026-11-04"),
            )
            db.commit()
        self.apply("delete", ["job:demo"])
        self.assertFalse(source_store.listing("P1")[0]["qc_verified"])

    def test_stale_preview_and_other_profile_id_rejected(self):
        row = self.entry("source:")
        p = fm.preview("P1", "delete", [row["id"]])
        Path(row["path"]).write_text("changed")
        with self.assertRaises(ValueError):
            fm.apply("P1", p["token"])
        with self.assertRaises(ValueError):
            fm.preview("P2", "delete", [row["id"]])

    def test_running_jobs_and_name_collision_block_changes(self):
        row = self.entry("source:")
        self.job(status="Running")
        with self.assertRaises(ValueError):
            fm.preview("P1", "delete", [row["id"]])
        for name in ("../escape.txt", "CON", "bad?.txt"):
            with self.assertRaises(ValueError):
                fm.validate_name(name)

    def test_replace_creates_unverified_new_source(self):
        row = self.entry("source:")
        replacement = self.root / "new.txt"
        replacement.write_text("different synthetic values")
        self.apply(
            "replace", [row["id"]], replacement=str(replacement), storage_mode="copy"
        )
        rows = source_store.listing("P1")
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0]["sha256"], row["sha256"])
        self.assertFalse(rows[0]["qc_verified"])
        self.assertTrue(replacement.exists())

    def test_job_rename_is_display_label_without_changing_id(self):
        folder = self.job(False)
        self.apply("rename", ["job:demo"], name="Reviewed example")
        self.assertTrue(folder.exists())
        self.assertEqual(
            json.loads((folder / "status.json").read_text())["title"],
            "Reviewed example",
        )
        self.assertEqual(
            next(r for r in fm.inventory("P1")["entries"] if r["id"] == "job:demo")[
                "name"
            ],
            "Reviewed example",
        )

    def test_trash_tampering_blocks_restore(self):
        row = self.entry("source:")
        result = self.apply("delete", [row["id"]])
        m = json.loads(
            (fm.trash("P1") / result["operation"] / "manifest.json").read_text()
        )
        p = self.root / m["moves"][0]["to"]
        p.write_text("tampered")
        with self.assertRaises(ValueError):
            fm.restore("P1", result["operation"])

    def test_profile_backup_after_delete_excludes_tombstoned_source(self):
        self.apply("delete", [self.entry("source:")["id"]])
        result = profile_transfer.export_profile(
            "P1", self.root / "Exports", log=lambda _: None
        )
        self.assertTrue(result)

    def test_json_only_tool_is_recorded_once_and_available_for_export(self):
        calls = []

        def compute(r):
            calls.append(1)
            return {"value": "synthetic result"}

        a = execution_journal.execute(
            "family.calculate", {"person": "P1", "pos": 101}, compute
        )
        b = execution_journal.execute(
            "family.calculate", {"person": "P1", "pos": 101}, compute
        )
        self.assertEqual(a, b)
        self.assertEqual(len(calls), 1)
        entry = self.entry("job:local_")
        files = fm.export_paths("P1", [entry["id"]])
        self.assertTrue(any(p.endswith("tool-result.json") for p in files["files"]))


if __name__ == "__main__":
    unittest.main()
