"""Local sequence utilities. Concatenation is never individual-genotype consensus."""

from pathlib import Path
import collections, gzip, hashlib, html, json, sqlite3, sys, uuid, zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "DNA_Software/Windows/PythonPackages"))
ALPHABET = set("ACGTURYSWKMBDHVN-.")


def opener(path):
    return (
        gzip.open(path, "rt", encoding="utf-8-sig")
        if str(path).lower().endswith(".gz")
        else Path(path).open(encoding="utf-8-sig")
    )


def stamp(path):
    p = Path(path).resolve()
    s = p.stat()
    return {"path": str(p), "bytes": s.st_size, "mtime_ns": s.st_mtime_ns}


def stable(before):
    if stamp(before["path"]) != before:
        raise ValueError("Input changed during processing; wait until downloads finish")


def save(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def checked(cancel):
    if cancel():
        raise InterruptedError("Sequence job cancelled; original inputs preserved")


def fasta_events(path, cancel=lambda: False):
    current = False
    length = 0
    at_line_start = True
    with opener(path) as stream:
        for line_no, raw in enumerate(
            iter(lambda: stream.readline(1024 * 1024), ""), 1
        ):
            checked(cancel)
            was_line_start = at_line_start
            at_line_start = raw.endswith("\n")
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                if not was_line_start or len(raw) >= 1024 * 1024:
                    raise ValueError("Invalid or excessively long FASTA header")
                if current and not length:
                    raise ValueError("Empty FASTA record before line " + str(line_no))
                name = line[1:].strip()
                if not name or any(ord(c) < 32 for c in name):
                    raise ValueError("Invalid FASTA header at line " + str(line_no))
                current = True
                length = 0
                yield "header", name
            else:
                if not current:
                    raise ValueError("FASTA sequence before the first header")
                seq = "".join(line.split()).upper()
                if set(seq) - ALPHABET:
                    raise ValueError(
                        "Invalid nucleotide symbols at line " + str(line_no)
                    )
                length += len(seq)
                yield "sequence", seq
    if not current or not length:
        raise ValueError("No complete FASTA record found")


def stats(person, inputs, out, log=print, cancel=lambda: False):
    out = Path(out)
    records = []
    sources = []
    fastq_limit = int(inputs.get("read_limit", "10000"))
    if not 1 <= fastq_limit <= 1000000:
        raise ValueError("FASTQ sample limit must be 1–1,000,000")
    for value in inputs["files"]:
        before = stamp(value)
        sources.append(before)
        name = Path(value).name.lower()
        counts = collections.Counter()
        lengths = []
        quality = collections.Counter()
        sampled = False
        if name.endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz")):
            from Bio.SeqIO.QualityIO import FastqGeneralIterator

            with opener(value) as f:
                iterator = FastqGeneralIterator(f)
                for i, (title, seq, q) in enumerate(iterator):
                    checked(cancel)
                    if i >= fastq_limit:
                        sampled = True
                        break
                    seq = seq.upper()
                    if set(seq) - ALPHABET:
                        raise ValueError("Invalid nucleotide symbols in FASTQ")
                    scores = [ord(c) - 33 for c in q]
                    if not scores or min(scores) < 0 or max(scores) > 93:
                        raise ValueError("Invalid Phred+33 quality values")
                    counts.update(seq)
                    lengths.append(len(seq))
                    quality.update(scores)
        else:
            length = 0
            for kind, value_ in fasta_events(value, cancel):
                if kind == "header":
                    if length:
                        lengths.append(length)
                    length = 0
                else:
                    counts.update(value_)
                    length += len(value_)
            lengths.append(length)
        stable(before)
        total = sum(counts.values())
        canonical = sum(counts[c] for c in "ACGTU")
        half = sum(lengths) / 2
        running = 0
        n50 = 0
        for length in sorted(lengths, reverse=True):
            running += length
            if running >= half:
                n50 = length
                break
        row = {
            "source": before,
            "records_scanned": len(lengths),
            "bases_scanned": total,
            "sampled_only": sampled,
            "complete_file_scanned": not sampled,
            "base_counts": dict(counts),
            "gc_percent_of_ACGTU": round(
                100 * (counts["G"] + counts["C"]) / canonical, 4
            )
            if canonical
            else None,
            "N_bases": counts["N"],
            "other_ambiguity_or_gap_bases": total - canonical - counts["N"],
            "N50_of_scanned_sequences": n50,
            "mean_phred33": sum(k * v for k, v in quality.items())
            / sum(quality.values())
            if quality
            else None,
            "Q30_base_calls_in_sample": sum(v for k, v in quality.items() if k >= 30)
            if quality
            else None,
            "not_genotype_quality_or_genome_coverage": True,
        }
        records.append(row)
        log(
            Path(value).name
            + ": "
            + str(len(lengths))
            + " records / "
            + str(total)
            + " bases"
            + (" (sample)" if sampled else "")
        )
    save(
        out / "sequence-statistics.json",
        {
            "person": person,
            "files": records,
            "note": "Counts describe sequence records, not independently verified human genotypes or genome completeness.",
        },
    )
    rows = "".join(
        "<tr><td>"
        + html.escape(Path(x["source"]["path"]).name)
        + "</td><td>"
        + str(x["records_scanned"])
        + "</td><td>"
        + str(x["bases_scanned"])
        + "</td><td>"
        + str(x["gc_percent_of_ACGTU"])
        + "</td><td>"
        + ("Sample only" if x["sampled_only"] else "Entire file")
        + "</td></tr>"
        for x in records
    )
    (out / "sequence-statistics.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Sequence statistics</title><style>body{font:16px Segoe UI;max-width:1100px;margin:40px auto;color:#163342}td,th{padding:14px;border-bottom:1px solid #ccd}</style><h1>Sequence statistics</h1><p>Sequence counts are not genotype quality, callable-genome coverage or clinical verification.</p><table><tr><th>File</th><th>Records</th><th>Bases</th><th>GC % (ACGTU)</th><th>Scope</th></tr>'
        + rows
        + "</table>",
        encoding="utf-8",
    )


def merge(person, inputs, out, log=print, cancel=lambda: False):
    out = Path(out)
    sources = [stamp(p) for p in inputs["files"]]
    dedup = inputs.get("deduplicate", "Nein") in ("Ja", "Yes")
    db = sqlite3.connect(out / "merge-index.sqlite")
    db.execute("CREATE TABLE seen(sha TEXT,length INTEGER,PRIMARY KEY(sha,length))")
    total = kept = removed = 0
    partial = out / "sequence-collection.fasta.partial"
    spool = out / "record.tmp"
    try:
        with (
            partial.open("x", encoding="ascii", newline="\n") as output,
            (out / "record-sources.tsv").open(
                "x", encoding="utf-8", newline="\n"
            ) as mapping,
        ):
            mapping.write(
                "output_id\tsource_file\toriginal_header\tlength\tsequence_sha256\tstatus\n"
            )
            for source_number, value in enumerate(inputs["files"], 1):
                current = None
                handle = None
                digest = None
                length = 0
                number = 0

                def flush():
                    nonlocal kept, removed, total, handle
                    if current is None:
                        return
                    handle.close()
                    handle = None
                    checked(cancel)
                    sha = digest.hexdigest()
                    total += 1
                    duplicate = (
                        dedup
                        and db.execute(
                            "SELECT 1 FROM seen WHERE sha=? AND length=?", (sha, length)
                        ).fetchone()
                    )
                    new_id = f"s{source_number:03d}_r{number:07d}"
                    if duplicate:
                        removed += 1
                        status = "duplicate_sequence_removed"
                    else:
                        kept += 1
                        status = "kept"
                        db.execute(
                            "INSERT OR IGNORE INTO seen VALUES(?,?)", (sha, length)
                        )
                        output.write(">" + new_id + "\n")
                        with spool.open(encoding="ascii") as inp:
                            while True:
                                chunk = inp.read(80)
                                if not chunk:
                                    break
                                checked(cancel)
                                output.write(chunk + "\n")
                    mapping.write(
                        "\t".join(
                            [
                                new_id,
                                str(Path(value).resolve()),
                                current.replace("\t", " "),
                                str(length),
                                sha,
                                status,
                            ]
                        )
                        + "\n"
                    )

                try:
                    for kind, text in fasta_events(value, cancel):
                        if kind == "header":
                            flush()
                            number += 1
                            current = text
                            digest = hashlib.sha256()
                            length = 0
                            handle = spool.open("w", encoding="ascii")
                        else:
                            handle.write(text)
                            digest.update(text.encode("ascii"))
                            length += len(text)
                    flush()
                    stable(sources[source_number - 1])
                    db.commit()
                    log(Path(value).name + ": " + str(number) + " records collected")
                finally:
                    if handle:
                        handle.close()
        partial.replace(out / "sequence-collection.fasta")
        with (out / "sequence-collection.fasta").open("rb") as f:
            output_hash = hashlib.file_digest(f, "sha256").hexdigest()
        save(
            out / "merge-manifest.json",
            {
                "person": person,
                "operation": "FASTA record concatenation, NOT individual-genome consensus",
                "sources": sources,
                "records_seen": total,
                "records_kept": kept,
                "identical_sequence_records_removed": removed,
                "identity_policy": "SHA-256 of uppercase sequence plus length; headers do not establish identity",
                "not_for_best_selection": True,
                "missing_genotypes_not_filled": True,
                "output_sha256": output_hash,
            },
        )
    finally:
        db.close()
        if spool.exists():
            spool.unlink()


def extract_sequence(inputs, out):
    import pyfastx

    path = Path(inputs["file"])
    before = stamp(path)
    start = int(inputs.get("start", "1"))
    end = int(inputs.get("end", "1000"))
    if not 1 <= start <= end or end - start + 1 > 5000000:
        raise ValueError(
            "Choose a 1-based inclusive interval of at most 5 million bases"
        )
    fastq = path.name.lower().endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz"))
    cls = pyfastx.Fastq if fastq else pyfastx.Fasta
    indexed = cls(str(path), index_file=str(Path(out) / "source.fxi"))
    name = inputs.get("record", "").strip() or next(iter(indexed.keys()))
    try:
        record = indexed[name]
    except KeyError:
        raise ValueError("Sequence identifier not found in the selected file") from None
    if end > len(record):
        raise ValueError(
            "Interval exceeds the selected sequence length (" + str(len(record)) + ")"
        )
    if fastq:
        seq = record.seq[start - 1 : end]
    else:
        piece = record[start - 1 : end]
        seq = piece.seq if hasattr(piece, "seq") else str(piece)
    seq = seq.upper()
    stable(before)
    return (
        name,
        seq,
        {
            "source": before,
            "record": name,
            "start_1based_inclusive": start,
            "end_1based_inclusive": end,
            "sequence_sha256": hashlib.sha256(seq.encode()).hexdigest(),
            "index_location": "job output folder; source file unchanged",
            "coordinate_scope": "within this sequence record; not an inferred genome build",
        },
    )


def extract(person, inputs, out, log=print, cancel=lambda: False):
    checked(cancel)
    name, seq, manifest = extract_sequence(inputs, out)
    checked(cancel)
    write_fasta(Path(out) / "extracted.fasta", name, seq)
    save(Path(out) / "extract-manifest.json", dict(manifest, person=person))
    log(str(len(seq)) + " bases extracted")


def write_fasta(path, name, seq):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        f.write(">" + name.replace("\n", " ").replace("\r", " ") + "\n")
        for i in range(0, len(seq), 80):
            f.write(seq[i : i + 80] + "\n")


def transform(person, inputs, out, log=print, cancel=lambda: False):
    from Bio.Seq import Seq

    name, seq, manifest = extract_sequence(inputs, out)
    checked(cancel)
    operation = inputs.get("operation", "Reverse complement")
    if operation == "Reverse complement":
        result = str(Seq(seq).reverse_complement())
        kind = "nucleotide"
    elif operation == "Translate frame 1":
        trimmed = len(seq) % 3
        result = str(Seq(seq[: len(seq) - trimmed] if trimmed else seq).translate())
        manifest["trailing_bases_not_translated"] = trimmed
        kind = "protein"
    else:
        raise ValueError("Unknown sequence transformation")
    write_fasta(Path(out) / "transformed.fasta", name + " | " + operation, result)
    save(
        Path(out) / "transform-manifest.json",
        dict(
            manifest,
            person=person,
            operation=operation,
            alphabet=kind,
            note="Sequence translation is not a gene prediction or disease interpretation.",
        ),
    )
    log(operation + " complete")


def view(person, inputs, out, log=print, cancel=lambda: False):
    import visual_tools

    if not visual_tools.installed("seqviz"):
        raise ValueError("Install the optional SeqViz viewer first")
    name, seq, manifest = extract_sequence(inputs, out)
    if len(seq) > 50000:
        raise ValueError("SeqViz view limit is 50,000 bases; choose a smaller interval")
    checked(cancel)
    job = uuid.uuid4().hex
    folder = visual_tools.RUNS / job
    folder.mkdir(parents=True)
    data = {
        "name": name,
        "seq": seq,
        "viewer": "both",
        "showComplement": True,
        "style": {"height": "78vh", "width": "100%"},
    }
    document = (
        '<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SeqViz · Local sequence</title><style>body{margin:0;font:15px Segoe UI;background:#eef5f7;color:#153342}header{padding:20px 30px}#root{background:white;margin:0 22px}</style><header><h1>SeqViz · Local sequence</h1><p>'
        + html.escape(
            person
            + " · "
            + name
            + " · "
            + str(manifest["start_1based_inclusive"])
            + "–"
            + str(manifest["end_1based_inclusive"])
        )
        + '</p><p>Coordinates are within this sequence. This view does not establish genotype quality, ancestry or disease.</p></header><div id="root"></div><script src="/tool-assets/seqviz/dist/seqviz.min.js"></script><script>window.seqviz.Viewer("root",'
        + json.dumps(data).replace("<", "\\u003c")
        + ").render();</script></html>"
    )
    # Keep the standalone export local too; upstream font imports must not contact Google.
    document = document.replace(
        '<meta charset="utf-8">',
        "<meta charset=\"utf-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'none'\">",
        1,
    )
    (folder / "index.html").write_text(document, encoding="utf-8")
    save(
        folder / "manifest.json",
        dict(
            manifest,
            person=person,
            tool="seqviz",
            version=visual_tools.LOCK["seqviz"]["version"],
            files={},
        ),
    )
    save(
        Path(out) / "view.json",
        {
            "path": "/visual-run/" + job + "/index.html",
            "person": person,
            "tool": "seqviz",
        },
    )
    write_fasta(Path(out) / "view-sequence.fasta", name, seq)
    asset = visual_tools.BASE / "seqviz" / visual_tools.LOCK["seqviz"]["entry"]
    exported = document.replace(
        "/tool-assets/seqviz/dist/seqviz.min.js", "seqviz.min.js"
    )
    with zipfile.ZipFile(
        Path(out) / "SeqViz_Offline_Viewer.zip", "w", zipfile.ZIP_DEFLATED
    ) as z:
        z.writestr("index.html", exported)
        z.write(asset, "seqviz.min.js")
        z.write(Path(out) / "view-sequence.fasta", "view-sequence.fasta")
        for p in (visual_tools.BASE / "seqviz").glob("*LICENSE*"):
            z.write(p, p.name)
    log("Interactive local SeqViz view and offline ZIP ready")
