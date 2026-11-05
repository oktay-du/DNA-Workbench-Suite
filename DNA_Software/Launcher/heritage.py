"""Public place context, kept separate from per-person genetic evidence."""

from pathlib import Path
import ctypes, re
import portable_json as json

APP = Path(__file__).parent


def catalog():
    data = json.loads((APP / "heritage-places.json").read_text(encoding="utf-8"))
    try:
        photos = json.loads((APP / "heritage-images.json").read_text(encoding="utf-8"))[
            "images"
        ]
    except (OSError, ValueError):
        photos = []
    for place in data["places"]:
        place["photos"] = [
            dict(p, url="/heritage-image/" + p["id"])
            for p in photos
            if p["place"] == place["id"]
            and (APP / "heritage-assets" / p["file"]).is_file()
        ]
    return data


def photo_path(identifier):
    if not re.fullmatch("[a-z0-9_-]{1,80}", identifier):
        raise ValueError("Invalid image identifier.")
    images = json.loads((APP / "heritage-images.json").read_text(encoding="utf-8"))[
        "images"
    ]
    image = next((p for p in images if p["id"] == identifier), None)
    if not image or not re.fullmatch("[a-z0-9_-]+[.]jpg", image["file"]):
        raise ValueError("Bild fehlt.")
    return APP / "heritage-assets" / image["file"]


def process_alive(pid):
    if not isinstance(pid, int) or pid < 1:
        return False
    try:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
        ]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return (
                bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code)))
                and code.value == 259
            )
        finally:
            kernel.CloseHandle(handle)
    except (AttributeError, OSError):
        return False


def statuses(people, results, root):
    answer = {}
    for person in people:
        pid = person["id"]
        own = [r["data"] for r in results if r["person"] == pid]
        ready = any(r.get("regions") for r in own)
        traits = any(r.get("traits") for r in own)
        state = "available" if ready else "pending"
        detail = (
            "Source, model and version remain visible."
            if ready
            else "This profile has not yet been evaluated for its origin, and no ongoing analysis of its origin has yet been established."
        )
        jobs = Path(root) / "Projects/Launcher" / pid
        if not ready and re.fullmatch("[A-Za-z0-9_-]+", pid) and jobs.is_dir():
            for path in sorted(
                jobs.glob("*/status.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:100]:
                try:
                    job = json.loads(path.read_text(encoding="utf-8"))
                    name = job.get("task", "")
                    if name not in ("rfmix", "pca", "ancestry", "admixture"):
                        continue
                    job_status = str(job.get("status", "")).casefold()
                    if job_status in (
                        "Running",
                        "running",
                        "in bearbeitung",
                    ) and process_alive(job.get("pid")):
                        state = "running"
                        detail = (
                            "A local analysis is underway:"
                            + str(job.get("title", name))
                            + "We do not yet have a comprehensible result of origin."
                        )
                        break
                    if job_status in ("fehlgeschlagen", "fehler", "failed"):
                        state = "failed"
                        detail = "The last analysis of origin has failed: order and protocol check; no results invented."
                        break
                except (OSError, ValueError):
                    continue
        answer[pid] = {
            "ancestry": {
                "state": state,
                "label": "Result available" if ready else "Still in progress",
                "detail": detail,
            },
            "traits": {
                "state": "available" if traits else "pending",
                "label": "Existing feature result" if traits else "Still in progress",
                "detail": "Imported model estimation is available."
                if traits
                else "No evaluable model result is yet available for these characteristics.",
            },
        }
    return answer
