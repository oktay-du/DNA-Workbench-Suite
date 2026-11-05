"""Source-labelled research PDFs for completed local tests; no invented diagnosis."""

from pathlib import Path
import json, hashlib, html


def publish(folder, person, task, title=None):
    import source_store, profile_identity, profile_documents
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    folder = Path(folder).resolve()
    out = folder / "Results"
    out.mkdir(exist_ok=True)
    base = (source_store.ROOT / "Projects/Launcher" / person).resolve()
    if not folder.is_relative_to(base):
        raise ValueError("Report output must belong to this profile")
    request = json.loads((folder / "inputs.json").read_text(encoding="utf-8-sig"))
    status = json.loads((folder / "status.json").read_text(encoding="utf-8-sig"))
    if status.get("status") != "Complete":
        raise ValueError("Only completed local tests can be published")
    pdf = out / "local-analysis-report.pdf"
    if pdf.is_file():
        profile_documents.index_file(
            person,
            pdf,
            provider="DNA Workbench / " + task,
            report_date=str(status.get("finished", ""))[:10],
            kind="analysis_output",
            copy=False,
            log=lambda x: None,
        )
        return {"pdf": str(pdf), "existing": True}
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13

    def para(text, style="BodyText"):
        return Paragraph(html.escape(str(text)).replace("\n", "<br/>"), styles[style])

    story = [
        para(title or status.get("title", task), "Title"),
        para("LOCAL ANALYSIS · RESEARCH OUTPUT", "Heading2"),
        para(
            "Not a clinical diagnosis. This report records an executed local workflow and its outputs. It does not replace the original result artifacts."
        ),
        Spacer(1, 14),
    ]
    ident = profile_identity.ensure(person)
    details = {
        "Profiles": person,
        "Permanent profile UUID": ident["uuid"],
        "Tool/workflow": task,
        "Job": folder.name,
        "Completed": status.get("finished", ""),
        "Inputs and parameters": request.get("inputs", {}),
    }
    for key, value in details.items():
        story.extend(
            [
                para(key, "Heading3"),
                para(
                    json.dumps(value, ensure_ascii=True, indent=2)
                    if isinstance(value, dict)
                    else value
                ),
            ]
        )
    versions = folder / "versionen.json"
    if versions.is_file():
        story.extend(
            [
                para("Recorded installation versions", "Heading2"),
                para(versions.read_text(encoding="utf-8")[:12000]),
            ]
        )
    else:
        story.append(
            para(
                "No per-job executable version snapshot was recorded. Consult the dependency menu and original job log."
            )
        )
    story.append(para("Original outputs", "Heading2"))
    artifacts = []
    budget = 24000
    for p in sorted(out.rglob("*")):
        if (
            not p.is_file()
            or p.is_symlink()
            or p.name.startswith(("local-analysis-report.", "result-seal."))
        ):
            continue
        stat = p.stat()
        item = {"name": str(p.relative_to(out)), "bytes": stat.st_size}
        # Never rescan large genome files just to create an overview PDF.
        if stat.st_size <= 8 * 1024**2:
            with p.open("rb") as f:
                item["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
        artifacts.append(item)
        story.append(
            para(
                item["name"]
                + " · "
                + str(item["bytes"])
                + " bytes"
                + (
                    " · SHA-256 " + item["sha256"]
                    if "sha256" in item
                    else " · large artifact, no additional hash scan"
                )
            )
        )
        if (
            p.suffix.lower() in (".txt", ".json", ".csv", ".tsv", ".md")
            and stat.st_size <= 1024**2
            and budget > 0
        ):
            text = p.read_text(encoding="utf-8", errors="replace")[: min(6000, budget)]
            budget -= len(text)
            story.append(para(text))
            story.append(Spacer(1, 9))
    story.extend(
        [
            para("Interpretation and limitations", "Heading2"),
            para(
                "Imported provider statements, measured variants, imputed estimates and manually entered information remain separate evidence sources. A completed workflow does not prove a medical finding. Review the full output, missing data, reference build, coverage, method and conflicting assessments before interpretation."
            ),
        ]
    )
    temp = pdf.with_suffix(".partial.pdf")

    def footer(canvas, doc):
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, 24, "DNA Workbench · OD · Local research report")
        canvas.drawRightString(555, 24, str(doc.page))

    SimpleDocTemplate(
        str(temp), leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=42
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    temp.replace(pdf)
    (out / "local-analysis-report.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "kind": "analysis_output",
                "person": person,
                "profile_uuid": ident["uuid"],
                "task": task,
                "job": folder.name,
                "completed": status.get("finished"),
                "artifacts": artifacts,
                "review": "unreviewed_local_analysis",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    profile_documents.index_file(
        person,
        pdf,
        provider="DNA Workbench / " + task,
        report_date=str(status.get("finished", ""))[:10],
        kind="analysis_output",
        copy=False,
        log=lambda x: None,
    )
    return {"pdf": str(pdf), "existing": False}


def publish_all(person, log=print):
    import source_store, result_cache

    rows = []
    base = source_store.ROOT / "Projects/Launcher" / person
    for p in sorted(base.glob("*/status.json")):
        status = json.loads(p.read_text(encoding="utf-8"))
        if status.get("status") != "Complete" or status.get("task", "").startswith(
            "profile_publish"
        ):
            continue
        if status.get("kind") == "launch" or status.get("task") in result_cache.ACTIONS:
            continue
        log("Publish local report: " + p.parent.name)
        rows.append(publish(p.parent, person, status["task"]))
        result_cache.seal(p.parent)
    return {"reports": rows}
