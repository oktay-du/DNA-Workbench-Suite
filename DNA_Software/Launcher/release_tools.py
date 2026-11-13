"""Public release staging from an explicit allowlist. No personal workspace exports."""

from pathlib import Path
import hashlib, json, os, platform, plistlib, subprocess, sys, zipfile, urllib.parse

ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).parent


def info():
    value = json.loads((APP / "project_info.json").read_text(encoding="utf-8"))
    for url in value.get("support_links", {}).values():
        parsed = urllib.parse.urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Support links must be public HTTPS URLs")
    return value


def verify():
    path = APP / "release-integrity.json"
    if not path.exists():
        return {
            "available": False,
            "status": "No release integrity manifest installed",
            "authenticated": False,
        }
    manifest = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for row in manifest["files"]:
        p = (ROOT / row["path"]).resolve()
        if not p.is_relative_to(ROOT.resolve()) or p.is_symlink():
            raise ValueError("Invalid release manifest path")
        actual = None
        if p.is_file():
            with p.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
        results.append({"path": row["path"], "matches": actual == row["sha256"]})
    return {
        "available": True,
        "version": manifest["version"],
        "matches": all(x["matches"] for x in results),
        "files": results,
        "authenticated": False,
        "notice": "Unsigned checksums detect accidental changes against this local manifest. They do not prove publisher identity or resist replacement of both file and manifest.",
    }


LINUX_LAUNCHER = """#!/bin/sh
set -eu
cd "$(dirname "$(readlink -f "$0")")"
exec python3 DNA_Software/Launcher/dna_cli.py desktop
"""


MAC_LAUNCHER = """#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
PYTHON=$(command -v python3.12 || command -v python3 || true)
if [ -z "$PYTHON" ] || ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 12))'; then
    /usr/bin/osascript -e 'display alert "DNA Workbench needs Python 3.12 or later."'
    exit 1
fi
exec "$PYTHON" DNA_Software/Launcher/dna_cli.py desktop
"""


def zip_entry(bundle, name, data, mode=0o644):
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = (0o100000 | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    bundle.writestr(info, data)


def build_desktop_zip(archive, mac_viewer=None):
    """Package native desktop entry points and the public workspace source."""
    import public_package

    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        if mac_viewer is None:
            zip_entry(bundle, "DNA-Workbench.sh", LINUX_LAUNCHER, 0o755)
            seen.add("DNA-Workbench.sh")
        else:
            prefix = "DNA-Workbench.app/Contents/"
            zip_entry(bundle, prefix + "MacOS/DNAWorkbench", MAC_LAUNCHER, 0o755)
            zip_entry(bundle, prefix + "MacOS/DNAWorkbenchWebView", mac_viewer, 0o755)
            zip_entry(
                bundle,
                prefix + "Info.plist",
                plistlib.dumps(
                    {
                        "CFBundleIdentifier": "io.github.oktay-du.DNAWorkbenchSuite",
                        "CFBundleExecutable": "DNAWorkbench",
                        "CFBundleName": "DNA Workbench",
                        "CFBundlePackageType": "APPL",
                        "CFBundleShortVersionString": json.loads(
                            (APP / "install-lock.json").read_text(encoding="utf-8")
                        )["app_version"],
                        "LSMinimumSystemVersion": "13.0",
                        "NSHighResolutionCapable": True,
                        "NSAppTransportSecurity": {
                            "NSExceptionDomains": {
                                "127.0.0.1": {
                                    "NSExceptionAllowsInsecureHTTPLoads": True
                                },
                            },
                        },
                    }
                ),
            )
        selected = list(public_package.entries()) + list(
            public_package.presentation_entries()
        )
        for name in (
            "README.md",
            "LICENSE",
            "THIRD_PARTY.md",
            "SECURITY.md",
            "RELEASING.md",
        ):
            selected.append((APP / "Public" / name, name))
        for source, target in selected:
            if target in seen or not source.is_file():
                continue
            seen.add(target)
            if target == "DNA_Software/Launcher/release-integrity.json":
                zip_entry(
                    bundle,
                    target,
                    public_package.integrity_manifest(public_package.entries()),
                )
            else:
                bundle.write(source, target)
    return archive


def build_linux_zip(archive):
    return build_desktop_zip(archive)


def desktop_arch(machine):
    try:
        return {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}[
            machine.lower()
        ]
    except KeyError:
        raise ValueError(f"Unsupported desktop architecture: {machine}") from None


def stage_desktop(target, arch):
    version = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))[
        "app_version"
    ]
    dest = ROOT / "DNAWorkbench_Release" / version
    if target == "macos":
        if sys.platform != "darwin":
            raise ValueError(
                "Building the macOS application requires macOS and Xcode tools."
            )
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="dna-macos-build-") as folder:
            binary = Path(folder) / "DNAWorkbenchWebView"
            swift_arch = "x86_64" if arch == "x64" else "arm64"
            subprocess.run(
                [
                    "/usr/bin/xcrun",
                    "swiftc",
                    "-O",
                    "-target",
                    swift_arch + "-apple-macos13.0",
                    str(APP / "MacWebView.swift"),
                    "-o",
                    str(binary),
                ],
                check=True,
            )
            archive = build_desktop_zip(
                dest / f"DNAWorkbench-macOS-{arch}.zip", binary.read_bytes()
            )
    else:
        archive = build_linux_zip(dest / f"DNAWorkbench-Linux-{arch}.zip")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    files = [{"path": archive.name, "sha256": digest, "bytes": archive.stat().st_size}]
    (dest / "release.json").write_text(
        json.dumps(
            {
                "version": version,
                "author": "OD",
                "target": target,
                "architecture": arch,
                "files": files,
                "signed": False,
                "publication_status": "Prepared locally; not uploaded to GitHub",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (dest / "SHA256SUMS.txt").write_text(
        digest + "  " + archive.name + "\n", encoding="ascii"
    )
    return str(dest)


def prepare(arch="x64"):
    import public_package, command_bus

    version = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))[
        "app_version"
    ]
    dest = ROOT / "DNAWorkbench_Release" / version
    if arch == "arm64":
        dest = dest / "windows-arm64"
    dest.mkdir(parents=True, exist_ok=True)
    launcher = "DNA_Launcher_ARM64.exe" if arch == "arm64" else "DNA_Launcher.exe"
    selected = [
        (ROOT / launcher, "DNA_Launcher.exe"),
        (ROOT / "DNAWorkbench_Source.zip", "DNAWorkbench_Source.zip"),
    ]
    if arch == "arm64":
        config = ROOT / (launcher + ".config")
        if config.is_file():
            selected.append((config, "DNA_Launcher.exe.config"))
    selected += [
        (APP / "Public" / name, name)
        for name in [
            "README.md",
            "LICENSE",
            "THIRD_PARTY.md",
            "SECURITY.md",
            "RELEASING.md",
        ]
    ]
    selected += list(public_package.presentation_entries())
    selected += [
        (src, target)
        for src, target in public_package.entries()
        if target.startswith("Samples/")
    ]
    files = []
    for src, name in selected:
        if not src.is_file():
            raise ValueError("Build/public source package missing: " + name)
        data = src.read_bytes()
        (dest / name).parent.mkdir(parents=True, exist_ok=True)
        (dest / name).write_bytes(data)
        files.append(
            {
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    # All command schemas, including new workflows, are generated from the live registry.
    commands = command_bus.manifest()
    commands["app"].pop("root", None)
    (dest / "commands.json").write_text(
        json.dumps(commands, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files.append(
        {
            "path": "commands.json",
            "sha256": hashlib.sha256((dest / "commands.json").read_bytes()).hexdigest(),
            "bytes": (dest / "commands.json").stat().st_size,
        }
    )
    (dest / "release.json").write_text(
        json.dumps(
            {
                "version": version,
                "author": "OD",
                "files": files,
                "signed": False,
                "publication_status": "Prepared locally; not uploaded to GitHub",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (dest / "SHA256SUMS.txt").write_text(
        "\n".join(x["sha256"] + "  " + x["path"] for x in files) + "\n",
        encoding="ascii",
    )
    archive = dest / f"DNAWorkbench-Windows-{arch}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for row in files:
            if row["path"] != "DNAWorkbench_Source.zip":
                z.write(dest / row["path"], row["path"])
    with archive.open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    files.append(
        {"path": archive.name, "sha256": archive_hash, "bytes": archive.stat().st_size}
    )
    (dest / "release.json").write_text(
        json.dumps(
            {
                "version": version,
                "author": "OD",
                "files": files,
                "signed": False,
                "publication_status": "Prepared locally; not uploaded to GitHub",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (dest / "SHA256SUMS.txt").write_text(
        "\n".join(x["sha256"] + "  " + x["path"] for x in files) + "\n",
        encoding="ascii",
    )
    return str(dest)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Stage the native release zip")
    parser.add_argument(
        "--target",
        choices=("auto", "windows", "linux", "macos"),
        default="auto",
        help="auto builds the package for this operating system",
    )
    parser.add_argument(
        "--arch", choices=("x64", "arm64"), help="Target desktop architecture"
    )
    args = parser.parse_args(argv)
    target = args.target
    if target == "auto":
        target = (
            "windows"
            if os.name == "nt"
            else "macos"
            if sys.platform == "darwin"
            else "linux"
        )
    if target == "windows":
        print(prepare(args.arch or "x64"))
    else:
        print(stage_desktop(target, args.arch or desktop_arch(platform.machine())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
