"""Explicit shared workflow DAG, built on the existing validated task runner/cache."""

from pathlib import Path
import contextlib, datetime, json, threading, time, uuid
import source_store, suite_api, workflow_sources, result_cache, profile_identity

GUARD = threading.RLock()
ACTIVE = None
OWNER = None
RECIPES = {
    "variant_review": (
        "Variant evidence review",
        "Variantenbelege prüfen",
        "◉",
        ["variant_evidence_audit", "vcf_qc"],
    ),
    "sequence_research": (
        "Sequence exploration",
        "Sequenzen erkunden",
        "≋",
        ["sequence_stats", "sequence_explore", "seqviz_view"],
    ),
    "prepare": (
        "Prepare files",
        "Preparing files",
        "▤",
        ["profile_analyze", "profile_generate", "profile_activate", "vcf_qc"],
    ),
    "ancestry": (
        "Ancestry & lineages",
        "Origin & Lines",
        "◎",
        ["profile_analyze", "vcf_qc", "mito", "yhaplo", "rfmix"],
    ),
    "health": (
        "Health research",
        "Gesundheitsforschung",
        "✧",
        ["profile_analyze", "vcf_qc", "opencravat_run", "vep"],
    ),
    "medication": (
        "Medication research",
        "Medikamentenforschung",
        "✚",
        ["profile_analyze", "vcf_qc", "pharmcat"],
    ),
    "fitness": (
        "Fitness scores",
        "Fitness-Scores",
        "↗",
        ["profile_analyze", "vcf_qc", "pgs"],
    ),
    "nutrition": (
        "Nutrition scores",
        "Nutritional scores",
        "◒",
        ["profile_analyze", "vcf_qc", "pgs"],
    ),
    "family": (
        "Family & transmission",
        "Family & inheritance",
        "♧",
        ["profile_analyze", "variant_index", "parent_origin", "roh", "kinship"],
    ),
}
DEPENDENCIES = {"profile_activate": ["profile_generate"]}
TERMINAL = {"Complete", "Failed", "Cancelled", "Started"}


def now():
    return profile_identity.now()


def root():
    return suite_api.ROOT


def schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS workflow_inputs(task TEXT PRIMARY KEY,inputs TEXT,updated TEXT,origin TEXT)"
    )


def configure(person, task, values, origin="manual workflow configuration", recipe=""):
    suite_api.checked_person(person)
    profile_identity.assert_writable(person)
    spec = next((x for x in suite_api.CAT()["tasks"] if x["id"] == task), None)
    if (
        not spec
        or not isinstance(values, dict)
        or set(values) - {f["key"] for f in spec["fields"]}
    ):
        raise ValueError("Invalid workflow configuration")
    for f in spec["fields"]:
        v = values.get(f["key"])
        if v is None:
            continue
        if f["kind"] == "choice" and v and v not in f["choices"]:
            raise ValueError("Invalid workflow choice")
        if (
            not isinstance(v, (str, list))
            or isinstance(v, list)
            and (len(v) > 50 or any(not isinstance(x, str) for x in v))
        ):
            raise ValueError("Invalid workflow input")
    if recipe and recipe not in RECIPES:
        raise ValueError("Unknown workflow")
    key = recipe + ":" + task if recipe and task == "pgs" else task
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        db.execute(
            "INSERT OR REPLACE INTO workflow_inputs VALUES(?,?,?,?)",
            (key, json.dumps(values), now(), origin),
        )
        db.commit()
    return {"saved": True, "task": task}


def remembered(person, task, history):
    with contextlib.closing(source_store.connect(person)) as db:
        schema(db)
        row = db.execute(
            "SELECT inputs,updated,origin FROM workflow_inputs WHERE task=?", (task,)
        ).fetchone()
        db.commit()
    if row:
        return {"inputs": json.loads(row[0]), "date": row[1], "origin": row[2]}
    for job in history:
        if job.get("task") == task and job.get("status") == "Complete":
            try:
                return {
                    "inputs": json.loads(
                        (
                            root()
                            / "Projects/Launcher"
                            / person
                            / job["job"]
                            / "inputs.json"
                        ).read_text(encoding="utf-8")
                    )["inputs"],
                    "date": job.get("finished", job.get("started")),
                    "origin": task + " / " + job["job"],
                }
            except (OSError, ValueError, KeyError):
                pass
    return None


def augment(person, task, history, plan):
    """Keep current biological ranking; reuse available non-biological configuration."""
    saved = remembered(person, task, history)
    plan["autofill"] = []
    for key in workflow_sources.ROLES.get(task, {}):
        value = plan["inputs"].get(key)
        paths = value if isinstance(value, list) else [value]
        for path in paths:
            if not path:
                continue
            option = next(
                (x for x in plan["options"].get(key, []) if x["path"] == path), None
            )
            if option:
                plan["autofill"].append(
                    {
                        "field": key,
                        "origin": option["provider"] + " / " + option["name"],
                        "date": "",
                    }
                )
    if not saved:
        return plan
    spec = next((x for x in suite_api.CAT()["tasks"] if x["id"] == task), None)
    for f in spec["fields"] if spec else []:
        k = f["key"]
        v = saved["inputs"].get(k)
        if (
            not v
            or k in workflow_sources.ROLES.get(task, {})
            or k in ("build", "build_a", "build_b", "analysis", "folder")
        ):
            continue
        if f["kind"] in ("file", "folder"):
            paths = v if isinstance(v, list) else [v]
            if not all(Path(p).exists() for p in paths):
                continue
        if f["kind"] == "choice" and v not in f["choices"]:
            continue
        plan["inputs"][k] = v
        plan["autofill"].append(
            {"field": k, "origin": saved["origin"], "date": saved["date"]}
        )
    return plan


def task_plan(person, task, recipe=""):
    spec = next(x for x in suite_api.CAT()["tasks"] if x["id"] == task)
    history = suite_api.jobs(person)
    p = workflow_sources.plan(root(), person, task, history)
    p["inputs"] = {
        k: v for k, v in p["inputs"].items() if k in {f["key"] for f in spec["fields"]}
    }
    # workflow_sources also supplies remembered inputs to ordinary tool windows.
    vals = {f["key"]: f.get("default", "") for f in spec["fields"]}
    vals.update(p["inputs"])
    saved = remembered(
        person, recipe + ":" + task if recipe and task == "pgs" else task, history
    )
    if recipe and task == "pgs":
        vals["score"] = ""
    if saved:
        for f in spec["fields"]:
            k = f["key"]
            v = saved["inputs"].get(k)
            if (
                (k not in p["inputs"] or recipe and task == "pgs" and k == "score")
                and v
                and f["kind"] in ("file", "folder")
            ):
                paths = v if isinstance(v, list) else [v]
                if all(Path(x).exists() for x in paths):
                    vals[k] = v
    if task == "profile_activate":
        for job in history:
            if (
                job.get("task") == "profile_generate"
                and job.get("status") == "Complete"
            ):
                folder = root() / "Projects/Launcher" / person / job["job"] / "Results"
                if (folder / "manifest.json").is_file():
                    vals["folder"] = str(folder)
                    break
    missing = []
    if task == "profile_analyze" and vals.get("target") == "GRCh38":
        chain = Path(
            vals.get("chain") or root() / "References/LiftOver/hg19ToHg38.over.chain.gz"
        )
        reference = Path(
            vals.get("reference")
            or root()
            / "References/FASTA_GRCh38/GRCh38_full_analysis_set_plus_decoy_hla.fa"
        )
        if not chain.is_file() or not reference.is_file():
            if saved and saved["inputs"].get("target") == "GRCh38":
                missing.extend(["chain", "reference"])
            else:
                vals["target"] = "Getrennt belassen"
    for f in spec["fields"]:
        v = vals.get(f["key"])
        bad = (
            not v or isinstance(v, str) and v in ("Please select", "Unknown", "Unknown")
        )
        if f.get("required") and bad:
            missing.append(f["key"])
        if v and f["kind"] in ("file", "folder"):
            paths = v if isinstance(v, list) else [v]
            if any(not Path(x).exists() for x in paths):
                missing.append(f["key"])
    cached = (
        result_cache.lookup(root(), person, spec, vals, history)
        if not missing
        else {"previous": None}
    )
    if task == "profile_activate" and vals.get("folder"):
        import profile_pipeline

        if any(
            x.get("folder") == vals["folder"]
            for x in profile_pipeline.summary(person).get("sets", [])
        ):
            cached = {
                "previous": {"job": Path(vals["folder"]).parent.name, "task": task}
            }
    return {
        "task": task,
        "title": spec["title"],
        "tools": spec["tools"],
        "inputs": vals,
        "missing": sorted(set(missing)),
        "status": "reusable"
        if cached["previous"]
        else "needs_input"
        if missing
        else "ready",
        "previous": cached["previous"],
        "autofill": p.get("autofill", []),
        "dependencies": DEPENDENCIES.get(task, []),
    }


def path(person, job):
    if not isinstance(job, str) or not __import__("re").fullmatch(
        r"flow_[A-Za-z0-9_-]+", job
    ):
        raise ValueError("Invalid workflow ID")
    return suite_api.job_path(person, job)


def read(person, job):
    suite_api.checked_person(person)
    p = path(person, job)
    data = json.loads((p / "workflow.json").read_text(encoding="utf-8"))
    try:
        status = json.loads((p / "status.json").read_text(encoding="utf-8"))
        if data["state"] == "completed" and status.get("status") != "Complete":
            data["state"] = "needs_review"
    except (OSError, ValueError):
        pass
    with GUARD:
        live = ACTIVE == (person, job)
    if data["state"] == "running" and not live:
        data["state"] = "interrupted"
        data["notice"] = (
            "App/server stopped. Start again to reuse completed steps; no automatic restart."
        )
    return data


def overview(person):
    suite_api.checked_person(person)
    runs = []
    for f in sorted(
        (root() / "Projects/Launcher" / person).glob("flow_*/workflow.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:20]:
        try:
            runs.append(read(person, f.parent.name))
        except (OSError, ValueError):
            pass
    return {
        "recipes": [
            {"id": k, "title": v[0], "title_de": v[1], "icon": v[2], "steps": v[3]}
            for k, v in RECIPES.items()
        ],
        "runs": runs,
        "inheritance": inheritance_latest(person),
    }


def plan(person, recipe):
    suite_api.checked_person(person)
    if recipe not in RECIPES:
        raise ValueError("Unknown workflow")
    steps = []
    for task in RECIPES[recipe][3]:
        if task == "parent_origin":
            steps.append(
                {
                    "task": task,
                    "title": "Parental transmission evidence",
                    "tools": "Local trio SNP evidence",
                    "inputs": {},
                    "missing": [],
                    "status": "ready",
                    "dependencies": [],
                }
            )
        else:
            steps.append(task_plan(person, task, recipe))
    return {
        "person": person,
        "recipe": recipe,
        "steps": steps,
        "notice": "Missing reference panels, scores or tools remain explicit. Progress counts steps, not estimated runtime. No invented clinical, ancestry or family findings.",
    }


def assert_idle():
    with GUARD:
        if ACTIVE and OWNER != threading.get_ident():
            raise ValueError(
                "A shared workflow is running. Wait or cancel it before starting another tool."
            )


def start(person, recipe):
    import source_batch

    source_batch.assert_idle()
    global ACTIVE, OWNER
    import batch_intake

    batch_intake.assert_idle()
    profile_identity.assert_writable(person)
    p = plan(person, recipe)
    with GUARD:
        if ACTIVE:
            raise ValueError("A workflow is already running")
        if any(proc.poll() is None for proc in suite_api.PROCESSES.values()):
            raise ValueError("Wait for the running tool to finish")
        job = (
            "flow_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )
        folder = path(person, job)
        (folder / "Results").mkdir(parents=True)
        state = p | {
            "job": job,
            "state": "running",
            "created": now(),
            "completed": 0,
            "total": len(p["steps"]),
            "percent": 0,
            "log": [],
        }
        save(folder, state)
        ACTIVE = (person, job)
        threading.Thread(
            target=worker, args=(folder, state), daemon=True, name="SharedWorkflow"
        ).start()
    return {"person": person, "job": job}


def save(folder, state):
    from profile_pipeline import atomic

    atomic(folder / "workflow.json", state)
    terminal = state["state"] != "running"
    status = {
        "id": state["job"],
        "job": state["job"],
        "person": state["person"],
        "task": "workflow." + state["recipe"],
        "title": RECIPES[state["recipe"]][0],
        "kind": "analysis",
        "started": state["created"],
        "status": "Running"
        if not terminal
        else "Complete"
        if state["state"] == "completed"
        else "Cancelled"
        if state["state"] == "cancelled"
        else "Eingaben erforderlich",
        "progress": {
            "percent": state["percent"],
            "completed": state["completed"],
            "total": state["total"],
            "unit": "steps",
        },
    }
    if terminal:
        status.update(finished=now(), outputs=["workflow-summary.json"])
    atomic(folder / "status.json", status)
    if not (folder / "inputs.json").exists():
        import execution_journal

        atomic(
            folder / "inputs.json",
            {
                "person": state["person"],
                "task": status["task"],
                "inputs": {"recipe": state["recipe"]},
                "source_state": execution_journal.source_state(
                    [state["person"]], include_graph=True
                ),
            },
        )
    if terminal:
        atomic(folder / "Results/workflow-summary.json", state)
        import execution_journal

        execution_journal.register(folder)


def worker(folder, state):
    global ACTIVE, OWNER
    OWNER = threading.get_ident()
    person = state["person"]
    done = {}

    def log(text):
        state["log"].append(now() + " " + text)
        state["log"] = state["log"][-150:]
        (folder / "auftrag.log").write_text("\n".join(state["log"]), encoding="utf-8")
        save(folder, state)

    try:
        for i, old in enumerate(state["steps"]):
            if (folder / "abbrechen.request").exists():
                state["state"] = "cancelled"
                break
            step = (
                task_plan(person, old["task"], state["recipe"])
                if old["task"] != "parent_origin"
                else old
            )
            state["steps"][i] = step
            task = step["task"]
            if any(
                done.get(d) not in ("completed", "reused")
                for d in step.get("dependencies", [])
            ):
                step.update(
                    status="blocked", error="A required predecessor is not completed."
                )
                log(task + ": waiting for predecessor")
                done[task] = "blocked"
                continue
            if step["status"] == "reusable":
                step["status"] = "reused"
                step["job"] = step["previous"]["job"]
                log(task + ": reused " + step["job"])
            elif step["missing"]:
                step.update(
                    status="needs_input", error="Missing: " + ", ".join(step["missing"])
                )
                log(task + ": " + step["error"])
            else:
                step["status"] = "running"
                log(task + ": starting " + step["tools"])
                try:
                    if task == "parent_origin":
                        import execution_journal

                        result = execution_journal.execute(
                            "inheritance.calculate",
                            {"person": person},
                            lambda args: parent_origin(args["person"]),
                        )
                        step.update(
                            status="completed", result_summary=result.get("summary")
                        )
                    else:
                        dep = __import__("on_demand").status(task)
                        if not dep["ready"]:
                            raise ValueError(
                                "Tool/service not ready. Use Check dependencies in the step window; no automatic large downloads."
                            )
                        child = suite_api.start(
                            {
                                "person": person,
                                "task": task,
                                "inputs": step["inputs"],
                                "sources": [{"workflow": state["job"], "step": task}],
                            }
                        )
                        step["job"] = child["job"]
                        save(folder, state)
                        while True:
                            proc = suite_api.PROCESSES.get(child["job"])
                            if proc is None or proc.poll() is not None:
                                break
                            if (folder / "abbrechen.request").exists():
                                (
                                    suite_api.job_path(person, child["job"])
                                    / "abbrechen.request"
                                ).touch()
                            time.sleep(0.5)
                        s = json.loads(
                            (
                                suite_api.job_path(person, child["job"]) / "status.json"
                            ).read_text(encoding="utf-8")
                        )
                        if s["status"] != "Complete":
                            raise ValueError(s.get("error") or s["status"])
                        step["status"] = (
                            "reused" if child["status"] == "cached" else "completed"
                        )
                    log(task + ": " + step["status"])
                except Exception as error:
                    step.update(status="needs_attention", error=str(error))
                    log(task + ": " + str(error))
            done[task] = step["status"]
            state["completed"] = sum(
                x.get("status") in ("completed", "reused") for x in state["steps"]
            )
            state["percent"] = round(100 * state["completed"] / state["total"])
            save(folder, state)
        if state["state"] == "running":
            state["state"] = (
                "completed"
                if state["completed"] == state["total"]
                else "needs_attention"
            )
    except Exception as error:
        state.update(state="needs_attention", error=str(error))
        log(str(error))
    finally:
        save(folder, state)
        with GUARD:
            ACTIVE = None
            OWNER = None


def cancel(person, job):
    read(person, job)
    (path(person, job) / "abbrechen.request").touch()
    return {"requested": True}


def inheritance_latest(person):
    with contextlib.closing(source_store.connect(person)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS inheritance_evidence(id TEXT PRIMARY KEY,created TEXT,payload TEXT)"
        )
        rows = db.execute(
            "SELECT payload FROM inheritance_evidence ORDER BY created DESC LIMIT 1"
        ).fetchall()
        db.commit()
    if not rows:
        return None
    r = json.loads(rows[0][0])
    import execution_journal

    people = [x["person"] for x in r.get("source_state", {}).get("profiles", [])]
    active = False
    with contextlib.closing(source_store.connect(person)) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='tool_runs'").fetchone():
            for (job,) in db.execute(
                "SELECT id FROM tool_runs WHERE command='inheritance.calculate' AND status='Complete'"
            ):
                f = (
                    root()
                    / "Projects/Launcher"
                    / person
                    / job
                    / "Results/tool-result.json"
                )
                try:
                    if json.loads(f.read_text(encoding="utf-8")).get("id") == r.get(
                        "id"
                    ):
                        active = True
                        break
                except (OSError, ValueError):
                    pass
    r["current"] = active and r.get("source_state") == execution_journal.source_state(
        people, include_graph=True
    )
    return r


def parent_origin(person):
    """Bounded, unambiguous high-quality autosomal trio alleles. Never a full phase."""
    import family, execution_journal

    with family.connect() as db:
        links = [
            dict(x)
            for x in db.execute(
                "SELECT * FROM links WHERE b=? AND kind IN ('mother','father')",
                (person,),
            )
        ]
    parents = {
        role: [l["a"] for l in links if l["kind"] == role]
        for role in ("mother", "father")
    }
    result = {
        "person": person,
        "created": now(),
        "parents": parents,
        "maternal_line": family.lineage(person, "mother"),
        "paternal_line": family.lineage(person, "father"),
        "rules": {
            "mitochondrial": "Normally maternal in sons and daughters; lineage expectation, not a copied measured genotype.",
            "Y": "Normally father to son where Y is measured; daughters normally do not inherit Y.",
            "X": "A son normally receives X from mother; a daughter normally receives one X from each parent.",
        },
        "loci": [],
        "summary": "No complete measured trio available. Lineage expectations only.",
    }
    people = [person] + [ids[0] for ids in parents.values() if len(ids) == 1]
    result["source_state"] = execution_journal.source_state(people, include_graph=True)

    def calls(pid):
        allowed = {
            x["id"]
            for x in source_store.listing(pid)
            if x.get("measurement") == "Measured"
            and x.get("qc_color") not in ("red", "black")
            and x.get("lifecycle") != "needs_review"
            and not x.get("qc_review_required")
        }
        out = {}
        bad = set()
        with contextlib.closing(source_store.connect(pid)) as db:
            cursor = db.execute(
                "SELECT file_id,build,chrom,pos,ref,alt,gt,dp,gq,filter FROM calls WHERE filter='PASS' AND CAST(dp AS REAL)>=10 AND CAST(gq AS REAL)>=20 ORDER BY build,chrom,pos LIMIT 200001"
            )
            for fid, build, chrom, pos, ref, alt, gt, dp, gq, filt in cursor:
                chrom = chrom.removeprefix("chr")
                if fid not in allowed or chrom not in {str(x) for x in range(1, 23)}:
                    continue
                try:
                    indices = [int(x) for x in gt.replace("|", "/").split("/")]
                    if any(x < 0 for x in indices):
                        continue
                    bases = [([ref] + alt.split(","))[x] for x in indices]
                except (ValueError, IndexError):
                    continue
                if len(bases) != 2 or any(x not in ("A", "C", "G", "T") for x in bases):
                    continue
                key = (build, chrom, pos, ref)
                value = tuple(sorted(bases))
                if key in out and out[key] != value:
                    bad.add(key)
                out[key] = value
        return {k: v for k, v in out.items() if k not in bad}

    if all(len(x) == 1 for x in parents.values()) and len(set(people)) == 3:
        child, mother, father = [
            calls(x) for x in [person, parents["mother"][0], parents["father"][0]]
        ]
        common = child.keys() & mother.keys() & father.keys()
        conflict = ambiguous = 0
        for key in sorted(common):
            pairs = {
                (m, f)
                for m in mother[key]
                for f in father[key]
                if tuple(sorted((m, f))) == child[key]
            }
            if len(pairs) == 1:
                m, f = next(iter(pairs))
                result["loci"].append(
                    {
                        "build": key[0],
                        "chrom": key[1],
                        "pos": key[2],
                        "ref": key[3],
                        "maternal_allele": m,
                        "paternal_allele": f,
                    }
                )
            elif not pairs:
                conflict += 1
            else:
                ambiguous += 1
        result.update(
            summary=f"{len(result['loci'])} unambiguous trio SNPs; {ambiguous} ambiguous; {conflict} incompatible. Bounded indexed subset, not genome-wide phasing.",
            common_loci=len(common),
            ambiguous=ambiguous,
            incompatible=conflict,
        )
    result["id"] = uuid.uuid4().hex
    with contextlib.closing(source_store.connect(person)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS inheritance_evidence(id TEXT PRIMARY KEY,created TEXT,payload TEXT)"
        )
        db.execute(
            "INSERT INTO inheritance_evidence VALUES(?,?,?)",
            (result["id"], result["created"], json.dumps(result)),
        )
        db.commit()
    return result
