"""Register converted variants with parent lineage; never another measurement."""

from contextlib import closing
import os, json, datetime
import source_store, inspector


def register(
    person, parent_sha, job, provider, measurement, log=print, operation="chip_vcf"
):
    out = source_store.ROOT / "Projects/Launcher" / person / job / "Results"
    parent = next(
        (r for r in source_store.listing(person) if r["sha256"] == parent_sha), {}
    )
    root_sha = (
        parent.get("source_root_sha256") or parent.get("container_sha256") or parent_sha
    )
    paths = []
    for src in out.glob("*.vcf*"):
        if source_store.classify(src.name) != "VCF":
            continue
        dest = (
            source_store.profile_dir(person)
            / "Sources"
            / source_store.safe_name(provider)
            / "Derived"
            / job
            / src.name
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dest)
        except OSError:
            raise ValueError(
                "Converted source remains in its job folder; managed registration requires a same-volume hard link. No automatic extra genome copy."
            )
        r = source_store.import_batch(
            person,
            [str(dest)],
            provider,
            "Derived conversion " + job,
            storage_mode="move",
            log=log,
        )
        row = next(x for x in source_store.listing(person) if x["id"] == r["ids"][0])
        detail = inspector.inspect(row["path"], log)
        with closing(source_store.connect(person)) as db:
            db.execute(
                "INSERT OR REPLACE INTO source_metadata VALUES(?,?,?)",
                (
                    row["id"],
                    json.dumps(
                        {
                            "source_root_sha256": root_sha,
                            "parent_sha256": parent_sha,
                            "operation": operation,
                            "job": job,
                            "measurement": measurement,
                            "declared_version": "Derived / " + job,
                            "provenance": "Converted representation of parent source; not independent",
                        }
                    ),
                    datetime.datetime.now().astimezone().isoformat(),
                ),
            )
            db.execute(
                "INSERT OR REPLACE INTO inspections VALUES(?,?,?)",
                (
                    row["sha256"],
                    json.dumps(detail),
                    datetime.datetime.now().astimezone().isoformat(),
                ),
            )
            db.commit()
        paths.append(
            {"id": row["id"], "path": row["path"], "parent_sha256": parent_sha}
        )
    return paths
