"""Local, source-labelled creative exports. No genotype or route is invented."""

from pathlib import Path
import base64, gzip, hashlib, html, math, re, struct, sys, unicodedata, zipfile
import portable_json as json

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "DNA_Software/Windows/PythonPackages"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def report(path, person, kind):
    from pypdf import PdfReader

    p = Path(path).resolve()
    archive = (ROOT / "DNA_Archiv/01_Originaldownloads").resolve()
    if p.is_relative_to(archive) and p.relative_to(archive).parts[0] != person:
        raise ValueError("Report belongs to another profile archive")
    if p.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Report limit: 50 MB")
    pdf = PdfReader(p)
    text = "\n".join(x.extract_text() or "" for x in pdf.pages[:30])
    out = {
        "path": str(p),
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "provider": "23andMe",
        "status": "reported, not independently verified",
    }
    if kind in ("maternal", "paternal"):
        m = re.search(r"your " + kind + r" haplogroup is\s+([A-Za-z0-9-]+)", text, re.I)
        if not m:
            raise ValueError(
                "No supported personal haplogroup statement found in " + p.name
            )
        out["haplogroup"] = m[1].rstrip(".")
        out["route_available"] = (
            kind == "maternal"
            and out["haplogroup"] == "H"
            or kind == "paternal"
            and out["haplogroup"] == "J-M67"
        )
        # Only a broad schematic when the source itself discusses these regions.
        if out["route_available"] and not all(
            term in text.lower() for term in ("africa", "asia")
        ):
            out["route_available"] = False
    else:
        m = re.search(
            r"found\s+([\d,]+)\s+variants in your DNA", text, re.I
        ) or re.search(r"Your Neanderthal Variant Total\s+(\d+)", text, re.I)
        if not m:
            raise ValueError("No supported Neanderthal variant-copy count found")
        out["variant_copies"] = int(m[1].replace(",", ""))
        pct = re.search(r"more Neanderthal DNA than\s+(\d+)%", text, re.I)
        if pct:
            out["customer_percentile"] = int(pct[1])
        if re.search(r"less than\s*~?2\s*percent", text, re.I):
            out["dna_fraction_statement"] = "< ~2% (provider estimate)"
    return out


def evidence(person, inputs):
    out = {}
    for kind in ("maternal", "paternal", "archaic"):
        if inputs.get(kind + "_report"):
            out[kind] = report(inputs[kind + "_report"], person, kind)
    return out


def storybook(person, inputs, out, log=print):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, Color
    import person_profile

    p = person_profile.read(person)
    data = evidence(person, inputs)
    en = inputs.get("language") == "English"
    tr = lambda english, fallback=None: __import__("localization").text(
        fallback if fallback is not None else english, "en" if en else "de"
    )
    import heritage_story

    story = heritage_story.create(person, p, data, out, "en" if en else "de")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out / "DNA_Storybook.pdf"), pagesize=(720, 720))
    c.setTitle(p["name"] + " · DNA Storybook")
    c.setAuthor("DNA Workbench · local research export")

    def line(text, y, size=15, color="#d7e6eb"):
        c.setFillColor(HexColor(color))
        c.setFont("Helvetica", size)
        c.drawString(55, y, text)

    def wrapped(text, y, width=89):
        import textwrap

        for value in textwrap.wrap(text, width):
            line(value, y, 12)
            y -= 20
        return y

    def page(kicker, title):
        c.setFillColor(HexColor("#102432"))
        c.rect(0, 0, 720, 720, fill=1, stroke=0)
        c.setFillColor(Color(0.05, 0.6, 0.57, alpha=0.18))
        c.circle(640, 670, 220, fill=1, stroke=0)
        line(kicker.upper(), 660, 12, "#62d8c7")
        line(title, 610, 30, "#ffffff")
        line("DNA WORKBENCH  /  " + p["name"], 34, 9, "#8aa9b8")

    def map_routes():
        # A geographic equirectangular canvas, no invented personal coordinates.
        world = json.loads(
            Path(__file__).with_name("world-land.json").read_text(encoding="utf-8")
        )

        def point(lon, lat):
            return 55 + (lon + 180) / 360 * 610, 190 + (lat + 90) / 180 * 300

        def rings(coords):
            if coords and isinstance(coords[0][0], (int, float)):
                yield coords
            else:
                for sub in coords:
                    yield from rings(sub)

        features = world.get("features", []) if isinstance(world, dict) else []
        if world.get("rings"):
            features = [{"geometry": {"coordinates": world["rings"]}}]
        c.setFillColor(HexColor("#29434f"))
        c.setStrokeColor(HexColor("#365461"))
        for f in features:
            for ring in rings(f.get("geometry", {}).get("coordinates", [])):
                if len(ring) < 3:
                    continue
                path = c.beginPath()
                path.moveTo(*point(*ring[0][:2]))
                for xy in ring[1:]:
                    path.lineTo(*point(*xy[:2]))
                path.close()
                c.drawPath(path, fill=1, stroke=0)
        for kind, color, points in [
            ("maternal", "#69dec7", [(38, 4), (44, 15), (48, 28), (28, 39), (15, 49)]),
            ("paternal", "#f0b76d", [(40, 4), (44, 17), (44, 30), (30, 36), (23, 39)]),
        ]:
            if not data.get(kind, {}).get("route_available"):
                continue
            c.setStrokeColor(HexColor(color))
            c.setFillColor(HexColor(color))
            c.setLineWidth(3)
            c.setDash(6, 4)
            for a, b in zip(points, points[1:]):
                c.line(*point(*a), *point(*b))
            for xy in points:
                c.circle(*point(*xy), 4, fill=1, stroke=0)
            c.setDash()

    page(tr("A personal storybook"), tr("Traces through time"))
    line(tr("Two lineages. Many stories."), 555, 21)
    map_routes()
    line(tr("GREEN: maternal lineage    GOLD: paternal lineage"), 175, 10, "#69dec7")
    wrapped(
        tr(
            "Schematic regional models from your provider reports. Lines are not verified journeys of individual ancestors."
        ),
        145,
    )
    c.showPage()
    for kind, de, en_title in [
        ("maternal", "The Mother Line", "The maternal lineage"),
        ("paternal", "The Father Line", "The paternal lineage"),
    ]:
        result = data.get(kind)
        page("mtDNA" if kind == "maternal" else "Y-DNA", tr(de, en_title))
        line(
            result["haplogroup"] if result else tr("Still in progress"),
            525,
            48,
            "#69dec7" if kind == "maternal" else "#f0b76d",
        )
        wrapped(
            tr(
                "A haplogroup describes one lineage. It is neither your entire ancestry nor a nationality."
            ),
            470,
        )
        if result:
            wrapped(
                tr(
                    "Imported from your 23andMe report. Not confirmed by an independent analysis."
                ),
                385,
            )
            if result.get("route_available"):
                wrapped(
                    tr(
                        "Eastern Africa · Southwest Asia · later dispersal into Europe. This sketch broadly illustrates regions discussed in the report; dates and exact paths depend on the model."
                    ),
                    310,
                )
            else:
                wrapped(
                    tr("No reviewed route model is available for this haplogroup yet."),
                    310,
                )
            wrapped(Path(result["path"]).name, 180, 78)
            line("SHA-256 " + result["sha256"][:32] + "...", 100, 9)
        c.showPage()
    page(tr("Archaic traces"), tr("Human encounters"))
    result = data.get("archaic")
    if result:
        line(
            str(result["variant_copies"]) + " " + tr("variant copies"),
            520,
            34,
            "#f0b76d",
        )
        wrapped(
            tr(
                "Neanderthal markers reported by the provider. Variant copies are not a percentage of your genome."
            ),
            465,
        )
        line(
            result.get("dna_fraction_statement", tr("DNA fraction: not established")),
            380,
            22,
        )
        if "customer_percentile" in result:
            wrapped(
                str(result["customer_percentile"])
                + tr(
                    "% is the customer comparison, not your Neanderthal DNA fraction."
                ),
                325,
            )
        wrapped(Path(result["path"]).name, 245)
    else:
        line(tr("Still in progress"), 510, 30)
    wrapped(
        tr(
            "Denisovan and other archaic groups: Still in progress. No value is guessed from ancestry or appearance."
        ),
        170,
    )
    c.showPage()
    import story_art

    artwork = {r["id"]: r for r in story_art.slots(person)["slots"]}

    def painted_pdf(record, title, value, caption):
        if not record or not (record.get("custom") or record.get("default")):
            return False
        default = None if record.get("custom") else record.get("default")
        cols = (default or {}).get("cols", 1)
        rows = (default or {}).get("rows", 1)
        x = (default or {}).get("x", 0)
        y = (default or {}).get("y", 0)
        path = (
            Path(record["custom"]["path"])
            if record.get("custom")
            else story_art.asset(default["asset"])
        )
        w = 1080 if cols == rows == 1 else 720
        h = 720
        c.setPageSize((w, h))
        c.saveState()
        clip = c.beginPath()
        clip.rect(0, 0, w, h)
        c.clipPath(clip, stroke=0, fill=0)
        c.drawImage(
            str(path),
            -w * x,
            h - h * rows + h * y,
            width=w * cols,
            height=h * rows,
            mask="auto",
        )
        c.restoreState()
        c.setFillColor(Color(0.98, 0.95, 0.87, alpha=0.9))
        c.roundRect(30, h - 245, min(465, w * 0.65), 215, 14, stroke=0, fill=1)
        line(title[:52], h - 90, 26, "#233e38")
        if value:
            line(value, h - 170, 50, "#704a27")
        c.setFillColor(Color(0.06, 0.15, 0.14, alpha=0.88))
        c.rect(0, 0, w, 75, fill=1, stroke=0)
        from reportlab.lib.utils import simpleSplit

        for i, text in enumerate(simpleSplit(caption, "Helvetica", 9, w - 100)[:3]):
            line(text, 48 - i * 12, 9, "#fff7e4")
        c.showPage()
        c.setPageSize((720, 720))
        return True

    if artwork.get("cover", {}).get("custom"):
        painted_pdf(
            artwork["cover"],
            p["name"],
            "",
            tr(
                "Personal storybook · Artistic illustration, not a genetic reconstruction."
            ),
        )
    for kind in ("maternal", "paternal"):
        if artwork.get(kind, {}).get("custom"):
            painted_pdf(
                artwork[kind],
                tr("Maternal lineage")
                if kind == "maternal"
                else tr("Paternal lineage"),
                data.get(kind, {}).get("haplogroup", ""),
                tr(
                    "Symbolic illustration. Actual haplogroups and routes require source evidence."
                ),
            )
    for region in story["major"]:
        record = artwork.get(story_art.region_key(region["name"]))
        if painted_pdf(
            record,
            region["name"],
            str(region["percent"]) + "%",
            tr(
                "Imported ancestry estimate · Cultural context, not a genetic portrait."
            ),
        ):
            continue
        page(tr("Ancestry model"), region["name"])
        line(str(region["percent"]) + "%", 515, 60, "#f0b76d")
        wrapped(tr("Imported model estimate. Not proof of nationality."), 420)
        if story["ancestry"]:
            ancestry_data = story["ancestry"]["data"]
            wrapped(
                ancestry_data["provider"]
                + " / "
                + ancestry_data["model"]
                + " / "
                + ancestry_data["version"],
                300,
            )
        c.showPage()
    if story["minor"]:
        page(tr("Additional components"), tr("Small components, together"))
        y = 530
        for region in story["minor"][:18]:
            y = wrapped(region["name"] + ": " + str(region["percent"]) + "%", y, 75) - 8
        wrapped(
            tr(
                "Components below 2%. Small values are particularly model-dependent. All entries remain available in the web view."
            ),
            130,
        )
        c.showPage()
    related = set()
    atlas = story_art.atlas()["countries"]
    for region in (story.get("ancestry") or {}).get("data", {}).get("regions", []):
        country = next(
            (
                r
                for r in atlas
                if story_art.region_key(r["name"])
                == story_art.region_key(region["name"])
            ),
            None,
        )
        if country:
            related.add(country["continent"])
    for continent in story_art.CONTINENTS:
        record = artwork.get("continent-" + continent.casefold().replace(" ", "-"))
        if record and (continent in related or record.get("custom")):
            painted_pdf(
                record,
                continent,
                "",
                tr("Continental cultural context · No additional DNA percentage."),
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
        de, en_title, *_ = story_art.SUBJECTS[subject]
        painted_pdf(
            artwork.get(subject),
            tr(de, en_title),
            "",
            tr(
                "Historical visual library · Personal association not established. Reconstruction carries uncertainty."
            ),
        )
    page(tr("Today"), p["name"])
    line(p.get("residence") or tr("Residence not specified yet"), 515, 24, "#69dec7")
    wrapped(
        tr(
            "This place is a personal profile entry. It is not a genetic result or evidence of your ancestors' journey."
        ),
        450,
    )
    c.showPage()
    page(tr("Sources and limitations"), tr("Keeping the evidence visible"))
    y = 540
    for kind, r in data.items():
        y = wrapped(kind + ": " + Path(r["path"]).name, y, 83) - 20
        y = wrapped("SHA-256: " + r["sha256"], y, 83) - 20
    wrapped(
        tr(
            "Provider reports are imported statements. This book is an artistic research presentation; it does not compute new haplogroups or archaic fractions. Missing results remain unknown."
        ),
        150,
    )
    c.save()
    write_json(
        out / "storybook-evidence.json",
        {
            "person": person,
            "evidence": data,
            "route_model": "broad-regions-from-selected-provider-report-v1",
            "not_independent_validation": True,
        },
    )
    with person_profile.family.connect() as db:
        details = person_profile.read(person)
        details["story_evidence"] = data
        db.execute(
            "INSERT OR REPLACE INTO profile_details VALUES(?,?)",
            (person, json.dumps(details, ensure_ascii=False)),
        )
    log("Storybook PDF and source manifest created.")
    return data


def avatar_pack(person, inputs, out, log=print):
    import person_profile, visual_store

    p = person_profile.read(person)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if not p.get("photo"):
        raise ValueError(
            "Choose a profile photograph first / Select a profile photo first"
        )
    mime, encoded = p["photo"].split(";base64,")
    name = "reference-photo." + ("png" if mime.endswith("png") else "jpg")
    (out / name).write_bytes(base64.b64decode(encoded))
    reports = [x for x in visual_store.listing() if x.get("person") == person]
    selected = []
    for row in reports:
        d = row.get("data", row)
        selected.append(
            {
                k: d[k]
                for k in ("provider", "model", "version", "regions", "traits")
                if k in d
            }
        )
    mode = inputs.get("include_ancestry", "Nein") in ("Ja", "Yes")
    payload = {
        "person": person,
        "name": p["name"],
        "style": "DNA Workbench watercolor portrait v1",
        "reference_photo_sha256": p["photo_sha256"],
        "ancestry_reports": selected if mode else [],
        "instructions": "Preserve the face from the reference photo. Use a consistent elegant watercolor portrait with a subtle teal and gold DNA double helix background. Include only the explicitly selected country/region motifs. Do not infer appearance, nationality or health from ancestry. No text or flags unless explicitly supported by the selected report. The portrait is artistic, not a genetic face reconstruction.",
        "render_status": "Prepared only. Requires an image-generation model; the installed text model cannot render images.",
    }
    write_json(out / "avatar-design.json", payload)
    (out / "prompt.txt").write_text(
        payload["instructions"]
        + "\n\nSelected context:\n"
        + json.dumps(payload["ancestry_reports"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "README.txt").write_text(
        "Local design pack, no external upload performed. Give reference-photo and prompt.txt to your chosen image generator. Import the returned PNG/JPEG using My profile > Choose photo. Original photo and ancestry evidence are not modified.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(
        out / "Avatar_Design_Pack.zip", "w", zipfile.ZIP_DEFLATED
    ) as z:
        for file in (
            out / name,
            out / "avatar-design.json",
            out / "prompt.txt",
            out / "README.txt",
        ):
            z.write(file, file.name)
    log("Photo + prompt + evidence exported; no generated image claimed.")


def read_sequence(path, length=30):
    p = Path(path)
    op = gzip.open if p.name.lower().endswith(".gz") else open
    if not p.name.lower().endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz")):
        raise ValueError(
            "Select FASTQ. Scattered VCF variants cannot form a contiguous personal sequence."
        )
    before = (p.stat().st_size, p.stat().st_mtime_ns)
    with op(p, "rt", encoding="ascii", errors="strict") as f:
        for index in range(10000):
            name = f.readline().strip()
            if not name:
                break
            seq = f.readline().strip().upper()
            plus = f.readline()
            quality = f.readline().strip()
            if (
                not name.startswith("@")
                or not plus.startswith("+")
                or len(seq) != len(quality)
            ):
                raise ValueError("Invalid FASTQ record")
            for start in range(max(0, len(seq) - length + 1)):
                piece = seq[start : start + length]
                q = quality[start : start + length]
                if (
                    len(piece) == length
                    and set(piece) <= set("ACGT")
                    and min(ord(x) - 33 for x in q) >= 30
                ):
                    if before != (p.stat().st_size, p.stat().st_mtime_ns):
                        raise ValueError(
                            "FASTQ changed while reading; wait until the download completes"
                        )
                    return piece, {
                        "path": str(p.resolve()),
                        "bytes": p.stat().st_size,
                        "mtime_ns": p.stat().st_mtime_ns,
                        "read_id": name,
                        "read_number": index + 1,
                        "read_offset_0based": start,
                        "minimum_phred": min(ord(x) - 33 for x in q),
                        "evidence": "single contiguous observed read; not a validated genomic haplotype",
                        "sequence_sha256": hashlib.sha256(piece.encode()).hexdigest(),
                    }
    raise ValueError(
        "No contiguous Q30 A/C/G/T segment found in the first 10,000 reads"
    )


def helix(person, inputs, out, log=print):
    import numpy as np, manifold3d as mf, person_profile

    path = Path(inputs["file"]).resolve()
    archive = (ROOT / "DNA_Archiv/01_Originaldownloads").resolve()
    if path.is_relative_to(archive) and path.relative_to(archive).parts[0] != person:
        raise ValueError("FASTQ belongs to another profile archive")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    seq, origin = read_sequence(inputs["file"])
    p = person_profile.read(person)
    meshes = []

    def add_mesh(solid, color):
        meshes.append((solid, color))

    def cylinder(a, b, r, color):
        v = np.array(b) - np.array(a)
        height = float(np.linalg.norm(v))
        z = v / height
        helper = (
            np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
        )
        x = np.cross(helper, z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        transform = np.column_stack((x, y, z, np.array(a)))
        add_mesh(mf.Manifold.cylinder(height, r, r, 12).transform(transform), color)

    add_mesh(mf.Manifold.cube((120, 40, 7)).translate((-60, -20, 0)), "#25394B")
    colors = {"A": "#54C7A4", "T": "#EFBA55", "C": "#62A9E8", "G": "#D7779D"}
    complement = str.maketrans("ACGT", "TGCA")

    def xyz(i, phase=0):
        angle = i * 2 * math.pi / 10.5 + phase
        return (12 * math.cos(angle), 12 * math.sin(angle), 7 + i * 4)

    for phase in (0, math.pi):
        for i in range(116):
            cylinder(xyz(i / 4, phase), xyz((i + 1) / 4, phase), 1.65, "#D7E3E8")
    for i, base in enumerate(seq):
        a = xyz(i)
        b = xyz(i, math.pi)
        mid = (0, 0, a[2])
        cylinder(a, mid, 1.25, colors[base])
        cylinder(mid, b, 1.25, colors[base.translate(complement)])
    # Raised dotted lettering is actual printable geometry on the stand.
    font = {
        "A": ["01110", "10001", "11111", "10001", "10001"],
        "B": ["11110", "10001", "11110", "10001", "11110"],
        "C": ["01111", "10000", "10000", "10000", "01111"],
        "D": ["11110", "10001", "10001", "10001", "11110"],
        "E": ["11111", "10000", "11110", "10000", "11111"],
        "F": ["11111", "10000", "11110", "10000", "10000"],
        "G": ["01111", "10000", "10111", "10001", "01110"],
        "H": ["10001", "10001", "11111", "10001", "10001"],
        "I": ["111", "010", "010", "010", "111"],
        "J": ["00111", "00010", "00010", "10010", "01100"],
        "K": ["10001", "10010", "11100", "10010", "10001"],
        "L": ["10000", "10000", "10000", "10000", "11111"],
        "M": ["10001", "11011", "10101", "10001", "10001"],
        "N": ["10001", "11001", "10101", "10011", "10001"],
        "O": ["01110", "10001", "10001", "10001", "01110"],
        "P": ["11110", "10001", "11110", "10000", "10000"],
        "Q": ["01110", "10001", "10101", "10010", "01101"],
        "R": ["11110", "10001", "11110", "10010", "10001"],
        "S": ["01111", "10000", "01110", "00001", "11110"],
        "T": ["11111", "00100", "00100", "00100", "00100"],
        "U": ["10001", "10001", "10001", "10001", "01110"],
        "V": ["10001", "10001", "10001", "01010", "00100"],
        "W": ["10001", "10001", "10101", "11011", "10001"],
        "X": ["10001", "01010", "00100", "01010", "10001"],
        "Y": ["10001", "01010", "00100", "00100", "00100"],
        "Z": ["11111", "00010", "00100", "01000", "11111"],
        "0": ["01110", "10011", "10101", "11001", "01110"],
        "1": ["010", "110", "010", "010", "111"],
        "2": ["11110", "00001", "01110", "10000", "11111"],
        "3": ["11110", "00001", "01110", "00001", "11110"],
        "4": ["10010", "10010", "11111", "00010", "00010"],
        "5": ["11111", "10000", "11110", "00001", "11110"],
        "6": ["01111", "10000", "11110", "10001", "01110"],
        "7": ["11111", "00010", "00100", "01000", "01000"],
        "8": ["01110", "10001", "01110", "10001", "01110"],
        "9": ["01110", "10001", "01111", "00001", "11110"],
        "-": ["000", "000", "111", "000", "000"],
        "_": ["000", "000", "000", "000", "111"],
        " ": ["000"] * 5,
        ".": ["0", "0", "0", "0", "1"],
    }
    label = (
        unicodedata.normalize("NFKD", p["name"])
        .encode("ascii", "ignore")
        .decode()
        .upper()[:40]
    )
    sample = re.search(r"\d{8,}", Path(inputs["file"]).name)
    source_id = sample[0] if sample else origin["sequence_sha256"][:14].upper()
    for text, ypos in [(label, -19), (source_id, 15)]:
        width = sum(len(font.get(ch, font["-"])[0]) + 1 for ch in text)
        scale = min(0.66, 112 / max(1, width))
        x = -width * scale / 2
        for ch in text:
            glyph = font.get(ch, font["-"])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        add_mesh(
                            mf.Manifold.cube((scale * 0.85, scale * 0.85, 1)).translate(
                                (x + col * scale, ypos + (4 - row) * scale, 6.8)
                            ),
                            "#FFFFFF",
                        )
            x += (len(glyph[0]) + 1) * scale
    combined = mf.Manifold.batch_boolean([m for m, _ in meshes], mf.OpType.Add)
    if combined.is_empty() or combined.status() != mf.Error.NoError:
        raise ValueError("3D union failed; no printable output accepted")
    mesh = combined.to_mesh()
    vertices = mesh.vert_properties[:, :3]
    triangles = mesh.tri_verts
    with (out / "DNA_Helix.obj").open("w", encoding="ascii") as f:
        f.write("# DNA Workbench fused model; units: millimetres\n")
        for vertex in vertices:
            f.write("v " + " ".join(str(float(x)) for x in vertex) + "\n")
        for tri in triangles:
            f.write("f " + " ".join(str(int(x) + 1) for x in tri) + "\n")
    with (out / "DNA_Helix.stl").open("wb") as f:
        f.write(
            b"DNA Workbench educational base-pair helix, millimetres".ljust(80, b" ")
        )
        f.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            points = vertices[tri]
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            norm = np.linalg.norm(normal)
            normal = normal / norm if norm else normal
            f.write(struct.pack("<12fH", *normal, *points.flatten(), 0))
    # 3MF uses separate colored solid objects. STL is the fused watertight print mesh.
    from xml.etree.ElementTree import Element, SubElement, tostring

    ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    model = Element("model", xmlns=ns, unit="millimeter")
    SubElement(model, "metadata", name="Title").text = p["name"] + " | " + source_id
    resources = SubElement(model, "resources")
    materials = SubElement(resources, "basematerials", id="1")
    palette = list(dict.fromkeys(color for _, color in meshes))
    for color in palette:
        SubElement(materials, "base", name=color, displaycolor=color + "FF")
    build = SubElement(model, "build")
    for i, (solid, color) in enumerate(meshes, 2):
        obj = SubElement(
            resources,
            "object",
            id=str(i),
            type="model",
            pid="1",
            pindex=str(palette.index(color)),
        )
        mm = SubElement(obj, "mesh")
        vv = SubElement(mm, "vertices")
        tt = SubElement(mm, "triangles")
        mesh = solid.to_mesh()
        for x, y, z in mesh.vert_properties[:, :3]:
            SubElement(vv, "vertex", x=str(float(x)), y=str(float(y)), z=str(float(z)))
        for a, b, c in mesh.tri_verts:
            SubElement(tt, "triangle", v1=str(int(a)), v2=str(int(b)), v3=str(int(c)))
        SubElement(build, "item", objectid=str(i))
    with zipfile.ZipFile(out / "DNA_Helix_Colour.3mf", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        )
        z.writestr(
            "3D/3dmodel.model", tostring(model, encoding="utf-8", xml_declaration=True)
        )
    manifest = {
        "person": person,
        "profile_name": p["name"],
        "source_id": source_id,
        "sequence": seq,
        "source": origin,
        "format": "STL fused solid + colored 3MF overlapping components",
        "educational_not_atomic_molecular_geometry": True,
        "dimensions_mm": [120, 40, 124.7],
        "closed_mesh": True,
        "volume_mm3": combined.volume(),
        "triangle_count": len(triangles),
        "printer_specific_fit_tested": False,
    }
    write_json(out / "helix-manifest.json", manifest)
    # A standalone, rotatable viewer with the exact colored model geometry.
    components = []
    for solid, color in meshes:
        m = solid.to_mesh()
        components.append(
            {
                "v": [
                    [round(float(x), 4) for x in row[:3]] for row in m.vert_properties
                ],
                "t": m.tri_verts.tolist(),
                "c": color,
            }
        )
    viewer = """<!doctype html><meta charset="utf-8"><title>DNA Helix · 3D</title><style>body{margin:0;background:#102432;color:#d7e6eb;font:15px Segoe UI}header{padding:22px}canvas{width:100%;height:78vh;touch-action:none}small{color:#7fadb8}</style><header><h1>DNA Helix</h1><p>Drag to rotate · Scroll to zoom · Millimetres · Educational base-pair model</p><small>__LABEL__</small></header><canvas></canvas><script>const parts=__DATA__,c=document.querySelector('canvas'),g=c.getContext('2d');let a=.5,b=-.3,zoom=3.1,down=null;function draw(){c.width=c.clientWidth*devicePixelRatio;c.height=c.clientHeight*devicePixelRatio;const faces=[];for(const p of parts){const vv=p.v.map(v=>{let x=v[0],y=v[1],z=v[2]-60;const xx=x*Math.cos(a)-y*Math.sin(a),yy=x*Math.sin(a)+y*Math.cos(a),zz=z*Math.cos(b)-yy*Math.sin(b),dd=z*Math.sin(b)+yy*Math.cos(b);return[c.width/2+xx*zoom*devicePixelRatio,c.height/2-zz*zoom*devicePixelRatio,dd]});for(const t of p.t)faces.push({v:t.map(i=>vv[i]),c:p.c,d:t.reduce((n,i)=>n+vv[i][2],0)/3})}faces.sort((x,y)=>y.d-x.d);g.clearRect(0,0,c.width,c.height);for(const f of faces){g.fillStyle=f.c;g.beginPath();g.moveTo(f.v[0][0],f.v[0][1]);for(const v of f.v.slice(1))g.lineTo(v[0],v[1]);g.closePath();g.fill()}}c.onpointerdown=e=>{down=[e.clientX,e.clientY];c.setPointerCapture(e.pointerId)};c.onpointerup=()=>down=null;c.onpointermove=e=>{if(down){a+=(e.clientX-down[0])*.01;b+=(e.clientY-down[1])*.01;down=[e.clientX,e.clientY];draw()}};c.onwheel=e=>{e.preventDefault();zoom=Math.max(.5,Math.min(8,zoom-e.deltaY*.003));draw()};window.onresize=draw;draw();</script>"""
    (out / "DNA_Helix_Viewer.html").write_text(
        viewer.replace("__LABEL__", html.escape(p["name"] + " · " + source_id)).replace(
            "__DATA__", json.dumps(components, separators=(",", ":"))
        ),
        encoding="utf-8",
    )
    (out / "README.txt").write_text(
        "STL: fused closed solid, units millimetres. 3MF: colored solid components; enable union of overlapping volumes in your slicer. Supports may be needed. Colors A green, T gold, C blue, G pink; grey represents a schematic backbone. This is an educational base-pair model, not atomic molecular geometry. Sequence is one observed Q30 read segment, not independently confirmed or mapped. Profile and source ID are raised on the stand.\n",
        encoding="utf-8",
    )
    log("Fused STL + colored 3MF + sequence provenance created.")
    return manifest
