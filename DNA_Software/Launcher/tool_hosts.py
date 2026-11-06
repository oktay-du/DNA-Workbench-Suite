"""Which pinned download runs on Windows, on Linux, or on both.

Prefer the same project when it publishes both builds. A host then uses its own
file. When a project publishes only one operating system, the other host gets
the named alternative. Wine is not used.
"""

import json
import os
from pathlib import Path

LOCK = Path(__file__).with_name("install-lock.json")

# tool name -> (windows pin, linux pin). None means that host has no file.
PAIRS = {
    "plink2": ("plink2-windows", "plink2-linux"),
    "haplogrep": (
        "haplogrep3-3-3-2-windows-tar-gz",
        "haplogrep3-3-3-2-linux-tar-gz",
    ),
    "gramps": ("grampsaio-6-0-8-1-win64-exe", "gramps-6-0-8-1-amd64-snap"),
    "jbrowse": (
        "jbrowse-desktop-v4-3-0-win-exe",
        "jbrowse-desktop-v4-3-0-linux-appimage",
    ),
    "ugene": ("ugene-53-1-windows", "ugene-53-1-linux"),
    "java-windows": ("java21-windows", "java21-linux"),
    "samtools": ("samtools-1-23-1-windows", "samtools-1-25-tar-bz2"),
    "bcftools": ("bcftools-1-23-1-windows", "bcftools-1-25-tar-bz2"),
    "mosdepth": (None, "mosdepth"),
}

NOTES = {
    "python-windows": (
        "native",
        "host Python 3.12",
        "Windows CPython archive. Linux uses the system Python because the desktop needs GTK bindings.",
    ),
    "webview2-runtime": (
        "native",
        "WebKitGTK",
        "Windows WebView2 runtime. Linux uses WebKitGTK 4.1.",
    ),
    "grampsaio-6-0-8-1-win64-exe": (
        "native",
        "same release, other file",
        "Windows installer. Linux uses the official gramps_6.0.8 amd64 snap from this release.",
    ),
    "gramps-6-0-8-1-amd64-snap": (
        "same release, other file",
        "native",
        "Official Linux snap of Gramps 6.0.8. Windows uses the AIO installer. The snap needs snapd.",
    ),
    "jbrowse-desktop-v4-3-0-win-exe": (
        "native",
        "same release, other file",
        "Windows installer. Linux uses the official JBrowse 4.3.0 desktop AppImage.",
    ),
    "jbrowse-desktop-v4-3-0-linux-appimage": (
        "same release, other file",
        "native",
        "Official Linux AppImage of JBrowse desktop 4.3.0. Windows uses the exe installer.",
    ),
    "jbrowse-web-v4-3-0-zip": (
        "browser",
        "browser",
        "Web bundle for both hosts. The desktop app has a separate file per host.",
    ),
    "haplogrep3-3-3-2-windows-tar-gz": (
        "native",
        "same release, other file",
        "Windows Haplogrep 3.3.2. Linux uses the Linux tar from the same release.",
    ),
    "haplogrep3-3-3-2-linux-tar-gz": (
        "same release, other file",
        "native",
        "Linux Haplogrep 3.3.2. Windows uses the Windows tar from the same release.",
    ),
    "plink2-windows": (
        "native",
        "same release, other file",
        "Windows PLINK 2. Linux uses the Linux zip from the same build.",
    ),
    "plink2-linux": (
        "same release, other file",
        "native",
        "Linux PLINK 2. Windows uses the Windows zip from the same build.",
    ),
    "openjdk21u-jre-x64-windows-hotspot-21-0-13-9-zip": (
        "native",
        "same release, other file",
        "Windows Temurin 21 JRE. Linux uses java21-linux from the same Adoptium release.",
    ),
    "java21-windows": (
        "native",
        "same release, other file",
        "Windows Temurin 21 JRE. Linux uses java21-linux from the same Adoptium release.",
    ),
    "java21-linux": (
        "same release, other file",
        "native",
        "Linux Temurin 21 JRE. The SHA-256 is the publisher file from this release. Windows uses the zip.",
    ),
    "ugene-53-1-windows": (
        "native",
        "same release, other file",
        "Windows UGENE 53.1. Linux uses the official Linux tar from this release.",
    ),
    "ugene-53-1-linux": (
        "same release, other file",
        "native",
        "Official Linux UGENE 53.1. Windows uses the Windows zip from this release.",
    ),
    "samtools-1-25-tar-bz2": (
        "Windows bundle is 1.23.1",
        "native source",
        "Official samtools 1.25 source. Linux builds it. Windows uses the Win-NGS 1.23.1 bundle because samtools publishes no Windows binary.",
    ),
    "samtools-samtools": (
        "Windows bundle is 1.23.1",
        "native source",
        "Source checkout of samtools 1.25. Same host split as the release tarball.",
    ),
    "samtools-1-23-1-windows": (
        "native alternative",
        "official 1.25 source",
        "Unofficial Win-NGS bundle of samtools 1.23.1 for Windows. Not an htslib release. Linux keeps the official 1.25 source.",
    ),
    "bcftools-1-25-tar-bz2": (
        "Windows bundle is 1.23.1",
        "native source",
        "Official bcftools 1.25 source. Linux builds it. Windows uses the Win-NGS 1.23.1 bundle because bcftools publishes no Windows binary.",
    ),
    "samtools-bcftools": (
        "Windows bundle is 1.23.1",
        "native source",
        "Source checkout of bcftools 1.25. Same host split as the release tarball.",
    ),
    "bcftools-1-23-1-windows": (
        "native alternative",
        "official 1.25 source",
        "Unofficial Win-NGS bundle of bcftools 1.23.1 for Windows. Not an htslib release. Linux keeps the official 1.25 source.",
    ),
    "mosdepth": (
        "samtools depth",
        "native",
        "Linux static binary. mosdepth publishes no Windows build. Windows coverage uses samtools depth from the Windows samtools bundle.",
    ),
    "brentp-mosdepth": (
        "samtools depth",
        "native source",
        "mosdepth source. The runnable file is the Linux binary. Windows uses samtools depth.",
    ),
    "ubuntu-wsl": (
        "WSL guest",
        "not used",
        "Windows can run a Linux-only program inside this Ubuntu image. A Linux desktop does not install WSL.",
    ),
    "pharmcat-3-4-0-all-jar": (
        "Java on the host",
        "Java on the host",
        "One jar for both hosts. Windows uses the Temurin Windows JRE. Linux uses the Temurin Linux JRE.",
    ),
    "beagle-5-5": (
        "Java on the host",
        "Java on the host",
        "One jar for both hosts, with the Temurin JRE for that host.",
    ),
    "gatk-4-7-0-0": (
        "Java on the host",
        "Java on the host",
        "One zip for both hosts, with the Temurin JRE for that host.",
    ),
    "igv-2-19-8": (
        "Java on the host",
        "Java on the host",
        "One Java desktop zip for both hosts, with the Temurin JRE for that host.",
    ),
    "nextflow-dist": (
        "Java on the host",
        "Java on the host",
        "One Nextflow distribution for both hosts, with the Temurin JRE for that host.",
    ),
}

LINUX_SOURCE_NOTE = (
    "WSL or the Windows alternative when one is pinned",
    "native",
    "Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL.",
)


def prefer(tool, fallback=None):
    """Pin id for this operating system. None when this host has no file."""
    pair = PAIRS.get(tool)
    if pair is None:
        return fallback
    windows, linux = pair
    return windows if os.name == "nt" else linux


def classify(item):
    ident = item["id"]
    group = item.get("group")
    if group == "references" or ident.startswith("pharmcat-positions-"):
        return {
            "id": ident,
            "windows": "data",
            "linux": "data",
            "note": "Reference or annotation data, not a program.",
        }
    if ident in NOTES:
        windows, linux, note = NOTES[ident]
        return {"id": ident, "windows": windows, "linux": linux, "note": note}
    if (
        ident
        in {
            "pharmcat-pipeline-3-4-0-tar-gz",
        }
        or group == "sources"
    ):
        windows, linux, note = LINUX_SOURCE_NOTE
        return {"id": ident, "windows": windows, "linux": linux, "note": note}
    raise KeyError("No host classification for " + ident)


def rows():
    items = json.loads(LOCK.read_text(encoding="utf-8"))["items"]
    return [classify(item) for item in items]


def program_rows():
    return [row for row in rows() if row["windows"] != "data"]


def markdown_table():
    lines = [
        "| Pinned id | Windows | Linux | What that means |",
        "|---|---|---|---|",
    ]
    for row in program_rows():
        lines.append("| `{id}` | {windows} | {linux} | {note} |".format(**row))
    return "\n".join(lines) + "\n"
