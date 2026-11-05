import unittest
from unittest.mock import patch
import local_ai


class LocalAITests(unittest.TestCase):
    def setUp(self):
        self.context = {
            "person": "P001_Test",
            "files": [],
            "ancestry_results": [],
            "jobs": [],
            "limits": [],
        }
        self.a = patch.object(
            local_ai.suite_api, "checked_person", side_effect=lambda x: x
        )
        self.b = patch.object(local_ai, "evidence", return_value=self.context)
        self.a.start()
        self.b.start()

    def tearDown(self):
        self.a.stop()
        self.b.stop()

    def test_model_receives_summaries_without_profile_or_report_text(self):
        import io, json

        self.context.update(
            profile={"name": "PRIVATE_NAME", "story_evidence": "PRIVATE_STORY"},
            document_evidence={
                "passages": [{"quote": "PRIVATE_REPORT"}],
                "manual_facts": [{"value": "PRIVATE_FACT"}],
            },
            files=[
                {
                    "provider": "23andMe",
                    "original_name": "PRIVATE_FILENAME",
                    "build": "GRCh38",
                }
            ],
            jobs=[{"status": "Complete", "title": "PRIVATE_JOB"}],
        )
        response = io.BytesIO(
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {"answer": "Use a suitable workflow", "actions": []}
                                )
                            }
                        }
                    ]
                }
            ).encode()
        )
        with (
            patch.object(local_ai, "KEY", "synthetic-test-token"),
            patch.object(local_ai, "ready", return_value=True),
            patch.object(local_ai, "start"),
            patch.object(
                local_ai.network_io, "open_loopback", return_value=response
            ) as send,
        ):
            result = local_ai.chat(
                {
                    "person": "P001_Test",
                    "message": "What should I do next?",
                    "language": "en",
                }
            )
        payload = json.loads(send.call_args.args[0].data)
        prompt = payload["messages"][1]["content"]
        for value in (
            "PRIVATE_NAME",
            "PRIVATE_STORY",
            "PRIVATE_REPORT",
            "PRIVATE_FACT",
            "PRIVATE_FILENAME",
            "PRIVATE_JOB",
            "P001_Test",
        ):
            self.assertNotIn(value, prompt)
        self.assertIn("GRCh38", prompt)
        self.assertIn("file_count", prompt)
        self.assertIs(result["evidence"], self.context)
        self.assertEqual(result["mode"], "local-model")

    def test_missing_ancestry_never_calls_model(self):
        with patch.object(
            local_ai, "start", side_effect=AssertionError("Must not infer")
        ):
            r = local_ai.chat(
                {
                    "person": "P001_Test",
                    "message": "Which countries do I come from?",
                    "language": "de",
                }
            )
        self.assertEqual(r["mode"], "verified-suite-answer")
        self.assertIn("no registered", r["answer"])

    def test_relationship_guidance_uses_relevant_tools(self):
        r = local_ai.chat(
            {
                "person": "P001_Test",
                "message": "Which tools check relatedness?",
                "language": "en",
            }
        )
        self.assertEqual([a["task"] for a in r["actions"]], ["kinship", "peddy", "ibd"])
        self.assertNotIn("missing", r["answer"])

    def test_typed_direct_navigation(self):
        r = local_ai.chat(
            {"person": "P001_Test", "message": "Open import", "language": "de"}
        )
        self.assertTrue(r["auto_action"])
        self.assertEqual(r["actions"][0]["route"], "import")

    def test_unknown_actions_cannot_become_shell_or_file_access(self):
        r = local_ai.safe_actions(
            [
                {"type": "shell", "command": "anything"},
                {"type": "navigate", "route": "https://external"},
                {"type": "task", "task": "unknown"},
                {"type": "task", "task": "kinship"},
            ]
        )
        self.assertEqual(r, [{"type": "task", "task": "kinship"}])

    def test_results_remain_separate_by_source(self):
        self.context["ancestry_results"] = [
            {
                "provider": "Synthetic A",
                "model": "Test",
                "version": "1",
                "regions": [{"name": "Example region", "percent": 25}],
            }
        ]
        r = local_ai.chat(
            {
                "person": "P001_Test",
                "message": "Show my ancestry results",
                "language": "en",
            }
        )
        # Direct show commands navigate; a factual question returns source-backed text.
        r = local_ai.chat(
            {
                "person": "P001_Test",
                "message": "What ancestry results exist?",
                "language": "en",
            }
        )
        self.assertIn("Synthetic A", r["answer"])
        self.assertIn("25%", r["answer"])


if __name__ == "__main__":
    unittest.main()
