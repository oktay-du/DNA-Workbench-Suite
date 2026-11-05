import security_sql

"""Persist local comparison evidence by exact participant, kit, filter and source state."""
from pathlib import Path
import hashlib, json, datetime, uuid
import family, source_store


def key(args):
    import matching

    args = {k: v for k, v in args.items() if k != "rerun"}
    with family.connect() as db:
        matching.init(db)
        tables = {}
        for table in (
            "research_segments",
            "research_roh",
            "links",
            "bindings",
            "kinship_evidence",
            "withdrawn_evidence",
        ):
            tables[table] = []
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone():
                tables[table] = [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM "
                        + security_sql.identifier(table)
                        + " ORDER BY rowid"
                    )
                ]
    sources = []
    for person in matching.people():
        pid = matching.family_verification.source_person(person["id"])
        if not pid:
            continue
        for row in source_store.listing(pid):
            p = Path(row["path"])
            s = p.stat() if p.is_file() else None
            sources.append(
                {
                    "person": person["id"],
                    "source": pid,
                    "id": row.get("id"),
                    "hash": row["sha256"],
                    "build": row.get("build"),
                    "bytes": s.st_size if s else None,
                    "mtime": s.st_mtime_ns if s else None,
                }
            )
    data = {"schema": 1, "selection": args, "sources": sources, "evidence": tables}
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def saved(args):
    pid = args.get("a", "")
    import matching

    matching.person(pid)
    stamp = key(args)
    base = source_store.ROOT / "Projects/Launcher" / pid
    for p in sorted(base.glob("matching_*/inputs.json"), reverse=True):
        try:
            req = json.loads(p.read_text(encoding="utf-8"))
            status = json.loads((p.parent / "status.json").read_text(encoding="utf-8"))
            result = p.parent / "Results/comparison.json"
            if (
                req.get("comparison_key") != stamp
                or status.get("status") != "Complete"
                or not result.is_file()
            ):
                continue
            if hashlib.sha256(result.read_bytes()).hexdigest() != status.get(
                "result_sha256"
            ):
                continue
            data = json.loads(result.read_text(encoding="utf-8"))
            data["saved_result"] = {
                "job": p.parent.name,
                "person": pid,
                "completed": status["finished"],
                "reused": True,
                "pdf": (p.parent / "Results/local-analysis-report.pdf").is_file(),
            }
            return data
        except (OSError, ValueError, KeyError):
            continue
    return None


def run(args):
    import matching, profile_identity

    if not args.get("rerun"):
        prior = saved(args)
        if prior is not None:
            return prior
    pid = matching.person(args.get("a"))
    profile_identity.assert_writable(pid)
    stamp = key(args)
    result = matching.compute_analysis(args)
    if key(args) != stamp:
        raise ValueError(
            "Comparison inputs changed during the run; retry with a stable selection"
        )
    job = (
        "matching_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )
    folder = source_store.ROOT / "Projects/Launcher" / pid / job
    out = folder / "Results"
    out.mkdir(parents=True)
    request = {
        "task": "matching_compare",
        "person": pid,
        "inputs": {k: v for k, v in args.items() if k != "rerun"},
        "comparison_key": stamp,
    }
    (folder / "inputs.json").write_text(json.dumps(request), encoding="utf-8")
    raw = json.dumps(result, ensure_ascii=False, indent=2)
    (out / "comparison.json").write_text(raw, encoding="utf-8")
    status = {
        "id": job,
        "job": job,
        "task": "matching_compare",
        "title": "Local DNA comparison",
        "kind": "analysis",
        "person": pid,
        "status": "Complete",
        "started": datetime.datetime.now().astimezone().isoformat(),
        "finished": datetime.datetime.now().astimezone().isoformat(),
        "result_sha256": hashlib.sha256(
            (out / "comparison.json").read_bytes()
        ).hexdigest(),
    }
    (folder / "status.json").write_text(json.dumps(status), encoding="utf-8")
    try:
        import analysis_reports

        status["research_report"] = analysis_reports.publish(
            folder, pid, "matching_compare", "Local DNA comparison"
        )
    except Exception as error:
        status["research_report"] = {"status": "report_pending", "error": str(error)}
    (folder / "status.json").write_text(json.dumps(status), encoding="utf-8")
    import execution_journal

    execution_journal.register(folder)
    result["saved_result"] = {
        "job": job,
        "person": pid,
        "completed": status["finished"],
        "reused": False,
        "pdf": (out / "local-analysis-report.pdf").is_file(),
    }
    return result
