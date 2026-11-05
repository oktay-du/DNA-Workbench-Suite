"""Source completeness, not a claim that a personal genome is complete."""

from pathlib import Path
import re
import source_store


def read_role(name):
    n = re.sub(r"^\d{3}-", "", Path(name).name)
    m = re.search(r"(?i)(?:^|[_.-])R([12])(?=[_.-])", n)
    if not m:
        m = re.search(r"(?i)[_.-]([12])(?=\.(?:fastq|fq))", n)
    if not m:
        return "", n
    return "R" + m[1], n[: m.start(1)] + "{mate}" + n[m.end(1) :]


def summary(person):
    rows = source_store.listing(person)
    groups = {}
    builds = {}
    formats = {}
    for r in rows:
        role, key = (
            read_role(r["original_name"])
            if r["kind"] == "FASTQ"
            else ("", r["original_name"])
        )
        formats[r["kind"]] = formats.get(r["kind"], 0) + 1
        builds[r["build"]] = builds.get(r["build"], 0) + 1
        if role:
            group = groups.setdefault(
                (r["provider"], key),
                {"provider": r["provider"], "name": key, "R1": [], "R2": []},
            )
            group[role].append(
                {
                    "id": r["id"],
                    "path": r["path"],
                    "name": r["original_name"],
                    "build": r["build"],
                }
            )
    for g in groups.values():
        g["state"] = (
            "candidate_pair"
            if len(g["R1"]) == len(g["R2"]) == 1
            else "ambiguous"
            if len(g["R1"]) > 1 or len(g["R2"]) > 1
            else "awaiting_R2"
            if g["R1"]
            else "awaiting_R1"
        )
    return {
        "person": person,
        "files": len(rows),
        "formats": formats,
        "builds": builds,
        "read_sets": list(groups.values()),
        "notice": "Missing mates do not block storage. Filename pairs are candidates, not proof of sample identity or complete sequencing. Builds remain separate; unknown builds remain open. New imports update this inventory, never automatically replace Best Selection.",
    }
