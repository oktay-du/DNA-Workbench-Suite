"""One explicit tool run over selected provider/version source groups."""

import datetime, threading, time, uuid
import portable_json as json
import source_store, suite_api, workflow_sources, tool_inputs

GUARD = threading.RLock()
ACTIVE = None
OWNER = None


def assert_idle():
    with GUARD:
        if ACTIVE and OWNER != threading.get_ident():
            raise ValueError(
                "A source comparison batch is running. Wait or cancel first."
            )


def groups(person, task):
    suite_api.checked_person(person)
    next(t for t in suite_api.CAT()["tasks"] if t["id"] == task)
    roles = workflow_sources.ROLES.get(task, {})
    # Pair/comparison semantics cannot be guessed from provider checkboxes.
    enabled = len(roles) == 1 or set(roles) == {"r1", "r2"}
    rows = source_store.listing(person)
    result = {}
    for r in rows:
        if not r["available"]:
            continue
        key = r["batch_id"]
        g = result.setdefault(
            key,
            {
                "id": key,
                "provider": "BestDataset"
                if r.get("origin") == "own_generated"
                else r["provider"],
                "version": r.get("declared_version", ""),
                "created": r["created"],
                "build": r["build"],
                "source_ids": [],
                "files": [],
                "compatible": 0,
            },
        )
        g["source_ids"].append(r["id"])
        g["files"].append(
            {
                "id": r["id"],
                "name": r["original_name"],
                "kind": r["kind"],
                "sha256": r["sha256"],
            }
        )
        meta = dict(r, **workflow_sources.metadata(r["path"]))
        if any(
            workflow_sources.compatible(meta, role, task) for role in roles.values()
        ):
            g["compatible"] += 1
    return {
        "groups": list(result.values()),
        "batch_supported": enabled,
        "notice": "Best choice is tool-specific. Multiple-source runs preserve provider/version provenance; pairwise comparisons and aligned-read phasing retain explicit input roles.",
    }


def preview(r):
    person = suite_api.checked_person(r["person"])
    task = r["task"]
    spec = next(t for t in suite_api.CAT()["tasks"] if t["id"] == task)
    roles = workflow_sources.ROLES.get(task, {})
    if not groups(person, task)["batch_supported"]:
        raise ValueError(
            "This tool needs explicit comparison/input roles; choose its individual files rather than a provider batch."
        )
    ids = set(r.get("source_ids", []))
    rows = [x for x in source_store.listing(person) if x["id"] in ids]
    if ids != {x["id"] for x in rows}:
        raise ValueError("Selected source ID is not part of this profile.")
    if not rows:
        return {
            "person": person,
            "task": task,
            "runs": [],
            "accepted": False,
            "selected_files": 0,
            "compatible_runs": 0,
            "skipped_source_ids": [],
            "notice": "Select a provider/dataset group.",
        }
    import workflows

    plan = workflows.task_plan(person, task)
    settings = {k: v for k, v in r.get("inputs", {}).items() if k not in roles}
    phase = r.get("phase", "ready")
    runs = []
    seen = set()
    if len(roles) == 1:
        key, role = next(iter(roles.items()))
        f = next(f for f in spec["fields"] if f["key"] == key)
        for row in rows:
            meta = dict(row, **workflow_sources.metadata(row["path"]))
            if row["sha256"] in seen or not workflow_sources.compatible(
                meta, role, task
            ):
                continue
            seen.add(row["sha256"])
            values = dict(plan["inputs"])
            values.update(settings)
            values[key] = [row["path"]] if f.get("multi") else row["path"]
            if "build" in {f["key"] for f in spec["fields"]} and meta.get("build") in (
                "GRCh37",
                "GRCh38",
            ):
                values["build"] = meta["build"]
            gate = tool_inputs.prepare(
                {"person": person, "task": task, "inputs": values, "phase": phase}
            )
            aliases = [
                {
                    k: x.get(k)
                    for k in (
                        "id",
                        "provider",
                        "declared_version",
                        "original_name",
                        "sha256",
                        "build",
                        "created",
                    )
                }
                for x in rows
                if x["sha256"] == row["sha256"]
            ]
            runs.append(
                {
                    "source_ids": [a["id"] for a in aliases],
                    "source_aliases": aliases,
                    "inputs": gate["inputs"],
                    "accepted": gate["accepted"],
                    "missing": gate["missing"],
                    "errors": gate["errors"],
                }
            )
    else:
        for group in {x["batch_id"] for x in rows}:
            subset = [x for x in rows if x["batch_id"] == group]
            p = workflow_sources.plan(
                suite_api.ROOT, person, task, [], scope_ids={x["id"] for x in subset}
            )
            values = dict(plan["inputs"])
            values.update(settings)
            for key in roles:
                values.pop(key, None)
            values.update(p["inputs"])
            gate = tool_inputs.prepare(
                {"person": person, "task": task, "inputs": values, "phase": phase}
            )
            runs.append(
                {
                    "source_ids": [x["id"] for x in subset],
                    "source_aliases": [
                        {
                            k: x.get(k)
                            for k in (
                                "id",
                                "provider",
                                "declared_version",
                                "original_name",
                                "sha256",
                                "build",
                                "created",
                            )
                        }
                        for x in subset
                    ],
                    "inputs": gate["inputs"],
                    "accepted": gate["accepted"],
                    "missing": gate["missing"],
                    "errors": gate["errors"],
                }
            )
    for run in runs:
        if run["accepted"] and phase == "ready":
            run["previous"] = __import__("result_cache").lookup(
                suite_api.ROOT, person, spec, run["inputs"], suite_api.jobs(person)
            )["previous"]
    return {
        "person": person,
        "task": task,
        "runs": runs,
        "accepted": any(x["accepted"] for x in runs),
        "selected_files": len(rows),
        "compatible_runs": sum(x["accepted"] for x in runs),
        "skipped_source_ids": sorted(
            ids - {i for run in runs for i in run["source_ids"]}
        ),
        "notice": "One run per distinct compatible content; identical aliases never create extra scientific votes. Incompatible or missing inputs remain explicit.",
    }


def start(r):
    global ACTIVE
    import workflows, batch_intake

    workflows.assert_idle()
    batch_intake.assert_idle()
    __import__("profile_identity").assert_writable(r["person"])
    p = preview(dict(r, phase="ready"))
    if not p["accepted"]:
        raise ValueError(
            "No selected source has complete compatible inputs. Check source formats/builds and prerequisites."
        )
    with GUARD:
        if ACTIVE or any(x.poll() is None for x in suite_api.PROCESSES.values()):
            raise ValueError("Another job is running.")
        job = "sourcebatch_" + uuid.uuid4().hex
        folder = suite_api.job_path(p["person"], job)
        (folder / "Results").mkdir(parents=True)
        p.update(
            job=job,
            state="running",
            created=datetime.datetime.now().astimezone().isoformat(),
            completed=0,
            total=len(p["runs"]) + 1,
            log=[],
        )
        save(folder, p)
        ACTIVE = (p["person"], job)
    threading.Thread(target=worker, args=(folder, p), daemon=True).start()
    return {"person": p["person"], "job": job}


def save(folder, p):
    from profile_pipeline import atomic

    atomic(folder / "source-batch.json", p)
    atomic(
        folder / "inputs.json",
        {
            "person": p["person"],
            "task": "source_batch",
            "inputs": {"tool": p["task"], "runs": p["runs"]},
        },
    )
    atomic(
        folder / "status.json",
        {
            "id": p["job"],
            "person": p["person"],
            "task": "source_batch",
            "title": "Selected-source research · " + p["task"],
            "kind": "analysis",
            "status": "Running"
            if p["state"] == "running"
            else "Complete"
            if p["state"] == "completed"
            else "Eingaben erforderlich",
            "started": p["created"],
            "finished": None
            if p["state"] == "running"
            else datetime.datetime.now().astimezone().isoformat(),
            "progress": {
                "completed": p["completed"],
                "total": p["total"],
                "percent": round(100 * p["completed"] / p["total"], 1),
                "unit": "steps",
            },
        },
    )
    (folder / "auftrag.log").write_text("\n".join(p["log"][-150:]), encoding="utf-8")
    if p["state"] != "running":
        atomic(folder / "Results/source-batch-summary.json", p)


def worker(folder, p):
    global ACTIVE, OWNER
    OWNER = threading.get_ident()

    def log(s):
        p["log"].append(s)
        save(folder, p)

    try:
        import on_demand

        for run in p["runs"]:
            if (folder / "abbrechen.request").exists():
                p["state"] = "cancelled"
                break
            try:
                if not run["accepted"]:
                    run["status"] = "needs_input"
                    continue
                dep = on_demand.status(p["task"])
                if not dep["ready"]:
                    run.update(status="needs_input", dependencies=dep["requirements"])
                    continue
                log(
                    "Start "
                    + p["task"]
                    + " · "
                    + ", ".join(
                        a["provider"] + " " + a.get("declared_version", "")
                        for a in run["source_aliases"]
                    )
                )
                child = suite_api.start(
                    {"person": p["person"], "task": p["task"], "inputs": run["inputs"]}
                )
                run["job"] = child["job"]
                while True:
                    status = json.loads(
                        (
                            suite_api.job_path(p["person"], child["job"])
                            / "status.json"
                        ).read_text(encoding="utf-8")
                    )
                    if status["status"] not in ("Running", "Queued", "Preparing"):
                        break
                    if (folder / "abbrechen.request").exists():
                        (
                            suite_api.job_path(p["person"], child["job"])
                            / "abbrechen.request"
                        ).touch()
                    time.sleep(0.4)
                run["status"] = (
                    "completed" if status["status"] == "Complete" else "needs_attention"
                )
                log(run["status"])
            except Exception as e:
                run.update(status="needs_attention", error=str(e))
                log(str(e))
            finally:
                p["completed"] += 1
                save(folder, p)
        if p["state"] == "running":
            import research_synthesis

            research_synthesis.build(p["person"], folder / "Results/synthesis", log)
            p["completed"] += 1
            p["state"] = (
                "completed"
                if all(x.get("status") == "completed" for x in p["runs"])
                else "needs_attention"
            )
    except Exception as e:
        p.update(state="needs_attention", error=str(e))
        log(str(e))
    finally:
        save(folder, p)
        with GUARD:
            ACTIVE = None
            OWNER = None


def dispatch(action, r):
    if action == "groups":
        return groups(r["person"], r["task"])
    if action == "preview":
        return preview(r)
    if action == "run":
        return start(r)
    if action == "cancel":
        person = suite_api.checked_person(r["person"])
        job = r["job"]
        if not __import__("re").fullmatch("sourcebatch_[a-f0-9]{32}", job):
            raise ValueError("Invalid source batch ID")
        (suite_api.job_path(person, job) / "abbrechen.request").touch()
        return {"requested": True}
    raise ValueError("Unknown source batch command")
