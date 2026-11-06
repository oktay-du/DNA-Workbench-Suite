"""Every pinned download has a Windows and Linux host decision."""

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import engine
import on_demand
import tool_hosts


class ToolHostTests(unittest.TestCase):
    def test_every_pin_has_one_decision(self):
        rows = tool_hosts.rows()
        items = tool_hosts.json.loads(tool_hosts.LOCK.read_text(encoding="utf-8"))[
            "items"
        ]
        self.assertEqual(len(rows), len(items))
        self.assertEqual(len({row["id"] for row in rows}), len(items))

    def test_windows_and_linux_binaries_stay_distinct(self):
        by_id = {row["id"]: row for row in tool_hosts.rows()}
        self.assertEqual(by_id["plink2-linux"]["linux"], "native")
        self.assertEqual(by_id["plink2-windows"]["windows"], "native")
        self.assertEqual(by_id["ubuntu-wsl"]["linux"], "not used")
        self.assertEqual(by_id["mosdepth"]["windows"], "samtools depth")
        self.assertIn("Win-NGS", by_id["samtools-1-23-1-windows"]["note"])
        if os.name == "nt":
            self.assertEqual(tool_hosts.prefer("gramps"), "grampsaio-6-0-8-1-win64-exe")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-23-1-windows")
        else:
            self.assertEqual(tool_hosts.prefer("gramps"), "gramps-6-0-8-1-amd64-snap")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-25-tar-bz2")
        with mock.patch.object(tool_hosts.os, "name", "nt"):
            self.assertEqual(tool_hosts.prefer("plink2"), "plink2-windows")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-23-1-windows")
            self.assertIsNone(tool_hosts.prefer("mosdepth"))
        self.assertTrue(
            all(
                row["linux"] != "wine" and row["windows"] != "wine"
                for row in tool_hosts.rows()
            )
        )

    def test_linux_host_keeps_a_native_path(self):
        if os.name == "nt":
            self.skipTest("Windows maps drive letters into WSL")
        path = engine.linux(Path(__file__).resolve())
        self.assertFalse(path.startswith("/mnt/"))
        self.assertTrue(path.endswith("test_tool_hosts.py"))

    def test_linux_file_is_installed_without_wsl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "mosdepth"
            blob.write_bytes(b"#!/bin/sh\necho mosdepth\n")
            with (
                mock.patch.object(on_demand, "ROOT", root),
                mock.patch.object(on_demand, "fetch", return_value=blob),
            ):
                result = on_demand.install_linux_local("mosdepth")
            target = root / "DNA_Software/Linux/bin/mosdepth"
            self.assertTrue(target.is_file())
            self.assertTrue(os.access(target, os.X_OK))
            self.assertIn("Linux file", result["status"])

    def test_windows_companion_extracts_the_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "samtools.zip"
            with zipfile.ZipFile(archive, "w") as packed:
                packed.writestr("samtools-1.23.1-windows-ucrt64/samtools.exe", b"MZ")
            with (
                mock.patch.object(on_demand, "ROOT", root),
                mock.patch.object(on_demand, "fetch", return_value=archive),
            ):
                result = on_demand.extract_windows_companion("samtools")
            found = list((root / "DNA_Software/Windows/Samtools").rglob("samtools.exe"))
            self.assertEqual(len(found), 1)
            self.assertIn("Windows file", result["status"])

    def test_place_archive_rejects_parent_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as packed:
                packed.writestr("../outside.txt", "nope")
            with self.assertRaises(ValueError):
                on_demand.place_archive(archive, root / "dest")

    def test_versions_page_matches_the_classifier(self):
        text = (
            Path(__file__)
            .resolve()
            .parents[2]
            .joinpath("docs/VERSIONS.md")
            .read_text(encoding="utf-8")
        )
        table = tool_hosts.markdown_table().strip()
        self.assertIn(table, text)


if __name__ == "__main__":
    unittest.main()
