import unittest, tempfile, contextlib, time
from pathlib import Path
from unittest.mock import patch
import batch_intake as b, source_store as s, family, suite_api, profile_transfer, profile_collections, profile_pipeline


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "suite"
        self.root.mkdir()
        self.stack = contextlib.ExitStack()
        for m in (s, family, suite_api, profile_transfer):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)", [("A", "Alex"), ("B", "Robin")]
            )
        b.ACTIVE = None
        b.OWNER = None

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()
        b.ACTIVE = None
        b.OWNER = None

    def wait(self, j):
        # Windows CI can take longer to finish the SQLite work and close file handles.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if b.ACTIVE is None:
                return b.read(j["person"], j["job"])
            time.sleep(0.01)
        self.fail("Batch did not finish")

    def file(self, name, text="Some non-genotype report text"):
        p = self.base / "downloads" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def scan(self, paths):
        return self.wait(
            b.start(
                {
                    "person": "A",
                    "files": [str(x) for x in paths],
                    "include_registered": False,
                }
            )
        )

    def accept(self, v, mode="move"):
        args = {
            "person": "A",
            "job": v["job"],
            "items": [
                {"id": x["id"], "person": "A", "provider": "23andMe"}
                for x in v["items"]
                if x["selected"]
            ],
            "confirmed": True,
            "storage_mode": mode,
            "follow_tools": False,
        }
        return self.wait(b.accept(args))

    def test_no_automatic_archive_profiles_or_sources(self):
        p = self.root / "DNA_Archiv/01_Originaldownloads/P999_NotImported"
        p.mkdir(parents=True)
        (p / "x.txt").write_text("private")
        with family.connect() as db:
            self.assertFalse(
                db.execute(
                    "SELECT 1 FROM people WHERE id=?", ("P999_NotImported",)
                ).fetchone()
            )
        self.assertEqual(s.listing("A"), [])
        with self.assertRaises(ValueError):
            b.start({"person": "A"})

    def test_new_batch_does_not_recheck_registered_sources_by_default(self):
        old = self.file("old.txt")
        s.import_batch("A", [str(old)], "Test", "Prior batch", log=lambda _: None)
        new = self.file("new.txt")
        with patch.object(
            s, "listing", side_effect=AssertionError("Unexpected full source rescan")
        ):
            batch = self.wait(b.start({"person": "A", "files": [str(new)]}))
        self.assertEqual([item["name"] for item in batch["items"]], ["new.txt"])
        self.assertEqual(batch["total"], 1)
        self.assertEqual(batch["phase"], "review")

    def test_recursive_folder_mixed_types_and_filter(self):
        a = self.file("reads/sample_R1_001.fastq", "@read\nACGT\n+\nIIII\n")
        self.file("reports/note.txt")
        self.file("nested/file.bam", "BAM fixture")
        r = self.wait(
            b.start(
                {
                    "person": "A",
                    "files": [str(a.parents[1])],
                    "kinds": ["FASTQ", "BAM"],
                    "include_registered": False,
                }
            )
        )
        self.assertEqual({x["kind"] for x in r["items"]}, {"FASTQ", "BAM"})
        self.assertTrue(a.exists())
        self.assertEqual(s.listing("A"), [])

    def test_reviewed_group_move_numbered_names_and_registered_paths(self):
        a = self.file("one/raw.txt")
        c = self.file("two/raw.txt", "A second report")
        r = self.accept(self.scan([a, c]))
        self.assertEqual(r["phase"], "completed")
        self.assertFalse(a.exists())
        self.assertFalse(c.exists())
        rows = s.listing("A")
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({x["path"] for x in rows}), 2)
        self.assertTrue(
            all(
                Path(x["path"]).is_relative_to(self.root / "Profiles/A/Sources")
                for x in rows
            )
        )
        self.assertTrue(any(Path(x["path"]).name.startswith("002-") for x in rows))

    def test_copy_and_unknown_version_keep_original(self):
        p = self.file("raw.txt")
        v = self.scan([p])
        self.accept(v, "copy")
        self.assertTrue(p.exists())
        self.assertEqual(s.listing("A")[0]["build"], "Unknown")

    def test_changed_source_rejected_before_moving(self):
        p = self.file("raw.txt")
        v = self.scan([p])
        p.write_text("changed after review")
        with self.assertRaises(ValueError):
            self.accept(v)
        self.assertTrue(p.exists())
        self.assertFalse(s.listing("A"))

    def test_incomplete_download_does_not_block_others(self):
        v = self.scan([self.file("a.part"), self.file("report.txt")])
        self.assertEqual(v["phase"], "review")
        self.assertEqual(len([x for x in v["items"] if x["selected"]]), 1)

    def test_later_fastq_mate_completes_inventory_without_merging_builds(self):
        r1 = self.file("kit_R1_001.fastq", "@read\nACGT\n+\nIIII\n")
        self.accept(self.scan([r1]))
        self.assertEqual(
            profile_collections.summary("A")["read_sets"][0]["state"], "awaiting_R2"
        )
        r2 = self.file("kit_R2_001.fastq", "@read\nTGCA\n+\nIIII\n")
        self.accept(self.scan([r2]))
        self.assertEqual(
            profile_collections.summary("A")["read_sets"][0]["state"], "candidate_pair"
        )

    def test_importing_both_reference_builds_preserves_labels(self):
        paths = []
        for build in ("GRCh37", "GRCh38"):
            paths.append(
                self.file(
                    build + ".vcf",
                    "##fileformat=VCFv4.2\n##reference="
                    + build
                    + "\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n1\t10\trs1\tA\tG\t50\tPASS\t.\tGT:DP:GQ\t0/1:30:40\n",
                )
            )
        self.accept(self.scan(paths))
        self.assertEqual(
            set(profile_collections.summary("A")["builds"]), {"GRCh37", "GRCh38"}
        )

    def test_no_success_for_empty_profile_comparison(self):
        with self.assertRaisesRegex(ValueError, "No files"):
            profile_pipeline.analyze(
                "A", self.root / "empty-output", log=lambda _: None
            )

    def test_review_can_explicitly_assign_an_unregistered_file_to_another_profile(self):
        p = self.file("report.txt")
        v = self.scan([p])
        item = v["items"][0]
        r = b.assign(
            {"person": "A", "job": v["job"], "item": item["id"], "destination": "B"}
        )
        self.assertEqual(r["item"]["person"], "B")
        self.assertFalse(r["item"]["details"]["verified"])
        self.assertTrue(p.exists())
        self.assertFalse(s.listing("B"))
        self.assertEqual(b.read("A", v["job"])["items"][0]["person"], "B")

    def test_routes_are_file_specific_and_do_not_claim_genome_from_pdf(self):
        for kind, task in [
            ("VCF", "vcf_qc"),
            ("BCF", "variant_convert"),
            ("BAM", "bam_qc"),
            ("CRAM", "bam_qc"),
            ("FASTQ", "fastq_report"),
            ("Report", "document"),
            ("GEDCOM", "gedcom"),
            ("Index", "sidecar"),
        ]:
            self.assertEqual(b.route({"kind": kind}, "x")[0], task)

    def test_profile_backup_accepts_new_owned_source_layout(self):
        p = self.file("raw.txt")
        self.accept(self.scan([p]))
        out = profile_transfer.export_profile("A", log=lambda _: None)
        self.assertTrue(out)


if __name__ == "__main__":
    unittest.main()
