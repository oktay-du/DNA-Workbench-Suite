"""Keep marker concordance separate from KING relatedness and pedigree claims."""

import hashlib, math, datetime
import portable_json as json
import family, source_store
from contextlib import closing


def source_person(person):
    with family.connect() as db:
        r = db.execute(
            "SELECT source_person FROM bindings WHERE person=?", (person,)
        ).fetchone()
        p = db.execute("SELECT synthetic FROM people WHERE id=?", (person,)).fetchone()
    return r[0] if r else person if p and not p[0] else None


def signature(person):
    if not person:
        return ""
    values = sorted(
        set(
            r["sha256"]
            for r in source_store.listing(person)
            if r.get("lifecycle") != "needs_review" and not r.get("qc_review_required")
        )
    )
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()


def degree(phi):
    if phi >= 0.354:
        return 0, "Identical sample / identical twins possible"
    if phi >= 0.177:
        return 1, "Parents–child or brother/sister possible"
    if phi >= 0.0884:
        return (
            2,
            "Grandparents–grandchildren, half-siblings or aunt/uncle–niece/nephew possible",
        )
    if phi >= 0.0442:
        return 3, "Cousin/Cousine 1st degree or other relationship 3rd degree possible"
    return (
        None,
        "No close kinship reliably supported; more distant relationship remains possible",
    )


def init(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS kinship_evidence(a TEXT,b TEXT,payload TEXT,created TEXT,PRIMARY KEY(a,b))"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS withdrawn_evidence(sha256 TEXT PRIMARY KEY,reason TEXT,created TEXT)"
    )


def import_king(r):
    text = str(r.get("text", ""))
    mapping = r.get("mapping", {})
    build = r.get("build")
    note = str(r.get("note", "")).strip()
    if build not in ["GRCh37", "GRCh38"] or not note:
        raise ValueError("Specify build and source / QC of the comparison panel.")
    if not mapping or len(set(mapping.values())) != len(mapping):
        raise ValueError("Assign each sample to its own profile.")
    with family.connect() as db:
        ids = {p[0] for p in db.execute("SELECT id FROM people")}
    if set(mapping.values()) - ids:
        raise ValueError("Unknown profile in sample assignment.")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Select KING table with header and result lines.")
    header = lines[0].lstrip("#").split()
    rows = [dict(zip(header, l.split())) for l in lines[1:]]
    if not {"IID1", "IID2", "KINSHIP", "NSNP"} <= set(header):
        raise ValueError("PLINK-2-KING table requires IID1, IID2, NSNP and KINSHIP.")
    samples = {x[k] for x in rows for k in ["IID1", "IID2"]}
    if samples - set(mapping):
        raise ValueError("Assign all sample identifiers from the table.")
    fid = {}
    for row in rows:
        for i in ["1", "2"]:
            iid = row["IID" + i]
            value = row.get("FID" + i, "0")
            if iid in fid and fid[iid] != value:
                raise ValueError(
                    "Mehrdeutige IID in verschiedenen Familien. Eindeutige Probenkennungen verwenden."
                )
            fid[iid] = value
    prepared = []
    seen = set()
    now = datetime.datetime.now().astimezone().isoformat()
    sha = hashlib.sha256(text.encode()).hexdigest()
    for row in rows:
        a, b = sorted([mapping[row["IID1"]], mapping[row["IID2"]]])
        if a == b or (a, b) in seen:
            raise ValueError("Doppelte / identische Probenpaarung.")
        seen.add((a, b))
        phi = float(row["KINSHIP"])
        n = int(row["NSNP"])
        if not math.isfinite(phi) or not -1 <= phi <= 0.6 or n < 1:
            raise ValueError("Invalid KING coefficient / marker number.")
        sa = source_person(a)
        sb = source_person(b)
        if not sa or not sb or sa == sb:
            raise ValueError(
                "DNA source profiles must be present and different, and empty profiles must be connected to data first."
            )
        payload = {
            "a": a,
            "b": b,
            "kinship": phi,
            "nsnp": n,
            "build": build,
            "source_sha256": sha,
            "note": note,
            "signature_a": signature(sa),
            "signature_b": signature(sb),
            "source_a": sa,
            "source_b": sb,
            "status": "imported KING result; sample assignment specified by the user",
        }
        prepared.append((a, b, json.dumps(payload, ensure_ascii=False), now))
    with family.connect() as db:
        init(db)
        db.execute("DELETE FROM withdrawn_evidence WHERE sha256=?", (sha,))
        db.executemany(
            "INSERT OR REPLACE INTO kinship_evidence VALUES(?,?,?,?)", prepared
        )
    return {"pairs": len(prepared)}


def marker_comparison(a, b):
    if not a or not b:
        return None

    def load(p):
        allowed = {
            r["sha256"]
            for r in source_store.listing(p)
            if r.get("lifecycle") != "needs_review" and not r.get("qc_review_required")
        }
        with closing(source_store.connect(p)) as db:
            rows = db.execute("SELECT sha256,payload FROM inspections").fetchall()
        result = []
        for row in rows:
            if row[0] not in allowed:
                continue
            r = json.loads(row[1])
            if (
                r.get("color") not in ["red", "black"]
                and r.get("fingerprint")
                and r.get("build")
            ):
                result.append(r)
        return result

    best = None
    for x in load(a):
        for y in load(b):
            if x["build"] != y["build"]:
                continue
            common = set(x["fingerprint"]) & set(y["fingerprint"])
            if len(common) < 1000:
                continue
            same = sum(x["fingerprint"][k] == y["fingerprint"][k] for k in common)
            item = {
                "common_snps": len(common),
                "concordance_percent": same / len(common) * 100,
                "build": x["build"],
                "source_a": x.get("name"),
                "source_b": y.get("name"),
                "meaning": "genotype match on commonly read markers; NO shared DNA content and no kinship.",
            }
            if not best or len(common) > best["common_snps"]:
                best = item
    return best


def expected(a, b):
    with family.connect() as db:
        links = [dict(r) for r in db.execute("SELECT * FROM links")]
        routes = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM routes WHERE (anchor=? AND target=?) OR (anchor=? AND target=?)",
                (a, b, b, a),
            )
        ]
    kinds = {l["kind"] for l in links if {l["a"], l["b"]} == {a, b}}
    if kinds & family.PARENTS:
        return {1}
    if kinds & {"brother", "sister"}:
        return {1}
    if kinds & family.HALF:
        return {2}
    degrees = {
        3 if r["relation"] == "cousin" else 2
        for r in routes
        if r["relation"] in ["cousin", "aunt", "uncle"]
    }
    # Grandparent paths are two parent-child edges, excluding step relations.
    for l in links:
        if l["kind"] in family.PARENTS and any(
            k["kind"] in family.PARENTS
            and k["a"] == l["b"]
            and {l["a"], k["b"]} == {a, b}
            for k in links
        ):
            degrees.add(2)
    return degrees


def verify(focus):
    with family.connect() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM people")]
        init(db)
        withdrawn = {r[0] for r in db.execute("SELECT sha256 FROM withdrawn_evidence")}
        evidence = {
            tuple(sorted((r["a"], r["b"]))): json.loads(r["payload"])
            for r in db.execute("SELECT * FROM kinship_evidence")
            if json.loads(r["payload"]).get("source_sha256") not in withdrawn
        }
    if focus not in ids:
        raise ValueError("Select the reference profile.")
    out = []
    sa = source_person(focus)
    for person in ids:
        if person == focus:
            continue
        sb = source_person(person)
        r = {
            "person": person,
            "focus": focus,
            "status": "Not checked yet",
            "relatedness_percent": None,
            "marker_comparison": None,
        }
        ev = evidence.get(tuple(sorted((focus, person))))
        if ev:
            current = all(
                signature(source_person(ev[k])) == ev["signature_" + k]
                and source_person(ev[k]) == ev["source_" + k]
                for k in ["a", "b"]
            )
            r["evidence"] = ev
            if not current:
                r["status"] = "Source status changed: re-examine comparison"
            elif ev["nsnp"] < 10000:
                r["status"] = "Too few common markers for kinship classification"
            else:
                deg, label = degree(ev["kinship"])
                r.update(
                    degree=deg,
                    possible_relationships=label,
                    relatedness_percent=max(0, min(100, 200 * ev["kinship"])),
                    status="Preliminary estimate of KING",
                    percentage_label="Estimated relative share (2 × KING; no segment-based measured IBD share)",
                )
                exp = expected(focus, person)
                r["pedigree_check"] = (
                    "Registered relationship compatible with this degree; not clearly confirmed"
                    if exp and deg in exp
                    else "Registered relationship does not fit the estimated degree; check sources and assignment"
                    if exp
                    else "No clear biological relationship specified; no compatibility confirmation"
                )
        if sa and sb:
            r["marker_comparison"] = marker_comparison(sa, sb)
        out.append(r)
    return {
        "focus": focus,
        "comparisons": out,
        "note": "KING values kinship, does not confirm a single family role, step-relationships do not count as biological ancestry.",
    }
