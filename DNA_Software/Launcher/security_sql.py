"""Identifiers are never values: validate and quote the small managed SQLite schema."""

import re


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]{0,79}", value
    ):
        raise ValueError("Invalid SQLite schema identifier")
    return '"' + value + '"'
