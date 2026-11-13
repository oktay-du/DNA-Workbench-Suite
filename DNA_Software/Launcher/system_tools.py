"""Resolve Windows host tools from the OS directory rather than the working folder."""

from pathlib import Path
import os
import platform
import shutil
import sys

HOST_TOOLS = {
    "wsl.exe": "System32/wsl.exe",
    "powershell.exe": "System32/WindowsPowerShell/v1.0/powershell.exe",
    "cmd.exe": "System32/cmd.exe",
    "notepad.exe": "System32/notepad.exe",
    "expand.exe": "System32/expand.exe",
}


def windows_executable(name):
    if name not in HOST_TOOLS:
        raise ValueError("Unknown Windows host tool")
    if os.name != "nt":
        raise OSError("This action requires Windows")
    import ctypes

    directory = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetWindowsDirectoryW(directory, len(directory))
    if not 0 < length < len(directory):
        raise OSError("Cannot locate the Windows directory")
    result = Path(directory.value) / HOST_TOOLS[name]
    if not result.is_file():
        raise OSError("Windows host tool is not installed: " + name)
    return str(result)


DESKTOP_APPS = {
    "gramps": (("gramps",), ("Gramps",)),
    "igv": (("igv",), ("IGV",)),
    "jbrowse": (
        ("jbrowse-desktop", "jbrowse-desktop.AppImage"),
        ("JBrowse 2", "JBrowse Desktop"),
    ),
    "ugene": (("ugene", "ugeneui"), ("UGENE",)),
}


def desktop_tool_command(root, tool, filename=None):
    """Resolve a supported native desktop program and its argument vector."""
    linux_names, mac_names = DESKTOP_APPS[tool]
    arguments = [str(Path(filename).resolve())] if filename else []
    if sys.platform == "darwin":
        for folder in (Path("/Applications"), Path.home() / "Applications"):
            for name in mac_names:
                bundle = folder / (name + ".app")
                if (bundle / "Contents/Info.plist").is_file():
                    return ["/usr/bin/open", "-a", str(bundle), *arguments]
        return None
    if not sys.platform.startswith("linux"):
        return None
    if platform.machine().lower() in {"x86_64", "amd64"}:
        folder = root / "DNA_Software/Linux/bin"
        for name in linux_names:
            binary = folder / name
            if binary.is_file() and os.access(binary, os.X_OK):
                return [str(binary), *arguments]
    for name in linux_names:
        binary = shutil.which(name)
        if binary:
            return [str(Path(binary).resolve()), *arguments]
    return None
