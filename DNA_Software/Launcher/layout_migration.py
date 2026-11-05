import security_sql

"""Read legacy metadata through a bounded mapping; original evidence stays intact."""
from pathlib import Path
import functools, json, sqlite3, contextlib


@functools.lru_cache(maxsize=1)
def layout():
    return json.loads(
        Path(__file__).with_name("legacy-layout.json").read_text(encoding="utf-8")
    )


def relative(value):
    if not isinstance(value, str):
        return value
    mapping = layout()["directories"] | layout()["files"]
    separator = "\\" if "\\" in value else "/"
    parts = value.replace("\\", "/").split("/")
    result = []
    original = False
    for part in parts:
        result.append(part if original else mapping.get(part, part))
        if part in ("Imports", "Launcher_Importe"):
            original = True
    return separator.join(result)


def path(value, root):
    if not isinstance(value, str):
        return value
    normalized = value.replace("\\", "/")
    prefix = str(root).replace("\\", "/").rstrip("/") + "/"
    if normalized.lower().startswith(prefix.lower()):
        return relative(value)
    if normalized.split("/")[0] in (
        "Profiles",
        "DNA_Software",
        "Projects",
        *layout()["directories"],
    ):
        return relative(value)
    return value


_updated = set()


def database(connection, root):
    """Upgrade only stored app paths, backing up the database before its first edit."""
    info = connection.execute("PRAGMA database_list").fetchone()
    file = info[2]
    if not file or file in _updated:
        return
    changes = []
    for (table,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ):
        try:
            security_sql.identifier(table)
        except ValueError:
            continue
        columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(" + security_sql.identifier(table) + ")"
            )
            if "TEXT" in row[2].upper()
        ]
        for column in columns:
            try:
                security_sql.identifier(column)
            except ValueError:
                continue
            for rowid, value in connection.execute(
                "SELECT rowid,"
                + security_sql.identifier(column)
                + " FROM "
                + security_sql.identifier(table)
                + " WHERE typeof("
                + security_sql.identifier(column)
                + ")='text'"
            ):
                updated = path(value, root)
                if updated != value:
                    changes.append((table, column, rowid, updated))
    if changes:
        backup = Path(file).with_name(Path(file).name + ".before-english-migration.bak")
        if not backup.exists():
            with contextlib.closing(sqlite3.connect(backup)) as target:
                connection.backup(target)
        for table, column, rowid, value in changes:
            connection.execute(
                "UPDATE "
                + security_sql.identifier(table)
                + " SET "
                + security_sql.identifier(column)
                + "=? WHERE rowid=?",
                (value, rowid),
            )
        connection.commit()
    _updated.add(file)
