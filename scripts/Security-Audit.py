"""Scan production Python and declared dependency pins without installing optional tools."""

from pathlib import Path
import argparse
import collections
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def review_identity(issue):
    path = Path(issue["filename"]).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Finding outside the checkout")
    code = "\n".join(re.sub(r"^\d+\s", "", line) for line in issue["code"].splitlines())
    return (
        path.relative_to(ROOT).as_posix(),
        issue["test_id"],
        hashlib.sha256(code.encode()).hexdigest(),
    )


def reviewed(issue, reviews):
    key = review_identity(issue)
    digest = hashlib.sha256((ROOT / key[0]).read_bytes()).hexdigest()
    return any(
        (row["path"], row["rule"], row["code_sha256"]) == key
        and row["file_sha256"] == digest
        and row.get("reason")
        and row.get("tests")
        for row in reviews
    )


def sarif_identity(issue):
    location = issue["locations"][0]["physicalLocation"]
    name = location["artifactLocation"]["uri"]
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("SARIF path outside checkout")
    region = location["region"]
    lines = path.read_text(encoding="utf-8").splitlines()
    code = "\n".join(
        lines[region["startLine"] - 1 : region.get("endLine", region["startLine"])]
    )
    return (
        path.relative_to(ROOT).as_posix(),
        issue["ruleId"],
        hashlib.sha256(code.encode()).hexdigest(),
    )


def reviewed_sarif(issue, reviews):
    key = sarif_identity(issue)
    digest = hashlib.sha256((ROOT / key[0]).read_bytes()).hexdigest()
    return any(
        row.get("tool") == "Bearer"
        and (row["path"], row["rule"], row["code_sha256"]) == key
        and row["file_sha256"] == digest
        and row.get("reason")
        and row.get("tests")
        for row in reviews
    )


def bandit_sarif(report):
    rules = {}
    findings = []
    for issue in report["results"]:
        path = Path(issue["filename"]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Scanner returned a location outside the source checkout")
        uri = path.relative_to(ROOT).as_posix()
        rule = issue["test_id"]
        severity = issue["issue_severity"]
        rules[rule] = {
            "id": rule,
            "name": issue["test_name"],
            "shortDescription": {"text": issue["test_name"]},
            "helpUri": issue["more_info"],
            "properties": {
                "security-severity": {"HIGH": "8.0", "MEDIUM": "5.0", "LOW": "2.0"}[
                    severity
                ]
            },
        }
        findings.append(
            {
                "ruleId": rule,
                "level": {"HIGH": "error", "MEDIUM": "warning", "LOW": "note"}[
                    severity
                ],
                "message": {"text": issue["issue_text"]},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": uri},
                            "region": {"startLine": max(1, issue["line_number"])},
                        }
                    }
                ],
                "partialFingerprints": {
                    "dnaWorkbenchExactSourceHash/v1": hashlib.sha256(
                        (uri + rule + issue["code"].strip()).encode()
                    ).hexdigest()
                },
            }
        )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Bandit",
                        "version": importlib.metadata.version("bandit"),
                        "informationUri": "https://bandit.readthedocs.io/",
                        "rules": list(rules.values()),
                    }
                },
                "results": findings,
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--bearer", type=Path, help="Checksum-verified local Bearer binary"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "bandit_version": importlib.metadata.version("bandit"),
        "pip_audit_version": importlib.metadata.version("pip-audit"),
        "scope": "Production Python and scripts; pinned Python requirements. Optional tools are not installed. Dependency resolution is disabled, so only explicitly declared pins are audited.",
        "dependency_reports": [],
        "errors": [],
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "DNA_Software/Launcher",
            "scripts",
            "fuzz",
            "-x",
            "*/test_*.py,*/__pycache__/*",
            "--ignore-nosec",
            "-f",
            "json",
            "-o",
            str(output / "bandit.json"),
        ],
        cwd=ROOT,
    )
    if result.returncode not in (0, 1) or not (output / "bandit.json").exists():
        raise RuntimeError("Bandit did not produce a usable scan")
    report = json.loads((output / "bandit.json").read_text(encoding="utf-8"))
    summary["errors"].extend(report.get("errors", []))
    summary["bandit_by_severity"] = dict(
        collections.Counter(issue["issue_severity"] for issue in report["results"])
    )
    ledger = ROOT / "security/ReviewedFindings.json"
    reviews = (
        json.loads(ledger.read_text(encoding="utf-8"))["findings"]
        if ledger.is_file()
        else []
    )
    unresolved = [issue for issue in report["results"] if not reviewed(issue, reviews)]
    summary["reviewed_findings"] = len(report["results"]) - len(unresolved)
    summary["unreviewed_by_severity"] = dict(
        collections.Counter(issue["issue_severity"] for issue in unresolved)
    )
    write(output / "bandit.sarif", bandit_sarif(report))
    if args.bearer:
        target = output / "bearer.sarif"
        target.unlink(missing_ok=True)
        scan = subprocess.run(
            [
                str(args.bearer.resolve()),
                "scan",
                str(ROOT),
                "--disable-version-check",
                "--disable-domain-resolution",
                "--force",
                "--hide-progress-bar",
                "--no-color",
                "--parallel",
                "2",
                "--skip-path",
                "DNA_Software/UserData,Projects,DNAWorkbench_Source,DNAWorkbench_Release,security-tools,security-reports,quality-reports,fuzz-artifacts,tools/quality/node_modules,tools/quality/.cache",
                "--format",
                "sarif",
                "--output",
                str(target),
            ],
            cwd=ROOT,
        )
        if scan.returncode not in (0, 1) or not target.is_file():
            summary["errors"].append("Bearer failed to produce a usable report")
        else:
            bearer = json.loads(target.read_text(encoding="utf-8"))
            findings = [
                item for run in bearer["runs"] for item in run.get("results", [])
            ]
            pending = [item for item in findings if not reviewed_sarif(item, reviews)]
            summary["bearer_findings"] = len(findings)
            summary["bearer_reviewed"] = len(findings) - len(pending)
            if pending:
                summary["errors"].append(
                    str(len(pending)) + " unreviewed Bearer findings"
                )
    requirements = [
        ROOT / "requirements-dev.txt",
        ROOT / "requirements-security.txt",
        ROOT / "requirements-quality.txt",
        ROOT / "requirements-fuzz.txt",
        *sorted((ROOT / "DNA_Software/Launcher/Locks").glob("*.txt")),
    ]
    for index, requirement in enumerate(requirements):
        target = output / f"pip-audit-{index:02d}.json"
        target.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--no-deps",
                "--disable-pip",
                "--progress-spinner",
                "off",
                "-r",
                str(requirement),
                "-f",
                "json",
                "-o",
                str(target),
            ],
            cwd=ROOT,
        )
        if result.returncode not in (0, 1) or not target.exists():
            summary["errors"].append(
                "Dependency audit failed: " + requirement.relative_to(ROOT).as_posix()
            )
            continue
        data = json.loads(target.read_text(encoding="utf-8"))
        skipped = [item for item in data["dependencies"] if item.get("skip_reason")]
        summary["errors"].extend(
            "Unaudited package: " + item["name"] + " / " + item["skip_reason"]
            for item in skipped
        )
        summary["dependency_reports"].append(
            {
                "requirements": requirement.relative_to(ROOT).as_posix(),
                "report": target.name,
                "vulnerabilities": sum(
                    len(item.get("vulns", [])) for item in data["dependencies"]
                ),
                "packages": len(data["dependencies"]),
            }
        )
    write(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    if summary["errors"]:
        return 2
    return (
        1
        if unresolved
        or any(row["vulnerabilities"] for row in summary["dependency_reports"])
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
