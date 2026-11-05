# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Required Notice: Copyright 2026 Oktay Du / OD — DNA Workbench
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import feedback
import command_bus


class FeedbackTests(unittest.TestCase):
    def test_default_draft_never_reads_logs_and_keeps_text_out_of_url(self):
        with patch.object(
            feedback, "diagnostics", side_effect=AssertionError("No consent")
        ):
            r = feedback.draft(
                {
                    "kind": "bug",
                    "title": "Issue",
                    "description": "Private report detail",
                }
            )
        self.assertFalse(r["submitted"])
        self.assertFalse(r["includes_log"])
        self.assertNotIn("Private", r["issue_url"])
        self.assertIn("Private report detail", r["text"])

    def test_diagnostics_cannot_disclose_raw_log_details(self):
        raw = "ValueError: patient Alice, rs123 A/G, BRCA1, alice@example.org, token=secret\nC:\\Users\\Alice\\DNA.vcf\nRuntimeError: bearer xyz\nACGTACGTACGT PatientAliceError ACGTACGTError"
        clean = feedback.filtered_log(raw)
        self.assertIn("ValueError", clean)
        self.assertIn("RuntimeError", clean)
        for sensitive in (
            "Alice",
            "rs123",
            "BRCA1",
            "example.org",
            "secret",
            "xyz",
            "ACGT",
        ):
            self.assertNotIn(sensitive, clean)

    def test_crash_record_is_filtered_and_supports_native_utf8_bom(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(feedback, "ROOT", Path(tmp)),
        ):
            p = Path(tmp) / "DNA_Software/UserData/Launcher/Diagnostics/last-crash.json"
            p.parent.mkdir(parents=True)
            p.write_text(
                json.dumps(
                    {
                        "exception_type": "System.InvalidOperationException",
                        "message": "private",
                    }
                ),
                encoding="utf-8-sig",
            )
            r = feedback.diagnostics()
            self.assertEqual(r["last_crash_type"], "InvalidOperationException")
            self.assertNotIn("private", str(r))

    def test_invalid_job_never_becomes_an_arbitrary_file_read(self):
        with patch("suite_api.job_path", side_effect=ValueError("Invalid ID")):
            with self.assertRaises(ValueError):
                feedback.diagnostics("../other", "../secret")

    def test_shared_commands_and_no_claim_of_submission(self):
        names = {r["id"] for r in command_bus.definitions()}
        self.assertTrue(
            {
                "feedback.draft",
                "app.notices",
                "app.license_inventory",
                "menu.feedback",
                "menu.notices",
            }
            <= names
        )
        r = feedback.draft(
            {
                "kind": "improvement",
                "title": "Better view",
                "description": "Add a graph",
                "include_log": True,
            }
        )
        self.assertIn("privacy-filtered", r["text"])
        self.assertIn("feature_request", r["issue_url"])
        self.assertFalse(r["submitted"])
