"""The runtime matrix stays aligned with the catalog and tool registry."""

import json
import unittest
from pathlib import Path

import on_demand
import tool_runtime
import workflows


class ToolRuntimeDocumentTests(unittest.TestCase):
    def test_document_matches_the_registry(self):
        document = Path(__file__).resolve().parents[2] / "docs/TOOL_RUNTIME.md"
        text = tool_runtime.render()
        self.assertEqual(document.read_text(encoding="utf-8"), text)
        tasks = json.loads(
            Path(__file__).with_name("catalog.json").read_text(encoding="utf-8")
        )["tasks"]
        for task in tasks:
            self.assertIn(f"`{task['id']}`", text)
        for tool in on_demand.TOOLS:
            self.assertIn(f"`{tool}`", text)
        for name in workflows.RECIPES:
            self.assertIn(f"`{name}`", text)
        self.assertEqual(len(tool_runtime.open_linux_arm64_tools()), 46)
        self.assertNotIn("rfmix", tool_runtime.open_linux_arm64_tools())
        self.assertIn("qemu-aarch64-static", text)
        self.assertIn("Debian arm64 image was executed", text)
        self.assertIn("Debian amd64 image was executed", text)
        self.assertIn("ubuntu-24.04-arm", text)
        self.assertIn("27644657162", text)
        self.assertIn("recorded as passed here", text)
