"""Read historical in-suite paths at the current location, without rewriting evidence files."""

import json as _json
from portable_paths import rebase

JSONDecodeError = _json.JSONDecodeError
JSONEncoder = _json.JSONEncoder
JSONDecoder = _json.JSONDecoder
dump = _json.dump
dumps = _json.dumps


def _upgrade(value):
    if isinstance(value, dict):
        layout = __import__("layout_migration").layout()
        choices = layout.get("choice_values", {})
        return {
            k: (
                layout.get("status_values", {}) if k == "status" else choices.get(k, {})
            ).get(v, v)
            if isinstance(v, str)
            else _upgrade(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_upgrade(v) for v in value]
    return value


def loads(value, *args, **kwargs):
    return rebase(_upgrade(_json.loads(value, *args, **kwargs)))


def load(stream, *args, **kwargs):
    return rebase(_upgrade(_json.load(stream, *args, **kwargs)))


def __getattr__(name):
    return getattr(_json, name)
