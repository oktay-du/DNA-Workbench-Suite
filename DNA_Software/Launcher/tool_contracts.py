import security_paths

"""Conservative contracts for THIS suite's adapters, not universal vendor promises.
Bounded header probes never certify a complete file or biological identity.
"""
from pathlib import Path
import gzip, bz2, lzma, re, zipfile

ARCHIVES = {"zip", "tar", "7z", "rar"}
TEXT_PACKS = ["none", "gzip", "bgzf"]
VCF_VERSIONS = ["VCFv4.1", "VCFv4.2", "VCFv4.3"]


def probe(path):
    p = security_paths.local_path(path)
    n = p.name.lower()
    out = {
        "compression": "none",
        "format_version": None,
        "format_version_status": "not_declared",
        "header_checked": False,
    }
    try:
        with p.open("rb") as f:
            head = f.read(65536)
        if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06"):
            out["compression"] = "zip"
        elif head.startswith(b"7z\xbc\xaf\x27\x1c"):
            out["compression"] = "7z"
        elif head.startswith(b"Rar!\x1a\x07"):
            out["compression"] = "rar"
        elif head.startswith(b"BZh"):
            out["compression"] = "bzip2"
        elif head.startswith(b"\xfd7zXZ\x00"):
            out["compression"] = "xz"
        elif head.startswith(b"\x28\xb5\x2f\xfd"):
            out["compression"] = "zstd"
        elif head.startswith(b"\x1f\x8b"):
            out["compression"] = "gzip"
            if len(head) >= 12 and head[3] & 4:
                extra = head[12 : 12 + int.from_bytes(head[10:12], "little")]
                i = 0
                while i + 4 <= len(extra):
                    length = int.from_bytes(extra[i + 2 : i + 4], "little")
                    if extra[i : i + 2] == b"BC" and length == 2:
                        out["compression"] = "bgzf"
                    i += 4 + length
        elif len(head) > 262 and head[257:262] == b"ustar":
            out["compression"] = "tar"
        if n.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")):
            out["container"] = "tar"
        pack = out["compression"]
        if pack in ("gzip", "bgzf", "bzip2", "xz"):
            opener = {
                "gzip": gzip.open,
                "bgzf": gzip.open,
                "bzip2": bz2.open,
                "xz": lzma.open,
            }[pack]
            with opener(p, "rb") as f:
                head = f.read(65536)
        if head.startswith(b"CRAM") and len(head) >= 6:
            out.update(
                format_version="CRAM " + str(head[4]) + "." + str(head[5]),
                header_checked=True,
            )
        elif head.startswith(b"BCF") and len(head) >= 5:
            out.update(
                format_version="BCF " + str(head[3]) + "." + str(head[4]),
                header_checked=True,
            )
        elif head.startswith(b"BAM\x01"):
            out.update(format_version="BAM 1", header_checked=True)
        else:
            text = head.decode("utf-8-sig", errors="replace")
            m = re.search(r"^##fileformat=(VCFv[^\s]+)", text, re.M)
            if m:
                out.update(format_version=m[1], header_checked=True)
            elif re.search(r"^0 +HEAD", text, re.M):
                m = re.search(r"1 +GEDC[\s\S]{0,100}?2 +VERS +([^\s]+)", text)
                if m:
                    out.update(format_version="GEDCOM " + m[1], header_checked=True)
        if out["format_version"]:
            out["format_version_status"] = "declared"
    except (OSError, ValueError, EOFError, lzma.LZMAError) as e:
        out["header_error"] = str(e)
    return out


def contract(task, field):
    """Every file field has an explicit policy. Unknown adapters are not guessed."""
    tid = task["id"]
    k = field["key"]
    c = {
        "field": k,
        "formats": [],
        "compression": ["none"],
        "versions": [],
        "builds": [],
        "sidecars": [],
        "version_policy": "Runtime parser validation; no complete-file guarantee from a header.",
        "policy": "adapter-contract-1",
    }
    if tid in ("import", "inventory", "missing", "export"):
        c.update(
            formats=["any"],
            compression=["any"],
            version_policy="Stored/inventoried as bytes; not decoded or scientifically validated.",
        )
        return c
    if k in ("reference",):
        c.update(
            formats=["FASTA"],
            sidecars=["Matching FASTA index; exact sequence/checksum for CRAM"],
        )
    elif k == "chain":
        c.update(formats=["CHAIN"], compression=TEXT_PACKS)
    elif k in ("refpanel", "reference_panel"):
        c.update(formats=["VCF"], compression=TEXT_PACKS, versions=VCF_VERSIONS)
    elif k in (
        "map",
        "samplemap",
        "sample_map",
        "ped",
        "labels",
        "populations",
        "score",
    ):
        c.update(
            formats=["TEXT"],
            compression=TEXT_PACKS if k == "score" else ["none"],
            version_policy="Tool-specific columns/IDs/map units required; parser checks content at execution.",
        )
    elif tid == "storybook":
        c.update(formats=["PDF"])
    elif tid == "ugene":
        c.update(
            formats=["FASTA", "FASTQ", "VCF", "GENBANK", "ALIGNMENT_TEXT"],
            compression=["none"],
            version_policy="Desktop parser checks supported document version when opened.",
        )
    elif tid == "variant_evidence_audit":
        c.update(
            formats=["VCF"],
            versions=VCF_VERSIONS + ["VCFv4.4", "VCFv4.5"],
            compression=TEXT_PACKS,
            version_policy="Local accounting audit, not full VCF validation; multi-sample files require explicit sample selection.",
        )
    elif tid == "provider_export":
        c.update(
            formats=["TEXT", "JSON", "PDF", "VCF", "BCF"],
            versions=VCF_VERSIONS + ["BCF 2.2"],
            compression=TEXT_PACKS + ["zip"],
            version_policy="23andMe export schema is inspected; ambiguous JSON fields require mapping.",
        )
    elif tid in (
        "sequence_stats",
        "sequence_extract",
        "sequence_transform",
        "sequence_explore",
        "model_readiness",
        "seqviz_view",
        "fasta_collect",
        "helix_export",
    ):
        c.update(
            formats=["FASTA"]
            if tid == "fasta_collect"
            else ["FASTQ"]
            if tid == "helix_export"
            else ["FASTA", "FASTQ"],
            compression=["none", "gzip", "bgzf"],
        )
    elif k in ("r1", "r2"):
        c.update(formats=["FASTQ"], compression=TEXT_PACKS)
    elif tid == "liftover_snps":
        c.update(
            formats=["VCF", "TEXT"],
            compression=TEXT_PACKS,
            versions=VCF_VERSIONS,
            builds=["GRCh37"],
        )
    elif tid == "chip_vcf":
        c.update(
            formats=["TEXT"],
            compression=TEXT_PACKS + ["zip"],
            version_policy="Consumer genotype schema parsed by snps; ZIP must contain exactly one TXT/CSV payload.",
        )
    elif k in ("bam", "alignment"):
        c.update(
            formats=["BAM", "CRAM"],
            compression=["bgzf", "none"],
            versions=["BAM 1", "CRAM 2.1", "CRAM 3.0", "CRAM 3.1"],
            sidecars=[
                "Alignment index (created by BAM QC; required for read phasing)",
                "CRAM: exact original FASTA required",
            ],
        )
    elif tid == "inspect":
        c.update(
            formats=["VCF", "BCF", "BAM", "CRAM", "TEXT"],
            compression=TEXT_PACKS + ["zip"],
            versions=VCF_VERSIONS
            + ["BCF 2.2", "BAM 1", "CRAM 2.1", "CRAM 3.0", "CRAM 3.1"],
        )
    else:
        import workflow_sources

        role = workflow_sources.ROLES.get(tid, {}).get(k)
        if (
            role in ("vcf", "multi", "phased", "phased_multi", "normalized", "sv")
            or tid == "truvari"
        ):
            c.update(
                formats=["VCF"]
                + (
                    ["BCF"]
                    if tid in ("vcf_qc", "normalize", "filter", "variant_convert")
                    else []
                ),
                compression=TEXT_PACKS,
                versions=VCF_VERSIONS
                + (
                    ["BCF 2.2"]
                    if tid in ("vcf_qc", "normalize", "filter", "variant_convert")
                    else []
                ),
            )
            if tid == "pca":
                c["formats"].append("PGEN")
                c["sidecars"] = ["PGEN requires matching .psam and .pvar or .pvar.zst"]
        elif tid == "variant_index":
            c.update(formats=["VCF"], compression=TEXT_PACKS, versions=VCF_VERSIONS)
        elif tid == "identity":
            c.update(formats=["VCF"], compression=TEXT_PACKS, versions=VCF_VERSIONS)
    if tid in ("pharmcat", "vep"):
        c["builds"] = ["GRCh38"]
    if tid == "yhaplo":
        c["builds"] = ["GRCh37"]
    if not c["formats"]:
        c["version_policy"] = (
            "No declared file adapter; select a supported workflow instead."
        )
    return c


def logical_format(path, meta):
    kind = meta.get("kind", "")
    v = meta.get("format_version") or ""
    n = Path(path).name.lower()
    for f in ("VCF", "BCF", "BAM", "CRAM"):
        if v.startswith(f):
            return f
    if kind in ("FASTQ", "FASTA"):
        return kind
    if kind in ("Chip / table", "Raw data / text"):
        return "TEXT"
    if kind == "Report":
        return "PDF"
    if kind.startswith("JSON"):
        return "JSON"
    if n.endswith(".pgen"):
        return "PGEN"
    if n.endswith((".chain", ".chain.gz")):
        return "CHAIN"
    if n.endswith(
        (
            ".txt",
            ".csv",
            ".tsv",
            ".map",
            ".ped",
            ".psam",
            ".samples",
            ".score",
            ".txt.gz",
            ".csv.gz",
            ".tsv.gz",
        )
    ):
        return "TEXT"
    if n.endswith((".fa", ".fasta", ".fna", ".fas", ".ffn", ".fsa")):
        return "FASTA"
    if n.endswith((".gb", ".gbk", ".genbank")):
        return "GENBANK"
    if n.endswith((".aln", ".clustal", ".phy")):
        return "ALIGNMENT_TEXT"
    return kind


def evaluate(task, field, path, meta):
    c = contract(task, field)
    p = Path(path)
    fmt = logical_format(p, meta)
    pack = meta.get("compression", "none")
    issues = []
    warnings = []
    remedies = []

    def fail(message, action=None):
        issues.append(message)
        if action:
            remedies.append(action)

    if "any" in c["formats"]:
        return {
            "accepted": True,
            "contract": c,
            "issues": [],
            "warnings": [],
            "remedies": [],
        }
    if pack in ARCHIVES or meta.get("container") == "tar":
        direct_zip = (
            pack == "zip"
            and "zip" in c["compression"]
            and task["id"] in ("chip_vcf", "provider_export", "inspect")
        )
        if direct_zip:
            try:
                with zipfile.ZipFile(p) as z:
                    members = [i for i in z.infolist() if not i.is_dir()]
                    allowed = (
                        (".txt", ".csv", ".json")
                        if task["id"] == "provider_export"
                        else (".txt", ".csv")
                    )
                    if (
                        len(members) != 1
                        or not members[0].filename.lower().endswith(allowed)
                        or members[0].flag_bits & 1
                    ):
                        fail(
                            "ZIP must contain exactly one unencrypted compatible export.",
                            "batch_extract",
                        )
            except (OSError, zipfile.BadZipFile):
                fail("ZIP directory cannot be read.", "finish_download")
            if not issues:
                return {
                    "accepted": True,
                    "contract": c,
                    "issues": [],
                    "warnings": ["ZIP payload parser validation still required."],
                    "remedies": [],
                }
        else:
            fail(
                "This tool cannot read this archive directly. Extract and check its payloads first.",
                "batch_extract",
            )
    elif pack not in c["compression"]:
        fail(
            "Compression "
            + pack
            + " is not supported by this adapter. Decode/repack before use.",
            "decode_or_repack",
        )
    if fmt not in c["formats"]:
        fail(
            "Expected " + ", ".join(c["formats"]) + "; detected " + fmt + ".",
            "compatible_profile_source",
        )
        if fmt == "BCF" and "VCF" in c["formats"]:
            remedies.append("variant_convert")
        elif fmt == "TEXT" and "VCF" in c["formats"]:
            remedies.append("chip_vcf")
    version = meta.get("format_version")
    if c["versions"] and fmt in ("VCF", "BCF", "BAM", "CRAM"):
        if version and version not in c["versions"]:
            fail(
                "Declared format version "
                + version
                + " is outside this adapter contract. Preserve the original; validate/convert with a suitable parser.",
                "validate_format_version",
            )
        elif not version:
            fail(
                "Required format version/header could not be read. Check the download or decode the container.",
                "inspect",
            )
    if meta.get("header_error"):
        fail(
            "Compressed/header input could not be decoded: " + meta["header_error"],
            "finish_download",
        )
    build = meta.get("build")
    if c["builds"] and build in ("GRCh37", "GRCh38") and build not in c["builds"]:
        fail(
            "This adapter requires "
            + ", ".join(c["builds"])
            + "; source is "
            + build
            + ".",
            "liftover_snps" if build == "GRCh37" else "compatible_profile_source",
        )
    if fmt == "PGEN":
        for suffixes in [(".psam",), (".pvar", ".pvar.zst")]:
            if not any(p.with_suffix(s).is_file() for s in suffixes):
                fail(
                    "Missing PGEN sidecar: " + " or ".join(suffixes),
                    "compatible_profile_source",
                )
    if fmt == "CRAM":
        warnings.append(
            "CRAM requires the exact original reference, not merely a matching GRCh label."
        )
    if fmt in ("TEXT", "FASTQ", "FASTA", "JSON") and not version:
        warnings.append(
            "No standard format version declared; validate records/schema with the runtime parser."
        )
    return {
        "accepted": not issues,
        "contract": c,
        "issues": issues,
        "warnings": warnings,
        "remedies": list(dict.fromkeys(remedies)),
    }
