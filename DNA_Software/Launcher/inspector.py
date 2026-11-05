"""Content-based provenance and conservative file QC; no phenotype guesses."""

from pathlib import Path
import csv, gzip, hashlib, io, re, zipfile, datetime, time
import portable_json as json

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = [
    "Detect automatically",
    "23andMe",
    "MyHeritage",
    "Nebula",
    "Dante Labs",
    "Sequencing.com",
    "GEDmatch",
    "GEDCOM / Origin unknown",
    "National Geographic / Genographic",
    "FamilyTreeDNA",
    "AncestryDNA",
    "Living DNA",
    "Helix",
    "DNA Complete",
    "Other laboratory",
    "Unknown",
]
RULES_VERSION = "2026-11-03.5"
AUTOSOMES = frozenset(str(x) for x in range(1, 23))


def chromosome_hint(result):
    """A screening label, never a confirmed chromosome copy-number call."""
    x = result.get("x_called", 0)
    y = result.get("y_called", 0)
    het = result.get("x_heterozygous", 0)
    if x >= 500 and y >= 50 and het / x <= 0.01:
        return "XY (provisional note)"
    if x >= 500 and het >= 25 and y == 0:
        return "XX (provisional note)"
    return "Undetermined"


def tokens(head, name):
    low = head.lower()
    result = {
        "provider": "Unknown",
        "producer": "Unknown",
        "build": "",
        "versions": [],
        "measurement": "Unknown",
        "name_hint": "",
        "confidence": "Not used",
    }
    signatures = [
        ("23andme", "23andMe"),
        ("myheritage", "MyHeritage"),
        ("nebula.org", "Nebula"),
        ("nebula genomics", "Nebula"),
        ("dantelabs", "Dante Labs"),
        ("dante labs", "Dante Labs"),
        ("sequencing.com", "Sequencing.com"),
        ("gedmatch", "GEDmatch"),
        ("ancestrydna", "AncestryDNA"),
        ("familytreedna", "FamilyTreeDNA"),
        ("family tree dna", "FamilyTreeDNA"),
        ("livingdna", "Living DNA"),
        ("genographic", "National Geographic / Genographic"),
        ("helix", "Helix"),
    ]
    for needle, p in signatures:
        if needle in low:
            result["provider"] = p
            result["confidence"] = "expliziter Inhaltsmarker"
            break
    if re.search(r"grch38|hg38|hs38|build[ =:]*(?:38)", low):
        result["build"] = "GRCh38"
    elif re.search(r"grch37|hg19|hs37|build[ =:]*(?:37)", low):
        result["build"] = "GRCh37"
    for line in head.splitlines():
        if any(
            x in line.lower()
            for x in [
                "##source=",
                "##dragen",
                "##gatkcommandline",
                "@pg",
                "##method=",
                "##version=",
                "##gvcf",
                "##reference=",
            ]
        ):
            result["versions"].append(line[:700])
    if "dragen" in low:
        result["producer"] = "DRAGEN (software; laboratory not determined thereby)"
    elif "haplotypecaller" in low:
        result["producer"] = "GATK/HaplotypeCaller (Software)"
    elif "deepvariant" in low:
        result["producer"] = "DeepVariant (Software)"
    if any(
        x in low
        for x in ["imputed genotype", "##imputation", "imputed data", "##source=imput"]
    ):
        result["measurement"] = "Imputed/statistically supplemented; check separately"
    elif re.search(
        r"phased genotype|statistically phased|##phasing=|haplotype.?1.*haplotype.?2",
        low,
    ):
        result["measurement"] = (
            "Phased/statistical assignment; no independent measurement"
        )
    elif "low-pass whole genome" in low:
        result["measurement"] = "Low pass sequencing specified; imputation not used"
    if re.search(r"(^|\n)0\s+HEAD", head):
        result["provider"] = "GEDCOM / Origin unknown"
        result["confidence"] = "GEDCOM format, no proof of provider"
    lower = name.lower()
    for needle, p in signatures:
        if needle.replace(".org", "").replace(".com", "") in lower:
            result["name_hint"] = p + "(only file name; no proof of origin)"
            break
    m = re.search(r"(?:^|[_\-.])v([1-6])(?:[_\-.]|$)", lower)
    if m:
        result["name_hint"] += (
            "· Possible chip version v" + m.group(1) + "in the filename, not confirmed"
        )
    if result["measurement"] == "Unknown":
        if re.search(r"(?:^|[_.-])phased_genome(?:_statistical)?_", lower):
            result["measurement"] = (
                "Phased/statistical export candidate; no independent measurement"
            )
            result["measurement_basis"] = (
                "Filename hint only; confirm the export/header before use"
            )
        elif "imputed" in lower or "imputation" in lower:
            result["measurement"] = (
                "Imputed export candidate; not established as directly measured"
            )
            result["measurement_basis"] = (
                "Filename hint only; confirm the export/header before use"
            )
    if "dnaworkbenchsynthetic" in low or "dnaworkbenchsynthetic=true" in low:
        result["synthetic"] = True
        result["measurement"] = "Synthetic / not measured human DNA"
        result["provider"] = "DNA Workbench Synthetic"
        result["confidence"] = "expliziter synthetischer Inhaltsmarker"
    return result


def file_sha256(path, log=lambda value: None):
    path = Path(path)
    size = path.stat().st_size
    digest = hashlib.sha256()
    completed = 0
    next_update = time.monotonic() + 2
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
            completed += len(block)
            if time.monotonic() >= next_update:
                log(f"Checksum progress: {completed} / {size} bytes")
                next_update = time.monotonic() + 2
    return digest.hexdigest()


def inspect(path, log=lambda x: None):
    from data_scope import describe

    result = _inspect(path, log)
    result["data_scope"] = describe(result)
    result.pop("content_header", None)
    return result


def _inspect(path, log=lambda x: None):
    p = Path(path).resolve()
    st = p.stat()
    log("Testing:" + p.name)
    digest = file_sha256(p, log)
    result = {
        "path": str(p),
        "name": p.name,
        "bytes": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "sha256": digest,
        "rules": RULES_VERSION,
        "checked": datetime.datetime.now().astimezone().isoformat(),
        "format": "Unknown",
        "color": "orange",
        "verified": False,
        "records": 0,
        "called_points": 0,
        "qc_supported_points": None,
        "issues": [],
        "fingerprint": {},
        "samples": [],
        "mt_called": 0,
        "y_called": 0,
        "x_called": 0,
        "x_heterozygous": 0,
        "genome_completeness": "Not derivable from file size",
        "profile": {
            "chromosomes": "Not determined",
            "mt_haplogroup": "Not determined",
            "y_haplogroup": "Not determined",
            "blood_group": "Not reliably determined",
        },
    }
    z = None
    stream = None
    try:
        if p.suffix.lower() in (".tbi", ".csi", ".bai", ".crai", ".fai"):
            result.update(tokens("", p.name))
            result["format"] = "Index / Hilfsdatei"
            result["color"] = "gray"
            result["issues"].append(
                "Index file: check for the associated source file, no DNA genotypes."
            )
            return result
        with p.open("rb") as raw:
            magic = raw.read(8)
        if zipfile.is_zipfile(p):
            z = zipfile.ZipFile(p)
            members = [i for i in z.infolist() if not i.is_dir()]
            result["archive_members"] = [
                {"name": i.filename, "bytes": i.file_size} for i in members
            ]
            candidates = [
                i
                for i in members
                if i.filename.lower().endswith(
                    (".txt", ".csv", ".vcf", ".ged", ".gedcom")
                )
            ]
            if len(candidates) != 1:
                result["format"] = "ZIP / multiple or not directly readable content"
                result["issues"].append(
                    "ZIP members remain separate. Select a single raw data file for unique DNA recognition."
                )
                result.update(tokens("", p.name))
                return result
            stream = io.TextIOWrapper(
                z.open(candidates[0]), encoding="utf-8-sig", errors="strict"
            )
            result["archive_payload"] = candidates[0].filename
        elif magic.startswith(b"%PDF"):
            result["format"] = "PDF report"
            result.update(tokens("", p.name))
            result["issues"].append(
                "The report does not contain any directly evaluable raw genotypes."
            )
            return result
        elif p.suffix.lower() == ".json":
            from provider_exports import read_text, tree_preview

            data = json.loads(read_text(p))
            result.update(tokens("", p.name))
            result["format"] = "JSON / Stammbaum-Kandidat"
            result["color"] = "gray"
            result["json_structure"] = tree_preview(data)
            result["issues"].append(
                "JSON structure tested; origin and relationships require confirmed field mapping; no raw genotypes and no automatically confirmed family links."
            )
            return result
        elif magic.startswith(b"CRAM") or p.name.lower().endswith((".bam", ".bcf")):
            result["format"] = (
                "CRAM" if magic.startswith(b"CRAM") else p.suffix[1:].upper()
            )
            header = ""
            if result["format"] == "BCF":
                opener = gzip.open if magic.startswith(b"\x1f\x8b") else open
                with opener(p, "rb") as raw:
                    start = raw.read(9)
                    if (
                        len(start) != 9
                        or start[:3] != b"BCF"
                        or start[3:5] != b"\x02\x02"
                    ):
                        raise ValueError(
                            "Expected BCF 2.2 header; use BCFtools to check other versions"
                        )
                    length = int.from_bytes(start[5:9], "little")
                    if not 1 <= length <= 1024 * 1024:
                        raise ValueError(
                            "BCF header exceeds the bounded preview; inspect with BCFtools"
                        )
                    payload = raw.read(length)
                    if len(payload) != length:
                        raise ValueError("Truncated BCF header")
                    header = payload.rstrip(b"\x00").decode("utf-8", errors="strict")
                result["format_version"] = "BCF 2.2"
                result["header_checked"] = True
                result["content_header"] = header
            result.update(tokens(header, p.name))
            result["issues"].append(
                "Binary header only: run BCFtools/SAMtools for complete records, sample checks and QC. No measured-point count is inferred."
            )
            return result
        else:
            stream = (
                gzip.open(p, "rt", encoding="utf-8-sig", errors="strict")
                if magic.startswith(b"\x1f\x8b")
                else p.open("rt", encoding="utf-8-sig", errors="strict")
            )
        first = []
        for i in range(150):
            line = stream.readline()
            if not line:
                break
            first.append(line)
            if not line.startswith("#") and line.strip():
                break
        if not any("##fileformat=VCF" in x or "#CHROM\tPOS" in x for x in first):
            for _ in range(40):
                line = stream.readline()
                if not line:
                    break
                first.append(line)
        head = "".join(first)
        result["content_header"] = head
        result.update(tokens(head, p.name))
        import itertools

        full = itertools.chain(first, stream)
        if "##fileformat=VCF" in head or "#CHROM\tPOS" in head:
            result["format"] = "VCF"
            result["qc_supported_points"] = 0
            bad = 0
            sample_count = 0
            seen = set()
            duplicates = 0
            quality_fields = False
            result["chromosome_counts"] = {}
            result["variant_types"] = {"SNV": 0, "indel": 0, "SV": 0, "CNV": 0}
            result["gvcf_blocks"] = 0
            for line in full:
                if line.startswith("##"):
                    result["content_header"] = (result["content_header"] + "\n" + line)[
                        :100000
                    ]
                    continue
                if line.startswith("#CHROM"):
                    result["samples"] = line.rstrip().split("\t")[9:]
                    sample_count = len(result["samples"])
                    continue
                if line.startswith("#") or not line.strip():
                    continue
                c = line.rstrip().split("\t")
                if len(c) < 8:
                    raise ValueError("Invalid VCF line: less than eight columns.")
                pos = int(c[1])
                result["records"] += 1
                if pos < 1 or not c[3]:
                    bad += 1
                    continue
                alts = c[4].split(",")
                info = c[7]
                if any(a in ("<NON_REF>", "<*>") for a in alts) and re.search(
                    r"(?:^|;)END=\d+", info
                ):
                    result["gvcf_blocks"] += 1
                if re.search(r"(?:^|;)SVTYPE=(?:CNV|DUP)(?:;|$)", info) or any(
                    a.startswith(("<CNV", "<DUP")) for a in alts
                ):
                    result["variant_types"]["CNV"] += 1
                elif re.search(r"(?:^|;)SVTYPE=", info) or any(
                    a.startswith("<")
                    and a not in ("<NON_REF>", "<*>")
                    or "[" in a
                    or "]" in a
                    for a in alts
                ):
                    result["variant_types"]["SV"] += 1
                elif any(
                    a not in (".", "*", "<NON_REF>", "<*>") and len(a) != len(c[3])
                    for a in alts
                ):
                    result["variant_types"]["indel"] += 1
                elif len(c[3]) == 1 and any(a in "ACGT" and len(a) == 1 for a in alts):
                    result["variant_types"]["SNV"] += 1
                if sample_count != 1:
                    continue
                if len(c) != 10:
                    bad += 1
                    continue
                data = dict(zip(c[8].split(":"), c[9].split(":")))
                gt = data.get("GT", ".")
                quality_fields = quality_fields or ("DP" in data and "GQ" in data)
                try:
                    alleles = [int(x) for x in re.split(r"[/|]", gt)]
                except ValueError:
                    continue
                variants = [c[3]] + ([] if c[4] == "." else c[4].split(","))
                if any(x < 0 or x >= len(variants) for x in alleles):
                    bad += 1
                    continue
                if any(variants[x] in ("<NON_REF>", "<*>") for x in alleles):
                    continue
                chrom = c[0].removeprefix("chr")
                site = (chrom, pos)
                if site in seen:
                    duplicates += 1
                    continue
                seen.add(site)
                result["called_points"] += 1
                result["chromosome_counts"][chrom] = (
                    result["chromosome_counts"].get(chrom, 0) + 1
                )
                if chrom in ["M", "MT"]:
                    result["mt_called"] += 1
                elif chrom in ["Y", "24"]:
                    result["y_called"] += 1
                elif chrom in ["X", "23"]:
                    result["x_called"] += 1
                    if len(set(alleles)) > 1:
                        result["x_heterozygous"] += 1
                dp = data.get("DP")
                gq = data.get("GQ")
                if (
                    c[6] == "PASS"
                    and dp not in [None, "."]
                    and gq not in [None, "."]
                    and float(dp) >= 10
                    and float(gq) >= 20
                ):
                    result["qc_supported_points"] += 1
                if (
                    len(variants) == 2
                    and all(len(x) == 1 and x in "ACGT" for x in variants)
                    and len(result["fingerprint"]) < 100000
                    and chrom in AUTOSOMES
                ):
                    result["fingerprint"][chrom + ":" + str(pos)] = "".join(
                        sorted(variants[i] for i in alleles)
                    )
            if not result["records"]:
                result["issues"].append("No variant records found.")
            if sample_count != 1:
                result["issues"].append(
                    "Contains"
                    + str(sample_count)
                    + "Samples; not automatically assigning to a single human being."
                )
            if bad:
                result["issues"].append(
                    str(bad) + "implausible or invalid VCF records."
                )
            ratio = result["qc_supported_points"] / max(1, result["called_points"])
            result["color"] = (
                "red"
                if bad or not result["records"]
                else "green"
                if result["called_points"] >= 1000
                and ratio >= 0.95
                and sample_count == 1
                and not duplicates
                else "orange"
            )
            result["verified"] = bool(
                result["records"] and not bad and sample_count == 1 and not duplicates
            )
            if not quality_fields:
                result["qc_supported_points"] = None
            if duplicates:
                result["issues"].append(
                    str(duplicates)
                    + "multiple positions: counted only once; check before consensus-building."
                )
            result["issues"].append(
                "QC points: full GT, PASS, FORMAT/DP ≥ 10 and FORMAT/GQ ≥ 20."
            )
            result["issues"].append(
                "The number of variants is not covered by the genome, and absent positions remain unknown without any additional evidence."
            )
            result.update(tokens(result["content_header"], p.name))
        elif re.search(r"(^|\n)0\s+HEAD", head):
            result["format"] = "GEDCOM / Stammbaum"
            result["records"] = sum(
                1 for line in full if re.match(r"^0\s+@.*@\s+INDI", line)
            )
            result["color"] = "gray"
            result["verified"] = True
            result["issues"].append(
                "Genealogical individuals, not DNA genotypes, not used for health or variant calculations."
            )
        elif head.lstrip().startswith(">"):
            result["format"] = "FASTA"
            result["color"] = "gray"
            result["issues"].append(
                "Sequences / reference, no proven WGS coverage or finished individual genotypes."
            )
        elif head.lstrip().startswith("@") and p.name.lower().endswith(
            (".fastq", ".fastq.gz", ".fq", ".fq.gz")
        ):
            result["format"] = "FASTQ"
            result["issues"].append(
                "For base quality fastp and for variants use a WGS pipeline."
            )
        elif (
            ("ancestry" in head.lower() or "population" in head.lower())
            and ("start" in head.lower() and "end" in head.lower())
            and ("chromosome" in head.lower() or "chrom" in head.lower())
        ):
            result["format"] = "Ancestry report / segment assignments"
            result["color"] = "gray"
            result["issues"].append(
                "Assignments of origin along chromosomes; no raw genotypes. Import percentages and model version separately."
            )
        elif re.search(r"\bDYS\d+\b", head, re.I) and not re.search(r"\brs\d+\b", head):
            result["format"] = "Y-STR table"
            result["color"] = "gray"
            result["issues"].append(
                "Y-STR structure detected; alleles and test panel still specifically test."
            )
        else:
            valid = missing = bad = 0
            is_match = False
            seen = set()
            duplicates = 0
            result["chromosome_counts"] = {}
            for line in full:
                if line.startswith("#") or not line.strip():
                    continue
                c = (
                    next(csv.reader([line]))
                    if "," in line
                    else re.split(r"\s+", line.strip())
                )
                low = " ".join(c).lower()
                if any(
                    x in low
                    for x in [
                        "centimorgan",
                        "kit number",
                        "start location",
                        "shared cm",
                    ]
                ):
                    is_match = True
                    continue
                if len(c) < 4:
                    continue
                if not re.match(r"^(rs\d+|i\d+|ss\d+)", c[0].strip('"')):
                    continue
                try:
                    pos = int(c[2])
                    chrom = c[1].strip('"').removeprefix("chr")
                except ValueError:
                    continue
                gt = c[3].strip('"').upper()
                if (
                    len(c) >= 5
                    and re.fullmatch("[ACGT0-]", gt)
                    and re.fullmatch("[ACGT0-]", c[4].strip('"').upper())
                ):
                    gt += c[4].strip('"').upper()
                result["records"] += 1
                if gt in ["--", "00", "NN", "N", "0", "-", ""]:
                    missing += 1
                    continue
                if not re.fullmatch("[ACGTID]{1,2}", gt) or pos < 1:
                    bad += 1
                    continue
                site = (chrom, pos)
                if site in seen:
                    duplicates += 1
                    continue
                seen.add(site)
                valid += 1
                canonical = (
                    "X"
                    if chrom == "23"
                    else "Y"
                    if chrom == "24"
                    else "MT"
                    if chrom in ("26", "M")
                    else chrom
                )
                result["chromosome_counts"][canonical] = (
                    result["chromosome_counts"].get(canonical, 0) + 1
                )
                if (
                    chrom in AUTOSOMES
                    and re.fullmatch("[ACGT]{1,2}", gt)
                    and len(result["fingerprint"]) < 100000
                ):
                    result["fingerprint"][chrom + ":" + str(pos)] = "".join(sorted(gt))
                if chrom in ["M", "MT", "26"]:
                    result["mt_called"] += 1
                elif chrom in ["Y", "24"]:
                    result["y_called"] += 1
                elif chrom in ["X", "23"]:
                    result["x_called"] += 1
                    if len(set(gt)) > 1:
                        result["x_heterozygous"] += 1
            if result["records"]:
                result["format"] = "Chip/SNP table"
                result["called_points"] = valid
                result["call_rate"] = valid / max(1, result["records"])
                result["verified"] = bad == 0 and not duplicates
                result["color"] = (
                    "red"
                    if bad
                    else "green"
                    if valid >= 100000
                    and result["call_rate"] >= 0.99
                    and not duplicates
                    else "orange"
                )
                if duplicates:
                    result["issues"].append(
                        str(duplicates)
                        + "double positions; not counted as DNA points multiple times."
                    )
                result["issues"].append(
                    "Readable chip genotypes are not sequence calls individually occupied by DP/GQ."
                )
                if bad:
                    result["issues"].append(str(bad) + "non-interpretable lines.")
            elif is_match:
                result["format"] = "Match-/Segmenttabelle"
                result["color"] = "gray"
                result["issues"].append("Match statistics, not raw genotypes.")
            else:
                result["issues"].append(
                    "No clearly supported crude genotype structure detected."
                )
        result["profile"]["chromosomes"] = chromosome_hint(result)
        if "imput" in result.get("measurement", "").lower():
            result["qc_supported_points"] = None
            result["color"] = "orange"
            result["issues"].append(
                "Imputation: DP/GQ are not confirmed as additional directly measured DNA points."
            )
        result["profile"]["chromosomes_status"] = (
            "Screening from X/Y markers; no confirmed determination of chromosome number"
        )
        result["profile"]["chromosomes_evidence"] = {
            "X_Positionen": result["x_called"],
            "X_heterozygot": result["x_heterozygous"],
            "Y_Positionen": result["y_called"],
        }
        if result["mt_called"]:
            result["profile"]["mt_haplogroup"] = (
                "mtDNA present; haplogrep evaluation required"
            )
        if result["y_called"]:
            result["profile"]["y_haplogroup"] = (
                "Y-DNA present; yhaplo evaluation required"
            )
    except (ValueError, UnicodeError, OSError, EOFError, zipfile.BadZipFile) as e:
        result["color"] = "red"
        result["verified"] = False
        result["issues"].append("File verification failed:" + str(e))
    finally:
        if stream:
            stream.close()
        if z:
            z.close()
    return result


def check_batch(person, paths, folder, log=lambda x: None):
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    items = []
    import source_store

    refs = []
    db = source_store.connect(person)
    db.execute(
        "CREATE TABLE IF NOT EXISTS inspections(sha256 TEXT PRIMARY KEY,payload TEXT NOT NULL,checked TEXT)"
    )
    db.commit()
    for row in db.execute("SELECT payload FROM inspections"):
        try:
            r = json.loads(row[0])
            if r.get("fingerprint") and r.get("color") not in ["red", "black"]:
                refs.append(r)
        except (ValueError, KeyError, TypeError) as error:
            log("Ignored invalid previous inspection: " + str(error))
    for i, path in enumerate(paths, 1):
        r = inspect(path, log)
        r["check_job"] = out.name
        r["check_folder"] = str(out)
        comparisons = []
        for ref in refs + items:
            if (
                r["sha256"] == ref.get("sha256")
                or not r.get("build")
                or r.get("build") != ref.get("build")
                or not r["fingerprint"]
                or not ref.get("fingerprint")
            ):
                continue
            if r["color"] in ["red", "black"] or ref.get("color") in ["red", "black"]:
                continue
            common = set(r["fingerprint"]).intersection(ref["fingerprint"])
            if len(common) < 1000:
                continue
            same = sum(r["fingerprint"][k] == ref["fingerprint"][k] for k in common)
            rate = same / len(common)
            comparisons.append(
                {
                    "common_called_snps": len(common),
                    "same": same,
                    "concordance": rate,
                    "reference_sha256": ref["sha256"],
                    "reference_name": ref["name"],
                }
            )
        if comparisons:
            # A kit must match at least one reference. Different registered sources
            # can themselves be misassigned; a single old conflict must not veto a match.
            best = max(comparisons, key=lambda x: x["concordance"])
            r["person_comparisons"] = comparisons
            r["person_comparison"] = best
            rate = best["concordance"]
            overlap = best["common_called_snps"]
            if overlap >= 10000 and rate < 0.85:
                r["color"] = "black"
                r["verified"] = False
                r["issues"].append(
                    "Examine other person or technical/reference issues; no automatic proof of identity."
                )
            elif rate < 0.995:
                r["color"] = "orange"
                r["issues"].append(
                    "Deviations from registered source: Assignment / Quality check."
                )
        cache = out / (str(i).zfill(3) + "_inspection.json")
        cache.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        items.append(r)
        (out / "inspection-status.json").write_text(
            json.dumps(
                {"completed": i, "total": len(paths), "last_file": Path(path).name}
            ),
            encoding="utf-8",
        )
    db.close()
    summaries = [{k: v for k, v in r.items() if k != "fingerprint"} for r in items]
    (out / "inspection.json").write_text(
        json.dumps(
            {
                "person": person,
                "files": summaries,
                "checked": datetime.datetime.now().astimezone().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return items
