import hashlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import hardware
import local_ai
import local_ai_runtime as runtime


class HardwareTests(unittest.TestCase):
    def test_cpu_budget_respects_available_cores(self):
        count = (
            "process_cpu_count"
            if hasattr(hardware.os, "process_cpu_count")
            else "cpu_count"
        )
        with patch.object(hardware.os, count, return_value=2):
            self.assertEqual(hardware.cpu_threads(), 1)
        self.assertLessEqual(hardware.cpu_threads(4), 4)

    def test_all_pinned_runtime_assets_have_hash_and_size(self):
        for builds in runtime.PACKAGES["platforms"].values():
            for assets in builds.values():
                for name, size, digest in assets:
                    self.assertTrue(name.endswith((".zip", ".tar.gz")))
                    self.assertGreater(size, 0)
                    self.assertRegex(digest, re.compile(r"^[0-9a-f]{64}$"))

    def test_gpu_order_and_device_filter(self):
        self.assertEqual(
            runtime.candidates(
                {"nvidia", "amd", "intel"}, {"cuda", "rocm", "sycl", "vulkan"}
            ),
            ["cuda", "rocm", "vulkan", "sycl"],
        )
        text = (
            "init: Vulkan1: initialize\nAvailable devices:\n"
            "  Vulkan0: Microsoft Basic Render Driver (16384 MiB, 16384 MiB free)\n"
            "  Vulkan1: NVIDIA (8192 MiB, 128 MiB free)\n"
            "  Vulkan2: AMD (4096 MiB, 3200 MiB free)\n"
        )
        self.assertEqual(runtime.select_device(text, "vulkan"), "Vulkan2")
        hybrid = text.replace(
            "NVIDIA (8192 MiB, 128 MiB free)", "NVIDIA (8192 MiB, 6000 MiB free)"
        ).replace(
            "AMD (4096 MiB, 3200 MiB free)", "Intel UHD (16384 MiB, 14000 MiB free)"
        )
        self.assertEqual(runtime.select_device(hybrid, "vulkan"), "Vulkan1")
        self.assertEqual(
            runtime.candidates({"intel"}, {"sycl", "vulkan"}), ["sycl", "vulkan"]
        )
        self.assertEqual(
            runtime.select_device("Available devices:\n  MTL0: Apple", "metal"), "MTL0"
        )
        self.assertIsNone(runtime.select_device("  Vulkan0: software device", "vulkan"))

    def test_windows_arm64_can_choose_adreno_opencl(self):
        packages = runtime.PACKAGES["platforms"]["Windows-arm64"]
        self.assertEqual(
            runtime.candidates({"qualcomm"}, packages), ["opencl", "vulkan"]
        )
        text = "Available devices:\n  GPUOpenCL: Qualcomm Adreno GPU (2048 MiB, 1700 MiB free)"
        self.assertEqual(runtime.select_device(text, "opencl"), "GPUOpenCL")

    def test_runtime_download_is_verified_before_publish(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("llama-server.exe", b"binary")
        payload = stream.getvalue()
        digest = hashlib.sha256(payload).hexdigest()
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(runtime.platform, "system", return_value="Windows"),
            patch.object(
                runtime.network_io,
                "open_https",
                side_effect=lambda *a, **k: io.BytesIO(payload),
            ),
        ):
            base = Path(folder)
            with patch.object(
                runtime,
                "builds",
                return_value={"cuda": [["x.zip", len(payload), "0" * 64]]},
            ):
                with self.assertRaisesRegex(ValueError, "checksum"):
                    runtime.install(base, "cuda")
                self.assertIsNone(runtime.executable(base, "cuda"))
            with patch.object(
                runtime,
                "builds",
                return_value={"cuda": [["x.zip", len(payload), digest]]},
            ):
                self.assertEqual(runtime.install(base, "cuda").read_bytes(), b"binary")

    def test_failed_accelerator_server_falls_back_to_cpu(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(local_ai, "STATE", Path(folder)),
            patch.object(local_ai, "SERVER", None),
            patch.object(local_ai, "PORT", None),
            patch.object(local_ai, "KEY", None),
            patch.object(local_ai, "ready", return_value=True),
            patch.object(local_ai, "prepare_runtime"),
            patch.object(hardware, "gpu_vendors", return_value={"nvidia"}),
            patch.object(runtime, "builds", return_value={"cuda": []}),
            patch.object(
                runtime, "executable", side_effect=lambda base, backend: Path(backend)
            ),
            patch.object(runtime, "device", return_value="CUDA0"),
            patch.object(
                local_ai,
                "start_server",
                side_effect=[ValueError("driver error"), "cpu server"],
            ) as start,
        ):
            local_ai.start()
            self.assertEqual(local_ai.SERVER, "cpu server")
            self.assertEqual(
                [entry.args for entry in start.call_args_list],
                [(Path("cuda"), "CUDA0"), (Path("cpu"), None)],
            )


if __name__ == "__main__":
    unittest.main()
