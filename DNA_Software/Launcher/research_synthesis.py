"""Final source-cited research overview; never average incomparable diagnoses/models."""

from pathlib import Path
import html, datetime, math
import portable_json as json
import source_store, profile_documents, visual_store


def weighted_ancestry(reports):
    groups = {}
    pending = []
    for r in reports:
        d = r.get("data", r)
        meta = d.get("comparability", {})
        q = d.get("quality", {})
        keys = (
            "population_scheme",
            "reference_panel",
            "panel_version",
            "calibration",
            "method_version",
        )
        if not all(meta.get(k) for k in keys):
            pending.append(
                {
                    "provider": d.get("provider"),
                    "reason": "No compatible population/reference/calibration metadata; percentages retained separately.",
                }
            )
            continue
        n = q.get("relevant_called")
        total = q.get("relevant_total")
        root = d.get("source_root_sha256")
        model_quality = q.get("model_quality")
        if (
            not root
            or not isinstance(n, (int, float))
            or not isinstance(total, (int, float))
            or total <= 0
            or not 0 < n <= total
            or not isinstance(model_quality, (int, float))
            or not 0 < model_quality <= 1
            or not all(math.isfinite(x) for x in (n, total, model_quality))
        ):
            pending.append(
                {
                    "provider": d.get("provider"),
                    "reason": "No documented marker-specific weight or source identity.",
                }
            )
            continue
        regions = d.get("regions", [])
        if (
            not regions
            or len({x.get("population_id") for x in regions}) != len(regions)
            or any(
                not x.get("population_id")
                or not isinstance(x.get("percent"), (int, float))
                or not math.isfinite(x["percent"])
                or not 0 <= x["percent"] <= 100
                for x in regions
            )
        ):
            pending.append(
                {
                    "provider": d.get("provider"),
                    "reason": "Canonical population IDs missing.",
                }
            )
            continue
        key = tuple(str(meta[k]) for k in keys)
        weight = n / total * model_quality
        group = groups.setdefault(key, {})
        # Same underlying measurement is not an additional vote.
        if root not in group or weight > group[root][0]:
            group[root] = (weight, d)
    calculated = []
    for key, byroot in groups.items():
        ids = [
            set(x["population_id"] for x in d["regions"]) for w, d in byroot.values()
        ]
        if any(s != ids[0] for s in ids):
            pending.append(
                {
                    "model": key,
                    "reason": "Different category coverage; missing categories are not treated as zero.",
                }
            )
            continue
        denominator = sum(w for w, d in byroot.values())
        values = []
        for region in sorted(ids[0]):
            values.append(
                {
                    "population_id": region,
                    "percent": sum(
                        w
                        * next(
                            x["percent"]
                            for x in d["regions"]
                            if x["population_id"] == region
                        )
                        for w, d in byroot.values()
                    )
                    / denominator,
                }
            )
        calculated.append(
            {
                "comparability": list(key),
                "regions": values,
                "independent_source_roots": len(byroot),
                "weights": [
                    {"provider": d["provider"], "weight": w, "source_root_sha256": root}
                    for root, (w, d) in byroot.items()
                ],
                "status": "exploratory technical weighting; not a calibrated ethnicity probability or clinical finding",
            }
        )
    return {"calculated": calculated, "kept_separate": pending}


def build(person, out, log=print):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sources = source_store.listing(person)
    documents = [
        d
        for d in profile_documents.listing(person)
        if d["kind"] != "calculated_research"
        and "research_synthesis" not in d.get("provider", "")
    ]
    visual = [r for r in visual_store.listing() if r["person"] == person]
    jobs = []
    base = source_store.ROOT / "Projects/Launcher" / person
    for sf in sorted(
        base.glob("*/status.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
            if s.get("status") != "Complete" or s.get("task") in (
                "research_synthesis",
                "source_batch",
            ):
                continue
            req = (
                json.loads((sf.parent / "inputs.json").read_text(encoding="utf-8"))
                if (sf.parent / "inputs.json").is_file()
                else {}
            )
            jobs.append(
                {
                    "job": sf.parent.name,
                    "task": s.get("task"),
                    "finished": s.get("finished"),
                    "inputs": req.get("input_manifest") or req.get("inputs"),
                    "outputs": s.get("outputs", []),
                }
            )
        except (OSError, ValueError):
            continue
    import person_profile

    profile = person_profile.read(person)
    data = {
        "profile_metadata": profile,
        "schema": 1,
        "person": person,
        "created": datetime.datetime.now().astimezone().isoformat(),
        "kind": "calculated_research_overview",
        "sources": [
            {
                k: r.get(k)
                for k in (
                    "id",
                    "provider",
                    "original_name",
                    "sha256",
                    "build",
                    "versions",
                    "declared_version",
                    "measurement",
                    "qc_color",
                    "called_points",
                    "scope_summary",
                )
            }
            for r in sources
        ],
        "provider_documents": [
            {
                k: r.get(k)
                for k in (
                    "id",
                    "name",
                    "provider",
                    "kind",
                    "report_date",
                    "status",
                    "sha256",
                )
            }
            for r in documents
            if r["kind"] != "analysis_output"
        ],
        "manual_profile_facts": profile_documents.facts(person),
        "executed_results": jobs,
        "ancestry_sources": visual,
        "ancestry_synthesis": weighted_ancestry(visual),
        "health_policy": "Use genotype consensus at each assayed locus and compatible validated trait models. Chip data can contribute measured loci; WGS is not a requirement for every trait. Never average diagnoses, drug advice or risk estimates from incomparable reports. Imported text, self-report, imputed values and local calculations remain separate evidence. Missing measurements are not negative findings.",
        "weight_policy": "Marker-specific callability and documented model quality only for explicitly comparable models. No weight from filename, file size, provider prestige or download date.",
    }
    path = out / "calculated-research.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        (
            "Scope",
            "Combined source-cited research overview. Pending model metadata or missing tool runs remain pending; no invented health or ancestry findings.",
        ),
        ("Profile context / self-reported metadata", profile),
        ("Source datasets", data["sources"]),
        ("Provider reports retained separately", data["provider_documents"]),
        ("Local executed results", jobs),
        ("Comparable ancestry calculations", data["ancestry_synthesis"]),
        ("Manual profile facts", data["manual_profile_facts"]),
        ("Health interpretation", data["health_policy"]),
        ("Weighting", data["weight_policy"]),
    ]
    body = "".join(
        "<h2>"
        + html.escape(title)
        + "</h2><pre>"
        + html.escape(
            value
            if isinstance(value, str)
            else json.dumps(value, ensure_ascii=False, indent=2)
        )
        + "</pre>"
        for title, value in sections
    )
    (out / "calculated-research.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Combined research overview</title><style>body{font:16px Segoe UI;max-width:1050px;margin:40px auto}pre{white-space:pre-wrap}h2{color:#087f82}</style><button onclick="window.print()">Print / Export PDF</button><h1>Combined research overview</h1>'
        + body,
        encoding="utf-8",
    )
    try:
        pdf = out / "calculated-research.pdf"
        render_pdf(data, pdf)
        profile_documents.index_file(
            person,
            pdf,
            "DNA Workbench / source synthesis",
            kind="calculated_research",
            copy=False,
            log=log,
        )
        data["pdf_status"] = "generated and indexed"
    except ImportError:
        data["pdf_status"] = "PDF module missing; HTML/JSON remain available"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def render_pdf(data, pdf):
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4

    teal = colors.HexColor("#087f82")
    ink = colors.HexColor("#183047")
    muted = colors.HexColor("#526575")
    pale = colors.HexColor("#eef5f5")
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ResearchBody",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=ink,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "ResearchSmall",
            parent=styles["ResearchBody"],
            fontSize=8,
            leading=10,
            textColor=muted,
        )
    )
    styles.add(
        ParagraphStyle(
            "ResearchHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=teal,
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        )
    )

    def para(value, style="ResearchBody"):
        return Paragraph(html.escape(str(value)).replace("\n", "<br/>"), styles[style])

    def table(headers, rows, widths):
        cells = [[para(x, "ResearchSmall") for x in headers]] + [
            [para(x, "ResearchSmall") for x in row] for row in rows
        ]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), pale),
                    ("TEXTCOLOR", (0, 0), (-1, 0), teal),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.7, teal),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#d8e2e7")),
                ]
            )
        )
        return t

    profile = data["profile_metadata"]
    story = [
        para("LOCAL RESEARCH / SOURCE-CITED OVERVIEW", "ResearchSmall"),
        Paragraph("Combined research overview", styles["Title"]),
        para(profile.get("name", data["person"])),
        para(
            "Generated " + data["created"][:10] + " | Profile " + data["person"],
            "ResearchSmall",
        ),
        Spacer(1, 9),
    ]
    story.append(
        para(
            "This overview combines source records, completed local tests and explicitly comparable calculations. It does not establish a diagnosis or a perfect genome. Missing or incompatible evidence stays visible."
        )
    )
    counts = [
        len({x["sha256"] for x in data["sources"]}),
        len(data["sources"]),
        len(data["provider_documents"]),
        len(data["executed_results"]),
    ]
    story.append(
        table(
            [
                "Distinct contents",
                "Source records",
                "Saved reports",
                "Completed local tests",
            ],
            [[str(n) for n in counts]],
            [124, 124, 124, 123],
        )
    )
    if data["sources"]:
        story.append(para("Source datasets", "ResearchHeading"))
        rows = []
        for i, r in enumerate(data["sources"], 1):
            measurement = {
                "Measured": "Measured (declared)",
                "Unknown": "Unknown",
                "Imputed": "Imputed",
                "Phased": "Phased",
            }.get(r.get("measurement"), r.get("measurement", "Unknown"))
            build = r.get("build") or "Unknown"
            build = "Unknown" if build == "Unknown" else build
            name = (
                r["original_name"]
                + "\n"
                + build
                + " / "
                + (r.get("declared_version") or "Version not declared")
            )
            quality = (
                "Not assessed"
                if not r.get("called_points")
                else str(r["called_points"]) + " called positions"
            )
            rows.append(
                [
                    str(i) + " / " + r["provider"],
                    name,
                    measurement + "\n" + quality + "\nSHA " + r["sha256"][:16],
                ]
            )
        story.append(
            table(
                ["Source", "File / reference / version", "Evidence / content identity"],
                rows,
                [103, 225, 167],
            )
        )
        story.append(Spacer(1, 6))
        story.append(
            para(
                "Identical content hashes do not count as additional measurements. Complete IDs, SHA-256 values and provenance are preserved in calculated-research.json.",
                "ResearchSmall",
            )
        )
    story.append(para("Ancestry calculations", "ResearchHeading"))
    ancestry = data["ancestry_synthesis"]
    if not ancestry["calculated"]:
        story.append(
            para(
                "No compatible combined ancestry calculation is available for this profile yet."
            )
        )
    for group in ancestry["calculated"]:
        story.append(
            para(
                "Exploratory technical weighting - matching population definitions and calibration only.",
                "ResearchSmall",
            )
        )
        story.append(
            table(
                ["Population identifier", "Weighted result"],
                [
                    [r["population_id"], f"{r['percent']:.2f}%"]
                    for r in group["regions"]
                ],
                [330, 165],
            )
        )
        story.append(
            para(
                "Source roots: "
                + str(group["independent_source_roots"])
                + " | Model: "
                + ", ".join(group["comparability"]),
                "ResearchSmall",
            )
        )
    for item in ancestry["kept_separate"]:
        story.append(
            para(
                str(item.get("provider") or "Model comparison") + ": " + item["reason"]
            )
        )
    story.append(para("Health and local results", "ResearchHeading"))
    if data["executed_results"]:
        story.append(
            table(
                ["Local tool", "Completed", "Result reference"],
                [
                    [r["task"], (r.get("finished") or "")[:10], r["job"]]
                    for r in data["executed_results"]
                ],
                [125, 70, 300],
            )
        )
    else:
        story.append(
            para("No completed local research tests are included in this snapshot.")
        )
    story.append(
        para(
            "Consumer chip data can contribute measured positions without WGS. Genotype consensus, provider statements, self-report and model predictions remain separate evidence. Diagnoses, drug advice and incompatible risks are never averaged into a medical finding. Missing data is not a negative result.",
            "ResearchSmall",
        )
    )
    story.append(para("Provider reports and profile facts", "ResearchHeading"))
    if data["provider_documents"]:
        story.append(
            table(
                ["Provider", "Report", "Date / state"],
                [
                    [
                        r["provider"],
                        r["name"],
                        (r.get("report_date") or "Date unknown") + " / " + r["status"],
                    ]
                    for r in data["provider_documents"]
                ],
                [115, 240, 140],
            )
        )
    else:
        story.append(para("No provider reports are included in this snapshot."))
    for fact in data["manual_profile_facts"]:
        story.append(para("Self-report: " + fact["question"] + " - " + fact["value"]))
    story.append(
        KeepTogether(
            [
                para("Weighting and traceability", "ResearchHeading"),
                para(data["weight_policy"], "ResearchSmall"),
                para(
                    "Full machine-readable sources, profile metadata and run references are provided in the JSON alongside this PDF. Source reports remain available independently.",
                    "ResearchSmall",
                ),
            ]
        )
    )

    def footer(canvas, doc):
        w, h = A4
        canvas.setStrokeColor(teal)
        canvas.line(42, 37, w - 42, 37)
        canvas.setFillColor(muted)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(42, 25, "DNA Workbench / OD - local research overview")
        canvas.drawRightString(w - 42, 25, "Page " + str(doc.page))

    SimpleDocTemplate(
        str(pdf),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=49,
        title="Combined research overview",
        author="OD / DNA Workbench",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
