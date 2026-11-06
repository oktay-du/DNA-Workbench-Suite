import importlib
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import profile_pipeline as pp, source_store, workflow_sources, snp_liftover


class ProfilePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch = patch.object(source_store, "ROOT", self.root)
        self.patch.start()
        self.pid = "P001_Test"
        self.fa = self.root / "reference.fa"
        self.fa.write_text(">1\n" + "A" * 2000 + "\n")
        Path(str(self.fa) + ".fai").write_text("1\t2000\t3\t2000\t2001\n")

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def folder(self, name):
        p = self.root / "Projects/Launcher" / self.pid / name / "Results"
        p.mkdir(parents=True)
        return p

    def source(
        self,
        name="a",
        genotypes=None,
        measurement="Measured",
        build="GRCh38",
        quality=True,
    ):
        p = self.root / (name + ".vcf")
        g = genotypes or [(10, "0/1"), (11, "0/0"), (12, "1/1")]
        text = (
            "##fileformat=VCFv4.2\n##reference="
            + build
            + "\n##fixture="
            + name
            + "\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
        )
        for pos, gt in g:
            text += (
                f"1\t{pos}\trs{pos}\tA\tG\t50\tPASS\t.\tGT:DP:GQ\t{gt}:"
                + ("30:40" if quality else ".:.")
                + "\n"
            )
        p.write_text(text)
        r = source_store.import_batch(
            self.pid,
            [str(p)],
            name,
            "synthetic",
            measurement=measurement,
            log=lambda s: None,
        )
        return next(x for x in source_store.listing(self.pid) if x["id"] == r["ids"][0])

    def analysis(self):
        out = self.folder("analysis")
        r = pp.analyze(self.pid, out, log=lambda s: None)
        return out, r

    def test_full_comparison_and_conflict_exclusion_roundtrip(self):
        self.source()
        self.source("b", [(10, "1/1"), (11, "0/0"), (12, "1/1")])
        analysis, r = self.analysis()
        self.assertEqual(r["pairs"][0]["common"], 3)
        self.assertEqual(r["pairs"][0]["discordant"], 1)
        out = self.folder("selection")
        result = pp.generate(
            self.pid, analysis, out, "GRCh38", self.fa, log=lambda s: None
        )
        self.assertEqual(result["statistics"]["conflicts"], 1)
        self.assertEqual(result["statistics"]["included"], 2)
        self.assertTrue(result["validation"]["passed"])
        self.assertEqual(
            sum(x["primary_snps"] for x in result["source_contributions"]), 2
        )
        self.assertAlmostEqual(
            sum(x["primary_percent"] for x in result["provider_contributions"]), 100
        )
        self.assertEqual(
            sum(x["supporting_snps"] for x in result["source_contributions"]), 4
        )
        calls = list(pp.calls(out / "best_selection.vcf", {}))
        self.assertEqual([c[2] for c in calls], ["AA", "GG"])

    def test_absent_position_not_filled_with_reference(self):
        self.source()
        a, r = self.analysis()
        out = self.folder("selection")
        pp.generate(self.pid, a, out, "GRCh38", self.fa, log=lambda s: None)
        self.assertEqual(
            [x[1] for x in pp.calls(out / "best_selection.vcf", {})], [10, 11, 12]
        )

    def test_different_builds_not_compared(self):
        self.source()
        self.source("b", build="GRCh37")
        _, r = self.analysis()
        self.assertEqual(r["pairs"][0]["status"], "different-build")
        self.assertEqual(r["pairs"][0]["common"], 0)

    def test_imputed_not_used_as_measured_evidence(self):
        self.source(measurement="Imputed")
        a, _ = self.analysis()
        with self.assertRaises(ValueError):
            pp.generate(
                self.pid,
                a,
                self.folder("selection"),
                "GRCh38",
                self.fa,
                log=lambda s: None,
            )

    def test_duplicates_are_excluded_not_voted_twice(self):
        self.source(genotypes=[(10, "0/1"), (10, "0/1"), (11, "0/0")])
        _, r = self.analysis()
        self.assertEqual(r["sources"][0]["stats"]["duplicates"], 1)
        self.assertEqual(r["sources"][0]["called"], 1)

    def test_changed_source_blocks_generation(self):
        row = self.source()
        a, _ = self.analysis()
        Path(row["path"]).write_text("changed")
        with self.assertRaises(ValueError):
            pp.generate(
                self.pid,
                a,
                self.folder("selection"),
                "GRCh38",
                self.fa,
                log=lambda s: None,
            )

    def test_activation_provenance_and_generated_exclusion(self):
        row = self.source()
        a, _ = self.analysis()
        out = self.folder("selection")
        pp.generate(self.pid, a, out, "GRCh38", self.fa, log=lambda s: None)
        r = pp.activate(self.pid, out)
        self.assertTrue(r["activated"])
        rows = source_store.listing(self.pid)
        self.assertEqual(len([x for x in rows if x["origin"] == "own_generated"]), 3)
        self.assertEqual(
            next(x for x in rows if x["id"] == row["id"])["lifecycle"],
            "used_in_selection",
        )
        self.assertTrue(pp.activate(self.pid, out)["already_active"])
        self.assertEqual(len(source_store.listing(self.pid)), 4)
        out2 = self.folder("analysis_again")
        report = pp.analyze(self.pid, out2, log=lambda s: None)
        self.assertEqual(
            sum(x["status"] == "derived-not-independent" for x in report["sources"]), 3
        )
        plan = workflow_sources.plan(self.root, self.pid, "vcf_qc", [])
        self.assertEqual(plan["inputs"]["vcf"], str(out / "best_selection.vcf"))
        self.source("new")
        plan = workflow_sources.plan(self.root, self.pid, "vcf_qc", [])
        self.assertEqual(plan["inputs"]["vcf"], str(out / "best_selection.vcf"))
        self.assertTrue(pp.summary(self.pid)["sets"][0]["needs_refresh"])
        self.assertEqual(pp.summary(self.pid)["refresh"]["status"], "available")
        pointer = self.root / "Projects/BestSelection" / self.pid / "current.json"
        self.assertEqual(json.loads(pointer.read_text())["folder"], str(out))

    def test_refresh_failure_keeps_previous_current(self):
        self.source()
        a, _ = self.analysis()
        out = self.folder("selection")
        pp.generate(self.pid, a, out, "GRCh38", self.fa, log=lambda s: None)
        pp.activate(self.pid, out)
        self.source("new")
        pointer = self.root / "Projects/BestSelection" / self.pid / "current.json"
        before = pointer.read_bytes()
        with self.assertRaises((OSError, ValueError)):
            pp.refresh(self.pid, self.folder("refresh"), log=lambda s: None)
        self.assertEqual(pointer.read_bytes(), before)
        self.assertEqual(pp.summary(self.pid)["refresh"]["status"], "failed")

    def test_profile_refresh_lock_prevents_concurrent_refresh(self):
        self.assertTrue(pp.refresh_available(self.pid))
        with pp.refresh_lock(self.pid):
            self.assertFalse(pp.refresh_available(self.pid))

    def test_windows_liftover_dependency_is_declared(self):
        import on_demand

        self.assertEqual(on_demand.mapped("liftover_snps"), ["pyliftover"])
        self.assertEqual(on_demand.mapped("profile_analyze"), ["pyliftover"])

    def test_activation_enriches_dna_profile_and_preserves_other_fields(self):
        import family
        from contextlib import closing

        with patch.object(family, "DB", self.root / "family.sqlite"):
            with closing(family.connect()) as db, db:
                db.executemany(
                    "INSERT INTO people VALUES(?,?,0)",
                    [(self.pid, "Manual profile name"), ("P002_Test", "Mein Vater")],
                )
                db.execute(
                    "INSERT INTO links VALUES(?,?,?,?)",
                    ("P002_Test", self.pid, "father", "Personal note"),
                )
            self.source()
            a, _ = self.analysis()
            out = self.folder("selection")
            pp.generate(self.pid, a, out, "GRCh38", self.fa, log=lambda s: None)
            pp.activate(self.pid, out)
            with closing(family.connect()) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT label FROM people WHERE id=?", (self.pid,)
                    ).fetchone()[0],
                    "Manual profile name",
                )
                self.assertEqual(
                    db.execute("SELECT note FROM links").fetchone()[0], "Personal note"
                )
            with closing(source_store.connect(self.pid)) as db:
                best = json.loads(
                    db.execute(
                        "SELECT payload FROM derived_profile WHERE key='best_selection'"
                    ).fetchone()[0]
                )
            self.assertEqual(best["snps"], 3)
            self.assertEqual(best["chromosome_counts"], {"1": 3})

    def test_output_tampering_blocks_activation(self):
        self.source()
        a, _ = self.analysis()
        out = self.folder("selection")
        pp.generate(self.pid, a, out, "GRCh38", self.fa, log=lambda s: None)
        (out / "best_selection.txt").write_text("changed")
        with self.assertRaises(ValueError):
            pp.activate(self.pid, out)

    def test_synthetic_sample_stays_on_its_own_build(self):
        path = self.root / "synthetic.vcf"
        path.write_text(
            "##fileformat=VCFv4.2\n##DNAWorkbenchSynthetic=true\n"
            "##reference=synthetic-educational-v1\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
            "1\t3\trs1\tA\tC\t60\tPASS\t.\tGT:DP:GQ\t0/1:30:60\n"
        )
        source_store.import_batch(
            self.pid,
            [str(path)],
            "sample",
            "synthetic",
            measurement="Measured",
            log=lambda s: None,
        )
        out = self.folder("synthetic")
        report = pp.analyze(
            self.pid,
            out,
            log=lambda s: None,
            target="GRCh38",
            chain=None,
            reference=None,
        )
        row = report["sources"][0]
        self.assertEqual(row["status"], "analyzed")
        self.assertEqual(row["build"], "synthetic-educational")
        self.assertEqual(row["called"], 1)
        self.assertEqual(report["target"], "separate")
        self.assertIsNone(report["chain_sha256"])

    def test_build_mismatch_in_file_is_excluded(self):
        row = self.source()
        p = Path(row["path"])
        p.write_text(p.read_text().replace("GRCh38", "GRCh37"))
        _, report = self.analysis()
        self.assertEqual(report["sources"][0]["status"], "excluded")

    def test_liftover_reverse_strand_preserves_alleles(self):
        packages = (
            Path(__file__).resolve().parents[2] / "DNA_Software/Windows/PythonPackages"
        )
        sys.path.insert(0, str(packages))
        try:
            importlib.import_module("pyliftover")
        except ImportError:
            self.skipTest("Optional pyliftover not installed")
        row = self.source(build="GRCh37")
        chain = self.root / "test.chain"
        chain.write_text("chain 100 chr1 2000 + 0 2000 chr1 2000 - 0 2000 1\n2000\n")
        out = self.folder("lift")
        result = snp_liftover.run(
            self.pid,
            row["path"],
            "GRCh37",
            "GRCh38",
            chain,
            self.fa,
            out,
            log=lambda s: None,
        )
        values = list(pp.calls(out / "lifted_snps.vcf", {}))
        self.assertEqual(result["stats"]["mapped"], 3)
        self.assertIn((1991, "CT"), [(c[1], c[2]) for c in values])
        self.assertEqual(source_store.build_hint(out / "lifted_snps.vcf"), "GRCh38")

    def test_multiple_liftover_hits_are_rejected(self):
        packages = (
            Path(__file__).resolve().parents[2] / "DNA_Software/Windows/PythonPackages"
        )
        sys.path.insert(0, str(packages))
        try:
            importlib.import_module("pyliftover")
        except ImportError:
            self.skipTest("Optional pyliftover not installed")
        row = self.source(build="GRCh37")
        chain = self.root / "test.chain"
        chain.write_text(
            "chain 100 chr1 2000 + 0 2000 chr1 2000 + 0 2000 1\n2000\n\nchain 90 chr1 2000 + 0 2000 chr1 2000 + 0 2000 2\n2000\n"
        )
        out = self.folder("lift")
        result = snp_liftover.run(
            self.pid,
            row["path"],
            "GRCh37",
            "GRCh38",
            chain,
            self.fa,
            out,
            log=lambda s: None,
        )
        self.assertEqual(result["stats"]["multiple"], 3)
        self.assertEqual(result["stats"]["mapped"], 0)

    def test_harmonized_analysis_compares_builds_and_generates_target(self):
        sys.path.insert(
            0,
            str(
                Path(__file__).resolve().parents[2]
                / "DNA_Software/Windows/PythonPackages"
            ),
        )
        try:
            importlib.import_module("pyliftover")
        except ImportError:
            self.skipTest("Optional pyliftover not installed")
        self.source("old", build="GRCh37")
        self.source("new", build="GRCh38")
        chain = self.root / "test.chain"
        chain.write_text("chain 100 chr1 2000 + 0 2000 chr1 2000 + 0 2000 1\n2000\n")
        a = self.folder("harmonized")
        r = pp.analyze(
            self.pid,
            a,
            log=lambda s: None,
            target="GRCh38",
            chain=chain,
            reference=self.fa,
        )
        self.assertEqual(r["pairs"][0]["common"], 3)
        self.assertEqual(r["pairs"][0]["same"], 3)
        result = pp.generate(
            self.pid, a, self.folder("selection"), "GRCh38", self.fa, log=lambda s: None
        )
        self.assertEqual(len(result["sources"]), 2)
        self.assertEqual(result["statistics"]["included"], 3)

    def test_reference_mismatches_are_not_silently_corrected(self):
        self.source()
        a, _ = self.analysis()
        self.fa.write_text(">1\n" + "C" * 2000 + "\n")
        with self.assertRaises(ValueError):
            pp.generate(
                self.pid,
                a,
                self.folder("selection"),
                "GRCh38",
                self.fa,
                log=lambda s: None,
            )

    def test_analysis_database_corruption_blocks_selection(self):
        self.source()
        a, _ = self.analysis()
        with (a / "vergleich.sqlite").open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaises(ValueError):
            pp.generate(
                self.pid,
                a,
                self.folder("selection"),
                "GRCh38",
                self.fa,
                log=lambda s: None,
            )

    def test_explicit_shared_lineage_does_not_count_twice(self):
        self.source("a", quality=False)
        self.source("b", quality=False)
        for row in source_store.listing(self.pid):
            p = Path(row["path"])
            content = p.read_text().replace(
                "##fixture=",
                "##DNAWorkbenchOriginalSHA256=" + "a" * 64 + "\n##fixture=",
            )
            p.write_text(content)
            sha = pp.digest(p)
            with (
                __import__("contextlib").closing(source_store.connect(self.pid)) as db,
                db,
            ):
                old = row["sha256"]
                db.execute(
                    "INSERT INTO blobs SELECT ?,stored_rel,?,kind,detected_build,members FROM blobs WHERE sha256=?",
                    (sha, p.stat().st_size, old),
                )
                db.execute("UPDATE files SET sha256=? WHERE id=?", (sha, row["id"]))
        a, _ = self.analysis()
        with self.assertRaises(ValueError):
            pp.generate(
                self.pid,
                a,
                self.folder("selection"),
                "GRCh38",
                self.fa,
                log=lambda s: None,
            )


if __name__ == "__main__":
    unittest.main()
