"""Small JSON state writes survive interrupted replacement without truncating live files.

Copyright 2026 Oktay Du / OD. PolyForm Noncommercial 1.0.0.
"""

from pathlib import Path
import json
import os
import threading
import uuid

LOCK = threading.RLock()


def write(path, value, backup=False):
    path = Path(path)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode(
        "utf-8"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK:
        if path.is_symlink():
            raise ValueError("Refusing a linked JSON destination")
        previous = path.with_name(path.name + ".bak")
        if backup and previous.is_symlink():
            raise ValueError("Refusing a linked backup destination")
        temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
        backup_temp = temp.with_suffix(".backup-partial")
        try:
            with temp.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if temp.read_bytes() != payload:
                raise OSError("JSON write read-back mismatch; existing state preserved")
            if backup and path.exists():
                old = path.read_bytes()
                json.loads(old)
                if old != payload:
                    with backup_temp.open("xb") as stream:
                        stream.write(old)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(backup_temp, previous)
            os.replace(temp, path)
            if os.name != "nt":
                directory = os.open(
                    path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                )
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            temp.unlink(missing_ok=True)
            backup_temp.unlink(missing_ok=True)
