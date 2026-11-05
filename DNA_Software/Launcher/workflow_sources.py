from contextlib import closing

"""Conservative, tool-specific source suggestions and reproducible result freshness."""
from pathlib import Path
import gzip
import portable_json as json
import source_store
import security_paths

# Only biological inputs are auto-selected. Panels, maps, truth sets and FASTA
# remain explicit: a matching build alone does not establish compatibility.
ROLES = {
    "identity": {"a": "any", "b": "any"},
    "inspect": {"file": "any"},
    "vcf_qc": {"vcf": "vcf"},
    "chip_vcf": {"file": "chip"},
    "fastq_report": {"r1": "r1", "r2": "r2"},
    "fastq_qc": {"r1": "r1", "r2": "r2"},
    "bam_qc": {"bam": "alignment"},
    "sarek": {"r1": "r1", "r2": "r2"},
    "deepvariant": {"bam": "alignment"},
    "normalize": {"vcf": "vcf"},
    "filter": {"vcf": "vcf"},
    "conflicts": {"a": "normalized", "b": "normalized"},
    "merge": {"files": "normalized"},
    "roh": {"vcf": "vcf"},
    "peddy": {"vcf": "multi"},
    "whatshap": {"vcf": "vcf", "alignment": "alignment"},
    "truvari": {"comparison": "sv"},
    "kinship": {"vcf": "multi"},
    "pca": {"file": "multi"},
    "beagle": {"vcf": "vcf"},
    "ibd": {"vcf": "phased_multi"},
    "rfmix": {"query": "phased"},
    "mito": {"vcf": "vcf"},
    "yhaplo": {"vcf": "vcf"},
    "opencravat_run": {"vcf": "vcf"},
    "vep": {"vcf": "vcf"},
    "pharmcat": {"vcf": "vcf"},
    "pgs": {"vcf": "vcf"},
    "variant_index": {"files": "vcf"},
}
ROLES["variant_convert"] = {"vcf": "vcf"}
ROLES["liftover_snps"] = {"file": "any"}
ROLES["helix_export"] = {"file": "r1"}
ROLES["provider_export"] = {"file": "provider_export"}
ROLES.update(
    {
        "sequence_stats": {"files": "sequence"},
        "fasta_collect": {"files": "fasta"},
        "sequence_extract": {"file": "sequence"},
        "sequence_transform": {"file": "sequence"},
        "sequence_explore": {"file": "sequence"},
        "model_readiness": {"file": "sequence"},
        "variant_evidence_audit": {"vcf": "vcf"},
        "seqviz_view": {"file": "sequence"},
        "gatk_validate": {"vcf": "vcf"},
    }
)


def metadata(path):
    p = security_paths.local_path(path)
    kind = source_store.classify(p.name)
    build = source_store.build_hint(p)
    import tool_contracts

    out = {
        "path": str(p),
        "kind": kind,
        "build": build,
        "samples": None,
        "phased": False,
        "sv": False,
        "normalized": False,
        **tool_contracts.probe(p),
    }
    if not p.is_file():
        return out
    if kind == "VCF":
        try:
            op = gzip.open if p.name.endswith((".gz", ".bgz")) else open
            with op(p, "rt", encoding="utf-8-sig", errors="replace") as stream:
                # Bounded read: never scan a whole genome in the dialog.
                text = stream.read(262144)
            out["normalized"] = "##bcftools_normCommand=" in text
            for line in text.splitlines():
                if line.startswith("#CHROM\t"):
                    out["samples"] = max(0, len(line.split("\t")) - 9)
                    out["sample_names"] = line.split("\t")[9:265]
                elif line and not line.startswith("#"):
                    cols = line.split("\t")
                    if len(cols) > 9:
                        keys = cols[8].split(":")
                        if "GT" in keys:
                            i = keys.index("GT")
                            out["phased"] |= any(
                                "|" in x.split(":")[i]
                                for x in cols[9:]
                                if len(x.split(":")) > i
                            )
                    if len(cols) > 7:
                        out["sv"] |= (
                            "SVTYPE=" in cols[7]
                            or "[" in cols[4]
                            or "]" in cols[4]
                            or "<DEL>" in cols[4]
                            or "<DUP>" in cols[4]
                        )
        except (OSError, ValueError, EOFError):
            pass
    return out


def rank(row):
    measurement = str(row.get("measurement", "")).lower()
    measured = (
        0
        if "imput" in measurement
        else 2
        if measurement in ("gemessen", "measured")
        else 1
    )
    return (
        measured,
        bool(row.get("qc_verified")),
        int(row.get("qc_points") or 0),
        int(row.get("called_points") or 0),
    )


def compatible(row, role, task):
    if (
        not row.get("available", True)
        or row.get("qc_color") in ("red", "black")
        or row.get("lifecycle") in ("needs_review", "withdrawn")
        or row.get("qc_review_required")
    ):
        return False
    kind = row.get("kind")
    name = Path(row["path"]).name.lower()
    if task:
        import tool_contracts, suite_api

        spec = next((t for t in suite_api.CAT()["tasks"] if t["id"] == task), None)
        key = next((k for k, v in ROLES.get(task, {}).items() if v == role), None)
        field = (
            next((f for f in spec["fields"] if f["key"] == key), None) if spec else None
        )
        if field:
            meta = dict(row, **tool_contracts.probe(row["path"]))
            if not tool_contracts.evaluate(spec, field, row["path"], meta)["accepted"]:
                return False
    if role == "provider_export":
        return kind in (
            "Report",
            "VCF",
            "Raw data / text",
            "Chip / table",
            "JSON/report or pedigree",
            "Archive",
        )
    if role in ("sequence", "fasta"):
        formats = (".fa", ".fasta", ".fna", ".ffn", ".fas", ".fsa") + (
            (".fastq", ".fq") if role == "sequence" else ()
        )
        return name.endswith(formats + tuple(x + ".gz" for x in formats))
    if task == "pharmcat" and row.get("build") != "GRCh38":
        return False
    if task == "liftover_snps" and row.get("build") != "GRCh37":
        return False
    if role == "any":
        return kind in (
            "VCF",
            "BCF",
            "BAM",
            "CRAM",
            "Chip / table",
            "Raw data / text",
            "Archive",
        )
    if role == "chip":
        return kind in ("Chip / table", "Raw data / text", "Archive")
    if role == "alignment":
        return kind in ("BAM", "CRAM")
    if role in ("r1", "r2"):
        import re

        return kind == "FASTQ" and (
            task == "helix_export"
            or bool(re.search(r"(?:^|[_.-])" + role + r"(?:[_.-]|$)", name))
        )
    if (
        kind == "BCF"
        and role == "vcf"
        and task in ("vcf_qc", "normalize", "filter", "variant_convert")
    ):
        return True
    if task == "pca" and name.endswith(".pgen"):
        return True
    if kind != "VCF":
        return False
    if role == "normalized" and not row.get("normalized"):
        return False
    if role in ("multi", "phased_multi") and (row.get("samples") or 0) < 2:
        return False
    if role in ("phased", "phased_multi") and not row.get("phased"):
        return False
    if role == "sv" and not row.get("sv"):
        return False
    return True


def manifest(task, values, rows):
    indexed = {str(Path(x["path"]).resolve()): x for x in rows}
    sources = []
    roles = (
        ROLES.get(task, {})
        if task != "storybook"
        else {
            k: "report"
            for k in ("maternal_report", "paternal_report", "archaic_report")
        }
    )
    for field, role in roles.items():
        val = values.get(field, [])
        paths = val if isinstance(val, list) else [val]
        for path in paths:
            if not path:
                continue
            p = security_paths.local_path(path)
            row = indexed.get(str(p.resolve()), {})
            stat = p.stat() if p.is_file() else None
            sources.append(
                {
                    "field": field,
                    "path": str(p.resolve()),
                    "sha256": row.get("sha256"),
                    "bytes": stat.st_size if stat else None,
                    "mtime_ns": stat.st_mtime_ns if stat else None,
                    "rank": list(rank(row)),
                    "build": source_store.build_hint(p) or row.get("build"),
                    "source_aliases": [
                        {
                            k: x.get(k)
                            for k in (
                                "id",
                                "provider",
                                "original_name",
                                "batch_id",
                                "created",
                                "declared_version",
                                "versions",
                                "sha256",
                            )
                        }
                        for x in rows
                        if str(Path(x["path"]).resolve()) == str(p.resolve())
                    ],
                }
            )
    return {"task": task, "sources": sources, "inputs": values}


def result_files(root, pid, job):
    base = security_paths.job(root, pid, job) / "Results"
    rows = []
    if base.is_dir():
        for p in base.rglob("*"):
            if len(rows) >= 100:
                break
            if p.is_file() and p.resolve().is_relative_to(base):
                rows.append(
                    {"name": p.relative_to(base).as_posix(), "bytes": p.stat().st_size}
                )
    return rows


def plan(root, pid, task, history, scope_ids=None):
    pid = security_paths.identifier(pid)
    rows = source_store.listing(pid)
    if scope_ids is not None:
        rows = [x for x in rows if x["id"] in scope_ids]
        history = []
    roles = ROLES.get(task, {})
    preferred = set()
    with closing(source_store.connect(pid)) as register, register:
        if register.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='preferred_sets'"
        ).fetchone():
            for (payload,) in register.execute(
                "SELECT payload FROM preferred_sets ORDER BY updated DESC LIMIT 1"
            ):
                selection = json.loads(payload)
                # A new import is an availability notice, not permission to
                # replace the active selection before the user requests renewal.
                valid = True
                for item in selection.get("source_state", []):
                    p = Path(item["path"])
                    valid = (
                        valid
                        and p.is_file()
                        and p.stat().st_size == item["bytes"]
                        and p.stat().st_mtime_ns == item["mtime_ns"]
                    )
                p = Path(selection["folder"]) / "best_selection.vcf"
                saved = selection.get("output_state", {})
                valid = (
                    valid
                    and p.is_file()
                    and p.stat().st_size == saved.get("bytes")
                    and p.stat().st_mtime_ns == saved.get("mtime_ns")
                )
                if valid and task in selection.get("preferred_for", []):
                    preferred.add(str(p))
    import best_assets

    raw_best = best_assets.snapshot(pid)
    if task in (
        "bam_qc",
        "deepvariant",
        "fastq_report",
        "fastq_qc",
        "sarek",
        "helix_export",
    ):
        preferred.update(a["path"] for a in raw_best["assets"])
    # Completed VCF outputs belong to this profile as well. They do not inherit
    # a green QC badge or unsupported point counts from their parent inputs.
    known = {str(Path(x["path"]).resolve()) for x in rows}
    for job in history:
        if job.get("status") != "Complete":
            continue
        base = security_paths.job(root, pid, job["job"]) / "Results"
        for artifact in result_files(root, pid, job["job"]):
            p = base / artifact["name"]
            if source_store.classify(p.name) != "VCF" or str(p.resolve()) in known:
                continue
            known.add(str(p.resolve()))
            rows.append(
                {
                    "path": str(p),
                    "original_name": p.name,
                    "provider": "DNA Workbench",
                    "label": job.get("title", job["job"]),
                    "kind": "VCF",
                    "build": "Unknown",
                    "available": True,
                    "qc_color": "orange",
                    "qc_verified": False,
                    "measurement": "Unknown",
                    "qc_points": 0,
                    "called_points": 0,
                }
            )
    candidates = []
    for row in rows:
        if row.get("available"):
            meta = metadata(row["path"])
            row.update({k: v for k, v in meta.items() if k not in ("build", "kind")})
            if meta["build"]:
                row["build"] = meta["build"]
        candidates.append(row)
    chosen = {}
    used = set()
    warnings = []
    options = {}
    if task == "storybook":
        import re
        import profile_documents

        reports = [
            Path(x["path"])
            for x in profile_documents.listing(pid)
            if x.get("available") and x["path"].lower().endswith(".pdf")
        ]
        reports += [
            Path(x["path"])
            for x in rows
            if x.get("available") and x["path"].lower().endswith(".pdf")
        ]
        for key, pattern in [
            ("maternal_report", "maternal.*haplogroup"),
            ("paternal_report", "paternal.*haplogroup"),
            ("archaic_report", "^Neanderthal -"),
        ]:
            found = sorted(
                (p for p in reports if re.search(pattern, p.name, re.I)),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if found:
                chosen[key] = str(found[0])
    for key, role in roles.items():
        good = sorted(
            (x for x in candidates if compatible(x, role, task)),
            key=lambda x: (
                x["path"] not in preferred,
                tuple(-v for v in rank(x)),
                x["path"],
            ),
        )
        options[key] = [
            {
                "path": x["path"],
                "name": x["original_name"],
                "provider": x["provider"],
                "build": x["build"],
                "rank": list(rank(x)),
            }
            for x in good
        ]
        if (
            role in ("alignment", "r1", "r2")
            and task not in ("inspect", "bam_qc", "fastq_report", "fastq_qc")
            and scope_ids is None
        ):
            good = [
                x
                for x in good
                if any(a["path"] == x["path"] for a in raw_best["assets"])
            ]
        good = [x for x in good if x["path"] not in used]
        if good:
            best = good[0]
            chosen[key] = [best["path"]] if key == "files" else best["path"]
            used.add(best["path"])
            if task in ("sequence_stats", "fasta_collect") and key == "files":
                chosen[key] = [x["path"] for x in good]
        else:
            warnings.append(
                "No properly verified source for"
                + key
                + "Select file manually or check source."
            )
    # Paired reads must share a provider batch and a unique matching filename stem.
    if "r1" in chosen and "r2" in chosen:
        import re

        a, b = (
            next(x for x in candidates if x["path"] == chosen[k]) for k in ("r1", "r2")
        )
        stem = lambda p: re.sub(
            r"([_.-])r[12]([_.-])", r"\1rX\2", Path(p).name, flags=re.I
        )
        verified_pair = any(
            x["path"] == a["path"]
            and x["role"] == "r1"
            and any(
                y["path"] == b["path"]
                and y["role"] == "r2"
                and y["qc_job"] == x["qc_job"]
                for y in raw_best["assets"]
            )
            for x in raw_best["assets"]
        )
        if not verified_pair and (
            Path(a["path"]).parent != Path(b["path"]).parent
            or a["provider"] != b["provider"]
            or stem(a["original_name"]) != stem(b["original_name"])
        ):
            chosen.pop("r2")
            warnings.append("FASTQ pair inconclusive: select R2 explicitly.")
    build_fields = {"a": "build_a", "b": "build_b"}
    builds = []
    for key, path in list(chosen.items()):
        paths = path if isinstance(path, list) else [path]
        for p in paths:
            build = next((x["build"] for x in candidates if x["path"] == p), None)
            if build is None:
                continue
            if build in ("GRCh37", "GRCh38"):
                builds.append(build)
                if key in build_fields:
                    chosen[build_fields[key]] = build
    if (
        builds
        and len(set(builds)) == 1
        and any(
            t["id"] == task and any(f["key"] == "build" for f in t["fields"])
            for t in __import__("suite_api").CAT()["tasks"]
        )
    ):
        chosen["build"] = builds[0]
    elif len(set(builds)) > 1:
        warnings.append(
            "Sources have different reference builds; do not process together."
        )
    if task in ("profile_generate", "best_dataset"):
        available = [
            j
            for j in history
            if j.get("task") == "profile_analyze" and j.get("status") == "Complete"
        ]
        analysis_target = None
        if available:
            chosen["analysis"] = str(
                security_paths.job(root, pid, available[0]["job"]) / "Results"
            )
            try:
                analysis_target = json.loads(
                    (Path(chosen["analysis"]) / "analysis.json").read_text(
                        encoding="utf-8"
                    )
                ).get("target")
            except (OSError, ValueError):
                pass
        present = {r["build"] for r in rows if r.get("origin") != "own_generated"}
        if analysis_target == "GRCh38" or "GRCh38" in present:
            chosen["build"] = "GRCh38"
        elif "GRCh37" in present:
            chosen["build"] = "GRCh37"
    if task in ("liftover_snps", "profile_generate", "best_dataset", "chip_vcf"):
        target = "GRCh38" if task == "liftover_snps" else chosen.get("build")
        reference = root / (
            "References/FASTA_GRCh38/GRCh38_full_analysis_set_plus_decoy_hla.fa"
            if target == "GRCh38"
            else "References/FASTA_GRCh37/hs37d5.fa"
        )
        if target and reference.is_file() and Path(str(reference) + ".fai").is_file():
            chosen["reference"] = str(reference)
        chain = root / "References/LiftOver/hg19ToHg38.over.chain.gz"
        if task in ("liftover_snps", "best_dataset") and chain.is_file():
            chosen["chain"] = str(chain)
    previous = next(
        (j for j in history if j.get("task") == task and j.get("status") == "Complete"),
        None,
    )
    freshness = "none"
    reason = "No completed result yet."
    if previous:
        path = security_paths.job(root, pid, previous["job"]) / "inputs.json"
        try:
            old = json.loads(path.read_text(encoding="utf-8")).get("input_manifest")
        except (OSError, ValueError):
            old = None
        freshness = "unknown"
        reason = "Old run without source comparison. Check input before reuse."
        if old:
            freshness = "current"
            reason = (
                "No better matching profile source is recognized compared to this run."
            )
            for key, value in chosen.items():
                if key not in roles:
                    continue
                oldrows = [x for x in old["sources"] if x["field"] == key]
                paths = value if isinstance(value, list) else [value]
                for p in paths:
                    row = next(x for x in candidates if x["path"] == p)
                    if (
                        not oldrows
                        or rank(row) > max(tuple(x.get("rank", [])) for x in oldrows)
                        or (
                            p in preferred
                            and all(
                                x["path"] != str(Path(p).resolve()) for x in oldrows
                            )
                        )
                    ):
                        freshness = "better"
                        reason = "Better or previously missing suitable profile source available."
            for oldrow in old["sources"]:
                p = Path(oldrow["path"])
                if (
                    not p.is_file()
                    or p.stat().st_size != oldrow.get("bytes")
                    or p.stat().st_mtime_ns != oldrow.get("mtime_ns")
                ):
                    if freshness != "better":
                        freshness = "changed"
                        reason = "An earlier input file is missing or has been changed."
        previous = dict(previous, artifacts=result_files(root, pid, previous["job"]))
        if task == "profile_analyze":
            try:
                old_report = json.loads(
                    (
                        security_paths.job(root, pid, previous["job"])
                        / "Results/analysis.json"
                    ).read_text(encoding="utf-8")
                )
                old_hashes = {
                    x["sha256"]
                    for x in old_report["sources"]
                    if x["status"] != "derived-not-independent"
                }
                current_hashes = {
                    x["sha256"] for x in rows if x.get("origin") != "own_generated"
                }
                if old_hashes != current_hashes:
                    freshness = "better"
                    reason = "Profile sources changed; re-analyze all files."
            except (OSError, ValueError, KeyError):
                freshness = "unknown"
                reason = "Re-examine previous source status."
        if (
            task == "profile_generate"
            and old
            and old.get("inputs", {}).get("analysis") != chosen.get("analysis")
        ):
            freshness = "better"
            reason = "A more recent profile analysis is available."
    import workflows

    assembled = {
        "inputs": chosen,
        "options": options,
        "library": [
            {"path": x["path"], "name": x["original_name"], "provider": x["provider"]}
            for x in candidates
            if x.get("available")
        ],
        "warnings": warnings,
        "previous": previous,
        "freshness": freshness,
        "reason": reason,
        "ranking": "Appropriate format and tool requirements; measured before imputed, then QC confirmation and occupied points. file size and download date are not proof of quality.",
    }
    return workflows.augment(pid, task, history, assembled)
