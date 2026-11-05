"""Versioned display inputs; never infer phenotype or ancestry from a name."""

import datetime, hashlib, math, secrets
import portable_json as json
import family

TRAITS = {
    "hair": ["black", "brown", "blond", "red"],
    "eyes": ["brown", "blue", "intermediate"],
    "freckles": ["yes", "no"],
    "earlobes": ["attached", "free"],
    "nose": ["narrow", "medium", "broad"],
}


def validate(r):
    person = str(r.get("person", ""))
    with family.connect() as db:
        if not db.execute("SELECT 1 FROM people WHERE id=?", (person,)).fetchone():
            raise ValueError("Select a person profile.")
    result = {
        "person": person,
        "provider": str(r.get("provider", "")).strip()[:150],
        "model": str(r.get("model", "")).strip()[:200],
        "version": str(r.get("version", "")).strip()[:150],
        "data_date": str(r.get("data_date", ""))[:60],
        "source_note": str(r.get("source_note", ""))[:2000],
        "regions": [],
        "traits": {},
    }
    if not all(result[k] for k in ["provider", "model", "version"]):
        raise ValueError(
            "Specify source, model and version / data status; expressly mark unknown information as unknown."
        )
    regions = r.get("regions", [])
    if not isinstance(regions, list) or len(regions) > 200:
        raise ValueError("Maximal 200 Herkunftsregionen.")
    for item in regions:
        region = {
            "name": str(item["name"]).strip()[:150],
            "percent": float(item["percent"]),
        }
        if (
            not region["name"]
            or not math.isfinite(region["percent"])
            or not 0 <= region["percent"] <= 100
        ):
            raise ValueError("Invalid region name/percentage value.")
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is not None or lon is not None:
            lat = float(lat)
            lon = float(lon)
            if (
                not math.isfinite(lat)
                or not math.isfinite(lon)
                or not -90 <= lat <= 90
                or not -180 <= lon <= 180
            ):
                raise ValueError("Card point outside the world map.")
            region.update(lat=lat, lon=lon)
        if item.get("population_id"):
            region["population_id"] = str(item["population_id"])[:150]
        result["regions"].append(region)
    if sum(i["percent"] for i in result["regions"]) > 100.1:
        raise ValueError(
            "Shares of origin may not exceed 100 % in total; overlapping upper and subgroups import separately."
        )
    traits = r.get("traits", {})
    if not isinstance(traits, dict):
        raise ValueError("Traits must be an object.")
    for name, value in traits.items():
        if name not in TRAITS:
            raise ValueError("Unsupported feature:" + name)
        probs = value.get("probabilities", {})
        if not probs or set(probs) - set(TRAITS[name]):
            raise ValueError("Unbekannte Kategorien bei " + name)
        probs = {k: float(v) for k, v in probs.items()}
        if (
            any(not math.isfinite(v) or v < 0 or v > 1 for v in probs.values())
            or abs(sum(probs.values()) - 1) > 0.001
        ):
            raise ValueError(
                "Wahrscheinlichkeiten bei "
                + name
                + "must be between 0 and 1 and add up to 1."
            )
        evidence = str(value.get("evidence", "")).strip()[:2000]
        if not evidence:
            raise ValueError("Specify model document/result source for each feature.")
        result["traits"][name] = {
            "probabilities": probs,
            "evidence": evidence,
            "status": "imported model estimate; not independently validated",
        }
    if r.get("comparability"):
        keys = (
            "population_scheme",
            "reference_panel",
            "panel_version",
            "calibration",
            "method_version",
        )
        if not isinstance(r["comparability"], dict) or set(r["comparability"]) - set(
            keys
        ):
            raise ValueError("Invalid comparison metadata")
        result["comparability"] = {
            k: str(v)[:250] for k, v in r["comparability"].items()
        }
    if r.get("quality"):
        if not isinstance(r["quality"], dict) or set(r["quality"]) - {
            "relevant_called",
            "relevant_total",
            "model_quality",
        }:
            raise ValueError("Invalid model quality metadata")
        if any(
            not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
            for v in r["quality"].values()
        ):
            raise ValueError("Invalid quality value")
        result["quality"] = r["quality"]
    if r.get("source_root_sha256"):
        import re, source_store

        sha = r["source_root_sha256"]
        if not re.fullmatch("[a-f0-9]{64}", sha) or sha not in {
            x.get("source_root_sha256") or x.get("container_sha256") or x["sha256"]
            for x in source_store.listing(result["person"])
        }:
            raise ValueError(
                "Model source must refer to a registered profile measurement"
            )
        result["source_root_sha256"] = sha
    if not result["regions"] and not result["traits"]:
        raise ValueError("No source or characteristic data are included.")
    return result


def save(r):
    import profile_identity

    profile_identity.assert_writable(r["person"])
    data = validate(r)
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
    sha = hashlib.sha256(raw.encode()).hexdigest()
    id = secrets.token_hex(12)
    with family.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS visual_results(id TEXT PRIMARY KEY,person TEXT,payload TEXT,sha256 TEXT,created TEXT)"
        )
        db.execute(
            "INSERT INTO visual_results VALUES(?,?,?,?,?)",
            (
                id,
                data["person"],
                raw,
                sha,
                datetime.datetime.now().astimezone().isoformat(),
            ),
        )
    return {"id": id, "sha256": sha}


def listing():
    with family.connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS visual_results(id TEXT PRIMARY KEY,person TEXT,payload TEXT,sha256 TEXT,created TEXT)"
        )
        return [
            dict(
                id=r["id"],
                person=r["person"],
                sha256=r["sha256"],
                created=r["created"],
                data=json.loads(r["payload"]),
            )
            for r in db.execute("SELECT * FROM visual_results ORDER BY created DESC")
        ]
