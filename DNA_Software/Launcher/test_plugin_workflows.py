import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import engine


class PluginWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rootpatch = patch.object(engine, "ROOT", self.root)
        self.rootpatch.start()

    def tearDown(self):
        self.rootpatch.stop()
        self.tmp.cleanup()

    def job(self, task, inputs):
        folder = self.root / "Projects/Launcher" / task
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "request.json"
        path.write_text(
            json.dumps({"task": task, "person": "Synthetic", "inputs": inputs})
        )
        return engine.Job(path)

    def test_peddy_grch37_uses_shipped_default_sites(self):
        job = self.job(
            "peddy",
            {
                "vcf": str(self.root / "input.vcf"),
                "ped": str(self.root / "input.ped"),
                "build": "GRCh37",
            },
        )
        try:
            script = job.shell()
            self.assertNotIn("--sites hg19", script)
            self.assertIn("peddy --plot", script)
        finally:
            job.log_handle.close()

    def test_peddy_grch38_sites_explicit(self):
        job = self.job(
            "peddy",
            {
                "vcf": str(self.root / "input.vcf"),
                "ped": str(self.root / "input.ped"),
                "build": "GRCh38",
            },
        )
        try:
            self.assertIn("--sites hg38", job.shell())
        finally:
            job.log_handle.close()

    def test_read_phasing_preserves_read_group_checks(self):
        job = self.job(
            "whatshap",
            {
                "vcf": str(self.root / "a.vcf"),
                "alignment": str(self.root / "a.bam"),
                "reference": str(self.root / "a.fa"),
                "build": "GRCh38",
            },
        )
        try:
            script = job.shell()
            self.assertIn("whatshap phase --reference", script)
            self.assertIn("whatshap stats", script)
            self.assertNotIn("--ignore-read-groups", script)
        finally:
            job.log_handle.close()

    def test_sv_comparison_checks_both_builds_before_comparison(self):
        job = self.job(
            "truvari",
            {
                "base": str(self.root / "base.vcf"),
                "comparison": str(self.root / "comparison.vcf"),
                "reference": str(self.root / "a.fa"),
                "build": "GRCh38",
            },
        )
        try:
            script = job.shell()
            self.assertEqual(script.count("check_build"), 2)
            self.assertIn("truvari bench -b", script)
            self.assertIn("sv_vergleichsergebnis", script)
        finally:
            job.log_handle.close()


if __name__ == "__main__":
    unittest.main()
