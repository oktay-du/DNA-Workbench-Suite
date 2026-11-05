import security_paths

"""Explicit file selection → batch checks → reviewed profile storage → typed tools.

No startup scan, implicit archive import, inferred owner or fabricated tool result.
"""
from pathlib import Path
import contextlib, datetime, gzip, hashlib, json, os, re, shutil, threading, time, uuid
import suite_api, source_store, inspector

GUARD = threading.RLock()
ACTIVE = None
OWNER = None


def assert_idle():
    with GUARD:
        if ACTIVE and OWNER != threading.get_ident():
            raise ValueError("A batch preparation is running. Wait or cancel it first.")


def now():
    return datetime.datetime.now().astimezone().isoformat()


def atomic(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def location(person, job):
    if not re.fullmatch(r"intake_[a-f0-9]{32}", job):
        raise ValueError("Invalid batch ID")
    return suite_api.job_path(person, job)


def read(person, job):
    p = location(person, job)
    value = json.loads((p / "batch.json").read_text(encoding="utf-8"))
    with GUARD:
        live = ACTIVE == (person, job)
    if value["phase"] in ("scanning", "processing") and not live:
        value.update(
            phase="interrupted",
            notice="Interrupted. Select/review again; nothing is restarted automatically.",
        )
    return value


def save(folder, v):
    atomic(folder / "batch.json", v)
    active = v["phase"] in ("scanning", "processing")
    status = (
        "Running"
        if active
        else "Complete"
        if v["phase"] == "completed"
        else "Cancelled"
        if v["phase"] == "cancelled"
        else "Failed"
        if v["phase"] == "failed"
        else "Eingaben erforderlich"
    )
    atomic(
        folder / "status.json",
        {
            "id": v["job"],
            "task": "batch_intake",
            "person": v["person"],
            "title": "Batch file preparation",
            "status": status,
            "started": v["created"],
            "finished": None if active else now(),
            "progress": {
                "completed": v["done"],
                "total": max(1, v["total"]),
                "percent": round(100 * v["done"] / max(1, v["total"]), 1),
                "unit": "files",
            },
            "outputs": ["batch-summary.json"],
        },
    )
    (folder / "auftrag.log").write_text(
        "\n".join(v.get("log", [])[-200:]), encoding="utf-8"
    )
    if not active:
        atomic(folder / "Results/batch-summary.json", v)


def collect(values):
    out = []
    seen = set()

    def linked(p):
        return p.is_symlink() or getattr(p, "is_junction", lambda: False)()

    for raw in values:
        p = security_paths.local_path(raw)
        if linked(p):
            raise ValueError(
                "Choose regular local files/folders, not symbolic links or junctions."
            )
        if p.is_dir():
            candidates = []
            for parent, dirs, files in os.walk(p, followlinks=False):
                dirs[:] = [d for d in dirs if not linked(Path(parent) / d)]
                candidates.extend(Path(parent) / f for f in files)
                if len(candidates) > 10000:
                    raise ValueError(
                        "Limit: 10,000 selected files. Select a smaller folder."
                    )
        else:
            candidates = [p]
        for x in candidates:
            if x.name.endswith(".dna-source.json"):
                continue
            if (
                x.is_file()
                and not linked(x)
                and not any(linked(parent) for parent in x.parents)
            ):
                key = str(x.resolve()).casefold()
                if key not in seen:
                    out.append(str(x.resolve()))
                    seen.add(key)
                if len(out) > 10000:
                    raise ValueError(
                        "Limit: 10,000 selected files. Select a smaller folder."
                    )
    return out


def start(r):
    import source_batch

    source_batch.assert_idle()
    global ACTIVE
    person = suite_api.checked_person(r["person"])
    paths = collect(r.get("files", []))
    registered = (
        source_store.listing(person) if r.get("include_registered", True) else []
    )
    wanted = r.get("kinds", [])
    if wanted:
        paths = [p for p in paths if source_store.classify(Path(p).name) in wanted]
        registered = [x for x in registered if x["kind"] in wanted]
    paths = list(dict.fromkeys(paths + [x["path"] for x in registered]))
    if not paths:
        raise ValueError(
            "Choose files or a folder explicitly, or import sources into this profile first. The private archive is never scanned automatically."
        )
    import workflows

    workflows.assert_idle()
    with GUARD:
        if ACTIVE or any(p.poll() is None for p in suite_api.PROCESSES.values()):
            raise ValueError("Wait for the running batch/tool first.")
        job = "intake_" + uuid.uuid4().hex
        folder = location(person, job)
        (folder / "Results").mkdir(parents=True)
        v = {
            "person": person,
            "job": job,
            "created": now(),
            "phase": "scanning",
            "done": 0,
            "total": len(paths),
            "items": [],
            "log": [],
            "explicit_selection": r.get("files", []),
            "rules": 1,
        }
        atomic(
            folder / "inputs.json",
            {
                "person": person,
                "task": "batch_intake",
                "inputs": {"files": paths},
                "source_state": "explicit_selection_only",
            },
        )
        save(folder, v)
        ACTIVE = (person, job)
    threading.Thread(
        target=scan, args=(folder, v, paths, registered), daemon=True
    ).start()
    return {"person": person, "job": job}


def scan(folder, v, paths, registered):
    global ACTIVE, OWNER
    OWNER = threading.get_ident()

    def log(s):
        v["log"].append(now() + " " + s)
        save(folder, v)

    known = {str(Path(x["path"]).resolve()).casefold(): x for x in registered}
    references = []
    with contextlib.closing(source_store.connect(v["person"])) as db:
        for row in db.execute(
            "SELECT payload FROM inspections ORDER BY checked DESC LIMIT 3"
        ):
            try:
                references.append(json.loads(row[0]))
            except ValueError:
                pass
    try:
        for i, path in enumerate(paths):
            if (folder / "abbrechen.request").exists():
                v["phase"] = "cancelled"
                break
            log(
                "Checking "
                + str(i + 1)
                + "/"
                + str(len(paths))
                + ": "
                + Path(path).name
            )
            row = known.get(path.casefold())
            kind = source_store.classify(Path(path).name)
            item = {
                "id": uuid.uuid4().hex,
                "path": path,
                "name": Path(path).name,
                "kind": kind,
                "person": v["person"],
                "provider": row["provider"] if row else "Unknown",
                "registered_id": row["id"] if row else None,
                "selected": True,
                "state": "checked",
                "build": row["build"] if row else "",
                "steps": [],
                "measurement": row.get("measurement", "Unknown") if row else "Unknown",
                "declared_version": row.get("declared_version", "") if row else "",
            }
            try:
                p = Path(path)
                if p.name.lower().endswith(
                    (".crdownload", ".part", ".tmp", ".importing")
                ):
                    raise ValueError(
                        "Download or file operation is still in progress; finish it first."
                    )
                if kind in ("FASTQ", "FASTA"):
                    st = p.stat()
                    with p.open("rb") as f:
                        h = hashlib.file_digest(f, "sha256").hexdigest()
                    op = gzip.open if p.name.lower().endswith((".gz", ".bgz")) else open
                    with op(p, "rt", encoding="utf-8-sig") as f:
                        lines = [f.readline(1024 * 1024) for _ in range(4)]
                    if kind == "FASTQ" and (
                        not lines[0].startswith("@")
                        or not lines[2].startswith("+")
                        or len(lines[1].strip()) != len(lines[3].strip())
                    ):
                        raise ValueError(
                            "FASTQ start is malformed or incomplete. Keep this download for review; do not run as a complete read file."
                        )
                    if kind == "FASTA" and not lines[0].startswith(">"):
                        raise ValueError("FASTA header missing.")
                    detail = {
                        "path": path,
                        "name": p.name,
                        "sha256": h,
                        "bytes": st.st_size,
                        "mtime_ns": st.st_mtime_ns,
                        "format": kind,
                        "color": "orange",
                        "verified": False,
                        "issues": [
                            "Header checked; full read/sequence validation is a subsequent routed tool step. No reference build is assumed for unaligned reads."
                        ],
                        "first_read": lines[0].strip() if kind == "FASTQ" else "",
                    }
                elif kind == "Image":
                    from PIL import Image

                    st = p.stat()
                    with p.open("rb") as f:
                        h = hashlib.file_digest(f, "sha256").hexdigest()
                    with Image.open(p) as im:
                        size = list(im.size)
                        im.verify()
                    detail = {
                        "path": path,
                        "name": p.name,
                        "sha256": h,
                        "bytes": st.st_size,
                        "mtime_ns": st.st_mtime_ns,
                        "format": "Image / report scan",
                        "color": "gray",
                        "verified": False,
                        "issues": [
                            "Image validated; OCR/medical interpretation has not been performed."
                        ],
                        "dimensions": size,
                    }
                elif kind == "Archive":
                    import tool_contracts

                    st = p.stat()
                    with p.open("rb") as f:
                        h = hashlib.file_digest(f, "sha256").hexdigest()
                    meta = tool_contracts.probe(p)
                    detail = {
                        "path": path,
                        "name": p.name,
                        "sha256": h,
                        "bytes": st.st_size,
                        "mtime_ns": st.st_mtime_ns,
                        "format": "Archive / " + meta["compression"],
                        "color": "orange",
                        "verified": False,
                        "issues": [
                            "Container checked as bytes only; payload validation follows reviewed extraction. Original retained."
                        ],
                        **meta,
                        **inspector.tokens("", p.name),
                    }
                else:
                    detail = inspector.inspect(path, log)
                after = p.stat()
                if (after.st_size, after.st_mtime_ns) != (
                    detail["bytes"],
                    detail["mtime_ns"],
                ):
                    raise ValueError(
                        "File changed during checking; finish the download and check again."
                    )
                detail["technical_color"] = detail["color"]
                comparisons = []
                for ref in references:
                    if (
                        detail.get("sha256") == ref.get("sha256")
                        or not detail.get("build")
                        or detail.get("build") != ref.get("build")
                    ):
                        continue
                    common = set(detail.get("fingerprint", {})) & set(
                        ref.get("fingerprint", {})
                    )
                    if len(common) >= 1000:
                        same = sum(
                            detail["fingerprint"][k] == ref["fingerprint"][k]
                            for k in common
                        )
                        comparisons.append(
                            {
                                "common": len(common),
                                "concordance": same / len(common),
                                "reference_sha256": ref["sha256"],
                            }
                        )
                if comparisons:
                    best = max(comparisons, key=lambda x: x["concordance"])
                    detail["person_comparisons"] = comparisons
                    if best["common"] >= 10000 and best["concordance"] < 0.85:
                        detail.update(
                            color="black", verified=False, assignment_conflict=True
                        )
                        detail["issues"].append(
                            "Strong profile/source conflict. Review person assignment and technical/reference differences before import."
                        )
                    elif best["concordance"] < 0.995:
                        detail.update(color="orange", verified=False)
                        detail["issues"].append(
                            "Source differences need review; this is not an identity or kinship proof."
                        )
                if (
                    len(references) < 3
                    and detail.get("fingerprint")
                    and detail.get("color") not in ("red", "black")
                ):
                    references.append(detail)
                if detail.get("color") == "red" and kind in ("FASTQ", "FASTA"):
                    detail.update(
                        color="orange",
                        verified=False,
                        issues=[
                            "Sequence format: use the routed sequence/FASTQ validator; not a chip genotype table."
                        ],
                    )
                if kind == "Report":
                    detail.update(color="gray", verified=False)
                if row and detail["sha256"] != row["sha256"]:
                    detail.update(color="red", verified=False)
                    detail["issues"].append(
                        "File changed since registration. Replace/review the source; do not silently accept altered bytes."
                    )
                item.update(
                    sha256=detail["sha256"],
                    bytes=detail["bytes"],
                    mtime_ns=detail["mtime_ns"],
                    build=detail.get("build") or item["build"],
                    color=detail["color"],
                    format=detail["format"],
                    issues=detail["issues"],
                    details={
                        k: x
                        for k, x in detail.items()
                        if k not in ("fingerprint", "content_header")
                    },
                )
                if item["provider"] == "Unknown":
                    item["provider"] = detail.get("provider", "Unknown")
                item["selected"] = item["color"] not in ("red", "black")
                atomic(folder / "checks" / (item["id"] + ".json"), detail)
            except Exception as e:
                item.update(
                    state="needs_review", color="red", selected=False, issues=[str(e)]
                )
            v["items"].append(item)
            v["done"] = i + 1
            save(folder, v)
        else:
            v["phase"] = "review"
            v["notice"] = (
                "Review ownership/provider and choose Move or Copy. Checks have not imported, moved or clinically verified any file."
            )
    except Exception as e:
        v.update(phase="failed", error=str(e))
    finally:
        save(folder, v)
        with GUARD:
            ACTIVE = None
            OWNER = None


def route(item, path):
    kind = item["kind"]
    fmt = item.get("format", "")
    if kind == "Archive":
        return ("archive_payloads", {})
    if kind == "BCF":
        return ("variant_convert", {"vcf": path, "output_format": "VCF.gz (BGZF)"})
    if kind == "VCF":
        return ("vcf_qc", {"vcf": path})
    if kind in ("BAM", "CRAM"):
        return ("bam_qc", {"bam": path})
    if kind == "FASTQ":
        return ("fastq_report", {"r1": path, "r2": ""})
    if kind == "FASTA":
        return ("sequence_stats", {"files": [path], "read_limit": "10000"})
    if kind == "Report":
        return ("document", {})
    if kind == "Image":
        return ("image_metadata", {})
    if kind == "GEDCOM":
        return ("gedcom", {})
    if kind == "Index":
        return ("sidecar", {})
    if kind in ("Raw data / text", "Chip / table") and (
        fmt == "Chip/SNP table" or item.get("details", {}).get("called_points", 0)
    ):
        return ("chip_vcf", {"file": path})
    if fmt in ("Chip/SNP table", "VCF") or item.get("details", {}).get(
        "called_points", 0
    ):
        return ("genotype_compare", {})
    if (
        "JSON" in fmt
        or "Match-/Segment" in fmt
        or "Segmentzuordnung" in fmt
        or "Herkunftsbericht" in fmt
    ):
        return (
            "provider_export",
            {"file": path, "export_kind": "Detect automatically"},
        )
    if kind == "Archive":
        return ("archive_payloads", {})
    return ("unsupported", {})


def organize(person, row, log, mode="move"):
    """Move an already registered external/legacy source, preserving IDs and hashes."""
    import profile_identity

    profile_identity.assert_writable(person)
    src = Path(row["path"]).resolve()
    base = (source_store.profile_dir(person) / "Sources").resolve()
    if src.is_relative_to(base):
        return str(src)
    if (
        source_store.build_hint(src)
        and row["build"] in ("GRCh37", "GRCh38")
        and source_store.build_hint(src) != row["build"]
    ):
        raise ValueError("Build differs from the register; review first.")
    with src.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    if digest != row["sha256"]:
        raise ValueError("File changed since registration; source was not moved.")
    targetdir = (
        base
        / source_store.safe_name(row["provider"])
        / ("Organized_" + uuid.uuid4().hex[:12])
    )
    targetdir.mkdir(parents=True)
    dest = targetdir / ("001-" + src.name)
    if dest.exists():
        raise ValueError("Destination exists; nothing overwritten.")
    before = src.stat()
    same = src.stat().st_dev == targetdir.stat().st_dev
    if same and mode == "move":
        src.rename(dest)
    else:
        shutil.copy2(src, dest)
        with dest.open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != digest:
                raise ValueError("Copy did not verify; source retained.")
    try:
        if (dest.stat().st_size, dest.stat().st_mtime_ns) != (
            before.st_size,
            before.st_mtime_ns,
        ):
            raise ValueError("Moved source metadata changed.")
        with contextlib.closing(source_store.connect(person)) as db:
            db.execute(
                "UPDATE blobs SET stored_rel=? WHERE sha256=?",
                (str(dest.relative_to(source_store.ROOT)), digest),
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS storage_moves(id TEXT PRIMARY KEY,sha256 TEXT,old_path TEXT,new_path TEXT,created TEXT)"
            )
            db.execute(
                "INSERT INTO storage_moves VALUES(?,?,?,?,?)",
                (uuid.uuid4().hex, digest, str(src), str(dest), now()),
            )
            db.commit()
    except BaseException:
        if same and mode == "move" and dest.exists() and not src.exists():
            dest.rename(src)
        raise
    if mode == "move" and not same:
        src.unlink()
    # Attachment rows can refer to exactly the same source bytes.
    import family

    with family.connect() as db:
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='profile_documents'"
        ).fetchone():
            db.execute(
                "UPDATE profile_documents SET path=? WHERE person=? AND path=?",
                (str(dest), person, str(src)),
            )
    log("Organized into profile: " + dest.name)
    return str(dest)


def accept(r):
    global ACTIVE
    owner = suite_api.checked_person(r["person"])
    folder = location(owner, r["job"])
    v = read(owner, r["job"])
    if v["phase"] not in ("review", "completed", "needs_attention"):
        raise ValueError("Wait for the batch check and review its results first.")
    if r.get("confirmed") is not True or r.get("storage_mode") not in ("move", "copy"):
        raise ValueError("Explicitly confirm profile assignments and Move or Copy.")
    choices = r.get("items", [])
    items = {x["id"]: x for x in v["items"]}
    selected = []
    for c in choices:
        item = items.get(c["id"])
        if not item or item.get("color") in ("red", "black") or not item.get("sha256"):
            raise ValueError(
                "Only successfully checked, non-conflicting files can be accepted."
            )
        person = suite_api.checked_person(c["person"])
        provider = str(c.get("provider") or item["provider"])
        if provider not in inspector.PROVIDERS:
            raise ValueError("Choose a known provider or Unknown.")
        if item["registered_id"] and person != item["person"]:
            raise ValueError(
                "A registered file cannot silently change its profile. Review/remove the old assignment explicitly first."
            )
        build = c.get("declared_build", "Unknown")
        if (
            build in ("GRCh37", "GRCh38")
            and item.get("build") in ("GRCh37", "GRCh38")
            and build != item["build"]
        ):
            raise ValueError(
                "Declared build contradicts the detected/registered build. Review the file instead of relabelling coordinates."
            )
        st = Path(item["path"]).stat()
        if (st.st_size, st.st_mtime_ns) != (item["bytes"], item["mtime_ns"]):
            raise ValueError("File changed after checking. Check again before import.")
        selected.append(
            dict(
                item,
                person=person,
                provider=provider,
                build=build if build in ("GRCh37", "GRCh38") else item.get("build", ""),
                declared_version=str(c.get("version", ""))[:200],
                measurement=c.get("measurement", "Unknown"),
            )
        )
    if not selected:
        raise ValueError("Select at least one checked file.")
    import workflows

    workflows.assert_idle()
    with GUARD:
        if ACTIVE or any(p.poll() is None for p in suite_api.PROCESSES.values()):
            raise ValueError("Another tool or batch is running.")
        ACTIVE = (owner, r["job"])
        v.update(
            phase="processing",
            done=0,
            total=len(selected),
            accepted=selected,
            storage_mode=r["storage_mode"],
            follow_tools=r.get("follow_tools", True),
            expand_archives=r.get("expand_archives", True),
            results=[],
        )
        save(folder, v)
    threading.Thread(target=process, args=(folder, v), daemon=True).start()
    return {"person": owner, "job": r["job"]}


def process(folder, v):
    global ACTIVE, OWNER
    OWNER = threading.get_ident()

    def log(s):
        v["log"].append(now() + " " + s)
        save(folder, v)

    try:
        # One provider batch keeps read mates and matching sidecar index names together.
        imported_paths = {}
        groups = {}
        for x in v["accepted"]:
            if not x["registered_id"]:
                groups.setdefault(
                    (
                        x["person"],
                        x["provider"],
                        x.get("build", ""),
                        x.get("declared_version", ""),
                    ),
                    [],
                ).append(x)
        for (
            person,
            provider,
            declared_build,
            declared_version,
        ), items in groups.items():
            paths = [x["path"] for x in items]
            expected = {str(Path(x["path"]).resolve()): x["sha256"] for x in items}
            try:
                batch = source_store.import_batch(
                    person,
                    paths,
                    provider,
                    "Reviewed batch " + v["job"],
                    expected=expected,
                    storage_mode=v["storage_mode"],
                    build=declared_build,
                    version=declared_version,
                    log=log,
                )
                fresh = source_store.listing(person)
                for x in items:
                    imported_paths[x["id"]] = next(
                        r["path"]
                        for r in fresh
                        if r["id"] in batch["ids"] and r["original_path"] == x["path"]
                    )
            except Exception as e:
                # Partial imports stay registered and source-safe; expose each row below.
                log("Storage group needs review: " + str(e))
                for x in items:
                    row = next(
                        (
                            r
                            for r in source_store.listing(person)
                            if r["sha256"] == x["sha256"]
                            and r["original_path"] == x["path"]
                            and r["available"]
                        ),
                        None,
                    )
                    if row:
                        imported_paths[x["id"]] = row["path"]
        for item in v["accepted"]:
            if (folder / "abbrechen.request").exists():
                v["phase"] = "cancelled"
                break
            result = {
                "id": item["id"],
                "person": item["person"],
                "name": item["name"],
                "status": "processing",
                "steps": [],
            }
            v["results"].append(result)
            try:
                person = item["person"]
                path = item["path"]
                if item["registered_id"]:
                    row = next(
                        x
                        for x in source_store.listing(person)
                        if x["id"] == item["registered_id"]
                    )
                    path = organize(person, row, log, v["storage_mode"])
                else:
                    if item["id"] not in imported_paths:
                        raise ValueError(
                            "Storage/import did not complete for this file; source retained where possible. Review the batch log."
                        )
                    path = imported_paths[item["id"]]
                checked = json.loads(
                    (folder / "checks" / (item["id"] + ".json")).read_text(
                        encoding="utf-8"
                    )
                )
                checked["path"] = path
                if item.get("build") and not checked.get("build"):
                    checked.update(
                        build=item["build"],
                        build_provenance="user-declared at reviewed batch import",
                    )
                checked.pop("declared_version", None)
                row = next(
                    r
                    for r in source_store.listing(person)
                    if r["sha256"] == item["sha256"]
                    and (
                        r["id"] == item.get("registered_id")
                        or not item.get("registered_id")
                        and r["original_path"]
                        == item.get("path_before_import", item["path"])
                    )
                )
                with contextlib.closing(source_store.connect(person)) as db:
                    db.execute(
                        "INSERT OR REPLACE INTO source_metadata VALUES(?,?,?)",
                        (
                            row["id"],
                            json.dumps(
                                {
                                    "declared_version": item.get(
                                        "declared_version", ""
                                    ),
                                    "measurement": item.get("measurement", "Unknown"),
                                    "provenance": "user-declared during reviewed batch; not independent quality evidence",
                                }
                            ),
                            now(),
                        ),
                    )
                    db.commit()
                with contextlib.closing(source_store.connect(person)) as db:
                    db.execute(
                        "INSERT OR REPLACE INTO inspections VALUES(?,?,?)",
                        (item["sha256"], json.dumps(checked), now()),
                    )
                    db.commit()
                result["path"] = path
                item["path"] = path
                task, inputs = route(item, path)
                result["route"] = task
                if not v["follow_tools"]:
                    result["status"] = "stored"
                    continue
                if task == "archive_payloads":
                    if not v["expand_archives"]:
                        result.update(
                            status="needs_input",
                            reason="Archive extraction not selected. The original archive is safely stored.",
                        )
                    else:
                        children = expand_archive(person, item, path, folder, log)
                        seen = {x["id"] for x in v["accepted"]}
                        for child in children:
                            if child["id"] not in seen:
                                v["accepted"].append(child)
                                v["total"] += 1
                                seen.add(child["id"])
                        result.update(
                            status="expanded",
                            children=len(children),
                            reason="Archive retained; payloads registered with container provenance, not independent measurements.",
                        )
                elif task == "document":
                    import profile_documents

                    d = profile_documents.index_file(
                        person,
                        path,
                        item["provider"],
                        kind="imported_report",
                        copy=False,
                        log=log,
                    )
                    result.update(status="completed", document=d["id"])
                elif task == "gedcom":
                    import genealogy_research

                    text = Path(path).read_text(encoding="utf-8-sig")
                    data = genealogy_research.parse(text)
                    atomic(
                        folder / "Results" / ("GEDCOM_" + item["id"] + ".json"), data
                    )
                    result.update(
                        status="completed",
                        notice="GEDCOM parsed and retained. Documented relationships are not DNA verification; graph changes require explicit import review.",
                    )
                elif task in ("sidecar", "genotype_compare", "image_metadata"):
                    result["status"] = "stored"
                elif task in ("archive_review", "unsupported"):
                    result.update(
                        status="needs_attention",
                        reason="Format retained. No safe automatic adapter; review this source. No guessed genotype conversion.",
                    )
                else:
                    import workflows, on_demand

                    plan = workflows.task_plan(person, task)
                    vals = dict(plan["inputs"])
                    vals.update(inputs)
                    spec = next(t for t in suite_api.CAT()["tasks"] if t["id"] == task)
                    missing = [
                        f["key"]
                        for f in spec["fields"]
                        if f.get("required") and not vals.get(f["key"])
                    ]
                    if item["kind"] == "CRAM" and not vals.get("reference"):
                        missing.append("exact_cram_reference")
                    deps = on_demand.status(task, path)
                    if missing or not deps["ready"]:
                        result.update(
                            status="needs_input",
                            reason="Missing inputs or tool/reference dependencies.",
                            task=task,
                            inputs=vals,
                            missing=missing,
                            dependencies=deps["requirements"],
                        )
                    else:
                        job = suite_api.start(
                            {"person": person, "task": task, "inputs": vals}
                        )
                        result.update(tool_job=job["job"], task=task)
                        while True:
                            state = json.loads(
                                (
                                    suite_api.job_path(person, job["job"])
                                    / "status.json"
                                ).read_text(encoding="utf-8")
                            )
                            if state["status"] not in (
                                "Running",
                                "Queued",
                                "Preparing",
                            ):
                                break
                            if (folder / "abbrechen.request").exists():
                                (
                                    suite_api.job_path(person, job["job"])
                                    / "abbrechen.request"
                                ).touch()
                            time.sleep(0.5)
                        result["status"] = (
                            "completed"
                            if state["status"] == "Complete"
                            else "needs_attention"
                        )
                        if (
                            task in ("chip_vcf", "variant_convert")
                            and state["status"] == "Complete"
                        ):
                            import derived_sources

                            result["derived_sources"] = derived_sources.register(
                                person,
                                item["sha256"],
                                job["job"],
                                item["provider"],
                                item.get("measurement", "Unknown"),
                                log,
                                operation=task,
                            )

            except Exception as e:
                result.update(status="needs_attention", reason=str(e))
                log(item["name"] + ": " + str(e))
            finally:
                v["done"] += 1
                save(folder, v)
        else:
            # Full source comparison once per profile, after file-specific adapters. No
            # conversion from raw reads is implied by a SNP comparison.
            if v["follow_tools"]:
                for person in sorted({x["person"] for x in v["accepted"]}):
                    if any(
                        x.get("details", {}).get("called_points", 0) > 0
                        and x.get("details", {}).get("variant_types", {}).get("SNV", 1)
                        > 0
                        for x in v["accepted"]
                        if x["person"] == person
                    ):
                        try:
                            job = suite_api.start(
                                {
                                    "person": person,
                                    "task": "profile_analyze",
                                    "inputs": {
                                        "target": "Getrennt belassen",
                                        "chain": "",
                                        "reference": "",
                                    },
                                }
                            )
                            while True:
                                s = json.loads(
                                    (
                                        suite_api.job_path(person, job["job"])
                                        / "status.json"
                                    ).read_text(encoding="utf-8")
                                )
                                if s["status"] not in (
                                    "Running",
                                    "Queued",
                                    "Preparing",
                                ):
                                    break
                                time.sleep(0.5)
                            v.setdefault("source_comparisons", []).append(
                                {
                                    "person": person,
                                    "job": job["job"],
                                    "status": s["status"],
                                }
                            )
                            log(
                                "Source SNP comparison: "
                                + s["status"]
                                + " for "
                                + person
                            )
                        except Exception as e:
                            v.setdefault("comparison_issues", []).append(str(e))
                            v["log"].append("SNP comparison requires review: " + str(e))
            v["phase"] = (
                "needs_attention"
                if v.get("comparison_issues")
                or any(
                    x["status"] != "Complete" for x in v.get("source_comparisons", [])
                )
                or any(
                    x["status"] in ("needs_input", "needs_attention")
                    for x in v["results"]
                )
                else "completed"
            )
    except Exception as e:
        v.update(phase="failed", error=str(e))
    finally:
        save(folder, v)
        with GUARD:
            ACTIVE = None
            OWNER = None


def expand_archive(person, item, path, folder, log):
    parent = item["sha256"]
    rows = source_store.listing(person)
    existing = [
        r for r in rows if r.get("container_sha256") == parent and r["available"]
    ]
    if existing:
        payloads = existing
    else:
        import archive_io

        temp = folder / "ArchiveWork" / (parent + "_" + uuid.uuid4().hex[:8])
        members = archive_io.unpack(
            path, temp, lambda: (folder / "abbrechen.request").exists()
        )
        paths = [p for p in members if source_store.classify(Path(p).name) != "Other"]
        atomic(
            folder / "checks" / ("archive_" + parent + ".json"),
            {
                "archive_sha256": parent,
                "original_archive_name": item["name"],
                "members": members,
                "skipped": [name for p, name in members.items() if p not in paths],
                "original_retained": True,
            },
        )
        if not paths:
            raise ValueError(
                "No supported archive payloads. Original archive retained."
            )
        imported = source_store.import_batch(
            person,
            paths,
            item["provider"],
            "Archive payloads " + parent[:12],
            storage_mode="move",
            log=log,
        )
        payloads = [
            r for r in source_store.listing(person) if r["id"] in imported["ids"]
        ]
        with contextlib.closing(source_store.connect(person)) as db:
            for r in payloads:
                db.execute(
                    "INSERT OR REPLACE INTO archive_payloads VALUES(?,?,?,?)",
                    (parent, r["id"], members[r["original_path"]], now()),
                )
            db.commit()
    children = []
    for r in payloads:
        # Each payload is checked independently, then follows the same typed routing.
        checked = (
            inspector.inspect(r["path"], log)
            if r["kind"] not in ("FASTQ", "FASTA")
            else {
                "sha256": r["sha256"],
                "bytes": r["bytes"],
                "mtime_ns": Path(r["path"]).stat().st_mtime_ns,
                "path": r["path"],
                "name": r["original_name"],
                "format": r["kind"],
                "color": "orange",
                "verified": False,
                "issues": ["Extracted read/sequence payload; full QC pending."],
            }
        )
        id = "payload_" + r["id"]
        atomic(folder / "checks" / (id + ".json"), checked)
        if checked.get("color") in ("red", "black"):
            raise ValueError(
                "Extracted payload failed validation: " + r["original_name"]
            )
        if r["kind"] == "Archive":
            raise ValueError(
                "Nested archive retained; extract it explicitly to avoid recursive archive expansion."
            )
        children.append(
            {
                "id": id,
                "path": r["path"],
                "name": r["original_name"],
                "kind": r["kind"],
                "person": person,
                "provider": item["provider"],
                "registered_id": r["id"],
                "sha256": r["sha256"],
                "bytes": r["bytes"],
                "mtime_ns": Path(r["path"]).stat().st_mtime_ns,
                "build": checked.get("build", ""),
                "format": checked["format"],
                "color": checked["color"],
                "details": {
                    k: v
                    for k, v in checked.items()
                    if k not in ("fingerprint", "content_header")
                },
                "issues": checked.get("issues", []),
                "selected": True,
                "declared_version": item.get("declared_version", ""),
                "measurement": checked.get("measurement", "Unknown")
                if item.get("measurement", "Unknown") == "Unknown"
                else item["measurement"],
            }
        )
    return children


def assign(r):
    owner = suite_api.checked_person(r["person"])
    destination = suite_api.checked_person(r["destination"])
    folder = location(owner, r["job"])
    v = read(owner, r["job"])
    if v["phase"] != "review":
        raise ValueError("Profile assignments can only change during batch review.")
    item = next((x for x in v["items"] if x["id"] == r["item"]), None)
    if not item or item.get("registered_id"):
        raise ValueError(
            "Only unregistered reviewed files can change destination profile."
        )
    detail = json.loads(
        (folder / "checks" / (item["id"] + ".json")).read_text(encoding="utf-8")
    )
    technical = detail.get("technical_color", detail["color"])
    if technical in ("red", "black"):
        raise ValueError(
            "Technical validation failed; changing a profile does not repair the file."
        )
    detail["color"] = technical
    detail["verified"] = False
    detail["assignment_conflict"] = False
    detail["person_comparisons"] = []
    detail["issues"] = [
        x
        for x in detail.get("issues", [])
        if not x.startswith(
            (
                "Strong profile/source conflict.",
                "Source differences need review;",
                "Destination profile conflict:",
                "Destination manually confirmed:",
            )
        )
    ]
    with contextlib.closing(source_store.connect(destination)) as db:
        for (raw,) in db.execute(
            "SELECT payload FROM inspections ORDER BY checked DESC LIMIT 3"
        ):
            ref = json.loads(raw)
            if not detail.get("build") or detail.get("build") != ref.get("build"):
                continue
            common = set(detail.get("fingerprint", {})) & set(
                ref.get("fingerprint", {})
            )
            if len(common) < 1000:
                continue
            concordance = sum(
                detail["fingerprint"][k] == ref["fingerprint"][k] for k in common
            ) / len(common)
            detail["person_comparisons"].append(
                {
                    "common": len(common),
                    "concordance": concordance,
                    "reference_sha256": ref["sha256"],
                }
            )
    if (
        detail["person_comparisons"]
        and max(x["concordance"] for x in detail["person_comparisons"]) < 0.85
        and max(x["common"] for x in detail["person_comparisons"]) >= 10000
    ):
        detail.update(color="black", assignment_conflict=True)
        detail["issues"].append(
            "Destination profile conflict: check biological ownership and technical differences."
        )
    else:
        detail["issues"].append(
            "Destination manually confirmed: "
            + destination
            + ". This assignment is not a DNA identity proof."
        )
    item.update(
        person=destination,
        color=detail["color"],
        selected=detail["color"] not in ("red", "black"),
        issues=detail["issues"],
        details={
            k: x
            for k, x in detail.items()
            if k not in ("fingerprint", "content_header")
        },
    )
    atomic(folder / "checks" / (item["id"] + ".json"), detail)
    save(folder, v)
    return {"item": item}


def dispatch(action, r):
    if action == "assign":
        return assign(r)
    if action == "collections":
        import profile_collections

        suite_api.checked_person(r["person"])
        return profile_collections.summary(r["person"])
    if action == "list":
        suite_api.checked_person(r["person"])
        rows = []
        for p in sorted(
            (suite_api.ROOT / "Projects/Launcher" / r["person"]).glob(
                "intake_*/batch.json"
            ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:30]:
            try:
                rows.append(
                    {
                        k: v
                        for k, v in read(r["person"], p.parent.name).items()
                        if k in ("person", "job", "created", "phase", "total", "done")
                    }
                )
            except (OSError, ValueError):
                pass
        return {"jobs": rows}
    if action == "start":
        return start(r)
    if action == "read":
        return read(r["person"], r["job"])
    if action == "accept":
        return accept(r)
    if action == "cancel":
        (location(r["person"], r["job"]) / "abbrechen.request").touch()
        return {"requested": True}
    raise ValueError("Unknown batch preparation command.")
