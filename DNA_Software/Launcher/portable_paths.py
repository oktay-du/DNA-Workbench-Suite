"""Location-independent app paths, process-local caches and host WSL identity."""

from pathlib import Path
import hashlib, json, os, uuid

ROOT = Path(__file__).resolve().parents[2]
_ROOTS = {}
INTERNAL = (
    "Profiles",
    "DNA_Software",
    "Projects",
    "DNA_Archiv",
    "References",
    "DNA_Linux",
    "DNAWorkbench_Source",
)


def configure(root=ROOT):
    root = Path(root).resolve()
    base = root / "DNA_Software/UserData"
    paths = {
        "TEMP": base / "Temp",
        "TMP": base / "Temp",
        "TMPDIR": base / "Temp",
        "XDG_CACHE_HOME": base / "Cache",
        "XDG_DATA_HOME": base / "Data",
        "XDG_CONFIG_HOME": base / "Config",
        "PIP_CACHE_DIR": base / "Cache/pip",
        "UV_CACHE_DIR": base / "Cache/uv",
        "HF_HOME": base / "Cache/huggingface",
        "TORCH_HOME": base / "Cache/torch",
        "MPLCONFIGDIR": base / "Cache/matplotlib",
        "npm_config_cache": base / "Cache/npm",
        "JUPYTER_CONFIG_DIR": base / "Jupyter/config",
        "JUPYTER_DATA_DIR": base / "Jupyter/data",
        "JUPYTER_RUNTIME_DIR": base / "Jupyter/runtime",
        "APPDATA": base / "AppData/Roaming",
        "LOCALAPPDATA": base / "AppData/Local",
    }
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)
    os.environ["DNA_SUITE_ROOT"] = str(root)
    os.environ["PYTHONNOUSERSITE"] = "1"
    state = base / "Launcher/portable-location.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(state.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        data = {}
    aliases = list(
        dict.fromkeys(
            [
                *data.get("previous_roots", []),
                *([data["root"]] if data.get("root") else []),
            ]
        )
    )
    value = {
        "root": str(root),
        "previous_roots": [
            x
            for x in aliases
            if x.rstrip("/\\").lower() != str(root).rstrip("/\\").lower()
        ],
    }
    if data != value:
        tmp = state.with_name(state.name + "." + uuid.uuid4().hex + ".tmp")
        tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
        os.replace(tmp, state)
        _ROOTS.pop(str(root), None)
        import portable_json

        portable_json.clear_cache()
    return value


def remembered_roots(root=ROOT):
    """Previous install locations, reread only when that record changes."""
    root = Path(root)
    file = root / "DNA_Software/UserData/Launcher/portable-location.json"
    try:
        info = file.stat()
        stamp = (info.st_mtime_ns, info.st_size)
    except OSError:
        stamp = None
    key = str(root)
    cached = _ROOTS.get(key)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    if cached is not None:
        import portable_json

        portable_json.clear_cache()
    aliases = []
    if stamp is not None:
        try:
            aliases = json.loads(file.read_text(encoding="utf-8-sig")).get(
                "previous_roots", []
            )
        except (OSError, ValueError):
            aliases = []
    if not isinstance(aliases, list):
        aliases = []
    _ROOTS[key] = (stamp, aliases)
    return aliases


def rebase(value, root=ROOT, aliases=None):
    root = Path(root)
    if aliases is None:
        aliases = remembered_roots(root)

    def convert(s):
        if not isinstance(s, str):
            return s
        s = __import__("layout_migration").path(s, root)
        normalized = s.replace("\\", "/")
        for old in sorted(aliases, key=len, reverse=True):
            prefix = str(old).replace("\\", "/").rstrip("/")
            current = str(root).replace("\\", "/").rstrip("/")
            # Moving from a drive root into one of its own subdirectories must
            # not rebase paths that already refer to the new location again.
            if current.lower().startswith((prefix + "/").lower()) and (
                normalized.lower() == current.lower()
                or normalized.lower().startswith((current + "/").lower())
            ):
                return s
            if (
                normalized.lower() == prefix.lower()
                or normalized.lower() == (prefix + "/").lower()
            ):
                return str(root)
            if normalized.lower().startswith((prefix + "/").lower()):
                tail = normalized[len(prefix) + 1 :]
                if (
                    tail.split("/")[0] == "DNA_Archiv"
                    and not (root / "DNA_Archiv").exists()
                ):
                    return s
                if tail.split("/")[0] in INTERNAL:
                    parts = tail.split("/")
                    if ".." in parts:
                        return s
                    return str(root.joinpath(*parts))
        return s

    if isinstance(value, dict):
        return {convert(k): rebase(v, root, aliases) for k, v in value.items()}
    if isinstance(value, list):
        return [rebase(v, root, aliases) for v in value]
    return convert(value)


def registered(root=ROOT):
    result = []
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Lxss"
        ) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as child:
                    base = winreg.QueryValueEx(child, "BasePath")[0].removeprefix(
                        "\\\\?\\"
                    )
                    result.append(
                        {
                            "name": winreg.QueryValueEx(child, "DistributionName")[0],
                            "path": base,
                        }
                    )
    except (OSError, ImportError):
        pass
    return result


def distro_name(root=ROOT):
    root = Path(root).resolve()
    expected = root / "DNA_Linux/DNA-SSD"
    for row in registered(root):
        if Path(row["path"]).resolve() == expected:
            return row["name"]
    normalized = str(root).rstrip("/\\").lower()
    return "DNA-WB-" + hashlib.sha256(normalized.encode()).hexdigest()[:12]
