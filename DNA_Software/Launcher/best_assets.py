"""Read/alignment assets supported by completed, source-matched local QC jobs."""

from pathlib import Path
import re
import portable_json as json
import source_store


def snapshot(person):
    rows = source_store.listing(person)
    indexed = {
        str(Path(r["path"]).resolve()): r
        for r in rows
        if r["available"] and r.get("qc_color") not in ("red", "black")
    }
    assets = []
    base = source_store.ROOT / "Projects/Launcher" / person
    for sf in base.glob("*/status.json"):
        try:
            status = json.loads(sf.read_text(encoding="utf-8"))
            task = status.get("task")
            if status.get("status") != "Complete" or task not in (
                "bam_qc",
                "fastq_report",
                "fastq_qc",
            ):
                continue
            seal = json.loads(
                (sf.parent / "result-seal.json").read_text(encoding="utf-8")
            )
            if any(
                not (sf.parent / "Results" / x["name"]).is_file()
                or (
                    (sf.parent / "Results" / x["name"]).stat().st_size,
                    (sf.parent / "Results" / x["name"]).stat().st_mtime_ns,
                )
                != (x["bytes"], x["mtime_ns"])
                for x in seal["files"]
            ):
                continue
            req = json.loads((sf.parent / "inputs.json").read_text(encoding="utf-8"))
            ins = req.get("inputs", {})
            manifest = req.get("input_manifest", {}).get("sources", [])
            out = sf.parent / "Results"
            score = 0.0
            metrics = {}
            sidecars = []
            if task == "bam_qc":
                text = (out / "samtools_stats.txt").read_text()
                values = {
                    m[0]: float(m[1])
                    for m in re.findall(r"^SN\s+([^\t]+):\s+([0-9.]+)", text, re.M)
                }
                if values.get("raw total sequences", 0):
                    score = (
                        values.get("reads mapped", 0) / values["raw total sequences"]
                    )
                    metrics = {
                        "mapped_fraction": score,
                        "total_reads": values["raw total sequences"],
                    }
                for name in ("reads.bam.bai", "reads.cram.crai"):
                    if (out / name).is_file():
                        sidecars.append(str(out / name))
                if not sidecars:
                    continue
                if (
                    str(ins.get("bam", "")).lower().endswith(".cram")
                    and not Path(ins.get("reference", "")).is_file()
                ):
                    continue
                keys = ["bam"]
            else:
                report = next(
                    (
                        p
                        for p in (out / "fastq_quality.json", out / "fastp.json")
                        if p.is_file()
                    ),
                    None,
                )
                if not report:
                    continue
                data = json.loads(report.read_text())
                metrics = data["summary"]["before_filtering"]
                score = float(metrics.get("q30_rate", 0))
                keys = ["r1", "r2"]
            for key in keys:
                if not ins.get(key):
                    continue
                path = Path(ins[key]).resolve()
                row = indexed.get(str(path))
                source = next((x for x in manifest if x.get("path") == str(path)), None)
                if not row or not source or source.get("sha256") != row["sha256"]:
                    continue
                st = path.stat()
                if (source.get("bytes"), source.get("mtime_ns")) != (
                    st.st_size,
                    st.st_mtime_ns,
                ):
                    continue
                assets.append(
                    {
                        "source_id": row["id"],
                        "path": str(path),
                        "sha256": row["sha256"],
                        "bytes": st.st_size,
                        "mtime_ns": st.st_mtime_ns,
                        "provider": row["provider"],
                        "build": row["build"],
                        "kind": row["kind"],
                        "role": key,
                        "qc_job": sf.parent.name,
                        "qc_task": task,
                        "metrics": metrics,
                        "rank_score": score,
                        "sidecars": sidecars,
                        "reference": ins.get("reference", ""),
                        "status": "source-matched QC completed; not clinical or biological identity verification",
                    }
                )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    # Keep different builds/formats separate; paired reads selected from one QC run.
    alignment = {}
    pairs = {}
    for a in assets:
        if a["role"] == "bam":
            key = (a["kind"], a["build"])
            if key not in alignment or a["rank_score"] > alignment[key]["rank_score"]:
                alignment[key] = a
        else:
            pairs.setdefault(a["qc_job"], []).append(a)
    best_pair = max(
        pairs.values(), key=lambda p: (len(p), p[0]["rank_score"]), default=[]
    )
    return {
        "assets": list(alignment.values()) + best_pair,
        "candidates": assets,
        "notice": "Alignment mapping fraction and read Q30 are separate technical metrics, not a universal genome quality score. References and sidecars retain their original QC-job provenance.",
    }


def link_into(assets, destination):
    import os

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    result = []
    for i, a in enumerate(assets, 1):
        source = Path(a["path"])
        name = f"{i:03d}-" + source.name
        target = destination / name
        try:
            os.link(source, target)
            mode = "hardlink"
        except OSError:
            mode = "reference"
            target = target.with_name(target.name + ".dna-source.json")
            target.write_text(json.dumps(a, indent=2), encoding="utf-8")
        item = dict(a, bundle_path=str(target), storage=mode)
        linked = []
        for sidecar in a["sidecars"]:
            original = Path(sidecar)
            suffix = ".bai" if original.name.endswith(".bai") else ".crai"
            dest = destination / (name + suffix)
            try:
                os.link(original, dest)
                linked.append(
                    {"source": str(original), "path": str(dest), "storage": "hardlink"}
                )
            except OSError:
                linked.append({"source": str(original), "storage": "reference"})
        item["bundle_sidecars"] = linked
        result.append(item)
    return result
