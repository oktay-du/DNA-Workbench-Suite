"""Permanent UUIDs independent of editable labels and legacy folder IDs."""

import uuid, datetime, contextlib, os
import family
import security_paths


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


MAINTENANCE = set()


@contextlib.contextmanager
def exclusive_restore(person):
    person = security_paths.identifier(person)
    # Outside folders that will be swapped, but checked by every suite writer.
    import source_store

    path = (
        source_store.ROOT
        / "DNA_Software/UserData/Launcher/ProfileLocks"
        / (person + ".lock")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        f.write(str(os.getpid()))
    MAINTENANCE.add(person)
    try:
        yield
    finally:
        MAINTENANCE.discard(person)
        path.unlink(missing_ok=True)


def assert_writable(person):
    person = security_paths.identifier(person)
    import source_store

    path = (
        source_store.ROOT
        / "DNA_Software/UserData/Launcher/ProfileLocks"
        / (person + ".lock")
    )
    if person not in MAINTENANCE and path.exists():
        raise ValueError(
            "A profile restore is in progress. Wait for completion before editing or starting analyses."
        )


def schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS profile_identities(person TEXT PRIMARY KEY,uuid TEXT NOT NULL UNIQUE,created TEXT NOT NULL,updated TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1)"
    )


def ensure(person):
    person = security_paths.identifier(person)
    with family.connect() as db:
        if not db.execute("SELECT 1 FROM people WHERE id=?", (person,)).fetchone():
            raise ValueError("Unknown profile")
        schema(db)
        stamp = now()
        value = (
            str(uuid.UUID(person[2:]))
            if person.startswith("P_") and len(person) == 34
            else str(uuid.uuid4())
        )
        db.execute(
            "INSERT OR IGNORE INTO profile_identities VALUES(?,?,?,?,1)",
            (person, value, stamp, stamp),
        )
        return dict(
            db.execute(
                "SELECT * FROM profile_identities WHERE person=?", (person,)
            ).fetchone()
        )


def touch(person):
    ensure(person)
    with family.connect() as db:
        db.execute(
            "UPDATE profile_identities SET updated=?,revision=revision+1 WHERE person=?",
            (now(), person),
        )


def lookup(value):
    value = str(uuid.UUID(value))
    # Lazy migration assigns stable IDs to existing legacy profiles without renaming folders.
    with family.connect() as db:
        schema(db)
        people = [r[0] for r in db.execute("SELECT id FROM people")]
    for p in people:
        ensure(p)
    with family.connect() as db:
        row = db.execute(
            "SELECT person FROM profile_identities WHERE uuid=?", (value,)
        ).fetchone()
    return row[0] if row else None


def assign(person, value, created=None, updated=None, revision=1):
    value = str(uuid.UUID(value))
    ensure(person)
    with family.connect() as db:
        previous = db.execute(
            "SELECT person FROM profile_identities WHERE uuid=?", (value,)
        ).fetchone()
        if previous and previous[0] != person:
            raise ValueError("UUID already belongs to another profile")
        db.execute(
            "UPDATE profile_identities SET uuid=?,created=?,updated=?,revision=? WHERE person=?",
            (value, created or now(), updated or now(), int(revision), person),
        )
