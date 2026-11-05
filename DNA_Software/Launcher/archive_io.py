"""Bounded, source-preserving ZIP/TAR and single-stream extraction.
7z/RAR/Zstandard are recognized but require an explicitly installed adapter.
"""

from pathlib import PurePosixPath
import zipfile, tarfile, gzip, bz2, lzma, shutil, stat
import tool_contracts, security_paths


def unpack(path, destination, cancel=lambda: False):
    path = security_paths.input_file(path)
    dest = security_paths.local_path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    meta = tool_contracts.probe(path)
    pack = meta["compression"]
    limit = max(0, shutil.disk_usage(dest).free - 1024**3)
    written = 0
    names = set()
    mapping = {}

    def safe(name):
        p = PurePosixPath(name)
        if (
            p.is_absolute()
            or ".." in p.parts
            or "\\" in name
            or ":" in name
            or any(c in name for c in ("\x00",))
        ):
            raise ValueError("Unsafe archive member path.")
        if not p.name or str(p).casefold() in names:
            raise ValueError("Colliding archive member paths.")
        names.add(str(p).casefold())
        return p

    def write(name, stream, size=None):
        nonlocal written
        p = safe(name)
        # Keep both outer context and inner name. Preserve directory paths and sidecar stems.
        outer = path.name
        for suffix in (
            ".tar.gz",
            ".tar.bz2",
            ".tar.xz",
            ".zip",
            ".tgz",
            ".tbz2",
            ".txz",
            ".tar",
            ".gz",
            ".bgz",
            ".bz2",
            ".xz",
        ):
            if outer.lower().endswith(suffix):
                outer = outer[: -len(suffix)]
                break
        contextual = (outer + "__" + p.name) if outer != p.name else p.name
        if len(contextual) > 220:
            raise ValueError(
                "Combined archive/payload filename is too long; rename the outer archive before extraction."
            )
        target = security_paths.contained(
            dest, PurePosixPath(*p.parts[:-1], contextual).as_posix()
        )
        if not target.resolve().is_relative_to(dest.resolve()):
            raise ValueError("Unsafe extraction destination.")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError(
                "Extracted destination already exists; no overwrite performed."
            )
        part = target.with_name(target.name + ".extracting")
        count = 0
        try:
            with part.open("xb") as out:
                while block := stream.read(8 * 1024**2):
                    if cancel():
                        raise InterruptedError(
                            "Extraction cancelled; original archive retained."
                        )
                    count += len(block)
                    written += len(block)
                    if written > limit or written > max(path.stat().st_size, 1) * 2000:
                        raise ValueError(
                            "Archive expansion exceeds free-space or expansion safety limit."
                        )
                    out.write(block)
            if size is not None and count != size:
                raise ValueError("Incomplete extracted member.")
            part.rename(target)
            mapping[str(target)] = str(p)
        except BaseException:
            part.unlink(missing_ok=True)
            raise

    if pack == "zip":
        with zipfile.ZipFile(path) as z:
            members = [m for m in z.infolist() if not m.is_dir()]
            if len(members) > 10000:
                raise ValueError("Archive exceeds 10,000 members.")
            for m in members:
                if stat.S_ISLNK(m.external_attr >> 16) or m.flag_bits & 1:
                    raise ValueError(
                        "Encrypted or linked ZIP members require manual review."
                    )
                with z.open(m) as stream:
                    write(m.filename, stream, m.file_size)
    elif pack == "tar" or meta.get("container") == "tar":
        with tarfile.open(path, "r:*") as z:
            count = 0
            for m in z:
                count += 1
                if count > 10000:
                    raise ValueError("Archive exceeds 10,000 members.")
                if m.isdir():
                    continue
                if not m.isfile():
                    raise ValueError("Archive links/devices are not allowed.")
                with z.extractfile(m) as stream:
                    write(m.name, stream, m.size)
    elif pack in ("gzip", "bgzf", "bzip2", "xz"):
        opener = {
            "gzip": gzip.open,
            "bgzf": gzip.open,
            "bzip2": bz2.open,
            "xz": lzma.open,
        }[pack]
        name = path.name.rsplit(".", 1)[0]
        with opener(path, "rb") as stream:
            write(name, stream)
    else:
        raise ValueError(
            "Recognized compression "
            + pack
            + " has no installed portable extraction adapter. Decode locally to ZIP/TAR or regular files; original retained."
        )
    if not mapping:
        raise ValueError("Archive has no regular payloads.")
    return mapping
