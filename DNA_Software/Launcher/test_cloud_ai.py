import os, unittest, tempfile, json, time, contextlib
from pathlib import Path
from unittest.mock import patch
import cloud_ai as c


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.object(c, "STATE", Path(self.tmp.name)))
        self.stack.enter_context(
            patch.dict(
                os.environ,
                {"DNA_CREDENTIAL_HOME": str(Path(self.tmp.name) / "config")},
                clear=False,
            )
        )
        c.REVIEWS.clear()
        c.JOBS.clear()

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def enable(self):
        c.save(
            {
                "api_key": "test-not-a-real-api-key",
                "enabled": True,
                "chat_enabled": True,
                "images_enabled": True,
                "chat_model": "test-model",
                "image_model": "test-image",
            }
        )

    def wait(self, id):
        for _ in range(200):
            r = c.job(id)
            if r["state"] != "running":
                return r
            time.sleep(0.01)
        self.fail("Cloud fixture did not finish")

    def test_disabled_and_no_network_on_defaults(self):
        with patch.object(c, "request", side_effect=AssertionError("No network")):
            self.assertFalse(c.status()["enabled"])
            with self.assertRaises(ValueError):
                c.prepare({"kind": "chat", "text": "hello"})

    def test_key_encrypted_and_not_in_status_or_config(self):
        self.enable()
        self.assertTrue(c.status()["key_present"])
        self.assertNotIn("test-not-a-real-api-key", json.dumps(c.status()))
        self.assertNotIn(
            b"test-not-a-real-api-key", (c.STATE / "openai.dpapi").read_bytes()
        )
        self.assertEqual(c.key(), "test-not-a-real-api-key")
        if os.name != "nt":
            stored = (c.STATE / "openai.dpapi").read_bytes()
            self.assertTrue(stored.startswith(b"DNACRED1"))
            key_file = (
                Path(os.environ["DNA_CREDENTIAL_HOME"])
                / "dna-workbench"
                / "api-credential.key"
            )
            self.assertEqual(key_file.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(b"test-not-a-real-api-key", key_file.read_bytes())
            with patch.dict(
                os.environ,
                {"DNA_CREDENTIAL_HOME": str(Path(self.tmp.name) / "other")},
            ):
                with self.assertRaises(ValueError):
                    c.crypt(stored, True)
            self.assertEqual(c.key(), "test-not-a-real-api-key")
        c.save({"remove_key": True})
        self.assertFalse(c.status()["enabled"])
        self.assertFalse(c.status()["key_present"])

    def test_activation_needs_key_and_model(self):
        with self.assertRaises(ValueError):
            c.save({"enabled": True})
        with self.assertRaises(ValueError):
            c.save({"assistant": "api"})

    def test_no_profile_context_by_default(self):
        self.enable()
        with patch("local_ai.evidence", side_effect=AssertionError("No profile reads")):
            r = c.prepare({"kind": "chat", "person": "P1", "text": "Help with suite"})
        self.assertFalse(r["includes_profile_evidence"])
        self.assertTrue(r["outbound"].startswith("Help with suite"))
        self.assertIn("AVAILABLE SUITE TASKS", r["outbound"])

    def test_evidence_requires_preview_and_confirmation(self):
        self.enable()
        with patch("local_ai.evidence", return_value={"fact": "SENSITIVE-TEST"}):
            r = c.prepare(
                {
                    "kind": "chat",
                    "person": "P1",
                    "text": "Question",
                    "include_evidence": True,
                }
            )
        self.assertIn("SENSITIVE-TEST", r["outbound"])
        with self.assertRaises(ValueError):
            c.submit({"review_token": r["review_token"]})
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "Suggested next steps"}
                    ],
                }
            ]
        }
        with patch.object(c, "request", return_value=response) as network:
            id = c.submit({"review_token": r["review_token"], "confirmed": True})["job"]
            done = self.wait(id)
        self.assertEqual(done["state"], "completed")
        self.assertEqual(done["result"]["actions"], [])
        self.assertEqual(network.call_count, 1)
        self.assertFalse(network.call_args.args[1]["store"])
        with self.assertRaises(ValueError):
            c.submit({"review_token": r["review_token"], "confirmed": True})
        self.assertNotIn(
            "SENSITIVE-TEST", (c.STATE / "jobs" / (id + ".json")).read_text()
        )

    def test_expired_and_changed_config_review_rejected(self):
        self.enable()
        r = c.prepare({"kind": "chat", "text": "Question"})
        c.REVIEWS[r["review_token"]]["review"]["expires"] = 0
        with self.assertRaises(ValueError):
            c.submit({"review_token": r["review_token"], "confirmed": True})
        r = c.prepare({"kind": "chat", "text": "Question"})
        c.save({"enabled": False})
        with self.assertRaises(ValueError):
            c.submit({"review_token": r["review_token"], "confirmed": True})

    def test_failure_never_echoes_remote_secret_or_retries(self):
        self.enable()
        r = c.prepare({"kind": "chat", "text": "Question"})
        with patch.object(
            c, "request", side_effect=RuntimeError("secret-value-from-provider")
        ) as network:
            done = self.wait(
                c.submit({"review_token": r["review_token"], "confirmed": True})["job"]
            )
        self.assertEqual(done["state"], "failed")
        self.assertNotIn("secret-value", json.dumps(done))
        self.assertEqual(network.call_count, 1)

    def test_image_bound_to_slot_and_imported_as_art(self):
        self.enable()
        with patch("story_art.selected", return_value={"id": "farmer"}):
            r = c.prepare(
                {
                    "kind": "image",
                    "person": "P1",
                    "slot": "farmer",
                    "text": "An educational painting",
                }
            )
        with (
            patch.object(c, "request", return_value={"data": [{"b64_json": "YXJ0"}]}),
            patch("story_art.upload", return_value={"document": "ART"}) as upload,
        ):
            done = self.wait(
                c.submit({"review_token": r["review_token"], "confirmed": True})["job"]
            )
        self.assertEqual(done["state"], "completed")
        self.assertEqual(upload.call_args.args, ("P1", "farmer"))
        self.assertEqual(upload.call_args.kwargs["provider"], "OpenAI · test-image")

    def test_registry_surfaces_and_no_arbitrary_url(self):
        import command_bus

        ids = {x["id"] for x in command_bus.definitions()}
        self.assertTrue(
            {
                "cloud.settings",
                "cloud.prepare",
                "cloud.submit",
                "cloud.job",
                "cloud.capabilities",
            }
            <= ids
        )
        with self.assertRaises(ValueError):
            c.save({"provider": "arbitrary"})
        with self.assertRaises(command_bus.CommandError):
            command_bus.validate(
                {"kind": "chat", "text": "q", "endpoint": "http://localhost"},
                next(
                    x["inputSchema"]
                    for x in command_bus.definitions()
                    if x["id"] == "cloud.prepare"
                ),
            )

    def test_restart_exposes_interrupted_job_without_retry(self):
        c.atomic(
            c.STATE / "jobs" / ("a" * 32 + ".json"),
            {
                "id": "a" * 32,
                "person": "P1",
                "kind": "chat",
                "state": "running",
                "started": 1,
            },
        )
        with patch.object(c, "request", side_effect=AssertionError("Never retry")):
            self.assertEqual(c.job("a" * 32)["state"], "interrupted")
            self.assertEqual(c.jobs()["jobs"][0]["person"], "P1")

    def test_orchestration_plan_uses_existing_planner_and_does_not_execute(self):
        with (
            patch("suite_api.checked_person", return_value="P1"),
            patch(
                "workflows.plan", return_value={"steps": [{"status": "reused"}]}
            ) as planner,
            patch("workflows.start", side_effect=AssertionError("Never start")),
        ):
            r = c.plan({"person": "P1", "goal": "health"})
            self.assertFalse(r["executed"])
            self.assertEqual(r["start_command"]["command"], "workflows.start")
            planner.assert_called_once_with("P1", "health")


if __name__ == "__main__":
    unittest.main()
