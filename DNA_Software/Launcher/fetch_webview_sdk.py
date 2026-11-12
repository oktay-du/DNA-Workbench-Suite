import network_io
from pathlib import Path
import argparse, json, zipfile, io, hashlib

parser = argparse.ArgumentParser()
parser.add_argument("--arch", choices=("x64", "arm64"), default="x64")
arch = parser.parse_args().arch

base = "https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/"
version = "1.0.4314.35"
data = network_io.open_https(
    base + version + "/microsoft.web.webview2." + version + ".nupkg", timeout=90
).read()
if (
    hashlib.sha256(data).hexdigest()
    != "90778deb1b77e36292828b4b5833c9255c27533f40e0ddd55891ae718944edc4"
):
    raise RuntimeError("WebView2 SDK checksum mismatch")
out = Path(__file__).with_name("WebView2" if arch == "x64" else "WebView2-arm64")
out.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as z:
    wanted = {"Microsoft.Web.WebView2.Core.dll", "Microsoft.Web.WebView2.WinForms.dll"}
    for name in z.namelist():
        if (
            name.startswith("lib/net462/")
            and Path(name).name in wanted
            or name == f"runtimes/win-{arch}/native/WebView2Loader.dll"
        ):
            (out / Path(name).name).write_bytes(z.read(name))
        if "license" in Path(name).name.lower() and not name.endswith("/"):
            (out / ("SDK-" + Path(name).name)).write_bytes(z.read(name))
(out / "source.json").write_text(
    json.dumps(
        {
            "package": "Microsoft.Web.WebView2",
            "version": version,
            "source": base,
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(version, [p.name for p in out.glob("*.dll")])
