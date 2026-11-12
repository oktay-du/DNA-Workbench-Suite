"""Native desktop window for the same loopback workspace the Windows EXE hosts.

The window is the desktop owner. It does not open the system browser.
"""

from pathlib import Path
import json, shutil, subprocess, sys, tempfile, time, urllib.parse


def embedded_command(info_path, python=None):
    launcher = Path(__file__).resolve().with_name("family.py")
    return [python or sys.executable, str(launcher), "--embedded", str(info_path)]


def workspace_url(service_url):
    parsed = urllib.parse.urlsplit(str(service_url))
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port is None
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("The desktop window only opens the loopback workspace")
    return "http://127.0.0.1:%d/app" % parsed.port


def wait_for_service(info_path, process, timeout=20):
    info_path = Path(info_path)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if info_path.is_file():
            return json.loads(info_path.read_text(encoding="utf-8"))
        if process.poll() is not None:
            detail = ""
            if process.stderr is not None:
                detail = process.stderr.read().decode(errors="replace").strip()
            raise RuntimeError(
                detail or "The local workspace service stopped before it was ready"
            )
        time.sleep(0.05)
    raise TimeoutError("The local workspace service did not respond")


def open_webkit(url):
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("WebKit2", "4.1")
    from gi.repository import Gtk, WebKit2

    window = Gtk.Window(title="DNA Workbench")
    window.set_default_size(1280, 800)
    web = WebKit2.WebView()
    web.get_settings().set_enable_javascript(True)
    web.get_settings().set_javascript_can_open_windows_automatically(False)
    web.load_uri(url)
    window.add(web)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


def open_macos(url):
    root = Path(__file__).resolve().parents[2]
    viewer = root / "DNA-Workbench.app/Contents/MacOS/DNAWorkbenchWebView"
    if not viewer.is_file():
        raise FileNotFoundError(
            "Build or extract the macOS application alongside the workspace."
        )
    subprocess.run([str(viewer), url], check=True)


def run():
    folder = Path(tempfile.mkdtemp(prefix="dna-desktop-"))
    info_path = folder / "service.json"
    process = subprocess.Popen(
        embedded_command(info_path),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        service = wait_for_service(info_path, process)
        url = workspace_url(service["url"])
        if sys.platform == "darwin":
            open_macos(url)
        else:
            open_webkit(url)
    finally:
        if process.poll() is None and process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        shutil.rmtree(folder, ignore_errors=True)


def main(argv=None):
    del argv
    try:
        run()
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
