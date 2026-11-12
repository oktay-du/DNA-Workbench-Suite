"""Select, install and probe pinned upstream llama.cpp builds."""

from functools import lru_cache
import hashlib
import json
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
from tempfile import TemporaryDirectory
import zipfile

import hardware
import network_io


PACKAGES = json.loads(
    Path(__file__).with_name("ai-runtimes.json").read_text(encoding="utf-8")
)
RELEASE = (
    "https://github.com/ggml-org/llama.cpp/releases/download/"
    + PACKAGES["release"]
    + "/"
)
LOG = logging.getLogger(__name__)
PREFERENCE = {
    "nvidia": "cuda",
    "amd": "rocm",
    "intel": "sycl",
    "apple": "metal",
    "qualcomm": "opencl",
}
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def platform_key():
    machine = platform.machine().lower()
    arch = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64"}.get(machine, machine)
    return platform.system() + "-" + arch


def builds():
    return PACKAGES["platforms"].get(platform_key(), {})


def runtime_path(base, backend):
    if platform_key() == "Darwin-arm64" and backend == "metal":
        # The official Metal archive also supports CPU execution.
        backend = "cpu"
    return base / "runtimes" / PACKAGES["release"] / platform_key() / backend


def candidates(vendors, available):
    preferred = [
        backend
        for vendor, backend in PREFERENCE.items()
        if vendor in vendors and backend in available
    ]
    if vendors and "vulkan" in available:
        index = (
            preferred.index("sycl")
            if vendors & {"nvidia", "amd"} and "sycl" in preferred
            else len(preferred)
        )
        preferred.insert(index, "vulkan")
    return preferred


def executable(base, backend):
    if (
        backend == "cpu"
        and platform.system() == "Windows"
        and builds().get("cpu") is None
    ):
        path = base / "runtime" / "llama-server.exe"
        return path if path.is_file() else None
    folder = runtime_path(base, backend)
    name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
    return next((path for path in sorted(folder.rglob(name)) if path.is_file()), None)


def install(base, backend):
    existing = executable(base, backend)
    if existing is not None:
        return existing
    assets = builds()[backend]
    target = runtime_path(base, backend)
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=backend + "-", dir=target.parent) as temp:
        stage = Path(temp)
        output = stage / "runtime"
        output.mkdir()
        for name, size, digest in assets:
            archive = stage / name
            with (
                network_io.open_https(RELEASE + name, timeout=120) as response,
                archive.open("wb") as dest,
            ):
                remaining = size
                while chunk := response.read(min(1024 * 1024, remaining + 1)):
                    remaining -= len(chunk)
                    if remaining < 0:
                        raise ValueError("Unexpected runtime archive size")
                    dest.write(chunk)
            with archive.open("rb") as stream:
                if (
                    remaining
                    or hashlib.file_digest(stream, "sha256").hexdigest() != digest
                ):
                    raise ValueError("Runtime archive checksum mismatch")
            if name.endswith(".zip"):
                from visual_tools import safe_member

                with zipfile.ZipFile(archive) as package:
                    for entry in package.infolist():
                        path = output / safe_member(entry.filename)
                        if not entry.is_dir():
                            path.parent.mkdir(parents=True, exist_ok=True)
                            with package.open(entry) as source, path.open("wb") as dest:
                                shutil.copyfileobj(source, dest)
            else:
                with tarfile.open(archive, "r:gz") as package:
                    package.extractall(output, filter="data")
            archive.unlink()
        name = "llama-server.exe" if platform.system() == "Windows" else "llama-server"
        if not any(path.is_file() for path in output.rglob(name)):
            raise ValueError("Local inference server missing from runtime package")
        try:
            output.rename(target)
        except OSError:
            if executable(base, backend) is None:
                raise
    return executable(base, backend)


def environment(binary):
    env = os.environ.copy()
    if platform.system() == "Linux":
        library_dirs = [
            str(binary.parent),
            str(binary.parent.parent / "lib"),
            str(binary.parent / "lib"),
        ]
        if Path("/usr/lib/wsl/lib").is_dir():
            library_dirs.append("/usr/lib/wsl/lib")
        if env.get("LD_LIBRARY_PATH"):
            library_dirs.append(env["LD_LIBRARY_PATH"])
        env["LD_LIBRARY_PATH"] = os.pathsep.join(library_dirs)
    return env


def select_device(output, backend):
    # Read only the list printed by --list-devices. Initialization logs can also contain GPU names.
    _, header, devices = output.partition("Available devices:")
    if not header:
        return None
    prefix = {
        "cuda": "CUDA",
        "rocm": "ROCm|HIP",
        "vulkan": "Vulkan",
        "sycl": "SYCL",
        "metal": "MTL|Metal",
        "opencl": "GPUOpenCL|OpenCL",
    }[backend]
    choices = []
    for line in devices.splitlines():
        match = re.match(rf"^\s*((?:{prefix})[0-9]*):\s*(.+)", line, re.IGNORECASE)
        if not match or re.search(
            r"llvmpipe|lavapipe|swiftshader|basic render|software|\bCPU\b",
            match[2],
            re.IGNORECASE,
        ):
            continue
        free = re.search(r"(\d+)\s*(?:MiB|MB) free", match[2], re.IGNORECASE)
        total = re.search(r"(\d+)\s*(?:MiB|MB)", match[2], re.IGNORECASE)
        memory = int((free or total)[1]) if free or total else None
        if memory is None or memory >= 896:
            # Integrated GPUs can report shared RAM as VRAM. Prefer a discrete Vulkan card.
            discrete = backend == "vulkan" and bool(
                re.search(
                    r"NVIDIA|Radeon\s+(RX|PRO)|Arc\s+[AB]\d", match[2], re.IGNORECASE
                )
            )
            choices.append((discrete, memory or 0, match[1]))
    return max(choices)[2] if choices else None


def device(binary, backend):
    try:
        result = subprocess.run(
            [str(binary), "--list-devices"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            cwd=binary.parent,
            env=environment(binary),
            creationflags=HIDDEN,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return select_device(result.stdout, backend) if result.returncode == 0 else None


@lru_cache(maxsize=8)
def prepare(base):
    for backend in candidates(hardware.gpu_vendors(), builds()):
        try:
            binary = install(base, backend)
            if binary is not None and device(binary, backend):
                return backend
        except (
            OSError,
            ValueError,
            RuntimeError,
            tarfile.TarError,
            zipfile.BadZipFile,
        ) as error:
            LOG.info(
                "Optional local inference runtime unavailable (%s): %s", backend, error
            )
    return None
