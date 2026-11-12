"""Read historical in-suite paths at the current location, without rewriting evidence files."""

import copy, threading
import json as _json
from portable_paths import rebase

JSONDecodeError = _json.JSONDecodeError
JSONEncoder = _json.JSONEncoder
JSONDecoder = _json.JSONDecoder
dump = _json.dump
dumps = _json.dumps
_CACHE = {}
_LOCK = threading.Lock()
_CACHE_LIMIT = 2000
_CACHE_CHARS = 200_000


def clear_cache():
    """Drop parsed copies after the install location changes."""
    with _LOCK:
        _CACHE.clear()


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
    cacheable = (
        not args
        and not kwargs
        and isinstance(value, str)
        and len(value) <= _CACHE_CHARS
    )
    if cacheable:
        with _LOCK:
            cached = _CACHE.get(value)
        if cached is not None:
            return copy.deepcopy(cached)
    parsed = rebase(_upgrade(_json.loads(value, *args, **kwargs)))
    if not cacheable:
        return parsed
    with _LOCK:
        if len(_CACHE) >= _CACHE_LIMIT:
            _CACHE.clear()
        _CACHE[value] = parsed
    return copy.deepcopy(parsed)


def load(stream, *args, **kwargs):
    return rebase(_upgrade(_json.load(stream, *args, **kwargs)))


def __getattr__(name):
    return getattr(_json, name)
