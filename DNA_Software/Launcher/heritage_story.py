"""Offline archival story template from explicit profile evidence; no external scripts."""

from pathlib import Path
import base64, html, json

E = lambda x: html.escape(str(x), quote=True)


def ancestry(person):
    import visual_store

    return next(
        (
            r
            for r in visual_store.listing()
            if r["person"] == person and r.get("data", {}).get("regions")
        ),
        None,
    )


def groups(row, threshold=2):
    regions = sorted(
        (row or {}).get("data", {}).get("regions", []), key=lambda x: -x["percent"]
    )
    return [x for x in regions if x["percent"] >= threshold], [
        x for x in regions if x["percent"] < threshold
    ]


def world_svg(points=()):
    world = json.loads(
        Path(__file__).with_name("world-land.json").read_text(encoding="utf-8")
    )
    paths = []

    def point(lon, lat):
        return (lon + 180) * 2, (90 - lat) * 2

    def rings(coords):
        if not coords:
            return
        if isinstance(coords[0][0], (int, float)):
            yield coords
        else:
            for c in coords:
                yield from rings(c)

    for ring in rings(
        world.get("rings")
        or [
            f.get("geometry", {}).get("coordinates", [])
            for f in world.get("features", [])
        ]
    ):
        if len(ring) < 3:
            continue
        pts = [point(*p[:2]) for p in ring]
        paths.append(
            '<path d="M' + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + 'Z"/>'
        )
    for p in points:
        if p.get("lat") is None or p.get("lon") is None:
            continue
        x, y = point(p["lon"], p["lat"])
        paths.append(
            f'<circle cx="{x}" cy="{y}" r="5" class="pin"><title>{E(p["name"])}</title></circle>'
        )
    return (
        '<svg class="world" viewBox="0 0 720 360" role="img" aria-label="World map; evidence-backed regional points">'
        + "".join(paths)
        + "</svg>"
    )


def place(region, language):
    import heritage

    name = __import__("story_art").clean(region["name"]).casefold()
    entry = next(
        (
            x
            for x in heritage.catalog()["places"]
            if name
            in {
                x["name"].casefold(),
                x["id"].casefold(),
                *[a.casefold() for a in x.get("aliases", [])],
            }
        ),
        None,
    )
    if not entry:
        return {
            "name": region["name"],
            "text": (
                "Regional cultural context is still in progress."
                if language == "en"
                else "Regionaler Kulturkontext noch in Bearbeitung."
            ),
            "image": "",
            "sources": [],
            "flag": "",
        }
    # Curated catalog prose remains in its source language; never silently label it translated.
    text = " ".join(entry.get(k, "") for k in ("landscape", "architecture"))
    image = ""
    photo = next(iter(entry.get("photos", [])), None)
    if photo:
        path = heritage.photo_path(photo["id"])
        image = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()
    code = entry["id"].upper()
    flag = (
        "".join(chr(127397 + ord(c)) for c in code)
        if len(code) == 2 and code.isalpha()
        else ""
    )
    return {
        "name": entry["name"],
        "text": text,
        "image": image,
        "photo": photo,
        "sources": entry.get("sources", []),
        "flag": flag,
    }


def create(person, profile, data, out, language="en"):
    import workflows, story_art

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tr = lambda english, fallback=None: __import__("localization").text(
        fallback if fallback is not None else english, language
    )
    missing = tr("Still in progress")
    row = ancestry(person)
    large, small = groups(row)
    sections = []
    art_rows = {r["id"]: r for r in story_art.slots(person)["slots"]}
    image_vars = {}
    art_hashes = {r["id"]: r["sha256"] for r in story_art.assets()}

    def image_var(record):
        identity = (
            record["custom"]["sha256"]
            if record.get("custom")
            else art_hashes.get((record.get("default") or {}).get("asset"))
        )
        if not identity:
            return None
        key = "--art-" + identity
        if key not in image_vars:
            image_vars[key] = story_art.image_data(record)
        return key

    def section(kicker, title, body, id=""):
        sections.append(
            '<section class="sheet"'
            + (' id="' + E(id) + '"' if id else "")
            + '><span class="kicker">'
            + E(kicker)
            + "</span><h2>"
            + E(title)
            + "</h2>"
            + body
            + "</section>"
        )

    cover = art_rows.get("cover")
    cover_var = image_var(cover) if cover else None
    if cover_var:
        sections.append(
            story_art.full_scene(
                cover,
                profile["name"],
                "",
                tr(
                    "A personal research storybook. The painted map is artistic; actual model values and sources follow on later pages."
                ),
                cover_var,
                id="cover",
            )
        )
    else:
        section(
            "DNA WORKBENCH",
            profile["name"],
            '<p class="lead">'
            + E(tr("Two lineages. Many stories."))
            + "</p>"
            + world_svg((row or {}).get("data", {}).get("regions", []))
            + "<p>"
            + E(
                tr(
                    "A personal research archive — evidenced results, visible sources and open questions."
                )
            )
            + "</p>",
            "cover",
        )
    for kind, de, en in [
        ("maternal", "The Mother Line", "The maternal lineage"),
        ("paternal", "The Father Line", "The paternal lineage"),
    ]:
        value = data.get(kind, {})
        body = (
            '<div class="number">'
            + E(value.get("haplogroup", missing))
            + "</div><p>"
            + E(tr("A haplogroup describes one lineage, not your full ancestry."))
            + "</p>"
        )
        if value.get("route_available"):
            body += (
                world_svg()
                + "<p>"
                + E(
                    tr(
                        "Broad regional model in the selected provider report: East Africa → Southwest Asia → Europe. Not a verified journey of individual ancestors; dates and exact routes depend on the model."
                    )
                )
                + "</p>"
            )
        else:
            body += "<p>" + E(tr("Reviewed route model: ") + missing) + "</p>"
        if value:
            body += (
                "<small>"
                + E(Path(value["path"]).name)
                + " · "
                + E(value["sha256"])
                + "</small>"
            )
        record = art_rows.get(kind)
        variable = image_var(record) if record else None
        if variable:
            sections.append(
                story_art.full_scene(
                    record,
                    tr(de, en),
                    value.get("haplogroup", missing),
                    tr(
                        "Symbolic lineage illustration; not an independent reconstruction of an actual route."
                    ),
                    variable,
                )
            )
        section("mtDNA" if kind == "maternal" else "Y-DNA", tr(de, en), body, kind)
    if row:
        d = row["data"]
        section(
            "ANCESTRY",
            tr("Your ancestry estimates"),
            world_svg(d["regions"])
            + "<p>"
            + E(d["provider"] + " · " + d["model"] + " · " + d["version"])
            + "</p><p>"
            + E(
                tr(
                    "Model estimates, not nationalities. A region can span several countries."
                )
            )
            + "</p>",
            "ancestry",
        )
        atlas_countries = story_art.atlas()["countries"]
        related = set()
        for region in d["regions"]:
            country = next(
                (
                    c
                    for c in atlas_countries
                    if story_art.region_key(c["name"])
                    == story_art.region_key(region["name"])
                ),
                None,
            )
            if country:
                related.add(country["continent"])
        for continent in story_art.CONTINENTS:
            record = art_rows.get("continent-" + continent.casefold().replace(" ", "-"))
            if record and (continent in related or record.get("custom")):
                variable = image_var(record)
                if variable:
                    sections.append(
                        story_art.full_scene(
                            record,
                            continent,
                            "",
                            tr(
                                "Continental cultural and landscape context. Modern boundaries are not genetic boundaries. No additional DNA percentage."
                            ),
                            variable,
                            story_art.map_svg(continent=continent),
                        )
                    )
        for r in large:
            context = place(r, language)
            record = art_rows.get(story_art.region_key(r["name"]))
            variable = image_var(record) if record else None
            if variable:
                country = next(
                    (
                        p
                        for p in story_art.atlas()["countries"]
                        if story_art.region_key(p["name"]) == record["id"]
                    ),
                    None,
                )
                map_markup = story_art.map_svg(country["id"]) if country else ""
                caption = (
                    context["text"]
                    + " "
                    + tr(
                        "Cultural context, not an additional personal genetic finding."
                    )
                )
                sections.append(
                    story_art.full_scene(
                        record,
                        context["flag"] + " " + r["name"],
                        str(r["percent"]) + "%",
                        caption,
                        variable,
                        map_markup,
                        id="scene-" + record["id"],
                    )
                )
                continue
            body = '<div class="number">' + E(r["percent"]) + "%</div>"
            if context["image"]:
                body += (
                    '<img class="culture" alt="'
                    + E(context["name"])
                    + '" src="'
                    + context["image"]
                    + '">'
                )
            body += "<p>" + E(context["text"]) + "</p>"
            if context.get("photo"):
                body += (
                    "<small>"
                    + E(json.dumps(context["photo"], ensure_ascii=False))
                    + "</small>"
                )
            body += (
                '<p class="sources">'
                + E(json.dumps(context["sources"], ensure_ascii=False))
                + "</p>"
            )
            section(
                context["flag"] + " · " + tr("Culture & landscape"), r["name"], body
            )
        if small:
            section(
                "SMALL COMPONENTS",
                tr("Additional ancestry components"),
                "<ul>"
                + "".join(
                    "<li>" + E(r["name"]) + " <b>" + E(r["percent"]) + "%</b></li>"
                    for r in small
                )
                + "</ul><p>"
                + E(
                    tr(
                        "Grouped: individual estimates below 2%. Small components are particularly model-dependent."
                    )
                )
                + "</p>",
            )
    else:
        section(
            "ANCESTRY",
            tr("Ancestry estimates"),
            "<p>" + E(missing) + "</p>",
            "ancestry",
        )
    archaic = data.get("archaic")
    body = "<p>" + E(missing) + "</p>"
    if archaic:
        body = (
            '<div class="number">'
            + E(archaic.get("variant_copies", missing))
            + "</div><p>"
            + E(
                tr(
                    "Provider-reported Neanderthal variant copies — not a genome percentage."
                )
            )
            + "</p>"
        )
        if archaic.get("dna_fraction_statement"):
            body += "<p>" + E(archaic["dna_fraction_statement"]) + "</p>"
        if archaic.get("customer_percentile") is not None:
            body += (
                "<p>"
                + E(
                    str(archaic["customer_percentile"])
                    + tr("% customer comparison, not genome fraction.")
                )
                + "</p>"
            )
    body += "<p>" + E(tr("Denisovan and other groups: ") + missing) + "</p>"
    section("ARCHAIC", tr("Human encounters"), body, "archaic")
    archaic_image = art_rows.get("neanderthal")
    archaic_var = image_var(archaic_image) if archaic_image else None
    if archaic_var:
        sections.append(
            story_art.full_scene(
                archaic_image,
                tr("Neanderthals"),
                str(archaic.get("variant_copies")) + " " + tr("variant copies")
                if archaic
                else missing,
                tr(
                    "Provider marker counts and genome percentages are different measurements. Artistic reconstruction, not a genetic portrait."
                ),
                archaic_var,
            )
        )
    inherit = workflows.inheritance_latest(person)
    if inherit and inherit.get("current"):
        body = (
            "<p>"
            + E(inherit["summary"])
            + "</p><p>"
            + E(
                tr(
                    "Green = maternal allele · Gold = paternal allele. Only unambiguous quality-filtered trio positions; not continuous segments."
                )
            )
            + "</p>"
        )
        for chrom in map(str, range(1, 23)):
            loci = [r for r in inherit["loci"] if r["chrom"] == chrom]
            if loci:
                body += (
                    '<p class="chrom">'
                    + E(chrom)
                    + ' <span class="maternal">'
                    + str(len(loci))
                    + '</span><span class="paternal">'
                    + str(len(loci))
                    + "</span></p>"
                )
    else:
        body = (
            "<p>"
            + E(missing)
            + "</p><p>"
            + E(
                tr(
                    "Run the family workflow with suitable child, mother and father data."
                )
            )
            + "</p>"
        )
    section("INHERITANCE", tr("Maternal and paternal evidence"), body, "inheritance")
    section(
        "HISTORICAL CONTEXT",
        tr("Ways of life through time"),
        '<p class="context-warning">'
        + E(
            tr(
                "The following scenes form an educational image library. They do not establish the lifeways of your ancestors. A haplogroup alone cannot do that."
            )
        )
        + "</p>",
    )
    for subject in (
        "farmer",
        "hunter-gatherer",
        "fisher",
        "desert",
        "herder",
        "migration",
        "neanderthal",
        "denisovan",
        "sapiens",
    ):
        record = art_rows.get(subject)
        variable = image_var(record) if record else None
        if variable:
            de, en, *_ = story_art.SUBJECTS[subject]
            caption = tr(
                "Artistic historical context. Personal association is not established. Appearance, dates and regional details are reconstructions and can be uncertain."
            )
            sections.append(
                story_art.full_scene(
                    record, tr(de, en), "", caption, variable, id="context-" + subject
                )
            )
    section(
        "TODAY",
        tr("Today"),
        "<h3>"
        + E(profile.get("residence") or missing)
        + "</h3><p>"
        + E(tr("Personal profile entry, not genetic ancestry evidence."))
        + "</p>",
    )
    provenance = {
        "person": person,
        "haplogroup_reports": data,
        "ancestry_result": row,
        "inheritance": {k: v for k, v in inherit.items() if k != "loci"}
        if inherit
        else None,
        "threshold_percent": 2,
        "template": "painted-archive-v2",
        "artwork": story_art.fingerprint(person),
        "limitations": "Reported/modelled results, not new genetic inference. Unknowns remain unknown.",
        "design_inspiration": "https://github.com/8bsite/genealogy-website-template; original implementation, no copied code or external runtime",
    }
    (out / "heritage-story-evidence.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    section(
        "SOURCES",
        tr("Sources & snapshot"),
        "<pre>" + E(json.dumps(provenance, ensure_ascii=False, indent=2)) + "</pre>",
        "sources",
    )
    css = """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#202927;color:#283f3d;font:17px/1.75 Georgia,serif}.bar{position:sticky;top:0;padding:14px 5%;background:#202927ee;color:#f8edda;z-index:2;display:flex;gap:12px;flex-wrap:wrap}.bar a,.bar button{color:inherit;background:transparent;border:1px solid #aeb8aa;border-radius:25px;padding:8px 17px;text-decoration:none;cursor:pointer}.sheet{max-width:1050px;min-height:80vh;margin:35px auto;padding:70px clamp(25px,7vw,90px);background:#f5eedf;border-radius:8px;box-shadow:0 20px 55px #0005;position:relative;overflow:hidden}.sheet:before{content:"";height:7px;position:absolute;inset:0 0 auto;background:repeating-linear-gradient(120deg,#b08748 0 15px,#517d72 15px 30px,#f5eedf 30px 42px)}.kicker{letter-spacing:.2em;font:12px system-ui;color:#53766c}h2{font-weight:400;font-size:clamp(30px,5vw,57px);line-height:1.15;margin:25px 0}h3{font-size:32px}.lead{font-size:25px}.number{font:80px/1.3 Georgia;color:#a47734}.world{width:100%;background:#e5e6d9;border-radius:16px}.world path{fill:#b7c7ba;stroke:#f1eadb;stroke-width:.5}.world .pin{fill:#bc713a;stroke:#fff;stroke-width:2}.culture{width:100%;height:320px;object-fit:cover;border-radius:10px}.sources,small,pre{font:11px/1.7 system-ui;overflow-wrap:anywhere}pre{white-space:pre-wrap;max-height:700px;overflow:auto}.maternal,.paternal{display:inline-block;width:35%;padding:3px 12px;background:#a5d7c4}.paternal{background:#ddba79}.chrom{margin:5px 0}body[data-style=studio]{font-family:system-ui;background:#112634}body[data-style=studio] .sheet{background:#eef5f6;border-radius:28px}body[data-style=studio] .sheet:before{background:linear-gradient(90deg,#20aaa0,#f3c26e)}@media(prefers-reduced-motion:no-preference){.sheet{animation:reveal both linear;animation-timeline:view();animation-range:entry 0% entry 25%}@keyframes reveal{from{opacity:.4;transform:translateY(35px)}to{opacity:1;transform:none}}}@media print{body{background:white}.bar{display:none}.sheet{margin:0;box-shadow:none;break-after:page;min-height:0;max-width:none;padding:20mm;animation:none!important;opacity:1!important;transform:none!important}pre{max-height:none}a{color:inherit}.culture{height:65mm}}"""
    css += (
        story_art.css()
        + ":root{"
        + "".join(k + ':url("' + v + '");' for k, v in image_vars.items())
        + "}"
    )
    bar = (
        '<nav class="bar"><button onclick="window.print()">'
        + E(tr("Print / export PDF"))
        + "</button><button onclick=\"document.body.dataset.style=document.body.dataset.style==='studio'?'archive':'studio'\">Archive / Studio</button>"
        + "".join(
            '<a href="#' + x + '">' + E(x.title()) + "</a>"
            for x in [
                "cover",
                "maternal",
                "paternal",
                "ancestry",
                "archaic",
                "inheritance",
            ]
        )
        + "</nav>"
    )
    document = (
        '<!doctype html><html lang="'
        + language
        + '"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'
        + E(profile["name"])
        + " · Heritage story</title><style>"
        + css
        + '</style><body data-style="archive">'
        + bar
        + "".join(sections)
        + "</body></html>"
    )
    (out / "Heritage_Story.html").write_text(document, encoding="utf-8")
    return {
        "ancestry": row,
        "major": large,
        "minor": small,
        "template": "painted-archive-v2",
        "artwork": story_art.fingerprint(person),
    }
