"""Measure the job view using synthetic profiles in a disposable workspace."""

import argparse
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "DNA_Software/Launcher"))
import family
import profile_transfer
import source_store
import suite_api


def benchmark(profiles=8, jobs=12, repeats=3):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with (
            patch.object(family, "ROOT", root),
            patch.object(family, "DB", root / "family.sqlite"),
            patch.object(source_store, "ROOT", root),
            patch.object(suite_api, "ROOT", root),
            patch.object(profile_transfer, "jobs", return_value=[]) as transfers,
        ):
            with family.connect() as db:
                for index in range(profiles):
                    person = "BENCH_" + str(index)
                    db.execute(
                        "INSERT INTO people VALUES(?,?,1)",
                        (person, "Synthetic benchmark " + str(index)),
                    )
                    for number in range(jobs):
                        folder = (
                            root / "Projects/Launcher" / person / ("job_" + str(number))
                        )
                        folder.mkdir(parents=True)
                        (folder / "status.json").write_text(
                            json.dumps(
                                {
                                    "task": "vcf_qc",
                                    "status": "Complete",
                                    "started": "2026-01-01T00:00:00",
                                }
                            ),
                            encoding="utf-8",
                        )
            timings = []
            original = suite_api.profiles
            with patch.object(suite_api, "profiles", wraps=original) as reads:
                for _ in range(repeats):
                    started = time.perf_counter()
                    result = suite_api.all_jobs()
                    timings.append((time.perf_counter() - started) * 1000)
                    if len(result) != profiles * jobs:
                        raise AssertionError("The job view lost synthetic results")
            return {
                "profiles": profiles,
                "jobs": profiles * jobs,
                "repeats": repeats,
                "median_ms": round(statistics.median(timings), 3),
                "profile_reads_per_render": reads.call_count / repeats,
                "transfer_reads_per_render": transfers.call_count / repeats,
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark()
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
