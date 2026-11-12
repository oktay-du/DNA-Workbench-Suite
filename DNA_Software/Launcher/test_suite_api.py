import json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, engine, mcp_dna


class SuiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(family, "DB", self.root / "family.sqlite"),
            patch.object(family, "ROOT", self.root),
            patch.object(source_store, "ROOT", self.root),
            patch.object(suite_api, "ROOT", self.root),
            patch.object(engine, "ROOT", self.root),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.execute(
                "INSERT INTO people VALUES(?,?,0)", ("P001_Test", "Test profile")
            )

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_settings_persist_and_validate(self):
        suite_api.settings({"language": "en", "theme": "dark"})
        self.assertEqual(suite_api.settings()["theme"], "dark")
        with self.assertRaises(ValueError):
            suite_api.settings({"language": "unknown", "theme": "dark"})

    def test_job_path_traversal_denied(self):
        for name in ["../other", "x/y", "C:\\Windows"]:
            with self.assertRaises(ValueError):
                suite_api.job_path("P001_Test", name)

    def test_unknown_workflow_and_inputs_do_not_execute(self):
        with patch.object(
            suite_api.subprocess,
            "Popen",
            side_effect=AssertionError("Must not execute"),
        ):
            with self.assertRaises(ValueError):
                suite_api.start(
                    {"person": "P001_Test", "task": "arbitrary-shell", "inputs": {}}
                )
            with self.assertRaises(ValueError):
                suite_api.start(
                    {
                        "person": "P001_Test",
                        "task": "report",
                        "inputs": {"shell": "echo bad"},
                    }
                )

    def test_missing_required_files_block_launch(self):
        with patch.object(
            suite_api.subprocess,
            "Popen",
            side_effect=AssertionError("Must not execute"),
        ):
            with self.assertRaises(ValueError):
                suite_api.start(
                    {"person": "P001_Test", "task": "kinship", "inputs": {}}
                )

    def test_mcp_result_read_is_bounded_to_job(self):
        path = suite_api.job_path("P001_Test", "demo") / "Results"
        path.mkdir(parents=True)
        (path / "summary.txt").write_text("synthetic evidence")
        args = {"person": "P001_Test", "job": "demo", "file": "summary.txt"}
        self.assertEqual(
            mcp_dna.call("read_result", args)["text"], "synthetic evidence"
        )
        with self.assertRaises(ValueError):
            mcp_dna.call("read_result", dict(args, file="../inputs.json"))

    def test_mcp_import_requires_explicit_storage_mode(self):
        with self.assertRaises(ValueError):
            mcp_dna.call(
                "run_workflow", {"person": "P001_Test", "task": "import", "inputs": {}}
            )

    def test_detected_build_mismatch_blocks_launch(self):
        p = self.root / "synthetic.vcf"
        p.write_text("##fileformat=VCFv4.2\n##reference=GRCh38\n")
        with patch.object(
            suite_api.subprocess,
            "Popen",
            side_effect=AssertionError("Must not execute"),
        ):
            with self.assertRaises(ValueError):
                suite_api.start(
                    {
                        "person": "P001_Test",
                        "task": "pharmcat",
                        "inputs": {"vcf": str(p), "build": "GRCh37"},
                    }
                )

    def test_multiqc_report_stays_inside_the_preview(self):
        folder = suite_api.job_path("P001_Test", "demo") / "Results"
        folder.mkdir(parents=True)
        page = "<h1>MultiQC</h1>" + ("A" * 600000)
        (folder / "multiqc_report.html").write_text(page, encoding="utf-8")
        result = suite_api.dispatch(
            "result-preview",
            {"person": "P001_Test", "job": "demo", "file": "multiqc_report.html"},
        )
        self.assertTrue(result["interactive_report"])
        self.assertFalse(result["truncated"])
        self.assertTrue(result["text"].startswith("<h1>MultiQC</h1>"))
        self.assertEqual(len(result["text"]), len(page))

    def test_result_preview_cannot_escape_output(self):
        p = suite_api.job_path("P001_Test", "demo")
        (p / "Results").mkdir(parents=True)
        (p / "inputs.json").write_text("private request")
        with self.assertRaises(ValueError):
            suite_api.dispatch(
                "result-preview",
                {"person": "P001_Test", "job": "demo", "file": "../inputs.json"},
            )

    def test_import_availability_does_not_start_renewal(self):
        import profile_pipeline

        profile_pipeline.atomic(
            profile_pipeline.queue_path("P001_Test"),
            {"person": "P001_Test", "status": "available"},
        )
        with patch.object(suite_api, "start") as launch:
            suite_api.refresh_tick()
            launch.assert_not_called()

    def test_explicit_renewal_queues_behind_running_job_and_can_be_cancelled(self):
        import profile_pipeline

        busy = type("Busy", (), {"poll": lambda self: None})()
        with (
            patch.object(
                profile_pipeline,
                "summary",
                return_value={"sets": [{"build": "GRCh38"}], "refresh": {}},
            ),
            patch.object(suite_api, "PROCESSES", {"busy": busy}),
        ):
            result = suite_api.submit_renewal({"person": "P001_Test"})
        path = suite_api.job_path("P001_Test", result["job"])
        self.assertEqual(
            json.loads((path / "status.json").read_text())["status"], "Queued"
        )
        suite_api.dispatch("cancel", result)
        self.assertEqual(
            json.loads((path / "status.json").read_text())["status"], "Cancelled"
        )
        self.assertEqual(
            json.loads(profile_pipeline.queue_path("P001_Test").read_text())["status"],
            "cancelled",
        )

    def test_shell_http_requires_local_token(self):
        server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        server.token = "synthetic-suite"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = "http://127.0.0.1:" + str(server.server_port)
        try:
            self.assertRegex(
                urllib.request.urlopen(url + "/app").read().decode(),
                r'DNA_SUITE_TOKEN\s*=\s*"synthetic-suite"',
            )
            req = urllib.request.Request(
                url + "/suite/settings",
                data=b'{"language":"en","theme":"dark"}',
                headers={"X-DNA-Token": "synthetic-suite"},
            )
            self.assertEqual(json.load(urllib.request.urlopen(req))["theme"], "dark")
            req = urllib.request.Request(url + "/suite/snapshot", data=b"{}")
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(req)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
