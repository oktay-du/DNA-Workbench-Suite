"""Exact, selection-scoped reuse of completed analyses. Never runs tools on lookup."""

from pathlib import Path
import hashlib, json, stat
import security_paths

# Imports, activation, exports and service launches are actions, never cached tests.
ACTIONS = {
    "import",
    "archive_index",
    "variant_index",
    "profile_activate",
    "profile_refresh",
    "export",
    "report",
}


def eligible(task):
    return task.get("kind") == "analysis" and task["id"] not in ACTIONS


def fingerprint(root, person, task, values):
    files = []
    complete = True

    def file(p, field):
        nonlocal complete
        p = security_paths.local_path(p)
        try:
            s = p.stat()
            files.append(
                {
                    "field": field,
                    "path": str(p),
                    "bytes": s.st_size,
                    "mtime_ns": s.st_mtime_ns,
                }
            )
        except OSError:
            complete = False
            files.append({"field": field, "path": str(p), "missing": True})

    for f in task.get("fields", []):
        if f["kind"] not in ("file", "folder"):
            continue
        value = values.get(f["key"])
        paths = value if isinstance(value, list) else [value]
        for p in paths:
            if not p:
                continue
            if f["kind"] == "file":
                file(p, f["key"])
            else:
                folder = security_paths.local_path(p)
                if not folder.is_dir():
                    complete = False
                    file(p, f["key"])
                    continue
                # Metadata inventory includes reference panels and every directory input.
                count = 0
                for item in sorted(folder.rglob("*")):
                    if item.is_symlink():
                        complete = False
                        continue
                    if item.is_file():
                        count += 1
                        if count > 20000:
                            complete = False
                            break
                        file(item, f["key"])
    # Workflows with implicit profile inputs need the actual source state, not name/age.
    if task["id"] in (
        "profile_analyze",
        "profile_generate",
        "best_dataset",
        "research_synthesis",
        "avatar_pack",
        "storybook",
    ):
        import source_store

        for row in source_store.listing(person):
            if row.get("origin") != "own_generated":
                file(row["path"], "profile_source")
    context = None
    if task["id"] == "best_dataset":
        import best_assets, source_store

        context = {
            "assets": best_assets.snapshot(person)["assets"],
            "metadata": [
                {
                    k: r.get(k)
                    for k in (
                        "id",
                        "sha256",
                        "declared_version",
                        "measurement",
                        "qc_color",
                        "versions",
                    )
                }
                for r in source_store.listing(person)
                if r.get("origin") != "own_generated"
            ],
        }
    if task["id"] == "research_synthesis":
        import profile_documents, visual_store, person_profile

        context = {
            "facts": profile_documents.facts(person),
            "profile": {
                k: v
                for k, v in person_profile.read(person).items()
                if k in ("name", "residence", "birth_date")
            },
            "visual": [r for r in visual_store.listing() if r["person"] == person],
            "documents": [
                {k: r.get(k) for k in ("id", "sha256", "status", "updated")}
                for r in profile_documents.listing(person)
                if r["kind"] != "calculated_research"
                and "research_synthesis" not in r.get("provider", "")
            ],
        }
    if task["id"] == "storybook":
        import visual_store, person_profile, workflows

        context = {
            "ancestry": [r for r in visual_store.listing() if r["person"] == person],
            "profile": {
                k: v
                for k, v in person_profile.read(person).items()
                if k in ("name", "residence", "birth_date")
            },
            "inheritance": workflows.inheritance_latest(person),
            "artwork": __import__("story_art").fingerprint(person),
        }
    data = {
        "context": context,
        "schema": 1,
        "person": person,
        "task": task["id"],
        "inputs": values,
        "files": files,
        "recipe": hashlib.sha256(
            json.dumps(task, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
    }
    return {
        "key": hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        "complete": complete,
        "state": data,
    }


def outputs_unchanged(folder, expected):
    """Resolve and stat each sealed artifact once; reject links, escapes and edits."""
    if not expected:
        return False
    for name, item in expected.items():
        path = security_paths.contained(folder / "Results", name.replace("\\", "/"))
        try:
            metadata = path.stat()
        except OSError:
            return False
        if not stat.S_ISREG(metadata.st_mode) or (
            metadata.st_size,
            metadata.st_mtime_ns,
        ) != (item["bytes"], item["mtime_ns"]):
            return False
    return True


def lookup(root, person, task, values, history):
    current = fingerprint(root, person, task, values)
    result = {
        "key": current["key"],
        "complete": current["complete"],
        "previous": None,
        "status": "first_run",
        "verified": False,
    }
    if task["id"] == "profile_analyze":
        import source_store

        if not source_store.listing(person):
            result.update(status="no_imported_sources", complete=False)
            return result
    if not eligible(task):
        result["status"] = "action"
        return result
    from workflow_sources import result_files

    known = {j["job"]: j for j in history}
    for path in security_paths.profile_jobs(root, person).glob("*/status.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
            if row.get("task") == task["id"]:
                known.setdefault(path.parent.name, dict(row, job=path.parent.name))
        except (ValueError, OSError):
            pass
    history = list(known.values())
    for job in sorted(
        history,
        key=lambda j: str(j.get("finished") or j.get("started") or ""),
        reverse=True,
    ):
        if job.get("task") != task["id"] or job.get("status") != "Complete":
            continue
        folder = security_paths.job(root, person, job["job"])
        try:
            req = json.loads((folder / "inputs.json").read_text(encoding="utf-8-sig"))
            saved = req.get("result_identity")
            if (
                not saved
                or not saved.get("complete")
                or saved["key"] != current["key"]
                or not current["complete"]
            ):
                continue
            # Restat original inputs; incomplete or modified output sets are not reusable.
            if fingerprint(root, person, task, req["inputs"])["key"] != saved["key"]:
                continue
            seal = json.loads((folder / "result-seal.json").read_text(encoding="utf-8"))
            outputs = result_files(root, person, job["job"])
            expected = {x["name"]: x for x in seal["files"]}
            if not outputs_unchanged(folder, expected):
                continue
        except (OSError, ValueError, KeyError, TypeError):
            continue
        result.update(
            previous=dict(job, artifacts=outputs), status="completed", verified=True
        )
        return result
    return result


def seal(folder):
    folder = Path(folder)
    rows = []
    for p in sorted((folder / "Results").rglob("*")):
        if p.is_file() and not p.is_symlink():
            s = p.stat()
            rows.append(
                {
                    "name": str(p.relative_to(folder / "Results")),
                    "bytes": s.st_size,
                    "mtime_ns": s.st_mtime_ns,
                }
            )
    target = folder / "result-seal.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps({"schema": 1, "files": rows}), encoding="utf-8")
    temp.replace(target)
