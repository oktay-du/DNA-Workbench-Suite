import security_paths

"""Local, page-cited document retrieval. Extracted reports are unreviewed evidence."""
from pathlib import Path
import hashlib, re, shutil, uuid, datetime, collections
import family, source_store, profile_identity
import portable_json as json

TOPICS = {
    "lactose": ["lactose", "lactase", "laktose", "laktase"],
    "chromosomes": ["chromosome", "chromosom", "karyotype", "xx", "xy"],
    "sex": ["sex", "geschlecht"],
    "age": ["age", "alter", "birth", "geburt"],
    "health": ["health", "health", "diagnosis", "diagnose", "disease", "krankheit"],
    "fitness": ["fitness", "sport", "wellness"],
    "ancestry": ["ancestry", "ancestry", "ethnicity", "ethnie"],
}


def schema(db):
    db.executescript("""CREATE TABLE IF NOT EXISTS profile_documents(id TEXT PRIMARY KEY,person TEXT NOT NULL,name TEXT,path TEXT,sha256 TEXT,provider TEXT,report_date TEXT,kind TEXT,status TEXT,pages INTEGER,bytes INTEGER,mtime_ns INTEGER,updated TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS document_chunks(id TEXT PRIMARY KEY,document TEXT NOT NULL,page INTEGER,part INTEGER,text TEXT,topics TEXT);
    CREATE INDEX IF NOT EXISTS chunks_document ON document_chunks(document);
    CREATE TABLE IF NOT EXISTS profile_facts(id TEXT PRIMARY KEY,person TEXT,question TEXT,value TEXT,source_type TEXT,created TEXT);
    """)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def listing(person):
    profile_identity.ensure(person)
    with family.connect() as db:
        schema(db)
        rows = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM profile_documents WHERE person=? AND status!='deleted' ORDER BY updated DESC",
                (person,),
            )
        ]
    for r in rows:
        import portable_paths

        relocated = portable_paths.rebase(r["path"])
        if relocated != r["path"] and Path(relocated).is_file():
            with family.connect() as db:
                db.execute(
                    "UPDATE profile_documents SET path=? WHERE id=? AND person=?",
                    (relocated, r["id"], person),
                )
            r["path"] = relocated
        p = Path(r["path"])
        r["available"] = p.is_file()
        if r["available"]:
            s = p.stat()
            if s.st_size != r["bytes"] or s.st_mtime_ns != r["mtime_ns"]:
                r["status"] = "changed_since_index"
    return rows


def facts(person):
    with family.connect() as db:
        schema(db)
        return [
            dict(r)
            for r in db.execute(
                "SELECT * FROM profile_facts WHERE person=? ORDER BY created DESC",
                (person,),
            )
        ]


def add_fact(person, question, value):
    profile_identity.assert_writable(person)
    profile_identity.ensure(person)
    question = str(question).strip()
    value = str(value).strip()
    if not question or not value or len(question) > 300 or len(value) > 4000:
        raise ValueError("Question and answer required (300 / 4000 characters maximum)")
    record = {
        "id": uuid.uuid4().hex,
        "person": person,
        "question": question,
        "value": value,
        "source_type": "self_report",
        "created": profile_identity.now(),
    }
    with family.connect() as db:
        schema(db)
        db.execute(
            "INSERT INTO profile_facts VALUES(:id,:person,:question,:value,:source_type,:created)",
            record,
        )
    profile_identity.touch(person)
    return record


def topics(text):
    text = text.casefold()
    return [
        key
        for key, terms in TOPICS.items()
        if any(re.search(r"\b" + re.escape(w) + r"\w*", text) for w in terms)
    ]


def index_file(
    person,
    file,
    provider="",
    report_date="",
    kind="provider_report",
    copy=True,
    log=print,
):
    profile_identity.assert_writable(person)
    profile_identity.ensure(person)
    src = security_paths.input_file(file)
    if not src.is_file() or src.is_symlink():
        raise ValueError("Document file not found or not a regular file")
    if src.suffix.lower() not in (".pdf", ".txt", ".md", ".csv", ".tsv", ".json"):
        raise ValueError("Use PDF or a supported text/JSON/CSV report")
    if src.stat().st_size > 200 * 1024**2:
        raise ValueError(
            "Document limit: 200 MiB per PDF; raw genome files belong in source import"
        )
    if report_date:
        datetime.date.fromisoformat(report_date)
    sha = digest(src)
    with family.connect() as db:
        schema(db)
        prior = db.execute(
            "SELECT id FROM profile_documents WHERE person=? AND sha256=? AND kind=? AND status!='deleted'",
            (person, sha, kind),
        ).fetchone()
    if prior:
        return {"id": prior[0], "deduplicated": True}
    dest = src
    if copy:
        folder = source_store.profile_dir(person) / "Findings"
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / (
            uuid.uuid4().hex[:12]
            + "-"
            + source_store.safe_name(src.stem)
            + src.suffix.lower()
        )
        shutil.copyfile(src, dest)
        if digest(dest) != sha:
            raise ValueError("Document copy checksum mismatch; source preserved")
    elif not src.is_relative_to(source_store.ROOT.resolve()):
        raise ValueError("Analysis documents must be inside this workspace")
    pages = []
    notes = []
    status = "indexed"
    if src.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(dest), strict=False)
            if reader.is_encrypted:
                raise ValueError("Encrypted PDF: provide a decrypted local copy")
            count = len(reader.pages)
            if count > 500:
                notes.append("Only the first 500 pages were indexed")
            budget = 0
            for number, page in enumerate(reader.pages[:500], 1):
                try:
                    text = (page.extract_text() or "").strip()
                except Exception as e:
                    text = ""
                    notes.append(
                        "Page "
                        + str(number)
                        + " could not be extracted: "
                        + type(e).__name__
                    )
                if len(text) > 50000:
                    text = text[:50000]
                    notes.append(
                        "Page " + str(number) + " text truncated at 50,000 characters"
                    )
                if budget + len(text) > 1000000:
                    notes.append("Text index capped at 1,000,000 characters")
                    break
                budget += len(text)
                pages.append((number, text))
            if not any(t for _, t in pages):
                status = "ocr_required"
                notes.append(
                    "No extractable text. Image-only/scanned PDF needs local OCR; it was not read successfully."
                )
        except ImportError:
            status = "reader_required"
            notes.append("Install the optional document-reader module and reindex")
        except Exception as e:
            status = "extraction_failed"
            notes.append(str(e)[:500])
    else:
        if dest.stat().st_size > 5 * 1024**2:
            status = "too_large_for_text_index"
            notes.append("Text report exceeds 5 MiB; retained without text indexing")
        else:
            pages = [
                (1, dest.read_text(encoding="utf-8-sig", errors="replace")[:1000000])
            ]
    id = uuid.uuid4().hex
    s = dest.stat()
    stamp = profile_identity.now()
    record = dict(
        id=id,
        person=person,
        name=src.name,
        path=str(dest),
        sha256=sha,
        provider=str(provider)[:200],
        report_date=report_date,
        kind=kind,
        status=status,
        pages=len(pages),
        bytes=s.st_size,
        mtime_ns=s.st_mtime_ns,
        updated=stamp,
        notes="; ".join(notes),
    )
    chunks = []
    for page, text in pages:
        for i, start in enumerate(range(0, len(text), 1000)):
            chunk = text[max(0, start - 120) : start + 1000]
            if chunk.strip():
                chunks.append(
                    (uuid.uuid4().hex, id, page, i, chunk, json.dumps(topics(chunk)))
                )
    with family.connect() as db:
        schema(db)
        db.execute(
            "INSERT INTO profile_documents VALUES(:id,:person,:name,:path,:sha256,:provider,:report_date,:kind,:status,:pages,:bytes,:mtime_ns,:updated,:notes)",
            record,
        )
        db.executemany("INSERT INTO document_chunks VALUES(?,?,?,?,?,?)", chunks)
    profile_identity.touch(person)
    log(src.name + ": " + status + " · " + str(len(chunks)) + " cited passages")
    return record


def reindex(person, id, log=print):
    row = next((r for r in listing(person) if r["id"] == id), None)
    if not row:
        raise ValueError("Document does not belong to selected profile")
    # Keep the previous record until successful extraction, even if the PDF has changed.
    old = id
    with family.connect() as db:
        schema(db)
        db.execute(
            "UPDATE profile_documents SET kind=? WHERE id=?",
            ("superseded:" + row["kind"], id),
        )
    try:
        r = index_file(
            person,
            row["path"],
            row["provider"],
            row["report_date"],
            row["kind"],
            copy=False,
            log=log,
        )
    except Exception:
        with family.connect() as db:
            db.execute(
                "UPDATE profile_documents SET kind=? WHERE id=?", (row["kind"], old)
            )
        raise
    return r


def scan_results(person, log=print):
    import suite_api

    out = []
    count = 0
    for job in suite_api.jobs(person):
        if job.get("status") != "Complete" or job.get("task", "").startswith(
            "profile_"
        ):
            continue
        base = suite_api.job_path(person, job["job"]) / "Results"
        for path in sorted(base.rglob("*")):
            if count >= 300:
                return {"documents": out, "truncated": True}
            if (
                not path.is_file()
                or path.is_symlink()
                or path.suffix.lower()
                not in (".pdf", ".txt", ".csv", ".tsv", ".json", ".md")
                or path.stat().st_size > 5 * 1024**2
            ):
                continue
            out.append(
                index_file(
                    person,
                    path,
                    "Suite analysis · " + str(job.get("task")),
                    str(job.get("finished", ""))[:10],
                    kind="analysis_output",
                    copy=False,
                    log=log,
                )
            )
            count += 1
    return {"documents": out, "truncated": False}


def search(person, query, limit=8):
    docs = {
        r["id"]: r
        for r in listing(person)
        if r["status"] == "indexed" and not r["kind"].startswith("superseded:")
    }
    words = set(re.findall(r"[\w]{2,}", str(query).casefold()))
    for key, terms in TOPICS.items():
        if any(any(term in w for w in words) for term in terms):
            words.update(terms)
    found = []
    with family.connect() as db:
        schema(db)
        for row in db.execute(
            "SELECT c.* FROM document_chunks c JOIN profile_documents d ON c.document=d.id WHERE d.person=?",
            (person,),
        ):
            if row["document"] not in docs:
                continue
            score = sum(min(4, row["text"].casefold().count(w)) for w in words)
            if score:
                d = docs[row["document"]]
                found.append(
                    {
                        "document": d["id"],
                        "name": d["name"],
                        "provider": d["provider"],
                        "report_date": d["report_date"],
                        "kind": d["kind"],
                        "review": (
                            "unreviewed_machine_translation"
                            if d["kind"].startswith("machine_translation")
                            else "unreviewed_ocr"
                            if d["kind"] == "ocr_extraction"
                            else "unreviewed_analysis_output"
                            if d["kind"] in ("analysis_output", "calculated_research")
                            else "unreviewed_extraction"
                        ),
                        "page": row["page"],
                        "quote": row["text"],
                        "sha256": d["sha256"],
                        "processing_notes": d.get("notes", ""),
                        "score": score,
                    }
                )
    return sorted(found, key=lambda r: r["score"], reverse=True)[
        : max(1, min(int(limit), 20))
    ]


def analysis_passages(person, query, limit=4):
    """Read-only retrieval of small completed analysis artifacts; no new analysis is run."""
    if not query:
        return []
    import suite_api

    words = set(re.findall(r"\w{3,}", str(query).casefold())) - {
        "does",
        "this",
        "person",
        "have",
        "what",
        "which",
        "about",
        "the",
        "and",
        "how",
        "is:",
        "hat",
        "diese",
        "person",
        "welche",
        "welchen",
        "over",
        "gibt",
        "laut",
    }
    for key, terms in TOPICS.items():
        if any(any(t in w for w in words) for t in terms):
            words.update(terms)
    out = []
    examined = 0
    budget = 0
    for job in suite_api.jobs(person):
        if job.get("status") != "Complete" or job.get("task", "").startswith(
            "profile_"
        ):
            continue
        base = (suite_api.job_path(person, job["job"]) / "Results").resolve()
        for p in base.rglob("*"):
            if examined >= 100 or budget >= 2 * 1024**2:
                break
            if (
                not p.is_file()
                or p.is_symlink()
                or not p.resolve().is_relative_to(base)
                or p.suffix.lower() not in (".txt", ".json", ".csv", ".tsv", ".md")
                or p.stat().st_size > 5 * 1024**2
            ):
                continue
            examined += 1
            with p.open("rb") as f:
                raw = f.read(131072)
            budget += len(raw)
            text = raw.decode("utf-8", errors="replace")
            lower = text.casefold()
            terms = [
                w for w in words if re.search(r"\b" + re.escape(w) + r"\w*", lower)
            ]
            if not terms:
                continue
            start = max(0, min(lower.index(w) for w in terms) - 200)
            snippet = text[start : start + 1100]
            out.append(
                {
                    "document": "job:" + job["job"] + ":" + p.name,
                    "name": p.name,
                    "provider": "Suite analysis · " + str(job["task"]),
                    "report_date": str(job.get("finished", ""))[:10],
                    "kind": "analysis_output",
                    "review": "unreviewed_analysis_output",
                    "page": "text / " + job["job"],
                    "quote": snippet,
                    "sha256": digest(p),
                    "score": len(terms),
                    "truncated_search": p.stat().st_size > len(raw),
                }
            )
        if examined >= 100 or budget >= 2 * 1024**2:
            break
    return sorted(out, key=lambda r: r["score"], reverse=True)[:limit]


def overview(person):
    documents = listing(person)
    questions = collections.Counter()
    with family.connect() as db:
        schema(db)
        for row in db.execute(
            "SELECT c.topics FROM document_chunks c JOIN profile_documents d ON c.document=d.id WHERE d.person=? AND d.status='indexed' AND d.kind NOT LIKE ?",
            (person, "superseded:%"),
        ):
            questions.update(json.loads(row[0]))
    return {
        "documents": documents,
        "facts": facts(person),
        "topics": dict(questions),
        "notice": "Extracted passages are unreviewed report statements, not diagnoses. Analysis outputs are not automatically clinical evidence. Conflicts remain visible.",
    }


def evidence(person, query):
    import person_profile

    p = person_profile.read(person)
    age = None
    if p.get("birth_date"):
        born = datetime.date.fromisoformat(p["birth_date"])
        today = datetime.date.today()
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
    return {
        "profile_uuid": p["identity"]["uuid"],
        "self_reported_age": age if age is None or age >= 0 else None,
        "self_reported_chromosomes": p.get("chromosomes", "Unknown"),
        "manual_facts": facts(person)[:40],
        "passages": search(person, query, 4) + analysis_passages(person, query),
        "weighting": [
            "Clinical confirmation, if explicitly documented and reviewed, addresses a different question from a genotype-based susceptibility prediction.",
            "Evaluate identity, method, coverage, review status, date and the precise question; neither a newer PDF nor a raw genotype is automatically more authoritative.",
            "Manual entries are self-reports. Extracted PDFs are unreviewed quotations. Keep contradictory sources side by side; do not decide a diagnosis by majority vote.",
        ],
    }
