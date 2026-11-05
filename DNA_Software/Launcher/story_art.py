"""Profile-owned story artwork slots; external generation remains a manual user action."""

from pathlib import Path
import base64, contextlib, hashlib, html, io, json, re, uuid, functools
import source_store, family, profile_identity, profile_documents

APP = Path(__file__).parent
SUBJECTS = {
    "farmer": ("Ackerbau", "Farming", "lifeways-v1", 0, 0, 3, 2),
    "hunter-gatherer": (
        "Jagd & Sammeln",
        "Hunting & gathering",
        "lifeways-v1",
        1,
        0,
        3,
        2,
    ),
    "fisher": ("Fischfang", "Fishing", "lifeways-v1", 2, 0, 3, 2),
    "desert": ("Desert regions", "Desert environments", "lifeways-v1", 0, 1, 3, 2),
    "herder": ("Hirten & Herden", "Herders & flocks", "lifeways-v1", 1, 1, 3, 2),
    "migration": ("Wanderungen", "Migrations", "lifeways-v1", 2, 1, 3, 2),
    "neanderthal": ("Neanderthal", "Neanderthals", "archaic-humans-v1", 0, 0, 3, 1),
    "denisovan": ("Denisova-Menschen", "Denisovans", "archaic-humans-v1", 1, 0, 3, 1),
    "sapiens": (
        "Early Homo sapiens",
        "Early Homo sapiens",
        "archaic-humans-v1",
        2,
        0,
        3,
        1,
    ),
}
CONTINENTS = [
    "Africa",
    "Europe",
    "Asia",
    "North America",
    "South America",
    "Oceania",
    "Antarctica",
]


def schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS artwork_slots(slot TEXT PRIMARY KEY,document TEXT,prompt TEXT,updated TEXT)"
    )


def assets():
    return json.loads((APP / "heritage-art.json").read_text(encoding="utf-8"))["images"]


def asset(id):
    row = next((r for r in assets() if r["id"] == id), None)
    if not row:
        raise ValueError("Unknown bundled artwork")
    path = APP / row["file"]
    if (
        not path.resolve().is_relative_to((APP / "heritage-art").resolve())
        or not path.is_file()
    ):
        raise ValueError("Artwork missing")
    return path


@functools.lru_cache(maxsize=2000)
def region_key(name):
    import heritage, unicodedata

    value = unicodedata.normalize("NFKD", clean(name)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    for p in heritage.catalog()["places"]:
        if value in {
            "".join(
                c
                for c in unicodedata.normalize("NFKD", a).casefold()
                if not unicodedata.combining(c)
            )
            for a in [p["name"], *p.get("aliases", [])]
        }:
            value = p["id"]
            break
    return "region-" + hashlib.sha256(value.encode()).hexdigest()[:20]


def clean(name):
    return name.split(" · synthetic illustration")[0].strip()


def bundled(slot, title=""):
    if slot in SUBJECTS:
        s = SUBJECTS[slot]
        return {"asset": s[2], "x": s[3], "y": s[4], "cols": s[5], "rows": s[6]}
    if slot == "cover" or slot.startswith("continent-"):
        return {"asset": "world-atlas-v1", "x": 0, "y": 0, "cols": 1, "rows": 1}
    if clean(title).casefold() in ("peru", "perú"):
        return {"asset": "peru-painted-v1", "x": 0, "y": 0, "cols": 1, "rows": 1}
    if slot.startswith("region-"):
        return {
            "asset": "world-atlas-v1",
            "x": 0,
            "y": 0,
            "cols": 1,
            "rows": 1,
            "placeholder": True,
        }
    return None


def prompt(title, kind):
    subject = clean(title)
    if kind == "country":
        scene = (
            "a coherent cultural and landscape panorama of "
            + subject
            + ", geographically appropriate landmarks, architecture, plants, textile and food details; do not reduce a diverse region to one stereotype"
        )
    elif kind == "lineage":
        scene = (
            "a poetic illustration of "
            + subject
            + ", an unlabelled branching tree and broad landscapes; do not invent specific migration routes, dates, haplogroup labels or ancestors"
        )
    elif kind == "continent":
        scene = (
            "a broad panorama celebrating the varied environments and cultural landscapes of "
            + subject
            + ", multiple regions, no stereotypical single culture"
        )
    else:
        scene = (
            "a carefully researched educational interpretation of "
            + subject
            + ", landscape-led and with people at small scale; show uncertainty for incomplete archaeological evidence"
        )
    if "denisov" in subject.casefold():
        scene += "; do not invent detailed faces because appearance is uncertain"
    return (
        "Create an original premium full-bleed watercolor and gouache heritage storybook illustration. Landscape 3:2. Depict "
        + scene
        + ". Elegant parchment, jade, teal, ochre and muted crimson pigments, subtle paper grain. A single continuous painted scene filling all edges; no inset photo or icon sheet. Leave quiet light space at upper left for software-added headings. No letters, numbers, labels, watermark, logo or invented scientific chart. Cultural/historical context only, not a genetic portrait or a claim about an individual. No personal names, raw genotypes or health results are supplied."
    )


def slots(person):
    import heritage_story

    profile_identity.ensure(person)
    row = heritage_story.ancestry(person)
    specs = [
        ("cover", "World & family story", "cover"),
        ("maternal", "Maternal lineage", "lineage"),
        ("paternal", "Paternal lineage", "lineage"),
    ]
    specs += [(id, s[1], "historical") for id, s in SUBJECTS.items()]
    specs += [
        ("continent-" + name.casefold().replace(" ", "-"), name, "continent")
        for name in CONTINENTS
    ]
    region_specs = [
        (region_key(r["name"]), r["name"], "country")
        for r in (row or {}).get("data", {}).get("regions", [])
    ]
    required = {"cover", *[r[0] for r in region_specs]}
    specs += region_specs
    import heritage

    known = {r[0] for r in specs}
    for place in heritage.catalog()["places"]:
        key = region_key(place["name"])
        if key not in known:
            specs.append((key, place["name"], "country"))
            known.add(key)
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        saved = {
            r[0]: dict(document=r[1], prompt=r[2], updated=r[3])
            for r in db.execute("SELECT * FROM artwork_slots")
        }
        db.commit()
    docs = {r["id"]: r for r in profile_documents.listing(person)}
    out = []
    for id, title, kind in specs:
        r = {
            "id": id,
            "title": title,
            "kind": kind,
            "prompt": saved.get(id, {}).get("prompt") or prompt(title, kind),
            "default": bundled(id, title),
            "status": "bundled"
            if bundled(id, title) and not bundled(id, title).get("placeholder")
            else "missing",
            "required": id in required,
        }
        doc = docs.get(saved.get(id, {}).get("document"))
        r["custom"] = None
        if doc and doc["status"] == "artwork_not_genetic_evidence" and doc["available"]:
            p = Path(doc["path"])
            base = source_store.ROOT / "DNA_Archiv/Reports" / person
            if (
                p.resolve().is_relative_to(base.resolve())
                or p.resolve().is_relative_to(
                    source_store.profile_dir(person).resolve()
                )
            ) and not p.is_symlink():
                r.update(
                    status="custom",
                    custom={
                        "document": doc["id"],
                        "path": str(p),
                        "sha256": doc["sha256"],
                        "bytes": doc["bytes"],
                        "updated": doc["updated"],
                    },
                )
        out.append(r)
    return {
        "person": person,
        "image_reader": __import__("importlib.util").util.find_spec("PIL") is not None,
        "slots": out,
        "ready": sum(s["status"] != "missing" for s in out),
        "total": len(out),
        "missing_required": sum(
            s["required"] and s["status"] == "missing" for s in out
        ),
        "notice": "Artwork readiness is separate from DNA-analysis readiness. Bundled lifeway/archaic images are educational context, not a personal inference.",
    }


def selected(person, slot):
    return next((r for r in slots(person)["slots"] if r["id"] == slot), None)


def save_prompt(person, slot, text):
    profile_identity.assert_writable(person)
    profile_identity.ensure(person)
    if (
        not selected(person, slot)
        or not isinstance(text, str)
        or not text.strip()
        or len(text) > 8000
    ):
        raise ValueError("Choose a known slot and a prompt up to 8000 characters")
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        db.execute(
            "INSERT INTO artwork_slots VALUES(?,?,?,?) ON CONFLICT(slot) DO UPDATE SET prompt=excluded.prompt,updated=excluded.updated",
            (slot, None, text, profile_identity.now()),
        )
        db.commit()
    profile_identity.touch(person)
    return {"saved": True, "slot": slot}


def upload(
    person,
    slot,
    path="",
    data_url="",
    prompt_text="",
    provider="External image generation",
):
    profile_identity.ensure(person)
    if any(
        j.get("task") == "storybook" and j.get("status") in ("Running", "Queued")
        for j in __import__("suite_api").jobs(person)
    ):
        raise ValueError(
            "Wait for the running story export before changing its artwork"
        )
    with profile_identity.exclusive_restore(person):
        return _upload(person, slot, path, data_url, prompt_text, provider)


def _upload(
    person,
    slot,
    path="",
    data_url="",
    prompt_text="",
    provider="External image generation",
):
    profile_identity.assert_writable(person)
    record = selected(person, slot)
    if not record:
        raise ValueError("Unknown image slot for this profile")
    if bool(path) == bool(data_url):
        raise ValueError("Choose one local image or one image upload")
    if path:
        p = __import__("security_paths").input_file(path)
        if not p.is_file() or p.is_symlink() or p.stat().st_size > 12 * 1024**2:
            raise ValueError("Use PNG/JPEG up to 12 MiB")
        raw = p.read_bytes()
    else:
        if not re.fullmatch(
            r"data:image/(?:png|jpeg);base64,[A-Za-z0-9+/=\r\n]+", data_url
        ):
            raise ValueError("Use PNG/JPEG")
        raw = base64.b64decode(data_url.split(",", 1)[1], validate=True)
        if len(raw) > 5 * 1024**2:
            raise ValueError(
                "Browser uploads support up to 5 MiB; use a local path for larger images"
            )
    from PIL import Image

    with Image.open(io.BytesIO(raw)) as image:
        if (
            image.format not in ("PNG", "JPEG")
            or image.width * image.height > 50_000_000
            or min(image.size) < 128
        ):
            raise ValueError(
                "PNG/JPEG, at least 128 pixels per side and at most 50 megapixels"
            )
        suffix = ".png" if image.format == "PNG" else ".jpg"
        dimensions = list(image.size)
        image.verify()
    digest = hashlib.sha256(raw).hexdigest()
    document = None
    with family.connect() as db:
        profile_documents.schema(db)
        prior = db.execute(
            "SELECT id,path FROM profile_documents WHERE person=? AND sha256=? AND kind='design_art' AND status!='deleted'",
            (person, digest),
        ).fetchone()
    if (
        prior
        and Path(prior["path"]).is_file()
        and profile_documents.digest(prior["path"]) == digest
    ):
        document = prior["id"]
    if not document:
        document = uuid.uuid4().hex
        folder = source_store.profile_dir(person) / "Artwork"
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / (slot + "-" + document[:12] + suffix)
        dest.write_bytes(raw)
        stat = dest.stat()
        notes = json.dumps(
            {
                "use": "Story illustration, not genetic evidence",
                "slot": slot,
                "dimensions": dimensions,
                "prompt": prompt_text or record["prompt"],
                "provider": provider,
                "original_preserved": True,
            },
            ensure_ascii=False,
        )
        with family.connect() as db:
            profile_documents.schema(db)
            db.execute(
                "INSERT INTO profile_documents VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    document,
                    person,
                    record["title"] + suffix,
                    str(dest),
                    digest,
                    provider[:150],
                    "",
                    "design_art",
                    "artwork_not_genetic_evidence",
                    0,
                    stat.st_size,
                    stat.st_mtime_ns,
                    profile_identity.now(),
                    notes,
                ),
            )
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        db.execute(
            "INSERT OR REPLACE INTO artwork_slots VALUES(?,?,?,?)",
            (slot, document, prompt_text or record["prompt"], profile_identity.now()),
        )
        db.commit()
    profile_identity.touch(person)
    return {
        "slot": slot,
        "document": document,
        "sha256": digest,
        "status": "custom",
        "original_preserved": True,
        "next_missing": next(
            (
                s["id"]
                for s in slots(person)["slots"]
                if s["status"] == "missing" and s["required"]
            ),
            None,
        )
        or next(
            (s["id"] for s in slots(person)["slots"] if s["status"] == "missing"), None
        ),
    }


def image_data(record):
    if record.get("custom"):
        p = Path(record["custom"]["path"])
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return "data:" + mime + ";base64," + base64.b64encode(p.read_bytes()).decode()
    if record.get("default"):
        return (
            "data:image/png;base64,"
            + base64.b64encode(asset(record["default"]["asset"]).read_bytes()).decode()
        )
    return ""


def fingerprint(person):
    art = {r["id"]: r["sha256"] for r in assets()}
    return [
        {
            "slot": r["id"],
            "sha256": r["custom"]["sha256"]
            if r["custom"]
            else art.get((r["default"] or {}).get("asset")),
            "status": r["status"],
        }
        for r in slots(person)["slots"]
        if r["required"] or r["kind"] != "country" or r["custom"]
    ]


def prompts_export(person):
    import execution_journal

    pack = {
        "prompts": [
            {
                "slot": r["id"],
                "title": r["title"],
                "prompt": r["prompt"],
                "status": r["status"],
            }
            for r in slots(person)["slots"]
        ],
        "note": "Prompts exclude personal names, raw genotype and health values. Copy to your chosen provider manually; this app does not upload them.",
    }
    return execution_journal.execute(
        "artwork.prompt-pack",
        {
            "person": person,
            "pack_version": hashlib.sha256(
                json.dumps(pack, sort_keys=True).encode()
            ).hexdigest(),
        },
        lambda args: pack,
    )


def atlas():
    import heritage

    geo = json.loads((APP / "atlas-countries.json").read_text(encoding="utf-8"))
    countries = []
    for place in heritage.catalog()["places"]:
        country = next(
            (r for r in geo["countries"] if str(r["code"]).lower() == place["id"]), None
        )
        countries.append(
            {
                "id": place["id"],
                "name": place["name"],
                "aliases": place.get("aliases", []),
                "continent": country["continent"] if country else "Not classified",
                "outline_available": bool(country),
                "curated": place.get("curated", False),
            }
        )
    return {
        "countries": countries,
        "continents": CONTINENTS,
        "subjects": [
            {"id": k, "name": v[1], "name_de": v[0]} for k, v in SUBJECTS.items()
        ],
        "assets": [
            {k: r[k] for k in ("id", "sha256", "interpretation")} for r in assets()
        ],
        "source": geo["source"],
        "notice": "Broad shared atlas artwork is available for all places; a dedicated painted country scene currently exists for Peru. Other country scenes can be added with the image assistant.",
    }


def map_svg(code="", continent=""):
    geo = json.loads((APP / "atlas-countries.json").read_text(encoding="utf-8"))
    out = []

    def rings(coords):
        if coords and isinstance(coords[0][0], (int, float)):
            yield coords
        elif coords:
            for c in coords:
                yield from rings(c)

    for row in geo["countries"]:
        active = (
            (code and str(row["code"]).lower() == code.lower())
            or continent
            and row["continent"] == continent
        )
        for ring in rings(row["geometry"]["coordinates"]):
            if len(ring) < 3:
                continue
            coords = [((p[0] + 180) * 2, (90 - p[1]) * 2) for p in ring]
            d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in coords) + "Z"
            out.append(
                '<path fill="'
                + ("#b76b31" if active else "#a5b9a9")
                + '" d="'
                + d
                + '"/>'
            )
    return (
        '<svg viewBox="0 0 720 360" aria-label="Natural Earth country map">'
        + "".join(out)
        + "</svg>"
    )


def css():
    return """
.sheet.painted-scene{max-width:none;margin:32px 0;min-height:100svh;aspect-ratio:3/2;padding:0;border-radius:0;background-image:var(--scene-image);background-size:var(--scene-size,cover);background-position:var(--scene-position,center);background-repeat:no-repeat;isolation:isolate;break-inside:avoid;print-color-adjust:exact;-webkit-print-color-adjust:exact;animation:none}
.sheet.painted-scene:before{display:none}.painted-title{position:relative;z-index:1;display:inline-block;max-width:min(540px,60%);padding:35px 48px 24px;background:linear-gradient(130deg,#fcf3dfed,#fcf3df80,transparent);border-radius:0 0 55px 0}.painted-title h2{font-size:clamp(30px,4vw,60px);margin:15px 0;overflow-wrap:anywhere}.painted-title .number{font-size:clamp(45px,7vw,90px);color:#634826}.painted-note{position:absolute;bottom:0;inset-inline:0;padding:35px 5% 20px;background:linear-gradient(transparent,#162b2aee);color:#fff7e7;font:15px/1.65 system-ui}.painted-note small{display:block}.painted-note a{color:#f4db9a}.scene-map{position:absolute;right:4%;top:5%;width:30%;background:#f5eedfc9;border-radius:20px;padding:12px}.scene-map svg{width:100%}.context-warning{background:#f4ead7;padding:12px 20px;color:#3f514b}.life-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.life-grid article{min-width:0}.life-grid .life-image{aspect-ratio:1;background-size:300% 200%;background-repeat:no-repeat;border-radius:16px}.life-grid h3{font-size:20px}.atlas-note{font:12px system-ui;opacity:.85}
@media(max-width:650px){.painted-title{padding:25px;max-width:90%}.sheet.painted-scene{min-height:95svh;aspect-ratio:auto}.scene-map{top:auto;bottom:180px;right:4%;width:40%}.life-grid{grid-template-columns:1fr 1fr}.painted-note{font-size:12px}}
@media print{.sheet.painted-scene{min-height:0;height:180mm;aspect-ratio:3/2;margin:0;break-after:page;background-size:var(--scene-size,cover)!important;background-position:var(--scene-position,center)!important}.painted-title{max-width:55%;padding:12mm}.painted-title h2{font-size:30px}.painted-note{font-size:10px;padding:12mm 8mm 5mm}.life-grid{grid-template-columns:repeat(3,1fr)}}
"""


def full_scene(record, title, value, caption, variable, map_markup="", id=""):
    e = lambda x: html.escape(str(x), quote=True)
    default = None if record.get("custom") else record.get("default")
    cols = (default or {}).get("cols", 1)
    rows = (default or {}).get("rows", 1)
    x = (default or {}).get("x", 0)
    y = (default or {}).get("y", 0)
    position = f"{100 * x / (cols - 1) if cols > 1 else 50}% {100 * y / (rows - 1) if rows > 1 else 50}%"
    size = "cover" if cols == rows == 1 else f"{cols * 100}% {rows * 100}%"
    artlabel = (
        "User-supplied artwork"
        if record.get("custom")
        else "Shared atlas placeholder; dedicated region picture pending"
        if record["status"] == "missing"
        else "AI-generated cultural / historical illustration"
    )
    # A shared atlas is suitable for the cover, never a substitute country scene.
    scene = (
        "linear-gradient(135deg,#f4ead6,#c6d6cb)"
        if record["status"] == "missing"
        else "var(" + variable + ")"
    )
    pending = (
        '<p class="context-warning">Country artwork not available. Add an image manually.</p>'
        if record["status"] == "missing"
        else ""
    )
    # Large embedded paintings exceed some browsers' custom-property value limit.
    # A regular image element keeps offline HTML and print exports self-contained.
    backdrop = ""
    if record["status"] != "missing":
        backdrop = (
            '<img alt="" aria-hidden="true" src="'
            + e(image_data(record))
            + '" style="position:absolute;max-width:none;z-index:-1;left:'
            + str(-100 * x)
            + "%;top:"
            + str(-100 * y)
            + "%;width:"
            + str(100 * cols)
            + "%;height:"
            + str(100 * rows)
            + '%;object-fit:cover">'
        )
        scene = "none"
    return (
        '<section class="sheet painted-scene"'
        + (' id="' + e(id) + '"' if id else "")
        + ' style="overflow:hidden;--scene-image:'
        + scene
        + ";--scene-size:"
        + size
        + ";--scene-position:"
        + position
        + '">'
        + backdrop
        + '<div class="painted-title"><span class="kicker">HERITAGE STORY</span><h2>'
        + e(title)
        + "</h2>"
        + ('<div class="number">' + e(value) + "</div>" if value else "")
        + pending
        + "</div>"
        + ('<div class="scene-map">' + map_markup + "</div>" if map_markup else "")
        + '<div class="painted-note">'
        + e(caption)
        + "<small>"
        + e(artlabel)
        + " · Not a genetic portrait. Scene combines places artistically.</small></div></section>"
    )
