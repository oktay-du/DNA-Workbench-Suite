"""Local-cohort research. IBS, imported IBD evidence and pedigrees stay distinct."""

import collections, csv, datetime, hashlib, io, itertools, math, re, secrets
import portable_json as json
import family, source_store, family_verification
from contextlib import closing

NOW = lambda: datetime.datetime.now().astimezone().isoformat()
AUTOSOMES = {str(i) for i in range(1, 23)}


def init(db):
    db.executescript("""CREATE TABLE IF NOT EXISTS research_segments(id TEXT PRIMARY KEY,batch TEXT,a TEXT,b TEXT,chrom TEXT,start INTEGER,end INTEGER,cm REAL,snps INTEGER,hap_a TEXT,hap_b TEXT,build TEXT,source TEXT,sha256 TEXT,signature_a TEXT,signature_b TEXT,created TEXT);
    CREATE INDEX IF NOT EXISTS research_segments_pair ON research_segments(a,b,build,chrom,start);
    CREATE TABLE IF NOT EXISTS research_roh(id TEXT PRIMARY KEY,person TEXT,chrom TEXT,start INTEGER,end INTEGER,snps INTEGER,build TEXT,source TEXT,sha256 TEXT,signature TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS research_projects(id TEXT PRIMARY KEY,title TEXT,ancestor TEXT,note TEXT,members TEXT,created TEXT);
    CREATE TABLE IF NOT EXISTS withdrawn_evidence(sha256 TEXT PRIMARY KEY,reason TEXT,created TEXT);""")


def people():
    with family.connect() as db:
        return [
            dict(r)
            for r in db.execute("SELECT id,label,synthetic FROM people ORDER BY label")
        ]


def person(value):
    if value not in {p["id"] for p in people()}:
        raise ValueError("Select local profile.")
    return value


def signature(pid):
    source = family_verification.source_person(pid)
    return family_verification.signature(source) if source else ""


def chromosome(value):
    value = str(value).strip().removeprefix("chr").upper()
    value = {"23": "X", "24": "Y", "26": "MT", "M": "MT"}.get(value, value)
    if value not in AUTOSOMES | {"X", "Y", "MT"}:
        raise ValueError("Unsupported chromosome:" + value)
    return value


def number(value, kind=float, minimum=0, maximum=1e10):
    result = kind(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError("Value outside the allowed range.")
    return result


def rows(text):
    lines = [
        line
        for line in str(text).lstrip("\ufeff").splitlines()
        if line.strip() and not line.startswith("##")
    ]
    if len(lines) < 2:
        raise ValueError("Table with header and data needed.")
    if len(lines) > 20001:
        raise ValueError("Maximum 20,000 lines per import; split large results.")
    delimiter = (
        "\t"
        if "\t" in lines[0]
        else ","
        if "," in lines[0]
        else ";"
        if ";" in lines[0]
        else None
    )
    values = (
        list(csv.reader(lines, delimiter=delimiter))
        if delimiter
        else [line.split() for line in lines]
    )
    header = [re.sub("[^a-z0-9]", "", v.lower().lstrip("#")) for v in values[0]]
    if len(header) != len(set(header)):
        raise ValueError("Doppelte Spaltennamen.")
    out = []
    for value in values[1:]:
        if len(value) != len(header):
            raise ValueError("Uneinheitliche Spaltenzahl.")
        out.append(dict(zip(header, value)))
    return out


def field(row, *keys, default=None):
    return next((row[k] for k in keys if k in row), default)


def import_segments(r):
    build = r.get("build")
    source = str(r.get("source", "")).strip()
    text = str(r.get("text", ""))
    if build not in ("GRCh37", "GRCh38") or not source:
        raise ValueError("Specify build and source/analysis version.")
    mapping = r.get("mapping", {})
    known = {p["id"] for p in people()}
    batch = secrets.token_hex(12)
    sha = hashlib.sha256(text.encode()).hexdigest()
    prepared = []
    seen = set()
    duplicates = 0
    signatures = {}
    for row in rows(text):
        raw_a = field(row, "a", "id1", "sample1", default=r.get("a"))
        raw_b = field(row, "b", "id2", "sample2", default=r.get("b"))
        a = mapping.get(raw_a, raw_a)
        b = mapping.get(raw_b, raw_b)
        if a not in known or b not in known or a == b:
            raise ValueError(
                "Assign each segment row to two different local profiles."
                + str(raw_a)
                + " / "
                + str(raw_b)
            )
        chrom = chromosome(field(row, "chrom", "chr", "chromosome"))
        start = number(
            field(row, "start", "startbp", "startlocation"), int, 1, 1000000000
        )
        end = number(field(row, "end", "endbp", "endlocation"), int, start, 1000000000)
        cm = number(field(row, "cm", "centimorgans", "centimorgan"), float, 0, 1000)
        snps = number(
            field(row, "snps", "nsnp", "nmarkers", default=0), int, 0, 100000000
        )
        ha = str(field(row, "hapa", "hap1", default=""))
        hb = str(field(row, "hapb", "hap2", default=""))
        if ha not in ("", "1", "2") or hb not in ("", "1", "2"):
            raise ValueError("Haplotype must be 1, 2 or empty.")
        if a > b:
            a, b = b, a
            ha, hb = hb, ha
        key = (a, b, chrom, start, end, cm, ha, hb, build)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        for p in (a, b):
            if p not in signatures:
                signatures[p] = signature(p)
        prepared.append(
            (
                secrets.token_hex(12),
                batch,
                a,
                b,
                chrom,
                start,
                end,
                cm,
                snps,
                ha,
                hb,
                build,
                source,
                sha,
                signatures[a],
                signatures[b],
                NOW(),
            )
        )
    with family.connect() as db:
        init(db)
        if db.execute(
            "SELECT 1 FROM withdrawn_evidence WHERE sha256=?", (sha,)
        ).fetchone():
            db.execute(
                "DELETE FROM research_segments WHERE sha256=? AND build=?", (sha, build)
            )
            db.execute("DELETE FROM withdrawn_evidence WHERE sha256=?", (sha,))
        existing = {
            tuple(x)
            for x in db.execute(
                "SELECT DISTINCT a,b FROM research_segments WHERE sha256=? AND build=?",
                (sha, build),
            )
        }
        if {(x[2], x[3]) for x in prepared} <= existing:
            raise ValueError(
                "This table content is already imported for these profile pairs and this build."
            )
        db.executemany(
            "INSERT INTO research_segments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            prepared,
        )
    return {
        "batch": batch,
        "segments": len(prepared),
        "duplicates_skipped": duplicates,
        "note": "Imported segment claims; no independent IBD verification.",
    }


def import_hapibd(r):
    text = str(r.get("text", ""))
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id1", "hap1", "id2", "hap2", "chrom", "start", "end", "cm"])
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        values = line.split()
        if len(values) != 8:
            raise ValueError(
                "hap-IBD requires 8 columns: ID1 HAP1 ID2 HAP2 CHR START END CM."
            )
        writer.writerow(values)
    return import_segments(dict(r, text=out.getvalue()))


def segments(build="GRCh38", min_cm=7, scope="autosomal", include_stale=False):
    if build not in ("GRCh37", "GRCh38"):
        raise ValueError("Select the build.")
    minimum = number(min_cm, float, 0, 1000)
    allowed = (
        AUTOSOMES
        if scope == "autosomal"
        else {"X"}
        if scope == "X"
        else AUTOSOMES | {"X", "Y", "MT"}
    )
    with family.connect() as db:
        init(db)
        items = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM research_segments WHERE build=? AND cm>=? AND NOT EXISTS(SELECT 1 FROM withdrawn_evidence w WHERE w.sha256=research_segments.sha256) ORDER BY a,b,chrom,start",
                (build, minimum),
            )
        ]
    signatures = {}
    result = []
    for row in items:
        if row["chrom"] not in allowed:
            continue
        for p in (row["a"], row["b"]):
            if p not in signatures:
                signatures[p] = signature(p)
        row["current"] = all(
            signatures[row[k]] == row["signature_" + k] for k in ("a", "b")
        )
        row["assignment_status"] = (
            "Source unchanged; assignment indicated by the importer"
            if row["current"]
            else "Source changed; reconsider comparison"
        )
        if row["current"] or include_stale:
            result.append(row)
    return result


def fir_candidates(items):
    grouped = collections.defaultdict(list)
    for row in items:
        if row["hap_a"] and row["hap_b"]:
            grouped[(row["a"], row["b"], row["chrom"])].append(row)
    result = []
    examined = 0
    for (a, b, chrom), rows_ in grouped.items():
        for x, y in itertools.combinations(rows_, 2):
            examined += 1
            if examined > 200000:
                return result
            if x["source"] != y["source"]:
                continue
            if x["hap_a"] == y["hap_a"] or x["hap_b"] == y["hap_b"]:
                continue
            start = max(x["start"], y["start"])
            end = min(x["end"], y["end"])
            if start >= end:
                continue
            result.append(
                {
                    "a": a,
                    "b": b,
                    "chrom": chrom,
                    "start": start,
                    "end": end,
                    "cm": None,
                    "status": "Overlap of complementary haplotype pairs; IBD2-FIR candidate, not independently confirmed.",
                }
            )
            if len(result) >= 1000:
                return result
    return result


def pair(a, b):
    return tuple(sorted((a, b)))


def pair_summary(items):
    unique = {
        (r["chrom"], r["start"], r["end"], r["hap_a"], r["hap_b"], round(r["cm"], 6)): r
        for r in items
    }
    items = list(unique.values())
    overlaps = False
    for chrom, group in itertools.groupby(
        sorted(items, key=lambda r: (r["chrom"], r["start"])), key=lambda r: r["chrom"]
    ):
        furthest = 0
        for row in group:
            if row["start"] < furthest:
                overlaps = True
            furthest = max(furthest, row["end"])
    return {
        "segments": len(items),
        "total_cm": None if overlaps else round(sum(r["cm"] for r in items), 3),
        "largest_cm": max((r["cm"] for r in items), default=0),
        "overlap": overlaps,
        "raw_segment_sum_cm": round(sum(r["cm"] for r in items), 3),
        "note": "Overlapping segments: no unchecked cM total."
        if overlaps
        else "cM sum of imported, non-overlapping segments; no DNA percentage.",
    }


def matches(focus, items):
    person(focus)
    groups = collections.defaultdict(list)
    for row in items:
        if focus in (row["a"], row["b"]):
            groups[row["b"] if row["a"] == focus else row["a"]].append(row)
    return sorted(
        [dict(person=p, **pair_summary(rows)) for p, rows in groups.items()],
        key=lambda r: r["largest_cm"],
        reverse=True,
    )


def shared_matches(a, b, items):
    x = {r["person"] for r in matches(a, items)}
    y = {r["person"] for r in matches(b, items)}
    return sorted((x & y) - {a, b})


def triangulation(focus, items, limit=1000):
    indexed = collections.defaultdict(list)
    for row in items:
        indexed[pair(row["a"], row["b"])].append(row)
    others = sorted({p for key in indexed if focus in key for p in key if p != focus})
    out = []
    examined = 0
    for b, c in itertools.combinations(others, 2):
        for ab in indexed[pair(focus, b)]:
            for ac in indexed[pair(focus, c)]:
                if ab["chrom"] != ac["chrom"]:
                    continue
                for bc in indexed[pair(b, c)]:
                    examined += 1
                    if examined > 200000:
                        return {"candidates": out, "limited": True}
                    if bc["chrom"] != ab["chrom"]:
                        continue
                    start = max(ab["start"], ac["start"], bc["start"])
                    end = min(ab["end"], ac["end"], bc["end"])
                    if start >= end:
                        continue
                    haps = collections.defaultdict(set)
                    complete = True
                    for row in (ab, ac, bc):
                        for k in ("a", "b"):
                            if not row["hap_" + k]:
                                complete = False
                            else:
                                haps[row[k]].add(row["hap_" + k])
                    consistent = (
                        complete
                        and len({row["source"] for row in (ab, ac, bc)}) == 1
                        and all(len(v) == 1 for v in haps.values())
                    )
                    out.append(
                        {
                            "a": focus,
                            "b": b,
                            "c": c,
                            "chrom": ab["chrom"],
                            "start": start,
                            "end": end,
                            "phase_consistent": consistent,
                            "status": "Phase-consistent candidate from imported segments"
                            if consistent
                            else "Overlap Candidate; Phase Not Confirmed",
                            "intersection_cm": None,
                        }
                    )
                    if len(out) >= limit:
                        return {"candidates": out, "limited": True}
    return {"candidates": out, "limited": False}


def graph_clusters(items):
    graph = collections.defaultdict(set)
    for row in items:
        graph[row["a"]].add(row["b"])
        graph[row["b"]].add(row["a"])
    groups = []
    seen = set()
    for node in sorted(graph):
        if node in seen:
            continue
        group = []
        todo = [node]
        seen.add(node)
        while todo:
            current = todo.pop()
            group.append(current)
            for neighbor in graph[current] - seen:
                seen.add(neighbor)
                todo.append(neighbor)
        edges = sum(len(graph[n] & set(group)) for n in group) // 2
        n = len(group)
        groups.append(
            {
                "members": sorted(group),
                "edges": edges,
                "density": edges / (n * (n - 1) / 2) if n > 1 else 0,
            }
        )
    return {
        "groups": groups,
        "method": "Contiguous components in the local match graph; no GEDmatch AutoCluster/AutoKinship reimplementation; high density alone proves no endogamy.",
    }


def panel(pid, file_id=""):
    source = family_verification.source_person(pid)
    if not source:
        return []
    registered = source_store.listing(source)
    allowed = {
        r["sha256"]: r
        for r in registered
        if r["available"]
        and r.get("lifecycle") != "needs_review"
        and not r.get("qc_review_required")
        and (not file_id or r["id"] == file_id)
    }
    with closing(source_store.connect(source)) as db:
        rows_ = db.execute("SELECT sha256,payload FROM inspections").fetchall()
    out = []
    for sha, payload in rows_:
        if sha not in allowed:
            continue
        r = json.loads(payload)
        if (
            r.get("color") in ("red", "black")
            or not r.get("build")
            or not r.get("fingerprint")
        ):
            continue
        out.append(
            {
                "sha256": sha,
                "file": allowed[sha]["original_name"],
                "build": r["build"],
                "points": r["fingerprint"],
                "limit": 100000,
                "checked": r.get("checked", ""),
            }
        )
    return out


def raw_comparison(a, b, kit_a="", kit_b=""):
    person(a)
    person(b)
    if a == b:
        raise ValueError("Select two different profiles.")
    best = None
    for x in panel(a, kit_a):
        for y in panel(b, kit_b):
            if x["build"] != y["build"]:
                continue
            common = set(x["points"]) & set(y["points"])
            genotypes = []
            for k in common:
                ga = x["points"][k]
                gb = y["points"][k]
                if len(ga) == 2 and len(gb) == 2 and set(ga + gb) <= set("ACGT"):
                    genotypes.append((ga, gb))
            if not genotypes:
                continue
            identical = sum(x == y for x, y in genotypes)
            ibs0 = sum(not (set(x) & set(y)) for x, y in genotypes)
            result = {
                "a": a,
                "b": b,
                "build": x["build"],
                "common_snps": len(genotypes),
                "identical_genotypes": identical,
                "ibs0": ibs0,
                "concordance_percent": identical / len(genotypes) * 100,
                "source_a": x["file"],
                "source_b": y["file"],
                "checked_a": x["checked"],
                "checked_b": y["checked"],
                "scope": "Autosome test fingerprints, maximum 100,000 SNPs per source; no full genome coverage, no IBD share, no kinship confirmation.",
            }
            if best is None or result["common_snps"] > best["common_snps"]:
                best = result
    return best or {
        "a": a,
        "b": b,
        "status": "No comparable test fingerprints with common build. Check files first in the import submenu.",
    }


def matrix(ids, items):
    groups = collections.defaultdict(list)
    for row in items:
        groups[pair(row["a"], row["b"])].append(row)
    return {
        "ids": ids,
        "values": [
            [
                None
                if a == b
                else pair_summary(groups[pair(a, b)])["total_cm"]
                if pair(a, b) in groups
                else None
                for b in ids
            ]
            for a in ids
        ],
        "unit": "cM; empty cells mean no suitable evidence, not zero shared DNA.",
    }


def compute_raw_matrix(r):
    build = r.get("build", "GRCh38")
    metric = r.get("metric", "overlap")
    ids = [p["id"] for p in people()][:40]
    if metric not in ("overlap", "identical", "concordance"):
        raise ValueError("Unbekannte Markermetrik.")
    selected = {}
    for p in ids:
        candidates = [x for x in panel(p) if x["build"] == build]
        if candidates:
            selected[p] = max(candidates, key=lambda x: len(x["points"]))
    values = []
    for a in ids:
        row = []
        for b in ids:
            if a not in selected or b not in selected:
                row.append(None)
                continue
            x = selected[a]["points"]
            y = selected[b]["points"]
            common = set(x) & set(y)
            if not common:
                row.append(None)
                continue
            same = sum(x[k] == y[k] for k in common)
            row.append(
                len(common)
                if metric == "overlap"
                else same
                if metric == "identical"
                else 100 * same / len(common)
            )
        values.append(row)
    return {
        "ids": ids,
        "values": values,
        "sources": {k: v["file"] for k, v in selected.items()},
        "metric": metric,
        "unit": "SNP-Anzahl"
        if metric != "concordance"
        else "% identical genotypes on the intersection",
        "note": "Autosome test fingerprints up to 100,000 SNPs per source, per profile the source with the most stored test points in the selected build, no IBD percentage, no kinship matrix.",
    }


def segment_groups(items):
    groups = []
    for chrom, rows_ in itertools.groupby(
        sorted(items, key=lambda r: (r["chrom"], r["start"])), key=lambda r: r["chrom"]
    ):
        current = []
        end = -1
        for row in rows_:
            if current and row["start"] >= end:
                groups.append(
                    {
                        "chrom": chrom,
                        "start": min(r["start"] for r in current),
                        "end": end,
                        "members": sorted(
                            {p for r in current for p in (r["a"], r["b"])}
                        ),
                        "segments": len(current),
                    }
                )
                current = []
            current.append(row)
            end = max((r["end"] for r in current), default=0)
        if current:
            groups.append(
                {
                    "chrom": chrom,
                    "start": min(r["start"] for r in current),
                    "end": end,
                    "members": sorted({p for r in current for p in (r["a"], r["b"])}),
                    "segments": len(current),
                }
            )
    return groups


def import_roh(r):
    pid = person(r.get("person"))
    build = r.get("build")
    source = str(r.get("source", "")).strip()
    text = str(r.get("text", ""))
    if build not in ("GRCh37", "GRCh38") or not source:
        raise ValueError("Build and source.")
    sha = hashlib.sha256(text.encode()).hexdigest()
    prepared = []
    seen = set()
    sig = signature(pid)
    for row in rows(text):
        chrom = chromosome(field(row, "chrom", "chr", "chromosome"))
        start = number(field(row, "start", "pos1"), int, 1, 1e9)
        end = number(field(row, "end", "pos2"), int, start, 1e9)
        snps = number(field(row, "snps", "nsnp", default=0), int, 0, 1e8)
        iid = field(row, "iid")
        if iid and r.get("sample") and iid != r["sample"]:
            continue
        if iid and not r.get("sample"):
            raise ValueError(
                "In the case of PLINK-.hom, specify the IID to be imported."
            )
        key = (chrom, start, end)
        if key in seen:
            continue
        seen.add(key)
        prepared.append(
            (
                secrets.token_hex(12),
                pid,
                chrom,
                start,
                end,
                snps,
                build,
                source,
                sha,
                sig,
                NOW(),
            )
        )
    if not prepared:
        raise ValueError("No matching ROH records.")
    with family.connect() as db:
        init(db)
        if db.execute(
            "SELECT 1 FROM research_roh WHERE person=? AND build=? AND sha256=?",
            (pid, build, sha),
        ).fetchone():
            raise ValueError("This ROH table is already imported.")
        db.executemany(
            "INSERT INTO research_roh VALUES(?,?,?,?,?,?,?,?,?,?,?)", prepared
        )
    return {
        "runs": len(prepared),
        "note": "Imported homozygosity sections; no automatic statement about a parental kinship.",
    }


def lengths(build):
    folder = source_store.ROOT / "References" / ("FASTA_" + build)
    for path in folder.glob("*.fai"):
        result = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            c = line.split("\t")
            try:
                chrom = chromosome(c[0])
                result[chrom] = int(c[1])
            except (ValueError, IndexError):
                continue
        if result:
            return {
                "values": result,
                "source": path.name,
                "mode": "Referenz-FASTA-Index",
            }
    return {
        "values": {},
        "source": "No local reference length list; bars scale to observed endpoints",
        "mode": "observed",
    }


def dashboard():
    profiles = people()
    kits = []
    for p in profiles:
        source = family_verification.source_person(p["id"])
        if not source:
            continue
        for row in source_store.listing(source):
            kits.append(
                {
                    k: row.get(k)
                    for k in (
                        "id",
                        "provider",
                        "label",
                        "original_name",
                        "build",
                        "qc_color",
                        "qc_verified",
                        "called_points",
                        "qc_points",
                        "scope_summary",
                    )
                }
                | {"person": p["id"]}
            )
    with family.connect() as db:
        init(db)
        sources = [
            dict(r)
            for r in db.execute(
                "SELECT batch,build,source,sha256,COUNT(*) AS segments,MIN(created) AS created FROM research_segments GROUP BY batch ORDER BY created DESC"
            )
        ]
        roh = db.execute("SELECT COUNT(*) FROM research_roh").fetchone()[0]
        projects = [
            dict(r)
            for r in db.execute("SELECT * FROM research_projects ORDER BY created DESC")
        ]
    for project in projects:
        project["members"] = json.loads(project["members"])
    return {
        "people": profiles,
        "kits": kits,
        "segment_sources": sources,
        "roh_runs": roh,
        "projects": projects,
        "scope": "Local data only. No access to GEDmatch accounts, global matches or proprietary models.",
    }


def compute_analysis(r):
    a = person(r.get("a"))
    b = r.get("b", "")
    build = r.get("build", "GRCh38")
    minimum = r.get("min_cm", 7)
    scope = r.get("scope", "autosomal")
    items = segments(build, minimum, scope)
    min_snps = number(r.get("min_snps", 0), int, 0, 100000000)
    if b:
        person(b)
        if a == b:
            raise ValueError("Select two different profiles.")
    if min_snps:
        items = [x for x in items if x["snps"] >= min_snps]
    if r.get("phased_only"):
        items = [x for x in items if x["hap_a"] and x["hap_b"]]
    pair_rows = [x for x in items if b and pair(x["a"], x["b"]) == pair(a, b)]
    neighbors = matches(a, items)
    with family.connect() as db:
        init(db)
        rohs = [
            dict(x)
            for x in db.execute(
                "SELECT * FROM research_roh WHERE person=? AND build=? AND NOT EXISTS(SELECT 1 FROM withdrawn_evidence w WHERE w.sha256=research_roh.sha256)",
                (a, build),
            )
        ]
    sig = signature(a)
    for row in rohs:
        row["current"] = row["signature"] == sig
    return {
        "focus": a,
        "build": build,
        "min_cm": minimum,
        "scope": scope,
        "matches": neighbors,
        "shared": shared_matches(a, b, items) if b else [],
        "pair": pair_summary(pair_rows),
        "segments": pair_rows if b else [x for x in items if a in (x["a"], x["b"])],
        "triangulation": triangulation(a, items),
        "clusters": graph_clusters(items),
        "segment_groups": segment_groups(items),
        "fir": fir_candidates(pair_rows),
        "matrix": matrix([p["id"] for p in people()][:80], items),
        "roh": rohs,
        "lengths": lengths(build),
        "king": family_verification.verify(a),
        "raw": raw_comparison(a, b, r.get("kit_a", ""), r.get("kit_b", ""))
        if b and a != b
        else None,
        "notes": [
            "IBS/genotype match is not a split IBD DNA component.",
            "Segments are imported evidence; construction, trial, phase and quality must fit.",
            "Common matches or overlapping segments alone do not confirm a common ancestor.",
            "No commercial Q-matching, AutoKinship or Oracle algorithms are reproduced here.",
        ],
    }


def project(r):
    title = str(r.get("title", "")).strip()
    members = list(dict.fromkeys(r.get("members", [])))
    if not title or len(title) > 150:
        raise ValueError("Project title angeben (maximal 150 Zeichen).")
    for p in members:
        person(p)
    ancestor = str(r.get("ancestor", ""))
    if ancestor:
        person(ancestor)
    with family.connect() as db:
        init(db)
        db.execute(
            "INSERT INTO research_projects VALUES(?,?,?,?,?,?)",
            (
                secrets.token_hex(12),
                title,
                ancestor,
                str(r.get("note", ""))[:2000],
                json.dumps(members),
                NOW(),
            ),
        )
    return {
        "status": "Local ancestor project stored; assignment is a research hypothesis."
    }


def compute_untransmitted(r):
    if len({r["a"], r["b"], r["child"]}) != 3:
        raise ValueError("Select two parent profiles and a different child profile.")
    a = family.locus(person(r["a"]), r["build"], str(r["chrom"]), int(r["pos"]))
    b = family.locus(person(r["b"]), r["build"], str(r["chrom"]), int(r["pos"]))
    c = family.locus(person(r["child"]), r["build"], str(r["chrom"]), int(r["pos"]))
    if chromosome(r["chrom"]) not in AUTOSOMES:
        raise ValueError(
            "This simplified calculator only supports autosomal positions."
        )
    if not all(len(x.get("alleles", [])) == 2 for x in (a, b, c)):
        return {
            "status": "Complete, unique diploid genotypes of all three profiles are missing."
        }
    options = []
    for i, x in enumerate(a["alleles"]):
        for j, y in enumerate(b["alleles"]):
            if sorted((x, y)) == sorted(c["alleles"]):
                options.append(
                    {
                        "transmitted": [x, y],
                        "not_transmitted": [a["alleles"][1 - i], b["alleles"][1 - j]],
                    }
                )
    return {
        "possibilities": list(
            {json.dumps(x, sort_keys=True): x for x in options}.values()
        ),
        "note": "Possible untransmitted alleles in ONE position. No real sibling profile, no phased genome, and no health prediction.",
    }


def analysis(r):
    import comparison_cache

    return comparison_cache.run(r)


def dispatch(action, r):
    if action == "viewed":
        import execution_journal

        return execution_journal.record_view(r)
    if action == "analysis-saved":
        import comparison_cache

        return {"result": comparison_cache.saved(r)}
    if action == "sources-manifest":
        pid = person(r["person"])
        source = family_verification.source_person(pid)
        files = source_store.listing(source) if source else []
        return {
            "person": pid,
            "files": [
                {
                    k: x.get(k)
                    for k in (
                        "id",
                        "provider",
                        "original_name",
                        "sha256",
                        "build",
                        "measurement",
                        "qc_color",
                        "called_points",
                        "qc_points",
                    )
                }
                for x in files
            ],
            "note": "Consensus Preparation Source Manifesto. No new genotype dataset. Check builds, measured/imputed values, dependent sources, and conflicts before merging.",
        }
    return (
        dashboard()
        if action == "dashboard"
        else analysis(r)
        if action == "analysis"
        else raw_matrix(r)
        if action == "raw-matrix"
        else import_segments(r)
        if action == "segments-import"
        else import_hapibd(r)
        if action == "hapibd-import"
        else import_roh(r)
        if action == "roh-import"
        else project(r)
        if action == "project"
        else untransmitted(r)
        if action == "untransmitted"
        else (_ for _ in ()).throw(ValueError("Unbekannte Vergleichsfunktion."))
    )


def raw_matrix(r):
    import execution_journal

    return execution_journal.execute("research.raw-matrix", r, compute_raw_matrix)


def untransmitted(r):
    import execution_journal

    return execution_journal.execute("research.untransmitted", r, compute_untransmitted)
