"""Read provider exports as evidence, never execute or silently turn reports into calls."""

from pathlib import Path
import csv, gzip, hashlib, html, json, re, zipfile

KINDS = [
    "Detect automatically",
    "Reports Summary",
    "Ancestry Composition CSV",
    "Family Tree JSON",
    "Raw Data TXT",
    "Imputed Genotype Data R6",
    "Phased Genotype Data",
]


def read_text(path, limit=32 * 1024 * 1024):
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            candidates = [
                x
                for x in z.infolist()
                if not x.is_dir()
                and x.filename.lower().endswith((".txt", ".csv", ".json", ".vcf"))
            ]
            if len(candidates) != 1:
                raise ValueError(
                    "Choose one extracted export; multi-file archives stay separate."
                )
            with z.open(candidates[0]) as f:
                data = f.read(limit + 1)
    else:
        op = gzip.open if path.name.lower().endswith((".gz", ".bgz")) else open
        with op(path, "rb") as f:
            data = f.read(limit + 1)
    if len(data) > limit:
        raise ValueError(
            "Structured export exceeds 32 MiB; use the genotype workflow for large VCF/TXT files."
        )
    return data.decode("utf-8-sig")


def tree_preview(value):
    # Schema-independent inventory only. 23andMe has no schema supplied here.
    stack = [value]
    objects = arrays = scalars = 0
    keys = set()
    person_like = 0
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            objects += 1
            keys.update(str(k) for k in node)
            lower = {str(k).lower() for k in node}
            if lower.intersection(
                {"name", "first_name", "firstname", "display_name"}
            ) and lower.intersection({"id", "person_id", "profile_id"}):
                person_like += 1
            stack.extend(node.values())
        elif isinstance(node, list):
            arrays += 1
            stack.extend(node)
        else:
            scalars += 1
        if objects + arrays + scalars > 200000:
            raise ValueError("JSON structure too large for bounded tree preview")
    return {
        "objects": objects,
        "arrays": arrays,
        "person_like_objects": person_like,
        "top_level_keys": list(value)[:100] if isinstance(value, dict) else [],
        "observed_keys": sorted(keys)[:200],
        "relationships_applied": 0,
        "status": "Source JSON preserved; unknown schema requires explicit relationship mapping. No people or family links were changed.",
    }


def ancestry_segments(text):
    lines = text.splitlines()
    comments = [s for s in lines if s.lstrip().startswith("#")]
    lines = [s for s in lines if s.strip() and not s.lstrip().startswith("#")]
    if not lines:
        raise ValueError("Empty ancestry CSV")
    delimiter = "\t" if "\t" in lines[0] else ","
    reader = csv.DictReader(lines, delimiter=delimiter)
    aliases = {
        "chromosome": "chromosome",
        "chrom": "chromosome",
        "chr": "chromosome",
        "start": "start",
        "startpoint": "start",
        "startposition": "start",
        "end": "end",
        "endpoint": "end",
        "endposition": "end",
        "ancestry": "ancestry",
        "population": "ancestry",
        "ancestrylabel": "ancestry",
        "copy": "copy",
        "haplotype": "copy",
    }
    names = {
        key: aliases.get(re.sub("[^a-z]", "", key.lower()))
        for key in (reader.fieldnames or [])
        if key
    }
    if not {"chromosome", "start", "end", "ancestry"} <= set(names.values()):
        raise ValueError(
            "Unsupported ancestry CSV columns; original is preserved, no inferred percentages."
        )
    rows = []
    for row in reader:
        if len(rows) >= 200000:
            raise ValueError("Too many ancestry segments")
        normalized = {names[k]: v for k, v in row.items() if k in names and names[k]}
        chrom = normalized["chromosome"].removeprefix("chr")
        start = int(normalized["start"])
        end = int(normalized["end"])
        if (
            chrom not in [str(i) for i in range(1, 23)] + ["X", "Y", "MT", "M"]
            or start < 0
            or end <= start
        ):
            raise ValueError("Invalid ancestry segment coordinates")
        rows.append(dict(normalized, chromosome=chrom, start=start, end=end))
    confidence = []
    for line in comments:
        if "confidence" in line.lower():
            confidence.append(line[:500])
    return {
        "segments": rows,
        "segment_count": len(rows),
        "confidence_metadata": confidence,
        "confidence": "Only as explicitly stated in source; not assumed to be 50%",
        "coordinate_convention": "Preserved from source; zero/one-based convention not guessed",
        "percentages_computed": False,
        "note": "Hierarchical labels and confidence levels may overlap. Segment lengths are not automatically ancestry percentages.",
    }


def inspect_export(person, inputs, out, log=print, cancel=lambda: False):
    import inspector

    p = Path(inputs["file"])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    before = p.stat()
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            if cancel():
                raise InterruptedError("Cancelled")
            h.update(b)
    kind = inputs.get("export_kind", "Detect automatically")
    result = {
        "person": person,
        "source": str(p),
        "sha256": h.hexdigest(),
        "requested_kind": kind,
        "clinical_validation": False,
        "provider_claim": "23andMe export selected by user; content signature checked separately",
        "profile_modified": False,
    }
    if zipfile.is_zipfile(p):
        from pathlib import PurePosixPath

        with zipfile.ZipFile(p) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            if not members or len(members) > 10000:
                raise ValueError("Use a ZIP with 1–10000 regular members")
            for m in members:
                name = PurePosixPath(m.filename)
                if (
                    name.is_absolute()
                    or ".." in name.parts
                    or "\\" in m.filename
                    or ":" in m.filename
                    or m.flag_bits & 1
                ):
                    raise ValueError(
                        "Unsafe or encrypted ZIP member; review the archive manually"
                    )
            result.update(
                format="23andMe ZIP export bundle",
                members=[
                    {
                        "name": m.filename,
                        "bytes": m.file_size,
                        "kind": "BCF"
                        if m.filename.lower().endswith(".bcf")
                        else "TXT"
                        if m.filename.lower().endswith(".txt")
                        else "Other",
                    }
                    for m in members
                ],
                status="Container inventory only. Use Batch file preparation to extract, import and validate each member. Members share container lineage; not independent tests.",
            )
            if kind == "Imputed Genotype Data R6":
                if not all(
                    m.filename.lower().endswith(
                        (".bcf", ".bcf.csi", ".vcf", ".vcf.gz", ".vcf.gz.tbi")
                    )
                    for m in members
                ):
                    raise ValueError(
                        "R6 expects BCF/VCF partitions with optional indexes"
                    )
                result.update(
                    measurement="imputed",
                    research_only=True,
                    qc_supported_measured_points=0,
                    version_claim="R6 user-selected; confirm from headers/provider metadata",
                )
            elif kind == "Phased Genotype Data":
                result.update(measurement="statistically phased", research_only=True)
    elif p.suffix.lower() == ".pdf" or kind == "Reports Summary":
        with p.open("rb") as f:
            magic = f.read(5)
        if magic == b"%PDF-":
            try:
                from pypdf import PdfReader

                reader = PdfReader(p)
                text = "\n".join(
                    (page.extract_text() or "") for page in list(reader.pages)[:200]
                )
                result.update(
                    format="Reports Summary PDF",
                    pages=len(reader.pages),
                    pages_previewed=min(200, len(reader.pages)),
                    text_preview=text[:131072],
                    provider_signature="23andme" in text.lower(),
                    status="Provider report, not raw genotypes. No diagnoses applied to profile.",
                )
            except ImportError:
                result.update(
                    format="PDF",
                    status="PDF archived; install the optional storybook-pdf dependency for text extraction.",
                )
        else:
            raise ValueError(
                "Reports Summary expects a PDF saved from the provider print view"
            )
    elif kind == "Ancestry Composition CSV":
        result.update(
            format="Ancestry Composition CSV", data=ancestry_segments(read_text(p))
        )
    elif kind == "Family Tree JSON":
        result.update(
            format="Family Tree JSON", data=tree_preview(json.loads(read_text(p)))
        )
    elif kind == "Detect automatically" and p.suffix.lower() == ".json":
        result.update(
            format="JSON / tree candidate", data=tree_preview(json.loads(read_text(p)))
        )
    else:
        checked = inspector.inspect(p, log)
        if checked["color"] == "red":
            raise ValueError("; ".join(checked["issues"]))
        if checked["format"] == "Ancestry report / segment assignments":
            result.update(
                format="Ancestry Composition CSV", data=ancestry_segments(read_text(p))
            )
        else:
            if kind == "Imputed Genotype Data R6" and checked["format"] not in (
                "VCF",
                "BCF",
            ):
                raise ValueError(
                    "R6 requires BCF/VCF files or their ZIP bundle, not an arbitrary TXT"
                )
            checked.pop("fingerprint", None)
            result.update(format=checked["format"], inspection=checked)
            if kind == "Imputed Genotype Data R6":
                result.update(
                    measurement="imputed",
                    research_only=True,
                    version_claim="R6 selected by user; only confirmed if header states R6",
                    qc_supported_measured_points=0,
                )
            if kind == "Phased Genotype Data":
                result.update(
                    measurement="statistically phased",
                    research_only=True,
                    status="Haplotype order does not identify mother/father without family evidence. Source preserved; no automatic independent measurement.",
                )
    if cancel():
        raise InterruptedError("Cancelled")
    after = p.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Source changed during inspection")
    (out / "provider-export.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    display = json.dumps(result, ensure_ascii=False, indent=2)
    (out / "provider-export.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>23andMe export review</title><style>body{font:16px Segoe UI;max-width:1100px;margin:35px auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>23andMe · Source export review</h1><p>Provider evidence, no clinical confirmation. Originals and family links unchanged.</p><pre>'
        + html.escape(display)
        + "</pre>",
        encoding="utf-8",
    )
    log("Export review ready; profile and original data unchanged")
