"""English source messages with optional external locale dictionaries."""

from pathlib import Path
import functools, json, re

LOCALES = Path(__file__).with_name("Locales")


@functools.cache
def languages():
    rows = json.loads((LOCALES / "languages.json").read_text(encoding="utf-8"))
    result = {}
    for row in rows:
        code, flag = row["id"], row["flag"]
        if (
            code in result
            or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z][a-z]{3})?", code)
            or not re.fullmatch(r"[a-z]{2}", flag)
            or row.get("dir", "ltr") not in ("ltr", "rtl")
        ):
            raise ValueError("Invalid interface language catalog")
        result[code] = row
    return result


@functools.cache
def ui_assets():
    assets = {"/Locales/languages.json": LOCALES / "languages.json"}
    for code, row in languages().items():
        if code != "en":
            assets[f"/Locales/{code}.json"] = LOCALES / f"{code}.json"
        flag = row["flag"]
        assets[f"/Locales/flags/{flag}.svg"] = LOCALES / "flags" / f"{flag}.svg"
    return assets


@functools.lru_cache(maxsize=12)
def dictionary(language):
    if language == "en" or language not in languages():
        return {}
    path = ui_assets()[f"/Locales/{language}.json"]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def text(english, language="en"):
    return dictionary(language).get(english, english)


def matches_intent(value, key, english_pattern):
    aliases = json.loads((LOCALES / "de-intents.json").read_text(encoding="utf-8"))
    return (
        re.search(english_pattern + "|" + aliases.get(key, "(?!)"), value, re.I)
        is not None
    )
