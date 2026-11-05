"""Personal metadata is independent of computed DNA evidence and family links."""

import base64, datetime, hashlib, re
import portable_json as json
import family

FIELDS = {
    "name",
    "birth_date",
    "death_date",
    "residence",
    "birth_place",
    "notes",
    "chromosomes",
    "pronunciation",
    "occupation",
}


def read(person):
    with family.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS profile_details(person TEXT PRIMARY KEY,data TEXT NOT NULL)"
        )
        row = db.execute(
            "SELECT label,synthetic FROM people WHERE id=?", (person,)
        ).fetchone()
        if not row:
            raise ValueError("Unknown profile / Unknown profile")
        detail = db.execute(
            "SELECT data FROM profile_details WHERE person=?", (person,)
        ).fetchone()
    data = json.loads(detail[0]) if detail else {}
    data.update(person=person, name=row[0], hypothetical=bool(row[1]))
    import profile_identity

    data["identity"] = profile_identity.ensure(person)
    return data


def save(person, values):
    import profile_identity

    profile_identity.assert_writable(person)
    data = read(person)
    if set(values) - FIELDS:
        raise ValueError("Unknown profile fields")
    for key, value in values.items():
        if not isinstance(value, str) or len(value) > 10000:
            raise ValueError("Invalid profile value")
        value = value.strip()
        if key.endswith("_date") and value:
            datetime.date.fromisoformat(value)
        if key == "name" and not value:
            raise ValueError("Name required / Name erforderlich")
        if key == "chromosomes" and value not in ("", "Unknown", "XX", "XY", "Other"):
            raise ValueError("Invalid chromosome description")
        data[key] = value
    data["updated"] = datetime.datetime.now().astimezone().isoformat()
    with family.connect() as db:
        db.execute("UPDATE people SET label=? WHERE id=?", (data["name"], person))
        db.execute(
            "INSERT OR REPLACE INTO profile_details VALUES(?,?)",
            (person, json.dumps(data, ensure_ascii=False)),
        )
    import profile_identity

    profile_identity.touch(person)
    return data


def photo(person, data_url):
    import profile_identity

    profile_identity.assert_writable(person)
    data = read(person)
    match = re.fullmatch(
        r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=\r\n]+)", data_url
    )
    if not match:
        raise ValueError("Use a PNG or JPEG photo / PNG or JPEG photo")
    raw = base64.b64decode(match[2], validate=True)
    if not 0 < len(raw) <= 3 * 1024 * 1024:
        raise ValueError("Photo limit: 3 MB")
    if not (
        raw.startswith(b"\x89PNG\r\n\x1a\n")
        if match[1] == "png"
        else raw.startswith(b"\xff\xd8\xff")
    ):
        raise ValueError("Invalid image header")
    data["photo"] = data_url
    data["photo_sha256"] = hashlib.sha256(raw).hexdigest()
    with family.connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO profile_details VALUES(?,?)",
            (person, json.dumps(data, ensure_ascii=False)),
        )
    import profile_identity

    profile_identity.touch(person)
    return {"person": person, "photo_sha256": data["photo_sha256"]}
