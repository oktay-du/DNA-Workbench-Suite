import json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, command_bus, agent_control, agent_client, dna_cli, mcp_dna, local_ai


class AgentControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(suite_api, "ROOT", self.root),
            patch.object(source_store, "ROOT", self.root),
            patch.object(family, "ROOT", self.root),
            patch.object(family, "DB", self.root / "family.sqlite"),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.execute(
                "INSERT INTO people VALUES(?,?,0)", ("P001_Demo", "Synthetic person")
            )
        command_bus.REQUESTS.clear()
        agent_control.EVENTS.clear()
        self.server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        self.server.token = "private-fixture-token"
        agent_control.publish(self.server, gui=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = agent_client.Client(agent_control.control_path())

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        agent_control.unpublish()
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_manifest_covers_workflows_and_contains_no_session_or_personal_data(self):
        manifest = command_bus.manifest()
        ids = [c["id"] for c in manifest["commands"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(
            {"workflow." + t["id"] for t in suite_api.CAT()["tasks"]} <= set(ids)
        )
        text = json.dumps(manifest)
        self.assertNotIn(self.server.token, text)
        self.assertNotIn("Synthetic person", text)
        self.assertFalse(manifest["policy"]["automaticRenewalOnImport"])
        self.assertEqual(len(command_bus.openapi()["paths"]), len(ids))

    def test_live_cli_json_and_mcp_share_state_and_validation(self):
        request = {
            "id": 7,
            "method": "command.execute",
            "params": {
                "command": "settings.update",
                "arguments": {"language": "en", "theme": "dark"},
            },
        }
        response = dna_cli.rpc(request, self.client)
        self.assertTrue(response["result"]["ok"])
        self.assertEqual(suite_api.settings()["theme"], "dark")
        response = mcp_dna.respond(
            {
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "dna_settings__update",
                    "arguments": {"language": "de", "theme": "light"},
                },
            },
            self.client,
        )
        self.assertNotIn("isError", response["result"])
        self.assertEqual(suite_api.settings()["theme"], "light")
        with self.assertRaises(agent_client.ClientError):
            self.client.call("settings.update", {"language": "bad", "theme": "light"})

    def test_unknown_commands_and_fields_never_spawn(self):
        with patch.object(
            suite_api.subprocess, "Popen", side_effect=AssertionError("Must not spawn")
        ):
            with self.assertRaises(agent_client.ClientError):
                self.client.call("shell.exec", {"command": "anything"})
            with self.assertRaises(agent_client.ClientError):
                self.client.call(
                    "workflow.vcf_qc",
                    {
                        "person": "P001_Demo",
                        "inputs": {"vcf": "missing", "shell": "anything"},
                    },
                )

    def test_import_requires_explicit_move_or_copy(self):
        with self.assertRaises(command_bus.CommandError):
            command_bus.execute(
                "workflow.import",
                {
                    "person": "P001_Demo",
                    "inputs": {"files": ["file"], "provider": "Test"},
                },
            )

    def test_request_id_deduplicates_mutation_and_rejects_reuse(self):
        a = self.client.call("profile.create", {"label": "New fixture"}, "same-request")
        b = self.client.call("profile.create", {"label": "New fixture"}, "same-request")
        self.assertEqual(a, b)
        with self.assertRaises(agent_client.ClientError):
            self.client.call(
                "profile.create", {"label": "Other fixture"}, "same-request"
            )

    def test_gui_events_are_pending_until_acknowledged(self):
        result = self.client.call("menu.health", {"person": "P001_Demo"})["result"]
        self.assertFalse(result["acknowledged"])
        events = self.client.post(
            "/agent/ui/poll", {"client": "fixture-gui", "view": {"route": "sources"}}
        )["events"]
        self.assertEqual(events[0]["payload"]["route"], "health")
        self.client.post(
            "/agent/ui/ack",
            {"client": "fixture-gui", "event_id": result["event_id"], "ok": True},
        )
        state = self.client.call("ui.state")["result"]
        self.assertEqual(state["events"][-1]["status"], "applied")
        self.assertTrue(state["attached"])

    def test_no_gui_does_not_claim_navigation_succeeded(self):
        with patch.object(agent_control, "GUI", False):
            with self.assertRaises(agent_client.ClientError) as error:
                self.client.call("menu.health")
        self.assertEqual(error.exception.code, "NO_GUI")

    def test_gui_form_fill_rejects_undeclared_fields(self):
        with self.assertRaises(agent_client.ClientError):
            self.client.call(
                "ui.open_workflow", {"task": "pharmcat", "inputs": {"cmd": "anything"}}
            )

    def test_compact_navigation_uses_typed_gui_channel(self):
        result = self.client.call("ui.navigation", {"open": True})["result"]
        self.assertFalse(result["acknowledged"])
        events = self.client.post(
            "/agent/ui/poll",
            {"client": "fixture-navigation", "view": {"route": "dashboard"}},
        )["events"]
        self.assertEqual(events[0]["payload"], {"open": True, "type": "navigation"})
        with self.assertRaises(agent_client.ClientError):
            self.client.call("ui.navigation", {"open": "yes"})

    def test_loopback_client_refuses_external_host_before_connecting(self):
        path = self.root / "external.json"
        path.write_text(
            json.dumps({"url": "http://example.org:1234", "token": "secret"})
        )
        with patch.object(
            agent_client.http.client,
            "HTTPConnection",
            side_effect=AssertionError("No network"),
        ):
            with self.assertRaises(agent_client.ClientError):
                agent_client.Client(path)

    def test_http_token_required_for_execution_and_manifest_does_not_leak_token(self):
        url = "http://127.0.0.1:" + str(self.server.server_port)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        # Use the same direct, bounded loopback transport as the CLI,
        # without proxy or redirect handlers.
        connection = agent_client.http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=10
        )
        try:
            connection.request("GET", "/agent/manifest")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            expected = int(response.getheader("Content-Length"))
            self.assertLess(expected, 16 * 1024 * 1024)
            chunks = []
            remaining = expected
            while remaining:
                part = response.read1(min(16384, remaining))
                self.assertTrue(part, "Manifest response ended before Content-Length")
                chunks.append(part)
                remaining -= len(part)
            text = b"".join(chunks).decode()
        finally:
            connection.close()
        self.assertNotIn(self.server.token, text)
        request = urllib.request.Request(
            url + "/agent/execute", data=b'{"command":"ui.state","arguments":{}}'
        )
        with self.assertRaises(urllib.error.HTTPError) as error:
            opener.open(request, timeout=10)
        self.assertEqual(error.exception.code, 403)

    def test_mcp_tool_names_unique_and_notifications_do_not_execute(self):
        names = [t["name"] for t in mcp_dna.definitions()]
        self.assertEqual(len(names), len(set(names)))
        with patch.object(
            mcp_dna, "call", side_effect=AssertionError("No notification execution")
        ):
            self.assertIsNone(
                mcp_dna.respond(
                    {"method": "tools/call", "params": {"name": "run_workflow"}}
                )
            )

    def test_local_chat_explicit_command_does_not_need_model(self):
        with patch.object(
            local_ai, "start", side_effect=AssertionError("Do not load model")
        ):
            result = local_ai.chat(
                {
                    "person": "P001_Demo",
                    "message": "/command job.list {}",
                    "language": "de",
                }
            )
        self.assertEqual(result["mode"], "typed-command-result")
        self.assertEqual(json.loads(result["answer"])["result"]["jobs"], [])

    def test_ancestry_context_reads_actual_saved_report_shape(self):
        report = {
            "person": "P001_Demo",
            "data": {
                "provider": "Synthetic source",
                "model": "Fixture",
                "version": "1",
                "regions": [{"name": "Fixture region", "percent": 100}],
            },
        }
        with patch.object(local_ai.visual_store, "listing", return_value=[report]):
            result = local_ai.evidence("P001_Demo")
        self.assertEqual(result["ancestry_results"][0]["provider"], "Synthetic source")

    def test_dependency_install_accepts_only_declared_recipe_ids(self):
        import plugin_hub

        with patch.object(
            plugin_hub, "submit", return_value={"job": "synthetic-plugin-job"}
        ) as submit:
            result = command_bus.execute("dependency.install", {"tool": "pyliftover"})
            self.assertEqual(result["result"]["job"], "synthetic-plugin-job")
            self.assertEqual(submit.call_args.args[0]["action"], "install-tool")
            with self.assertRaises(command_bus.CommandError):
                command_bus.execute(
                    "dependency.install", {"tool": "arbitrary package or shell"}
                )
            self.assertEqual(submit.call_count, 1)

    def test_second_service_cannot_replace_live_control_metadata(self):
        before = agent_control.control_path().read_bytes()
        other = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        other.token = "other-token"
        try:
            with self.assertRaises(RuntimeError):
                agent_control.publish(other, gui=False)
            self.assertEqual(agent_control.control_path().read_bytes(), before)
        finally:
            other.server_close()


if __name__ == "__main__":
    unittest.main()
