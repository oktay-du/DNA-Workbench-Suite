"""Typed API for the native desktop shell; reuses the existing job runner."""

from pathlib import Path
import datetime, os, subprocess, sys, threading, uuid
import portable_json as json
import family, source_store, inspector
import portable_paths
import security_paths

portable_paths.configure()
APP = Path(__file__).parent
ROOT = APP.parents[1]
CAT = lambda: json.loads((APP / "catalog.json").read_text(encoding="utf-8"))


def catalog_stamp():
    info = (APP / "catalog.json").stat()
    return f"{info.st_mtime_ns}:{info.st_size}"


LOCK = threading.Lock()
PROCESSES = {}


def settings(r=None):
    path = ROOT / "DNA_Software/UserData/Launcher/appearance.json"
    if r is not None:
        if r.get("language") not in ("de", "en") or r.get("theme") not in (
            "light",
            "dark",
            "system",
        ):
            raise ValueError("Invalid language or presentation.")
        if r.get("design", "studio") not in ("studio", "archive"):
            raise ValueError("Unknown design theme")
        path.parent.mkdir(parents=True, exist_ok=True)
        import durable_store

        durable_store.write(
            path,
            {k: r[k] for k in ("language", "theme")}
            | {"design": r.get("design", "studio")},
            backup=True,
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"language": "en", "theme": "light"}


def profiles():
    with family.connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM people ORDER BY label")]


def checked_person(pid):
    pid = security_paths.identifier(pid)
    if pid not in {p["id"] for p in profiles()}:
        raise ValueError("Select profile / select a profile.")
    return pid


def job_path(pid, job_id):
    """Validate the selected profile before exposing an owned job directory."""
    if not str(job_id).startswith("transfer_"):
        checked_person(pid)
    return _owned_job_path(pid, job_id)


def _owned_job_path(pid, job_id):
    """Resolve a job for a profile already checked within this request."""
    job_id = security_paths.identifier(job_id)
    if job_id.startswith("transfer_"):
        import profile_transfer

        path = security_paths.contained(profile_transfer.base(), job_id)
        status = json.loads((path / "status.json").read_text(encoding="utf-8"))
        if status.get("person", "") != (pid or ""):
            raise ValueError("Profile operation belongs to a different profile")
        return path
    return security_paths.job(ROOT, pid, job_id)


def _profile_jobs(pid, transfers):
    """Use one request-scoped profile/transfer snapshot, never a persistent cache."""
    base = security_paths.profile_jobs(ROOT, pid)
    candidates = []
    for path in base.glob("*/status.json"):
        try:
            candidates.append((path.stat().st_mtime_ns, path))
        except OSError:
            continue  # A job can be removed between directory listing and stat.
    rows = []
    for _, path in sorted(candidates, key=lambda item: item[0], reverse=True)[:100]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                continue
            value["job"] = path.parent.name
            rows.append(value)
        except (ValueError, OSError):
            continue
    return sorted(
        rows + [j for j in transfers if j.get("person") == pid],
        key=lambda row: row.get("started", ""),
        reverse=True,
    )


def jobs(pid):
    checked_person(pid)
    import profile_transfer

    return _profile_jobs(pid, profile_transfer.jobs())


def all_jobs():
    import profile_transfer

    people = profiles()
    transfers = profile_transfer.jobs()
    rows = []
    for person in people:
        security_paths.identifier(person["id"])
        for row in _profile_jobs(person["id"], transfers):
            row.update(person=person["id"], profile_name=person["label"])
            base = _owned_job_path(person["id"], row["job"])
            progress = row.get("progress")
            try:
                step = json.loads(
                    (base / "inspection-status.json").read_text(encoding="utf-8")
                )
                if 0 <= step["completed"] <= step["total"] and step["total"] > 0:
                    progress = {
                        "completed": step["completed"],
                        "total": step["total"],
                        "unit": step.get("unit", "files"),
                        "percent": round(100 * step["completed"] / step["total"], 1),
                    }
            except (OSError, ValueError, KeyError, TypeError):
                pass
            if row.get("task") == "profile_analyze":
                try:
                    historical = json.loads(
                        (base / "Results/analysis.json").read_text(encoding="utf-8")
                    )
                    if not historical.get("sources"):
                        row.update(
                            status="Inputs required",
                            error="Historical empty analysis: no source comparison was performed.",
                        )
                except (OSError, ValueError):
                    pass
            row["progress"] = progress
            try:
                with (base / "auftrag.log").open("rb") as stream:
                    stream.seek(max(0, (base / "auftrag.log").stat().st_size - 4096))
                    lines = stream.read().decode("utf-8", errors="replace").splitlines()
                row["activity"] = next(
                    (line[:500] for line in reversed(lines) if line.strip()), ""
                )
            except OSError:
                row["activity"] = ""
            rows.append(row)
    import profile_transfer

    rows += [
        r | {"person_label": "Profile import / backup"}
        for r in transfers
        if not r.get("person")
    ]
    return sorted(
        rows,
        key=lambda x: (
            x.get("status") in ("Running", "Queued", "Preparing"),
            x.get("started", ""),
        ),
        reverse=True,
    )


def snapshot(pid=None, catalog_token=None):
    people = profiles()
    pid = (
        pid if pid in {x["id"] for x in people} else people[0]["id"] if people else None
    )
    import profile_pipeline
    import release_tools, sample_data

    token = catalog_stamp()
    data = {
        "sample_profile": sample_data.is_sample(pid) if pid else False,
        "project": release_tools.info(),
        "people": people,
        "person": pid,
        "files": source_store.listing(pid) if pid else [],
        "best_selection": profile_pipeline.summary(pid) if pid else {"sets": []},
        "jobs": jobs(pid) if pid else [],
        "settings": settings(),
        "catalog_token": token,
        "providers": inspector.PROVIDERS,
        "root": str(ROOT),
        "version": json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))[
            "app_version"
        ],
    }
    # The tool catalog is large and stable. Menus reuse it until the file changes.
    if catalog_token != token:
        data["catalog"] = CAT()
    return data


def refresh_tick():
    import profile_pipeline

    if any(proc.poll() is None for proc in list(PROCESSES.values())):
        return
    base = ROOT / "DNA_Software/UserData/Launcher/Refresh"
    for marker in base.glob("*.json"):
        request = {}
        try:
            request = json.loads(marker.read_text(encoding="utf-8"))
            if request.get("status") not in ("queued_by_user", "running"):
                continue
            pid = checked_person(request["person"])
            if not profile_pipeline.refresh_available(pid):
                continue
            if request.get("status") == "running":
                try:
                    age = (
                        datetime.datetime.now().astimezone()
                        - datetime.datetime.fromisoformat(request["running_since"])
                    ).total_seconds()
                except (ValueError, KeyError):
                    age = 31
                if age < 30:
                    continue
                profile_pipeline.atomic(
                    marker,
                    dict(
                        request,
                        status="failed",
                        error="Interrupted renewal. Start again via the button.",
                    ),
                )
                continue
            request.update(
                status="running",
                running_since=datetime.datetime.now().astimezone().isoformat(),
            )
            profile_pipeline.atomic(marker, request)
            path = job_path(pid, request["job"])
            if (path / "abbrechen.request").exists():
                profile_pipeline.atomic(marker, dict(request, status="cancelled"))
                continue
            result = start(
                {"person": pid, "task": "profile_refresh", "inputs": {}},
                queued_job=request["job"],
            )
            current = json.loads(marker.read_text(encoding="utf-8"))
            if (
                current.get("nonce") == request.get("nonce")
                and current.get("status") == "running"
            ):
                profile_pipeline.atomic(marker, dict(current, job=result["job"]))
            return
        except Exception as error:
            try:
                profile_pipeline.atomic(
                    marker, dict(request, status="failed", error=str(error))
                )
            except (OSError, ValueError) as write_error:
                __import__("logging").getLogger(__name__).warning(
                    "Cannot persist failed refresh: %s", write_error
                )


def start_refresh_service():
    def loop():
        import time

        while True:
            try:
                refresh_tick()
            except Exception:
                __import__("logging").getLogger(__name__).exception(
                    "Refresh service failed"
                )
            time.sleep(4)

    threading.Thread(target=loop, daemon=True, name="BestSelectionQueue").start()


def submit_renewal(r):
    import workflows

    workflows.assert_idle()
    import profile_pipeline

    pid = checked_person(r["person"])
    state = profile_pipeline.summary(pid)
    if not state["sets"]:
        raise ValueError("First, create and activate a cleaned SNP selection.")
    with LOCK:
        if state["refresh"].get("status") == "queued_by_user":
            return {"job": state["refresh"]["job"], "person": pid, "status": "queued"}
        if not profile_pipeline.refresh_available(pid):
            raise ValueError("A renewal is already underway for this profile.")
        name = (
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "_profile_refresh_"
            + uuid.uuid4().hex[:6]
        )
        folder = job_path(pid, name)
        folder.mkdir(parents=True)
        (folder / "inputs.json").write_text(
            json.dumps({"task": "profile_refresh", "person": pid, "inputs": {}}),
            encoding="utf-8",
        )
        (folder / "status.json").write_text(
            json.dumps(
                {
                    "id": name,
                    "job": name,
                    "task": "profile_refresh",
                    "person": pid,
                    "title": "Renew Best Selection",
                    "status": "Queued",
                    "started": datetime.datetime.now().astimezone().isoformat(),
                }
            ),
            encoding="utf-8",
        )
        profile_pipeline.atomic(
            profile_pipeline.queue_path(pid),
            {
                "person": pid,
                "build": state["sets"][0]["build"],
                "nonce": uuid.uuid4().hex,
                "status": "queued_by_user",
                "job": name,
                "created": datetime.datetime.now().astimezone().isoformat(),
            },
        )
    refresh_tick()
    return {"job": name, "person": pid, "status": "queued"}


def start(r, queued_job=None):
    import source_batch

    source_batch.assert_idle()
    import batch_intake

    batch_intake.assert_idle()
    import workflows

    workflows.assert_idle()
    pid = checked_person(r["person"])
    task = next((t for t in CAT()["tasks"] if t["id"] == r.get("task")), None)
    import profile_identity

    profile_identity.assert_writable(pid)
    if not task:
        raise ValueError("Unbekannter Arbeitsablauf.")
    import sample_data

    if task["id"] in (
        "pharmcat",
        "pgs",
        "vep",
        "opencravat_run",
        "mito",
        "yhaplo",
        "pca",
        "rfmix",
        "ancient",
    ) and sample_data.is_sample(pid):
        raise ValueError(
            "Synthetic sample profile: no health, haplogroup or genetic ancestry inference. Use illustrative imported demo views only."
        )
    values = r.get("inputs", {})
    if not isinstance(values, dict):
        raise ValueError("Invalid submissions.")
    allowed = {x["key"] for x in task["fields"]} | {"checked_folder", "storage_mode"}
    if set(values) - allowed:
        raise ValueError("Unbekannte Eingabefelder.")
    for field in task["fields"]:
        val = values.get(field["key"], "")
        if field["kind"] == "choice" and val and val not in field["choices"]:
            raise ValueError("Invalid selection:" + field["label"])
    import tool_inputs

    gate = tool_inputs.prepare(
        {"person": pid, "task": task["id"], "inputs": values, "phase": "ready"}
    )
    if not gate["accepted"]:
        messages = [x["message"] for x in gate["errors"]] + [
            "Missing: " + x["label"] for x in gate["missing"]
        ]
        raise ValueError("Input compatibility: " + "; ".join(messages))
    values = gate["inputs"]
    import workflow_sources

    source_rows = source_store.listing(pid)
    input_manifest = workflow_sources.manifest(task["id"], values, source_rows)
    import execution_journal

    source_state = execution_journal.source_state([pid])
    for entry in input_manifest["sources"]:
        buildkey = {"a": "build_a", "b": "build_b"}.get(entry["field"], "build")
        declared = values.get(buildkey)
        if (
            declared in ("GRCh37", "GRCh38")
            and entry["build"] in ("GRCh37", "GRCh38")
            and declared != entry["build"]
        ):
            raise ValueError(
                "Recognized reference build contradicts the selection:" + entry["path"]
            )
    preview = r.get("preview") is True
    import result_cache

    result_identity = result_cache.fingerprint(ROOT, pid, task, values)
    if not preview and not r.get("rerun", False) and not queued_job:
        cached = result_cache.lookup(ROOT, pid, task, values, jobs(pid))
        if cached["previous"]:
            return {
                "job": cached["previous"]["job"],
                "person": pid,
                "status": "cached",
                "task": task["id"],
                "verified": True,
            }
    if not preview and task["id"] in ("family", "visual", "profile_view"):
        raise ValueError("Open this view in the menu.")
    with LOCK:
        if any(proc.poll() is None for proc in PROCESSES.values()):
            raise ValueError("An order is already underway; wait for its completion.")
        if not preview and not r.get("rerun", False) and not queued_job:
            cached = result_cache.lookup(ROOT, pid, task, values, jobs(pid))
            if cached["previous"]:
                return {
                    "job": cached["previous"]["job"],
                    "person": pid,
                    "status": "cached",
                    "task": task["id"],
                    "verified": True,
                }
        name = (
            queued_job
            or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "_"
            + task["id"]
            + "_"
            + uuid.uuid4().hex[:6]
        )
        folder = job_path(pid, name)
        folder.mkdir(parents=True, exist_ok=queued_job is not None)
        request = folder / "inputs.json"
        request.write_text(
            json.dumps(
                {
                    "task": task["id"],
                    "person": pid,
                    "inputs": values,
                    "source_selection": r.get("sources", []),
                    "input_manifest": input_manifest,
                    "source_state": source_state,
                    "result_identity": result_identity,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        import engine

        job = engine.Job(request)
        try:
            job.validate()
        finally:
            job.log_handle.close()
        command = [sys.executable, str(APP / "engine.py"), str(request)] + (
            ["--preview"] if preview else []
        )
        log = (folder / "startfehler.log").open("ab")
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=log,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=dict(os.environ, PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8"),
            )
        finally:
            log.close()
        PROCESSES[name] = proc
    return {"job": name, "person": pid, "status": "started", "task": task["id"]}


def inspect(r):
    import batch_intake

    batch_intake.assert_idle()
    import workflows

    workflows.assert_idle()
    pid = checked_person(r["person"])
    files = r.get("files", [])
    if not isinstance(files, list) or not files or len(files) > 50:
        raise ValueError("Select 1–50 files.")
    for file in files:
        if not security_paths.input_file(file).is_file():
            raise ValueError("File missing:" + str(file))
    with LOCK:
        if any(proc.poll() is None for proc in PROCESSES.values()):
            raise ValueError("An order is already underway.")
        name = (
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "_check_"
            + uuid.uuid4().hex[:6]
        )
        folder = job_path(pid, name)
        folder.mkdir(parents=True)
        request = folder / "check-request.json"
        request.write_text(
            json.dumps({"person": pid, "files": files}), encoding="utf-8"
        )
        (folder / "status.json").write_text(
            json.dumps(
                {
                    "id": name,
                    "job": name,
                    "task": "inspection",
                    "title": "Check files / Check source files",
                    "person": pid,
                    "status": "Running",
                    "started": datetime.datetime.now().isoformat(),
                }
            ),
            encoding="utf-8",
        )
        with (folder / "auftrag.log").open("ab") as log:
            PROCESSES[name] = subprocess.Popen(
                [sys.executable, str(APP / "engine.py"), "--inspect", str(request)],
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            )
    return {"job": name, "person": pid, "folder": str(folder), "status": "checking"}


def dispatch(action, r):
    if action == "all-jobs":
        return {"jobs": all_jobs()}
    if action in ("profile-read", "profile-save", "profile-photo"):
        import person_profile

        pid = checked_person(r["person"])
        if action == "profile-read":
            return person_profile.read(pid)
        if action == "profile-photo":
            return person_profile.photo(pid, r["data_url"])
        return person_profile.save(pid, r["values"])
    if action == "snapshot":
        return snapshot(r.get("person"), r.get("catalog_token") or None)
    if action == "settings":
        return settings(r)
    if action == "run":
        return start(r)
    if action == "inspect":
        return inspect(r)
    if action == "renew-selection":
        return submit_renewal(r)
    if action == "workflow-result":
        import result_cache

        pid = checked_person(r["person"])
        task = next((t for t in CAT()["tasks"] if t["id"] == r.get("task")), None)
        if not task or not isinstance(r.get("inputs"), dict):
            raise ValueError("Invalid workflow input")
        return result_cache.lookup(ROOT, pid, task, r["inputs"], jobs(pid))
    if action == "workflow-sources":
        import workflow_sources

        pid = checked_person(r["person"])
        if r.get("task") not in {t["id"] for t in CAT()["tasks"]}:
            raise ValueError("Unbekannter Arbeitsablauf.")
        return workflow_sources.plan(ROOT, pid, r["task"], jobs(pid))
    if action == "file-build":
        import workflow_sources

        paths = r.get("files", [])
        if not isinstance(paths, list) or len(paths) > 50:
            raise ValueError("Too many files.")
        return {"files": [workflow_sources.metadata(str(p)) for p in paths]}
    if action == "result-preview":
        base = (job_path(r["person"], r["job"]) / "Results").resolve()
        path = (base / str(r.get("file", ""))).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError("Invalid result file.")
        if path.suffix.lower() not in (
            ".txt",
            ".csv",
            ".tsv",
            ".json",
            ".md",
            ".html",
            ".htm",
            ".svg",
        ):
            raise ValueError("Open file about Show result.")
        story = False
        if path.name == "Heritage_Story.html":
            try:
                story = (
                    json.loads(
                        (base.parent / "inputs.json").read_text(encoding="utf-8")
                    )["task"]
                    == "storybook"
                )
            except (OSError, ValueError, KeyError):
                pass
        limit = 64 * 1024 * 1024 if story else 524288
        with path.open("rb") as stream:
            text = stream.read(limit).decode("utf-8", errors="replace")
        return {
            "name": path.name,
            "kind": path.suffix.lower(),
            "text": text,
            "truncated": path.stat().st_size > limit,
            "interactive_story": story,
        }
    if action == "new-person":
        pid = source_store.new_person(str(r.get("label", "")).strip())
        with family.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO people VALUES(?,?,0)",
                (pid, str(r.get("label", "")).strip()),
            )
        import profile_identity

        profile_identity.ensure(pid)
        return {"person": pid}
    if action == "jobs":
        return {"jobs": jobs(r["person"])}
    if action in ("job", "cancel"):
        path = job_path(r["person"], r["job"])
        if not path.is_dir():
            raise ValueError("Order not available.")
        if action == "cancel":
            (path / "abbrechen.request").write_text(datetime.datetime.now().isoformat())
            file = path / "status.json"
            if file.is_file():
                status = json.loads(file.read_text(encoding="utf-8"))
                if status.get("status") == "Queued":
                    status["status"] = "Cancelled"
                    file.write_text(
                        json.dumps(status, ensure_ascii=False), encoding="utf-8"
                    )
                    import profile_pipeline

                    marker = profile_pipeline.queue_path(r["person"])
                    if marker.is_file():
                        pending = json.loads(marker.read_text(encoding="utf-8"))
                        if pending.get("job") == r["job"]:
                            profile_pipeline.atomic(
                                marker, dict(pending, status="cancelled")
                            )
            return {"status": "cancel-requested"}
        out = {}
        for name, key in [
            ("status.json", "status"),
            ("auftrag.log", "log"),
            ("command.txt", "command"),
            ("startfehler.log", "errors"),
        ]:
            file = path / name
            if file.is_file():
                data = file.read_bytes()[-80000:].decode("utf-8", errors="replace")
                out[key] = json.loads(data) if name.endswith(".json") else data
        out["folder"] = str(path / "Results")
        import workflow_sources

        out["artifacts"] = (
            workflow_sources.result_files(ROOT, r["person"], r["job"])
            if not r["job"].startswith("transfer_")
            else []
        )
        if (path / "check-request.json").is_file():
            proc = PROCESSES.get(r["job"])
            if (path / "inspection.json").is_file() and not out["status"].get(
                "manual_review"
            ):
                out["checks"] = [
                    {
                        k: v
                        for k, v in json.loads(p.read_text(encoding="utf-8")).items()
                        if k not in ("fingerprint", "header")
                    }
                    for p in sorted(path.glob("*_inspection.json"))
                ]
                out["checked_folder"] = str(path)
                out["status"]["status"] = "Complete"
                (path / "status.json").write_text(
                    json.dumps(out["status"], ensure_ascii=False), encoding="utf-8"
                )
            elif proc is not None and proc.poll() is not None:
                out["status"]["status"] = "Failed"
        return out
    raise ValueError("Unbekannte Suite-Aktion.")
