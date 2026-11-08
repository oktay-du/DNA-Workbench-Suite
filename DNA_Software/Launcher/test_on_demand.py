import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import on_demand as demand


class DemandTests(unittest.TestCase):
    def test_internal_features_do_not_probe_linux(self):
        tasks = [
            t
            for t in demand.CAT["tasks"]
            if t.get("platform") != "WSL" and t.get("kind") != "launch"
        ]
        with patch.object(
            demand, "linux_state", side_effect=AssertionError("Unexpected Linux probe")
        ):
            for task in tasks:
                self.assertFalse(demand.status(task["id"])["needs_linux"])

    def test_stopped_linux_not_started_or_probed_by_status(self):
        task = next(t["id"] for t in demand.CAT["tasks"] if t.get("action") == "vcf_qc")
        with (
            patch.object(
                demand,
                "linux_state",
                return_value={"running": False, "disk": True, "state": "Linux starten"},
            ),
            patch.object(
                demand.subprocess,
                "run",
                side_effect=AssertionError("Unexpected process launch"),
            ),
        ):
            report = demand.status(task)
            self.assertFalse(report["ready"])
            self.assertIsNone(report["requirements"][0]["installed"])

    def test_rfmix_license_required_before_installer(self):
        with patch.object(
            demand,
            "linux_state",
            side_effect=AssertionError("Must reject before probing"),
        ):
            with self.assertRaisesRegex(ValueError, "Stanford"):
                demand.install("rfmix")

    def test_requirement_mapping_has_no_unknown_tool(self):
        for task in demand.CAT["tasks"]:
            for name in demand.mapped(task["id"]):
                self.assertIn(name, demand.TOOLS)

    def test_linux_pip_install_uses_the_suite_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(demand, "ROOT", root),
                patch.object(demand.os, "name", "posix"),
                patch.object(demand.subprocess, "run") as run,
            ):
                result = demand.install("snps")
        self.assertIn("suite package", result["status"])
        command = run.call_args.args[0]
        self.assertIn("--target", command)
        self.assertIn("snps==2.12.1", command)
        self.assertTrue(any(part.endswith("PythonPackages") for part in command))

    def test_linux_multiqc_wrapper_calls_the_suite_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(demand, "ROOT", root),
                patch.object(demand.os, "name", "posix"),
                patch.object(demand.subprocess, "run"),
            ):
                demand.install("multiqc")
            text = (root / "DNA_Software/Linux/bin/multiqc").read_text()
        self.assertIn("python3 -m multiqc", text)
        self.assertIn("PythonPackages", text)

    def test_linux_plink19_names_the_package_when_it_is_missing(self):
        with (
            patch.object(demand.os, "name", "posix"),
            patch.object(demand.shutil, "which", return_value=None),
        ):
            with self.assertRaisesRegex(ValueError, "plink1.9"):
                demand.install("plink19")

    def test_linux_plink_not_windows_executable(self):
        self.assertEqual(demand.TOOLS["plink2"][1], "plink2-linux")
        item = next(i for i in demand.LOCK["items"] if i["id"] == "plink2-linux")
        self.assertIn("linux", item["url"])
        self.assertTrue(item["expected_sha256"])


if __name__ == "__main__":
    unittest.main()
