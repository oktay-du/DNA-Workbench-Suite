"""Public release staging from an explicit allowlist. No personal workspace exports."""

from pathlib import Path
import hashlib, json, zipfile, urllib.parse

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


def prepare():
    import public_package, command_bus

    version = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))[
        "app_version"
    ]
    dest = ROOT / "DNAWorkbench_Release" / version
    dest.mkdir(parents=True, exist_ok=True)
    selected = [
        (ROOT / "DNA_Launcher.exe", "DNA_Launcher.exe"),
        (ROOT / "DNAWorkbench_Source.zip", "DNAWorkbench_Source.zip"),
    ]
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
    with zipfile.ZipFile(
        dest / "DNAWorkbench-Windows-x64.zip", "w", zipfile.ZIP_DEFLATED
    ) as z:
        for row in files:
            if row["path"] != "DNAWorkbench_Source.zip":
                z.write(dest / row["path"], row["path"])
    archive = dest / "DNAWorkbench-Windows-x64.zip"
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


if __name__ == "__main__":
    print(prepare())
