"""Documented one-line compatibility patch for MIT-licensed Peddy 0.4.8.

Peddy reads a bytes buffer as uint8 then copies to int32. np.frombuffer has
the same binary interpretation without the removed binary np.fromstring API.
No genotype inference, filtering or prediction model is changed.
"""

from pathlib import Path
import os, uuid
import datetime, hashlib, importlib.metadata, importlib.util, json


def durable(path, data):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def apply():
    if importlib.metadata.version("peddy") != "0.4.8":
        raise ValueError("Compatibility patch is tested for Peddy 0.4.8 only.")
    package = Path(
        next(iter(importlib.util.find_spec("peddy").submodule_search_locations))
    )
    path = package / "pca.py"
    receipt = package / "dna-workbench-compatibility.json"
    original = path.read_bytes()
    text = original.decode("utf-8")
    old = "np.fromstring(gzip.open(f, 'rb').read(), dtype=np.uint8)"
    new = "np.frombuffer(gzip.open(f, 'rb').read(), dtype=np.uint8)"
    if old not in text:
        if receipt.is_file():
            try:
                rec = json.loads(receipt.read_text(encoding="utf-8"))
                if (
                    new in text
                    and rec["modified_sha256"] == hashlib.sha256(original).hexdigest()
                ):
                    return rec
            except (ValueError, KeyError):
                pass
        # Recover metadata after an interrupted SSD write, only for the exact
        # known patched bytes and a reversible original with the expected hash.
        if (
            hashlib.sha256(original).hexdigest()
            == "56a05fd56722cc26b87de6640bd55dc7dc640481f4da7a91139f858b7a14804b"
            and text.count(new) == 1
        ):
            restored = text.replace(new, old).encode("utf-8")
            if (
                hashlib.sha256(restored).hexdigest()
                == "b03317d26f78e7cff85aeb740285e2c4bcf4da06d47b61f88bf7336c62fc9df4"
            ):
                durable(path, restored)
                return apply()
        raise ValueError("Unexpected peddy source level; no automatic patch applied.")
    if (
        hashlib.sha256(original).hexdigest()
        != "b03317d26f78e7cff85aeb740285e2c4bcf4da06d47b61f88bf7336c62fc9df4"
    ):
        raise ValueError(
            "Peddy file deviates from the tested PyPI source level; not changed."
        )
    if text.count(old) != 1:
        raise ValueError("Unexpected number of API calls to be corrected.")
    backup = package / "pca.py.before-dna-workbench"
    durable(backup, original)
    modified = text.replace(old, new).encode("utf-8")
    durable(path, modified)
    rec = {
        "tool": "peddy",
        "version": "0.4.8",
        "patch": "binary-numpy-frombuffer-1",
        "changed": datetime.datetime.now().astimezone().isoformat(),
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "modified_sha256": hashlib.sha256(modified).hexdigest(),
        "source": "https://github.com/brentp/peddy/blob/v0.4.8/peddy/pca.py",
        "license": "MIT",
        "note": "One binary buffer reader API replacement. No model or genotype rules changed.",
    }
    durable(receipt, json.dumps(rec, indent=2).encode("utf-8"))
    return rec


if __name__ == "__main__":
    print(json.dumps(apply()))
