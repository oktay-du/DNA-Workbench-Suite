"""Bounded local GEDCOM index and common-ancestor search, separate from DNA proof."""

import collections, hashlib, re, secrets
import family


def init(db):
    db.executescript("""CREATE TABLE IF NOT EXISTS research_gedcoms(id TEXT PRIMARY KEY,label TEXT,sha256 TEXT,created TEXT,raw TEXT);
    CREATE TABLE IF NOT EXISTS research_gedpeople(document TEXT,xref TEXT,name TEXT,sex TEXT,birth TEXT,death TEXT,PRIMARY KEY(document,xref));
    CREATE TABLE IF NOT EXISTS research_gedparents(document TEXT,parent TEXT,child TEXT,role TEXT,PRIMARY KEY(document,parent,child,role));""")


def parse(text):
    if not isinstance(text, str) or len(text) > 16 * 1024**2:
        raise ValueError("GEDCOM text exceeds the supported size")
    text = str(text).lstrip("\ufeff")
    lines = text.splitlines()
    if len(lines) > 100000:
        raise ValueError("Maximal 100.000 GEDCOM-Zeilen pro Import.")
    records = []
    current = None
    last_level = -1
    for line in lines:
        if not line.strip():
            continue
        if len(line) > 65536:
            raise ValueError("GEDCOM line is too long")
        fields = line.split(maxsplit=2)
        if len(fields) < 2 or not re.fullmatch(r"[0-9]{1,3}", fields[0]):
            raise ValueError("Invalid GEDCOM level")
        level = int(fields[0])
        xref = ""
        if fields[1].startswith("@"):
            if len(fields) < 3 or not re.fullmatch(r"@[^@\s]{1,200}@", fields[1]):
                raise ValueError("Invalid GEDCOM identifier")
            xref = fields[1]
            tail = fields[2].split(maxsplit=1)
            tag = tail[0]
            value = tail[1] if len(tail) > 1 else ""
        else:
            tag = fields[1]
            value = fields[2] if len(fields) > 2 else ""
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", tag):
            raise ValueError("Invalid GEDCOM tag")
        tag = tag.upper()
        value = value.strip()
        if level > last_level + 1:
            raise ValueError("Invalid GEDCOM level jump.")
        last_level = level
        if level == 0:
            current = {"xref": xref, "tag": tag, "lines": []}
            records.append(current)
        elif current is None:
            raise ValueError("GEDCOM needs a header.")
        else:
            current["lines"].append((level, tag, value))
    if not records or records[0]["tag"] != "HEAD" or records[-1]["tag"] != "TRLR":
        raise ValueError("GEDCOM head HEAD and completion TRLR required.")
    people = {}
    families = []
    for record in records:
        if record["tag"] == "INDI":
            xref = record["xref"]
            if not xref or xref in people:
                raise ValueError("Missing or duplicate identifier.")
            p = {"xref": xref, "name": "Unbenannt", "sex": "", "birth": "", "death": ""}
            event = ""
            for level, tag, value in record["lines"]:
                if level == 1:
                    event = tag
                    if tag == "NAME":
                        p["name"] = value[:300]
                    elif tag == "SEX":
                        p["sex"] = value[:10]
                elif level == 2 and tag == "DATE" and event in ("BIRT", "DEAT"):
                    p["birth" if event == "BIRT" else "death"] = value[:100]
            people[xref] = p
        elif record["tag"] == "FAM":
            families.append(record)
    if len(people) > 10000:
        raise ValueError("Maximal 10.000 Personen pro GEDCOM-Index.")
    parents = []
    warnings = []
    for fam in families:
        adults = [
            (value, tag)
            for level, tag, value in fam["lines"]
            if level == 1 and tag in ("HUSB", "WIFE")
        ]
        children = [
            value for level, tag, value in fam["lines"] if level == 1 and tag == "CHIL"
        ]
        for adult, role in adults:
            for child in children:
                if adult not in people or child not in people:
                    warnings.append("Family reference to unincorporated person.")
                    continue
                if adult == child:
                    raise ValueError("GEDCOM contains a self-ancestry.")
                parents.append((adult, child, role))
    graph = collections.defaultdict(list)
    for parent, child, _ in parents:
        graph[child].append(parent)
    colors = {}

    def visit(node, depth=0):
        if depth > 500:
            raise ValueError("Descent too deep or cyclical.")
        if colors.get(node) == 1:
            raise ValueError("Cycle in GEDCOM descent.")
        if colors.get(node) == 2:
            return
        colors[node] = 1
        for parent in graph[node]:
            visit(parent, depth + 1)
        colors[node] = 2

    for node in people:
        visit(node)
    return list(people.values()), list(set(parents)), sorted(set(warnings))


def import_file(r):
    text = str(r.get("text", ""))
    label = str(r.get("label", "")).strip()
    if not label:
        raise ValueError("Enter a pedigree source name.")
    people, parents, warnings = parse(text)
    sha = hashlib.sha256(text.encode()).hexdigest()
    document = secrets.token_hex(12)
    import datetime

    with family.connect() as db:
        init(db)
        if db.execute(
            "SELECT 1 FROM research_gedcoms WHERE sha256=?", (sha,)
        ).fetchone():
            raise ValueError("This pedigree is already indicated.")
        db.execute(
            "INSERT INTO research_gedcoms VALUES(?,?,?,?,?)",
            (
                document,
                label[:200],
                sha,
                datetime.datetime.now().astimezone().isoformat(),
                text,
            ),
        )
        db.executemany(
            "INSERT INTO research_gedpeople VALUES(?,?,?,?,?,?)",
            [
                (document, p["xref"], p["name"], p["sex"], p["birth"], p["death"])
                for p in people
            ],
        )
        db.executemany(
            "INSERT INTO research_gedparents VALUES(?,?,?,?)",
            [(document, *p) for p in parents],
        )
    return {
        "document": document,
        "people": len(people),
        "relationships": len(parents),
        "warnings": warnings,
        "note": "GEDCOM family assignments are genealogical indications, and adoptive, care and step contexts are not taken as DNA evidence.",
    }


def index():
    with family.connect() as db:
        init(db)
        documents = [
            dict(r)
            for r in db.execute(
                "SELECT id,label,sha256,created FROM research_gedcoms ORDER BY created DESC"
            )
        ]
        people = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM research_gedpeople ORDER BY name LIMIT 10000"
            )
        ]
    return {"documents": documents, "people": people}


def ancestors(node, parents, max_depth=20):
    found = {}
    todo = collections.deque([(node, 0, [node])])
    while todo:
        current, depth, path = todo.popleft()
        if depth >= max_depth:
            continue
        for parent in parents.get(current, []):
            if parent in path:
                continue
            if parent not in found:
                found[parent] = {"distance": depth + 1, "path": path + [parent]}
                todo.append((parent, depth + 1, path + [parent]))
    return found


def compute_mrca(r):
    document = r.get("document", "")
    a = r["a"]
    b = r["b"]
    if a == b:
        raise ValueError("Choose two different people.")
    parents = collections.defaultdict(list)
    with family.connect() as db:
        init(db)
        if document:
            labels = {
                p["xref"]: p["name"]
                for p in db.execute(
                    "SELECT * FROM research_gedpeople WHERE document=?", (document,)
                )
            }
            for row in db.execute(
                "SELECT parent,child FROM research_gedparents WHERE document=?",
                (document,),
            ):
                parents[row["child"]].append(row["parent"])
        else:
            labels = {p["id"]: p["label"] for p in db.execute("SELECT * FROM people")}
            for row in db.execute("SELECT * FROM links"):
                if row["kind"] in family.PARENTS:
                    parents[row["b"]].append(row["a"])
    if a not in labels or b not in labels:
        raise ValueError("Select people in the selected family tree.")
    aa = ancestors(a, parents)
    bb = ancestors(b, parents)
    # The person themselves is relevant when comparing an ancestor with a descendant.
    aa[a] = {"distance": 0, "path": [a]}
    bb[b] = {"distance": 0, "path": [b]}
    common = sorted(
        set(aa) & set(bb),
        key=lambda n: (
            aa[n]["distance"] + bb[n]["distance"],
            max(aa[n]["distance"], bb[n]["distance"]),
        ),
    )
    out = [
        {
            "id": n,
            "name": labels[n],
            "generations_a": aa[n]["distance"],
            "generations_b": bb[n]["distance"],
            "path_a": aa[n]["path"],
            "path_b": bb[n]["path"],
        }
        for n in common[:100]
    ]
    return {
        "common_ancestors": out,
        "note": "Common ancestors, according to the documented graph, up to 20 generations; no genetic ancestry; incomplete trees limit search.",
    }


def compute_mini_export():
    with family.connect() as db:
        people = [dict(r) for r in db.execute("SELECT * FROM people ORDER BY id")]
        links = [dict(r) for r in db.execute("SELECT * FROM links")]
    ids = {p["id"]: "@I" + str(i + 1) + "@" for i, p in enumerate(people)}
    text = [
        "0 HEAD",
        "1 SOUR DNAWorkbench",
        "1 GEDC",
        "2 VERS 5.5.1",
        "2 FORM LINEAGE-LINKED",
        "1 CHAR UTF-8",
    ]
    children = collections.defaultdict(dict)
    for link in links:
        if link["kind"] in ("mother", "father"):
            children[link["b"]][link["kind"]] = link["a"]
    groups = collections.defaultdict(list)
    for child, roles in children.items():
        groups[(roles.get("father", ""), roles.get("mother", ""))].append(child)
    fams = {key: "@F" + str(i + 1) + "@" for i, key in enumerate(groups)}
    for p in people:
        name = re.sub(r"[\r\n\x00-\x1f]", " ", p["label"]).replace("@", "(at)")
        text += ["0 " + ids[p["id"]] + " INDI", "1 NAME " + name]
        if p["synthetic"]:
            text += ["1 NOTE Empty or hypothetical profile; no measured DNA implies."]
        for key, kids in groups.items():
            if p["id"] in kids:
                text += ["1 FAMC " + fams[key]]
            if p["id"] in key:
                text += ["1 FAMS " + fams[key]]
    for (father, mother), kids in groups.items():
        text += ["0 " + fams[(father, mother)] + " FAM"]
        if father:
            text += ["1 HUSB " + ids[father]]
        if mother:
            text += ["1 WIFE " + ids[mother]]
        text += ["1 CHIL " + ids[k] for k in kids]
    text += ["0 TRLR"]
    return {
        "text": "\n".join(text) + "\n",
        "filename": "DNAWorkbench-lokaler-Stammbaum.ged",
        "note": "Minimal export of explicitly registered mother/father links. step roles and unresolved siblings are not invented as biological parenting.",
    }


def mrca(r):
    import execution_journal

    return execution_journal.execute("research.mrca", r, compute_mrca)


def mini_export(r=None):
    import execution_journal

    return execution_journal.execute(
        "research.gedcom-export", r or {}, lambda _: compute_mini_export()
    )
