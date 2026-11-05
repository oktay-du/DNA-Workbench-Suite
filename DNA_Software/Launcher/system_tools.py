"""Resolve Windows host tools from the OS directory rather than the working folder."""

from pathlib import Path
import os

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
