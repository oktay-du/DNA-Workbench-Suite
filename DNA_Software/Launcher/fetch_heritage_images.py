import network_io

"""Download openly licensed Commons thumbnails with individual attribution."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
import concurrent.futures, datetime, hashlib, json, urllib.request, sys

APP = Path(__file__).parent
OUT = APP / "heritage-assets"
QUERIES = [
    (
        "de-castle",
        "de",
        "Neuschwanstein Castle 2024-02",
        "Neuschwanstein Castle · Bavaria",
    ),
    (
        "de-city",
        "de",
        "Heidelberg castle panorama",
        "Heidelberg · Example of southwestern German urban landscape",
    ),
    ("at-vienna", "at", "Vienna Schonbrunn palace panorama", "Schönbrunn · Vienna"),
    (
        "cz-prague",
        "cz",
        "Prague Charles Bridge panorama",
        "Prague · Charles Bridge and Old Town",
    ),
    (
        "pl-krakow",
        "pl",
        "Krakow main square panorama",
        "Krakow · Historic market square",
    ),
    ("pt-porto", "pt", "Porto Ribeira panorama", "Porto · Douro and Ribeira"),
    ("tr-ani", "tr", "Ani cathedral ruins", "Ani · Historical site near Kars"),
    (
        "ir-shiraz",
        "ir",
        "Nasir al Mulk mosque interior",
        "Shiraz · Nasir al-Mulk Mosque",
    ),
    (
        "ge-ushguli",
        "ge",
        "Ushguli Svaneti towers panorama",
        "Uzhguli · Defence towers in Svanetia",
    ),
    ("am-geghard", "am", "Geghard monastery Armenia", "Geghard · Monastery complex"),
    ("it-florence", "it", "Florence skyline panorama", "Florence · Historic cityscape"),
    ("gr-athens", "gr", "Athens Acropolis panorama", "Athens · Acropolis"),
]


class Plain(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = Plain()
    parser.feed(str(value))
    return " ".join("".join(parser.parts).split())


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DNAWorkbench-open-culture-assets/1.0 (local educational app; source metadata retained)"
        },
    )
    with network_io.open_https(req, timeout=40) as response:
        data = response.read(5_000_001)
        if len(data) > 5_000_000:
            raise ValueError("Image / metadata too big.")
        return data


def one(spec):
    id, place, query, caption = spec
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query + " filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 6,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1000,
    }
    if id in ("ge-ushguli", "tr-ani"):
        params = {
            k: v
            for k, v in params.items()
            if k not in ("generator", "gsrsearch", "gsrnamespace", "gsrlimit")
        }
        params["titles"] = (
            "File:Ushguli - panoramio.jpg"
            if id == "ge-ushguli"
            else "File:Cathedral of Ani.jpg"
        )
    url = "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
    raw = fetch(url)
    pages = json.loads(raw).get("query", {}).get("pages", {})
    pages = sorted(pages.values(), key=lambda p: p.get("index", 99))
    candidates = []
    for page in pages:
        info = page.get("imageinfo", [{}])[0]
        meta = info.get("extmetadata", {})
        value = lambda k: plain(meta.get(k, {}).get("value", ""))
        license = value("LicenseShortName")
        value("LicenseUrl")
        if not (
            license.startswith(("CC BY", "CC0")) or license in ("Public domain", "PD")
        ):
            continue
        image_url = info.get("thumburl", "").split("?")[0]
        if not image_url or urlparse(image_url).hostname not in (
            "upload.wikimedia.org",
            "thumb.wikimedia.org",
        ):
            continue
        if not image_url.lower().endswith((".jpg", ".jpeg")):
            continue
        candidates.append((license.startswith("CC0"), page, info, meta, image_url))
    if not candidates:
        raise ValueError("No suitable openly licensed JPEG found: " + query)
    _, page, info, meta, image_url = sorted(candidates, key=lambda x: not x[0])[0]
    data = fetch(image_url)
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("JPEG-Signatur fehlt.")
    OUT.mkdir(exist_ok=True)
    filename = id + ".jpg"
    (OUT / filename).write_bytes(data)
    value = lambda k: plain(meta.get(k, {}).get("value", ""))
    return {
        "id": id,
        "place": place,
        "file": filename,
        "caption": caption,
        "title": page["title"].removeprefix("File:"),
        "author": value("Artist") or value("Attribution") or "Siehe Bildquelle",
        "attribution": value("Attribution"),
        "license": value("LicenseShortName"),
        "license_url": value("LicenseUrl")
        or "https://creativecommons.org/publicdomain/zero/1.0/",
        "source": info["descriptionurl"],
        "download_url": image_url,
        "sha256": hashlib.sha256(data).hexdigest(),
        "downloaded": datetime.datetime.now().astimezone().isoformat(),
        "modification": "Scaled-down preview provided by Wikimedia; image file unchanged locally.",
    }


if __name__ == "__main__":
    previous = (
        json.loads((APP / "heritage-images.json").read_text(encoding="utf-8"))
        if (APP / "heritage-images.json").exists()
        else {"images": []}
    )
    requested = sys.argv[1:]
    selected = [s for s in QUERIES if not requested or s[0] in requested]
    selected = [
        (
            id,
            place,
            "Ani cathedral exterior photograph -Bashinjaghian -painting"
            if id == "tr-ani"
            else "Ushguli village panorama"
            if id == "ge-ushguli"
            else query,
            caption,
        )
        for id, place, query, caption in selected
    ]
    images = {p["id"]: p for p in previous["images"]}
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        tasks = {pool.submit(one, s): s for s in selected}
        for future in concurrent.futures.as_completed(tasks):
            try:
                image = future.result()
                images[image["id"]] = image
                print(image["id"], image["title"], image["license"], flush=True)
            except Exception as e:
                errors.append(str(e))
                print("FEHLER", str(e), flush=True)
    for image in images.values():
        image["modification"] = (
            "Reduced Wikimedia preview; file unchanged locally. The interface displays a responsive image section."
        )
    if "de-city" in images:
        images["de-city"]["caption"] = "Heidelberg Castle · Friedrichsbau facade detail"
    (APP / "heritage-images.json").write_text(
        json.dumps(
            {
                "version": "2026-11-03.1",
                "images": sorted(images.values(), key=lambda x: x["id"]),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
