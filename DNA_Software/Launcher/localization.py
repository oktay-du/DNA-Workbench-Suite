"""English source messages with optional external locale dictionaries."""

from pathlib import Path
import functools, json


@functools.lru_cache(maxsize=4)
def dictionary(language):
    if language != "de":
        return {}
    return json.loads(
        Path(__file__)
        .with_name("Locales")
        .joinpath("de.json")
        .read_text(encoding="utf-8")
    )


def text(english, language="en"):
    return dictionary(language).get(english, english)


def matches_intent(value, key, english_pattern):
    import re

    aliases = json.loads(
        Path(__file__)
        .with_name("Locales")
        .joinpath("de-intents.json")
        .read_text(encoding="utf-8")
    )
    return (
        re.search(english_pattern + "|" + aliases.get(key, "(?!)"), value, re.I)
        is not None
    )
