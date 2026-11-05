import security_sql, security_paths

"""Checksummed profile folders, explicit conflict review and source-preserving restore."""
from pathlib import Path, PurePosixPath
import sys, os, uuid, hashlib, sqlite3, shutil, secrets, datetime, subprocess, contextlib
import portable_json as json
import family, source_store, person_profile, profile_identity, profile_documents

ROOT = source_store.ROOT
APP = Path(__file__).parent
TABLES = (
    "batches",
    "blobs",
    "files",
    "calls",
    "inspections",
    "derived_profile",
    "file_annotations",
    "preferred_sets",
    "file_operations",
    "manager_names",
    "manager_events",
    "tool_runs",
    "file_tombstones",
    "workflow_inputs",
    "inheritance_evidence",
    "artwork_slots",
    "archive_payloads",
    "source_metadata",
    "preferred_asset_sets",
)


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def valid_rel(name):
    p = PurePosixPath(str(name))
    if (
        not str(name)
        or p.is_absolute()
        or ".." in p.parts
        or "\\" in str(name)
        or ":" in str(name)
        or str(p) != str(name)
    ):
        raise ValueError("Invalid backup relative path")
    return p


def require_file(root, name):
    valid_rel(name)
    p = security_paths.contained(root, name)
    if (
        not p.is_file()
        or p.is_symlink()
        or not p.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError("Missing or unsafe backup file: " + name)
    return p


def owned_roots(person):
    return [
        ROOT / "Profiles" / person,
        ROOT / "DNA_Archiv/01_Originaldownloads" / person,
        ROOT / "DNA_Archiv/Reports" / person,
        ROOT / "Projects/Databases" / person,
        ROOT / "Projects/Launcher" / person,
    ]


def metadata(person):
    p = person_profile.read(person)
    identity = p.pop("identity")
    p.pop("person", None)
    with family.connect() as db:
        profile_documents.schema(db)
        links = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM links WHERE a=? OR b=?", (person, person)
            )
        ]
        routes = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM routes WHERE anchor=? OR target=?", (person, person)
            )
        ]
        others = {
            v for l in links for k, v in l.items() if k in ("a", "b") and v != person
        }
        for r in routes:
            others.update(x for x in json.loads(r["path"]) if x != person)
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='visual_results'"
        ).fetchone():
            visuals = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM visual_results WHERE person=?", (person,)
                )
            ]
        else:
            visuals = []
        docs = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM profile_documents WHERE person=? AND status!='deleted'",
                (person,),
            )
        ]
        chunks = [
            dict(r)
            for r in db.execute(
                "SELECT c.* FROM document_chunks c JOIN profile_documents d ON d.id=c.document WHERE d.person=? AND d.status!='deleted'",
                (person,),
            )
        ]
        facts = [
            dict(r)
            for r in db.execute("SELECT * FROM profile_facts WHERE person=?", (person,))
        ]
        bound = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM bindings WHERE person=? OR source_person=?",
                (person, person),
            )
        ]
        others.update(v for b in bound for v in b.values() if v != person)
    neighbors = []
    for id in sorted(others):
        try:
            other = person_profile.read(id)
            neighbors.append(
                {
                    "person": id,
                    "uuid": other["identity"]["uuid"],
                    "name": other["name"],
                    "hypothetical": other["hypothetical"],
                }
            )
        except ValueError:
            pass
    import sample_data

    return {
        "person": person,
        "identity": identity,
        "profile": p,
        "sample_profile": sample_data.is_sample(person),
        "documents": docs,
        "chunks": chunks,
        "facts": facts,
        "visuals": visuals,
        "links": links,
        "routes": routes,
        "neighbors": neighbors,
        "bindings": bound,
    }


def fingerprint(person):
    # Relative source hashes + portable metadata + database revision/size prevent date-only decisions.
    value = metadata(person)
    value["sources"] = [
        {
            k: r.get(k)
            for k in (
                "id",
                "sha256",
                "provider",
                "measurement",
                "build",
                "call_count",
                "created",
            )
        }
        for r in source_store.listing(person)
    ]
    # Read table counts and derived state from a consistent connection.
    with contextlib.closing(source_store.connect(person)) as db:
        counts = []
        for table in TABLES:
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone():
                counts.append(
                    (
                        table,
                        db.execute(
                            "SELECT count(*) FROM " + security_sql.identifier(table)
                        ).fetchone()[0],
                    )
                )
        value["database_counts"] = counts
        value["derived"] = [
            list(r) for r in db.execute("SELECT * FROM derived_profile ORDER BY key")
        ]
    # Changes to results, attachments and the source DB are additionally caught by file metadata.
    value["owned_state"] = [
        (str(p.relative_to(ROOT)), p.stat().st_size, p.stat().st_mtime_ns)
        for base in owned_roots(person)
        if base.exists()
        for p in sorted(base.rglob("*"))
        if p.is_file()
        and not p.name.endswith("-shm")
        and (not p.name.endswith("-wal") or p.stat().st_size > 0)
    ]
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def active(person):
    import suite_api

    return [
        j
        for j in suite_api.jobs(person)
        if (
            not str(j.get("job", "")).startswith("transfer_")
            or j.get("task")
            in ("profile_documents", "profile_scan_results", "profile_reindex")
        )
        and j.get("status") in ("Running", "Queued", "Preparing")
    ]


def export_profile(person, destination=None, log=print, cancel=lambda: False):
    if active(person):
        raise ValueError(
            "Wait for this profile’s running or queued analyses before exporting"
        )
    data = metadata(person)
    uid = data["identity"]["uuid"]
    before = fingerprint(person)
    parent = (
        security_paths.local_path(destination)
        if destination
        else ROOT / "ProfileExports"
    )
    if any(parent.is_relative_to(base.resolve()) for base in owned_roots(person)):
        raise ValueError(
            "Export destination must be outside this profile’s source/result folders"
        )
    parent.mkdir(parents=True, exist_ok=True)
    name = (
        "profile-"
        + uid
        + "-"
        + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-"
        + secrets.token_hex(3)
    )
    stage = parent / (name + ".partial")
    stage.mkdir()
    entries = []
    paths = {}

    def copy(src, rel):
        if cancel():
            raise InterruptedError("Profile operation cancelled; originals retained")
        src = Path(src)
        before_stat = src.stat()
        dest = stage / "files" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        with src.open("rb") as i, dest.open("xb") as o:
            while block := i.read(8 * 1024**2):
                if cancel():
                    raise InterruptedError("Profile operation cancelled")
                h.update(block)
                o.write(block)
        if (src.stat().st_size, src.stat().st_mtime_ns) != (
            before_stat.st_size,
            before_stat.st_mtime_ns,
        ):
            raise ValueError("Source changed during export: " + src.name)
        digest = h.hexdigest()
        if sha(dest) != digest:
            raise ValueError("Export copy failed verification")
        entries.append(
            {
                "path": "files/" + str(rel).replace("\\", "/"),
                "restore": str(rel).replace("\\", "/"),
                "sha256": digest,
                "bytes": dest.stat().st_size,
            }
        )
        paths[str(src.resolve())] = str(rel).replace("\\", "/")
        log("Verified: " + src.name)

    database = source_store.folder(person) / "sources.sqlite"
    for base in owned_roots(person):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_symlink():
                raise ValueError("Symbolic links are not exported")
            if not p.is_file() or p.name.endswith(("-wal", "-shm")) or p == database:
                continue
            if not p.resolve().is_relative_to(base.resolve()):
                raise ValueError("Profile file escapes its folder")
            copy(p, p.relative_to(ROOT))
    dbrel = database.relative_to(ROOT)
    snap = stage / "files" / dbrel
    snap.parent.mkdir(parents=True, exist_ok=True)
    with (
        contextlib.closing(source_store.connect(person)) as db,
        contextlib.closing(sqlite3.connect(snap)) as target,
    ):
        db.backup(target)
    import profile_files

    profile_files.clean_export_database(snap)
    entries.append(
        {
            "path": "files/" + dbrel.as_posix(),
            "restore": dbrel.as_posix(),
            "sha256": sha(snap),
            "bytes": snap.stat().st_size,
        }
    )
    # Register any source saved outside the standard owned folders in a contained restore location.
    for r in source_store.listing(person):
        src = Path(r["path"]).resolve()
        if not src.is_file():
            raise ValueError("A registered source is missing: " + r["original_name"])
        if str(src) not in paths:
            copy(
                src,
                Path("DNA_Archiv/01_Originaldownloads")
                / person
                / "RestoredSources"
                / (r["sha256"][:12] + "-" + source_store.safe_name(src.name)),
            )
        if sha(src) != r["sha256"]:
            raise ValueError(
                "A registered source no longer matches its original hash: " + src.name
            )
    for d in data["documents"]:
        src = Path(d["path"]).resolve()
        if not src.is_file():
            raise ValueError("A saved report is missing: " + d["name"])
        if str(src) not in paths:
            copy(
                src,
                Path("DNA_Archiv/Reports")
                / person
                / (d["id"] + "-" + source_store.safe_name(src.name)),
            )
        if sha(src) != d["sha256"]:
            raise ValueError(
                "A report changed; reindex/review before exporting: " + d["name"]
            )
    if fingerprint(person) != before:
        raise ValueError(
            "Profile changed during export; incomplete .partial folder retained, no valid backup published"
        )
    data["source_paths"] = paths
    data["old_root"] = str(ROOT.resolve())
    atomic(stage / "profile.json", data)
    manifest = {
        "format": "DNAWorkbenchProfile",
        "version": 1,
        "profile_uuid": uid,
        "created": profile_identity.now(),
        "identity": data["identity"],
        "source_person": person,
        "profile_sha256": sha(stage / "profile.json"),
        "files": entries,
        "notes": [
            "Contains private profile, source files, saved reports and job outputs. No encryption is provided. Store on a trusted backup drive.",
            "Shared tool installations, model weights and reference panels are not bundled; retain/download the pinned resources separately.",
            "Unlinked relatives are represented by UUID/name stubs; their DNA is not included.",
        ],
    }
    atomic(stage / "profile-transfer.json", manifest)
    final = parent / name
    stage.rename(final)
    return {
        "folder": str(final),
        "profile_uuid": uid,
        "files": len(entries),
        "bytes": sum(r["bytes"] for r in entries),
        "complete": True,
    }


def validate_folder(folder, log=print, cancel=lambda: False):
    root = Path(folder).resolve()
    mfile = require_file(root, "profile-transfer.json")
    if mfile.stat().st_size > 20 * 1024**2:
        raise ValueError("Backup manifest too large")
    m = json.loads(mfile.read_text(encoding="utf-8-sig"))
    if m.get("format") != "DNAWorkbenchProfile" or m.get("version") != 1:
        raise ValueError("Unsupported profile backup format")
    uid = str(uuid.UUID(m["profile_uuid"]))
    pfile = require_file(root, "profile.json")
    if pfile.stat().st_size > 30 * 1024**2 or sha(pfile) != m["profile_sha256"]:
        raise ValueError("Profile metadata checksum mismatch")
    data = json.loads(pfile.read_text(encoding="utf-8"))
    old = m["source_person"]
    if (
        data["identity"]["uuid"] != uid
        or data["person"] != old
        or not __import__("re").fullmatch("[A-Za-z0-9_-]{1,120}", old)
    ):
        raise ValueError("Inconsistent profile identity")
    seen = set()
    allowed = [
        f"Profiles/{old}/",
        f"DNA_Archiv/01_Originaldownloads/{old}/",
        f"DNA_Archiv/Reports/{old}/",
        f"Projects/Databases/{old}/",
        f"Projects/Launcher/{old}/",
    ]
    if not isinstance(m["files"], list) or len(m["files"]) > 100000:
        raise ValueError("Invalid backup file list")
    for r in m["files"]:
        if cancel():
            raise InterruptedError("Check cancelled")
        valid_rel(r["restore"])
        if (
            not any(r["restore"].startswith(prefix) for prefix in allowed)
            or r["path"] != "files/" + r["restore"]
            or r["restore"].casefold() in seen
        ):
            raise ValueError("Invalid or duplicate restore destination")
        seen.add(r["restore"].casefold())
        p = require_file(root, r["path"])
        if p.stat().st_size != r["bytes"] or sha(p) != r["sha256"]:
            raise ValueError("Backup file checksum mismatch: " + r["path"])
        log("Checked: " + p.name)
    if f"Projects/Databases/{old}/sources.sqlite".casefold() not in seen:
        raise ValueError("Backup source database missing")
    validate_source_paths(m, data)
    return root, m, data


def validate_source_paths(manifest, data):
    """A backup may reference only bytes included and checked in that backup."""
    mapping = data.get("source_paths")
    if not isinstance(mapping, dict) or len(mapping) > 100000:
        raise ValueError("Invalid backup source map")
    files = {item["restore"].casefold(): item for item in manifest["files"]}
    normalized = {}
    for original, relative in mapping.items():
        if not isinstance(original, str) or not original or "\x00" in original:
            raise ValueError("Invalid original source label")
        valid_rel(relative)
        if relative.casefold() not in files:
            raise ValueError("Source mapping references bytes absent from the backup")
        key = original.replace("\\", "/").casefold()
        if key in normalized:
            raise ValueError("Ambiguous original source path")
        normalized[key] = files[relative.casefold()]
    for document in data.get("documents", []):
        item = normalized.get(
            str(document.get("path", "")).replace("\\", "/").casefold()
        )
        if (
            not item
            or document.get("sha256") != item["sha256"]
            or document.get("person") != manifest["source_person"]
        ):
            raise ValueError(
                "Saved report does not refer to checked bytes belonging to this backup"
            )


def check_import(folder, log=print, cancel=lambda: False):
    root, m, data = validate_folder(folder, log, cancel)
    existing = profile_identity.lookup(m["profile_uuid"])
    record = {
        "token": secrets.token_hex(32),
        "folder": str(root),
        "manifest_sha256": sha(root / "profile-transfer.json"),
        "profile_uuid": m["profile_uuid"],
        "existing_person": existing,
        "local_fingerprint": fingerprint(existing) if existing else None,
        "created": profile_identity.now(),
    }
    token_dir = ROOT / "DNA_Software/UserData/Launcher/ProfileChecks"
    atomic(token_dir / (record["token"] + ".json"), record)
    local = profile_identity.ensure(existing) if existing else None
    return record | {
        "incoming_name": data["profile"]["name"],
        "incoming_updated": data["identity"]["updated"],
        "local_updated": local["updated"] if local else None,
        "incoming_revision": data["identity"]["revision"],
        "local_revision": local["revision"] if local else None,
        "files": len(m["files"]),
        "bytes": sum(x["bytes"] for x in m["files"]),
        "conflict": bool(existing),
        "warning": "A matching UUID already exists. Dates/revisions from different PCs do not prove which data is better. Replacement requires explicit confirmation and creates a pre-import backup."
        if existing
        else "New UUID: import creates a separate profile; matching names do not cause overwrite.",
    }


def remap(value, old_root, person_map, path_map=None):
    if isinstance(value, dict):
        return {k: remap(v, old_root, person_map, path_map) for k, v in value.items()}
    if isinstance(value, list):
        return [remap(v, old_root, person_map, path_map) for v in value]
    if not isinstance(value, str):
        return value
    if value in person_map:
        return person_map[value]
    if path_map and value in path_map:
        return str(ROOT / path_map[value])
    if path_map and value.replace("\\", "/").startswith(
        ("Profiles/", "DNA_Archiv/", "Projects/")
    ):
        original = str(Path(old_root) / Path(value))
        if original in path_map:
            return path_map[original]
    normalized = value.replace("\\", "/")
    prefix = old_root.replace("\\", "/").rstrip("/") + "/"
    if normalized.casefold().startswith(prefix.casefold()):
        normalized = normalized[len(prefix) :]
        absolute = True
    elif normalized.startswith(("Profiles/", "DNA_Archiv/", "Projects/")):
        absolute = False
    else:
        return value
    parts = [person_map.get(x, x) for x in normalized.split("/")]
    return str(ROOT / Path(*parts)) if absolute else "/".join(parts)


def safe_database(src, dest, person_map, old_root, path_map):
    # Never install an imported SQLite schema, trigger or extension. Copy values into our schema.
    old = source_store.ROOT
    source_store.ROOT = dest
    try:
        target = source_store.connect(next(iter(person_map.values())))
        import profile_pipeline

        profile_pipeline.annotation_schema(target)
        import profile_files

        profile_files.schema(target)
        import workflows

        workflows.schema(target)
        import story_art

        story_art.schema(target)
        target.execute(
            "CREATE TABLE IF NOT EXISTS inheritance_evidence(id TEXT PRIMARY KEY,created TEXT,payload TEXT)"
        )
        target.execute(
            "CREATE TABLE IF NOT EXISTS file_operations(file_id TEXT PRIMARY KEY,source TEXT,target TEXT,requested TEXT,actual TEXT,status TEXT,sha256 TEXT,created TEXT)"
        )
        incoming = sqlite3.connect(src.as_uri() + "?mode=ro&immutable=1", uri=True)
        incoming.execute("PRAGMA trusted_schema=OFF")
        try:
            for table in TABLES:
                if not incoming.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone():
                    continue
                cols = [
                    r[1]
                    for r in target.execute(
                        "PRAGMA table_info(" + security_sql.identifier(table) + ")"
                    )
                ]
                got = [
                    r[1]
                    for r in incoming.execute(
                        "PRAGMA table_info(" + security_sql.identifier(table) + ")"
                    )
                ]
                if cols != got:
                    raise ValueError("Unsupported source database schema: " + table)
                insert = (
                    "INSERT INTO "
                    + security_sql.identifier(table)
                    + " VALUES("
                    + ",".join("?" for _ in cols)
                    + ")"
                )
                for row in incoming.execute(
                    "SELECT * FROM " + security_sql.identifier(table)
                ):
                    values = []
                    for k, v in zip(cols, row):
                        if k in (
                            "payload",
                            "members",
                            "request",
                            "sources",
                            "outputs",
                            "inputs",
                        ) and isinstance(v, str):
                            try:
                                v = json.dumps(
                                    remap(
                                        json.loads(v), old_root, person_map, path_map
                                    ),
                                    ensure_ascii=False,
                                )
                            except ValueError:
                                pass
                        elif k in ("stored_rel", "original_path", "source", "target"):
                            if k == "stored_rel":
                                valid_rel(str(v).replace("\\", "/"))
                            v = remap(v, old_root, person_map, path_map)
                            if k == "stored_rel":
                                valid_rel(str(v).replace("\\", "/"))
                        elif (
                            table == "manager_names"
                            and k == "id"
                            and str(v).startswith("file:")
                        ):
                            v = "file:" + remap(v[5:], old_root, person_map, path_map)
                        values.append(v)
                    target.execute(insert, values)
            target.commit()
            target.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            incoming.close()
            target.close()
    finally:
        source_store.ROOT = old


def import_profile(folder, token, replace=False, log=print, cancel=lambda: False):
    # UUID detection is read-only; re-check under the profile write guard in the worker.
    root = Path(folder).resolve()
    m = json.loads(
        require_file(root, "profile-transfer.json").read_text(encoding="utf-8")
    )
    existing = profile_identity.lookup(str(uuid.UUID(m["profile_uuid"])))
    with profile_identity.exclusive_restore(
        existing or "P_" + uuid.UUID(m["profile_uuid"]).hex
    ):
        return _import_profile(folder, token, replace, log, cancel)


def _import_profile(folder, token, replace=False, log=print, cancel=lambda: False):
    if not __import__("re").fullmatch("[a-f0-9]{64}", token):
        raise ValueError("Run the import check first")
    plan = ROOT / "DNA_Software/UserData/Launcher/ProfileChecks" / (token + ".json")
    if not plan.is_file():
        raise ValueError("Import check is missing or already used")
    record = json.loads(plan.read_text(encoding="utf-8"))
    root, m, data = validate_folder(folder, log, cancel)
    if record["folder"] != str(root) or record["manifest_sha256"] != sha(
        root / "profile-transfer.json"
    ):
        raise ValueError("Backup changed after preview; check again")
    existing = profile_identity.lookup(m["profile_uuid"])
    if (
        existing != record["existing_person"]
        or existing
        and fingerprint(existing) != record["local_fingerprint"]
    ):
        raise ValueError(
            "Local profile changed after preview; check again before deciding"
        )
    if existing and not replace:
        raise ValueError(
            "Matching UUID exists. Nothing overwritten. Explicit replacement confirmation required"
        )
    if existing and active(existing):
        raise ValueError("Wait for running/queued profile analyses before restore")
    pid = existing or "P_" + uuid.UUID(m["profile_uuid"]).hex
    with family.connect() as db:
        if (
            not existing
            and db.execute("SELECT 1 FROM people WHERE id=?", (pid,)).fetchone()
        ):
            pid = "P_" + uuid.uuid4().hex
    previous = (
        export_profile(existing, ROOT / "ProfileExports/BeforeImport", log, cancel)
        if existing
        else None
    )
    mapping = {m["source_person"]: pid}
    pathmap = {
        k: "/".join(mapping.get(x, x) for x in v.split("/"))
        for k, v in data["source_paths"].items()
    }
    stage = ROOT / "DNA_Projects/ProfileTransfers" / ("stage_" + secrets.token_hex(12))
    stage.mkdir(parents=True)
    for r in m["files"]:
        if cancel():
            raise InterruptedError("Import cancelled; current profile unchanged")
        rel = "/".join(mapping.get(x, x) for x in r["restore"].split("/"))
        if r["restore"].endswith("/sources.sqlite"):
            continue
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / r["path"], target)
        if sha(target) != r["sha256"]:
            raise ValueError("Staged restore copy checksum mismatch")
    olddb = require_file(
        root, f"files/Projects/Databases/{m['source_person']}/sources.sqlite"
    )
    safe_database(olddb, stage, mapping, data["old_root"], pathmap)
    # Validate every registered path against staged bytes before changing the active profile.
    with contextlib.closing(
        sqlite3.connect(stage / "Projects/Databases" / pid / "sources.sqlite")
    ) as db:
        for hash, rel in db.execute("SELECT sha256,stored_rel FROM blobs"):
            valid_rel(rel)
            file = stage / rel
            if not file.is_file() or sha(file) != hash:
                raise ValueError(
                    "Restored source registry does not match the backup files"
                )
    if existing and fingerprint(existing) != record["local_fingerprint"]:
        raise ValueError(
            "Local data changed while staging. Nothing replaced; run the check again"
        )
    if cancel():
        raise InterruptedError("Import cancelled before activation")
    stubs = []
    for n in data["neighbors"]:
        other = profile_identity.lookup(n["uuid"])
        if other is None:
            other = "HYP_" + uuid.UUID(n["uuid"]).hex
            with family.connect() as db:
                if db.execute("SELECT 1 FROM people WHERE id=?", (other,)).fetchone():
                    other = "HYP_" + uuid.uuid4().hex
            stubs.append((other, n))
        mapping[n["person"]] = other
    # Rebase only suite-owned job metadata, never original DNA/report payloads.
    for p in (stage / "Projects/Launcher" / pid).glob("**/*.json"):
        if p.name not in ("status.json", "inputs.json", "view.json"):
            continue
        try:
            atomic(
                p,
                remap(
                    json.loads(p.read_text(encoding="utf-8-sig")),
                    data["old_root"],
                    mapping,
                    pathmap,
                ),
            )
        except (ValueError, OSError):
            pass
    history = ROOT / "DNA_Projects/ProfileImportHistory" / secrets.token_hex(16)
    moved = []
    installed = []
    try:
        for target in owned_roots(pid):
            staged = stage / target.relative_to(ROOT)
            if target.exists():
                saved = history / target.relative_to(ROOT)
                saved.parent.mkdir(parents=True, exist_ok=True)
                target.rename(saved)
                moved.append((saved, target))
            if staged.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                staged.rename(target)
                installed.append(target)
        with family.connect() as db:
            profile_documents.schema(db)
            profile_identity.schema(db)
            if not existing:
                db.execute(
                    "INSERT INTO people VALUES(?,?,?)",
                    (
                        pid,
                        data["profile"]["name"],
                        int(data["profile"].get("hypothetical", False)),
                    ),
                )
            else:
                db.execute(
                    "UPDATE people SET label=? WHERE id=?",
                    (data["profile"]["name"], pid),
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS profile_details(person TEXT PRIMARY KEY,data TEXT NOT NULL)"
            )
            details = remap(data["profile"], data["old_root"], mapping, pathmap)
            db.execute(
                "INSERT OR REPLACE INTO profile_details VALUES(?,?)",
                (pid, json.dumps(details, ensure_ascii=False)),
            )
            db.execute(
                "INSERT OR REPLACE INTO profile_identities VALUES(?,?,?,?,?)",
                (
                    pid,
                    m["profile_uuid"],
                    data["identity"]["created"],
                    data["identity"]["updated"],
                    data["identity"]["revision"],
                ),
            )
            if data.get("sample_profile"):
                db.execute(
                    "CREATE TABLE IF NOT EXISTS sample_profiles(person TEXT PRIMARY KEY,version TEXT)"
                )
                db.execute(
                    "INSERT OR REPLACE INTO sample_profiles VALUES(?,?)",
                    (pid, "restored-synthetic"),
                )
            for other, n in stubs:
                db.execute("INSERT INTO people VALUES(?,?,1)", (other, n["name"]))
                db.execute(
                    "INSERT INTO profile_identities VALUES(?,?,?,?,1)",
                    (other, n["uuid"], profile_identity.now(), profile_identity.now()),
                )
            db.execute(
                "DELETE FROM document_chunks WHERE document IN (SELECT id FROM profile_documents WHERE person=?)",
                (pid,),
            )
            for table in ("profile_documents", "profile_facts"):
                db.execute(
                    "DELETE FROM " + security_sql.identifier(table) + " WHERE person=?",
                    (pid,),
                )
            # Map document IDs to avoid collisions with unrelated profiles.
            docids = {d["id"]: uuid.uuid4().hex for d in data["documents"]}
            for d in data["documents"]:
                d = remap(d, data["old_root"], mapping, pathmap)
                d["id"] = docids[d["id"]]
                p = Path(d["path"])
                d["mtime_ns"] = p.stat().st_mtime_ns
                try:
                    notes = json.loads(d.get("notes") or "{}")
                    if (
                        isinstance(notes, dict)
                        and notes.get("source_document") in docids
                    ):
                        notes["source_document"] = docids[notes["source_document"]]
                        d["notes"] = json.dumps(notes, ensure_ascii=False)
                except (ValueError, TypeError):
                    pass
                db.execute(
                    "INSERT INTO profile_documents VALUES(:id,:person,:name,:path,:sha256,:provider,:report_date,:kind,:status,:pages,:bytes,:mtime_ns,:updated,:notes)",
                    d,
                )
            for c in data["chunks"]:
                db.execute(
                    "INSERT INTO document_chunks VALUES(?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        docids[c["document"]],
                        c["page"],
                        c["part"],
                        c["text"],
                        c["topics"],
                    ),
                )
            for f in data["facts"]:
                db.execute(
                    "INSERT INTO profile_facts VALUES(?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        pid,
                        f["question"],
                        f["value"],
                        f["source_type"],
                        f["created"],
                    ),
                )
            db.execute(
                "CREATE TABLE IF NOT EXISTS visual_results(id TEXT PRIMARY KEY,person TEXT,payload TEXT,sha256 TEXT,created TEXT)"
            )
            db.execute("DELETE FROM visual_results WHERE person=?", (pid,))
            for v in data["visuals"]:
                raw = json.dumps(
                    remap(json.loads(v["payload"]), data["old_root"], mapping, pathmap),
                    ensure_ascii=False,
                )
                db.execute(
                    "INSERT INTO visual_results VALUES(?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        pid,
                        raw,
                        hashlib.sha256(raw.encode()).hexdigest(),
                        v["created"],
                    ),
                )
            db.execute("DELETE FROM links WHERE a=? OR b=?", (pid, pid))
            db.execute("DELETE FROM routes WHERE anchor=? OR target=?", (pid, pid))
            for l in data["links"]:
                family.add_link(
                    mapping[l["a"]], mapping[l["b"]], l["kind"], l["note"], db=db
                )
            for r in data["routes"]:
                db.execute(
                    "INSERT INTO routes VALUES(?,?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        mapping[r["anchor"]],
                        mapping[r["target"]],
                        r["relation"],
                        r["side"],
                        json.dumps([mapping[p] for p in json.loads(r["path"])]),
                        r["note"],
                    ),
                )
            # Bindings are restored only if both endpoints exist; foreign source profiles remain empty stubs.
            for b in data["bindings"]:
                if b["person"] in mapping and b["source_person"] in mapping:
                    db.execute(
                        "INSERT OR IGNORE INTO bindings VALUES(?,?)",
                        (mapping[b["person"]], mapping[b["source_person"]]),
                    )
        try:
            plan.rename(plan.with_suffix(".used"))
        except OSError:
            pass  # Active state fingerprint/UUID checks also prevent replay.
        return {
            "person": pid,
            "profile_uuid": m["profile_uuid"],
            "pre_import_backup": previous,
            "history": str(history),
            "notice": "Restored as the same UUID. Related people already present were not overwritten. Shared tools/reference resources must be available separately.",
        }
    except Exception:
        for target in reversed(installed):
            if target.exists():
                saved = stage / "failed-activation" / target.relative_to(ROOT)
                saved.parent.mkdir(parents=True, exist_ok=True)
                target.rename(saved)
        for saved, target in reversed(moved):
            target.parent.mkdir(parents=True, exist_ok=True)
            saved.rename(target)
        raise


def base():
    return ROOT / "DNA_Projects/ProfileTransfers"


def submit(kind, args):
    id = (
        "transfer_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + secrets.token_hex(6)
    )
    folder = base() / id
    folder.mkdir(parents=True)
    person = args.get("person", "")
    stamp = profile_identity.now()
    atomic(folder / "request.json", {"kind": kind, "args": args})
    atomic(
        folder / "status.json",
        {
            "job": id,
            "id": id,
            "person": person,
            "task": "profile_" + kind,
            "title": {
                "export": "Export profile backup",
                "check": "Check profile backup",
                "import": "Import profile backup",
                "documents": "Import and index documents",
                "scan_results": "Index existing analysis results",
                "reindex": "Reindex document",
                "publish": "Publish local analysis reports",
                "process": "OCR and translate report",
                "manager_apply": "Manage profile files",
                "manager_restore": "Restore profile files",
            }[kind],
            "status": "Running",
            "started": stamp,
            "transfer": True,
        },
    )
    with (folder / "auftrag.log").open("ab") as log:
        subprocess.Popen(
            [
                sys.executable,
                str(APP / "profile_transfer.py"),
                "--worker",
                str(folder / "request.json"),
            ],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
    return {"job": id, "person": person, "status": "started", "transfer": True}


def jobs():
    rows = []
    for p in base().glob("transfer_*/status.json"):
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            pass
    return rows


def worker(request):
    folder = request.parent
    r = json.loads(request.read_text(encoding="utf-8"))
    args = r["args"]
    status = json.loads((folder / "status.json").read_text())
    cancel = lambda: (folder / "abbrechen.request").exists()

    def log(text):
        print(text, flush=True)
        status["activity"] = str(text)[:500]
        atomic(folder / "status.json", status)

    try:
        if r["kind"] == "manager_apply":
            import profile_files

            result = profile_files.apply(
                args["person"], args["token"], folder.name, log
            )
        elif r["kind"] == "manager_restore":
            import profile_files

            result = profile_files.restore(
                args["person"], args["operation"], folder.name, log
            )
        elif r["kind"] == "export":
            result = export_profile(
                args["person"], args.get("destination"), log, cancel
            )
        elif r["kind"] == "check":
            result = check_import(args["folder"], log, cancel)
        elif r["kind"] == "import":
            result = import_profile(
                args["folder"], args["token"], args.get("replace", False), log, cancel
            )
            status["target_person"] = result["person"]
        elif r["kind"] == "documents":
            documents = []
            for p in args["files"]:
                if cancel():
                    raise InterruptedError("Document import cancelled")
                documents.append(
                    profile_documents.index_file(
                        args["person"],
                        p,
                        args.get("provider", ""),
                        args.get("report_date", ""),
                        log=log,
                    )
                )
            result = {"documents": documents}
        elif r["kind"] == "scan_results":
            result = profile_documents.scan_results(args["person"], log)
        elif r["kind"] == "process":
            import document_processing

            result = document_processing.process(args, log, cancel)
        elif r["kind"] == "publish":
            import analysis_reports

            result = analysis_reports.publish_all(args["person"], log)
        elif r["kind"] == "reindex":
            result = profile_documents.reindex(args["person"], args["document"], log)
        else:
            raise ValueError("Unknown profile operation")
        atomic(folder / "Results/result.json", result)
        status.update(
            status="Complete", finished=profile_identity.now(), activity="Complete"
        )
    except Exception as e:
        status.update(
            status="Cancelled" if isinstance(e, InterruptedError) else "Failed",
            error=str(e),
            finished=profile_identity.now(),
        )
        print(str(e), flush=True)
    atomic(folder / "status.json", status)


if __name__ == "__main__":
    worker(Path(sys.argv[2]))
