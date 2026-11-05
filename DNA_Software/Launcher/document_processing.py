from system_tools import windows_executable
import network_io

"""Local multilingual OCR and explicit-source-language translation of saved reports."""
from pathlib import Path, PurePosixPath
import csv, io, json, os, re, shutil, subprocess, sys, uuid, zipfile
import source_store, profile_documents, profile_identity, family
from portable_paths import distro_name

APP = Path(__file__).parent
LANGUAGES = {
    "en": "eng",
    "de": "deu",
    "tr": "tur",
    "fr": "fra",
    "es": "spa",
    "pl": "pol",
    "ru": "rus",
    "uk": "ukr",
    "ar": "ara",
}


def manifest():
    return json.loads((APP / "document-packages.json").read_text(encoding="utf-8-sig"))


def models_root():
    return source_store.ROOT / "DNA_Software/Models/DocumentTranslation"


def install_translation():
    lock = APP / "Locks/document-translation-windows.txt"
    target = source_store.ROOT / "DNA_Software/Windows/PythonPackages"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(target),
            "--upgrade",
            "--no-deps",
            "--require-hashes",
            "-r",
            str(lock),
        ],
        check=True,
    )
    installed = []
    cache = source_store.ROOT / "DNA_Software/Downloads/DocumentModels"
    cache.mkdir(parents=True, exist_ok=True)
    for m in manifest()["models"]:
        if m.get("enabled") is False:
            continue
        p = cache / m["filename"]
        if not p.is_file() or profile_documents.digest(p) != m["sha256"]:
            temp = p.with_suffix(".part")
            with (
                network_io.open_https(m["url"], timeout=120) as response,
                temp.open("wb") as stream,
            ):
                shutil.copyfileobj(response, stream, 1024**2)
            if profile_documents.digest(temp) != m["sha256"]:
                raise ValueError("Translation model checksum mismatch")
            temp.replace(p)
        dest = models_root() / m["filename"].removesuffix(".argosmodel")
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(p) as archive:
            prefix = PurePosixPath(
                next(
                    n
                    for n in archive.namelist()
                    if n.endswith("/metadata.json") or n == "metadata.json"
                )
            ).parent
            for info in archive.infolist():
                relative = PurePosixPath(info.filename).relative_to(prefix)
                out = (dest / str(relative)).resolve()
                if (
                    not out.is_relative_to(dest.resolve())
                    or info.external_attr >> 16 & 0o170000 == 0o120000
                ):
                    raise ValueError("Unsafe translation package path")
                if info.is_dir():
                    out.mkdir(parents=True, exist_ok=True)
                else:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as src, out.open("wb") as dst:
                        shutil.copyfileobj(src, dst, 1024**2)
        (dest / "verified-package.json").write_text(
            json.dumps(m, indent=2), encoding="utf-8"
        )
        installed.append(m["filename"])
    return {"installed": installed, "location": str(models_root())}


def translate(text, source, target):
    if source == target:
        return text
    if source == "ar":
        raise ValueError(
            "Arabic report translation is disabled: the model failed a medical-term smoke test. Arabic OCR remains available."
        )
    if source != "en" and target != "en":
        return translate(translate(text, source, "en"), "en", target)
    import ctranslate2, sentencepiece

    m = next(
        (m for m in manifest()["models"] if m["from"] == source and m["to"] == target),
        None,
    )
    if not m:
        raise ValueError(
            "No installed translation model for " + source + " to " + target
        )
    folder = models_root() / m["filename"].removesuffix(".argosmodel")
    if not (folder / "verified-package.json").is_file():
        raise ValueError("Install document translation models first")
    if (folder / "sentencepiece.model").is_file():
        processor = sentencepiece.SentencePieceProcessor(
            model_file=str(folder / "sentencepiece.model")
        )
        encode = lambda text: processor.encode(text, out_type=str)
    elif (folder / "bpe.model").is_file():
        from argostranslate.tokenizer import BPETokenizer

        processor = BPETokenizer(folder / "bpe.model", source, target)
        encode = processor.encode
    else:
        raise ValueError("Translation tokenizer missing; repair model installation")
    translator = ctranslate2.Translator(
        str(folder / "model"),
        device="cpu",
        compute_type="int8",
        inter_threads=1,
        intra_threads=min(4, os.cpu_count() or 2),
    )
    # Bounded sentence/line chunks avoid context truncation; no generative summarisation.
    chunks = []
    for line in text.splitlines():
        if not line.strip():
            chunks.append("")
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            words = sentence.split()
            for start in range(0, len(words), 100):
                chunks.append(" ".join(words[start : start + 100]))
    nonempty = [encode(c) for c in chunks if c]
    results = translator.translate_batch(
        nonempty, beam_size=4, replace_unknowns=True, max_decoding_length=512
    )
    decoded = iter(
        processor.decode(r.hypotheses[0]).replace("▁", " ").replace("_", " ")
        for r in results
    )
    return "\n".join(next(decoded) if c else "" for c in chunks)


def linux_path(p):
    p = Path(p).resolve()
    if len(p.drive) != 2:
        raise ValueError("OCR needs a local Windows drive")
    return "/mnt/" + p.drive[0].lower() + "/" + p.as_posix()[3:]


def wsl(*args, timeout=120):
    p = subprocess.run(
        [
            windows_executable("wsl.exe"),
            "-d",
            distro_name(source_store.ROOT),
            "-u",
            "dna",
            "--",
            *args,
        ],
        capture_output=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if p.returncode:
        raise RuntimeError(
            p.stderr.decode("utf-8", errors="replace")[-2000:]
            or "OCR dependency unavailable; install document OCR"
        )
    return p.stdout.decode("utf-8", errors="replace")


def ocr_pages(path, folder, languages, log=print, cancel=lambda: False):
    from pypdf import PdfReader

    if not languages or set(languages) - set(LANGUAGES):
        raise ValueError("Select supported OCR languages")
    count = len(PdfReader(str(path)).pages)
    if count > 100:
        raise ValueError(
            "OCR limit is 100 pages per report; split a larger report first"
        )
    available = wsl("tesseract", "--list-langs")
    codes = [LANGUAGES[l] for l in languages]
    if any(c not in available.splitlines() for c in codes):
        raise ValueError("Required OCR language is not installed")
    pages = []
    quality = []
    for number in range(1, count + 1):
        if cancel():
            raise InterruptedError("Document processing cancelled")
        log("OCR page " + str(number) + " / " + str(count))
        stem = folder / ("page-" + str(number))
        image = stem.with_suffix(".png")
        wsl(
            "pdftoppm",
            "-f",
            str(number),
            "-l",
            str(number),
            "-singlefile",
            "-scale-to",
            "2400",
            "-png",
            linux_path(path),
            linux_path(stem),
        )
        raw = wsl(
            "tesseract", linux_path(image), "stdout", "-l", "+".join(codes), "tsv"
        )
        rows = list(csv.DictReader(io.StringIO(raw), delimiter="\t"))
        lines = {}
        conf = []
        for row in rows:
            if row.get("level") != "5" or not row.get("text", "").strip():
                continue
            key = tuple(row.get(k) for k in ("block_num", "par_num", "line_num"))
            lines.setdefault(key, []).append(row["text"])
            conf.append(float(row["conf"]))
        text = "\n".join(" ".join(words) for words in lines.values())
        pages.append((number, text))
        quality.append(
            {
                "page": number,
                "mean_word_confidence": round(sum(conf) / len(conf), 2)
                if conf
                else None,
                "words": len(conf),
            }
        )
        (folder / ("page-" + str(number) + ".tsv")).write_text(raw, encoding="utf-8")
        image.unlink(missing_ok=True)
    return pages, {
        "engine": wsl("tesseract", "--version").splitlines()[0],
        "languages": codes,
        "pages": quality,
        "note": "OCR confidence is not certainty of a medical statement; manually check negations, numbers and units.",
    }


def process(args, log=print, cancel=lambda: False):
    person = args["person"]
    profile_identity.assert_writable(person)
    doc = next(
        (d for d in profile_documents.listing(person) if d["id"] == args["document"]),
        None,
    )
    if not doc or doc["status"] == "changed_since_index":
        raise ValueError("Saved original missing or changed; reindex before processing")
    path = Path(doc["path"])
    if profile_documents.digest(path) != doc["sha256"]:
        raise ValueError("Original checksum changed")
    source = args.get("source_language", "en")
    if source not in LANGUAGES:
        raise ValueError("Select source language explicitly")
    if source in ("ar", "uk") and args.get("translate", True):
        raise ValueError(
            "Use OCR only for Arabic/Ukrainian reports. Arabic translation failed a medical-term check; no Ukrainian translation model is configured."
        )
    folder = (
        source_store.profile_dir(person)
        / "Findings/Processed"
        / doc["id"]
        / uuid.uuid4().hex
    )
    folder.mkdir(parents=True)
    provenance = {
        "source_document": doc["id"],
        "source_name": doc["name"],
        "source_sha256": doc["sha256"],
        "source_language": source,
        "review": "unreviewed_machine_processing",
        "created": profile_identity.now(),
    }
    if args.get("ocr", False):
        pages, provenance["ocr"] = ocr_pages(
            path, folder, args.get("languages", ["en", "de"]), log, cancel
        )
    elif path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        pages = [
            (i + 1, p.extract_text() or "")
            for i, p in enumerate(PdfReader(str(path)).pages[:100])
        ]
    else:
        with family.connect() as db:
            profile_documents.schema(db)
            chunks = db.execute(
                "SELECT page,part,text FROM document_chunks WHERE document=? ORDER BY page,part",
                (doc["id"],),
            ).fetchall()
        grouped = {}
        # Chunk overlaps are retained and flagged instead of inventing missing original text.
        for row in chunks:
            grouped.setdefault(row["page"], []).append(row["text"])
        pages = [(n, "\n".join(parts)) for n, parts in grouped.items()]
    if not pages or not any(text.strip() for _, text in pages):
        raise ValueError("No extracted text. Enable OCR for scanned PDFs.")
    if sum(len(t) for _, t in pages) > 300000:
        raise ValueError(
            "Translation limit: 300,000 extracted characters; split the report"
        )
    generated = []
    for target in ["original"] + (["en", "de"] if args.get("translate", True) else []):
        if cancel():
            raise InterruptedError("Document processing cancelled")
        log("Document output: " + target)
        texts = []
        converted_pages = []
        for page, text in pages:
            converted = (
                text if target == "original" else translate(text, source, target)
            )
            texts.append("SOURCE PAGE " + str(page) + "\n" + converted)
            converted_pages.append((page, converted))
        dest = folder / (target + ".txt")
        dest.write_text("\n\n".join(texts), encoding="utf-8")
        kind = (
            ("ocr_extraction" if args.get("ocr") else "extracted_text")
            if target == "original"
            else "machine_translation_" + target
        )
        record = profile_documents.index_file(
            person,
            dest,
            doc["provider"] + " / " + kind,
            doc["report_date"],
            kind,
            copy=False,
            log=log,
        )
        with family.connect() as db:
            db.execute(
                "UPDATE profile_documents SET notes=?,pages=? WHERE id=?",
                (
                    json.dumps(provenance | {"language": target}, ensure_ascii=False),
                    len(converted_pages),
                    record["id"],
                ),
            )
            db.execute("DELETE FROM document_chunks WHERE document=?", (record["id"],))
            for page, text in converted_pages:
                for part, offset in enumerate(range(0, len(text), 880)):
                    chunk = text[offset : offset + 1000]
                    db.execute(
                        "INSERT INTO document_chunks VALUES(?,?,?,?,?,?)",
                        (
                            uuid.uuid4().hex,
                            record["id"],
                            page,
                            part,
                            chunk,
                            json.dumps(profile_documents.topics(chunk)),
                        ),
                    )
        generated.append(
            {"language": target, "document": record["id"], "path": str(dest)}
        )
    used = (
        {(source, "en")}
        if source == "de"
        else {("en", "de")}
        if source == "en"
        else {(source, "en"), ("en", "de")}
    )
    provenance["translation_models"] = [
        {k: m[k] for k in ("from", "to", "version", "sha256")}
        for m in manifest()["models"]
        if args.get("translate", True) and (m["from"], m["to"]) in used
    ]
    (folder / "processing-provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"generated": generated, "provenance": provenance}
