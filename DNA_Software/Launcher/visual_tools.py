import network_io

"""Local visualization adapters. Scraped links never become executable recipes."""
from pathlib import Path
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser
import base64, datetime, gzip, hashlib, io, mimetypes, os, re, subprocess, sys, tarfile, urllib.request, uuid, zipfile
import portable_json as json

APP = Path(__file__).parent
ROOT = APP.parents[1]
BASE = ROOT / "DNA_Software/Windows/VisualTools"
RUNS = ROOT / "Projects/Visualisierungen"
CACHE = ROOT / "DNA_Software/UserData/Launcher/Visualization Catalogue"
LOCK = json.loads((APP / "visual-packages.json").read_text(encoding="utf-8"))
SOURCES = [
    "https://github.com/genome-spy/genome-spy",
    "https://github.com/topics/genome-visualization",
    "https://cmdcolin.github.io/awesome-genome-visualization/",
    "https://pavelavdeyev.github.io/software/",
    "https://moshi4.github.io/pyGenomeViz/",
]
CURATED = [
    {
        "id": "genomespy",
        "name": "GenomeSpy",
        "url": SOURCES[0],
        "license": "MIT",
        "formats": "VCF, BED, GFF",
        "description": "Interactive position/quality view of a selected genome window. No origin or disease calculation.",
    },
    {
        "id": "igvjs",
        "name": "IGV.js",
        "url": "https://github.com/igvteam/igv.js",
        "license": "MIT",
        "formats": "VCF, BAM, CRAM, BED, GFF + lokale FASTA/FAI",
        "description": "Reads, variants and annotations directly in the EXE. Large compressed files require suitable indices.",
    },
    {
        "id": "jbrowse",
        "name": "JBrowse 2 Web",
        "url": "https://github.com/GMOD/jbrowse-components",
        "license": "Apache-2.0",
        "formats": "VCF, BAM, CRAM, BED, GFF + lokale FASTA/FAI",
        "description": "Extensible genome browser within the EXE; reference and tracks remain local.",
    },
    {
        "id": "pygenomeviz",
        "name": "pyGenomeViz",
        "url": "https://github.com/moshi4/pyGenomeViz",
        "license": "MIT",
        "formats": "VCF, BED, GFF",
        "description": "SVG/PNG diagram of a genome window. The adapter draws variants or features; no automatic sequence comparison analysis.",
    },
    {
        "id": "pycirclize",
        "name": "pyCirclize",
        "url": "https://github.com/moshi4/pyCirclize",
        "license": "MIT",
        "formats": "VCF, BED, GFF",
        "description": "Circular representation of a selected genome window with variants and annotations. No measured DNA coverage.",
    },
    {
        "id": "dnafeaturesviewer",
        "name": "DNA Features Viewer",
        "url": "https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer",
        "license": "MIT",
        "formats": "VCF, BED, GFF",
        "description": "Labeled local genome sections as SVG, PNG and PDF; no automatic health assessment.",
    },
]


def now():
    return datetime.datetime.now().astimezone().isoformat()


def digest(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def get(url, limit=30_000_000):
    if urlparse(url).scheme != "https":
        raise ValueError("Only HTTPS sources are allowed.")
    with network_io.open_https(
        urllib.request.Request(
            url, headers={"User-Agent": "DNAWorkbench-visual-catalog/1"}
        ),
        timeout=40,
    ) as r:
        data = r.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Source exceeds the size limit.")
        return data


def installed(tool):
    try:
        m = json.loads((BASE / tool / "installation.json").read_text(encoding="utf-8"))
        if m["version"] != LOCK[tool]["version"]:
            return False
        return all(
            (BASE / tool / p).is_file() and digest(BASE / tool / p) == h
            for p, h in m["files"].items()
        )
    except (OSError, ValueError, KeyError):
        return False


def listing():
    rows = [
        dict(
            x,
            installable=x["id"] in LOCK,
            installed=installed(x["id"]),
            version=LOCK.get(x["id"], {}).get("version", ""),
            source="Editorial review",
        )
        for x in CURATED
    ]
    try:
        extra = json.loads((CACHE / "catalog.json").read_text(encoding="utf-8"))
        rows += [
            x
            for x in extra["tools"]
            if x.get("url", "").rstrip("/").lower()
            != "https://github.com/angshuman1211/vestige"
        ]
    except (OSError, ValueError):
        pass
    return {
        "tools": rows,
        "sources": SOURCES,
        "note": "Only editorially tested adapters can be installed, and discovered project links are never executed as commands.",
    }


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("https://github.com/"):
                self.urls.append(href)


def refresh():
    CACHE.mkdir(parents=True, exist_ok=True)
    found = {}
    errors = []
    receipts = []

    def add(name, url, tags, source):
        if (
            not url.startswith("https://")
            or url.rstrip("/").lower() == "https://github.com/angshuman1211/vestige"
        ):
            return
        key = url.rstrip("/").lower()
        if key in {r["url"].rstrip("/").lower() for r in CURATED}:
            return
        found.setdefault(
            key,
            {
                "id": "discovery-" + hashlib.sha256(key.encode()).hexdigest()[:16],
                "name": str(name)[:140],
                "url": url,
                "license": "Check before use",
                "formats": "Examine project documentation",
                "description": " · ".join(tags)[:700]
                or "Discovered project; not yet tested execution adapter.",
                "source": source,
                "installable": False,
                "installed": False,
                "version": "",
            },
        )

    urls = [
        (
            "awesome",
            "https://raw.githubusercontent.com/cmdcolin/awesome-genome-visualization/main/TOOLS.json",
        ),
        ("topic", "https://github.com/topics/genome-visualization"),
        ("pavel", "https://pavelavdeyev.github.io/software/"),
    ]
    for name, url in urls:
        try:
            data = get(url, 8_000_000)
            (CACHE / (name + ".source")).write_bytes(data)
            receipts.append(
                {
                    "url": url,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "fetched": now(),
                }
            )
            if name == "awesome":
                for row in json.loads(data)["tools"]:
                    add(
                        row["name"],
                        row.get("url", ""),
                        row.get("tags", []),
                        "https://cmdcolin.github.io/awesome-genome-visualization/",
                    )
            else:
                parser = Links()
                parser.feed(data.decode("utf-8"))
                for link in parser.urls:
                    parsed = urlparse(link)
                    parts = parsed.path.strip("/").split("/")
                    if len(parts) == 2 and parts[0] not in (
                        "topics",
                        "sponsors",
                        "collections",
                        "features",
                        "settings",
                        "orgs",
                    ):
                        add("/".join(parts), link, [], url)
        except Exception as e:
            errors.append({"url": url, "error": str(e)})
    result = {
        "checked": now(),
        "tools": sorted(found.values(), key=lambda r: r["name"].lower()),
        "sources": receipts,
        "errors": errors,
    }
    if not found:
        raise ValueError(
            "No projects loaded; the previous catalog was retained. " + str(errors)
        )
    atomic(CACHE / "catalog.json", result)
    return {"status": str(len(found)) + " weitere Projekte geladen", "errors": errors}


def safe_member(name):
    p = Path(name)
    if (
        name.startswith("/")
        or p.is_absolute()
        or ".." in p.parts
        or ":" in name
        or "\\" in name
    ):
        raise ValueError("Inadmissible archival path.")
    return p


def install(tool):
    if tool not in LOCK:
        raise ValueError(
            "For this project, there is no tested installation adapter yet. Open project page."
        )
    item = LOCK[tool]
    if item["kind"] == "pip" and os.name != "nt":
        raise ValueError("This installation recipe requires Windows.")
    dest = BASE / tool
    dest.mkdir(parents=True, exist_ok=True)
    if installed(tool):
        return {"status": "Bereits eingerichtet", "tool": tool}
    if item["kind"] == "pip":
        venv = dest / "venv"
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True
        )
        python = venv / "Scripts/python.exe"
        env = dict(
            os.environ,
            PIP_CACHE_DIR=str(BASE / "pip-cache"),
            PYTHONNOUSERSITE="1",
            MPLCONFIGDIR=str(dest / "matplotlib"),
        )
        temp = dest / "temp"
        temp.mkdir(exist_ok=True)
        env["TMP"] = env["TEMP"] = str(temp)
        p = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--only-binary=:all:",
                "--disable-pip-version-check",
                "--report",
                str(dest / "pip-report.json"),
                "-r",
                str(APP / "Locks" / (tool + "-windows.txt")),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        (dest / "install.log").write_bytes(p.stdout)
        if p.returncode:
            raise ValueError(
                "Installation fehlgeschlagen; siehe " + str(dest / "install.log")
            )
        subprocess.run(
            [
                str(python),
                "-c",
                "import "
                + item.get("module", tool)
                + "; from importlib.metadata import version; assert version("
                + repr(item["package"])
                + ")=="
                + repr(item["version"]),
            ],
            check=True,
            capture_output=True,
        )
        files = {item["entry"]: digest(python)}
    else:
        data = get(item["url"], 120_000_000)
        sha = hashlib.sha256(data).hexdigest()
        if "integrity" in item:
            actual = (
                "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()
            )
            if actual != item["integrity"]:
                raise ValueError("Packet checksum is not correct.")
        elif sha != item["sha256"]:
            raise ValueError("Packet checksum is not correct.")
        archives = BASE / "Downloads"
        archives.mkdir(exist_ok=True)
        (
            archives
            / (
                tool
                + "-"
                + item["version"]
                + (".tgz" if item["kind"] == "npm" else ".zip")
            )
        ).write_bytes(data)
        if item["kind"] == "npm":
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                for entry in archive:
                    if not entry.isfile():
                        continue
                    name = entry.name.removeprefix("package/")
                    relative = safe_member(name)
                    if not (
                        name.startswith("dist/")
                        or "license" in name.lower()
                        or name in ("package.json", "NOTICE")
                    ):
                        continue
                    p = dest / relative
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(archive.extractfile(entry).read())
        else:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for entry in archive.infolist():
                    relative = safe_member(entry.filename)
                    if entry.is_dir():
                        continue
                    p = dest / relative
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(archive.read(entry))
        if not (dest / item["entry"]).is_file():
            raise ValueError(
                "Paketstruktur unerwartet; Einstiegspunkt fehlt: " + item["entry"]
            )
        files = {item["entry"]: digest(dest / item["entry"])}
        item = dict(item, archive_sha256=sha)
    atomic(
        dest / "installation.json", dict(item, tool=tool, installed=now(), files=files)
    )
    return {
        "status": "Set up and checked entry point",
        "tool": tool,
        "version": item["version"],
    }


def records(path, chrom, start, end, limit=20000):
    """Bounded view adapter, not a genotype/QC or coverage engine."""
    p = Path(path)
    name = p.name.lower()
    fmt = (
        "vcf"
        if name.endswith((".vcf", ".vcf.gz", ".vcf.bgz"))
        else "gff"
        if name.endswith((".gff", ".gff3", ".gff.gz", ".gff3.gz"))
        else "bed"
        if name.endswith((".bed", ".bed.gz"))
        else ""
    )
    if not fmt:
        raise ValueError(
            "This adapter requires VCF, BED or GFF. Chip-TXT convert controlled first."
        )
    rows = []
    scanned = 0
    truncated = False
    with (
        gzip.open(p, "rt", encoding="utf-8-sig")
        if name.endswith((".gz", ".bgz"))
        else p.open(encoding="utf-8-sig")
    ) as f:
        for line in f:
            if line.startswith(("#", "track", "browser")) or not line.strip():
                continue
            scanned += 1
            if scanned > 15_000_000:
                truncated = True
                break
            c = line.rstrip().split("\t")
            chrname = c[0].removeprefix("chr")
            if chrname != chrom.removeprefix("chr"):
                continue
            try:
                if fmt == "vcf":
                    if len(c) < 8:
                        raise ValueError("VCF with less than eight columns.")
                    pos = int(c[1])
                    stop = pos + max(1, len(c[3]))
                    label = c[2] if c[2] != "." else c[3] + ">" + c[4]
                    quality = float(c[5]) if c[5] != "." else None
                    status = c[6]
                elif fmt == "gff":
                    pos = int(c[3])
                    stop = int(c[4]) + 1
                    attrs = dict(x.split("=", 1) for x in c[8].split(";") if "=" in x)
                    label = unquote(
                        attrs.get("Name")
                        or attrs.get("gene_name")
                        or attrs.get("ID")
                        or c[2]
                    )
                    quality = None
                    status = "Annotation"
                else:
                    pos = int(c[1]) + 1
                    stop = int(c[2]) + 1
                    label = c[3] if len(c) > 3 else "Intervall"
                    quality = None
                    status = "Intervall"
            except (ValueError, IndexError) as e:
                raise ValueError("Non-readable" + fmt + "-Eintrag: " + str(e))
            if pos > end or stop <= start:
                continue
            rows.append(
                {
                    "pos": pos,
                    "end": stop,
                    "quality": quality,
                    "score": quality if quality is not None else 0,
                    "label": label[:180],
                    "status": status,
                    "strand": (1 if c[6] == "+" else -1 if c[6] == "-" else 0)
                    if fmt == "gff"
                    else 0,
                }
            )
            if len(rows) >= limit:
                truncated = True
                break
    return rows, {
        "format": fmt,
        "records_shown": len(rows),
        "scanned_records": scanned,
        "limited": truncated,
        "limit": limit,
        "note": "Only selected window; no complete quality, genomic or source evaluation.",
    }


def reference_files(reference):
    p = Path(reference).resolve()
    if not p.is_file() or p.suffix.lower() not in (".fa", ".fasta", ".fna"):
        raise ValueError("Select uncompressed local reference FASTA.")
    fai = Path(str(p) + ".fai")
    if not fai.is_file():
        raise ValueError("Passender FASTA-Index fehlt: " + str(fai))
    return {"reference": str(p), "fai": str(fai)}


def track_config(path, urls, jbrowse=False):
    name = Path(path).name.lower()
    base = {"name": Path(path).name}
    if jbrowse:
        if name.endswith(".vcf"):
            adapter = {"type": "VcfAdapter", "vcfLocation": {"uri": urls["input"]}}
        elif name.endswith((".vcf.gz", ".vcf.bgz")):
            if "index" not in urls:
                raise ValueError("Compressed VCF requires TBI/CSI.")
            adapter = {
                "type": "VcfTabixAdapter",
                "vcfGzLocation": {"uri": urls["input"]},
                "index": {
                    "location": {"uri": urls["index"]},
                    "indexType": "CSI" if urls.get("index_kind") == "csi" else "TBI",
                },
            }
        elif name.endswith(".bam"):
            if "index" not in urls:
                raise ValueError("BAM requires BAI/CSI.")
            adapter = {
                "type": "BamAdapter",
                "bamLocation": {"uri": urls["input"]},
                "index": {
                    "location": {"uri": urls["index"]},
                    "indexType": "CSI" if urls.get("index_kind") == "csi" else "BAI",
                },
            }
        elif name.endswith((".gff", ".gff3")):
            adapter = {"type": "Gff3Adapter", "gffLocation": {"uri": urls["input"]}}
        elif name.endswith(".bed"):
            adapter = {"type": "BedAdapter", "bedLocation": {"uri": urls["input"]}}
        else:
            raise ValueError(
                "JBrowse adapter supports VCF, indexed BAM, BED and GFF3; CRAM open first with IGV.js."
            )
        return dict(
            base,
            type="VariantTrack"
            if "Vcf" in adapter["type"]
            else "AlignmentsTrack"
            if "Bam" in adapter["type"]
            else "FeatureTrack",
            trackId="selected",
            assemblyNames=["local"],
            adapter=adapter,
        )
    if name.endswith((".bam", ".cram", ".vcf.gz", ".vcf.bgz")) and "index" not in urls:
        raise ValueError(
            "Select or provide a suitable index for BAM/CRAM or compressed VCF."
        )
    fmt = (
        "vcf"
        if ".vcf" in name
        else "bam"
        if name.endswith(".bam")
        else "cram"
        if name.endswith(".cram")
        else "bed"
        if ".bed" in name
        else "gff3"
        if ".gff" in name
        else ""
    )
    if not fmt:
        raise ValueError("IGV adapter supports VCF, BAM, CRAM, BED or GFF.")
    return dict(
        base,
        format=fmt,
        url=urls["input"],
        **({"indexURL": urls["index"]} if "index" in urls else {"indexed": False}),
    )


def prepare(r):
    tool = r["tool"]
    person = r["person"]
    if tool not in LOCK or not installed(tool):
        raise ValueError("Werkzeug zuerst installieren / reparieren.")
    if not re.fullmatch("[A-Za-z0-9_-]+", person):
        raise ValueError("Invalid person.")
    p = Path(r["file"]).resolve()
    if not p.is_file():
        raise ValueError("Datensatzdatei fehlt.")
    source_root = (ROOT / "DNA_Archiv/01_Originaldownloads").resolve()
    if p.is_relative_to(source_root) and p.relative_to(source_root).parts[0] != person:
        raise ValueError(
            "According to the archive path, this file belongs to another person."
        )
    chrom = str(r.get("chrom", "1"))
    if not re.fullmatch("[A-Za-z0-9_.-]{1,80}", chrom):
        raise ValueError("Invalid chromosome name.")
    start = int(r.get("start", 1))
    end = int(r.get("end", 1000000))
    if start < 1 or end < start:
        raise ValueError("Specify valid genome window (1-based).")
    job = uuid.uuid4().hex
    folder = RUNS / job
    folder.mkdir(parents=True)
    manifest = {
        "id": job,
        "tool": tool,
        "version": LOCK[tool]["version"],
        "person": person,
        "created": now(),
        "input": str(p),
        "source_size": p.stat().st_size,
        "source_mtime_ns": p.stat().st_mtime_ns,
        "region": {"chrom": chrom, "start": start, "end": end},
        "files": {"input": str(p)},
        "note": "View of a selected source file; original unchanged. No automatically merged master dataset.",
    }
    prefix = "/visual-run/" + job + "/"
    if tool in ("igvjs", "jbrowse"):
        ref = reference_files(r.get("reference", ""))
        manifest["files"].update(ref)
        index = r.get("index", "")
        if not index:
            for suffix in (".tbi", ".csi", ".bai", ".crai"):
                options = [Path(str(p) + suffix), p.with_suffix(suffix)]
                index = next((str(x) for x in options if x.is_file()), "")
                if index:
                    break
        if index:
            ip = Path(index).resolve()
            if not ip.is_file():
                raise ValueError("Indexdatei fehlt.")
            manifest["files"]["index"] = str(ip)
        urls = {k: prefix + "file/" + k for k in manifest["files"]}
        urls["index_kind"] = Path(index).suffix[1:] if index else ""
        if tool == "igvjs":
            config = {
                "reference": {
                    "id": "local",
                    "name": "Local reference (check assignment yourself)",
                    "fastaURL": urls["reference"],
                    "indexURL": urls["fai"],
                },
                "locus": chrom + ":" + str(start) + "-" + str(end),
                "tracks": [track_config(p, urls)],
                "loadDefaultGenomes": False,
                "showGenomeWidget": False,
                "showIdeogram": False,
            }
        else:
            config = {
                "assemblies": [
                    {
                        "name": "local",
                        "sequence": {
                            "type": "ReferenceSequenceTrack",
                            "trackId": "reference",
                            "adapter": {
                                "type": "IndexedFastaAdapter",
                                "fastaLocation": {"uri": urls["reference"]},
                                "faiLocation": {"uri": urls["fai"]},
                            },
                        },
                    }
                ],
                "tracks": [track_config(p, urls, True)],
                "defaultSession": {
                    "name": "Local dataset",
                    "view": {
                        "id": "linear",
                        "type": "LinearGenomeView",
                        "tracks": [
                            {
                                "type": track_config(p, urls, True)["type"],
                                "configuration": "selected",
                                "displays": [
                                    {
                                        "type": "LinearVariantDisplay"
                                        if ".vcf" in p.name.lower()
                                        else "LinearAlignmentsDisplay"
                                        if p.suffix.lower() == ".bam"
                                        else "LinearBasicDisplay",
                                        "configuration": "selected-"
                                        + (
                                            "LinearVariantDisplay"
                                            if ".vcf" in p.name.lower()
                                            else "LinearAlignmentsDisplay"
                                            if p.suffix.lower() == ".bam"
                                            else "LinearBasicDisplay"
                                        ),
                                    }
                                ],
                            }
                        ],
                    },
                },
            }
        atomic(folder / "config.json", config)
        if tool == "jbrowse":
            manifest["view_url"] = (
                "/tool-assets/jbrowse/index.html?config=" + prefix + "config.json"
            )
    else:
        rows, stats = records(
            p,
            chrom,
            start,
            end,
            limit=150
            if tool == "dnafeaturesviewer"
            else 2000
            if tool == "pycirclize"
            else 1000
            if tool == "pygenomeviz"
            else 20000,
        )
        manifest["stats"] = stats
        if not rows:
            raise ValueError(
                "No entries in the selected window. Check chromosome name and positions."
            )
        atomic(folder / "points.json", rows)
        if tool in ("pygenomeviz", "pycirclize", "dnafeaturesviewer"):
            spec = {
                "tool": tool,
                "folder": str(folder),
                "start": start,
                "end": end,
                "chrom": chrom,
                "rows": rows,
            }
            atomic(folder / "plot-request.json", spec)
            env = dict(
                os.environ,
                MPLCONFIGDIR=str(BASE / tool / "matplotlib"),
                PYTHONNOUSERSITE="1",
                MPLBACKEND="Agg",
            )
            proc = subprocess.run(
                [
                    str(BASE / tool / LOCK[tool]["entry"]),
                    str(
                        APP
                        / (
                            "visual_plot.py"
                            if tool == "pygenomeviz"
                            else "extended_plot.py"
                        )
                    ),
                    str(folder / "plot-request.json"),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            (folder / "plot.log").write_bytes(proc.stdout)
            if proc.returncode:
                raise ValueError(
                    "Diagramm fehlgeschlagen; siehe " + str(folder / "plot.log")
                )
    atomic(folder / "manifest.json", manifest)
    template = (APP / "visual-viewer.html").read_text(encoding="utf-8")
    (folder / "index.html").write_text(
        template.replace(
            "__RUN__", json.dumps(manifest, ensure_ascii=False).replace("<", "\\u003c")
        ),
        encoding="utf-8",
    )
    return {
        "path": prefix + "index.html",
        "folder": str(folder),
        "status": "Lokale Ansicht Preparing",
        "tool": tool,
    }


def serve(handler, head=False):
    """Only assets, generated runs and explicitly selected input files; supports byte ranges."""
    route = unquote(urlparse(handler.path).path)
    if not route.startswith(("/tool-assets/", "/visual-run/")):
        return False
    try:
        parts = route.strip("/").split("/")
        if any(x in ("", "..", ".") or "\\" in x or ":" in x for x in parts):
            raise ValueError("Invalid path.")
        if parts[0] == "tool-assets":
            if len(parts) < 3 or parts[1] not in LOCK:
                raise ValueError("Werkzeug fehlt.")
            base = (BASE / parts[1]).resolve()
            p = (base / Path(*parts[2:])).resolve()
            if not p.is_relative_to(base) or any(
                x in ("venv", "temp") for x in parts[2:]
            ):
                raise ValueError("Nicht freigegeben.")
        else:
            if len(parts) < 3 or not re.fullmatch("[a-f0-9]{32}", parts[1]):
                raise ValueError("Invalid view.")
            base = RUNS / parts[1]
            m = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
            if len(parts) == 4 and parts[2] == "file":
                p = Path(m["files"][parts[3]])
                if parts[3] == "input" and (
                    p.stat().st_size != m["source_size"]
                    or p.stat().st_mtime_ns != m["source_mtime_ns"]
                ):
                    raise ValueError("Source changed since launch; re-prepare view.")
            elif len(parts) == 3 and parts[2] in (
                "index.html",
                "config.json",
                "points.json",
                "plot.svg",
                "plot.png",
                "plot.pdf",
            ):
                p = base / parts[2]
            else:
                raise ValueError("Nicht freigegeben.")
        if not p.is_file():
            raise ValueError("File missing.")
        compressed = None
        if (
            parts[0] == "tool-assets"
            and p.suffix in (".js", ".css")
            and p.stat().st_size > 65536
            and "gzip" in handler.headers.get("Accept-Encoding", "")
            and not handler.headers.get("Range")
        ):
            compressed = gzip.compress(p.read_bytes(), compresslevel=5)
        size = len(compressed) if compressed is not None else p.stat().st_size
        first = 0
        last = size - 1
        range_value = handler.headers.get("Range")
        code = 200
        if range_value:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_value)
            if not match or not any(match.groups()):
                raise ValueError("Invalid byte range.")
            if match[1]:
                first = int(match[1])
                last = min(last, int(match[2])) if match[2] else last
            else:
                first = max(0, size - int(match[2]))
            if first >= size or first > last:
                handler.send_response(416)
                handler.send_header("Content-Range", "bytes */" + str(size))
                handler.end_headers()
                return True
            code = 206
        handler.send_response(code)
        handler.send_header(
            "Content-Type",
            mimetypes.guess_type(p.name)[0] or "application/octet-stream",
        )
        handler.send_header("Content-Length", str(max(0, last - first + 1)))
        handler.send_header("Accept-Ranges", "bytes")
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("X-Content-Type-Options", "nosniff")
        # GenomeSpy's Vega expression compiler requires new Function. Enable only
        # on our generated GenomeSpy views/assets, with all network access self-only.
        expression = (
            " 'unsafe-eval'"
            if (parts[0] == "tool-assets" and parts[1] == "genomespy")
            or (parts[0] == "visual-run" and m.get("tool") == "genomespy")
            else ""
        )
        handler.send_header(
            "Content-Security-Policy",
            "default-src 'self'; frame-src 'self' https://dna-assets.local; script-src 'self' https://dna-assets.local 'unsafe-inline' 'wasm-unsafe-eval'"
            + expression
            + "; connect-src 'self' https://dna-assets.local; style-src 'self' https://dna-assets.local 'unsafe-inline'; img-src 'self' https://dna-assets.local data: blob:; font-src 'self' https://dna-assets.local data:; worker-src 'self' blob:; object-src 'none'",
        )
        if parts[0] == "visual-run":
            handler.send_header(
                "Access-Control-Allow-Origin", "https://dna-assets.local"
            )
            handler.send_header(
                "Access-Control-Expose-Headers",
                "Content-Length, Content-Range, Accept-Ranges",
            )
        if compressed is not None:
            handler.send_header("Content-Encoding", "gzip")
            handler.send_header("Vary", "Accept-Encoding")
        if code == 206:
            handler.send_header("Content-Range", f"bytes {first}-{last}/{size}")
        handler.end_headers()
        if not head:
            if compressed is not None:
                handler.wfile.write(compressed)
                return True
            with p.open("rb") as f:
                f.seek(first)
                remaining = last - first + 1
                while remaining > 0:
                    data = f.read(min(65536, remaining))
                    if not data:
                        break
                    handler.wfile.write(data)
                    remaining -= len(data)
        return True
    except (ValueError, KeyError, OSError):
        handler.send_error(404)
        return True


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        result = (
            listing()
            if action == "list"
            else refresh()
            if action == "refresh"
            else install(sys.argv[2])
            if action == "install"
            else prepare(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig")))
            if action == "prepare"
            else None
        )
        if result is None:
            raise ValueError("Unbekannte Aktion.")
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
