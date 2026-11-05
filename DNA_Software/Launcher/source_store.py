"""Per-person SQLite source library and optional source-preserving VCF index."""

from pathlib import Path
import sqlite3, os, re, uuid, hashlib, datetime, zipfile, gzip
import portable_json as json
import security_paths

ROOT = Path(__file__).resolve().parents[2]
NOW = lambda: datetime.datetime.now().astimezone().isoformat()


def folder(person):
    return security_paths.contained(
        ROOT / "Projects/Databases", security_paths.identifier(person)
    )


def connect(person):
    path = folder(person)
    path.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path / "sources.sqlite", timeout=30)
    __import__("layout_migration").database(db, ROOT)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,provider TEXT NOT NULL,label TEXT NOT NULL,declared_build TEXT,measurement TEXT,note TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS blobs(sha256 TEXT PRIMARY KEY,stored_rel TEXT NOT NULL,bytes INTEGER NOT NULL,kind TEXT,detected_build TEXT,members TEXT);
    CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,batch_id TEXT NOT NULL REFERENCES batches(id),sha256 TEXT NOT NULL REFERENCES blobs(sha256),original_name TEXT,original_path TEXT,index_state TEXT DEFAULT "Non-indexed",call_count INTEGER DEFAULT 0,created TEXT);
    CREATE INDEX IF NOT EXISTS files_batch ON files(batch_id);
    CREATE TABLE IF NOT EXISTS calls(file_id TEXT NOT NULL REFERENCES files(id),sample TEXT,build TEXT,chrom TEXT,pos INTEGER,ref TEXT,alt TEXT,gt TEXT,dp TEXT,gq TEXT,filter TEXT,info_dp TEXT);
    CREATE INDEX IF NOT EXISTS calls_region ON calls(build,chrom,pos);
    CREATE INDEX IF NOT EXISTS calls_file ON calls(file_id);
    CREATE TABLE IF NOT EXISTS inspections(sha256 TEXT PRIMARY KEY,payload TEXT NOT NULL,checked TEXT);
    CREATE TABLE IF NOT EXISTS derived_profile(key TEXT PRIMARY KEY,payload TEXT,updated TEXT);
    CREATE TABLE IF NOT EXISTS file_tombstones(file_id TEXT PRIMARY KEY,deleted TEXT,operation TEXT);
    CREATE TABLE IF NOT EXISTS source_metadata(file_id TEXT PRIMARY KEY,payload TEXT,updated TEXT);
    CREATE TABLE IF NOT EXISTS archive_payloads(parent_sha256 TEXT,file_id TEXT PRIMARY KEY,member TEXT,created TEXT);
    """)
    db.commit()
    return db


def classify(name):
    n = name.lower()
    if n.endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")):
        return "Image"
    if n.endswith((".ged", ".gedcom")):
        return "GEDCOM"
    for suffix, kind in [
        (".vcf.gz", "VCF"),
        (".vcf.bgz", "VCF"),
        (".vcf", "VCF"),
        (".bcf", "BCF"),
        (".cram", "CRAM"),
        (".bam", "BAM"),
        (".fastq.gz", "FASTQ"),
        (".fq.gz", "FASTQ"),
        (".fastq", "FASTQ"),
        (".fq", "FASTQ"),
        (".fai", "Index"),
        (".tbi", "Index"),
        (".bai", "Index"),
        (".crai", "Index"),
        (".csi", "Index"),
        (".pdf", "Report"),
        (".zip", "Archive"),
        (".csv", "Chip / table"),
        (".txt", "Raw data / text"),
    ]:
        if n.endswith(suffix):
            return kind
    if n.endswith((".fa", ".fasta", ".fna", ".fa.gz", ".fasta.gz", ".fna.gz")):
        return "FASTA"
    if n.endswith(".json"):
        return "JSON/report or pedigree"
    if n.endswith((".csv.gz", ".csv.bgz")):
        return "Chip / table"
    if n.endswith((".txt.gz", ".txt.bgz")):
        return "Raw data / text"
    if n.endswith(
        (
            ".tar",
            ".tgz",
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
            ".tbz2",
            ".txz",
            ".7z",
            ".rar",
            ".gz",
            ".bgz",
            ".bz2",
            ".xz",
            ".zst",
        )
    ):
        return "Archive"
    return "Other"


def build_hint(path):
    if classify(path.name) not in ["VCF", "Raw data / text", "Chip / table"]:
        return ""
    try:
        op = gzip.open if str(path).endswith((".gz", ".bgz")) else open
        with op(path, "rt", encoding="utf-8-sig", errors="replace") as f:
            text = f.read(25000).lower()
        if re.search(r"grch38|hg38|hs38|build[ =:]*(?:38)", text):
            return "GRCh38"
        if re.search(r"grch37|hg19|hs37|build[ =:]*(?:37)", text):
            return "GRCh37"
    except (OSError, ValueError, EOFError):
        return ""
    return ""


def listing(person):
    db = connect(person)
    db.row_factory = sqlite3.Row
    __import__("layout_migration").database(db, ROOT)
    rows = []
    for row in db.execute(
        """SELECT f.id,f.batch_id,b.provider,b.label,b.declared_build,b.measurement,b.created,f.original_name,f.original_path,f.index_state,f.call_count,o.sha256,o.stored_rel,o.bytes,o.kind,o.detected_build FROM files f JOIN batches b ON f.batch_id=b.id JOIN blobs o ON f.sha256=o.sha256 WHERE NOT EXISTS(SELECT 1 FROM file_tombstones t WHERE t.file_id=f.id) ORDER BY b.created DESC,f.original_name"""
    ):
        r = dict(row)
        r["path"] = str(ROOT / r["stored_rel"])
        r["build"] = r["detected_build"] or r["declared_build"] or "Unknown"
        r["available"] = Path(r["path"]).is_file()
        r["origin"] = "imported"
        r["lifecycle"] = "imported"
        r["comparison"] = {}
        container = db.execute(
            "SELECT parent_sha256,member FROM archive_payloads WHERE file_id=?",
            (r["id"],),
        ).fetchone()
        if container:
            r.update(
                container_sha256=container[0],
                container_member=container[1],
                independent_measurement=False,
            )
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='file_annotations'"
        ).fetchone():
            annotation = db.execute(
                "SELECT origin,lifecycle,payload FROM file_annotations WHERE file_id=?",
                (r["id"],),
            ).fetchone()
            if annotation:
                r.update(
                    origin=annotation[0],
                    lifecycle=annotation[1],
                    comparison=json.loads(annotation[2]),
                )
        inspection = db.execute(
            "SELECT payload FROM inspections WHERE sha256=?", (r["sha256"],)
        ).fetchone()
        detail = json.loads(inspection[0]) if inspection else {}
        if detail:
            from inspector import chromosome_hint

            detail.setdefault("profile", {})["chromosomes"] = chromosome_hint(detail)
            if detail.get("measurement", "Unknown") != "Unknown":
                r["measurement"] = detail["measurement"]
        r["build"] = (
            detail.get("build")
            or r["detected_build"]
            or r["declared_build"]
            or "Unknown"
        )
        r["qc_review_required"] = bool(detail.get("manual_review_required"))
        r["qc_color"] = detail.get("color", "orange")
        r["qc_verified"] = detail.get("verified", False)
        r["qc_points"] = detail.get("qc_supported_points")
        r["called_points"] = detail.get("called_points", 0)
        r["qc_issues"] = "\n".join(detail.get("issues", []))
        r["detected_provider"] = detail.get("provider", "Unknown")
        r["producer"] = detail.get("producer", "Unknown")
        r["profile"] = detail.get("profile", {})
        r["versions"] = detail.get("versions", [])
        r["declared_version"] = ""
        perfile = db.execute(
            "SELECT payload FROM source_metadata WHERE file_id=?", (r["id"],)
        ).fetchone()
        if perfile:
            source_meta = json.loads(perfile[0])
            r["declared_version"] = source_meta.get("declared_version", "")
            r["measurement"] = source_meta.get("measurement") or r["measurement"]
            r["metadata_provenance"] = source_meta.get("provenance", "user-declared")
            r["source_root_sha256"] = (
                source_meta.get("source_root_sha256")
                or r.get("container_sha256")
                or r["sha256"]
            )
            r["derived_operation"] = source_meta.get("operation")
        r["data_scope"] = detail.get("data_scope", {})
        r["scope_summary"] = r["data_scope"].get(
            "summary", "Not yet checked with the data scope check"
        )
        analysis = r["comparison"].get("source", {})
        pairs = r["comparison"].get("comparisons", [])
        r["comparison_status"] = (
            "Examining conflicts"
            if any(p.get("status") == "review-conflicts" for p in pairs)
            else "SNP compliance supported"
            if any(p.get("status") == "consistent" for p in pairs)
            else "Not enough comparison yet"
        )
        if analysis.get("status") == "analyzed":
            r["called_points"] = analysis.get("called", r["called_points"])
            r["qc_points"] = (
                analysis.get("qc_supported")
                if analysis.get("stats", {}).get("quality_fields")
                else None
            )
        if analysis.get("status") == "excluded":
            r["qc_color"] = "red"
            r["qc_verified"] = False
        rows.append(r)
    db.close()
    return rows


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")[:90] or "Unknown"


def profile_dir(person):
    folder(person)  # validate the stable profile ID, never an editable display name
    return security_paths.contained(
        ROOT / "Profiles", security_paths.identifier(person)
    )


def import_batch(
    person,
    files,
    provider,
    label,
    build="",
    measurement="Unknown",
    note="",
    log=print,
    cancel=lambda: False,
    expected=None,
    storage_mode="copy",
    version="",
):
    import profile_identity

    profile_identity.assert_writable(person)
    if storage_mode not in ("move", "copy"):
        raise ValueError("Select Move or Copy import type.")
    db = connect(person)
    batch = uuid.uuid4().hex
    label = label or "Import " + datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    db.execute(
        "CREATE TABLE IF NOT EXISTS file_operations(file_id TEXT PRIMARY KEY,source TEXT,target TEXT,requested TEXT,actual TEXT,status TEXT,sha256 TEXT,created TEXT)"
    )
    db.execute(
        "INSERT INTO batches VALUES(?,?,?,?,?,?,?)",
        (batch, provider, label, build, measurement, note, NOW()),
    )
    db.commit()
    archive = (profile_dir(person) / "Sources").resolve()
    target = (
        archive
        / safe_name(provider)
        / "Imports"
        / (
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            + "_"
            + safe_name(version or "version-unknown")
            + "_"
            + safe_name(build or "build-unknown")
            + "_"
            + batch[:8]
        )
    )
    added = []
    operations = []
    # A unique batch directory isolates concurrent imports. Number the original
    # names; preserve matching sidecar stems so common genome viewers find them.
    planned = {}
    sequence = 0
    resolved = [Path(value).resolve() for value in files]
    for src in resolved:
        managed = (ROOT / "Profiles").resolve()
        if src.is_relative_to(managed) and src.relative_to(managed).parts[0] != person:
            raise ValueError(
                "Source belongs to another profile; review the assignment explicitly."
            )
        if src.suffix.lower() in (".tbi", ".csi", ".bai", ".crai"):
            continue
        sequence += 1
        planned[str(src)] = f"{sequence:03d}-" + src.name
    for src in resolved:
        if str(src) in planned:
            continue
        parent = src.with_suffix("")
        if str(parent) not in planned and src.suffix.lower() in (".bai", ".crai"):
            parent = src.with_suffix(
                ".bam" if src.suffix.lower() == ".bai" else ".cram"
            )
        if str(parent) in planned:
            planned[str(src)] = planned[str(parent)].split("-", 1)[0] + "-" + src.name
        else:
            sequence += 1
            planned[str(src)] = f"{sequence:03d}-" + src.name

    def fingerprint(path):
        stat = path.stat()
        return stat.st_size, stat.st_mtime_ns

    def checksum(path):
        h = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                if cancel():
                    raise InterruptedError(
                        "Import cancelled; sources are not removed unchecked."
                    )
                block = stream.read(8 * 1024 * 1024)
                if not block:
                    break
                h.update(block)
        return h.hexdigest()

    try:
        for i, value in enumerate(files, 1):
            if cancel():
                raise InterruptedError(
                    "Import aborted. Files already registered remain traceable."
                )
            src = Path(value).resolve()
            if not src.is_file():
                raise ValueError("File missing:" + str(src))
            origin = (ROOT / "DNA_Archiv/01_Originaldownloads").resolve()
            if (
                src.is_relative_to(origin)
                and src.relative_to(origin).parts[0] != person
            ):
                raise ValueError(
                    "According to the archive path, the file belongs to another person:"
                    + str(src)
                )
            inside = src.is_relative_to(archive)
            before = fingerprint(src)
            count = before[0]
            log(
                "Import "
                + str(i)
                + "/"
                + str(len(files))
                + ": "
                + src.name
                + " · "
                + storage_mode
            )
            digest = checksum(src)
            if fingerprint(src) != before:
                raise ValueError("Source changed during the test:" + src.name)
            if expected and expected.get(str(src)) != digest:
                raise ValueError(
                    "Checksum changed since the preliminary check." + src.name
                )
            existing = db.execute(
                "SELECT stored_rel FROM blobs WHERE sha256=?", (digest,)
            ).fetchone()
            renamed = False
            new_blob = False
            if existing:
                stored = (ROOT / existing[0]).resolve()
                if not stored.is_relative_to(ROOT.resolve()) or not stored.is_file():
                    deleted = (
                        db.execute(
                            "SELECT count(*) FROM files f WHERE f.sha256=? AND NOT EXISTS(SELECT 1 FROM file_tombstones t WHERE t.file_id=f.id)",
                            (digest,),
                        ).fetchone()[0]
                        == 0
                    )
                    if deleted:
                        raise ValueError(
                            "Identical source is in the profile paper basket. Restore in the profile file manager; no second genome copy is created."
                        )
                    raise ValueError(
                        "Registered storage path is missing or out of suite."
                    )
                if stored != src and (
                    stored.stat().st_size != count or checksum(stored) != digest
                ):
                    raise ValueError(
                        "Saved identical file deviates from the checksum register; source remains."
                    )
                actual = "existing"
                log("Identical bytes exist; no second archival copy created.")
            elif inside:
                stored = src
                actual = "in-place"
                new_blob = True
            else:
                target.mkdir(parents=True, exist_ok=True)
                stored = target / planned[str(src)]
                new_blob = True
                if stored.exists():
                    raise ValueError(
                        "Goal already exists; no overwriting:" + str(stored)
                    )
                if storage_mode == "move" and src.stat().st_dev == target.stat().st_dev:
                    src.replace(stored)
                    renamed = True
                    actual = "move"
                    try:
                        if fingerprint(stored) != before or checksum(stored) != digest:
                            raise ValueError(
                                "File changed after moving; import stopped."
                            )
                    except BaseException:
                        if not src.exists():
                            stored.replace(src)
                        raise
                else:
                    temp = target / (uuid.uuid4().hex + ".importing")
                    try:
                        with src.open("rb") as inp, temp.open("xb") as out:
                            while True:
                                if cancel():
                                    raise InterruptedError(
                                        "Import abgebrochen; Quelldatei erhalten."
                                    )
                                block = inp.read(8 * 1024 * 1024)
                                if not block:
                                    break
                                out.write(block)
                            out.flush()
                            os.fsync(out.fileno())
                        if fingerprint(src) != before or checksum(temp) != digest:
                            raise ValueError("Copy does not match the verified source.")
                        temp.replace(stored)
                        actual = (
                            "copy-delete-pending" if storage_mode == "move" else "copy"
                        )
                    finally:
                        if temp.exists():
                            temp.unlink()
            fileid = uuid.uuid4().hex
            try:
                if new_blob:
                    members = []
                    if zipfile.is_zipfile(stored):
                        with zipfile.ZipFile(stored) as z:
                            members = [
                                {"name": x.filename, "bytes": x.file_size}
                                for x in z.infolist()
                            ]
                    db.execute(
                        "INSERT INTO blobs VALUES(?,?,?,?,?,?)",
                        (
                            digest,
                            str(stored.relative_to(ROOT.resolve())),
                            count,
                            classify(src.name),
                            build_hint(stored),
                            json.dumps(members, ensure_ascii=False),
                        ),
                    )
                db.execute(
                    "INSERT INTO files(id,batch_id,sha256,original_name,original_path,created) VALUES(?,?,?,?,?,?)",
                    (fileid, batch, digest, src.name, str(src), NOW()),
                )
                db.execute(
                    "INSERT INTO file_operations VALUES(?,?,?,?,?,?,?,?)",
                    (
                        fileid,
                        str(src),
                        str(stored),
                        storage_mode,
                        actual,
                        "registered",
                        digest,
                        NOW(),
                    ),
                )
                db.commit()
            except BaseException:
                db.rollback()
                if renamed and stored.exists() and not src.exists():
                    stored.replace(src)
                raise
            status = "complete"
            receipt = None
            if storage_mode == "move" and src != stored:
                receipt = src.with_name(
                    src.name + "." + fileid[:8] + ".dna-source.json"
                )
                try:
                    with receipt.open("x", encoding="utf-8") as stream:
                        json.dump(
                            {
                                "schema": "dna-source-location-1",
                                "person": person,
                                "provider": provider,
                                "batch": batch,
                                "source_id": fileid,
                                "original_name": src.name,
                                "original_path": str(src),
                                "stored_name": stored.name,
                                "target": str(stored),
                                "suite_root": str(ROOT.resolve()),
                                "target_relative": str(
                                    stored.relative_to(ROOT.resolve())
                                ),
                                "sha256": digest,
                                "created": NOW(),
                                "note": "Location receipt only, not DNA data. Identical bytes share one stored payload.",
                            },
                            stream,
                            ensure_ascii=False,
                            indent=2,
                        )
                except OSError as error:
                    receipt = None
                    log("  Location receipt could not be written: " + str(error))
            status = "complete"
            if storage_mode == "move" and not inside and not renamed and src != stored:
                try:
                    if fingerprint(src) != before or checksum(src) != digest:
                        raise ValueError("Source changed after import; not removed.")
                    # Destination is durable and registered before the source is removed.
                    if checksum(stored) != digest:
                        raise ValueError("Target changed; source not removed.")
                    src.unlink()
                    actual = "deduplicated-move" if existing else "cross-volume-move"
                except (OSError, ValueError, InterruptedError) as error:
                    status = "source-kept"
                    log("Source, as a precautionary measure:" + str(error))
            db.execute(
                "UPDATE file_operations SET actual=?,status=? WHERE file_id=?",
                (actual, status, fileid),
            )
            db.commit()
            operations.append(
                {
                    "source": str(src),
                    "target": str(stored),
                    "requested": storage_mode,
                    "actual": actual,
                    "status": status,
                    "receipt": str(receipt) if receipt else None,
                }
            )
            added.append(fileid)
        queued = False
        if added:
            try:
                import profile_pipeline

                queued = profile_pipeline.note_new_sources(person)
            except (OSError, ValueError, sqlite3.Error) as error:
                log("Indication of available renewal failed:" + str(error))
        return {
            "batch_id": batch,
            "provider": provider,
            "label": label,
            "files_registered": len(added),
            "database": str(folder(person) / "sources.sqlite"),
            "ids": added,
            "storage_mode": storage_mode,
            "operations": operations,
            "best_selection_renewal_available": queued,
        }
    finally:
        db.close()


def index_archive(person, log=print, cancel=lambda: False):
    raise ValueError(
        "Automatic archive indexing has been removed. Select files/folders explicitly in Batch file preparation."
    )


def index_vcfs(person, paths, fallback="", log=print, cancel=lambda: False):
    registered = listing(person)
    db = connect(person)
    summary = []
    for value in paths:
        path = Path(value).resolve()
        row = next((r for r in registered if Path(r["path"]).resolve() == path), None)
        if not row:
            raise ValueError(
                "Please import this file into this person’s source management first:"
                + str(path)
            )
        if row["kind"] != "VCF":
            raise ValueError(
                "Variant indexing supports VCF/VCF.gz. Chip/BCF data first convert in a controlled manner:"
                + path.name
            )
        if row["index_state"] == "Complete":
            log("Already fully indexed:" + path.name)
            continue
        if (
            row["detected_build"]
            and fallback in ["GRCh37", "GRCh38"]
            and row["detected_build"] != fallback
        ):
            raise ValueError("Abweichender Build: " + path.name)
        build = row["detected_build"] or row["declared_build"] or fallback or "Unknown"
        fid = row["id"]
        db.execute("DELETE FROM calls WHERE file_id=?", (fid,))
        db.execute(
            "UPDATE files SET index_state=?,call_count=0 WHERE id=?",
            ("Incomplete", fid),
        )
        db.commit()
        op = gzip.open if str(path).endswith((".gz", ".bgz")) else open
        records = 0
        batch = []
        samples = []
        log("VCF indizieren: " + path.name + " · " + build)
        with op(path, "rt", encoding="utf-8-sig", errors="strict") as f:
            for line in f:
                if cancel():
                    raise InterruptedError(
                        "Source and already written subset remain marked separately."
                    )
                if line.startswith("#CHROM"):
                    samples = line.rstrip().split("\t")[9:]
                    continue
                if line.startswith("#") or not line.strip():
                    continue
                cols = line.rstrip().split("\t")
                if len(cols) < 8:
                    raise ValueError("Invalid VCF line.")
                fmt = cols[8].split(":") if len(cols) > 8 else []
                info = {
                    kv.split("=", 1)[0]: kv.split("=", 1)[1]
                    for kv in cols[7].split(";")
                    if "=" in kv
                }
                samplevalues = cols[9:] if samples else [""]
                for i, raw in enumerate(samplevalues):
                    data = dict(zip(fmt, raw.split(":")))
                    batch.append(
                        (
                            fid,
                            samples[i] if samples else "",
                            build,
                            cols[0],
                            int(cols[1]),
                            cols[3],
                            cols[4],
                            data.get("GT"),
                            data.get("DP"),
                            data.get("GQ"),
                            cols[6],
                            info.get("DP"),
                        )
                    )
                records += 1
                if len(batch) >= 10000:
                    db.executemany(
                        "INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", batch
                    )
                    batch = []
                    db.execute(
                        "UPDATE files SET call_count=? WHERE id=?", (records, fid)
                    )
                    db.commit()
                    if records % 100000 == 0:
                        log("  " + str(records) + " Variantenzeilen gespeichert")
        if batch:
            db.executemany("INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", batch)
        db.execute(
            "UPDATE files SET index_state=?,call_count=? WHERE id=?",
            ("Complete", records, fid),
        )
        db.commit()
        summary.append({"file": path.name, "variant_rows": records, "build": build})
    db.close()
    return summary


def new_person(label):
    if not label or len(label) > 160:
        raise ValueError("Profile name required (maximum 160 characters)")
    person = "P_" + uuid.uuid4().hex
    (profile_dir(person) / "Sources").mkdir(parents=True)
    connect(person).close()
    return person


def profile(person):
    rows = listing(person)
    db = connect(person)
    derived = {
        r[0]: json.loads(r[1])
        for r in db.execute("SELECT key,payload FROM derived_profile")
    }
    db.close()
    text = [
        "PERSON " + person,
        "",
        "Sources:"
        + str(len(rows))
        + "Files for:"
        + str(len({r["provider"] for r in rows}))
        + " Anbietern / Plattformen.",
        "",
        "AUTOMATISCH AUS DATEN ABGELEITET",
    ]
    signals = sorted(
        {
            r.get("profile", {}).get("chromosomes", "Undetermined")
            for r in rows
            if r.get("qc_color") not in ["red", "black"]
            and r.get("lifecycle") != "needs_review"
            and not r.get("qc_review_required")
        }
    )
    informative = [s for s in signals if s.startswith(("XX ", "XY "))]
    chromosome = "Undetermined"
    if len(informative) == 1:
        chromosome = informative[0]
    elif len(informative) > 1:
        chromosome += "(contradictory XX/XY references in the sources)"
    text += ["Chromosomen (XX / XY): " + chromosome]
    if derived.get("best_selection"):
        best = derived["best_selection"]
        text += [
            "",
            "AKTUELLE BEST SELECTION",
            best["build"] + " · " + str(best["snps"]) + " beobachtete SNPs",
            "XX-/XY-Screening dieser Auswahl: "
            + best.get("chromosomes_hint", "Undetermined"),
            best["status"],
        ]
        text += [
            "  "
            + r["provider"]
            + ": "
            + format(r["primary_percent"], ".1f")
            + "% lead,"
            + format(r["support_percent"], ".1f")
            + "% confirmatory"
            for r in best.get("providers", [])
        ]
    import family

    with family.connect() as graph:
        labels = {r[0]: r[1] for r in graph.execute("SELECT id,label FROM people")}
        relationships = [
            dict(r)
            for r in graph.execute(
                "SELECT * FROM links WHERE a=? OR b=?", (person, person)
            )
        ]
    text += ["", "FAMILY LINKS (documented, not genetically confirmed)"]
    for link in relationships:
        role = family.RELATION_LABELS.get(link["kind"], link["kind"])
        text.append(
            labels.get(link["a"], link["a"])
            + " · "
            + role
            + " · "
            + labels.get(link["b"], link["b"])
        )
    if not relationships:
        text.append("There are no links on the family page yet.")
    text += [
        "Maternal lineage: "
        + " ← ".join(labels.get(p, p) for p in family.lineage(person, "mother")),
        "Paternal lineage: "
        + " ← ".join(labels.get(p, p) for p in family.lineage(person, "father")),
        "",
    ]
    for key, title in [
        ("mt_haplogroup", "Maternal haplogroup"),
        ("y_haplogroup", "Paternal haplogroup"),
    ]:
        value = derived.get(key)
        text.append(
            title
            + ": "
            + (
                value.get("value", "Not determined")
                + " · "
                + value.get("status", "provisionally provisional")
                + "· Source:"
                + value.get("source", "")
                if value
                else "Evaluation via Haplogrep / yhaplo required."
            )
        )
    text += [
        "Blood type ABO / Rh: Not reliably determined. No clinically validated ABO / RHD evaluation module is set up.",
        "",
        "XX / XY is displayed as a preliminary data indication. Missing Y entries alone do not occupy XX; the marker check does not confirm a chromosome number.",
        "",
        "QUALITY FROM SOURCE",
    ]
    for r in rows:
        text += [
            "• "
            + r["provider"]
            + " / "
            + r["original_name"]
            + ": "
            + r["qc_color"]
            + " · "
            + str(r["called_points"])
            + " auslesbare Genotypen · QC-Punkte: "
            + str(
                r["qc_points"]
                if r["qc_points"] is not None
                else "Not occupied by DP/GQ"
            ),
            "  Datenumfang: " + r["scope_summary"],
        ]
    return {
        "person": person,
        "sources": len(rows),
        "derived": derived,
        "summary": "\n".join(text),
    }
