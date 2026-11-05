"""Public software/data provenance, distinct from private DNA and runtime guarantees."""

from pathlib import Path
import importlib.metadata, json, sys

ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).parent


def load(name):
    return json.loads((APP / name).read_text(encoding="utf-8-sig"))


def local(relative):
    p = (ROOT / relative).resolve()
    if not p.is_relative_to(ROOT.resolve()):
        raise ValueError("Catalog path outside app root")
    return p


def snapshot():
    lock = load("install-lock.json")
    rows = []
    audits = {x["url"].rstrip("/"): x for x in load("project-audit.json")["projects"]}
    for item in lock["items"]:
        p = local(item["relative_path"])
        target = local(item["target"]) if item.get("target") else None
        audit = audits.get(item.get("source", "").rstrip("/"), {})
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "group": item["group"],
                "version": item.get("version") or item.get("commit") or "Unknown",
                "source": item.get("source", ""),
                "download_url": item.get("url", ""),
                "relative_path": item["relative_path"],
                "bytes": item.get("expected_bytes")
                or (p.stat().st_size if p.is_file() else None),
                "size_basis": "publisher manifest"
                if item.get("expected_bytes")
                else "local archive metadata"
                if p.is_file()
                else "unknown",
                "sha256": item.get("expected_sha256"),
                "md5": item.get("expected_md5"),
                "license": item.get("license")
                or audit.get("license")
                or item.get("license_notice")
                or "See upstream project",
                "license_url": audit.get("license_url") or item.get("source", ""),
                "cached": p.is_file(),
                "target_present": bool(target and target.exists()),
                "runtime_verified": False,
                "date_basis": "Pinned snapshot label; retrieval date is not necessarily upstream publication date",
                "required_by": "Optional workflow prerequisites; no bulk automatic download",
            }
        )
    for id, item in load("visual-packages.json").items():
        folder = ROOT / "DNA_Software/Windows/VisualTools" / id
        rows.append(
            {
                "id": "visual-" + id,
                "name": item.get("package", id),
                "group": "visualization",
                "version": item["version"],
                "source": next(
                    (x["url"] for x in audits.values() if x.get("id") == id),
                    item.get("source", ""),
                ),
                "download_url": item.get("url", ""),
                "license": next(
                    (
                        x.get("license", "See upstream")
                        for x in audits.values()
                        if x.get("id") == id
                    ),
                    "See upstream",
                ),
                "relative_path": "DNA_Software/Windows/VisualTools/" + id,
                "cached": folder.exists(),
                "target_present": (folder / item["entry"]).is_file(),
                "runtime_verified": False,
                "bytes": None,
                "sha256": item.get("sha256"),
                "integrity": item.get("integrity"),
                "size_basis": "unknown",
            }
        )
    documents = load("document-packages.json")
    for name, item in documents["runtime"].items():
        rows.append(
            {
                "id": "document-" + name,
                "name": name,
                "group": "document translation runtime",
                "version": item["version"],
                "source": item.get("source", "https://pypi.org/project/" + name + "/"),
                "download_url": item["url"],
                "relative_path": "DNA_Software/Windows/PythonPackages",
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "license": item.get("license", "See upstream"),
                "target_present": False,
                "runtime_verified": False,
                "size_basis": "pinned PyPI wheel",
            }
        )
    for item in documents["models"]:
        folder = (
            ROOT
            / "DNA_Software/Models/DocumentTranslation"
            / item["filename"].removesuffix(".argosmodel")
        )
        rows.append(
            {
                "id": "translation-" + item["from"] + "-" + item["to"],
                "name": "Argos " + item["from"] + " to " + item["to"],
                "enabled": item.get("enabled", True),
                "quality_note": item.get("quality_note", ""),
                "group": "offline translation model"
                + (" (disabled)" if item.get("enabled") is False else ""),
                "version": item["version"],
                "source": item["source"],
                "download_url": item["url"],
                "relative_path": str(folder.relative_to(ROOT)),
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "license": item["license"],
                "target_present": (folder / "verified-package.json").is_file(),
                "runtime_verified": False,
                "size_basis": item["hash_basis"],
            }
        )
    for kind, item in load("ai-packages.json").items():
        target = (
            ROOT
            / "DNA_Software/Windows/LocalAI"
            / (
                "models/" + item["filename"]
                if kind == "model"
                else "runtime/llama-server.exe"
            )
        )
        rows.append(
            {
                "id": "ai-" + kind,
                "name": item.get("name", "llama.cpp CPU runtime"),
                "group": "optional-ai",
                "version": item.get("version") or item.get("commit"),
                "source": item["source"],
                "download_url": item["url"],
                "license": item["license"],
                "bytes": item.get("bytes"),
                "sha256": item["sha256"],
                "cached": target.is_file(),
                "target_present": target.is_file(),
                "runtime_verified": False,
                "size_basis": "publisher manifest" if item.get("bytes") else "unknown",
                "relative_path": str(target.relative_to(ROOT)).replace("\\", "/"),
            }
        )
    packages = []
    package_root = ROOT / "DNA_Software/Windows/PythonPackages"
    for dist in importlib.metadata.distributions(path=[str(package_root)]):
        meta = dist.metadata
        name = meta.get("Name", dist.name)
        license = (
            meta.get("License-Expression")
            or meta.get("License")
            or "See distribution license"
        )
        if len(license) > 120 or "\n" in license:
            license = "See distribution license"
        packages.append(
            {
                "name": name,
                "version": dist.version,
                "license": license,
                "source": "https://pypi.org/project/" + name + "/",
                "evidence": "installed distribution metadata, not an execution test",
            }
        )
    return {
        "app_version": lock["app_version"],
        "author": "OD",
        "snapshot_date": "2026-11-04",
        "runtime_python": sys.version.split()[0],
        "catalog_count": len(rows),
        "items": rows,
        "python_distributions": sorted(packages, key=lambda x: x["name"].lower()),
        "projects": list(audits.values()),
        "notice": "Pins, archive presence, package metadata and successful execution are different evidence. No private DNA or local account paths are exported. Reference and model licenses remain separate.",
    }


def markdown():
    s = snapshot()
    lines = [
        "# Software, reference data and model versions",
        "",
        s["notice"],
        "",
        "Catalog snapshot: " + s["snapshot_date"] + " · app " + s["app_version"],
        "",
        "Large files are optional and downloaded separately. Retrieval labels are not source publication dates. Unknown sizes/checksums are intentionally left unknown.",
        "",
        "| Component | Pin / data snapshot | Category | Download size | License / source |",
        "|---|---|---|---|---|",
    ]
    for r in s["items"]:
        size = f"{r['bytes'] / 1024**3:.2f} GiB" if r.get("bytes") else "Unknown"
        name = r["name"].replace("|", "/")
        lines.append(
            f"| [{name}]({r.get('source') or r.get('download_url') or '#'}) | {r['version']} | {r['group']} | {size} | [{str(r.get('license', 'See upstream')).replace('|', '/')}]({r.get('license_url') or r.get('source') or r.get('download_url') or '#'}) |"
        )
    lines += [
        "",
        "## Python distribution inventory",
        "",
        "Versions below were read from this installation’s distribution metadata. They are an environment snapshot, not a required bundled installation or proof that every package was exercised.",
        "",
        "| Package | Version | Declared license |",
        "|---|---|---|",
    ]
    for r in s["python_distributions"]:
        lines.append(
            f"| [{r['name']}]({r['source']}) | {r['version']} | {r['license'].replace('|', '/')} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    folder = APP / "Public/docs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "VERSIONS.md").write_text(markdown(), encoding="utf-8")
    (folder / "software-data-catalog.json").write_text(
        json.dumps(snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Public version/data catalog generated")
