import unittest, tempfile, contextlib, json
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, source_batch, best_assets, best_dataset, research_synthesis, result_cache


class SourceBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (family, source_store, suite_api):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)", [("P1", "Example"), ("P2", "Other")]
            )
        source_batch.ACTIVE = None
        source_batch.OWNER = None

    def tearDown(self):
        source_batch.ACTIVE = None
        source_batch.OWNER = None
        self.stack.close()
        self.tmp.cleanup()

    def source(self, name, provider="23andMe", payload=None):
        p = self.root / "Downloads" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(
            payload
            or b"##fileformat=VCFv4.2\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n1\t10\trs10\tA\tG\t50\tPASS\t.\tGT:DP:GQ\t0/1:30:40\n"
        )
        r = source_store.import_batch(
            "P1",
            [str(p)],
            provider,
            "fixture",
            measurement="Measured",
            storage_mode="move",
            log=lambda _: None,
        )
        return next(x for x in source_store.listing("P1") if x["id"] == r["ids"][0])

    def test_selected_groups_have_distinct_versions_even_for_same_bytes(self):
        a = self.source("raw.vcf")
        b = self.source("other/raw.vcf", "MyHeritage")
        with contextlib.closing(source_store.connect("P1")) as db:
            db.execute(
                "INSERT INTO source_metadata VALUES(?,?,?)",
                (
                    b["id"],
                    json.dumps({"declared_version": "v2", "measurement": "Measured"}),
                    "now",
                ),
            )
            db.commit()
        g = source_batch.groups("P1", "vcf_qc")
        self.assertEqual(len(g["groups"]), 2)
        self.assertTrue(any(x["version"] == "v2" for x in g["groups"]))
        r = source_batch.preview(
            {
                "person": "P1",
                "task": "vcf_qc",
                "source_ids": [a["id"], b["id"]],
                "inputs": {},
            }
        )
        self.assertTrue(r["accepted"])
        self.assertEqual(len(r["runs"]), 1)
        self.assertEqual(len(r["runs"][0]["source_aliases"]), 2)

    def test_different_contents_create_separate_runs_and_wrong_profile_rejected(self):
        a = self.source("one.vcf")
        b = self.source(
            "two.vcf", payload=Path(a["path"]).read_bytes().replace(b"rs10", b"rs11")
        )
        p = source_batch.preview(
            {
                "person": "P1",
                "task": "vcf_qc",
                "source_ids": [a["id"], b["id"]],
                "inputs": {},
            }
        )
        self.assertEqual(p["compatible_runs"], 2)
        with self.assertRaises(ValueError):
            source_batch.preview(
                {
                    "person": "P2",
                    "task": "vcf_qc",
                    "source_ids": [a["id"]],
                    "inputs": {},
                }
            )

    def test_unknown_comparison_pairing_not_automated(self):
        self.assertFalse(source_batch.groups("P1", "identity")["batch_supported"])
        with self.assertRaises(ValueError):
            source_batch.preview(
                {"person": "P1", "task": "identity", "source_ids": [], "inputs": {}}
            )

    def test_no_selection_and_missing_reference_are_explicit(self):
        self.assertFalse(
            source_batch.preview(
                {"person": "P1", "task": "vcf_qc", "source_ids": [], "inputs": {}}
            )["accepted"]
        )
        a = self.source("raw.vcf")
        r = source_batch.preview(
            {
                "person": "P1",
                "task": "normalize",
                "source_ids": [a["id"]],
                "inputs": {},
                "phase": "ready",
            }
        )
        self.assertFalse(r["accepted"])
        self.assertIn("reference", [m["field"] for m in r["runs"][0]["missing"]])

    def test_multi_source_manifest_keeps_all_aliases(self):
        a = self.source("a.vcf")
        self.source("b.vcf", "Nebula")
        rows = source_store.listing("P1")
        import workflow_sources

        m = workflow_sources.manifest("vcf_qc", {"vcf": a["path"]}, rows)
        self.assertEqual(len(m["sources"][0]["source_aliases"]), 2)

    def test_unchecked_reads_are_not_best_choice_and_checked_reads_link_without_copy(
        self,
    ):
        a = self.source("kit_R1.fastq", payload=b"@read\nACGT\n+\nIIII\n")
        self.assertFalse(best_assets.snapshot("P1")["assets"])
        job = self.root / "Projects/Launcher/P1/read_qc"
        out = job / "Results"
        out.mkdir(parents=True)
        row = Path(a["path"])
        st = row.stat()
        (job / "status.json").write_text(
            json.dumps({"status": "Complete", "task": "fastq_report"})
        )
        (job / "inputs.json").write_text(
            json.dumps(
                {
                    "inputs": {"r1": str(row)},
                    "input_manifest": {
                        "sources": [
                            {
                                "field": "r1",
                                "path": str(row),
                                "sha256": a["sha256"],
                                "bytes": st.st_size,
                                "mtime_ns": st.st_mtime_ns,
                            }
                        ]
                    },
                }
            )
        )
        (out / "fastq_quality.json").write_text(
            json.dumps(
                {"summary": {"before_filtering": {"q30_rate": 0.98, "total_reads": 1}}}
            )
        )
        result_cache.seal(job)
        assets = best_assets.snapshot("P1")["assets"]
        self.assertEqual(len(assets), 1)
        dest = self.root / "Projects/Launcher/P1/bundle/results"
        r = best_dataset.build("P1", dest, "Automatic", None, log=lambda _: None)
        self.assertTrue(r["activated"])
        manifest = json.loads((Path(r["folder"]) / "manifest.json").read_text())
        self.assertEqual(manifest["dataset_kind"], "checked_sequence_assets")
        self.assertEqual(manifest["checked_assets"][0]["storage"], "hardlink")
        self.assertEqual(
            Path(manifest["checked_assets"][0]["bundle_path"]).stat().st_ino,
            row.stat().st_ino,
        )

    def test_unchecked_reads_not_auto_best_choice_for_downstream_analysis(self):
        self.source("kit_R1.fastq", payload=b"@read\nACGT\n+\nIIII\n")
        import workflow_sources

        plan = workflow_sources.plan(self.root, "P1", "sarek", [])
        self.assertNotIn("r1", plan["inputs"])
        self.assertTrue(plan["options"]["r1"])

    def test_array_derived_representation_preserves_parent_lineage(self):
        import derived_sources

        parent = self.source(
            "raw.txt",
            payload=b"# MyHeritage\n# build=38\nrsid\tchromosome\tposition\tgenotype\nrs10\t1\t10\tAG\n",
        )
        out = self.root / "Projects/Launcher/P1/conversion/results"
        out.mkdir(parents=True)
        (out / "output.vcf").write_bytes(
            b"##fileformat=VCFv4.2\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n1\t10\trs10\tA\tG\t.\tPASS\t.\tGT\t0/1\n"
        )
        result = derived_sources.register(
            "P1",
            parent["sha256"],
            "conversion",
            "MyHeritage",
            "Measured",
            lambda _: None,
        )
        row = next(x for x in source_store.listing("P1") if x["id"] == result[0]["id"])
        self.assertEqual(row["source_root_sha256"], parent["sha256"])
        self.assertEqual(row["derived_operation"], "chip_vcf")


class SynthesisTests(unittest.TestCase):
    def report(self, provider, pct, root, called=100):
        return {
            "data": {
                "provider": provider,
                "source_root_sha256": root,
                "comparability": {
                    "population_scheme": "same",
                    "reference_panel": "same",
                    "panel_version": "1",
                    "calibration": "same",
                    "method_version": "1",
                },
                "quality": {
                    "relevant_called": called,
                    "relevant_total": 100,
                    "model_quality": 1,
                },
                "regions": [{"population_id": "DE", "name": "Example", "percent": pct}],
            }
        }

    def test_incompatible_provider_models_are_not_averaged(self):
        a = self.report("23andMe", 60, "a")
        b = self.report("MyHeritage", 30, "b")
        b["data"]["comparability"]["population_scheme"] = "different"
        r = research_synthesis.weighted_ancestry([a, b])
        self.assertEqual(len(r["calculated"]), 2)
        self.assertNotIn(45, [x["regions"][0]["percent"] for x in r["calculated"]])

    def test_only_comparable_marker_weighted_results_and_no_duplicate_votes(self):
        a = self.report("A", 60, "a", 50)
        b = self.report("B", 30, "b", 100)
        r = research_synthesis.weighted_ancestry([a, b])
        self.assertEqual(r["calculated"][0]["regions"][0]["percent"], 40)
        duplicate = self.report("Re-export", 60, "a", 50)
        self.assertEqual(
            research_synthesis.weighted_ancestry([a, b, duplicate])["calculated"][0][
                "regions"
            ][0]["percent"],
            40,
        )

    def test_missing_quality_or_population_ids_remain_pending(self):
        a = self.report("A", 60, "a")
        a["data"].pop("quality")
        r = research_synthesis.weighted_ancestry([a])
        self.assertFalse(r["calculated"])
        self.assertTrue(r["kept_separate"])

    def test_missing_category_not_invented_as_zero(self):
        a = self.report("A", 60, "a")
        b = self.report("B", 30, "b")
        b["data"]["regions"].append({"population_id": "OTHER", "percent": 70})
        r = research_synthesis.weighted_ancestry([a, b])
        self.assertFalse(r["calculated"])
        self.assertTrue(r["kept_separate"])


if __name__ == "__main__":
    unittest.main()
