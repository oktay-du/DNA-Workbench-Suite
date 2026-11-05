import gzip, json, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import inspector, provider_exports, release_tools, command_bus


class ProviderExportTests(unittest.TestCase):
    def test_ancestry_csv_preserves_coordinates_and_confidence(self):
        r = provider_exports.ancestry_segments(
            "# confidence: 90%\nAncestry,Chromosome,Start Point,End Point\nEuropean,1,0,120\n"
        )
        self.assertEqual(r["segments"][0]["start"], 0)
        self.assertFalse(r["percentages_computed"])
        self.assertIn("90%", r["confidence_metadata"][0])

    def test_invalid_segment_is_rejected(self):
        with self.assertRaises(ValueError):
            provider_exports.ancestry_segments(
                "Ancestry,Chromosome,Start,End\nEurope,1,100,50\n"
            )

    def test_tree_inventory_never_changes_family(self):
        r = provider_exports.tree_preview(
            {"people": [{"id": "x", "name": "Example", "parent": "y"}]}
        )
        self.assertEqual(r["person_like_objects"], 1)
        self.assertEqual(r["relationships_applied"], 0)

    def test_json_is_not_snp_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tree.json"
            p.write_text('{"people":[{"id":"x","name":"Demo"}]}')
            r = inspector.inspect(p)
            self.assertEqual(r["called_points"], 0)
            self.assertEqual(r["color"], "gray")
            self.assertTrue(r["format"].startswith("JSON"))

    def test_imputed_high_dp_is_not_measured_qc(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.vcf"
            p.write_text(
                "##fileformat=VCFv4.2\n##source=23andMe Imputed Genotype Data R6\n##reference=GRCh37\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\n1\t10\trs1\tA\tG\t50\tPASS\t.\tGT:DP:GQ\t0|1:40:99\n"
            )
            r = inspector.inspect(p)
            self.assertIn("Imputed", r["measurement"])
            self.assertIsNone(r["qc_supported_points"])
            self.assertEqual(r["color"], "orange")

    def test_phasing_header_is_derived(self):
        r = inspector.tokens("# 23andMe Phased Genotype Data\n# build 37", "sample.txt")
        self.assertIn("Phased", r["measurement"])

    def test_export_review_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tree.json"
            raw = b'{"people":[]}'
            p.write_bytes(raw)
            out = Path(tmp) / "out"
            provider_exports.inspect_export(
                "P001",
                {"file": str(p), "export_kind": "Family Tree JSON"},
                out,
                lambda _: None,
            )
            r = json.loads((out / "provider-export.json").read_text())
            self.assertFalse(r["profile_modified"])
            self.assertEqual(p.read_bytes(), raw)

    def test_partitioned_r6_zip_is_inventory_not_measured_genotypes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "imputed_data.zip"
            with zipfile.ZipFile(p, "w") as z:
                for name in [
                    *["chr" + str(i) for i in range(1, 23)],
                    "chrX.nonpar",
                    "chrX.par1",
                    "chrX.par2",
                ]:
                    z.writestr(name + ".bcf", b"BCF-placeholder")
            out = Path(tmp) / "review"
            provider_exports.inspect_export(
                "demo",
                {"file": str(p), "export_kind": "Imputed Genotype Data R6"},
                out,
                lambda _: None,
            )
            r = json.loads((out / "provider-export.json").read_text(encoding="utf-8"))
            self.assertEqual(len(r["members"]), 25)
            self.assertEqual(r["qc_supported_measured_points"], 0)
            self.assertFalse(r["profile_modified"])
            self.assertTrue(p.exists())

    def test_phased_zip_retains_all_three_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "phased_genotype_data.zip"
            with zipfile.ZipFile(p, "w") as z:
                for name in (
                    "phased_genome_demo_v5.txt",
                    "phased_genome_statistical_20190101_demo.txt",
                    "phased_genome_statistical_20190202_demo.txt",
                ):
                    z.writestr(name, "# 23andMe\n# build 37\nrs1 1 10 A G\n")
            out = Path(tmp) / "review"
            provider_exports.inspect_export(
                "demo",
                {"file": str(p), "export_kind": "Phased Genotype Data"},
                out,
                lambda _: None,
            )
            r = json.loads((out / "provider-export.json").read_text(encoding="utf-8"))
            self.assertEqual(len(r["members"]), 3)
            self.assertTrue(r["research_only"])
            self.assertIn(
                "Phased",
                inspector.tokens(
                    "# 23andMe", "001-phased_genotype_data__phased_genome_demo_v5.txt"
                )["measurement"],
            )

    def test_numbered_standalone_phased_filename_is_not_measured(self):
        r = inspector.tokens(
            "# 23andMe", "001-phased_genome_statistical_20190101_demo.txt"
        )
        self.assertIn("Phased", r["measurement"])
        self.assertIn("Filename", r["measurement_basis"])

    def test_bcf_header_is_decoded_without_claiming_variant_qc(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "chrX.par1.bcf"
            header = b"##fileformat=VCFv4.2\n##source=23andMe Imputed Genotype Data R6\n##reference=GRCh37\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n\x00"
            with gzip.open(p, "wb") as f:
                f.write(b"BCF\x02\x02" + len(header).to_bytes(4, "little") + header)
            r = inspector.inspect(p)
            self.assertEqual(r["format"], "BCF")
            self.assertEqual(r["build"], "GRCh37")
            self.assertIn("Imputed", r["measurement"])
            self.assertFalse(r["verified"])
            self.assertEqual(r["called_points"], 0)

    def test_bundle_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bundle.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("../secret.bcf", b"bad")
            with self.assertRaises(ValueError):
                provider_exports.inspect_export(
                    "demo", {"file": str(p)}, Path(tmp) / "out", lambda _: None
                )

    def test_all_new_features_in_command_registry(self):
        defs = {r["id"] for r in command_bus.definitions()}
        self.assertTrue(
            {
                "app.info",
                "app.donation",
                "release.verify",
                "workflow.provider_export",
                "workflow.seqviz_view",
            }
            <= defs
        )
        self.assertEqual(
            command_bus.invoke("app:donation", {})["payment_submitted"], False
        )

    def test_integrity_detects_changed_file(self):
        import hashlib

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = root / "app"
            app.mkdir()
            p = root / "a.py"
            p.write_bytes(b"original")
            (app / "release-integrity.json").write_text(
                json.dumps(
                    {
                        "version": "test",
                        "files": [
                            {
                                "path": "a.py",
                                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                )
            )
            with (
                patch.object(release_tools, "APP", app),
                patch.object(release_tools, "ROOT", root),
            ):
                self.assertTrue(release_tools.verify()["matches"])
                p.write_bytes(b"changed")
                self.assertFalse(release_tools.verify()["matches"])


if __name__ == "__main__":
    unittest.main()
