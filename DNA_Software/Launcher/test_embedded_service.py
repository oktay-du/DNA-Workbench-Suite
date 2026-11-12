"""Check embedded service readiness and owner-pipe shutdown, without DNA reads."""

from pathlib import Path
import json, shutil, subprocess, sys, tempfile, time, urllib.request
from urllib.error import HTTPError
import public_package

with tempfile.TemporaryDirectory() as folder:
    info = Path(folder) / "service.json"
    root = Path(folder) / "isolated suite"
    for source, target in public_package.entries():
        destination = root / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    proc = subprocess.Popen(
        [
            sys.executable,
            str(root / "DNA_Software/Launcher/family.py"),
            "--embedded",
            str(info),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(100):
            if info.exists():
                break
            if proc.poll() is not None:
                raise RuntimeError(proc.stderr.read().decode())
            time.sleep(0.1)
        config = json.loads(info.read_text())
        with urllib.request.urlopen(config["url"] + "/visual", timeout=5) as response:
            assert response.status == 200
            assert (
                "<title>DNA · Origin and appearance</title>" in response.read().decode()
            )
        with urllib.request.urlopen(
            config["url"] + "/Locales/de.json", timeout=20
        ) as response:
            assert json.loads(response.read())["Settings"] == "Einstellungen"
        with urllib.request.urlopen(
            config["url"] + "/Locales/languages.json", timeout=20
        ) as response:
            assert len(json.loads(response.read())) == 36
        with urllib.request.urlopen(
            config["url"] + "/Locales/flags/tr.svg", timeout=20
        ) as response:
            assert response.headers.get_content_type() == "image/svg+xml"
        try:
            urllib.request.urlopen(config["url"] + "/Locales/unknown.json", timeout=20)
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("An unregistered language asset was served")
        proc.stdin.close()
        proc.wait(timeout=8)
        assert proc.returncode == 0
        print(
            "OK: Start signal, internal HTML view, clean stop when closing the EXE connection."
        )
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=8)
