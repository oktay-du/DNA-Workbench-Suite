"""Persist local tool executions even when they produce JSON/tables instead of reports."""

from pathlib import Path
import contextlib, datetime, hashlib, json, uuid
import family, source_store, profile_identity


def source_state(people, include_graph=False):
    result = []
    with family.connect() as graph:
        ids = {r[0] for r in graph.execute("SELECT id FROM people")}
        links = [
            list(r) for r in graph.execute("SELECT * FROM links ORDER BY a,b,kind")
        ]
        bindings = dict(graph.execute("SELECT person,source_person FROM bindings"))
        trees = (
            [
                list(r)
                for r in graph.execute(
                    "SELECT id,sha256 FROM research_gedcoms ORDER BY id"
                )
            ]
            if graph.execute(
                "SELECT 1 FROM sqlite_master WHERE name='research_gedcoms'"
            ).fetchone()
            else []
        )
    for person in dict.fromkeys(people):
        if person not in ids:
            continue
        source = bindings.get(person, person)
        files = []
        for r in source_store.listing(source):
            path = Path(r["path"])
            s = path.stat() if path.is_file() else None
            files.append(
                {
                    k: r.get(k)
                    for k in (
                        "id",
                        "sha256",
                        "provider",
                        "build",
                        "measurement",
                        "qc_color",
                        "qc_verified",
                        "index_state",
                        "call_count",
                        "lifecycle",
                        "qc_review_required",
                    )
                }
                | {
                    "path": r["path"],
                    "bytes": s.st_size if s else None,
                    "mtime_ns": s.st_mtime_ns if s else None,
                }
            )
        best = []
        with contextlib.closing(source_store.connect(source)) as db:
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='preferred_sets'"
            ).fetchone():
                for build, payload, updated in db.execute(
                    "SELECT build,payload,updated FROM preferred_sets"
                ):
                    p = json.loads(payload)
                    best.append(
                        {
                            "build": build,
                            "created": p.get("created", updated),
                            "folder": p.get("folder"),
                            "sources": p.get("sources", []),
                        }
                    )
        result.append(
            {
                "person": person,
                "source_profile": source,
                "profile_uuid": profile_identity.ensure(person)["uuid"],
                "available_sources": files,
                "profile_best_at_start": best,
            }
        )
    return {
        "profiles": result,
        "documented_links": links if include_graph else [],
        "gedcom_sources": trees if include_graph else [],
        "note": "Available source snapshot and profile Best Selection at execution start. Explicit input paths/positions are recorded separately; availability is not proof a tool used every source.",
    }


def register(folder):
    folder = Path(folder).resolve()
    base = (source_store.ROOT / "Projects/Launcher").resolve()
    if not folder.is_relative_to(base):
        return
    try:
        s = json.loads((folder / "status.json").read_text(encoding="utf-8-sig"))
        r = json.loads((folder / "inputs.json").read_text(encoding="utf-8-sig"))
        person = s["person"]
        if folder.parent.name != person:
            return
        profile_identity.assert_writable(person)
        from profile_files import schema

        with contextlib.closing(source_store.connect(person)) as db:
            schema(db)
            db.execute(
                "INSERT OR REPLACE INTO tool_runs VALUES(?,?,?,?,?,?,?,?)",
                (
                    folder.name,
                    r.get("command") or s.get("task", ""),
                    s["status"],
                    s.get("started", ""),
                    s.get("finished", ""),
                    json.dumps(r.get("inputs", {}), ensure_ascii=False),
                    json.dumps(
                        r.get("source_state") or r.get("input_manifest") or {},
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "files": s.get("outputs", []),
                            "research_report": s.get("research_report", {}),
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            db.commit()
    except (OSError, ValueError, KeyError):
        return


def execute(command, args, compute):
    # Legacy isolated tests may intentionally patch only one half of the workspace.
    if family.ROOT.resolve() != source_store.ROOT.resolve():
        return compute(args)
    with family.connect() as db:
        ids = {r[0] for r in db.execute("SELECT id FROM people")}
    participants = [
        args.get(k)
        for k in ("person", "a", "b", "child", "focus")
        if args.get(k) in ids
    ]
    participants += [p for p in args.get("people", []) if p in ids]
    owner = (
        args.get("person")
        if args.get("person") in ids
        else next(iter(participants), None)
    )
    if not owner:
        return compute(args)
    profile_identity.assert_writable(owner)
    if command == "research.raw-matrix" and not args.get("people"):
        participants = list(ids)
    if command == "inheritance.calculate":
        for role in ("mother", "father"):
            participants += family.lineage(owner, role)[1:]
    snapshot = source_state(
        participants,
        command in ("research.mrca", "research.gedcom-export", "inheritance.calculate"),
    )
    inputs = dict(args)
    force = inputs.pop("rerun", False)
    key = hashlib.sha256(
        json.dumps(
            {"command": command, "inputs": inputs, "snapshot": snapshot},
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    from profile_files import schema

    with contextlib.closing(source_store.connect(owner)) as db:
        schema(db)
        if not force:
            for id, sources in db.execute(
                "SELECT id,sources FROM tool_runs WHERE command=? AND status='Complete' ORDER BY finished DESC",
                (command,),
            ):
                try:
                    state = json.loads(sources)
                    p = (
                        source_store.ROOT
                        / "Projects/Launcher"
                        / owner
                        / id
                        / "Results/tool-result.json"
                    )
                    if (
                        state.get("execution_key") == key
                        and p.is_file()
                        and hashlib.sha256(p.read_bytes()).hexdigest()
                        == state.get("result_sha256")
                    ):
                        return json.loads(p.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    pass
    job = (
        "local_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )
    folder = source_store.ROOT / "Projects/Launcher" / owner / job
    out = folder / "Results"
    out.mkdir(parents=True)
    snapshot["execution_key"] = key
    request = {
        "task": command.replace(".", "_"),
        "command": command,
        "person": owner,
        "inputs": inputs,
        "source_state": snapshot,
    }
    status = {
        "id": job,
        "job": job,
        "person": owner,
        "task": request["task"],
        "title": command,
        "kind": "analysis",
        "status": "Running",
        "started": profile_identity.now(),
        "output": str(out),
    }

    def save():
        (folder / "inputs.json").write_text(
            json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (folder / "status.json").write_text(
            json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        register(folder)

    save()
    try:
        result = compute(args)
        raw = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        (out / "tool-result.json").write_bytes(raw)
        snapshot["result_sha256"] = hashlib.sha256(raw).hexdigest()
        status.update(
            status="Complete",
            finished=profile_identity.now(),
            outputs=["tool-result.json"],
        )
        save()
        try:
            import analysis_reports

            status["research_report"] = analysis_reports.publish(
                folder, owner, command, command
            )
        except Exception as error:
            status["research_report"] = {
                "status": "report_pending",
                "error": str(error),
            }
        status["outputs"] = [
            str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()
        ]
        save()
        return result
    except Exception as error:
        status.update(
            status="Failed", error=str(error), finished=profile_identity.now()
        )
        save()
        raise


def record_view(args):
    """Record a view of saved evidence, separately from a newly completed analysis."""
    import matching_features

    person = args.get("person")
    feature = args.get("feature")
    job = args.get("job", "")
    if feature not in {r["id"] for r in matching_features.FEATURES}:
        raise ValueError("Unknown result view")
    if not isinstance(job, str) or not __import__("re").fullmatch(
        "[A-Za-z0-9_-]+", job
    ):
        raise ValueError("Invalid source job")
    profile_identity.ensure(person)
    profile_identity.assert_writable(person)
    source = source_store.ROOT / "Projects/Launcher" / person / job
    status = json.loads((source / "status.json").read_text(encoding="utf-8"))
    if status.get("person") != person or status.get("status") != "Complete":
        raise ValueError("Select a completed result belonging to this profile")
    command = "research.view." + feature
    from profile_files import schema

    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        for id, request in db.execute(
            "SELECT id,request FROM tool_runs WHERE command=? AND status='Viewed saved result'",
            (command,),
        ):
            if (
                json.loads(request).get("source_job") == job
                and (source.parent / id / "status.json").is_file()
            ):
                return {"job": id, "existing": True}
    id = (
        "view_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )
    folder = source.parent / id
    out = folder / "Results"
    out.mkdir(parents=True)
    inputs = {"feature": feature, "source_job": job}
    r = {
        "person": person,
        "task": command,
        "command": command,
        "inputs": inputs,
        "source_state": {
            "person": person,
            "source_job": job,
            "completed": status.get("finished"),
            "input_reference": str(source / "inputs.json"),
        },
    }
    feature_row = next(r for r in matching_features.FEATURES if r["id"] == feature)
    s = {
        "id": id,
        "job": id,
        "person": person,
        "task": command,
        "title": feature_row["title"],
        "kind": "view",
        "status": "Viewed saved result",
        "started": profile_identity.now(),
        "finished": profile_identity.now(),
        "outputs": ["view-source.json"],
    }
    (folder / "inputs.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (folder / "status.json").write_text(
        json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "view-source.json").write_text(
        json.dumps(
            {
                "feature": feature,
                "source_job": job,
                "source_outputs": [
                    str(p.relative_to(source / "Results"))
                    for p in (source / "Results").rglob("*")
                    if p.is_file()
                ],
                "note": "Viewed existing evidence; no new genetic calculation or clinical verification.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    register(folder)
    return {"job": id, "existing": False}
