import security_sql

"""Profile-owned file inventory and reviewed reversible edits. No arbitrary path deletion."""
from pathlib import Path
import contextlib, datetime, hashlib, json, os, re, secrets, sqlite3, uuid
import source_store, family, profile_documents, profile_identity
import security_paths

ACTIVE = {"Running", "Queued", "Preparing"}


def now():
    return profile_identity.now()


def root():
    return source_store.ROOT.resolve()


def bases(person):
    person = security_paths.identifier(person)
    return [
        root() / "Profiles" / person,
        root() / "DNA_Archiv/01_Originaldownloads" / person,
        root() / "DNA_Archiv/Reports" / person,
        root() / "Projects/Launcher" / person,
    ]


def trash(person):
    return security_paths.contained(
        root() / "DNA_Trash", security_paths.identifier(person)
    )


def schema(db):
    db.executescript("""CREATE TABLE IF NOT EXISTS file_tombstones(file_id TEXT PRIMARY KEY,deleted TEXT,operation TEXT);
    CREATE TABLE IF NOT EXISTS manager_names(id TEXT PRIMARY KEY,name TEXT,updated TEXT);
    CREATE TABLE IF NOT EXISTS manager_events(id TEXT PRIMARY KEY,kind TEXT,created TEXT,payload TEXT);
    CREATE TABLE IF NOT EXISTS tool_runs(id TEXT PRIMARY KEY,command TEXT,status TEXT,created TEXT,finished TEXT,request TEXT,sources TEXT,outputs TEXT);""")


def ensure(person):
    profile_identity.ensure(person)
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        db.commit()
    with family.connect() as db:
        profile_documents.schema(db)


def stat(path):
    p = security_paths.local_path(path)
    if not p.is_file() or p.is_symlink():
        return {"available": False, "bytes": 0, "mtime_ns": None, "file_created": ""}
    s = p.stat()
    return {
        "available": True,
        "bytes": s.st_size,
        "mtime_ns": s.st_mtime_ns,
        "file_created": datetime.datetime.fromtimestamp(
            getattr(s, "st_birthtime", s.st_ctime), datetime.timezone.utc
        ).isoformat(),
    }


def walk(folder):
    if not Path(folder).is_dir():
        return []
    base = Path(folder).absolute()
    if base.resolve() != base:
        return []
    files = []
    for current, dirs, names in os.walk(base, followlinks=False):
        dirs[:] = [
            name
            for name in dirs
            if not (Path(current) / name).is_symlink()
            and not (Path(current) / name).is_junction()
        ]
        for name in names:
            p = Path(current) / name
            if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(base):
                files.append(p)
    return files


def owned(path, person):
    p = Path(path)
    if p.is_symlink():
        return False
    return any(
        b.resolve() == b.absolute() and p.resolve().is_relative_to(b.resolve())
        for b in bases(person)
    )


def inventory(person):
    ensure(person)
    rows = []
    known = set()
    label = {}
    with contextlib.closing(source_store.connect(person)) as db:
        db.row_factory = sqlite3.Row
        label = dict(db.execute("SELECT id,name FROM manager_names"))
        runs = {r["id"]: dict(r) for r in db.execute("SELECT * FROM tool_runs")}

    def append(row):
        row.setdefault("provenance", "")
        row.setdefault("imported", "")
        row.setdefault("created", "")
        row.setdefault("status", "")
        row.setdefault("source_date", "")
        row.setdefault("provider", "")
        row.setdefault("build", "")
        row.setdefault("editable", True)
        row["custom_label"] = row["id"] in label
        row["name"] = label.get(row["id"], row["name"])
        rows.append(row)
        if row.get("path") and not row.get("directory"):
            known.add(str(Path(row["path"]).resolve()))

    for r in source_store.listing(person):
        append(
            {
                "id": "source:" + r["id"],
                "kind": "dataset",
                "name": r["original_name"],
                "path": r["path"],
                "source_id": r["id"],
                "sha256": r["sha256"],
                "provider": r["provider"],
                "format": source_store.classify(Path(r["path"]).name),
                "quality": r["qc_color"],
                "verified": r["qc_verified"],
                "points": r["qc_points"],
                "lifecycle": r["lifecycle"],
                "build": r["build"],
                "status": r["index_state"],
                "created": r.get("created", ""),
                "imported": r.get("created", ""),
                "provenance": r["provider"]
                + " · "
                + r["label"]
                + " · "
                + r["measurement"],
                "source_date": "Imported "
                + r.get("created", "")
                + " (measurement date not inferred)",
                **stat(r["path"]),
            }
        )
    for d in profile_documents.listing(person):
        append(
            {
                "id": "document:" + d["id"],
                "kind": d["kind"],
                "name": d["name"],
                "path": d["path"],
                "document_id": d["id"],
                "sha256": d["sha256"],
                "provider": d["provider"],
                "status": d["status"],
                "created": d["updated"],
                "imported": d["updated"],
                "source_date": d["report_date"],
                "provenance": d["notes"] or d["provider"],
                **stat(d["path"]),
            }
        )
    for sf in sorted((root() / "Projects/Launcher" / person).glob("*/status.json")):
        try:
            s = json.loads(sf.read_text(encoding="utf-8-sig"))
            req = (
                json.loads((sf.parent / "inputs.json").read_text(encoding="utf-8-sig"))
                if (sf.parent / "inputs.json").is_file()
                else json.loads(
                    (sf.parent / "check-request.json").read_text(encoding="utf-8-sig")
                )
                if (sf.parent / "check-request.json").is_file()
                else {}
            )
            files = walk(sf.parent)
            job = sf.parent.name
            outputs = walk(sf.parent / "Results")
            qc = []
            if s.get("task") == "inspection":
                for check in sf.parent.glob("*_inspection.json"):
                    if check.stat().st_size <= 4 * 1024**2:
                        item = json.loads(check.read_text(encoding="utf-8"))
                        qc.append(
                            {
                                "sha256": item.get("sha256"),
                                "checked": item.get("checked"),
                            }
                        )
            run = runs.get(job)
            status = s.get("status", "Unknown")
            if not run and s.get("status") not in ACTIVE:
                import execution_journal

                execution_journal.register(sf.parent)
            if run and run["status"] not in ("deleted", status):
                status = "Status conflict: " + status + " / " + run["status"]
            provenance = {
                "selected_inputs": req.get("input_manifest")
                or req.get("inputs", {})
                or req.get("files", []),
                "profile_snapshot": req.get("source_state", {}),
                "recorded_at": s.get("started", ""),
            }
            append(
                {
                    "id": "job:" + job,
                    "kind": "tool_start"
                    if s.get("kind") == "launch"
                    else "view"
                    if s.get("kind") == "view"
                    else "test",
                    "name": s.get("title", job),
                    "path": str(sf.parent),
                    "directory": True,
                    "job": job,
                    "task": s.get("task", ""),
                    "qc_evidence": qc,
                    "status": status,
                    "db_status": run["status"] if run else s.get("status", ""),
                    "recorded_status": s.get("status", ""),
                    "created": s.get("started", ""),
                    "finished": s.get("finished", ""),
                    "provenance": json.dumps(provenance, ensure_ascii=False)[:16000],
                    "source_date": s.get("started", ""),
                    "bytes": sum(p.stat().st_size for p in files),
                    "available": True,
                    "mtime_ns": sf.stat().st_mtime_ns,
                    "file_created": "",
                    "outputs": [
                        str(p.relative_to(sf.parent / "Results")) for p in outputs
                    ],
                    "editable": s.get("status") not in ACTIVE,
                }
            )
        except (OSError, ValueError, KeyError):
            continue
    for base in bases(person):
        for p in walk(base):
            if p.name.endswith(("-wal", "-shm")) or p.name in (
                "status.json",
                "inputs.json",
                "result-seal.json",
                "auftrag.log",
                "command.txt",
                "versionen.json",
                "startfehler.log",
                "ausfuehren.sh",
                "linux.pid",
            ):
                continue
            if str(p.resolve()) in known:
                continue
            if (
                p.is_relative_to(root() / "Projects/Launcher" / person)
                and "Results"
                not in p.relative_to(root() / "Projects/Launcher" / person).parts
            ):
                continue
            job = next(
                (
                    r
                    for r in rows
                    if r.get("directory")
                    and p.is_relative_to(Path(r["path"]) / "Results")
                ),
                None,
            )
            append(
                {
                    "id": "file:" + p.relative_to(root()).as_posix(),
                    "kind": "artifact" if job else "unregistered_file",
                    "name": p.name,
                    "path": str(p),
                    "job": job.get("job", "") if job else "",
                    "created": job.get("finished") or job.get("created", "")
                    if job
                    else "",
                    "provenance": job["provenance"]
                    if job
                    else "Not yet assigned to a registered dataset",
                    "source_date": job["source_date"] if job else "",
                    **stat(p),
                }
            )
    # Count physical files once, including metadata/indexes. Logical file sizes, not NTFS allocated blocks.
    unique = {}
    for base in bases(person) + [source_store.folder(person)]:
        for p in walk(base):
            s = p.stat()
            unique[(s.st_dev, s.st_ino) if s.st_ino else str(p.resolve())] = s.st_size
    for r in rows:
        if not r.get("directory") and r["available"]:
            p = Path(r["path"])
            s = p.stat()
            unique[(s.st_dev, s.st_ino) if s.st_ino else str(p.resolve())] = s.st_size
    trash_bytes = sum(p.stat().st_size for p in walk(trash(person)))
    operations = []
    for p in sorted(trash(person).glob("*/manifest.json"), reverse=True):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
            operations.append(
                {
                    "operation": p.parent.name,
                    "action": j["action"],
                    "created": j["created"],
                    "status": j["status"],
                    "names": [r["name"] for r in j.get("entries", [])],
                }
            )
        except (ValueError, OSError):
            pass
    return {
        "person": person,
        "entries": rows,
        "bytes": sum(unique.values()),
        "gb": round(sum(unique.values()) / 10**9, 4),
        "gib": round(sum(unique.values()) / 1024**3, 4),
        "file_count": len(unique),
        "trash_bytes": trash_bytes,
        "trash": operations[:200],
        "size_note": "Unique logical file bytes including profile databases; shared tools/references and separate backups excluded. Trash is shown separately.",
    }


def signature(data):
    value = [
        {
            k: r.get(k)
            for k in ("id", "path", "name", "bytes", "mtime_ns", "status", "sha256")
        }
        for r in data["entries"]
    ]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def busy(person, ignore=""):
    paths = list((root() / "Projects/Launcher" / person).glob("*/status.json")) + list(
        (root() / "DNA_Projects/ProfileTransfers").glob("*/status.json")
    )
    for p in paths:
        if p.parent.name == ignore:
            continue
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            if s.get("person") == person and s.get("status") in ACTIVE:
                raise ValueError(
                    "Wait for running/queued profile jobs before changing files: "
                    + p.parent.name
                )
        except (OSError, json.JSONDecodeError):
            continue


def validate_name(name):
    name = str(name).strip()
    if (
        not name
        or len(name) > 180
        or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
        or name.endswith((".", " "))
        or name in (".", "..")
        or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name)
    ):
        raise ValueError("Use a valid Windows file name, not a path")
    return name


def check_base(person, ids):
    data = inventory(person)
    indexed = {r["id"]: r for r in data["entries"]}
    if (
        not isinstance(ids, list)
        or not ids
        or len(ids) > 1000
        or len(set(ids)) != len(ids)
        or set(ids) - set(indexed)
    ):
        raise ValueError("Select 1–1000 current entries from this profile")
    return data, [indexed[id] for id in ids]


def foreign_refs(person):
    paths = set()
    with family.connect() as graph:
        people = [
            r[0] for r in graph.execute("SELECT id FROM people WHERE id!=?", (person,))
        ]
        profile_documents.schema(graph)
        paths.update(
            str(Path(r[0]).resolve())
            for r in graph.execute(
                "SELECT path FROM profile_documents WHERE person!=? AND status!='deleted'",
                (person,),
            )
        )
    for pid in people:
        path = source_store.folder(pid) / "sources.sqlite"
        if not path.is_file():
            continue
        with contextlib.closing(
            sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        ) as db:
            condition = (
                " AND NOT EXISTS(SELECT 1 FROM file_tombstones t WHERE t.file_id=f.id)"
                if db.execute(
                    "SELECT 1 FROM sqlite_master WHERE name='file_tombstones'"
                ).fetchone()
                else ""
            )
            paths.update(
                str((root() / r[0]).resolve())
                for r in db.execute(
                    "SELECT b.stored_rel FROM files f JOIN blobs b ON f.sha256=b.sha256 WHERE 1=1"
                    + condition
                )
            )
    return paths


def preview(person, action, ids, name="", replacement="", storage_mode="copy"):
    profile_identity.assert_writable(person)
    busy(person)
    data, entries = check_base(person, ids)
    if action not in ("delete", "rename", "replace"):
        raise ValueError("Unknown file operation")
    if any(not r["editable"] for r in entries):
        raise ValueError("A running entry cannot be edited")
    if action != "delete" and len(entries) != 1:
        raise ValueError("Rename or replace exactly one entry")
    if action in ("delete", "replace", "rename"):
        paired = {
            str(p.resolve())
            for r in entries
            for p in sidecars(r["path"])
            if not r.get("directory")
        }
        extras = [
            r
            for r in data["entries"]
            if not r.get("directory")
            and str(Path(r["path"]).resolve()) in paired
            and r["id"] not in ids
        ]
        ids = ids + [r["id"] for r in extras]
        entries = entries + extras
    if action == "delete":
        containers = [Path(r["path"]) for r in entries if r.get("directory")]
        extras = [
            r
            for r in data["entries"]
            if r["id"] not in ids
            and any(Path(r["path"]).is_relative_to(base) for base in containers)
        ]
        ids += [r["id"] for r in extras]
        entries += extras
    if action in ("delete", "replace"):
        docs = {r["document_id"]: r for r in data["entries"] if r.get("document_id")}
        docids = {r["document_id"] for r in entries if r.get("document_id")}
        changed = True
        while changed:
            changed = False
            for did, r in docs.items():
                try:
                    parent = json.loads(r.get("provenance") or "{}").get(
                        "source_document"
                    )
                except (ValueError, AttributeError):
                    parent = None
                if parent in docids and did not in docids:
                    docids.add(did)
                    changed = True
        processed = [
            base / did
            for base in (
                root() / "DNA_Archiv/Reports" / person / "Processed",
                source_store.profile_dir(person) / "Findings/Processed",
            )
            for did in docids
        ]
        extras = [
            r
            for r in data["entries"]
            if r["id"] not in ids
            and (
                r.get("document_id") in docids
                or any(Path(r["path"]).is_relative_to(folder) for folder in processed)
            )
        ]
        ids += [r["id"] for r in extras]
        entries += extras
    warnings = [
        "Changes are applied only after confirmation. Source provenance of previous analyses is retained; changed inputs do not inherit verification."
    ]
    if action == "delete":
        warnings.append(
            "Selected owned files move to profile trash. Shared/external files are retained. A deleted test stops being offered as a completed test; dependent results are marked for review. Trash still consumes SSD space."
        )
    if action == "rename":
        r = entries[0]
        name = str(name).strip()
        if (
            r.get("directory")
            or r["kind"] == "artifact"
            or r["kind"] == "analysis_output"
            and Path(r["path"]).is_relative_to(root() / "Projects/Launcher" / person)
        ):
            if not name or len(name) > 180 or any(ord(c) < 32 for c in name):
                raise ValueError("Use a display label of 1–180 characters")
        else:
            name = validate_name(name)
        if (
            not r.get("directory")
            and r["kind"] != "artifact"
            and str(Path(r["path"]).resolve()) in foreign_refs(person)
        ):
            raise ValueError(
                "Another profile references these file bytes. Rename the profile display record instead of moving a shared path"
            )
        if (
            r.get("directory")
            or r["kind"] == "artifact"
            or r["kind"] == "analysis_output"
            and Path(r["path"]).is_relative_to(root() / "Projects/Launcher" / person)
        ):
            warnings.append(
                "This is a tool-managed result: its display name is changed. Technical job IDs and output filenames remain stable for downstream tools."
            )
        elif not owned(r["path"], person):
            raise ValueError(
                "External files cannot be renamed; import them into this profile first"
            )
        else:
            p = Path(r["path"])
            suffix = next(
                (
                    x
                    for x in (
                        ".vcf.gz",
                        ".vcf.bgz",
                        ".fastq.gz",
                        ".fq.gz",
                        ".fasta.gz",
                        ".fa.gz",
                        ".txt.gz",
                    )
                    if p.name.lower().endswith(x)
                ),
                p.suffix,
            )
            if suffix and not name.lower().endswith(suffix.lower()):
                raise ValueError("Keep the full original extension: " + suffix)
            target = p.with_name(name)
            if target != p and target.exists():
                raise ValueError(
                    "The target name already exists; nothing will be overwritten"
                )
    replace_stat = None
    if action == "replace":
        r = entries[0]
        if r.get("directory"):
            raise ValueError(
                "Use Rerun to replace a test with a new execution; a job folder cannot be replaced by an uploaded file"
            )
        p = security_paths.input_file(replacement)
        if not p.is_file() or p.is_symlink() or p == Path(r["path"]).resolve():
            raise ValueError("Select another regular file")
        if storage_mode not in ("copy", "move"):
            raise ValueError("Choose copy or move")
        if any(
            p.is_relative_to(b.resolve())
            for b in (
                root() / "Profiles",
                root() / "DNA_Archiv/01_Originaldownloads",
                root() / "DNA_Archiv/Reports",
                root() / "Projects/Launcher",
            )
        ) and not owned(p, person):
            raise ValueError("Do not take another profile’s file")
        if r["kind"] == "artifact":
            raise ValueError(
                "Tool-generated artifacts can be exported, renamed for display or removed. Rerun the parent test to replace its output, or import a separate manual report."
            )
        replace_stat = stat(p)
        replacement = str(p)
        warnings.append(
            "A replacement is registered as a new unverified source/report. The previous entry moves to trash; previous test evidence stays traceable."
        )
    token = secrets.token_hex(32)
    plan = {
        "token": token,
        "person": person,
        "action": action,
        "ids": ids,
        "name": name,
        "replacement": replacement,
        "replacement_state": replace_stat,
        "storage_mode": storage_mode,
        "signature": signature(data),
        "created": now(),
        "entries": entries,
        "warnings": warnings,
    }
    folder = root() / "DNA_Software/UserData/Launcher/FileManagerChecks" / person
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (token + ".json")).write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return plan


def sidecars(path):
    p = Path(path)
    found = []
    for candidate in (
        [Path(str(p) + ext) for ext in (".tbi", ".csi", ".bai", ".crai")]
        + ([p.with_suffix(".bai")] if p.suffix == ".bam" else [])
        + ([p.with_suffix(".crai")] if p.suffix == ".cram" else [])
    ):
        if candidate.is_file() and not candidate.is_symlink():
            found.append(candidate)
    return list(dict.fromkeys(found))


def invalidate_sources(db, person, paths, job_ids=(), qc_evidence=()):
    # Never rewrite historical inputs to pretend a different source was used.
    paths = [Path(p).resolve() for p in paths]

    def used(value):
        if isinstance(value, dict):
            return any(used(v) for v in value.values())
        if isinstance(value, list):
            return any(used(v) for v in value)
        if isinstance(value, str) and (
            value.startswith(str(root())) or re.match(r"^[A-Za-z]:[\\/]", value)
        ):
            p = Path(value).resolve()
            return any(p == x or p.is_relative_to(x) for x in paths)
        return False

    has_source = any(
        used(str(root() / r[0])) for r in db.execute("SELECT stored_rel FROM blobs")
    )
    has_pref = False
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='preferred_sets'").fetchone():
        has_pref = any(
            used(json.loads(r[0]))
            for r in db.execute("SELECT payload FROM preferred_sets")
        )
    if has_source or has_pref:
        db.execute("DELETE FROM derived_profile")
        if has_pref:
            db.execute("DELETE FROM preferred_sets")
    if db.execute(
        "SELECT 1 FROM sqlite_master WHERE name='file_annotations'"
    ).fetchone():
        for fid, origin, lifecycle, payload in db.execute(
            "SELECT file_id,origin,lifecycle,payload FROM file_annotations"
        ).fetchall():
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            if used(data):
                db.execute(
                    "UPDATE file_annotations SET lifecycle=?,payload=? WHERE file_id=?",
                    (
                        "needs_review",
                        json.dumps(
                            {
                                "withdrawn_previous_assessment": data,
                                "reason": "Its source analysis was removed or relocated",
                            }
                        ),
                        fid,
                    ),
                )
    for sha, payload, checked in db.execute("SELECT * FROM inspections").fetchall():
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        if (
            used(data.get("check_folder", ""))
            or data.get("check_job") in job_ids
            or any(
                q.get("sha256") == sha and q.get("checked") == checked
                for q in qc_evidence
            )
        ):
            data.update(
                color="orange",
                verified=False,
                qc_supported_points=None,
                manual_review_required=True,
            )
            data.setdefault("issues", []).append(
                "The check supporting this assessment was removed; run a new quality check."
            )
            db.execute(
                "UPDATE inspections SET payload=? WHERE sha256=?",
                (json.dumps(data, ensure_ascii=False), sha),
            )
    states = []
    for sf in (root() / "Projects/Launcher" / person).glob("*/status.json"):
        if sf.parent.name in job_ids:
            continue
        try:
            request = json.loads(
                (sf.parent / "inputs.json").read_text(encoding="utf-8")
            )
            if (
                used(request)
                or any(p.is_relative_to(sf.parent / "Results") for p in paths)
                or request.get("inputs", {}).get("source_job") in job_ids
            ):
                states.append((sf, json.loads(sf.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            pass
    return states


def apply(person, token, ignore="", log=print):
    if not re.fullmatch("[a-f0-9]{64}", str(token)):
        raise ValueError("Invalid confirmation token")
    p = (
        root()
        / "DNA_Software/UserData/Launcher/FileManagerChecks"
        / person
        / (token + ".json")
    )
    plan = json.loads(p.read_text(encoding="utf-8"))
    if (
        plan["person"] != person
        or (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.datetime.fromisoformat(plan["created"])
        ).total_seconds()
        > 900
    ):
        raise ValueError("Review expired; preview again")
    with profile_identity.exclusive_restore(person):
        busy(person, ignore)
        other_refs = foreign_refs(person)
        data, entries = check_base(person, plan["ids"])
        if signature(data) != plan["signature"]:
            raise ValueError(
                "Profile files changed since preview. Nothing changed; preview again"
            )
        if (
            plan["replacement"]
            and stat(plan["replacement"]) != plan["replacement_state"]
        ):
            raise ValueError("Replacement file changed after preview")
        action = plan["action"]
        operation = (
            "files_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:10]
        )
        folder = trash(person) / operation
        if folder.resolve() != folder.absolute() or not folder.resolve().is_relative_to(
            root()
        ):
            raise ValueError("Unsafe trash folder")
        folder.mkdir(parents=True)
        manifest = {
            "id": operation,
            "person": person,
            "action": action,
            "created": now(),
            "status": "prepared",
            "entries": entries,
            "moves": [],
            "documents": [],
            "jobs": [],
            "deleted_sources": [],
            "warnings": plan["warnings"],
        }
        moved = []
        changed_json = []
        committed = False

        def save():
            target = folder / "manifest.json"
            temp = target.with_suffix(".tmp")
            temp.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temp.replace(target)

        save()

        def move(src, dest):
            src = Path(src)
            dest = Path(dest)
            if not owned(src, person):
                return
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise ValueError("Target already exists: " + dest.name)
            originals = walk(src) if src.is_dir() else [src]
            checks = [
                {"name": str(f.relative_to(src)) if src.is_dir() else "", **stat(f)}
                for f in originals
            ]
            os.rename(src, dest)
            moved.append((src, dest))
            manifest["moves"].append(
                {
                    "from": src.relative_to(root()).as_posix(),
                    "to": dest.relative_to(root()).as_posix(),
                    "checks": checks,
                }
            )
            save()

        def write_json(path, value):
            original = path.read_bytes()
            changed_json.append((path, original))
            temp = path.with_suffix(".manager-tmp")
            temp.write_text(
                json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temp.replace(path)

        replacement_result = None
        try:
            # Import first, then quarantine the old item. Failure never removes the old source.
            if action == "replace":
                r = entries[0]
                log(
                    "Verify and register replacement: " + Path(plan["replacement"]).name
                )
                if r["kind"] == "dataset" or r["kind"] == "unregistered_file":
                    replacement_result = source_store.import_batch(
                        person,
                        [plan["replacement"]],
                        "Manual replacement / provider unverified",
                        "Replacement for " + r["name"],
                        note="Manual replacement; previous source retained in trash. QC must be rerun.",
                        storage_mode=plan["storage_mode"],
                        log=log,
                    )
                    newrows = source_store.listing(person)
                    if any(
                        x["sha256"] == r.get("sha256")
                        for x in newrows
                        if x["id"] in replacement_result["ids"]
                    ):
                        with contextlib.closing(
                            source_store.connect(person)
                        ) as cleanup:
                            for fid in replacement_result["ids"]:
                                cleanup.execute(
                                    "DELETE FROM file_operations WHERE file_id=?",
                                    (fid,),
                                )
                                cleanup.execute("DELETE FROM files WHERE id=?", (fid,))
                            cleanup.execute(
                                "DELETE FROM batches WHERE id=?",
                                (replacement_result["batch_id"],),
                            )
                            cleanup.commit()
                        # Identical bytes require no deletion of the old source.
                        manifest.update(
                            status="no_change",
                            result="Identical source bytes already present; old entry retained",
                        )
                        save()
                        p.rename(p.with_suffix(".used"))
                        return manifest
                else:
                    if profile_documents.digest(plan["replacement"]) == r.get("sha256"):
                        manifest.update(
                            status="no_change",
                            result="Identical report bytes; previous entry retained",
                        )
                        save()
                        return manifest
                    replacement_result = profile_documents.index_file(
                        person,
                        plan["replacement"],
                        "Manual replacement / provider unverified",
                        kind="manual_replacement",
                        log=log,
                    )
                    replacement_path = Path(plan["replacement"])
                    if (
                        plan["storage_mode"] == "move"
                        and str(replacement_path)
                        not in {e["path"] for e in data["entries"]}
                        and not owned(replacement_path, person)
                    ):
                        saved = next(
                            d
                            for d in profile_documents.listing(person)
                            if d["id"] == replacement_result["id"]
                        )
                        if (
                            profile_documents.digest(replacement_path)
                            == saved["sha256"]
                        ):
                            replacement_path.unlink()
                    if replacement_result.get("id") == r.get("document_id"):
                        manifest.update(
                            status="no_change",
                            result="Identical report already present",
                        )
                        save()
                        return manifest
            with contextlib.closing(source_store.connect(person)) as db:
                schema(db)
                db.row_factory = sqlite3.Row
                db.execute("ATTACH DATABASE ? AS graph", (str(family.DB),))
                db.execute("BEGIN IMMEDIATE")
                evidence_hashes = {r["sha256"] for r in entries if r.get("sha256")}
                budget = 32 * 1024**2
                if action in ("delete", "replace"):
                    for entry in entries:
                        output_files = (
                            walk(Path(entry["path"]) / "Results")
                            if entry.get("directory")
                            else [Path(entry["path"])]
                        )
                        for file in output_files:
                            if (
                                file.is_file()
                                and file.suffix.lower()
                                in (
                                    ".txt",
                                    ".csv",
                                    ".tsv",
                                    ".kin0",
                                    ".kin",
                                    ".ibd",
                                    ".json",
                                )
                                and file.stat().st_size <= min(budget, 8 * 1024**2)
                            ):
                                raw = file.read_bytes()
                                budget -= len(raw)
                                evidence_hashes.add(hashlib.sha256(raw).hexdigest())
                                evidence_hashes.add(
                                    hashlib.sha256(
                                        raw.replace(b"\r\n", b"\n")
                                    ).hexdigest()
                                )
                selected = {e["id"] for e in entries}
                removed_jobs = {e["job"] for e in entries if e.get("directory")}
                paths = []
                if action in ("delete", "replace"):
                    db.execute(
                        "CREATE TABLE IF NOT EXISTS graph.withdrawn_evidence(sha256 TEXT PRIMARY KEY,reason TEXT,created TEXT)"
                    )
                    for sha in evidence_hashes:
                        db.execute(
                            "INSERT OR REPLACE INTO graph.withdrawn_evidence VALUES(?,?,?)",
                            (
                                sha,
                                "Source removed/replaced by profile file manager: "
                                + operation,
                                now(),
                            ),
                        )
                    for r in entries:
                        log("Quarantine: " + r["name"])
                        if r["id"].startswith("source:"):
                            db.execute(
                                "INSERT OR REPLACE INTO file_tombstones VALUES(?,?,?)",
                                (r["source_id"], now(), operation),
                            )
                            manifest["deleted_sources"].append(r["source_id"])
                        paths.append(Path(r["path"]))
                    # Reports derived from a deleted original or a deleted output are withdrawn as evidence.
                    docs = [
                        dict(r)
                        for r in db.execute(
                            "SELECT * FROM graph.profile_documents WHERE person=?",
                            (person,),
                        )
                    ]
                    selected_docs = {
                        r["document_id"] for r in entries if r.get("document_id")
                    }
                    expanded = True
                    while expanded:
                        expanded = False
                        for d in docs:
                            try:
                                parent = json.loads(d.get("notes") or "{}").get(
                                    "source_document"
                                )
                            except (ValueError, AttributeError):
                                parent = None
                            if parent in selected_docs and d["id"] not in selected_docs:
                                selected_docs.add(d["id"])
                                expanded = True
                    for d in docs:
                        path = Path(d["path"])
                        if d["id"] in selected_docs or any(
                            path == x or x.is_dir() and path.is_relative_to(x)
                            for x in paths
                        ):
                            selected_docs.add(d["id"])
                            manifest["documents"].append(
                                {"id": d["id"], "status": d["status"]}
                            )
                            db.execute(
                                "UPDATE graph.profile_documents SET status='deleted' WHERE id=? AND person=?",
                                (d["id"], person),
                            )
                    active_refs = {
                        str(Path(r["path"]).resolve())
                        for r in data["entries"]
                        if r["id"] not in selected
                        and not r.get("directory")
                        and not (r.get("document_id") in selected_docs)
                        and not r.get("job") in removed_jobs
                    } | other_refs
                    # One selected alias must not move bytes still used by another live record.
                    candidates = []
                    for r in entries:
                        source = Path(r["path"])
                        if r.get("directory"):
                            if any(
                                Path(path).is_relative_to(source)
                                for path in active_refs
                            ):
                                raise ValueError(
                                    "Selected job contains a file still registered elsewhere. Remove its dataset/report aliases first or include them in this selection."
                                )
                            candidates.append(source)
                        elif str(source.resolve()) not in active_refs:
                            candidates.extend(
                                [source]
                                + [
                                    sc
                                    for sc in sidecars(source)
                                    if str(sc.resolve()) not in active_refs
                                ]
                            )
                    candidates = sorted(set(candidates), key=lambda x: len(x.parts))
                    top = []
                    for source in candidates:
                        if any(source.is_relative_to(x) for x in top):
                            continue
                        if source.exists() and owned(source, person):
                            top.append(source)
                            move(source, folder / "files" / source.relative_to(root()))
                    for r in entries:
                        if r.get("directory"):
                            db.execute(
                                "UPDATE tool_runs SET status='deleted' WHERE id=?",
                                (r["job"],),
                            )
                    for sf, old in invalidate_sources(
                        db,
                        person,
                        paths,
                        removed_jobs,
                        [q for r in entries for q in r.get("qc_evidence", [])],
                    ):
                        manifest["jobs"].append(
                            {"path": sf.relative_to(root()).as_posix(), "status": old}
                        )
                        write_json(
                            sf,
                            dict(
                                old,
                                status="Inputs changed / review required",
                                manual_review={
                                    "operation": operation,
                                    "reason": "A used source/result was removed or replaced",
                                },
                            ),
                        )
                        db.execute(
                            "UPDATE tool_runs SET status='Inputs changed / review required' WHERE id=?",
                            (sf.parent.name,),
                        )
                        for doc in docs:
                            if (
                                doc["id"] not in selected_docs
                                and Path(doc["path"]).is_relative_to(
                                    sf.parent / "Results"
                                )
                                and doc["status"] == "indexed"
                            ):
                                if doc["id"] not in {
                                    d["id"] for d in manifest["documents"]
                                }:
                                    manifest["documents"].append(
                                        {"id": doc["id"], "status": doc["status"]}
                                    )
                                db.execute(
                                    "UPDATE graph.profile_documents SET status='stale_analysis' WHERE id=?",
                                    (doc["id"],),
                                )
                elif action == "rename":
                    r = entries[0]
                    name = plan["name"]
                    if (
                        r.get("directory")
                        or r["kind"] == "artifact"
                        or r["kind"] == "analysis_output"
                        and Path(r["path"]).is_relative_to(
                            root() / "Projects/Launcher" / person
                        )
                    ):
                        db.execute(
                            "INSERT OR REPLACE INTO manager_names VALUES(?,?,?)",
                            (r["id"], name, now()),
                        )
                        if r.get("document_id"):
                            db.execute(
                                "UPDATE graph.profile_documents SET name=? WHERE id=? AND person=?",
                                (name, r["document_id"], person),
                            )
                        if r.get("directory"):
                            sf = Path(r["path"]) / "status.json"
                            old_state = json.loads(sf.read_text(encoding="utf-8"))
                            manifest["jobs"].append(
                                {
                                    "path": sf.relative_to(root()).as_posix(),
                                    "status": old_state,
                                }
                            )
                            write_json(
                                sf, dict(old_state, title=name, custom_title=True)
                            )
                    else:
                        old = Path(r["path"])
                        new = old.with_name(name)
                        move(old, new)
                        maps = {str(old): str(new)}
                        # Sidecars stay paired with the data file and retain their suffix convention.
                        for sc in sidecars(old):
                            dest = (
                                Path(str(new) + str(sc)[len(str(old)) :])
                                if str(sc).startswith(str(old))
                                else new.with_suffix(sc.suffix)
                            )
                            move(sc, dest)
                            maps[str(sc)] = str(dest)
                        for a, b in maps.items():
                            db.execute(
                                "UPDATE blobs SET stored_rel=? WHERE replace(stored_rel, char(92), '/')=?",
                                (
                                    Path(b).relative_to(root()).as_posix(),
                                    Path(a).relative_to(root()).as_posix(),
                                ),
                            )
                            db.execute(
                                "UPDATE files SET original_name=? WHERE sha256 IN (SELECT sha256 FROM blobs WHERE stored_rel=?)",
                                (Path(b).name, Path(b).relative_to(root()).as_posix()),
                            )
                            db.execute(
                                "UPDATE graph.profile_documents SET path=?,name=? WHERE person=? AND path=?",
                                (b, Path(b).name, person, a),
                            )
                            if db.execute(
                                "SELECT 1 FROM sqlite_master WHERE name='file_operations'"
                            ).fetchone():
                                db.execute(
                                    "UPDATE file_operations SET target=? WHERE target=?",
                                    (b, a),
                                )
                        # Source fingerprints retain the original analysis provenance; expose stale-input state.
                        for sf, old_state in invalidate_sources(db, person, [old]):
                            manifest["jobs"].append(
                                {
                                    "path": sf.relative_to(root()).as_posix(),
                                    "status": old_state,
                                }
                            )
                            write_json(
                                sf,
                                dict(
                                    old_state,
                                    status="Inputs relocated / review required",
                                    manual_review={
                                        "operation": operation,
                                        "relocations": maps,
                                    },
                                ),
                            )
                            db.execute(
                                "UPDATE tool_runs SET status='Inputs relocated / review required' WHERE id=?",
                                (sf.parent.name,),
                            )
                manifest["replacement"] = replacement_result
                manifest["status"] = "applied"
                save()
                db.execute(
                    "INSERT INTO manager_events VALUES(?,?,?,?)",
                    (
                        operation,
                        action,
                        now(),
                        json.dumps(manifest, ensure_ascii=False),
                    ),
                )
                db.execute(
                    "UPDATE graph.profile_identities SET updated=?,revision=revision+1 WHERE person=?",
                    (now(), person),
                )
                db.commit()
                committed = True
            try:
                p.rename(p.with_suffix(".used"))
            except OSError:
                pass
            log("Profile file operation complete")
            return {
                "operation": operation,
                "status": "applied",
                "entries": len(entries),
                "replacement": replacement_result,
            }
        except BaseException as error:
            if committed:
                manifest.update(status="applied", postcommit_warning=str(error))
                save()
                return {
                    "operation": operation,
                    "status": "applied",
                    "warning": str(error),
                }
            for path, raw in reversed(changed_json):
                path.write_bytes(raw)
            for src, dest in reversed(moved):
                if dest.exists() and not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(dest, src)
            manifest.update(
                status="replacement_imported_old_retained"
                if replacement_result
                else "rolled_back",
                replacement=replacement_result,
                error=str(error),
            )
            save()
            raise


def restore(person, operation, ignore="", log=print):
    if not re.fullmatch("files_[A-Za-z0-9_]+", operation):
        raise ValueError("Invalid trash operation")
    path = trash(person) / operation / "manifest.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    if (
        m["person"] != person
        or m["status"] != "applied"
        or m["action"] not in ("delete", "replace")
    ):
        raise ValueError("This operation cannot be restored")
    with profile_identity.exclusive_restore(person):
        busy(person, ignore)
        moved = []
        try:
            for row in m["moves"]:
                dest = (root() / row["from"]).resolve()
                src = (root() / row["to"]).resolve()
                if (
                    not owned(dest, person)
                    or not src.is_relative_to((trash(person) / operation).resolve())
                    or not src.exists()
                    or src.is_symlink()
                    or dest.exists()
                ):
                    raise ValueError(
                        "A restore path is missing, occupied or unsafe; nothing overwritten"
                    )
                for check in row.get("checks", []):
                    file = (src / check["name"]).resolve() if check["name"] else src
                    if check["name"] and not file.is_relative_to(src.resolve()):
                        raise ValueError("Invalid trash file path")
                    current = stat(file)
                    if (
                        not current["available"]
                        or current["bytes"] != check["bytes"]
                        or current["mtime_ns"] != check["mtime_ns"]
                    ):
                        raise ValueError("Trash payload changed; restore blocked")
            for entry in m["entries"]:
                if entry.get("sha256"):
                    original = Path(entry["path"])
                    mapped = next(
                        (
                            row
                            for row in m["moves"]
                            if original == root() / row["from"]
                            or original.is_relative_to(root() / row["from"])
                        ),
                        None,
                    )
                    if mapped:
                        saved = (
                            root()
                            / mapped["to"]
                            / original.relative_to(root() / mapped["from"])
                            if original != root() / mapped["from"]
                            else root() / mapped["to"]
                        )
                        if profile_documents.digest(saved) != entry["sha256"]:
                            raise ValueError("Trash source checksum mismatch")
            with contextlib.closing(source_store.connect(person)) as db:
                db.execute("ATTACH DATABASE ? AS graph", (str(family.DB),))
                db.execute("BEGIN IMMEDIATE")
                for row in m["moves"]:
                    dest = root() / row["from"]
                    src = root() / row["to"]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(src, dest)
                    moved.append((src, dest))
                for fid in m["deleted_sources"]:
                    db.execute(
                        "DELETE FROM file_tombstones WHERE file_id=? AND operation=?",
                        (fid, operation),
                    )
                for doc in m["documents"]:
                    db.execute(
                        "UPDATE graph.profile_documents SET status=? WHERE id=? AND person=?",
                        (doc["status"], doc["id"], person),
                    )
                for entry in m["entries"]:
                    if entry.get("directory"):
                        db.execute(
                            "UPDATE tool_runs SET status=? WHERE id=?",
                            (entry.get("db_status") or entry["status"], entry["job"]),
                        )
                db.execute(
                    "INSERT INTO manager_events VALUES(?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        "restore",
                        now(),
                        json.dumps({"operation": operation}),
                    ),
                )
                db.commit()
            m.update(status="restored", restored=now())
            path.write_text(
                json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            profile_identity.touch(person)
            return {"status": "restored", "operation": operation}
        except BaseException:
            for src, dest in reversed(moved):
                if dest.exists() and not src.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(dest, src)
            raise


def export_paths(person, ids):
    _, entries = check_base(person, ids)
    paths = set()
    for r in entries:
        if r.get("directory"):
            paths.update(str(p) for p in walk(Path(r["path"]) / "Results"))
        elif r["available"]:
            paths.add(r["path"])
    if not paths:
        raise ValueError("No available result/source files selected")
    return {
        "person": person,
        "files": sorted(paths),
        "bytes": sum(Path(p).stat().st_size for p in paths),
    }


def clean_export_database(path):
    # A profile backup includes active sources only; quarantined payload lives outside it.
    with contextlib.closing(sqlite3.connect(path)) as db, db:
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='file_tombstones'"
        ).fetchone():
            return
        for table in ("calls", "file_annotations", "file_operations"):
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE name=?", (table,)
            ).fetchone():
                db.execute(
                    "DELETE FROM "
                    + security_sql.identifier(table)
                    + " WHERE file_id IN (SELECT file_id FROM file_tombstones)"
                )
        db.execute(
            "DELETE FROM files WHERE id IN (SELECT file_id FROM file_tombstones)"
        )
        db.execute("DELETE FROM blobs WHERE sha256 NOT IN (SELECT sha256 FROM files)")
        db.execute(
            "DELETE FROM inspections WHERE sha256 NOT IN (SELECT sha256 FROM blobs)"
        )
        db.execute("DELETE FROM file_tombstones")
