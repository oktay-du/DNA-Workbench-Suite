"""VEP image pull and optional start. The GRCh38 cache is not downloaded here."""

import json
import os
import platform
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import on_demand
import system_tools


def vep_help_command(prefix, route, output):
    """Start vep --help with the same isolation as a Kiri annotation job."""
    command = [
        *prefix,
        "run",
        "--rm",
        "--pull=never",
        "--platform=" + route.platform,
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,mode=1777",
        "--mount",
        f"type=bind,source={output},target=/output",
        "--workdir",
        "/output",
        "--entrypoint",
        "/bin/sh",
    ]
    if os.name != "nt":
        command.extend(["--user", f"{os.getuid()}:{os.getgid()}"])
    command.extend([route.image, "-c", "HOME=/output vep --help"])
    return command


class VepImageTests(unittest.TestCase):
    def test_prepare_pulls_the_pinned_index_without_the_cache(self):
        calls = []

        def run(command, **_kwargs):
            calls.append(list(command))
            return subprocess.CompletedProcess(command, 0)

        with (
            patch.object(on_demand, "kiri_sequence_tool", side_effect=[None, object()]),
            patch.object(on_demand.subprocess, "run", side_effect=run),
            patch.object(on_demand, "fetch") as fetch,
        ):
            on_demand.prepare_vep_image(
                ["docker", "--host", "unix:///run/kiri/docker.sock"], {}
            )
        fetch.assert_not_called()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "docker")
        self.assertEqual(calls[0][-2:], ["pull", system_tools.KIRI_VEP_IMAGE])

    def test_prepare_skips_the_pull_when_the_image_is_present(self):
        with (
            patch.object(on_demand, "kiri_sequence_tool", return_value=object()),
            patch.object(on_demand.subprocess, "run") as run,
        ):
            on_demand.prepare_vep_image(["docker"], {})
        run.assert_not_called()

    def test_missing_image_after_the_pull_is_an_error(self):
        with (
            patch.object(on_demand, "kiri_sequence_tool", return_value=None),
            patch.object(
                on_demand.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["docker"], 0),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                on_demand.prepare_vep_image(["docker"], {})

    def test_install_prepares_the_image_before_the_cache(self):
        with (
            patch.object(on_demand, "kiri_docker", return_value=(["docker"], {})),
            patch.object(on_demand, "prepare_vep_image") as image,
            patch.object(
                on_demand, "install_vep_cache", return_value={"tool": "vep-cache"}
            ) as cache,
        ):
            result = on_demand.install("vep")
        image.assert_called_once_with(["docker"], {})
        cache.assert_called_once_with()
        self.assertEqual(result["tool"], "vep-cache")

    def test_help_command_uses_the_isolated_engine(self):
        route = system_tools.KiriRoute(
            ["docker"], {}, "linux/arm64", system_tools.KIRI_VEP_IMAGE_IDS["arm64"]
        )
        command = vep_help_command(route.prefix, route, "/output")
        self.assertIn("--pull=never", command)
        self.assertIn("--platform=linux/arm64", command)
        self.assertIn("--network=none", command)
        self.assertIn("--read-only", command)
        self.assertIn(system_tools.KIRI_VEP_IMAGE_IDS["arm64"], command)
        self.assertIn("HOME=/output vep --help", command)
        self.assertNotIn("vep-cache", " ".join(command))


class VepSmokeTests(unittest.TestCase):
    def test_requested_smoke_fails_without_the_engine(self):
        with (
            patch.dict(os.environ, {"DNA_VEP_SMOKE": "1"}),
            patch.object(on_demand, "kiri_docker", return_value=None),
        ):
            with self.assertRaisesRegex(AssertionError, "Docker socket"):
                self.test_pinned_image_starts()

    def test_pinned_image_starts(self):
        if os.environ.get("DNA_VEP_SMOKE") != "1":
            self.skipTest("Set DNA_VEP_SMOKE=1 to pull and start the pinned VEP image.")
        local = on_demand.kiri_docker()
        if local is None:
            self.fail("DNA_VEP_SMOKE=1 requires the local Kiri or Docker socket.")
        prefix, env = local
        on_demand.prepare_vep_image(prefix, env)
        route = system_tools.kiri_sequence_tool("vep")
        self.assertIsNotNone(route)
        machine = platform.machine().lower()
        expected = "linux/arm64" if machine in {"arm64", "aarch64"} else "linux/amd64"
        self.assertEqual(route.platform, expected)
        arch = expected.removeprefix("linux/")
        pinned = system_tools.KIRI_VEP_IMAGE_IDS[arch]
        if route.image == pinned:
            image_id = route.image
        else:
            inspected = subprocess.run(
                [*prefix, "image", "inspect", "--format", "{{.Id}}", route.image],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            image_id = inspected.stdout.strip()
        self.assertEqual(image_id, pinned)
        with tempfile.TemporaryDirectory() as output:
            completed = subprocess.run(
                vep_help_command(prefix, route, output),
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
        detail = completed.stdout + completed.stderr
        self.assertIn("version 116", detail.lower(), detail[-4000:])
        print(
            "VEP_SMOKE "
            + json.dumps(
                {
                    "machine": machine,
                    "platform": route.platform,
                    "image": image_id,
                    "help_status": completed.returncode,
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
