# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Required Notice: Copyright 2026 Oktay Du / OD — DNA Workbench
"""Local, opt-in issue drafts. Never submit reports or read genome/report payloads."""

from pathlib import Path
import builtins, json, platform, re

APP = Path(__file__).resolve().parent
ROOT = APP.parents[1]
ISSUES = "https://github.com/oktay-du/DNA-Workbench-Suite/issues/new"
EXCEPTIONS = re.compile(
    r"\b(?:[A-Za-z]{1,40}(?:Error|Exception)|KeyboardInterrupt|SystemExit)\b"
)


EXCEPTION_TYPES = {
    name
    for name in dir(builtins)
    if isinstance(getattr(builtins, name), type)
    and issubclass(getattr(builtins, name), BaseException)
} | {
    "InvalidOperationException",
    "IOException",
    "UnauthorizedAccessException",
    "ArgumentException",
    "ArgumentNullException",
    "FileNotFoundException",
    "DirectoryNotFoundException",
    "Win32Exception",
    "ExternalException",
    "NullReferenceException",
    "TimeoutException",
    "MissingMethodException",
    "TypeLoadException",
    "BadImageFormatException",
    "OutOfMemoryException",
    "ObjectDisposedException",
    "COMException",
}


def filtered_log(text):
    """Retain exception types only, never untrusted messages, paths or source lines."""
    counts = {}
    for line in text.splitlines():
        for kind in EXCEPTIONS.findall(line):
            if kind in EXCEPTION_TYPES:
                counts[kind] = counts.get(kind, 0) + 1
    return (
        "\n".join(
            f"{kind}: {count} occurrence(s); details omitted"
            for kind, count in sorted(counts.items())
        )
        or "No recognized exception types in the selected log tail."
    )


def diagnostics(person="", job=""):
    info = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))
    result = {
        "app_version": info["app_version"],
        "os": platform.system(),
        "architecture": platform.machine(),
        "log_policy": "Exception types only; no raw logs, paths, profile names, genotypes, report text or credentials.",
    }
    if bool(person) != bool(job):
        raise ValueError("Select both a profile and a job, or neither")
    if job:
        import suite_api

        folder = suite_api.job_path(person, job)
        errors = []
        for name in ("auftrag.log", "startfehler.log", "dienst.log"):
            path = folder / name
            if path.is_file() and not path.is_symlink():
                with path.open("rb") as stream:
                    stream.seek(max(0, path.stat().st_size - 32768))
                    errors.append(
                        filtered_log(
                            stream.read(32768).decode("utf-8", errors="replace")
                        )
                    )
        result["selected_job_log"] = errors or ["No local logs available."]
    crash = ROOT / "DNA_Software/UserData/Launcher/Diagnostics/last-crash.json"
    if crash.is_file() and not crash.is_symlink():
        try:
            d = json.loads(crash.read_text(encoding="utf-8-sig"))
            kind = str(d.get("exception_type", "")).split(".")[-1]
            if kind in EXCEPTION_TYPES:
                result["last_crash_type"] = kind
        except (OSError, ValueError):
            pass
    return result


def draft(args):
    kind = args.get("kind", "bug")
    if kind not in ("bug", "improvement"):
        raise ValueError("Unknown feedback kind")
    title = str(args.get("title", "")).strip()
    description = str(args.get("description", "")).strip()
    if not title or len(title) > 160 or not description or len(description) > 12000:
        raise ValueError(
            "Use a title up to 160 characters and a description up to 12000 characters"
        )
    # A draft is returned only to the local caller; user text is never put in an external URL.
    text = (
        "## "
        + ("Bug report" if kind == "bug" else "Improvement request")
        + "\n\n"
        + title
        + "\n\n"
        + description
    )
    if args.get("include_log", False):
        data = diagnostics(args.get("person", ""), args.get("job", ""))
        text += (
            "\n\n## Optional privacy-filtered diagnostics\n\n```json\n"
            + json.dumps(data, indent=2)
            + "\n```"
        )
    text += "\n\nPlease review before posting. Do not include DNA, medical reports, keys, names or unredacted screenshots."
    return {
        "text": text,
        "issue_url": ISSUES
        + "?template="
        + ("bug_report.yml" if kind == "bug" else "feature_request.yml"),
        "submitted": False,
        "includes_log": bool(args.get("include_log", False)),
    }


def notices():
    data = json.loads((APP / "project-notices.json").read_text(encoding="utf-8"))
    data["license_text"] = (APP / "Notices/POLYFORM-NONCOMMERCIAL-1.0.0.md").read_text(
        encoding="utf-8"
    )
    data["legacy_license_text"] = (APP / "Notices/LEGACY-MIT-LICENSE.txt").read_text(
        encoding="utf-8"
    )
    return data


def licenses():
    return json.loads((APP / "third-party-inventory.json").read_text(encoding="utf-8"))
