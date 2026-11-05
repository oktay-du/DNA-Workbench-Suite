"""Small deterministic synthetic fixtures and an explicit, idempotent local demo import."""

from pathlib import Path
import gzip, hashlib, json, random, threading

ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).parent
VERSION = "synthetic-demo-1.1"
LOCK = threading.Lock()
PEOPLE = [
    ("DEMO_Alex", "Alex Example"),
    ("DEMO_Robin", "Robin Example"),
    ("DEMO_Sam", "Sam Example"),
    ("DEMO_Taylor", "Taylor Example"),
]
SAMPLE_FILES = (
    [
        "Profiles/" + pid + "/" + name
        for pid, _ in PEOPLE
        for name in ("synthetic.vcf", "synthetic-chip.txt")
    ]
    + [
        "Formats/" + name
        for name in (
            "synthetic-reference.fasta",
            "synthetic-reference.fasta.fai",
            "synthetic_R1.fastq",
            "synthetic_R2.fastq",
            "synthetic_R1.fastq.gz",
            "synthetic_R2.fastq.gz",
            "synthetic-intervals.bed",
            "synthetic.sam",
            "synthetic.bam",
            "synthetic.bam.bai",
            "synthetic.cram",
            "synthetic.cram.crai",
        )
    ]
    + [
        "Results/" + name
        for name in (
            "illustrative-ancestry.json",
            "illustrative-segments.csv",
            "ancestry-composition.csv",
            "family-tree.json",
            "family.ged",
        )
    ]
    + ["README.md"]
)
SAMPLE_FILES += ["Results/synthetic-provider-report.pdf"]


def generate(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1032026)

    def text(name, value):
        p = folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value, encoding="utf-8", newline="\n")

    ref = "".join(rng.choice("ACGT") for _ in range(12000))
    text(
        "Formats/synthetic-reference.fasta",
        ">1 synthetic educational contig; NOT a human reference genome\n"
        + "\n".join(ref[i : i + 80] for i in range(0, len(ref), 80))
        + "\n",
    )
    alt = lambda a: next(x for x in "ACGT" if x != a)
    for index, (pid, label) in enumerate(PEOPLE):
        vcf = (
            '##fileformat=VCFv4.2\n##source=DNAWorkbenchSynthetic\n##DNAWorkbenchSynthetic=true\n##reference=synthetic-educational-v1\n##contig=<ID=1,length=12000>\n##FORMAT=<ID=GT,Number=1,Type=String,Description="Synthetic genotype">\n##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Synthetic depth">\n##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Synthetic genotype quality">\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t'
            + pid
            + "\n"
        )
        chip = "# DNAWorkbenchSynthetic=true\n# Synthetic SNP table; NOT personal DNA, no human reference build\n# rsid\tchromosome\tposition\tgenotype\n"
        for i in range(1, 3001):
            father = ["0/0", "0/1", "1/1"][i % 3]
            mother = ["0/1", "1/1", "0/0"][(i // 3) % 3]
            child = father.split("/")[i % 2] + "/" + mother.split("/")[(i // 2) % 2]
            pos = i * 3
            g = [child, father, mother, ["0/0", "0/1", "1/1"][(i * 7 + i // 7) % 3]][
                index
            ]
            a = ref[pos - 1]
            b = alt(a)
            vcf += (
                f"1\t{pos}\tsynthetic_{i}\t{a}\t{b}\t60\tPASS\t.\tGT:DP:GQ\t{g}:30:60\n"
            )
            chip += (
                f"rs{900000000 + i}\t1\t{pos}\t"
                + "".join([a, b][int(x)] for x in g.split("/"))
                + "\n"
            )
        text(f"Profiles/{pid}/synthetic.vcf", vcf)
        text(f"Profiles/{pid}/synthetic-chip.txt", chip)
    fastq = ""
    for i in range(40):
        seq = ref[i * 7 : i * 7 + 150]
        fastq += f"@synthetic_read_{i}\n{seq}\n+\n" + ("I" * len(seq)) + "\n"
    text("Formats/synthetic_R1.fastq", fastq)
    text("Formats/synthetic_R2.fastq", fastq)
    for name in ["synthetic_R1.fastq", "synthetic_R2.fastq"]:
        with gzip.GzipFile(
            filename=str(folder / "Formats" / (name + ".gz")), mode="wb", mtime=0
        ) as f:
            f.write((folder / "Formats" / name).read_bytes())
    text(
        "Formats/synthetic-intervals.bed",
        "1\t0\t800\tSynthetic_region_A\n1\t1200\t2300\tSynthetic_region_B\n",
    )
    sam = "@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:1\tLN:12000\n@RG\tID:demo\tSM:SYNTHETIC\tPL:ILLUMINA\n"
    for i in range(20):
        sam += (
            f"synthetic_{i}\t0\t1\t{i * 20 + 1}\t60\t150M\t*\t0\t0\t{ref[i * 20 : i * 20 + 150]}\t"
            + ("I" * 150)
            + "\tRG:Z:demo\n"
        )
    text("Formats/synthetic.sam", sam)
    visual = {
        "person": "DEMO_Alex",
        "provider": "DNA Workbench SYNTHETIC illustration",
        "model": "Manually authored map example; not inferred from genotypes",
        "version": VERSION,
        "data_date": "2026-11-03",
        "source_note": "Entirely synthetic percentages for software demonstration. No genetic ancestry was calculated.",
        "regions": [
            {
                "name": "Sweden · synthetic illustration",
                "percent": 45,
                "lat": 60,
                "lon": 18,
            },
            {
                "name": "Japan · synthetic illustration",
                "percent": 35,
                "lat": 36,
                "lon": 138,
            },
            {
                "name": "Peru · synthetic illustration",
                "percent": 20,
                "lat": -10,
                "lon": -75,
            },
        ],
        "traits": {},
    }
    text("Results/illustrative-ancestry.json", json.dumps(visual, indent=2))
    text(
        "Results/illustrative-segments.csv",
        "a,b,chrom,start,end,cm,snps\nDEMO_Alex,DEMO_Taylor,1,1000000,25000000,28,2200\nDEMO_Alex,DEMO_Taylor,2,2000000,21000000,24,1800\nDEMO_Alex,DEMO_Taylor,5,3000000,19000000,22,1400\n",
    )
    text(
        "Results/ancestry-composition.csv",
        "# SYNTHETIC illustration; confidence not applicable\nAncestry,Chromosome,Start Point,End Point\nDemonstration A,1,0,4500\nDemonstration B,1,4500,9000\n",
    )
    text(
        "Results/family-tree.json",
        json.dumps(
            {
                "format": "DNAWorkbenchSyntheticTree",
                "version": 1,
                "people": [{"id": p, "name": n} for p, n in PEOPLE],
                "note": "Synthetic JSON structure; not a real 23andMe export schema",
            },
            indent=2,
        ),
    )
    text(
        "Results/family.ged",
        "0 HEAD\n1 SOUR DNAWorkbenchSynthetic\n1 GEDC\n2 VERS 5.5.1\n1 CHAR UTF-8\n0 @A@ INDI\n1 NAME Alex /Example/\n0 @R@ INDI\n1 NAME Robin /Example/\n0 @S@ INDI\n1 NAME Sam /Example/\n0 @F@ FAM\n1 HUSB @R@\n1 WIFE @S@\n1 CHIL @A@\n0 TRLR\n",
    )
    # Tiny, deterministic text-PDF fixture; no external renderer or personal report.
    lines = [
        "DNA Workbench - SYNTHETIC software fixture",
        "Person: Alex Example (fictional)",
        "Report statement: Lactose intolerance not reported.",
        "Not a human test. Not a clinical result.",
        "This statement is authored for document retrieval testing.",
    ]
    content = (
        "BT /F1 14 Tf 50 780 Td "
        + "".join(
            ("0 -28 Td " if i else "")
            + "("
            + s.replace("(", "\\(").replace(")", "\\)")
            + ") Tj\n"
            for i, s in enumerate(lines)
        )
        + " ET"
    )
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        "<< /Length "
        + str(len(content.encode()))
        + " >>\nstream\n"
        + content
        + "\nendstream",
    ]
    raw = b"%PDF-1.4\n"
    offsets = [0]
    for i, o in enumerate(objects, 1):
        offsets.append(len(raw))
        raw += (str(i) + " 0 obj\n" + o + "\nendobj\n").encode()
    start = len(raw)
    raw += (
        "xref\n0 6\n0000000000 65535 f \n"
        + "".join(f"{n:010d} 00000 n \n" for n in offsets[1:])
        + "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(start)
        + "\n%%EOF\n"
    ).encode()
    pdf = folder / "Results/synthetic-provider-report.pdf"
    pdf.parent.mkdir(exist_ok=True)
    pdf.write_bytes(raw)
    text(
        "README.md",
        "# Synthetic sample data\n\nThese are entirely artificial fixtures, not personal DNA, real ancestry results, clinical examples or a validated human reference. MIT licensed as part of DNA Workbench.\n\nUse the app’s Sample data page or `DNA.cmd call sample.create` to add four clearly labelled demo profiles. Loading is explicit and does not replace existing people. The loader copies tiny sample files into local archives; packaged samples stay available.\n\nThe 12,000-base reference is synthetic. Do not label it GRCh37/38, use it for human liftover, or interpret its artificial rs-identifiers clinically. Quality values and ancestry percentages are authored fixtures. The map and segment tables illustrate imported results; they are not derived from these genotype files. Missing WGS, Y/mtDNA and health evidence stays missing.\n\nVCF, chip TXT, FASTA, FASTQ/gzip, SAM, BED, CSV, JSON and GEDCOM are included. BAM/CRAM and indices may be included when regenerated with SAMtools. Do not add real files to this public folder.\n",
    )
    refresh_manifest(folder)


def refresh_manifest(folder):
    folder = Path(folder)
    files = []
    for name in SAMPLE_FILES:
        p = folder / name
        if p.is_file():
            files.append(
                {
                    "path": name,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                    "bytes": p.stat().st_size,
                }
            )
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "version": VERSION,
                "synthetic": True,
                "personal_data": False,
                "people": [{"id": p, "name": n} for p, n in PEOPLE],
                "files": files,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def validate(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("synthetic") is not True
        or manifest.get("personal_data") is not False
    ):
        raise ValueError("Not a public synthetic sample manifest")
    for row in manifest["files"]:
        if row["path"] not in SAMPLE_FILES:
            raise ValueError("Unapproved sample file")
        p = (folder / row["path"]).resolve()
        if not p.is_relative_to(folder) or not p.is_file():
            raise ValueError("Invalid sample path")
        if hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Sample checksum mismatch: " + row["path"])
    return manifest


def is_sample(person):
    import family

    with family.connect() as db:
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sample_profiles'"
        ).fetchone():
            return False
        return bool(
            db.execute(
                "SELECT 1 FROM sample_profiles WHERE person=?", (person,)
            ).fetchone()
        )


def info():
    manifest = validate(ROOT / "Samples")
    return {
        "version": VERSION,
        "synthetic": True,
        "people": manifest["people"],
        "files": manifest["files"],
        "bytes": sum(x["bytes"] for x in manifest["files"]),
        "notice": "Artificial educational fixtures. No real human genome, health result or genetically inferred ancestry.",
    }


def create():
    import family, source_store, person_profile, inspector, visual_store, matching, genealogy_research, profile_documents

    folder = ROOT / "Samples"
    validate(folder)
    with LOCK:
        with family.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS sample_profiles(person TEXT PRIMARY KEY,version TEXT)"
            )
            for pid, label in PEOPLE:
                existing = db.execute(
                    "SELECT label FROM people WHERE id=?", (pid,)
                ).fetchone()
                if (
                    existing
                    and not db.execute(
                        "SELECT 1 FROM sample_profiles WHERE person=?", (pid,)
                    ).fetchone()
                ):
                    raise ValueError(
                        "Sample ID conflicts with an existing person; no overwrite"
                    )
            if all(
                db.execute(
                    "SELECT 1 FROM sample_profiles WHERE person=? AND version=?",
                    (pid, VERSION),
                ).fetchone()
                for pid, _ in PEOPLE
            ):
                return {
                    "person": "DEMO_Alex",
                    "people": [p for p, _ in PEOPLE],
                    "already_loaded": True,
                }
            for pid, label in PEOPLE:
                db.execute(
                    "INSERT OR IGNORE INTO people VALUES(?,?,0)",
                    (pid, label + " · SYNTHETIC"),
                )
                db.execute(
                    "INSERT OR REPLACE INTO sample_profiles VALUES(?,?)",
                    (pid, "loading:" + VERSION),
                )
        for pid, label in PEOPLE:
            person_profile.save(
                pid,
                {
                    "name": label + " · SYNTHETIC",
                    "notes": "Entirely synthetic demo. No real DNA, health results or verified ancestry.",
                },
            )
            files = list((folder / "Profiles" / pid).glob("*"))
            if pid == "DEMO_Alex":
                files += [
                    folder / "Formats/synthetic-reference.fasta",
                    folder / "Formats/synthetic_R1.fastq.gz",
                    folder / "Formats/synthetic_R2.fastq.gz",
                ]
            if not source_store.listing(pid):
                source_store.import_batch(
                    pid,
                    [str(p) for p in files],
                    "DNA Workbench Synthetic",
                    VERSION,
                    measurement="Synthetic / not measured human DNA",
                    storage_mode="copy",
                    log=lambda _: None,
                )
            checked = source_store.folder(pid) / "SampleChecks"
            inspector.check_batch(
                pid,
                [r["path"] for r in source_store.listing(pid)],
                checked,
                lambda _: None,
            )
        family.add_link(
            "DEMO_Robin",
            "DEMO_Alex",
            "father",
            "Synthetic documented relationship, not DNA validation",
        )
        family.add_link(
            "DEMO_Sam",
            "DEMO_Alex",
            "mother",
            "Synthetic documented relationship, not DNA validation",
        )
        if not any(
            x["person"] == "DEMO_Alex" and x["data"].get("version") == VERSION
            for x in visual_store.listing()
        ):
            visual_store.save(
                json.loads(
                    (folder / "Results/illustrative-ancestry.json").read_text(
                        encoding="utf-8"
                    )
                )
            )
        text = (folder / "Results/illustrative-segments.csv").read_text(
            encoding="utf-8"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        with family.connect() as db:
            matching.init(db)
            segments = bool(
                db.execute(
                    "SELECT 1 FROM research_segments WHERE sha256=?", (sha,)
                ).fetchone()
            )
        if not segments:
            matching.import_segments(
                {
                    "build": "GRCh38",
                    "source": "SYNTHETIC visualization fixture; not inferred IBD",
                    "text": text,
                }
            )
        text = (folder / "Results/family.ged").read_text(encoding="utf-8")
        sha = hashlib.sha256(text.encode()).hexdigest()
        if not any(x["sha256"] == sha for x in genealogy_research.index()["documents"]):
            genealogy_research.import_file(
                {"text": text, "label": "Synthetic Example family"}
            )
        if (folder / "Results/synthetic-provider-report.pdf").is_file():
            profile_documents.index_file(
                "DEMO_Alex",
                folder / "Results/synthetic-provider-report.pdf",
                "SYNTHETIC report example",
                "2026-11-04",
                log=lambda _: None,
            )
        with family.connect() as db:
            db.execute(
                "UPDATE sample_profiles SET version=? WHERE person IN (?,?,?,?)",
                (VERSION, *(p for p, _ in PEOPLE)),
            )
        return {
            "person": "DEMO_Alex",
            "people": [p for p, _ in PEOPLE],
            "already_loaded": False,
            "notice": "Synthetic files and illustrative reports; no real genetic inference.",
        }


if __name__ == "__main__":
    import sys

    generate(sys.argv[1])
