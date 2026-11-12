from system_tools import windows_executable
import network_io

"""Curated local plugins. Project discovery never supplies executable commands."""
from portable_paths import distro_name
from pathlib import Path
import urllib.error
import concurrent.futures, datetime, hashlib, os, re, subprocess, sys, threading, urllib.request, uuid, zipfile
import portable_json as json
import on_demand, visual_tools

APP = Path(__file__).parent
ROOT = APP.parents[1]
STATE = ROOT / "DNA_Software/UserData/Launcher/Plugins"
SOURCES = ROOT / "DNA_Software/SourceArchives"
POOL = concurrent.futures.ThreadPoolExecutor(max_workers=1)
GUARD = threading.Lock()
ACTIVE = {}
TASKS = {
    "snps": "chip_vcf",
    "peddy": "peddy",
    "whatshap": "whatshap",
    "truvari": "truvari",
    "sarek": "sarek",
    "pgsc-calc": "pgs",
    "pharmcat": "pharmcat",
    "hap-ibd": "ibd",
    "rfmix": "rfmix",
    "gramps": "gramps",
}
TASKS.update(
    {
        "biopython": "sequence_stats",
        "pyfastx": "sequence_extract",
        "seqviz": "seqviz_view",
        "gatk": "gatk_validate",
        "ugene": "ugene",
    }
)
RESTRICTED = {"rfmix"}


def now():
    return datetime.datetime.now().astimezone().isoformat()


def audit():
    return json.loads((APP / "project-audit.json").read_text(encoding="utf-8"))


def project(id):
    row = next((x for x in audit()["projects"] if x["id"] == id), None)
    if not row:
        raise ValueError("No audited project with this identifier.")
    return row


def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def cached(name, default=None):
    try:
        return json.loads((STATE / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {} if default is None else default


def listing():
    rows = []
    probes = cached("probes.json")
    updates = cached("updates.json")
    for item in audit()["projects"]:
        id = item["id"]
        visual = id in visual_tools.LOCK
        visual_installable = visual and (
            os.name == "nt" or visual_tools.LOCK[id]["kind"] != "pip"
        )
        tool = id in on_demand.TOOLS
        recipe = (
            "visual"
            if visual_installable
            else "on-demand"
            if not visual
            and tool
            and on_demand.TOOLS[id][2] not in ("manual", "windows-manual")
            else ""
        )
        receipt = cached("source-" + id + ".json")
        source_ok = False
        if receipt:
            path = Path(receipt.get("path", ""))
            source_ok = path.is_file() and receipt.get("commit") == item.get("commit")
        rows.append(
            dict(
                item,
                recipe=recipe,
                installable=bool(recipe),
                installed=(
                    visual_tools.installed(id)
                    and probes.get(id, {}).get("installed", True)
                )
                if visual
                else probes.get(id, {}).get("installed"),
                installed_version=visual_tools.LOCK[id]["version"]
                if visual and visual_tools.installed(id)
                else probes.get(id, {}).get("version", "Not tested"),
                task=TASKS.get(id, ""),
                visual=visual,
                source_downloaded=source_ok,
                source_receipt=receipt,
                update=updates.get(id, {}),
                restriction=on_demand.LICENSE if id in RESTRICTED else "",
                probe=probes.get(id, {}),
            )
        )
    return {
        "projects": rows,
        "checked": audit()["checked"],
        "jobs": jobs(),
        "linux": on_demand.linux_state(),
        "note": "Installed libraries and their licenses remain independent. A plugin or separate download does not cancel terms of use. No personal data is sent for updates or source retrievals.",
    }


def archive(id, rights=False):
    row = project(id)
    if id in RESTRICTED and not rights:
        raise ValueError(on_demand.LICENSE)
    commit = row.get("commit", "")
    repo = row["repo"]
    if not re.fullmatch("[a-f0-9]{40}", commit) or not re.fullmatch(
        "[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo
    ):
        raise ValueError("No recorded source status available.")
    SOURCES.mkdir(parents=True, exist_ok=True)
    path = SOURCES / (id + "-" + commit + ".zip")
    receipt = cached("source-" + id + ".json")
    if path.exists() and receipt.get("path") == str(path):
        with path.open("rb") as stream:
            sha = hashlib.file_digest(stream, "sha256").hexdigest()
        if sha != receipt.get("sha256"):
            raise ValueError("Source archive changed; checksum is not correct.")
        return receipt
    part = path.with_suffix(".zip.part")
    sha = hashlib.sha256()
    total = 0
    with (
        network_io.open_https(
            urllib.request.Request(
                row["source_url"],
                headers={"User-Agent": "DNAWorkbench-source-archive/1"},
            ),
            timeout=90,
        ) as response,
        part.open("wb") as output,
    ):
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            total += len(chunk)
            if total > 150 * 1024 * 1024:
                raise ValueError("Source archive over 150 MiB; use project page.")
            sha.update(chunk)
            output.write(chunk)
    with zipfile.ZipFile(part) as zipped:
        if len(zipped.infolist()) > 100000:
            raise ValueError("Too many archive entries.")
        if sum(x.file_size for x in zipped.infolist()) > 1024**3:
            raise ValueError("Unpacked source code too large.")
        for entry in zipped.infolist():
            visual_tools.safe_member(entry.filename)
    part.replace(path)
    receipt = {
        "id": id,
        "path": str(path),
        "commit": commit,
        "sha256": sha.hexdigest(),
        "bytes": total,
        "source_url": row["source_url"],
        "license": row.get("license", "Unresolved"),
        "downloaded": now(),
        "note": "Archive from captured commit; SHA-256 documented after HTTPS download, no independent upstream signature; not executed and not included in the public app package.",
    }
    atomic(STATE / ("source-" + id + ".json"), receipt)
    return receipt


def probe(id):
    item = project(id)
    if id in visual_tools.LOCK:
        result = {
            "installed": visual_tools.installed(id),
            "version": visual_tools.LOCK[id]["version"],
            "checked": now(),
            "detail": "Installation manifest and entry point checksum",
        }
        entry = visual_tools.LOCK[id]
        if entry["kind"] == "pip" and result["installed"]:
            code = (
                "import "
                + entry.get("module", id)
                + "; import importlib.metadata as m; print(m.version("
                + repr(entry["package"])
                + "))"
            )
            check = subprocess.run(
                [str(visual_tools.BASE / id / entry["entry"]), "-c", code],
                capture_output=True,
                timeout=45,
                env=dict(os.environ, PYTHONNOUSERSITE="1", MPLBACKEND="Agg"),
            )
            version = check.stdout.decode("utf-8", errors="replace").strip()
            result.update(
                installed=check.returncode == 0 and version == entry["version"],
                version=version or entry["version"],
                detail="Library import and package version checked"
                if check.returncode == 0
                else check.stderr.decode("utf-8", errors="replace")[-1500:],
            )
    elif id in on_demand.TOOLS:
        if id in on_demand.WINDOWS:
            tasks = {
                id: next(
                    (
                        t["id"]
                        for t in on_demand.CAT["tasks"]
                        if id in on_demand.mapped(t["id"])
                    ),
                    None,
                )
            }
            report = on_demand.status(tasks[id]) if tasks[id] else {}
            r = next((x for x in report.get("requirements", []) if x["id"] == id), {})
            result = {
                "installed": r.get("installed"),
                "version": r.get("version", "Not tested"),
                "checked": now(),
                "detail": r.get("state", "No test prescription"),
            }
        elif not on_demand.linux_state()["running"]:
            result = {
                "installed": None,
                "version": "Not tested",
                "checked": now(),
                "detail": "WSL is stopped; not started by this test.",
            }
        else:
            modules = {
                "snps": "snps",
                "peddy": "peddy",
                "whatshap": "whatshap",
                "truvari": "truvari",
            }
            executable = {
                "rfmix": "rfmix",
                "pharmcat": "pharmcat",
                "hap-ibd": "hap-ibd",
                "sarek": "nextflow",
                "pgsc-calc": "nextflow",
            }.get(id, id)
            code = (
                "import json,shutil,importlib.util,importlib.metadata as m; module="
                + repr(modules.get(id))
                + "; tool="
                + repr(executable)
                + "; exists=bool(importlib.util.find_spec(module)) if module else bool(shutil.which(tool)); version=m.version(module) if module and exists else ''; print(json.dumps({'installed':exists,'version':version,'executable':shutil.which(tool)}))"
            )
            runtime = (
                "/opt/dna/envs/" + id + "/bin/python"
                if id in ("peddy", "whatshap", "truvari")
                else "/opt/dna/envs/analysis/bin/python"
            )
            args = [
                windows_executable("wsl.exe"),
                "-d",
                distro_name(ROOT),
                "-u",
                "dna",
                "--",
                "env",
                "PATH=/opt/dna/bin:/opt/dna/envs/analysis/bin:/usr/local/bin:/usr/bin:/bin",
                runtime,
                "-c",
                code,
            ]
            r = subprocess.run(args, capture_output=True, timeout=30)
            if r.returncode:
                raise ValueError(
                    "WSL test failed:" + r.stderr.decode(errors="replace")[-1000:]
                )
            result = json.loads(r.stdout)
            result.update(
                checked=now(),
                detail="Library import / executable entry point; no scientific proof of validation.",
            )
            if not result.get("version"):
                receipt = next(
                    (
                        x
                        for x in on_demand.LOCK["items"]
                        if x.get("source") == item["url"]
                    ),
                    {},
                )
                result["version"] = (
                    receipt.get("version")
                    or receipt.get("commit")
                    or "Presence; version not determined"
                )
    else:
        result = {
            "installed": None,
            "version": "Not an execution adapter",
            "checked": now(),
            "detail": "Only research archive; no local operational readiness claimed.",
        }
    values = cached("probes.json")
    values[id] = result
    atomic(STATE / "probes.json", values)
    return result


def updates(ids):
    results = cached("updates.json")
    for id in ids:
        row = project(id)
        repo = row["repo"]
        rec = {"checked": now()}
        try:
            if (
                id in visual_tools.LOCK and visual_tools.LOCK[id]["kind"] == "pip"
            ) or id in on_demand.PIP:
                package = (
                    visual_tools.LOCK[id]["package"]
                    if id in visual_tools.LOCK
                    else on_demand.PIP[id].split("==")[0]
                )
                url = "https://pypi.org/pypi/" + package + "/json"
                with network_io.open_https(url, timeout=30) as response:
                    data = json.load(response)
                rec.update(
                    latest=data["info"]["version"], url=data["info"]["project_url"]
                )
            else:
                url = "https://api.github.com/repos/" + repo + "/releases/latest"
                try:
                    with network_io.open_https(
                        urllib.request.Request(
                            url, headers={"User-Agent": "DNAWorkbench-public-updates"}
                        ),
                        timeout=30,
                    ) as response:
                        data = json.load(response)
                    rec.update(latest=data["tag_name"], url=data["html_url"])
                except urllib.error.HTTPError as error:
                    if error.code != 404:
                        raise
                    with network_io.open_https(
                        urllib.request.Request(
                            "https://api.github.com/repos/"
                            + repo
                            + "/commits?per_page=1",
                            headers={"User-Agent": "DNAWorkbench-public-updates"},
                        ),
                        timeout=30,
                    ) as response:
                        data = json.load(response)
                    rec.update(
                        latest=data[0]["sha"],
                        url=data[0]["html_url"],
                        kind="Sourcecommit; no tested release",
                    )
            rec["status"] = (
                "Public metadata checked. Installation remains on the tested state; check new version separately."
            )
        except Exception as error:
            rec.update(status="Online verification failed", error=str(error))
        results[id] = rec
    atomic(STATE / "updates.json", results)
    return results


def jobs():
    result = []
    for path in sorted(STATE.glob("job-*.json"), reverse=True)[:30]:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            if rec["state"] == "running" and rec["id"] not in ACTIVE:
                rec["state"] = "interrupted"
                rec["detail"] = (
                    "Service has been terminated. Check result and protocol before restart."
                )
            result.append(rec)
        except (OSError, ValueError):
            pass
    return result


def submit(r):
    action = r.get("action")
    id = r.get("id", "")
    rights = r.get("rights") is True
    if action not in (
        "install",
        "install-tool",
        "source",
        "probe",
        "updates",
        "start-linux",
    ):
        raise ValueError("Unbekannte Plugin-Aktion.")
    if action == "install-tool":
        if id not in on_demand.TOOLS:
            raise ValueError("Unknown dependence.")
    elif action != "start-linux":
        project(id)
    if (
        id in RESTRICTED
        and action in ("install", "install-tool", "source")
        and not rights
    ):
        raise ValueError(on_demand.LICENSE)
    with GUARD:
        if ACTIVE:
            raise ValueError(
                "A plugin job is already running. Wait until it is completed."
            )
        job = uuid.uuid4().hex
        path = STATE / ("job-" + job + ".json")
        record = {
            "id": job,
            "plugin": id,
            "action": action,
            "state": "running",
            "started": now(),
            "detail": "Waiting for background execution",
        }
        atomic(path, record)
        ACTIVE[job] = record

    def work():
        try:
            if action == "source":
                result = archive(id, rights)
            elif action == "probe":
                result = probe(id)
            elif action == "updates":
                result = updates([id])
            elif action == "start-linux":
                result = on_demand.start_linux()
            else:
                if id in visual_tools.LOCK:
                    command = [
                        sys.executable,
                        str(APP / "visual_tools.py"),
                        "install",
                        id,
                    ]
                elif id in on_demand.TOOLS and on_demand.TOOLS[id][2] not in (
                    "manual",
                    "windows-manual",
                ):
                    command = [
                        sys.executable,
                        str(APP / "on_demand.py"),
                        "install",
                        id,
                    ] + (["--license-reviewed"] if rights else [])
                else:
                    raise ValueError(
                        "Not yet a verified installation recipe for this project. Source archive / Project page use."
                    )
                p = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=3600,
                    env=dict(
                        os.environ, PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1"
                    ),
                )
                log = STATE / ("job-" + job + ".log")
                log.write_bytes(p.stdout)
                if p.returncode:
                    raise ValueError(
                        "Installation fehlgeschlagen. "
                        + str(log)
                        + "\n"
                        + p.stdout.decode("utf-8", errors="replace")[-1000:]
                    )
                if action == "install-tool":
                    task = next(
                        (
                            t["id"]
                            for t in on_demand.CAT["tasks"]
                            if id in on_demand.mapped(t["id"])
                        ),
                        None,
                    )
                    checked = (
                        on_demand.status(task)
                        if task
                        else {
                            "state": "Installation completed; no assigned function check."
                        }
                    )
                else:
                    checked = probe(id)
                result = {
                    "installation": p.stdout.decode("utf-8", errors="replace"),
                    "probe": checked,
                    "log": str(log),
                }
            record.update(
                state="complete",
                finished=now(),
                detail="Operation complete",
                result=result,
            )
        except Exception as error:
            record.update(state="failed", finished=now(), detail=str(error))
        finally:
            atomic(path, record)
            with GUARD:
                ACTIVE.pop(job, None)

    POOL.submit(work)
    return {"job": job, "status": "Started in the background"}


def dispatch(action, r):
    if action == "list":
        return listing()
    if action == "submit":
        return submit(r)
    if action == "jobs":
        return {"jobs": jobs()}
    raise ValueError("Unbekannte Plugin-Funktion.")
