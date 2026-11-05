from contextlib import closing

"""Auditable, disk-backed comparison and conservative measured-SNP consensus.

Missing loci are never reference calls. This module cannot create reads, a gVCF,
clinical validation, or evidence of independence between uploaded providers.
"""
from pathlib import Path
from contextlib import contextmanager
import csv, gzip, hashlib, io, re, sqlite3, datetime, sys, zipfile
import portable_json as json
import source_store, inspector

VERSION = "1.0"
NOW = lambda: datetime.datetime.now().astimezone().isoformat()


def digest(path, cancel=lambda: False):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            if cancel():
                raise InterruptedError("Cancelled; originals are preserved.")
            h.update(block)
    return h.hexdigest()


@contextmanager
def textfile(path):
    p = Path(path)
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            members = [
                x
                for x in z.infolist()
                if not x.is_dir()
                and x.filename.lower().endswith((".vcf", ".txt", ".csv"))
            ]
            if len(members) != 1:
                raise ValueError(
                    "Archive requires exactly one clearly readable genotype file."
                )
            with (
                z.open(members[0]) as raw,
                io.TextIOWrapper(raw, encoding="utf-8-sig") as stream,
            ):
                yield stream
    else:
        op = gzip.open if p.name.endswith((".gz", ".bgz")) else open
        with op(p, "rt", encoding="utf-8-sig") as stream:
            yield stream


def chrom(value):
    value = value.removeprefix("chr")
    return {"23": "X", "24": "Y", "26": "MT", "M": "MT"}.get(value, value)


def calls(path, stats):
    """Yield 1-based, plus-strand, literal ACGT genotypes only."""
    head = ""
    vcf = False
    samples = 0
    with textfile(path) as stream:
        for line in stream:
            if line.startswith("#"):
                head = (head + line)[:262144]
                if line.startswith("##fileformat=VCF"):
                    vcf = True
                if line.startswith("#CHROM"):
                    vcf = True
                    samples = len(line.rstrip().split("\t")) - 9
                continue
            if not line.strip():
                continue
            stats["rows"] = stats.get("rows", 0) + 1
            if vcf:
                c = line.rstrip().split("\t")
                if samples != 1 or len(c) != 10:
                    raise ValueError(
                        "Only individual VCF with exactly one genotype column supported."
                    )
                stats["is_vcf"] = True
                pos = int(c[1])
                alleles = [c[3]] + ([] if c[4] == "." else c[4].split(","))
                data = dict(zip(c[8].split(":"), c[9].split(":")))
                if not all(len(a) == 1 and a in "ACGT" for a in alleles):
                    stats["non_snp"] = stats.get("non_snp", 0) + 1
                    continue
                try:
                    indices = [
                        int(x)
                        for x in re.split(r"[/|]", data.get("GT", "."))
                        if x != "."
                    ]
                    if any(x < 0 or x >= len(alleles) for x in indices):
                        raise ValueError("GT outside alleles")
                    gt = "".join(sorted(alleles[x] for x in indices))
                except (ValueError, IndexError):
                    stats["invalid"] = stats.get("invalid", 0) + 1
                    continue
                rawgt = data.get("GT", ".")
                if "." in rawgt or len(gt) not in (1, 2):
                    stats["missing"] = stats.get("missing", 0) + 1
                    continue
                dp = data.get("DP")
                gq = data.get("GQ")
                stats["quality_fields"] = stats.get("quality_fields", False) or (
                    dp is not None and gq is not None
                )
                try:
                    high = c[6] == "PASS" and float(dp) >= 10 and float(gq) >= 20
                except (ValueError, TypeError):
                    high = False
                valid = c[6] in ("PASS", ".")
                item = (chrom(c[0]), pos, gt, c[2], c[3], int(high), int(valid))
            else:
                c = next(csv.reader([line])) if "," in line else line.strip().split()
                if len(c) < 4 or not re.fullmatch(r"(?:rs|i|ss)\d+", c[0]):
                    continue
                try:
                    pos = int(c[2])
                except ValueError:
                    continue
                gt = c[3].upper()
                if len(c) > 4 and len(gt) == 1:
                    gt += c[4].upper()
                if not re.fullmatch("[ACGT]{1,2}", gt):
                    stats["missing"] = stats.get("missing", 0) + 1
                    continue
                item = (chrom(c[1]), pos, "".join(sorted(gt)), c[0], "", 0, 1)
            if pos < 1 or item[0] not in [str(i) for i in range(1, 23)] + [
                "X",
                "Y",
                "MT",
            ]:
                stats["invalid"] = stats.get("invalid", 0) + 1
                continue
            yield item
    stats["detected"] = inspector.tokens(head, Path(path).name)
    lineage = re.search(r"^##DNAWorkbenchOriginalSHA256=([a-f0-9]{64})$", head, re.M)
    if lineage:
        stats["root_sha256"] = lineage.group(1)


def annotation_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS file_annotations(file_id TEXT PRIMARY KEY,origin TEXT,lifecycle TEXT,payload TEXT,updated TEXT)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS preferred_sets(build TEXT PRIMARY KEY,payload TEXT,updated TEXT)"
    )


def analyze(
    person,
    out,
    log=print,
    cancel=lambda: False,
    target="separate",
    chain=None,
    reference=None,
):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "vergleich.sqlite"
    if path.exists():
        raise ValueError("Analysis goal already exists; create new order.")
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("PRAGMA cache_size=-65536")
    db.set_progress_handler(lambda: int(cancel()), 100000)
    db.executescript(
        "CREATE TABLE calls(source TEXT,build TEXT,chrom TEXT,pos INTEGER,gt TEXT,rsid TEXT,ref TEXT,high INTEGER,valid INTEGER,PRIMARY KEY(source,build,chrom,pos)); CREATE TABLE sources(id TEXT PRIMARY KEY,payload TEXT);"
    )
    rows = source_store.listing(person)
    sources = []
    seen = set()
    if not rows:
        db.close()
        raise ValueError(
            "No files have been explicitly imported into this profile. Use Files → Batch preparation first. Private download folders are not scanned automatically."
        )
    try:
        for row in rows:
            if cancel():
                raise InterruptedError("Analyse abgebrochen.")
            r = {
                "id": row["id"],
                "path": row["path"],
                "provider": row["provider"],
                "sha256": row["sha256"],
                "build": row["build"],
                "status": "unprocessed",
                "stats": {},
                "original_name": row["original_name"],
                "imported": row["created"],
                "versions": row.get("versions", []),
                "declared_version": row.get("declared_version", ""),
                "label": row["label"],
            }
            sources.append(r)
            log("Check the source:" + row["original_name"])
            if row.get("origin") == "own_generated":
                r["status"] = "derived-not-independent"
                continue
            if row["sha256"] in seen:
                r["status"] = "duplicate-bytes"
                continue
            seen.add(row["sha256"])
            if row["kind"] not in ("VCF", "Raw data / text", "Chip / table", "Archive"):
                r["status"] = "not-genotype-input"
                continue
            try:
                before = Path(row["path"]).stat()
                if digest(row["path"], cancel) != row["sha256"]:
                    raise ValueError("The checksum is different from the import.")
                batch = []
                n = 0
                for c in calls(row["path"], r["stats"]):
                    if n % 10000 == 0 and cancel():
                        raise InterruptedError("Analyse abgebrochen.")
                    batch.append((row["id"], row["build"], *c))
                    n += 1
                    if len(batch) >= 10000:
                        _insert(db, batch, r["stats"])
                        batch = []
                        db.commit()
                        log("  " + str(n) + " SNP-Aufrufe gelesen")
                _insert(db, batch, r["stats"])
                after = Path(row["path"]).stat()
                if (before.st_size, before.st_mtime_ns) != (
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    raise ValueError("Source changed during the analysis.")
                detected = r["stats"].get("detected", {})
                build = detected.get("build") or row["build"]
                if build not in ("GRCh37", "GRCh38"):
                    raise ValueError("Reference build not occupied; explicitly check.")
                if (
                    detected.get("build")
                    and row["build"] in ("GRCh37", "GRCh38")
                    and detected["build"] != row["build"]
                ):
                    raise ValueError("Build contradicts the source register.")
                db.execute(
                    "UPDATE calls SET build=? WHERE source=?", (build, row["id"])
                )
                r["build"] = build
                measurement = (
                    str(row.get("measurement", ""))
                    + " "
                    + detected.get("measurement", "")
                )
                r["imputed"] = "imput" in measurement.lower()
                r["phased_derived"] = (
                    "phas" in measurement.lower()
                    or "statistical" in measurement.lower()
                )
                r["measured"] = (
                    str(row.get("measurement", "")).lower() in ("gemessen", "measured")
                    and not r["imputed"]
                    and not r["phased_derived"]
                )
                r["called"] = db.execute(
                    "SELECT count(*) FROM calls WHERE source=? AND valid=1",
                    (row["id"],),
                ).fetchone()[0]
                r["qc_supported"] = db.execute(
                    "SELECT count(*) FROM calls WHERE source=? AND valid=1 AND high=1",
                    (row["id"],),
                ).fetchone()[0]
                r["status"] = "analyzed" if r["called"] else "no-eligible-snps"
                r["selection_eligible"] = row.get("qc_color") not in ("red", "black")
                r["root_sha256"] = (
                    row.get("source_root_sha256")
                    or row.get("container_sha256")
                    or r["stats"].get("root_sha256", r["sha256"])
                )
            except (OSError, ValueError, UnicodeError, zipfile.BadZipFile) as error:
                db.execute("DELETE FROM calls WHERE source=?", (row["id"],))
                r["status"] = "excluded"
                r["error"] = str(error)
            db.execute("INSERT INTO sources VALUES(?,?)", (r["id"], json.dumps(r)))
            db.commit()
        if target == "GRCh38":
            if not chain or not reference:
                raise ValueError(
                    "For joint GRCh38 analysis, chain and indexed GRCh38-FASTA are required."
                )
            harmonize(db, sources, chain, reference, log, cancel)
        pairs = []
        eligible = [r for r in sources if r["status"] == "analyzed"]
        for i, a in enumerate(eligible):
            for b in eligible[i + 1 :]:
                if cancel():
                    raise InterruptedError("Analyse abgebrochen.")
                pair = {
                    "a": a["id"],
                    "b": b["id"],
                    "status": "different-build",
                    "common": 0,
                }
                basis = a.get("comparison_build", a["build"])
                if basis == b.get("comparison_build", b["build"]):
                    n, same = db.execute(
                        "SELECT count(*),sum(a.gt=b.gt) FROM calls a JOIN calls b ON a.build=b.build AND a.chrom=b.chrom AND a.pos=b.pos WHERE a.source=? AND b.source=? AND a.build=? AND a.valid=1 AND b.valid=1",
                        (a["id"], b["id"], basis),
                    ).fetchone()
                    pair.update(
                        common=n,
                        same=same or 0,
                        discordant=n - (same or 0),
                        concordance=(same / n if n else None),
                        status="too-few-markers"
                        if n < 1000
                        else "consistent"
                        if same / n >= 0.995
                        else "review-conflicts",
                    )
                pairs.append(pair)
                log(
                    "Source pair:"
                    + pair["status"]
                    + " · "
                    + str(pair["common"])
                    + " gemeinsame SNPs"
                )
        db.commit()
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        report = {
            "version": VERSION,
            "person": person,
            "created": NOW(),
            "database_sha256": digest(path, cancel),
            "target": target,
            "chain_sha256": digest(chain, cancel) if target == "GRCh38" else None,
            "reference_sha256": digest(reference, cancel)
            if target == "GRCh38"
            else None,
            "sources": sources,
            "pairs": pairs,
            "scope": "Observed SNP genotypes only; no indels/SVs, coverage, clinical verification or independence proof. Different builds are never compared directly; optional GRCh38 harmonization maps SNPs with strand correction.",
        }
        (out / "analysis.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with closing(source_store.connect(person)) as register, register:
            annotation_schema(register)
            for r in sources:
                if r["status"] == "derived-not-independent":
                    continue
                register.execute(
                    "INSERT OR REPLACE INTO file_annotations VALUES(?,?,?,?,?)",
                    (
                        r["id"],
                        "imported",
                        "analyzed",
                        json.dumps(
                            {
                                "analysis": str(out),
                                "source": r,
                                "comparisons": [
                                    p for p in pairs if r["id"] in (p["a"], p["b"])
                                ],
                            }
                        ),
                        NOW(),
                    ),
                )
        (out / "report.html").write_text(
            '<meta charset="utf-8"><h1>Profile comparison</h1><p>SNP genotypes, not clinical verification. Different reference builds remain separate.</p><pre>'
            + __import__("html").escape(
                json.dumps(report, ensure_ascii=False, indent=2)
            )
            + "</pre>",
            encoding="utf-8",
        )
        return report
    finally:
        db.close()


def _insert(db, batch, stats):
    for item in batch:
        try:
            db.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?)", item)
        except sqlite3.IntegrityError:
            stats["duplicates"] = stats.get("duplicates", 0) + 1
            db.execute(
                "UPDATE calls SET valid=0 WHERE source=? AND build=? AND chrom=? AND pos=?",
                item[:4],
            )


def harmonize(db, sources, chain, reference, log, cancel):
    """Add mapped calls; keep original-build rows for provenance and separate exports."""
    sys.path.insert(0, str(source_store.ROOT / "DNA_Software/Windows/PythonPackages"))
    try:
        from pyliftover import LiftOver
    except ImportError:
        raise ValueError("Install pyliftover first via check dependencies.")
    op = gzip.open if str(chain).endswith(".gz") else open
    with op(chain, "rt") as stream:
        for line in stream:
            c = line.split()
            if c and c[0] == "chain" and c[2] in ("chr1", "1"):
                if int(c[3]) == 248956422 or int(c[8]) == 249250621:
                    raise ValueError("Chain does not have the direction GRCh37→GRCh38.")
                break
    lo = LiftOver(str(chain))
    fa = Fasta(reference)
    comp = str.maketrans("ACGT", "TGCA")
    if any(fa.index[n][0] == 249250621 for n in ("1", "chr1") if n in fa.index):
        fa.close()
        raise ValueError("Target FASTA is GRCh37 instead of GRCh38.")
    db.execute(
        "CREATE TABLE mapping_rejects(source TEXT,chrom TEXT,pos INTEGER,reason TEXT)"
    )
    try:
        for r in sources:
            if r["status"] != "analyzed":
                continue
            if r["build"] == "GRCh38":
                r["comparison_build"] = "GRCh38"
                continue
            if r["build"] != "GRCh37":
                continue
            stats = {
                "mapped": 0,
                "unmapped": 0,
                "multiple": 0,
                "reference_error": 0,
                "collisions": 0,
            }
            log("GRCh37-SNPs nach GRCh38 abbilden: " + Path(r["path"]).name)
            for i, c in enumerate(
                db.execute(
                    "SELECT chrom,pos,gt,rsid,ref,high,valid FROM calls WHERE source=? AND build='GRCh37'",
                    (r["id"],),
                )
            ):
                if i % 10000 == 0 and cancel():
                    raise InterruptedError("Abbildung abgebrochen.")
                chromosome, pos, gt, rsid, oldref, high, valid = c
                hits = (
                    lo.convert_coordinate(
                        "chrM" if chromosome == "MT" else "chr" + chromosome, pos - 1
                    )
                    or []
                )
                reason = (
                    "unmapped" if not hits else "multiple" if len(hits) != 1 else ""
                )
                if not reason:
                    name, zero, strand, _ = hits[0]
                    name = chrom(name)
                    position = zero + 1
                    if strand == "-":
                        gt = "".join(sorted(gt.translate(comp)))
                    try:
                        ref = fa.base(name, position)
                    except ValueError:
                        reason = "reference_error"
                if reason:
                    stats[reason] += 1
                    db.execute(
                        "INSERT INTO mapping_rejects VALUES(?,?,?,?)",
                        (r["id"], chromosome, pos, reason),
                    )
                    continue
                try:
                    db.execute(
                        "INSERT INTO calls VALUES(?,?,?,?,?,?,?,?,?)",
                        (r["id"], "GRCh38", name, position, gt, rsid, ref, high, valid),
                    )
                    stats["mapped"] += 1
                except sqlite3.IntegrityError:
                    db.execute(
                        "UPDATE calls SET valid=0 WHERE source=? AND build='GRCh38' AND chrom=? AND pos=?",
                        (r["id"], name, position),
                    )
                    stats["collisions"] += 1
            r["comparison_build"] = "GRCh38"
            r["liftover"] = stats
            db.execute(
                "UPDATE sources SET payload=? WHERE id=?", (json.dumps(r), r["id"])
            )
            db.commit()
    finally:
        fa.close()


class Fasta:
    def __init__(self, path):
        self.path = Path(path)
        self.index = {}
        for line in Path(str(path) + ".fai").read_text().splitlines():
            c = line.split("\t")
            self.index[c[0]] = tuple(map(int, c[1:5]))
        self.handle = self.path.open("rb")

    def base(self, chromosome, pos):
        names = [chromosome, "chr" + chromosome] + (
            ["chrM", "MT", "M"] if chromosome == "MT" else []
        )
        name = next((n for n in names if n in self.index), None)
        if name is None:
            raise ValueError("Chromosom fehlt in FASTA: " + chromosome)
        length, offset, width, bytesline = self.index[name]
        if not 0 < pos <= length:
            raise ValueError("Position outside FASTA.")
        zero = pos - 1
        self.handle.seek(offset + zero // width * bytesline + zero % width)
        result = self.handle.read(1).decode().upper()
        if result not in "ACGT":
            raise ValueError("Reference basis is not clear.")
        return result

    def close(self):
        self.handle.close()


def generate(person, analysis, out, build, reference, log=print, cancel=lambda: False):
    analysis = Path(analysis).resolve()
    report = json.loads((analysis / "analysis.json").read_text(encoding="utf-8"))
    if report["person"] != person:
        raise ValueError("Analysis belongs to another profile.")
    if digest(analysis / "vergleich.sqlite", cancel) != report.get("database_sha256"):
        raise ValueError("Analysis database has been changed; re-analyze.")
    if build not in ("GRCh37", "GRCh38"):
        raise ValueError("Select the target build.")
    reference_before = Path(reference).stat()
    reference_sha256 = digest(reference, cancel)
    if (
        report.get("target") == build
        and report.get("reference_sha256") != reference_sha256
    ):
        raise ValueError("Target FASTA deviates from the unified analysis.")
    rows = source_store.listing(person)
    byid = {r["id"]: r for r in rows}
    sources = [
        r
        for r in report["sources"]
        if r["status"] == "analyzed"
        and (r["build"] == build or r.get("comparison_build") == build)
        and r.get("measured")
        and r.get("selection_eligible")
    ]
    if not sources:
        raise ValueError(
            "Do not check explicitly measured analyzed SNP sources for this build. measurement type in the import."
        )
    ids = {r["id"] for r in sources}
    if any(
        p["a"] in ids
        and p["b"] in ids
        and p.get("common", 0) >= 1000
        and p.get("concordance", 1) < 0.98
        for p in report["pairs"]
    ):
        raise ValueError(
            "Strong source contradiction: check assignment first; no automatic best selection."
        )
    for r in sources:
        if r["id"] not in byid or digest(byid[r["id"]]["path"], cancel) != r["sha256"]:
            raise ValueError("Source status changed since analysis; re-analyze.")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(analysis / "vergleich.sqlite")
    fa = Fasta(reference)
    expected = {"GRCh37": 249250621, "GRCh38": 248956422}
    if any(
        fa.index[n][0] in expected.values() and fa.index[n][0] != expected[build]
        for n in ("1", "chr1")
        if n in fa.index
    ):
        db.close()
        fa.close()
        raise ValueError("FASTA chromosome 1 contradicts the selected build.")
    db.execute(
        "CREATE TEMP TABLE lineage(source TEXT PRIMARY KEY,root TEXT,is_vcf INTEGER)"
    )
    db.executemany(
        "INSERT INTO lineage VALUES(?,?,?)",
        [
            (
                r["id"],
                r.get("root_sha256", r["sha256"]),
                int(bool(r["stats"].get("is_vcf"))),
            )
            for r in sources
        ],
    )
    # The parameterised lineage join selects exactly these sources; no dynamic SQL IN list.
    query = """SELECT chrom,pos,count(DISTINCT gt),min(gt),max(high),count(DISTINCT lineage.root),min(CASE WHEN rsid LIKE 'rs%' THEN rsid END),max(lineage.is_vcf),group_concat(DISTINCT ref),group_concat(source||':'||high) FROM calls JOIN lineage USING(source) WHERE valid=1 AND build=? GROUP BY chrom,pos ORDER BY CASE WHEN chrom GLOB '[0-9]*' THEN CAST(chrom AS INTEGER) ELSE 100 END,chrom,pos"""
    totals = {
        "included": 0,
        "conflicts": 0,
        "insufficient_evidence": 0,
        "reference_errors": 0,
    }
    vcf = out / "best_selection.vcf"
    txt = out / "best_selection.txt"
    tsv = out / "best_selection.tsv"
    contributions = {
        r["id"]: {
            "source_id": r["id"],
            "provider": r["provider"],
            "file": Path(r["path"]).name,
            "primary_snps": 0,
            "supporting_snps": 0,
            "unique_snps": 0,
            "sha256": r["sha256"],
            "original_name": r.get("original_name"),
            "imported": r.get("imported"),
            "versions": r.get("versions", []),
            "declared_version": r.get("declared_version", ""),
            "build": r["build"],
            "root_sha256": r.get("root_sha256", r["sha256"]),
        }
        for r in sources
    }
    provider_counts = {}
    source_map = {r["id"]: r for r in sources}
    try:
        with (
            vcf.open("w", encoding="utf-8", newline="\n") as v,
            txt.open("w", encoding="utf-8", newline="\n") as raw,
            tsv.open("w", encoding="utf-8", newline="\n") as table,
            (out / "excluded.tsv").open("w", encoding="utf-8") as exclusions,
            (out / "variant_provenance.tsv").open("w", encoding="utf-8") as lineage_out,
        ):
            lineage_out.write(
                "chrom\tpos\tprimary_source_id\tprimary_sha256\tsupporting_source_ids\tsupporting_root_sha256\n"
            )
            v.write(
                "##fileformat=VCFv4.2\n##reference="
                + build
                + "\n##source=DNAWorkbench_BestSelection_SNP_v"
                + VERSION
                + '\n##FILTER=<ID=ResearchEvidence,Description="Observed SNP consensus; not clinical validation">\n##INFO=<ID=NSRC,Number=1,Type=Integer,Description="Concordant sources; independence not established">\n##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t'
                + person
                + "\n"
            )
            raw.write(
                "# DNA Workbench observed SNP selection; not an original provider test\n# build="
                + build
                + "\n# rsid\tchromosome\tposition\tgenotype\n"
            )
            table.write("rsid\tchromosome\tposition\tgenotype\tsources\n")
            exclusions.write("chrom\tpos\treason\n")
            for (
                chromosome,
                pos,
                distinct,
                gt,
                high,
                count,
                rsid,
                has_vcf,
                refs,
                members,
            ) in db.execute(query, [build]):
                if totals["included"] % 10000 == 0 and cancel():
                    raise InterruptedError(
                        "Creation cancelled; partial output is not registered."
                    )
                reason = (
                    "conflicts"
                    if distinct != 1
                    else "insufficient_evidence"
                    if not high and count < 2
                    else ""
                )
                if not reason:
                    try:
                        ref = fa.base(chromosome, pos)
                        if any(r and r != ref for r in (refs or "").split(",")):
                            raise ValueError("VCF-REF does not agree with FASTA.")
                    except ValueError:
                        reason = "reference_errors"
                if reason:
                    totals[reason] += 1
                    exclusions.write(f"{chromosome}\t{pos}\t{reason}\n")
                    continue
                alt = sorted(set(gt) - {ref})
                alleles = [ref] + alt
                indices = "/".join(str(alleles.index(a)) for a in gt)
                rsid = rsid if re.fullmatch("rs[0-9]+", rsid or "") else "."
                v.write(
                    f"{chromosome}\t{pos}\t{rsid}\t{ref}\t{','.join(alt) or '.'}\t.\tResearchEvidence\tNSRC={count}\tGT\t{indices}\n"
                )
                raw.write(f"{rsid}\t{chromosome}\t{pos}\t{gt}\n")
                table.write(f"{rsid}\t{chromosome}\t{pos}\t{gt}\t{count}\n")
                totals["included"] += 1
                supporting = [
                    (item.split(":")[0], int(item.split(":")[1]))
                    for item in members.split(",")
                ]
                winner = max(
                    supporting,
                    key=lambda item: (
                        item[1],
                        source_map[item[0]]["stats"].get("is_vcf", False),
                        source_map[item[0]].get("qc_supported", 0)
                        / max(1, source_map[item[0]].get("called", 0)),
                        item[0],
                    ),
                )[0]
                lineage_out.write(
                    str(chromosome)
                    + "\t"
                    + str(pos)
                    + "\t"
                    + winner
                    + "\t"
                    + source_map[winner]["sha256"]
                    + "\t"
                    + ",".join(sid for sid, _ in supporting)
                    + "\t"
                    + ",".join(
                        sorted(
                            {
                                source_map[sid].get(
                                    "root_sha256", source_map[sid]["sha256"]
                                )
                                for sid, _ in supporting
                            }
                        )
                    )
                    + "\n"
                )
                contributions[winner]["primary_snps"] += 1
                if count == 1:
                    contributions[winner]["unique_snps"] += 1
                for sid, _ in supporting:
                    contributions[sid]["supporting_snps"] += 1
                primary_provider = contributions[winner]["provider"]
                for provider in {
                    contributions[sid]["provider"] for sid, _ in supporting
                }:
                    item = provider_counts.setdefault(
                        provider,
                        {"provider": provider, "primary_snps": 0, "supporting_snps": 0},
                    )
                    item["supporting_snps"] += 1
                provider_counts[primary_provider]["primary_snps"] += 1
        if not totals["included"]:
            raise ValueError("No SNPs meet the consensus rules.")
        # Independent output parser checks all genotype records against both text exports.
        validation = validate_outputs(vcf, txt, tsv, totals["included"])
        reference_after = Path(reference).stat()
        if (reference_before.st_size, reference_before.st_mtime_ns) != (
            reference_after.st_size,
            reference_after.st_mtime_ns,
        ):
            raise ValueError("Reference changed during creation.")
        for item in [*contributions.values(), *provider_counts.values()]:
            item.update(
                primary_percent=100 * item["primary_snps"] / totals["included"],
                support_percent=100 * item["supporting_snps"] / totals["included"],
            )
        result = {
            "version": VERSION,
            "person": person,
            "build": build,
            "origin": "own_generated",
            "label": "Best Selection · beobachtete SNPs",
            "scope": "SNP-only research selection; no complete genome, indels, SVs, reads or imputation",
            "created": NOW(),
            "analysis": str(analysis),
            "sources": [r["sha256"] for r in sources],
            "analyzed_snapshot": sorted(
                {
                    r["sha256"]
                    for r in report["sources"]
                    if r["status"] != "derived-not-independent"
                }
            ),
            "statistics": totals,
            "validation": validation,
            "reference": str(reference),
            "reference_sha256": reference_sha256,
            "source_contributions": list(contributions.values()),
            "source_aliases": [
                {
                    "id": x["id"],
                    "sha256": x["sha256"],
                    "provider": x["provider"],
                    "original_name": x["original_name"],
                    "stored_path": x["path"],
                    "imported": x["created"],
                    "declared_version": x.get("declared_version", ""),
                    "versions": x.get("versions", []),
                }
                for x in rows
                if x["sha256"] in {r["sha256"] for r in sources}
            ],
            "provider_contributions": list(provider_counts.values()),
            "contribution_method": "One primary attribution per included SNP: original QC support, VCF evidence, source QC rate, deterministic source ID tie-break. Supporting percentages overlap; neither attribution nor concordance establishes independent measurements.",
        }
        result["files"] = {p.name: digest(p, cancel) for p in (vcf, txt, tsv)}
        (out / "manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with (out / "source-contributions.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "provider",
                    "file",
                    "primary_snps",
                    "primary_percent",
                    "supporting_snps",
                    "support_percent",
                ],
                delimiter="\t",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(result["source_contributions"])
        log(
            "Ausgaben validiert: "
            + str(totals["included"])
            + "SNPs. Not yet activated as preferred."
        )
        return result
    finally:
        db.close()
        fa.close()


def validate_outputs(vcf, txt, tsv, expected):
    h = hashlib.sha256()
    count = 0
    chromosomes = {}
    xhet = 0
    for c in calls(vcf, {}):
        h.update(f"{c[0]}\t{c[1]}\t{c[2]}\n".encode())
        count += 1
        chromosomes[c[0]] = chromosomes.get(c[0], 0) + 1
        if c[0] == "X" and len(set(c[2])) > 1:
            xhet += 1
    fingerprint = h.hexdigest()
    for path in (txt, tsv):
        h = hashlib.sha256()
        n = 0
        with Path(path).open(encoding="utf-8") as stream:
            for line in stream:
                if line.startswith("#") or line.startswith("rsid\t"):
                    continue
                c = line.strip().split("\t")
                h.update(f"{c[1]}\t{c[2]}\t{c[3]}\n".encode())
                n += 1
        if n != expected or h.hexdigest() != fingerprint:
            raise ValueError("Issue roundtrip does not match.")
    if count != expected:
        raise ValueError("VCF call number is not correct.")
    hint = inspector.chromosome_hint(
        {
            "x_called": chromosomes.get("X", 0),
            "y_called": chromosomes.get("Y", 0),
            "x_heterozygous": xhet,
        }
    )
    return {
        "passed": True,
        "roundtrip_snps": count,
        "genotype_digest": fingerprint,
        "clinical_validation": False,
        "chromosome_counts": chromosomes,
        "chromosomes_hint": hint,
    }


def activate(person, folder, cancel=lambda: False):
    folder = Path(folder).resolve()
    r = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if r.get("person") != person or not r.get("validation", {}).get("passed"):
        raise ValueError("No validated set for that person.")
    rows = source_store.listing(person)
    if (
        r.get("analyzed_snapshot") is not None
        and sorted({x["sha256"] for x in rows if x.get("origin") != "own_generated"})
        != r["analyzed_snapshot"]
    ):
        raise ValueError(
            "New sources have been added since analysis. Recalculate selection before it is activated."
        )
    if not set(r["sources"]) <= {x["sha256"] for x in rows}:
        raise ValueError("Ursprungsquellen fehlen.")
    for row in rows:
        if (
            row["sha256"] in r["sources"]
            and digest(row["path"], cancel) != row["sha256"]
        ):
            raise ValueError("Source of origin changed; renew analysis.")
    for name, sha in r["files"].items():
        if Path(name).name != name or digest(folder / name, cancel) != sha:
            raise ValueError("The output has been changed.")
    r["source_state"] = [
        {
            "path": x["path"],
            "bytes": Path(x["path"]).stat().st_size,
            "mtime_ns": Path(x["path"]).stat().st_mtime_ns,
        }
        for x in rows
        if x["sha256"] in r["sources"]
    ]
    r["output_state"] = {
        "bytes": (folder / "best_selection.vcf").stat().st_size,
        "mtime_ns": (folder / "best_selection.vcf").stat().st_mtime_ns,
    }
    r["imported_snapshot"] = sorted(
        {x["sha256"] for x in rows if x.get("origin") != "own_generated"}
    )
    # Generated files stay in their job folder: register them without making another copy.
    with closing(source_store.connect(person)) as db, db:
        annotation_schema(db)
        batch = __import__("uuid").uuid4().hex
        db.execute(
            "INSERT INTO batches VALUES(?,?,?,?,?,?,?)",
            (
                batch,
                "DNA Workbench",
                r["label"],
                r["build"],
                "Measured",
                "Derived; no independent measurement",
                NOW(),
            ),
        )
        prior = db.execute(
            "SELECT payload FROM preferred_sets WHERE build=?", (r["build"],)
        ).fetchone()
        if prior and json.loads(prior[0]).get("folder") == str(folder):
            db.execute("DELETE FROM batches WHERE id=?", (batch,))
            return {"activated": True, "already_active": True, "build": r["build"]}
        for name, sha in r["files"].items():
            p = folder / name
            rel = str(p.relative_to(source_store.ROOT.resolve()))
            fid = __import__("uuid").uuid4().hex
            db.execute(
                "INSERT OR IGNORE INTO blobs VALUES(?,?,?,?,?,?)",
                (
                    sha,
                    rel,
                    p.stat().st_size,
                    source_store.classify(name),
                    r["build"],
                    "[]",
                ),
            )
            db.execute(
                "INSERT INTO files(id,batch_id,sha256,original_name,original_path,created) VALUES(?,?,?,?,?,?)",
                (fid, batch, sha, name, str(p), NOW()),
            )
            db.execute(
                "INSERT OR REPLACE INTO file_annotations VALUES(?,?,?,?,?)",
                (
                    fid,
                    "own_generated",
                    "best_selection",
                    json.dumps(
                        {"manifest": str(folder / "manifest.json"), "scope": r["scope"]}
                    ),
                    NOW(),
                ),
            )
        for row in rows:
            if row.get("origin") == "own_generated" and row["build"] == r["build"]:
                db.execute(
                    "UPDATE file_annotations SET lifecycle='superseded' WHERE file_id=?",
                    (row["id"],),
                )
            if row["sha256"] in r["sources"]:
                old = db.execute(
                    "SELECT payload FROM file_annotations WHERE file_id=?", (row["id"],)
                ).fetchone()
                payload = json.loads(old[0]) if old else {}
                payload["used_in"] = str(folder)
                db.execute(
                    "INSERT OR REPLACE INTO file_annotations VALUES(?,?,?,?,?)",
                    (
                        row["id"],
                        "imported",
                        "used_in_selection",
                        json.dumps(payload),
                        NOW(),
                    ),
                )
        r["folder"] = str(folder)
        r["preferred_for"] = ["vcf_qc", "roh", "beagle", "pgs"]
        r["auto_refresh"] = False
        db.execute(
            "INSERT OR REPLACE INTO preferred_sets VALUES(?,?,?)",
            (r["build"], json.dumps(r), NOW()),
        )
        db.execute(
            "INSERT OR REPLACE INTO derived_profile VALUES(?,?,?)",
            (
                "best_selection",
                json.dumps(
                    {
                        "build": r["build"],
                        "snps": r["statistics"]["included"],
                        "chromosome_counts": r["validation"].get(
                            "chromosome_counts", {}
                        ),
                        "chromosomes_hint": r["validation"].get(
                            "chromosomes_hint", "Undetermined"
                        ),
                        "providers": r.get("provider_contributions", []),
                        "source": str(folder / "manifest.json"),
                        "status": "Observed SNP selection; no clinical validation",
                    }
                ),
                NOW(),
            ),
        )
    pointer = source_store.ROOT / "Projects/BestSelection" / person / "current.json"
    atomic(pointer, r)
    return {
        "activated": True,
        "build": r["build"],
        "scope": r["scope"],
        "preferred_for": r["preferred_for"],
    }


def atomic(path, value):
    import uuid

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def queue_path(person):
    source_store.folder(person)  # validate profile ID before constructing paths
    return (
        source_store.ROOT
        / "DNA_Software/UserData/Launcher/Refresh"
        / (person + ".json")
    )


def summary(person):
    rows = source_store.listing(person)
    sets = []
    with closing(source_store.connect(person)) as db:
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='preferred_sets'"
        ).fetchone():
            sets = [
                json.loads(x[0])
                for x in db.execute(
                    "SELECT payload FROM preferred_sets ORDER BY updated DESC"
                )
            ]
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='preferred_asset_sets'"
        ).fetchone():
            sets += [
                json.loads(x[0])
                for x in db.execute(
                    "SELECT payload FROM preferred_asset_sets ORDER BY updated DESC"
                )
            ]
    sets.sort(key=lambda r: r.get("created", ""), reverse=True)
    hashes = sorted({x["sha256"] for x in rows if x.get("origin") != "own_generated"})
    for r in sets:
        r["needs_refresh"] = hashes != r.get("imported_snapshot")
    try:
        queue = json.loads(queue_path(person).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        queue = {}
    return {"sets": sets, "refresh": queue}


def note_new_sources(person):
    state = summary(person)
    if not state["sets"]:
        return False
    if not state["sets"][0]["needs_refresh"]:
        return False
    if state["refresh"].get("status") in ("queued_by_user", "running"):
        return True
    import uuid

    atomic(
        queue_path(person),
        {
            "person": person,
            "build": state["sets"][0]["build"],
            "nonce": uuid.uuid4().hex,
            "status": "available",
            "created": NOW(),
        },
    )
    return True


@contextmanager
def refresh_lock(person):
    path = queue_path(person).with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def refresh_available(person):
    try:
        with refresh_lock(person):
            return True
    except OSError:
        return False


def refresh(person, out, log=print, cancel=lambda: False):
    with refresh_lock(person):
        return _refresh(person, out, log, cancel)


def _refresh(person, out, log=print, cancel=lambda: False):
    marker = queue_path(person)
    try:
        request = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        request = {"person": person, "build": "GRCh38", "nonce": ""}

    def finish(status, error=""):
        try:
            current = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = request
        if current.get("nonce") == request.get("nonce"):
            atomic(marker, dict(current, status=status, error=error, finished=NOW()))

    try:
        build = request["build"]
        root = source_store.ROOT
        reference = root / (
            "References/FASTA_GRCh38/GRCh38_full_analysis_set_plus_decoy_hla.fa"
            if build == "GRCh38"
            else "References/FASTA_GRCh37/hs37d5.fa"
        )
        analysis = Path(out) / "Analyse"
        selection = Path(out) / "BestSelection"
        analyze(
            person,
            analysis,
            log,
            cancel,
            target="GRCh38" if build == "GRCh38" else "separate",
            chain=root / "References/LiftOver/hg19ToHg38.over.chain.gz",
            reference=reference,
        )
        generate(person, analysis, selection, build, reference, log, cancel)
        result = activate(person, selection, cancel)
        finish("completed")
        return result
    except BaseException as error:
        finish(
            "cancelled" if isinstance(error, InterruptedError) else "failed", str(error)
        )
        raise
