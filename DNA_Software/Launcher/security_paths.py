"""Filesystem boundaries for managed metadata and explicitly selected local inputs."""

from pathlib import Path, PurePosixPath
import os
import re


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", value):
        raise ValueError("Invalid managed identifier")
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", value):
        raise ValueError("Reserved managed identifier")
    return value


def _no_links(path, stop=None):
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError("Linked paths are not supported at this boundary")
        if stop is not None and part == stop:
            break


def local_path(value):
    if not isinstance(value, (str, os.PathLike)):
        raise ValueError("Expected a local filesystem path")
    text = os.fspath(value)
    if not isinstance(text, str) or not text or len(text) > 32767 or "\x00" in text:
        raise ValueError("Invalid local path")
    if (
        text.startswith(("\\\\", "//"))
        or "://" in text
        or re.match(r"^[A-Za-z]:[^\\/]", text)
    ):
        raise ValueError(
            "Network, device, URL and drive-relative paths are not accepted"
        )
    path = Path(text).expanduser().absolute()
    _no_links(path)
    return path.resolve()


def input_file(value):
    path = local_path(value)
    if not path.is_file():
        raise ValueError("Select an existing regular local file")
    return path


def input_directory(value):
    path = local_path(value)
    if not path.is_dir():
        raise ValueError("Select an existing local directory")
    return path


def contained(base, relative):
    """Resolve an untrusted relative artifact name below one known directory."""
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
        or "\x00" in relative
    ):
        raise ValueError("Invalid relative artifact path")
    parts = PurePosixPath(relative)
    if (
        parts.is_absolute()
        or ".." in parts.parts
        or any(part in ("", ".") for part in relative.split("/"))
    ):
        raise ValueError("Artifact path must stay within its directory")
    base = Path(base).absolute()
    _no_links(base)
    target = base.joinpath(*parts.parts)
    _no_links(target, base)
    resolved = target.resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("Artifact path escapes its directory")
    return resolved


def profile_jobs(root, person):
    return contained(Path(root) / "Projects/Launcher", identifier(person))


def job(root, person, job_id):
    return contained(profile_jobs(root, person), identifier(job_id))
