from system_tools import windows_executable
import network_io
from pathlib import Path
import re, json, hashlib, subprocess

root = Path(__file__).resolve().parents[2]
page = "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
html = network_io.open_https(page, timeout=40).read().decode()
match = re.search(
    r'"(https:[^"<>]+Microsoft\.WebView2\.FixedVersionRuntime\.[0-9.]+\.x64\.cab)"',
    html,
)
if not match:
    raise RuntimeError("Official download link not found.")
url = json.loads('"' + match[1] + '"')
name = url.rsplit("/", 1)[-1]
folder = root / "DNA_Software/Downloads/WebView2"
folder.mkdir(parents=True, exist_ok=True)
cab = folder / name
part = cab.with_suffix(".cab.partial")
sha = hashlib.sha256()
total = 0
with network_io.open_https(url, timeout=90) as response, part.open("wb") as out:
    expected = int(response.headers.get("Content-Length", 0))
    while True:
        chunk = response.read(8 * 1024 * 1024)
        if not chunk:
            break
        out.write(chunk)
        sha.update(chunk)
        total += len(chunk)
        if total % (64 * 1024 * 1024) == 0:
            print(total // 1048576, "MiB", flush=True)
if expected and total != expected:
    raise RuntimeError("Incomplete runtime download.")
part.replace(cab)
target = root / "DNA_Software/Windows/WebView2Runtime"
target.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [windows_executable("expand.exe"), "-F:*", str(cab), str(target)],
    check=True,
    stdout=subprocess.DEVNULL,
)
exe = next(target.rglob("msedgewebview2.exe"))
(target / "runtime.json").write_text(
    json.dumps(
        {
            "source": url,
            "page": page,
            "sha256": sha.hexdigest(),
            "bytes": total,
            "executable_relative": str(exe.relative_to(target)),
        },
        indent=2,
    ),
    encoding="utf-8",
)
print("Portable WebView2 Runtime bereit:", exe, flush=True)
