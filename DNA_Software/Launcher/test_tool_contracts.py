import unittest, tempfile, gzip, bz2, lzma, zipfile, tarfile, io
from pathlib import Path
import tool_contracts as c, source_store, suite_api, archive_io


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, name):
        return next(t for t in suite_api.CAT()["tasks"] if t["id"] == name)

    def gate(self, task, key, p):
        t = self.task(task)
        f = next(f for f in t["fields"] if f["key"] == key)
        m = {"kind": source_store.classify(p.name), **c.probe(p)}
        return c.evaluate(t, f, p, m)

    def vcf(self, version="4.2"):
        return (
            "##fileformat=VCFv"
            + version
            + "\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t1\t.\tA\tG\t.\tPASS\t.\n"
        ).encode()

    def test_every_file_field_has_explicit_contract(self):
        for t in suite_api.CAT()["tasks"]:
            for f in t["fields"]:
                if f["kind"] == "file":
                    self.assertTrue(c.contract(t, f)["formats"], (t["id"], f["key"]))

    def test_gzip_vcf_direct_zip_not_direct_for_vcf_tool(self):
        p = self.root / "sample.vcf.gz"
        p.write_bytes(gzip.compress(self.vcf()))
        self.assertTrue(self.gate("vcf_qc", "vcf", p)["accepted"])
        self.assertEqual(c.probe(p)["format_version"], "VCFv4.2")
        z = self.root / "sample.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("sample.vcf", self.vcf())
        r = self.gate("vcf_qc", "vcf", z)
        self.assertFalse(r["accepted"])
        self.assertIn("batch_extract", r["remedies"])

    def test_future_version_is_unverified_not_silently_accepted(self):
        p = self.root / "future.vcf"
        p.write_bytes(self.vcf("9.0"))
        r = self.gate("vcf_qc", "vcf", p)
        self.assertFalse(r["accepted"])
        self.assertIn("validate_format_version", r["remedies"])

    def test_truncated_gzip_and_fake_extension_fail(self):
        p = self.root / "broken.vcf.gz"
        p.write_bytes(gzip.compress(self.vcf())[:-8])
        self.assertFalse(self.gate("vcf_qc", "vcf", p)["accepted"])
        p = self.root / "fake.vcf"
        p.write_text("not a VCF")
        self.assertFalse(self.gate("vcf_qc", "vcf", p)["accepted"])

    def test_single_chip_zip_only_and_multi_payload_requires_batch(self):
        p = self.root / "chip.zip"
        with zipfile.ZipFile(p, "w") as f:
            f.writestr("raw.txt", "rsid chromosome position genotype")
        self.assertTrue(self.gate("chip_vcf", "file", p)["accepted"])
        with zipfile.ZipFile(p, "a") as f:
            f.writestr("second.txt", "other")
        self.assertFalse(self.gate("chip_vcf", "file", p)["accepted"])

    def test_bcf_only_supported_by_declared_adapters(self):
        p = self.root / "x.bcf"
        p.write_bytes(gzip.compress(b"BCF\x02\x02" + b"header"))
        self.assertTrue(self.gate("vcf_qc", "vcf", p)["accepted"])
        self.assertFalse(self.gate("pharmcat", "vcf", p)["accepted"])

    def test_reference_must_be_decoded_and_pgen_sidecars_required(self):
        p = self.root / "ref.fa.gz"
        p.write_bytes(gzip.compress(b">chr1\nACGT\n"))
        self.assertFalse(self.gate("normalize", "reference", p)["accepted"])
        p = self.root / "cohort.pgen"
        p.write_bytes(b"plink")
        self.assertFalse(self.gate("pca", "file", p)["accepted"])
        p.with_suffix(".psam").write_text("#IID")
        p.with_suffix(".pvar").write_text("#CHROM")
        self.assertTrue(self.gate("pca", "file", p)["accepted"])

    def test_archives_keep_outer_and_inner_names_and_sidecar_stems(self):
        p = self.root / "Oktay_genome_2026.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("lane/file.vcf.gz", gzip.compress(self.vcf()))
            z.writestr("lane/file.vcf.gz.tbi", b"index")
        rows = archive_io.unpack(p, self.root / "out")
        names = {Path(x).name for x in rows}
        self.assertIn("Oktay_genome_2026__file.vcf.gz", names)
        self.assertIn("Oktay_genome_2026__file.vcf.gz.tbi", names)
        self.assertTrue(p.exists())
        self.assertIn("lane/file.vcf.gz", rows.values())

    def test_zip_slip_and_case_collision_rejected(self):
        for names in [(".." + "/escape.txt",), ("A.txt", "a.txt")]:
            p = self.root / ("bad" + str(len(names)) + ".zip")
            with zipfile.ZipFile(p, "w") as z:
                for n in names:
                    z.writestr(n, "hello")
            with self.assertRaises(ValueError):
                archive_io.unpack(p, self.root / ("out" + str(len(names))))
        self.assertFalse((self.root / "escape.txt").exists())

    def test_single_streams_and_tar_extracted_checked(self):
        for ext, encode in [
            (".gz", gzip.compress),
            (".bz2", bz2.compress),
            (".xz", lzma.compress),
        ]:
            p = self.root / ("sample.vcf" + ext)
            p.write_bytes(encode(self.vcf()))
            rows = archive_io.unpack(p, self.root / ("out" + ext))
            self.assertEqual(next(Path(x).read_bytes() for x in rows), self.vcf())
        p = self.root / "reads.tar.gz"
        with tarfile.open(p, "w:gz") as z:
            data = b"@r\nACGT\n+\nIIII\n"
            m = tarfile.TarInfo("R1.fastq")
            m.size = len(data)
            z.addfile(m, io.BytesIO(data))
        rows = archive_io.unpack(p, self.root / "tarout")
        self.assertEqual(next(iter(rows.values())), "R1.fastq")

    def test_tar_symlinks_not_followed(self):
        p = self.root / "bad.tar"
        with tarfile.open(p, "w") as z:
            m = tarfile.TarInfo("link")
            m.type = tarfile.SYMTYPE
            m.linkname = "../../elsewhere"
            z.addfile(m)
        with self.assertRaises(ValueError):
            archive_io.unpack(p, self.root / "out")

    def test_unsupported_archive_is_explicit_not_fake_success(self):
        p = self.root / "x.7z"
        p.write_bytes(b"7z\xbc\xaf\x27\x1c")
        self.assertEqual(c.probe(p)["compression"], "7z")
        with self.assertRaisesRegex(ValueError, "no installed portable"):
            archive_io.unpack(p, self.root / "out")

    def test_cancelled_extraction_preserves_source(self):
        p = self.root / "cancel.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("raw.txt", "payload")
        with self.assertRaises(InterruptedError):
            archive_io.unpack(p, self.root / "out", lambda: True)
        self.assertTrue(p.exists())
        self.assertFalse(list((self.root / "out").glob("*.extracting")))

    def test_repacking_is_explicit_and_does_not_change_reference(self):
        import engine, json
        from unittest.mock import patch

        root = self.root / "suite"
        folder = root / "Projects/Launcher/P1/convert"
        folder.mkdir(parents=True)
        vcf = self.root / "source.vcf"
        vcf.write_bytes(self.vcf())
        req = folder / "inputs.json"
        req.write_text(
            json.dumps(
                {
                    "task": "variant_convert",
                    "person": "P1",
                    "inputs": {"vcf": str(vcf), "output_format": "VCF.gz (BGZF)"},
                }
            )
        )
        with patch.object(engine, "ROOT", root):
            job = engine.Job(req)
            try:
                job.validate()
                command = job.shell()
            finally:
                job.log_handle.close()
        self.assertIn("bcftools view -Oz", command)
        self.assertNotIn("liftover", command)
        self.assertNotIn("bcftools norm", command)


if __name__ == "__main__":
    unittest.main()
