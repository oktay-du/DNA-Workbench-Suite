import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import on_demand as demand
import system_tools


class DemandTests(unittest.TestCase):
    def test_verified_reference_download_resumes_and_checks_entire_archive(self):
        import hashlib
        import io

        data = b"reference archive"
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "cache.tar.gz"
            part = destination.with_suffix(".gz.part")
            part.write_bytes(data[:5])
            response = io.BytesIO(data[5:])
            response.status = 206
            response.headers = {"Content-Range": f"bytes 5-{len(data) - 1}/{len(data)}"}
            item = {
                "url": "https://example.invalid/cache.tar.gz",
                "expected_bytes": len(data),
                "expected_sha256": hashlib.sha256(data).hexdigest(),
            }
            with patch.object(
                demand.network_io, "open_https", return_value=response
            ) as download:
                demand.fetch_verified(item, destination, part)
            self.assertEqual(download.call_args.args[0].get_header("Range"), "bytes=5-")
            self.assertEqual(destination.read_bytes(), data)
            self.assertFalse(part.exists())

    def test_native_pipeline_skips_unresponsive_sockets_and_remote_context(self):
        with (
            patch.object(demand.sys, "platform", "linux"),
            patch.object(demand, "host_command", return_value="/usr/bin/docker"),
            patch.object(Path, "is_socket", return_value=True),
            patch.dict(
                os.environ, {"DOCKER_CONTEXT": "remote", "DOCKER_HOST": "tcp://remote"}
            ),
            patch.object(
                demand.subprocess,
                "run",
                side_effect=[
                    subprocess.TimeoutExpired("docker", 3),
                    Mock(returncode=0, stdout="linux\n"),
                ],
            ) as run,
        ):
            socket = demand.native_pipeline_docker_socket()
        self.assertEqual(socket, str(Path.home() / ".docker/desktop/docker.sock"))
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0][1:3], ["--host", "unix://" + socket])
        self.assertNotIn("DOCKER_CONTEXT", run.call_args.kwargs["env"])
        self.assertNotIn("DOCKER_HOST", run.call_args.kwargs["env"])

    def test_nextflow_install_uses_the_verified_standalone_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path_type = type(folder)
            source = folder / "download"
            source.write_bytes(b"verified nextflow distribution")
            with (
                patch.object(demand, "LOG", folder),
                patch.object(demand, "Path", path_type),
                patch.object(demand.os, "name", "posix"),
                patch.object(demand, "fetch", return_value=source) as fetch,
            ):
                path = path_type(demand.install("nextflow")["path"])
                self.assertEqual(demand.host_command("nextflow"), str(path))
            fetch.assert_called_once_with("nextflow-dist")
            self.assertEqual(path.read_bytes(), source.read_bytes())
            self.assertTrue(os.access(path, os.X_OK))

    def test_windows_kiri_pipeline_requires_both_images_on_the_same_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "main.nf").touch()
            launcher = folder / "nextflow"
            launcher.touch()
            route = system_tools.KiriRoute(["docker"], {}, "linux/amd64", "nextflow")
            prep = route._replace(image="plink")
            for platform in ("linux/amd64", "linux/arm64"):
                with (
                    self.subTest(platform=platform),
                    patch.object(demand.os, "name", "nt"),
                    patch.object(demand, "ROOT", folder),
                    patch.dict(demand.NEXTFLOW_DIST, {"relative_path": "nextflow"}),
                    patch.object(demand, "native_pipeline_source", return_value=folder),
                    patch.object(
                        demand,
                        "kiri_sequence_tool",
                        side_effect=[route, prep._replace(platform=platform)],
                    ),
                ):
                    setup = demand.windows_kiri_pipeline("pgs")
                if platform == "linux/amd64":
                    self.assertEqual(setup, (route, prep, folder, launcher))
                else:
                    self.assertIsNone(setup)

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
            patch.object(system_tools, "kiri_windows_pipe_exists", return_value=False),
            patch.object(Path, "is_socket", return_value=False),
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
        with (
            patch.object(demand, "rfmix_license_reviewed", return_value=False),
            patch.object(
                demand,
                "linux_state",
                side_effect=AssertionError("Must reject before probing"),
            ),
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
