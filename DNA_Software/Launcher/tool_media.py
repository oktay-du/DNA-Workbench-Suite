import network_io

"""Historical GenoCAT discovery and bounded, local publisher-image cache.

Catalog metadata is never an installation recipe. Images keep source attribution
and are not redistributed in the public source or profile exports.
"""
from pathlib import Path
import base64, hashlib, io, json, threading, urllib.request

APP = Path(__file__).parent
ROOT = APP.parents[1]
CACHE = ROOT / "DNA_Software/UserData/Launcher/ToolMedia"
GUARD = threading.Lock()


def catalog():
    value = json.loads((APP / "genocat-catalog.json").read_text(encoding="utf-8"))
    import plugin_hub
    from visual_tools import CURATED

    curated = {p["id"]: p for p in plugin_hub.listing()["projects"]}
    aliases = {
        "igv": "igvjs",
        "integrative-genomics-viewer": "igvjs",
        "jbrowse": "jbrowse",
    }
    listed = {aliases.get(row["id"], row["id"]) for row in value["tools"]}
    visual_names = {row["id"]: row["name"] for row in CURATED}
    visual_names["seqviz"] = "SeqViz"
    for id, project in curated.items():
        if not project["visual"] or id in listed:
            continue
        value["tools"].append(
            {
                "id": id,
                "name": visual_names.get(id, id),
                "catalog_date": "",
                "metadata": {"browser": project["url"], "license": project["license"]},
                "images": [],
            }
        )
    for row in value["tools"]:
        id = aliases.get(row["id"], row["id"])
        p = curated.get(id)
        row["adapter"] = (
            {
                "id": id,
                "task": p["task"],
                "installable": p["installable"],
                "installed": p.get("installed"),
                "visual": p["visual"],
            }
            if p
            else None
        )

        def display(v):
            vals = v if isinstance(v, list) else [v] if v else []
            return ", ".join(str(x).strip("“”") for x in vals) or "not specified"

        m = row["metadata"]
        row["summary"] = (
            "Formats: "
            + display(m.get("supported_files"))
            + " · Layout: "
            + display(m.get("genome_layout"))
            + " · Access: "
            + display(m.get("access_format"))
        )
    return value


def media_index():
    rows = json.loads((APP / "genocat-catalog.json").read_text(encoding="utf-8"))[
        "tools"
    ]
    out = {
        r["id"]: {
            "images": r["images"],
            "project": r["metadata"].get("browser", ""),
            "name": r["name"],
            "catalog": True,
        }
        for r in rows
    }
    out["igvjs"] = out.get(
        "igv", out.get("integrative-genomics-viewer", {"images": []})
    )
    out["igv"] = out.get("integrative-genomics-viewer", {"images": []})
    extra = APP / "tool-media.json"
    if extra.exists():
        for k, v in json.loads(extra.read_text(encoding="utf-8"))["tools"].items():
            if v["images"] or k not in out:
                out[k] = v
    return out


def picture(id):
    row = media_index().get(id, {"images": []})
    images = row.get("images", [])
    if not images:
        return {
            "available": False,
            "notice": "No verified publisher screenshot is registered. CLI tools may not have a graphical interface.",
            "project": row.get("project", ""),
        }
    image = images[0]
    url = image["url"]
    if not url.startswith("https://raw.githubusercontent.com/"):
        raise ValueError("Unsupported screenshot source.")
    name = hashlib.sha256(url.encode()).hexdigest() + ".png"
    path = CACHE / name
    with GUARD:
        if not path.is_file():
            from PIL import Image

            with network_io.open_https(
                urllib.request.Request(
                    url, headers={"User-Agent": "DNAWorkbench-tool-media/1"}
                ),
                timeout=20,
            ) as response:
                raw = response.read(8 * 1024**2 + 1)
            if len(raw) > 8 * 1024**2:
                raise ValueError("Publisher image exceeds the preview limit.")
            with Image.open(io.BytesIO(raw)) as im:
                if im.width * im.height > 30_000_000 or im.format not in (
                    "PNG",
                    "JPEG",
                    "GIF",
                    "WEBP",
                ):
                    raise ValueError("Unsupported publisher image.")
                im.seek(0)
                im = im.convert("RGB")
                im.thumbnail((1200, 750))
                buf = io.BytesIO()
                im.save(buf, format="PNG")
            CACHE.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(buf.getvalue())
            tmp.replace(path)
    return {
        "available": True,
        "image": "data:image/png;base64,"
        + base64.b64encode(path.read_bytes()).decode(),
        "source": url,
        "publisher_page": image.get("publisher_page", row.get("project", "")),
        "caption": image.get(
            "provenance", "Project-published screenshot or example output."
        ),
        "rights": image.get(
            "redistribution", "Rights remain with the upstream image owner."
        ),
        "catalog_date": "2022-10-06" if row.get("catalog") else None,
    }


def dispatch(action, r):
    if action == "catalog":
        return catalog()
    if action == "index":
        return {
            "tools": [
                {"id": k, "name": v.get("name", k), "has_image": bool(v["images"])}
                for k, v in media_index().items()
            ]
        }
    if action == "picture":
        return picture(r["id"])
    raise ValueError("Unknown tool catalog action.")
