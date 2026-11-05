"""Job-view scale and freshness regressions using disposable synthetic data."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import profile_transfer
import suite_api


class JobViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.people = [
            {"id": "P1", "label": "Synthetic one"},
            {"id": "P2", "label": "Synthetic two"},
        ]
        self.patches = [
            patch.object(suite_api, "ROOT", self.root),
            patch.object(suite_api, "profiles", return_value=self.people),
            patch.object(profile_transfer, "jobs", return_value=[]),
        ]
        self.mocks = [item.start() for item in self.patches]
        self.addCleanup(self.temp.cleanup)
        for item in self.patches:
            self.addCleanup(item.stop)

    def create_job(self, person, name="job_1", status="Complete"):
        folder = self.root / "Projects/Launcher" / person / name
        folder.mkdir(parents=True)
        (folder / "status.json").write_text(
            json.dumps({"task": "vcf_qc", "status": status, "started": "2026-01-01"}),
            encoding="utf-8",
        )
        return folder

    def test_many_jobs_read_profile_and_transfer_lists_once(self):
        for person in self.people:
            for index in range(20):
                self.create_job(person["id"], "job_" + str(index))
        rows = suite_api.all_jobs()
        self.assertEqual(len(rows), 40)
        self.assertEqual({row["person"] for row in rows}, {"P1", "P2"})
        self.assertEqual(self.mocks[1].call_count, 1)
        self.assertEqual(self.mocks[2].call_count, 1)

    def test_next_view_sees_new_jobs_and_changed_progress(self):
        folder = self.create_job("P1", status="Running")
        progress = folder / "inspection-status.json"
        progress.write_text(json.dumps({"completed": 1, "total": 4}), encoding="utf-8")
        self.assertEqual(suite_api.all_jobs()[0]["progress"]["percent"], 25)
        progress.write_text(json.dumps({"completed": 3, "total": 4}), encoding="utf-8")
        self.create_job("P2")
        rows = suite_api.all_jobs()
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            next(r for r in rows if r["person"] == "P1")["progress"]["percent"], 75
        )

    def test_corrupt_status_does_not_hide_other_profiles(self):
        folder = self.create_job("P1")
        (folder / "status.json").write_text("[]", encoding="utf-8")
        self.create_job("P2")
        self.assertEqual([r["person"] for r in suite_api.all_jobs()], ["P2"])


if __name__ == "__main__":
    unittest.main()
