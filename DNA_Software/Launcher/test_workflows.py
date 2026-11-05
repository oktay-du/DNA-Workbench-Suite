import unittest, tempfile, contextlib, time
from pathlib import Path
from unittest.mock import patch
import workflows, source_store, family, suite_api


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (source_store, family, suite_api):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)",
                [("Child", "Child"), ("Mother", "Mother"), ("Father", "Father")],
            )
        workflows.ACTIVE = None
        workflows.OWNER = None

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()
        workflows.ACTIVE = None
        workflows.OWNER = None

    def test_plan_tracks_share_preparation_without_starting(self):
        with patch.object(suite_api, "start") as start:
            a = workflows.plan("Child", "health")
            b = workflows.plan("Child", "medication")
        self.assertEqual(a["steps"][0]["task"], b["steps"][0]["task"])
        start.assert_not_called()
        self.assertIn("vcf", a["steps"][1]["missing"])

    def test_remembered_reference_is_reused_not_missing_paths(self):
        ref = self.root / "ref.fa"
        ref.write_text(">1\nA\n")
        workflows.configure(
            "Child", "normalize", {"reference": str(ref), "build": "GRCh38"}
        )
        p = workflows.task_plan("Child", "normalize")
        self.assertEqual(p["inputs"]["reference"], str(ref))
        self.assertTrue(p["autofill"])
        ref.unlink()
        self.assertFalse(
            workflows.task_plan("Child", "normalize")["inputs"].get("reference")
        )

    def test_manual_unknown_fields_rejected(self):
        with self.assertRaises(ValueError):
            workflows.configure("Child", "pharmcat", {"shell": "bad"})
        with self.assertRaises(ValueError):
            workflows.plan("Child", "shell")

    def test_pipeline_persists_partial_progress_and_continues(self):
        def task(person, name, recipe=""):
            return {
                "task": name,
                "tools": "Synthetic",
                "inputs": {},
                "missing": ["fixture"],
                "status": "needs_input",
                "dependencies": [],
            }

        with patch.object(workflows, "task_plan", side_effect=task):
            r = workflows.start("Child", "health")
            for _ in range(100):
                if workflows.ACTIVE is None:
                    break
                time.sleep(0.01)
        state = workflows.read(**r)
        self.assertEqual(state["state"], "needs_attention")
        self.assertTrue(all(x["status"] == "needs_input" for x in state["steps"]))
        self.assertEqual(state["percent"], 0)
        self.assertTrue(
            (workflows.path(**r) / "Results/workflow-summary.json").is_file()
        )

    def test_cached_steps_do_not_launch_or_check_dependencies(self):
        def task(person, name, recipe=""):
            return {
                "task": name,
                "tools": "Synthetic",
                "inputs": {},
                "missing": [],
                "status": "reusable",
                "previous": {"job": "saved"},
                "dependencies": [],
            }

        with (
            patch.object(workflows, "task_plan", side_effect=task),
            patch.object(suite_api, "start") as launch,
        ):
            r = workflows.start("Child", "health")
            for _ in range(100):
                if workflows.ACTIVE is None:
                    break
                time.sleep(0.01)
            launch.assert_not_called()
        self.assertEqual(workflows.read(**r)["percent"], 100)

    def test_cross_workflow_run_guard(self):
        workflows.ACTIVE = ("Child", "flow_test")
        workflows.OWNER = -1
        with self.assertRaises(ValueError):
            workflows.assert_idle()

    def test_maternal_paternal_rules_not_copied_into_child_calls(self):
        family.add_link("Mother", "Child", "mother")
        family.add_link("Father", "Child", "father")
        r = workflows.parent_origin("Child")
        self.assertEqual(r["maternal_line"], ["Child", "Mother"])
        self.assertEqual(r["paternal_line"], ["Child", "Father"])
        self.assertEqual(r["loci"], [])
        self.assertIn("daughters normally do not inherit Y", r["rules"]["Y"])

    def test_trio_only_unambiguous_high_quality_autosomal_alleles(self):
        family.add_link("Mother", "Child", "mother")
        family.add_link("Father", "Child", "father")
        for pid, gt in [("Mother", "0/0"), ("Father", "1/1"), ("Child", "0/1")]:
            with contextlib.closing(source_store.connect(pid)) as db:
                db.execute("PRAGMA foreign_keys=OFF")
                db.execute(
                    "INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        pid,
                        "sample",
                        "GRCh38",
                        "1",
                        100,
                        "A",
                        "G",
                        gt,
                        "30",
                        "60",
                        "PASS",
                        "",
                    ),
                )
                db.execute(
                    "INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        pid,
                        "sample",
                        "GRCh38",
                        "Y",
                        101,
                        "A",
                        "G",
                        gt,
                        "30",
                        "60",
                        "PASS",
                        "",
                    ),
                )
                db.commit()

        def listing(pid):
            return [{"id": pid, "measurement": "Measured", "qc_color": "orange"}]

        with (
            patch.object(source_store, "listing", side_effect=listing),
            patch("execution_journal.source_state", return_value={}),
        ):
            r = workflows.parent_origin("Child")
        self.assertEqual(len(r["loci"]), 1)
        self.assertEqual(r["loci"][0]["maternal_allele"], "A")
        self.assertEqual(r["loci"][0]["paternal_allele"], "G")


if __name__ == "__main__":
    unittest.main()
