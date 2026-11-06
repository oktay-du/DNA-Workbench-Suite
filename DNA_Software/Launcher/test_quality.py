"""Synthetic regression checks: no personal DNA used or uploaded."""

import gzip, tempfile, unittest
from pathlib import Path
import inspector


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def vcf(self, name="sample.vcf", n=1200, gt="0/1", quality=True):
        p = self.dir / name
        header = "##fileformat=VCFv4.2\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"
        rows = "".join(
            f"1\t{i + 1}\trs{i + 1}\tA\tG\t50\tPASS\t.\t"
            + ("GT:DP:GQ\t" + gt + ":25:40" if quality else "GT\t" + gt)
            + "\n"
            for i in range(n)
        )
        p.write_text(header + rows)
        return p

    def test_full_checksum_reports_byte_progress_without_disclosing_content(self):
        import hashlib
        from unittest.mock import patch

        payload = b"Synthetic private sequence content"
        path = self.dir / "large-fixture.fastq"
        path.write_bytes(payload)
        messages = []
        with patch.object(inspector.time, "monotonic", side_effect=[0, 3, 3]):
            digest = inspector.file_sha256(path, messages.append)
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
        self.assertEqual(
            messages, [f"Checksum progress: {len(payload)} / {len(payload)} bytes"]
        )
        self.assertNotIn(payload.decode(), "".join(messages))

    def test_measured_qc(self):
        r = inspector.inspect(self.vcf())
        self.assertEqual(
            (r["color"], r["qc_supported_points"], r["verified"]), ("green", 1200, True)
        )
        self.assertIn("Not", r["genome_completeness"])

    def test_small_is_not_invalid(self):
        r = inspector.inspect(self.vcf(n=4))
        self.assertEqual(r["color"], "orange")
        self.assertTrue(r["verified"])

    def test_no_quality_is_unknown(self):
        r = inspector.inspect(self.vcf(quality=False))
        self.assertIsNone(r["qc_supported_points"])
        self.assertEqual(r["color"], "orange")

    def test_missing_is_not_called(self):
        r = inspector.inspect(self.vcf(gt="./."))
        self.assertEqual(r["called_points"], 0)
        self.assertEqual(r["qc_supported_points"], 0)

    def test_invalid_allele_is_red(self):
        r = inspector.inspect(self.vcf(n=1, gt="0/7"))
        self.assertEqual(r["color"], "red")
        self.assertFalse(r["verified"])

    def test_duplicates_not_extra_points(self):
        p = self.vcf(n=2)
        p.write_text(p.read_text() + p.read_text().splitlines()[-1] + "\n")
        r = inspector.inspect(p)
        self.assertEqual(r["qc_supported_points"], 2)
        self.assertFalse(r["verified"])

    def test_broken_gzip_is_red(self):
        p = self.dir / "broken.vcf.gz"
        p.write_bytes(gzip.compress(self.vcf().read_bytes())[:-9])
        self.assertEqual(inspector.inspect(p)["color"], "red")

    def test_no_blood_or_sex_guess(self):
        r = inspector.inspect(self.vcf())
        self.assertEqual(r["profile"]["chromosomes"], "Undetermined")
        self.assertEqual(r["profile"]["blood_group"], "Not reliably determined")

    def test_xx_xy_are_provisional(self):
        self.assertEqual(
            inspector.chromosome_hint(
                {"x_called": 1000, "y_called": 100, "x_heterozygous": 0}
            ),
            "XY (provisional note)",
        )
        self.assertEqual(
            inspector.chromosome_hint(
                {"x_called": 1000, "y_called": 0, "x_heterozygous": 100}
            ),
            "XX (provisional note)",
        )

    def test_sparse_or_ambiguous_chromosomes_stay_unknown(self):
        for counts in [
            {"y_called": 100},
            {"x_called": 1000},
            {"x_called": 1000, "y_called": 100, "x_heterozygous": 100},
        ]:
            self.assertEqual(inspector.chromosome_hint(counts), "Undetermined")

    def test_build_and_hosting(self):
        r = inspector.tokens(
            "##reference=GRCh37\n##source=DRAGEN\n##hosting=sequencing.com", "data.vcf"
        )
        self.assertEqual(r["provider"], "Sequencing.com")
        self.assertIn("DRAGEN", r["producer"])
        self.assertEqual(r["build"], "GRCh37")


if __name__ == "__main__":
    unittest.main(verbosity=2)
