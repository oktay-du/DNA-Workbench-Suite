"""Explicit, versioned publication of conservative SNP selection + source assets.
No claim of a perfect genome or fabricated FASTQ/BAM/structural calls.
"""

from pathlib import Path
from contextlib import closing
import datetime, gzip, hashlib, os, shutil, uuid
import portable_json as json
import source_store, profile_pipeline as pp


def build(person, out, build, reference, chain=None, log=print, cancel=lambda: False):
    with pp.refresh_lock(person):
        return _build(
            person,
            Path(out),
            build,
            Path(reference) if reference else None,
            chain,
            log,
            cancel,
        )


def _build(person, out, build, reference, chain, log, cancel):
    out.mkdir(parents=True, exist_ok=True)
    rows = [
        r for r in source_store.listing(person) if r.get("origin") != "own_generated"
    ]
    if not rows:
        raise ValueError("Import profile sources first.")
    relevant = {
        r["build"]
        for r in rows
        if r["kind"] in ("VCF", "Chip / table", "Raw data / text")
    }
    if build == "Automatic":
        build = (
            "GRCh38"
            if "GRCh38" in relevant
            else "GRCh37"
            if "GRCh37" in relevant
            else "Automatic"
        )
    import best_assets

    checked_assets = best_assets.snapshot(person)["assets"]
    if not relevant:
        return publish_assets(person, out, checked_assets, log, cancel)
    if build not in ("GRCh37", "GRCh38") or not reference:
        raise ValueError(
            "Genotype selection requires a confirmed target build and matching indexed reference FASTA."
        )
    if build == "GRCh37" and "GRCh38" in relevant:
        raise ValueError(
            "GRCh38 sources cannot be silently down-labelled. Choose GRCh38 or a separate explicitly reviewed selection."
        )
    analysis = out / "Analysis"
    generated = out / "Generated"
    target = "GRCh38" if build == "GRCh38" and "GRCh37" in relevant else "separate"
    pp.atomic(
        out.parent / "inspection-status.json",
        {"completed": 0, "total": 4, "unit": "steps"},
    )
    log("1/4 Check all imported source genotypes and conflicts")
    pp.analyze(
        person, analysis, log, cancel, target=target, chain=chain, reference=reference
    )
    pp.atomic(
        out.parent / "inspection-status.json",
        {"completed": 1, "total": 4, "unit": "steps"},
    )
    log("2/4 Select supported observed SNP calls; preserve exclusions")
    result = pp.generate(person, analysis, generated, build, reference, log, cancel)
    pp.atomic(
        out.parent / "inspection-status.json",
        {"completed": 2, "total": 4, "unit": "steps"},
    )
    log("3/4 Generate equivalent core formats and provenance")
    for name in ["best_selection.vcf", "best_selection.txt", "best_selection.tsv"]:
        src = generated / name
        dest = generated / (name + ".gz")
        with src.open("rb") as inp, dest.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, mtime=0
            ) as compressed:
                while block := inp.read(8 * 1024**2):
                    if cancel():
                        raise InterruptedError(
                            "BestDataset cancelled; previous current dataset retained."
                        )
                    compressed.write(block)
        with gzip.open(dest, "rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != pp.digest(
                src, cancel
            ):
                raise ValueError("Compressed export roundtrip failed.")
        result["files"][dest.name] = pp.digest(dest, cancel)
    assets = []
    for row in rows:
        assets.append(
            {
                "source_id": row["id"],
                "sha256": row["sha256"],
                "path": row["path"],
                "provider": row["provider"],
                "name": row["original_name"],
                "build": row["build"],
                "versions": row.get("versions", []),
                "declared_version": row.get("declared_version", ""),
                "created": row["created"],
                "kind": row["kind"],
                "qc_color": row.get("qc_color"),
                "qc_verified": row.get("qc_verified", False),
                "handling": "reference to managed original; not recreated or an independent measurement",
            }
        )
    result.update(
        label="BestDataset · observed SNP selection",
        dataset_name="BestDataset",
        source_assets=assets,
        available_formats=["VCF", "TXT", "TSV", "VCF.gz (gzip)", "TXT.gz", "TSV.gz"],
        unavailable_formats={
            "FASTQ": "Cannot reconstruct reads from genotypes; use validated imported read assets.",
            "BAM/CRAM": "Require original reads/alignments and matching reference; use managed imported assets.",
            "complete FASTA": "Unobserved bases, phasing and structural variation are not resolved by SNP consensus.",
            "BCF/PLINK": "Use the explicit installed conversion adapters after this dataset is generated.",
        },
    )
    (generated / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    base = source_store.profile_dir(person) / "BestDataset"
    version = (
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + "_"
        + build
        + "_"
        + uuid.uuid4().hex[:8]
    )
    dest = base / "Versions" / version
    dest.mkdir(parents=True, exist_ok=False)
    try:
        for p in generated.iterdir():
            if not p.is_file():
                continue
            target = dest / p.name
            try:
                os.link(p, target)
            except OSError:
                shutil.copyfile(p, target)
            if pp.digest(target, cancel) != pp.digest(p, cancel):
                raise ValueError("Published artifact differs from generated output.")
        if cancel():
            raise InterruptedError(
                "Cancelled before activation; previous dataset retained."
            )
        pp.atomic(
            out.parent / "inspection-status.json",
            {"completed": 3, "total": 4, "unit": "steps"},
        )
        log("4/4 Validate and activate BestDataset; keep previous generations")
        linked_assets = best_assets.link_into(checked_assets, dest / "Assets")
        result["checked_assets"] = linked_assets
        (dest / "manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        activated = pp.activate(person, dest, cancel)
        pointer = {
            "schema": 1,
            "person": person,
            "build": build,
            "folder": str(dest),
            "created": result["created"],
            "name": "BestDataset",
            "version": version,
            "manifest": str(dest / "manifest.json"),
            "files": result["files"],
            "scope": result["scope"],
        }
        pp.atomic(base / "current.json", pointer)
        pp.atomic(out / "BestDataset.json", pointer)
        pp.atomic(
            out.parent / "inspection-status.json",
            {"completed": 4, "total": 4, "unit": "steps"},
        )
        log("BestDataset ready: " + str(dest))
        return dict(
            pointer,
            activated=activated,
            source_contributions=result["source_contributions"],
        )
    except BaseException:
        # Failed generation directories are retained for diagnostics; never selected
        # by current.json or treated as a second DNA test.
        raise


def publish_assets(person, out, assets, log, cancel):
    if not assets:
        raise ValueError(
            "No source-matched completed BAM/FASTQ QC is available. Run batch file preparation/QC before BestDataset."
        )
    if cancel():
        raise InterruptedError("Cancelled; previous dataset retained.")
    import best_assets

    version = (
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + "_reads_"
        + uuid.uuid4().hex[:8]
    )
    base = source_store.profile_dir(person) / "BestDataset"
    dest = base / "Versions" / version
    dest.mkdir(parents=True, exist_ok=False)
    linked = best_assets.link_into(assets, dest / "Assets")
    stamp = pp.NOW()
    r = {
        "person": person,
        "build": "Source-specific / unaligned",
        "created": stamp,
        "folder": str(dest),
        "dataset_name": "BestDataset",
        "dataset_kind": "checked_sequence_assets",
        "label": "BestDataset · QC-supported sequence assets",
        "scope": "Source-matched read/alignment QC; no generated genotype consensus or clinical validation.",
        "statistics": {"included": 0},
        "files": {},
        "checked_assets": linked,
        "provider_contributions": [],
        "source_contributions": [],
        "imported_snapshot": sorted(
            {
                x["sha256"]
                for x in source_store.listing(person)
                if x.get("origin") != "own_generated"
            }
        ),
        "preferred_for": ["bam_qc", "fastq_report", "fastq_qc", "deepvariant", "sarek"],
    }
    pp.atomic(dest / "manifest.json", r)
    (dest / "source-contributions.tsv").write_text(
        "provider\trole\tsource_sha256\tqc_job\n"
        + "".join(
            a["provider"]
            + "\t"
            + a["role"]
            + "\t"
            + a["sha256"]
            + "\t"
            + a["qc_job"]
            + "\n"
            for a in assets
        ),
        encoding="utf-8",
    )
    with closing(source_store.connect(person)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS preferred_asset_sets(id TEXT PRIMARY KEY,payload TEXT,updated TEXT)"
        )
        db.execute(
            "INSERT OR REPLACE INTO preferred_asset_sets VALUES(?,?,?)",
            ("current", json.dumps(r), stamp),
        )
        db.commit()
    pointer = {
        "person": person,
        "build": r["build"],
        "folder": str(dest),
        "created": stamp,
        "name": "BestDataset",
        "version": version,
        "manifest": str(dest / "manifest.json"),
        "scope": r["scope"],
    }
    pp.atomic(base / "current.json", pointer)
    pp.atomic(out / "BestDataset.json", pointer)
    log("BestDataset checked sequence assets ready: " + str(dest))
    return dict(pointer, activated=True, source_contributions=[])
