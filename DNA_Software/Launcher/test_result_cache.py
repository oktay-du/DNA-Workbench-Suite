import unittest, tempfile, json
from pathlib import Path
import result_cache as rc


class ResultCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.task = {
            "id": "compare",
            "kind": "analysis",
            "fields": [{"key": k, "kind": "file"} for k in ["a", "b", "reference"]],
        }
        self.values = {}
        for name in ["a", "b", "reference"]:
            p = self.root / (name + ".txt")
            p.write_text(name)
            self.values[name] = str(p)
        self.values["threshold"] = "7"
        self.folder = self.root / "Projects/Launcher/P1/run1"
        (self.folder / "Results").mkdir(parents=True)
        (self.folder / "Results/report.txt").write_text("result")
        (self.folder / "inputs.json").write_text(
            json.dumps(
                {
                    "inputs": self.values,
                    "result_identity": rc.fingerprint(
                        self.root, "P1", self.task, self.values
                    ),
                }
            )
        )
        rc.seal(self.folder)
        self.history = [{"task": "compare", "job": "run1", "status": "Complete"}]

    def tearDown(self):
        self.tmp.cleanup()

    def lookup(self, values=None, person="P1", history=None):
        return rc.lookup(
            self.root,
            person,
            self.task,
            values or self.values,
            self.history if history is None else history,
        )

    def test_same_selection_reuses(self):
        self.assertTrue(self.lookup()["verified"])

    def test_running_job_with_null_finished_does_not_break_cached_lookup(self):
        complete = dict(self.history[0], finished="2026-11-05T10:00:00")
        running = {
            "job": "intake_pending",
            "task": "batch_intake",
            "status": "Running",
            "started": "2026-11-05T11:00:00",
            "finished": None,
        }
        self.assertTrue(self.lookup(history=[complete, running])["verified"])

    def test_missing_job_timestamps_do_not_break_lookup(self):
        complete = dict(self.history[0], finished="2026-11-05T10:00:00")
        missing = {
            "job": "pending",
            "task": "batch_intake",
            "status": "Failed",
            "started": None,
            "finished": None,
        }
        self.assertTrue(self.lookup(history=[complete, missing])["verified"])

    def test_different_parent_pair_initial_run(self):
        p = self.root / "mother.txt"
        p.write_text("mother")
        self.assertEqual(
            self.lookup(dict(self.values, a=str(p)))["status"], "first_run"
        )

    def test_parameter_and_reference_change(self):
        self.assertFalse(self.lookup(dict(self.values, threshold="8"))["verified"])
        Path(self.values["reference"]).write_text("newreference")
        self.assertFalse(self.lookup()["verified"])

    def test_profiles_do_not_cross(self):
        self.assertFalse(self.lookup(person="P2")["verified"])

    def test_failed_or_missing_result_never_complete(self):
        self.assertFalse(
            self.lookup(history=[dict(self.history[0], status="Failed")])["verified"]
        )
        (self.folder / "Results/report.txt").unlink()
        self.assertFalse(self.lookup()["verified"])

    def test_source_change_is_not_reused(self):
        Path(self.values["b"]).write_text("changed")
        self.assertFalse(self.lookup()["verified"])

    def test_existing_unrelated_import_does_not_change_explicit_selection(self):
        (self.root / "new-unselected.vcf").write_text("new")
        self.assertTrue(self.lookup()["verified"])

    def test_changed_recipe_needs_run(self):
        self.task["method_version"] = "2"
        self.assertFalse(self.lookup()["verified"])

    def test_actions_not_reused(self):
        self.task["id"] = "import"
        self.assertEqual(self.lookup()["status"], "action")


if __name__ == "__main__":
    unittest.main()
