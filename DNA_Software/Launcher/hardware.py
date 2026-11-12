"""Host resources for local tools. Detection never starts WSL or installs drivers."""

from functools import lru_cache
import os
from pathlib import Path
import platform
import subprocess
import threading


def windows_arm64():
    if os.name != "nt":
        return False
    machine = os.environ.get("PROCESSOR_ARCHITEW6432") or platform.machine()
    return machine.lower() in {"arm64", "aarch64"}


def cpu_threads(limit=8):
    count = getattr(os, "process_cpu_count", os.cpu_count)() or 1
    if hasattr(os, "sched_getaffinity"):
        count = min(count, len(os.sched_getaffinity(0)))
    return max(1, min(limit, count - 1))


@lru_cache(maxsize=1)
def gpu_vendors():
    system = platform.system()
    if system == "Windows":
        from system_tools import windows_executable

        try:
            result = subprocess.run(
                [
                    windows_executable("powershell.exe"),
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | ForEach-Object { $_.PNPDeviceID; $_.Name }",
                ],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError, ValueError):
            return frozenset()
        ids = result.stdout.upper()
        vendors = {
            vendor
            for pci, vendor in {
                "10DE": "nvidia",
                "1002": "amd",
                "8086": "intel",
            }.items()
            if "VEN_" + pci in ids
        }
        if "VEN_17CB" in ids or "ADRENO" in ids:
            vendors.add("qualcomm")
        return frozenset(vendors)
    if system == "Linux":
        vendors = set()
        for path in Path("/sys/class/drm").glob("card[0-9]*/device/vendor"):
            try:
                vendors.add(
                    {"0x10de": "nvidia", "0x1002": "amd", "0x8086": "intel"}.get(
                        path.read_text().strip()
                    )
                )
            except OSError:
                continue
        if Path("/dev/dxg").exists() and Path("/usr/lib/wsl/lib/nvidia-smi").exists():
            vendors.add("nvidia")
        if Path("/dev/nvidiactl").exists():
            vendors.add("nvidia")
        return frozenset(vendors - {None})
    return (
        frozenset({"apple"})
        if system == "Darwin" and platform.machine() == "arm64"
        else frozenset()
    )


def detect_in_background():
    threading.Thread(target=gpu_vendors, daemon=True, name="hardware-detection").start()
