# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Required Notice: Copyright 2026 Oktay Du / OD — DNA Workbench
"""Guided, rights-reviewed asset staging. Never executes imported files."""

from pathlib import Path
import datetime, hashlib, json, os, shutil, uuid
import security_paths

APP = Path(__file__).resolve().parent
ROOT = APP.parents[1]


def catalog():
    lock = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))
    audits = json.loads((APP / "project-audit.json").read_text(encoding="utf-8"))[
        "projects"
    ]
    import on_demand

    declarations = {
        r["asset_id"]: r
        for r in json.loads(
            (APP / "third-party-inventory.json").read_text(encoding="utf-8")
        )["items"]
        if r.get("asset_id")
    }
    result = []
    for item in lock["items"]:
        project = next((a for a in audits if a.get("url") == item.get("source")), {})
        license = (
            item.get("license")
            or project.get("license")
            or item.get("license_notice")
            or "Unknown; review upstream terms"
        )
        declaration = declarations.get(item["id"], {})
        license = declaration.get("license") or license
        source = item.get("source", "").lower()
        if "python-build-standalone" in source:
            license = "PSF-2.0 and included runtime dependency licenses"
        elif "webview2" in item["id"].lower():
            license = "Microsoft WebView2 terms and included third-party notices"
        elif item["id"] == "ubuntu-wsl":
            license = "Individual Ubuntu package licenses; retain installed copyright/source notices"
        restricted = bool(item.get("license_notice")) or any(
            s in license.lower()
            for s in (
                "academic",
                "noncommercial",
                "non-commercial",
                "noassertion",
                "unknown",
                "stanford",
            )
        )
        tool = next((k for k, v in on_demand.TOOLS.items() if v[1] == item["id"]), "")
        result.append(
            {
                "id": item["id"],
                "name": item["name"],
                "group": item["group"],
                "source": item.get("source") or item["url"],
                "license": license,
                "license_url": declaration.get("license_url")
                or project.get("license_url")
                or item.get("source")
                or item["url"],
                "restricted": restricted,
                "notice": item.get(
                    "license_notice",
                    "Review the upstream terms. Import/storage does not grant permission to use or redistribute an asset.",
                ),
                "cache_relative": item["relative_path"],
                "target": item.get("target")
                or "See the tool installer; staging alone is not installation",
                "expected_sha256": item.get("expected_sha256"),
                "tool": tool,
                "automatic_available": bool(
                    tool
                    and "unknown" not in license.lower()
                    and "noassertion" not in license.lower()
                    and on_demand.TOOLS[tool][2] not in ("manual", "windows-manual")
                ),
            }
        )
    return {
        "items": result,
        "notice": "Separate tools and datasets keep their own licenses. A checkbox or manual import does not override them.",
    }


def plan(asset):
    row = next((r for r in catalog()["items"] if r["id"] == asset), None)
    if row is None:
        raise ValueError("Choose a known asset")
    row = dict(row)
    staging = security_paths.contained(
        ROOT / "DNA_Software/ManualAssets", security_paths.identifier(asset)
    )
    cache = security_paths.contained(ROOT, row["cache_relative"])
    row.update(
        staging_folder=str(staging),
        cache_path=str(cache),
        import_is_installation=False,
        exact_filename=cache.name,
    )
    if "rfmix" in asset.lower():
        row["license_text"] = (APP / "Notices/RFMIX-LICENSE.txt").read_text(
            encoding="utf-8"
        )
    return row


def stage(args):
    if args.get("rights_reviewed") is not True:
        raise ValueError(
            "Review upstream terms and confirm your necessary rights first"
        )
    row = plan(args["asset"])
    src = security_paths.input_file(args["file"])
    if args["mode"] not in ("copy", "move"):
        raise ValueError("Choose Copy or Move")
    before = src.stat()
    with src.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if row["expected_sha256"] and digest != row["expected_sha256"]:
        raise ValueError("Checksum differs from the pinned asset; source unchanged")
    if row["expected_sha256"]:
        dest = Path(row["cache_path"])
    else:
        dest = security_paths.contained(
            Path(row["staging_folder"]), digest[:16] + "-" + src.name
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        with dest.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError(
                    "Destination contains different bytes; nothing overwritten"
                )
    elif src != dest:
        temp = dest.with_name(dest.name + "." + uuid.uuid4().hex + ".importing")
        try:
            shutil.copyfile(src, temp)
            with temp.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    raise ValueError("Copied asset failed checksum validation")
            after = src.stat()
            if (before.st_size, before.st_mtime_ns) != (
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError("Source changed; no import completed")
            if os.name == "nt":
                temp.rename(dest)
            else:
                os.link(temp, dest)
                temp.unlink()
        finally:
            temp.unlink(missing_ok=True)
    if args["mode"] == "move" and src != dest:
        after = src.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(
                "Source changed; validated destination retained and source not removed"
            )
        src.unlink()
    receipt = {
        "asset": row["id"],
        "sha256": digest,
        "bytes": dest.stat().st_size,
        "path": str(dest),
        "created": datetime.datetime.now().astimezone().isoformat(),
        "rights_reviewed": True,
        "license": row["license"],
        "installed": False,
        "executed": False,
        "status": "Verified bytes cached"
        if row["expected_sha256"]
        else "Stored for manual review; no trusted publisher hash",
    }
    receipts = security_paths.contained(
        ROOT / "DNA_Software/UserData/Launcher/AssetReceipts",
        security_paths.identifier(row["id"]) + ".json",
    )
    receipts.parent.mkdir(parents=True, exist_ok=True)
    receipts.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt
