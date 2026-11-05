import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import workflow_sources as ws, source_store


class WorkflowSourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rows = []
        self.mock = patch.object(source_store, "listing", lambda person: self.rows)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.tmp.cleanup()

    def file(
        self,
        name,
        points=10,
        build="GRCh38",
        measurement="Measured",
        color="green",
        verified=True,
        samples=1,
    ):
        p = self.root / name
        p.write_text(
            "##fileformat=VCFv4.2\n##reference="
            + build
            + "\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
            + "".join("\tS" + str(i) for i in range(samples))
            + "\n1\t10\t.\tA\tG\t50\tPASS\t.\tGT"
            + ("\t0/1" * samples)
            + "\n"
        )
        row = {
            "path": str(p),
            "original_name": name,
            "provider": "Test",
            "label": "same",
            "kind": "VCF",
            "build": build,
            "available": True,
            "qc_points": points,
            "called_points": points,
            "qc_color": color,
            "qc_verified": verified,
            "measurement": measurement,
            "sha256": name,
        }
        self.rows.append(row)
        return row

    def plan(self, task="pharmcat", history=None):
        return ws.plan(self.root, "P1", task, history or [])

    def test_compatible_quality_wins_not_size_or_date(self):
        self.file("large_imputed.vcf", 900000, measurement="Imputed")
        best = self.file("measured.vcf", 100)
        self.assertEqual(self.plan()["inputs"]["vcf"], best["path"])
        self.assertEqual(self.plan()["inputs"]["build"], "GRCh38")

    def test_pharmcat_rejects_grch37_and_bad_qc(self):
        self.file("old.vcf", build="GRCh37")
        self.file("bad.vcf", color="black")
        self.assertNotIn("vcf", self.plan()["inputs"])

    def test_multi_sample_workflow_does_not_suggest_single_person(self):
        self.file("single.vcf", 10000)
        multi = self.file("multi.vcf", 10, samples=2)
        self.assertEqual(self.plan("kinship")["inputs"]["vcf"], multi["path"])

    def test_pair_has_distinct_sources_and_separate_builds(self):
        a = self.file("a.vcf", 100, build="GRCh37")
        b = self.file("b.vcf", 50)
        for row in (a, b):
            p = Path(row["path"])
            p.write_text("##bcftools_normCommand=norm\n" + p.read_text())
        r = self.plan("conflicts")
        self.assertNotEqual(r["inputs"]["a"], r["inputs"]["b"])
        self.assertNotEqual(r["inputs"]["build_a"], r["inputs"]["build_b"])
        self.assertTrue(r["warnings"])

    def old(self, task="pharmcat", manifest=True):
        plan = self.plan(task)
        base = self.root / "Projects/Launcher/P1/old"
        base.mkdir(parents=True)
        data = {"inputs": plan["inputs"]}
        if manifest:
            data["input_manifest"] = ws.manifest(task, plan["inputs"], self.rows)
        (base / "inputs.json").write_text(json.dumps(data))
        (base / "Results").mkdir()
        (base / "Results/report.txt").write_text("synthetic report")
        return [{"task": task, "status": "Complete", "job": "old"}]

    def test_existing_result_and_better_source_detection(self):
        self.file("first.vcf", 100)
        history = self.old()
        self.assertEqual(self.plan(history=history)["freshness"], "current")
        self.file("better.vcf", 500)
        plan = self.plan(history=history)
        self.assertEqual(plan["freshness"], "better")
        self.assertEqual(plan["previous"]["artifacts"][0]["name"], "report.txt")

    def test_newer_lower_quality_does_not_invalidate(self):
        self.file("first.vcf", 100)
        history = self.old()
        self.file("new.vcf", 50)
        self.assertEqual(self.plan(history=history)["freshness"], "current")

    def test_old_provenance_not_claimed_current(self):
        self.file("first.vcf")
        history = self.old(manifest=False)
        self.assertEqual(self.plan(history=history)["freshness"], "unknown")

    def test_modified_input_is_flagged(self):
        row = self.file("first.vcf")
        history = self.old()
        Path(row["path"]).write_text("changed")
        self.assertEqual(self.plan(history=history)["freshness"], "changed")

    def test_reference_auxiliary_not_automatically_chosen(self):
        self.file("first.vcf")
        r = self.plan("normalize")
        self.assertNotIn("reference", r["inputs"])

    def test_file_build_from_header_not_filename(self):
        row = self.file("hg19_named.vcf", build="GRCh38")
        self.assertEqual(ws.metadata(row["path"])["build"], "GRCh38")

    def test_raw_vcf_not_suggested_as_normalized(self):
        self.file("raw.vcf")
        self.assertNotIn("a", self.plan("conflicts")["inputs"])

    def test_completed_normalized_output_is_available_without_qc_inheritance(self):
        row = self.file("raw.vcf")
        history = self.old()
        base = self.root / "Projects/Launcher/P1/old/Results"
        output = base / "normalized.vcf"
        output.write_text(
            "##bcftools_normCommand=norm\n" + Path(row["path"]).read_text()
        )
        plan = self.plan("merge", history)
        self.assertEqual(plan["inputs"]["files"], [str(output)])
        self.assertEqual(plan["options"]["files"][0]["rank"], [1, False, 0, 0])


if __name__ == "__main__":
    unittest.main()
