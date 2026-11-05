"""Refresh unsigned local integrity metadata from the explicit public allowlist."""

import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
app = root / "DNA_Software/Launcher"
sys.path.insert(0, str(app))
import public_package

rows = [
    {"path": target, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    for source, target in public_package.entries()
    if not target.endswith("/release-integrity.json")
]
version = json.loads((app / "install-lock.json").read_text(encoding="utf-8"))[
    "app_version"
]
(app / "release-integrity.json").write_text(
    json.dumps({"version": version, "files": rows}, indent=2), encoding="utf-8"
)
manifest = [
    {"path": target, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    for source, target in public_package.entries()
]
for source, target in public_package.presentation_entries():
    manifest.append(
        {"path": target, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    )
(root / "source-manifest.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(f"Sealed {len(rows)} allowlisted files. Checksums are not publisher signatures.")
