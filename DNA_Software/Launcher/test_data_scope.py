"""Synthetic scope checks; provider branding must not imply WGS or health validation."""

import tempfile, unittest, zipfile
from pathlib import Path
import inspector
from data_scope import describe


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, text, name="sample.txt"):
        p = self.root / name
        p.write_text(text, encoding="utf-8")
        return inspector.inspect(p)

    def test_chip_not_wgs_and_no_y_not_xx(self):
        r = self.read("# 23andMe\nrs1\t1\t10\tAG\nrs2\tX\t20\tAA\n")
        s = r["data_scope"]
        self.assertEqual(s["regions"]["autosomal"], 1)
        self.assertIn("no detection", s["scope"])
        self.assertIn("Not proven", s["capabilities"]["y_lineage"])
        self.assertNotIn("XX", s["summary"])

    def test_vendor_does_not_prove_complete_wgs(self):
        r = self.read(
            "##fileformat=VCFv4.2\n##provider=Dante Labs\n##reference=GRCh37\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\nY\t5\t.\tA\tG\t50\tPASS\t.\tGT:DP:GQ\t1:25:40\n",
            "sample.vcf",
        )
        self.assertEqual(r["provider"], "Dante Labs")
        self.assertEqual(r["build"], "GRCh37")
        self.assertEqual(r["data_scope"]["scope"], "Genome size not recorded")
        self.assertEqual(r["data_scope"]["regions"]["Y"], 1)
        self.assertEqual(r["data_scope"]["variant_types"]["SNV"], 1)

    def test_gvcf_block_is_not_all_bases_called(self):
        r = self.read(
            "##fileformat=VCFv4.2\n##assay=WGS\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n1\t1\t.\tA\t<NON_REF>\t.\tPASS\tEND=1000\tGT:DP:GQ\t0/0:20:30\n",
            "a.vcf",
        )
        self.assertEqual(r["called_points"], 1)
        self.assertEqual(r["gvcf_blocks"], 1)
        self.assertIn("not verified", r["data_scope"]["scope"])
        self.assertIn("gVCF", r["data_scope"]["kind"])

    def test_ancestry_segments_are_not_genotypes(self):
        r = self.read(
            "Ancestry,Chromosome,Start Point,End Point\nGerman,1,1,100000\n",
            "composition.csv",
        )
        self.assertEqual(r["format"], "Ancestry report / segment assignments")
        self.assertEqual(r["called_points"], 0)
        self.assertIn("No suitable", r["data_scope"]["capabilities"]["health"])

    def test_y_str_is_not_y_sequencing(self):
        r = self.read("Marker,Value\nDYS393,13\nDYS390,24\n")
        self.assertEqual(r["format"], "Y-STR table")
        self.assertIn("no complete", r["data_scope"]["scope"])

    def test_pdf_name_not_health_or_raw_evidence(self):
        p = self.root / "Dante_30x_Health.pdf"
        p.write_bytes(b"%PDF-1.4\n")
        s = inspector.inspect(p)["data_scope"]
        self.assertIn("not yet", s["scope"])
        self.assertIn("No suitable", s["capabilities"]["health"])

    def test_fastq_zip_manifest_not_verified_reads(self):
        p = self.root / "reads.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("sample_R1.fastq.gz", b"not gzip")
            z.writestr("sample_R2.fastq.gz", b"not gzip")
        r = inspector.inspect(p)
        self.assertFalse(r["verified"])
        self.assertIn("unchecked", r["data_scope"]["evidence"][0])

    def test_imputed_is_not_measured(self):
        s = describe(
            {
                "format": "VCF",
                "called_points": 100,
                "measurement": "Imputed",
                "color": "orange",
            }
        )
        self.assertIn("Statistical", s["capabilities"]["health"])

    def test_binary_needs_coverage(self):
        s = describe({"format": "BAM", "bytes": 100_000_000_000})
        self.assertIn("not yet distinguished", s["scope"])

    def test_low_pass_is_not_automatically_imputed(self):
        t = inspector.tokens("##assay=low-pass whole genome", "sample.vcf")
        s = describe(dict(t, format="VCF", called_points=10))
        self.assertFalse(s["capabilities"]["health"].startswith("Statistical"))

    def test_non_ref_allele_not_secure_genotype(self):
        r = self.read(
            "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n1\t1\t.\tA\t<NON_REF>\t.\tPASS\tEND=1000\tGT:DP:GQ\t0/1:20:30\n",
            "nonref.vcf",
        )
        self.assertEqual(r["called_points"], 0)
        self.assertEqual(r["qc_supported_points"], 0)

    def test_conflict_blocks_analysis(self):
        s = describe({"format": "VCF", "called_points": 10, "color": "black"})
        self.assertIn("Locked", s["capabilities"]["health"])


if __name__ == "__main__":
    unittest.main()
