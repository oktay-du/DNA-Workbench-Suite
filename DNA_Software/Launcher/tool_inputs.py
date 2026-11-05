import security_paths

"""One technical input gate shared by GUI, CLI and MCP; never a DNA identity check."""
from pathlib import Path
import suite_api, workflow_sources, source_store, tool_contracts

CONFIG_FILES = {
    "reference",
    "chain",
    "map",
    "panel",
    "labels",
    "populations",
    "score",
    "ped",
    "baseline",
    "analysis",
    "folder",
    "reference_panel",
    "refpanel",
    "sample_map",
    "samplemap",
    "base",
}


def source_fields(task):
    roles = workflow_sources.ROLES.get(task["id"], {})
    return (
        list(roles)
        if roles
        else [
            f["key"]
            for f in task["fields"]
            if f["kind"] == "file" and f["key"] not in CONFIG_FILES
        ]
    )


def prepare(r):
    person = suite_api.checked_person(r["person"])
    task = next((t for t in suite_api.CAT()["tasks"] if t["id"] == r["task"]), None)
    if not task:
        raise ValueError("Unknown tool")
    values = dict(r.get("inputs", {}))
    known = {f["key"] for f in task["fields"]}
    if set(values) - known:
        raise ValueError("Unknown input field")
    sources = source_fields(task)
    phase = r.get("phase", "ready")
    errors = []
    missing = []
    files = []
    registered = {
        str(Path(x["path"]).resolve()): x for x in source_store.listing(person)
    }
    if task["id"] == "best_dataset":
        rows = source_store.listing(person)
        builds = {
            x["build"]
            for x in rows
            if x["kind"] in ("VCF", "Chip / table", "Raw data / text")
            and x.get("origin") != "own_generated"
        }
        if builds:
            selected = values.get("build", "Automatic")
            if selected == "Automatic":
                selected = (
                    "GRCh38"
                    if "GRCh38" in builds
                    else "GRCh37"
                    if "GRCh37" in builds
                    else "Automatic"
                )
                values["build"] = selected
            if selected == "Automatic":
                missing.append({"field": "build", "label": "Confirmed target build"})
            if not values.get("reference"):
                missing.append(
                    {"field": "reference", "label": "Matching indexed reference FASTA"}
                )
        else:
            import best_assets

            if not best_assets.snapshot(person)["assets"]:
                errors.append(
                    {
                        "field": "profile",
                        "message": "Run BAM/FASTQ QC first; no checked sequence assets are available.",
                    }
                )
    contracts = [
        tool_contracts.contract(task, f) for f in task["fields"] if f["kind"] == "file"
    ]
    remedies = []
    for f in task["fields"]:
        k = f["key"]
        v = values.get(k, "")
        if phase == "sources" and k not in sources:
            continue
        if f.get("required") and (
            not v or v in ("Please select", "Unknown") if isinstance(v, str) else not v
        ):
            missing.append({"field": k, "label": f["label"]})
            continue
        if not v:
            continue
        if f["kind"] == "choice" and v not in f["choices"]:
            errors.append({"field": k, "message": "Invalid choice"})
            continue
        if f["kind"] in ("file", "folder"):
            paths = v if isinstance(v, list) else [v]
            for path in paths:
                try:
                    p = security_paths.local_path(path)
                except (ValueError, OSError) as error:
                    errors.append({"field": k, "message": str(error)})
                    continue
                if not (p.is_file() if f["kind"] == "file" else p.is_dir()):
                    errors.append(
                        {"field": k, "message": "File/folder is not available"}
                    )
                    continue
                if f["kind"] == "folder":
                    continue
                meta = workflow_sources.metadata(str(p))
                if task["id"] == "variant_evidence_audit" and phase == "ready":
                    samples = meta.get("sample_names", [])
                    selected_sample = values.get("sample", "").strip()
                    if len(samples) > 1 and not selected_sample:
                        missing.append(
                            {
                                "field": "sample",
                                "label": "VCF sample: " + ", ".join(samples)[:1000],
                            }
                        )
                    elif selected_sample and samples and selected_sample not in samples:
                        errors.append(
                            {
                                "field": "sample",
                                "message": "Select a sample present in the VCF: "
                                + ", ".join(samples)[:1000],
                            }
                        )
                role = workflow_sources.ROLES.get(task["id"], {}).get(k)
                reg = registered.get(str(p.resolve()), {})
                profile_base = (source_store.ROOT / "Profiles").resolve()
                if (
                    p.resolve().is_relative_to(profile_base)
                    and p.resolve().relative_to(profile_base).parts[0] != person
                ):
                    errors.append(
                        {
                            "field": k,
                            "message": "File belongs to another profile folder.",
                        }
                    )
                    continue
                row = dict(
                    reg, **meta, available=True, qc_color=reg.get("qc_color", "orange")
                )
                row["build"] = (
                    meta.get("build")
                    or reg.get("build")
                    or values.get({"a": "build_a", "b": "build_b"}.get(k, "build"), "")
                )
                gate = tool_contracts.evaluate(task, f, p, row)
                if not gate["accepted"]:
                    errors.extend(
                        {"field": k, "message": message} for message in gate["issues"]
                    )
                    remedies.extend(
                        {"field": k, "action": action} for action in gate["remedies"]
                    )
                    continue
                compatibility_task = (
                    ""
                    if phase == "sources"
                    and task["id"] in ("pharmcat", "liftover_snps")
                    and row["build"] not in ("GRCh37", "GRCh38")
                    else task["id"]
                )
                if (
                    role
                    and not (role in ("r1", "r2") and row["kind"] == "FASTQ")
                    and not workflow_sources.compatible(row, role, compatibility_task)
                ):
                    errors.append(
                        {
                            "field": k,
                            "message": "This file type, build or sample layout is not suitable for this tool.",
                        }
                    )
                    continue
                buildkey = {"a": "build_a", "b": "build_b"}.get(k, "build")
                detected = (
                    meta.get("build") or reg.get("build")
                    if reg.get("build") in ("GRCh37", "GRCh38")
                    else meta.get("build")
                )
                if detected and buildkey in known:
                    selected = values.get(buildkey)
                    if selected in ("GRCh37", "GRCh38") and selected != detected:
                        errors.append(
                            {
                                "field": buildkey,
                                "message": "Reference build contradicts file contents.",
                            }
                        )
                    else:
                        values[buildkey] = detected
                if (
                    row["kind"] == "CRAM"
                    and phase == "ready"
                    and not values.get("reference")
                ):
                    missing.append(
                        {
                            "field": "reference",
                            "label": "Exact original CRAM reference FASTA",
                        }
                    )
                files.append(
                    {
                        "field": k,
                        "name": p.name,
                        "kind": meta["kind"],
                        "build": detected or "unknown",
                        "compression": meta["compression"],
                        "format_version": meta.get("format_version"),
                        "warnings": gate["warnings"],
                    }
                )
    return {
        "person": person,
        "task": task["id"],
        "source_fields": sources,
        "inputs": values,
        "accepted": not errors and not missing,
        "missing": missing,
        "errors": errors,
        "files": files,
        "contracts": contracts,
        "remedies": remedies,
        "notice": "Technical compatibility only; not biological identity, clinical verification or a complete genome.",
    }
