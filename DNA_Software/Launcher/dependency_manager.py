from system_tools import windows_executable
import network_io
import hardware

"""Public metadata and immutable update staging. No personal DNA is transmitted."""
from portable_paths import distro_name
from pathlib import Path
import datetime, gzip, hashlib, os, re, subprocess, sys, urllib.request
import portable_json as json

ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).parent
STATE = ROOT / "DNA_software/user data/launcher/dependencies"
STATE.mkdir(parents=True, exist_ok=True)
LOCK = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))
NOW = lambda: datetime.datetime.now().astimezone().isoformat()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def get(url, method="GET"):
    if not url.startswith("https://"):
        raise ValueError("Updater only accepts HTTPS sources.")
    return network_io.open_https(
        urllib.request.Request(
            url,
            method=method,
            headers={
                "User-Agent": "DNAWorkbench/0.3-local-updater",
                "Accept": "application/json",
            },
        ),
        timeout=30,
    )


def version(value):
    return tuple(int(n) for n in re.findall(r"\d+", value)[:4])


def all_items():
    repo = LOCK.get("release_repository", "").strip()
    app = {
        "id": "app",
        "name": "DNA_Launcher.exe",
        "relative_path": "DNA_Launcher.exe",
        "source": "https://github.com/" + repo if repo else "",
        "group": "core",
        "version": LOCK["app_version"],
    }
    return [app] + LOCK["items"]


def snapshot():
    tested = load(ROOT / "DNA_Software/Logs/installation-verification.json", {})
    checks = tested.get("checks", {})
    updates = load(STATE / "updates.json", {}).get("items", {})
    rows = []
    for item in all_items():
        p = ROOT / item["relative_path"]
        installed = ""
        state = "Not loaded"
        ready = False
        source = item.get("source", "")
        probe = next(
            (
                key
                for key in checks
                if key.lower() in item["id"]
                or key.lower() in source.rsplit("/", 1)[-1].lower()
            ),
            None,
        )
        if probe:
            rec = checks[probe]
            installed = rec.get("detail", "").splitlines()[0][:140]
            ready = rec.get("ready", False)
            state = "Recently successfully tested" if ready else "Test not successful"
        if item["id"] == "python-windows":
            installed = "Python " + sys.version.split()[0]
            state = "Aktiv"
            ready = True
        if item["id"] == "app":
            installed = LOCK["app_version"]
            state = "Aktive App"
            ready = True
        if item["id"] == "webview2-runtime":
            exes = list((ROOT / item["target"]).glob("**/msedgewebview2.exe"))
            installed = "156.0.4314.58" if exes else ""
            ready = bool(exes)
            state = "Portable runtime is available" if ready else "Missing"
        if p.is_file() and not ready:
            state = "Archive / data file available (not confirmed as a running tool)"
        update = updates.get(item["id"], {})
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "group": item["group"],
                "locked_version": item.get("version", item.get("commit", "Unknown")),
                "installed_version": installed
                or ("Datendatei" if p.is_file() else "Not tested"),
                "latest_version": update.get("latest", "Not checked online"),
                "status": state,
                "update_status": update.get("status", ""),
                "available": p.is_file(),
                "path": str(p),
                "license": item.get(
                    "license", item.get("license_notice", "Siehe Projektquelle")
                ),
                "source": source,
                "checked_at": tested.get("checked_at", ""),
                "optional": item["group"] not in ["core"],
            }
        )
    return {
        "app_version": LOCK["app_version"],
        "release_repository": LOCK.get("release_repository", ""),
        "app_update_status": "No public release repository configured yet"
        if not LOCK.get("release_repository")
        else "Releasequelle konfiguriert",
        "checked": NOW(),
        "items": rows,
    }


def check_updates(ids):
    selected = [i for i in all_items() if i["id"] in ids]
    previous = load(STATE / "updates.json", {}).get("items", {})
    repos = {}
    results = {}

    def one(item):
        source = item.get("source", "")
        old = previous.get(item["id"], {})
        r = {
            "id": item["id"],
            "checked": NOW(),
            "latest": item.get("version", "Unknown"),
        }
        try:
            if item["id"] == "app" and not LOCK.get("release_repository"):
                raise ValueError(
                    "No public release repository has yet been configured."
                )
            match = re.match(r"https://github.com/([^/]+/[^/]+)/*$", source)
            if match:
                repo = match[1]
                if repo not in repos:
                    with get(
                        "https://api.github.com/repos/" + repo + "/releases/latest"
                    ) as response:
                        repos[repo] = json.load(response)
                release = repos[repo]
                r.update(
                    latest=release["tag_name"],
                    release_url=release["html_url"],
                    assets=[
                        {
                            k: a.get(k)
                            for k in ["name", "size", "browser_download_url", "digest"]
                        }
                        for a in release.get("assets", [])
                    ],
                )
                r["status"] = (
                    "Newer version available"
                    if version(r["latest"]) > version(item.get("version", ""))
                    else "No newer stable release found"
                )
            elif item["group"] == "references":
                with get(item["url"], "HEAD") as response:
                    headers = response.headers
                    r.update(
                        etag=headers.get("ETag", ""),
                        last_modified=headers.get("Last-Modified", ""),
                        bytes=headers.get("Content-Length", ""),
                    )
                r["latest"] = r.get("last_modified") or item.get(
                    "version", "Data version unknown"
                )
                r["status"] = (
                    "Source metadata modified; new version load separately"
                    if old
                    and any(
                        old.get(k) != r.get(k)
                        for k in ["etag", "last_modified", "bytes"]
                    )
                    else "Source metadata collected; no automatic reassessment"
                )
            else:
                r["status"] = "Set version; check current release source manually"
            if item.get("license_notice"):
                r["status"] = item["license_notice"]
        except Exception as e:
            r["status"] = "Online verification failed:" + str(e)
        return item["id"], r

    # Sequential per repository avoids exhausting unauthenticated GitHub quotas.
    for item in selected:
        key, value = one(item)
        results[key] = value
    previous.update(results)
    write(STATE / "updates.json", {"checked": NOW(), "items": previous})
    return {"checked": len(results), "items": results}


def stage(ids):
    checked = load(STATE / "updates.json", {}).get("items", {})
    results = []
    done_clinvar = set()
    for item in [i for i in all_items() if i["id"] in ids]:
        result = {"id": item["id"], "status": "Failed"}
        try:
            if item["id"] == "app" and not LOCK.get("release_repository"):
                raise ValueError(
                    "No public release repository has yet been configured."
                )
            if item.get("license_notice"):
                raise ValueError(item["license_notice"])
            if item["url"].startswith("https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_"):
                base = item["url"].removesuffix(".tbi")
                if base not in done_clinvar:
                    results.append(stage_clinvar(item))
                    done_clinvar.add(base)
                continue
            update = checked.get(item["id"], {})
            latest = update.get("latest", "")
            asset = None
            if update.get("status") == "Newer version available":
                target_name = item["name"].replace(
                    item.get("version", "").lstrip("v"), latest.lstrip("v")
                )
                asset = next(
                    (
                        a
                        for a in update.get("assets", [])
                        if a["name"] == target_name
                        and (a.get("digest") or "").startswith("sha256:")
                    ),
                    None,
                )
                if not asset:
                    raise ValueError(
                        "Not a clearly matching release artifact with Publisher-SHA256. source and installation recipe check."
                    )
                url = asset["browser_download_url"]
                expected = asset["digest"].split(":", 1)[1]
                name = asset["name"]
                size = asset["size"]
                v = latest
            else:
                url = item["url"]
                expected = item.get("expected_sha256")
                name = Path(item["relative_path"]).name
                size = item.get("expected_bytes")
                v = item.get("version", "snapshot")
            if name in [".", ".."] or any(c in name for c in "\\/:"):
                raise ValueError("Inadmissible artifact name.")
            dest = (
                ROOT
                / "DNA_Software/Updates"
                / item["id"]
                / (
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    + "_"
                    + os.urandom(3).hex()
                )
                / name
            )
            # Legacy publisher MD5 detects transfer errors only; it is not authentication.
            dest.parent.mkdir(parents=True, exist_ok=False)
            part = dest.with_name(dest.name + ".part")
            sha = hashlib.sha256()
            md5 = hashlib.md5(usedforsecurity=False)
            count = 0
            with get(url) as response, part.open("wb") as out:
                while True:
                    block = response.read(8 * 1024 * 1024)
                    if not block:
                        break
                    out.write(block)
                    sha.update(block)
                    md5.update(block)
                    count += len(block)
            if size and count != int(size):
                raise ValueError("Download size is different.")
            if expected and sha.hexdigest().lower() != expected.lower():
                raise ValueError("SHA256 is not true.")
            if (
                not asset
                and item.get("expected_md5")
                and md5.hexdigest().lower() != item["expected_md5"].lower()
            ):
                raise ValueError("MD5 is not true.")
            if not count:
                raise ValueError("Empty download.")
            part.replace(dest)
            result.update(
                status="Separately loaded; setup/data verification still required",
                path=str(dest),
                version=v,
                sha256=sha.hexdigest(),
                publisher_hash_verified=bool(
                    expected and (asset or not item.get("checksum_origin"))
                ),
                bytes=count,
                source=url,
            )
            write(dest.parent / "manifest.json", result)
        except Exception as e:
            result["error"] = str(e)
        results.append(result)
    write(STATE / "downloads.json", {"finished": NOW(), "items": results})
    return {
        "items": results,
        "note": "Active versions and personal DNA were not overwritten.",
    }


def stage_clinvar(item):
    base = item["url"].removesuffix(".tbi")
    urls = [base, base + ".tbi"]
    checks = {}

    def checksum(url):
        with get(url + ".md5") as response:
            text = response.read(2048).decode()
        m = re.search(r"\b[a-fA-F0-9]{32}\b", text)
        if not m:
            raise ValueError("ClinVar publisher MD5 is missing.")
        return m[0].lower()

    for url in urls:
        checks[url] = checksum(url)
    folder = (
        ROOT
        / "DNA_Software/Updates/ClinVar"
        / ("GRCh38" if "GRCh38" in base else "GRCh37")
        / (
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "_"
            + os.urandom(3).hex()
        )
    )
    folder.mkdir(parents=True)
    artifacts = []
    for url in urls:
        dest = folder / url.rsplit("/", 1)[-1]
        part = dest.with_suffix(dest.suffix + ".part")
        md5 = hashlib.md5(usedforsecurity=False)
        sha = hashlib.sha256()
        size = 0
        with get(url) as response, part.open("wb") as out:
            while True:
                block = response.read(8 * 1024 * 1024)
                if not block:
                    break
                out.write(block)
                md5.update(block)
                sha.update(block)
                size += len(block)
        if md5.hexdigest() != checks[url]:
            raise ValueError("ClinVar-MD5 is not true; version not released.")
        if checksum(url) != checks[url]:
            raise ValueError("ClinVar changed during the download.")
        part.replace(dest)
        artifacts.append(
            {
                "file": dest.name,
                "sha256": sha.hexdigest(),
                "publisher_md5": checks[url],
                "bytes": size,
            }
        )
    with gzip.open(folder / "clinvar.vcf.gz", "rt") as f:
        if not f.readline().startswith("##fileformat=VCF"):
            raise ValueError("No readable ClinVar VCF found.")
    result = {
        "id": item["id"],
        "status": "ClinVar snapshot and index downloaded; validation required before activation",
        "path": str(folder),
        "version": NOW(),
        "artifacts": artifacts,
        "source": base,
        "publisher_hash_verified": False,
        "publisher_md5_matches": True,
        "integrity_note": "Downloaded over HTTPS. Publisher MD5 checks detect transfer errors; they do not authenticate the publisher. SHA-256 is recorded locally, not independently publisher-verified.",
    }
    write(folder / "manifest.json", result)
    return result


def foundation():
    # Public recipe for the selected core scientific tools; no licensed RFMix.
    archives = {"samtools-1-25-tar-bz2", "bcftools-1-25-tar-bz2"}
    if not hardware.windows_arm64():
        archives.add("mosdepth")
    items = [i for i in LOCK["items"] if i["id"] in archives]
    plan = STATE / "foundation-plan.json"
    write(plan, items)
    for item in items:
        path = ROOT / item["relative_path"]
        if not path.exists():
            with get(item["url"]) as response:
                path.parent.mkdir(parents=True, exist_ok=True)
                part = path.with_suffix(".part")
                with part.open("wb") as out:
                    while True:
                        block = response.read(8 * 1024 * 1024)
                        if not block:
                            break
                        out.write(block)
                if (
                    hashlib.file_digest(part.open("rb"), "sha256").hexdigest()
                    != item["expected_sha256"]
                ):
                    raise ValueError("Foundation checksum mismatch")
                part.replace(path)
        if (
            hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
            != item["expected_sha256"]
        ):
            raise ValueError("Foundation checksum mismatch")
    mount = "/mnt/" + ROOT.drive[0].lower() + ROOT.as_posix()[2:].rstrip("/")
    cmd = [
        windows_executable("wsl.exe"),
        "-d",
        distro_name(ROOT),
        "-u",
        "root",
        "--",
        "bash",
        mount + "/DNA_Software/Launcher/install-foundation.sh",
        mount,
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (STATE / "foundation.log").write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(
            "Foundation installation failed; see " + str(STATE / "foundation.log")
        )
    return {
        "status": "Linux-Analysegrundlage eingerichtet",
        "log": str(STATE / "foundation.log"),
    }


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        ids = sys.argv[2:]
        result = (
            snapshot()
            if action == "snapshot"
            else check_updates(ids)
            if action == "check"
            else stage(ids)
            if action == "stage"
            else foundation()
            if action == "install-foundation"
            else None
        )
        if result is None:
            raise ValueError("Unbekannte Aktion")
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
