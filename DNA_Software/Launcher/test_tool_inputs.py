import unittest, tempfile, contextlib
from pathlib import Path
from unittest.mock import patch
import tool_inputs as ui, suite_api, source_store, family


class ToolInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (suite_api, source_store, family):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.execute("INSERT INTO people VALUES(?,?,0)", ("P1", "Alex"))
        self.vcf = self.root / "sample.vcf"
        self.vcf.write_text(
            "##fileformat=VCFv4.2\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\n1\t1\trs1\tA\tG\t50\tPASS\t.\tGT\t0/1\n"
        )

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def test_every_tool_has_declared_source_fields_and_no_arbitrary_keys(self):
        for task in suite_api.CAT()["tasks"]:
            self.assertTrue(
                set(ui.source_fields(task)) <= {f["key"] for f in task["fields"]},
                task["id"],
            )

    def test_vcf_accepted_and_build_autofilled(self):
        r = ui.prepare(
            {
                "person": "P1",
                "task": "pharmcat",
                "inputs": {"vcf": str(self.vcf), "build": "Please select"},
                "phase": "sources",
            }
        )
        self.assertTrue(r["accepted"])
        self.assertEqual(r["inputs"]["build"], "GRCh38")

    def test_variant_audit_requests_sample_before_queuing_multisample_file(self):
        self.vcf.write_text(
            "##fileformat=VCFv4.5\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
            "1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n",
            encoding="utf-8",
        )
        request = {
            "person": "P1",
            "task": "variant_evidence_audit",
            "phase": "ready",
            "inputs": {"vcf": str(self.vcf)},
        }
        result = ui.prepare(request)
        self.assertFalse(result["accepted"])
        self.assertIn("sample", [x["field"] for x in result["missing"]])
        request["inputs"]["sample"] = "B"
        self.assertTrue(ui.prepare(request)["accepted"])
        request["inputs"]["sample"] = "not-in-the-header"
        self.assertFalse(ui.prepare(request)["accepted"])

    def test_reference_mismatch_rejected(self):
        r = ui.prepare(
            {
                "person": "P1",
                "task": "pharmcat",
                "inputs": {"vcf": str(self.vcf), "build": "GRCh37"},
                "phase": "ready",
            }
        )
        self.assertFalse(r["accepted"])
        self.assertTrue(r["errors"])

    def test_wrong_file_type_rejected(self):
        p = self.root / "report.pdf"
        p.write_bytes(b"%PDF fixture")
        r = ui.prepare(
            {
                "person": "P1",
                "task": "vcf_qc",
                "inputs": {"vcf": str(p)},
                "phase": "sources",
            }
        )
        self.assertFalse(r["accepted"])

    def test_only_source_fields_needed_in_first_step(self):
        r = ui.prepare(
            {
                "person": "P1",
                "task": "normalize",
                "inputs": {"vcf": str(self.vcf)},
                "phase": "sources",
            }
        )
        self.assertTrue(r["accepted"])
        r = ui.prepare(
            {
                "person": "P1",
                "task": "normalize",
                "inputs": {"vcf": str(self.vcf)},
                "phase": "ready",
            }
        )
        self.assertFalse(r["accepted"])
        self.assertIn("reference", [x["field"] for x in r["missing"]])

    def test_missing_or_other_profile_file_is_not_accepted(self):
        p = self.root / "Profiles/OTHER/Sources/x.vcf"
        p.parent.mkdir(parents=True)
        p.write_bytes(self.vcf.read_bytes())
        r = ui.prepare(
            {
                "person": "P1",
                "task": "vcf_qc",
                "inputs": {"vcf": str(p)},
                "phase": "sources",
            }
        )
        self.assertFalse(r["accepted"])

    def test_cli_job_gate_rejects_archive_before_creating_job(self):
        import zipfile

        p = self.root / "genome.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("raw.vcf", self.vcf.read_bytes())
        with self.assertRaisesRegex(ValueError, "compatibility"):
            suite_api.start(
                {"person": "P1", "task": "vcf_qc", "inputs": {"vcf": str(p)}}
            )
        self.assertFalse((self.root / "Projects/Launcher/P1").exists())

    def test_cram_source_requires_exact_reference_at_ready_stage(self):
        p = self.root / "reads.cram"
        p.write_bytes(b"CRAM\x03\x00" + b"header")
        r = ui.prepare(
            {
                "person": "P1",
                "task": "bam_qc",
                "inputs": {"bam": str(p)},
                "phase": "ready",
            }
        )
        self.assertFalse(r["accepted"])
        self.assertIn("reference", [x["field"] for x in r["missing"]])


if __name__ == "__main__":
    unittest.main()
