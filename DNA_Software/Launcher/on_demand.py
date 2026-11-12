from system_tools import windows_executable
import network_io

"""Explicit per-function preparation; status checks never start a WSL distro."""
from portable_paths import distro_name
from pathlib import Path
import datetime, hashlib, os, platform, shlex, shutil, subprocess, sys, tarfile, urllib.request, zipfile
import portable_json as json
import portable_paths
import tool_hosts
import hardware
from importlib.util import find_spec

portable_paths.configure()
ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).parent
LOCK = json.loads((APP / "install-lock.json").read_text(encoding="utf-8"))
CAT = json.loads((APP / "catalog.json").read_text(encoding="utf-8"))
Q = shlex.quote
LOG = ROOT / "DNA_Software/UserData/Launcher/Needed"
PIP = {
    "peddy": "peddy==0.4.8",
    "whatshap": "whatshap==2.8",
    "truvari": "truvari==5.5.0",
    "snps": "snps==2.12.1",
    "pysam": "pysam==0.24.1",
    "multiqc": "multiqc==1.35",
    "plotly": "plotly==7.1.0",
    "open-cravat": "open-cravat==3.2.4",
    "yhaplo": "yhaplo[vcf,plot]==2.1.17",
}
PIP["pyliftover"] = "pyliftover==0.4.1"
PIP.update(
    {
        "storybook-pdf": "reportlab==5.1.0 / pypdf==6.21.4",
        "helix-3d": "manifold3d==3.5.4 / numpy==2.5.4",
    }
)
PIP["sequence-python"] = "biopython==1.88 / pyfastx==2.3.1 / numpy==2.5.4"
PIP.update({"biopython": "biopython==1.88", "pyfastx": "pyfastx==2.3.1"})
PIP["seqviz"] = "seqviz==3.10.25"
PIP["document-reader"] = "pypdf==6.21.4"
TOOLS = {
    "document-translation": (
        "https://github.com/argosopentech/argos-translate",
        None,
        "document-translation",
    ),
    "document-ocr": (
        "https://github.com/tesseract-ocr/tesseract",
        None,
        "document-ocr",
    ),
    "document-reader": ("https://github.com/py-pdf/pypdf", None, "windows-pip"),
    "seqviz": ("https://github.com/Lattice-Automation/seqviz", None, "visual-seqviz"),
    "biopython": ("https://github.com/biopython/biopython", None, "windows-pip"),
    "pyfastx": ("https://github.com/lmdu/pyfastx", None, "windows-pip"),
    "sequence-python": ("https://github.com/biopython/biopython", None, "windows-pip"),
    "gatk": ("https://github.com/broadinstitute/gatk", "gatk-4-7-0-0", "gatk"),
    "ugene": (
        "https://github.com/ugeneunipro/ugene",
        "ugene-53-1-windows",
        "windows-ugene",
    ),
    "storybook-pdf": ("https://www.reportlab.com/opensource/", None, "windows-pip"),
    "helix-3d": ("https://github.com/elalish/manifold", None, "windows-pip"),
    "pyliftover": ("https://github.com/konstantint/pyliftover", None, "windows-pip"),
    "nextflow": (
        "https://github.com/nextflow-io/nextflow",
        "nextflow-dist",
        "nextflow",
    ),
    "peddy": ("https://github.com/brentp/peddy", None, "isolated-pip"),
    "whatshap": ("https://github.com/whatshap/whatshap", None, "isolated-pip"),
    "truvari": ("https://github.com/ACEnglish/truvari", None, "isolated-pip"),
    "plink19": ("https://www.cog-genomics.org/plink/1.9/", None, "apt"),
    "bcftools": (
        "https://github.com/samtools/bcftools",
        "samtools-bcftools",
        "samtools",
    ),
    "samtools": (
        "https://github.com/samtools/samtools",
        "samtools-samtools",
        "samtools",
    ),
    "mosdepth": ("https://github.com/brentp/mosdepth", "mosdepth", "binary"),
    "fastp": ("https://github.com/OpenGene/fastp", None, "apt"),
    "snps": ("https://github.com/apriha/snps", None, "pip"),
    "pysam": ("https://github.com/pysam-developers/pysam", None, "pip"),
    "multiqc": ("https://github.com/MultiQC/MultiQC", None, "pip"),
    "plotly": ("https://github.com/plotly/plotly.py", None, "pip"),
    "open-cravat": (
        "https://github.com/KarchinLab/open-cravat",
        "karchinlab-open-cravat",
        "pip",
    ),
    "yhaplo": ("https://github.com/23andMe/yhaplo", "23andme-yhaplo", "pip"),
    "rfmix": ("https://github.com/slowkoni/rfmix", "slowkoni-rfmix", "rfmix"),
    "beagle": (
        "https://faculty.washington.edu/browning/beagle/beagle.html",
        "beagle-5-5",
        "java",
    ),
    "haplogrep": (
        "https://github.com/genepi/haplogrep3",
        "haplogrep3-3-3-2-linux-tar-gz",
        "haplogrep",
    ),
    "plink2": ("https://www.cog-genomics.org/plink/2.0/", "plink2-linux", "plink"),
    "hap-ibd": (
        "https://github.com/browning-lab/hap-ibd",
        "browning-lab-hap-ibd",
        "hap-ibd",
    ),
    "vep": ("https://github.com/Ensembl/ensembl-vep", "ensembl-ensembl-vep", "vep"),
    "pharmcat": (
        "https://github.com/PharmGKB/PharmCAT",
        "pharmcat-3-4-0-all-jar",
        "java",
    ),
    "sarek": ("https://github.com/nf-core/sarek", "nf-core-sarek", "nextflow-pipeline"),
    "pgsc-calc": (
        "https://github.com/PGScatalog/pgsc_calc",
        "pgscatalog-pgsc-calc",
        "nextflow-pipeline",
    ),
    "deepvariant": ("https://github.com/google/deepvariant", None, "manual"),
    "docker": ("https://github.com/moby/moby", None, "docker"),
    "linux-shell": ("https://github.com/microsoft/WSL", "ubuntu-wsl", "manual"),
    "admixtools": (
        "https://github.com/uqrmaie1/admixtools",
        "uqrmaie1-admixtools",
        "manual",
    ),
    "opencravat-models": ("https://github.com/KarchinLab/open-cravat", None, "manual"),
    "gramps": (
        "https://github.com/gramps-project/gramps",
        "grampsaio-6-0-8-1-win64-exe",
        "windows-manual",
    ),
    "jbrowse": (
        "https://github.com/GMOD/jbrowse-components",
        "jbrowse-desktop-v4-3-0-win-exe",
        "windows-manual",
    ),
    "igv": ("https://github.com/igvteam/igv", "igv-2-19-8", "windows-zip"),
    "java-windows": (
        "https://github.com/adoptium/temurin21-binaries",
        "java21-windows",
        "windows-zip",
    ),
    "jupyter-windows": (
        "https://github.com/jupyterlab/jupyterlab",
        None,
        "windows-pip",
    ),
}
WINDOWS = {
    "gramps",
    "jbrowse",
    "igv",
    "java-windows",
    "jupyter-windows",
    "pyliftover",
    "storybook-pdf",
    "helix-3d",
}
WINDOWS.update(("sequence-python", "ugene"))
WINDOWS.update(("biopython", "pyfastx"))
WINDOWS.add("seqviz")
WINDOWS.update(("document-reader", "document-translation"))
REQUIREMENTS = {
    "best_dataset": ["pyliftover"],
    "variant_convert": ["bcftools"],
    "fastq_report": ["fastp"],
    "liftover_snps": ["pyliftover"],
    "profile_analyze": ["pyliftover"],
    "profile_refresh": ["pyliftover"],
    "inspect": ["bcftools", "samtools", "snps"],
    "vcf_qc": ["bcftools"],
    "chip_vcf": ["snps", "pysam", "samtools", "bcftools"],
    "compare": ["bcftools", "pysam"],
    "fastq_qc": ["fastp"],
    "bam_qc": ["samtools", "mosdepth", "multiqc"],
    "multiqc": ["multiqc"],
    "sarek": ["nextflow", "sarek", "docker"],
    "deepvariant": ["deepvariant", "samtools", "docker"],
    "normalize": ["bcftools"],
    "filter": ["bcftools"],
    "peddy": ["peddy", "bcftools"],
    "whatshap": ["whatshap", "samtools", "bcftools"],
    "truvari": ["truvari", "bcftools"],
    "roh": ["plink19"],
    "merge": ["bcftools"],
    "kinship": ["plink2"],
    "ref_export": ["plink2"],
    "pca": ["plink2", "plotly"],
    "beagle": ["beagle"],
    "ibd": ["hap-ibd"],
    "rfmix": ["rfmix"],
    "mito": ["haplogrep", "bcftools"],
    "yhaplo": ["yhaplo", "bcftools"],
    "opencravat_run": ["open-cravat", "opencravat-models"],
    "vep": ["vep"],
    "pharmcat": ["pharmcat", "bcftools"],
    "pgs": ["nextflow", "pgsc-calc", "plink2", "docker"],
}
LICENSE = "RFMix: free academic research use only. Other uses require a separate Stanford license. Review https://github.com/slowkoni/rfmix#license. Checking a box does not grant a license."


def mapped(task, filename=""):
    if task == "provider_export":
        return ["storybook-pdf"] if filename.lower().endswith(".pdf") else []
    if task == "ugene":
        return ["ugene"]
    if task == "sequence_stats":
        return ["biopython"]
    if task == "sequence_extract":
        return ["pyfastx"]
    if task == "seqviz_view":
        return ["pyfastx", "seqviz"]
    if task in ("sequence_transform", "sequence_explore"):
        return ["biopython", "pyfastx"]
    if task == "model_readiness":
        return ["pyfastx"]
    if task == "gatk_validate":
        return ["gatk", "samtools"]
    if task == "research_synthesis":
        return ["storybook-pdf"]
    if task == "storybook":
        return ["storybook-pdf"]
    if task == "helix_export":
        return ["helix-3d"]
    entry = next((t for t in CAT["tasks"] if t["id"] == task), None)
    if not entry:
        raise ValueError("Unbekannte Funktion.")
    if entry.get("kind") == "launch":
        return {
            "OpenCRAVAT": ["open-cravat"],
            "Haplogrep": ["haplogrep"],
            "GrampsWeb": ["docker"],
            "Gramps": ["gramps"],
            "IGV": ["igv", "java-windows"],
            "JBrowse": ["jbrowse"],
            "Jupyter": ["jupyter-windows"],
            "Start": ["linux-shell"],
            "Linux": ["linux-shell"],
            "Admixtools": ["admixtools"],
        }.get(entry.get("core"), [])
    if entry["action"] == "inspect" and filename:
        return (
            ["bcftools"]
            if filename.lower().endswith((".vcf", ".vcf.gz", ".vcf.bgz", ".bcf"))
            else ["samtools"]
            if filename.lower().endswith((".bam", ".cram"))
            else ["snps"]
        )
    if entry["action"] in (
        "liftover_snps",
        "profile_analyze",
        "profile_refresh",
        "best_dataset",
    ):
        return REQUIREMENTS[entry["action"]]
    return (
        REQUIREMENTS.get(entry["action"], []) if entry.get("platform") == "WSL" else []
    )


def linux_path(path):
    p = Path(path).resolve()
    if os.name != "nt":
        return p.as_posix()
    return "/mnt/" + p.drive[0].lower() + p.as_posix()[2:]


LINUX_LOCAL = {
    "plink2",
    "haplogrep",
    "ugene",
    "java-windows",
    "jbrowse",
    "mosdepth",
    "gramps",
}
# The pinned guest binaries for these tools target x86-64. An ARM guest can
# still use a compatible version that is already on its PATH.
WSL_X64_ONLY = {"plink2", "haplogrep"}
WINDOWS_COMPANION = {
    "plink2": ("plink2-windows", "DNA_Software/Windows/PLINK2", "plink2.exe"),
    "haplogrep": (
        "haplogrep3-3-3-2-windows-tar-gz",
        "DNA_Software/Windows/Haplogrep",
        "haplogrep3.exe",
    ),
    "samtools": (
        "samtools-1-23-1-windows",
        "DNA_Software/Windows/Samtools",
        "samtools.exe",
    ),
    "bcftools": (
        "bcftools-1-23-1-windows",
        "DNA_Software/Windows/Bcftools",
        "bcftools.exe",
    ),
}
LINUX_SPEC = {
    "plink2": ("plink2-linux", "DNA_Software/Linux/PLINK2", "plink2", "plink2"),
    "haplogrep": (
        "haplogrep3-3-3-2-linux-tar-gz",
        "DNA_Software/Linux/Haplogrep",
        "haplogrep3",
        "haplogrep",
    ),
    "ugene": ("ugene-53-1-linux", "DNA_Software/Linux/UGENE", "ugene", "ugene"),
    "java-windows": ("java21-linux", "DNA_Software/Linux/Java21", "java", "java"),
    "mosdepth": ("mosdepth", None, None, "mosdepth"),
    "jbrowse": (
        "jbrowse-desktop-v4-3-0-linux-appimage",
        None,
        None,
        "jbrowse-desktop.AppImage",
    ),
    "gramps": ("gramps-6-0-8-1-amd64-snap", None, None, None),
}


def uses_host_tool_packages():
    return os.name != "nt" and (
        sys.platform == "darwin" or platform.machine().lower() in {"arm64", "aarch64"}
    )


HOST_COMMANDS = {
    "java-windows": "java",
    "haplogrep": "haplogrep",
    "open-cravat": "oc",
    "document-ocr": "tesseract",
}


def host_command(tool):
    return shutil.which(HOST_COMMANDS.get(tool, tool))


HOST_MODULES = {
    "biopython": ("Bio",),
    "document-reader": ("pypdf",),
    "helix-3d": ("manifold3d", "numpy"),
    "plotly": ("plotly",),
    "pyliftover": ("pyliftover",),
    "pyfastx": ("pyfastx",),
    "pysam": ("pysam",),
    "sequence-python": ("Bio", "pyfastx", "numpy"),
    "snps": ("snps",),
    "storybook-pdf": ("reportlab", "pypdf", "PIL"),
}


def host_tool_available(tool):
    if tool in HOST_MODULES:
        return all(find_spec(module) is not None for module in HOST_MODULES[tool])
    if tool == "document-ocr":
        return bool(host_command(tool) and shutil.which("pdftoppm"))
    return bool(host_command(tool))


def skips_wsl(tool):
    if tool in WINDOWS:
        return True
    return os.name != "nt" and tool in LINUX_LOCAL


def place_archive(archive, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as packed:
            for entry in packed.infolist():
                path = (dest / entry.filename).resolve()
                if not path.is_relative_to(dest.resolve()):
                    raise ValueError("Invalid archive path")
                if entry.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(packed.read(entry))
        return
    with tarfile.open(archive) as packed:
        packed.extractall(dest, filter="data")


def find_named(dest, name):
    return [path for path in Path(dest).rglob(name) if path.is_file()]


def publish_linux_bin(source, name):
    bindir = ROOT / "DNA_Software/Linux/bin"
    bindir.mkdir(parents=True, exist_ok=True)
    source = Path(source)
    source.chmod(source.stat().st_mode | 0o111)
    target = bindir / name
    if target.exists() or target.is_symlink():
        target.unlink()
    if source.parent == bindir and source.name == name:
        return target
    wrapper = "#!/bin/sh\nexec " + shlex.quote(str(source)) + ' "$@"\n'
    target.write_text(wrapper, encoding="utf-8")
    target.chmod(0o755)
    return target


def extract_windows_companion(tool):
    artifact, folder, name = WINDOWS_COMPANION[tool]
    dest = ROOT / folder
    place_archive(fetch(artifact), dest)
    found = find_named(dest, name)
    if not found:
        raise ValueError("Windows entry point missing: " + name)
    return {
        "tool": tool,
        "status": "Windows file extracted. The Linux file is still used inside WSL when that workflow is a shell script.",
    }


def install_linux_local(tool):
    artifact, folder, entry, binary = LINUX_SPEC[tool]
    archive = fetch(artifact)
    if tool == "gramps":
        return {
            "tool": tool,
            "status": "Linux Gramps snap downloaded. Install it with snapd; Wine is not used.",
            "path": str(archive),
        }
    if folder is None:
        dest = ROOT / "DNA_Software/Linux/bin" / binary
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, dest)
        dest.chmod(0o755)
        return {"tool": tool, "status": "Linux file installed", "path": str(dest)}
    dest = ROOT / folder
    place_archive(archive, dest)
    found = find_named(dest, entry)
    if tool == "java-windows":
        found = [path for path in found if path.parent.name == "bin"]
    if len(found) != 1:
        raise ValueError("Linux entry point missing: " + entry)
    publish_linux_bin(found[0], binary)
    return {"tool": tool, "status": "Linux file installed", "path": str(found[0])}


def linux_state():
    disk = ROOT / "DNA_Linux/DNA-SSD/ext4.vhdx"
    result = {
        "disk": disk.is_file(),
        "running": False,
        "registered": False,
        "wrong_location": False,
        "state": "Ubuntu fehlt",
    }
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Lxss"
        ) as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                with winreg.OpenKey(root, winreg.EnumKey(root, i)) as key:
                    if winreg.QueryValueEx(key, "DistributionName")[0] != distro_name(
                        ROOT
                    ):
                        continue
                    result["registered"] = True
                    base = winreg.QueryValueEx(key, "BasePath")[0].removeprefix(
                        chr(92) * 2 + "?" + chr(92)
                    )
                    result["wrong_location"] = (
                        Path(base).resolve() != disk.parent.resolve()
                    )
        if result["wrong_location"]:
            result["state"] = "DNA SSD is registered elsewhere"
            return result
        if result["registered"]:
            p = subprocess.run(
                [windows_executable("wsl.exe"), "--list", "--running", "--quiet"],
                capture_output=True,
                timeout=8,
            )
            result["running"] = (
                distro_name(ROOT)
                in p.stdout.decode("utf-16le", errors="ignore")
                .replace("\x00", "")
                .replace("\ufeff", "")
                .split()
            )
        result["state"] = (
            "Linux is running"
            if result["running"]
            else "Linux starten"
            if result["disk"]
            else "Ubuntu einrichten"
        )
    except (OSError, ImportError, subprocess.TimeoutExpired):
        result["state"] = "WSL-Host / Ubuntu einrichten"
    return result


def status(task, filename=""):
    required = mapped(task, filename)
    host_packages = uses_host_tool_packages()
    needs_linux = not host_packages and any(not skips_wsl(tool) for tool in required)
    state = (
        linux_state()
        if needs_linux
        else {
            "running": False,
            "state": "Not needed",
            "disk": False,
            "wrong_location": False,
        }
    )
    installed = {}
    if needs_linux and state["running"]:
        code = (
            "import importlib.util,json,shutil,pathlib; ids="
            + repr(required)
            + "; modules={'snps':'snps','pysam':'pysam','plotly':'plotly','open-cravat':'cravat','yhaplo':'yhaplo','multiqc':'multiqc'}; print(json.dumps({k:pathlib.Path('/opt/dna/R/library/admixtools/DESCRIPTION').is_file() if k=='admixtools' else (pathlib.Path('/opt/dna/opencravat/modules/annotators/clinvar/data/clinvar.sqlite').is_file() and all((pathlib.Path('/opt/dna/opencravat/modules/annotators/gnomad4/data')/('chr'+c+'.vcf.gz')).is_file() for c in [str(i) for i in range(1,23)]+['X'])) if k=='opencravat-models' else pathlib.Path('/opt/dna/envs/'+k+'/bin/'+k).is_file() if k in ('peddy','whatshap','truvari') else bool(importlib.util.find_spec(modules[k])) if k in modules else bool(shutil.which('tesseract') and shutil.which('pdftoppm')) if k=='document-ocr' else bool(shutil.which('bash' if k=='linux-shell' else k)) for k in ids}))"
        )
        cmd = [
            windows_executable("wsl.exe"),
            "-d",
            distro_name(ROOT),
            "-u",
            "dna",
            "--",
            "env",
            "PATH=/opt/dna/bin:/opt/dna/envs/analysis/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "/opt/dna/envs/analysis/bin/python",
            "-c",
            code,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=12)
            installed = (
                json.loads(r.stdout.decode("utf-8")) if r.returncode == 0 else {}
            )
        except (ValueError, OSError, subprocess.TimeoutExpired):
            pass
    records = []
    for tool in required:
        source, artifact, recipe = TOOLS[tool]
        artifact = tool_hosts.prefer(tool, artifact)
        arm_guest = hardware.windows_arm64()
        unsupported_pin = arm_guest and tool in WSL_X64_ONLY
        if unsupported_pin or (arm_guest and tool == "mosdepth"):
            artifact = None
        known = installed.get(tool)
        item = next((i for i in LOCK["items"] if i["id"] == artifact), {})
        if host_packages:
            if tool in LINUX_LOCAL:
                artifact, item = None, {}
            known = host_tool_available(tool)
            if tool == "seqviz":
                import visual_tools

                known = visual_tools.installed("seqviz")
        elif tool in WINDOWS and os.name == "nt":
            base = ROOT / "DNA_Software/Windows"
            known = (
                bool(list((base / "Java21").glob("**/java.exe")))
                if tool == "java-windows"
                else (base / "IGV/IGV_2.19.8/lib/igv.jar").is_file()
                if tool == "igv"
                else (base / "Gramps-6.0.8/grampsw.exe").is_file()
                if tool == "gramps"
                else (base / "JBrowse-4.3.0/jbrowse-desktop.exe").is_file()
                if tool == "jbrowse"
                else (base / "PythonPackages/jupyterlab").is_dir()
            )
            if tool == "pyliftover":
                known = (base / "PythonPackages/pyliftover/__init__.py").is_file()
            if tool == "document-translation":
                known = bool(
                    list(
                        (ROOT / "DNA_Software/Models/DocumentTranslation").glob(
                            "*/verified-package.json"
                        )
                    )
                )
            if tool == "document-reader":
                known = (base / "PythonPackages/pypdf/__init__.py").is_file()
            if tool == "storybook-pdf":
                known = all(
                    (base / "PythonPackages" / m).is_dir()
                    for m in ("reportlab", "pypdf", "PIL")
                )
            if tool == "helix-3d":
                known = (base / "PythonPackages/numpy").is_dir() and bool(
                    list((base / "PythonPackages").glob("manifold3d*.pyd"))
                )
            if tool == "sequence-python":
                known = (base / "PythonPackages/Bio").is_dir() and bool(
                    list((base / "PythonPackages").glob("pyfastx*.pyd"))
                )
            if tool == "biopython":
                known = (base / "PythonPackages/Bio").is_dir()
            if tool == "pyfastx":
                known = bool(list((base / "PythonPackages").glob("pyfastx*.pyd")))
            if tool == "seqviz":
                import visual_tools

                known = visual_tools.installed("seqviz")
            if tool == "ugene":
                known = bool(list((base / "UGENE").glob("**/ugeneui.exe")))
        elif os.name != "nt" and tool in LINUX_LOCAL:
            bindir = ROOT / "DNA_Software/Linux/bin"
            if tool == "gramps":
                known = shutil.which("gramps") is not None
            elif tool == "java-windows":
                known = bool(find_named(ROOT / "DNA_Software/Linux/Java21", "java"))
            elif tool == "haplogrep":
                known = (bindir / "haplogrep").is_file()
            elif tool == "ugene":
                known = (bindir / "ugene").is_file()
            elif tool == "jbrowse":
                known = (bindir / "jbrowse-desktop.AppImage").is_file()
            elif tool == "mosdepth":
                known = (bindir / "mosdepth").is_file()
            elif tool == "plink2":
                known = (bindir / "plink2").is_file()
        elif tool in WINDOWS:
            known = False
        records.append(
            {
                "id": tool,
                "installed": known,
                "state": "Bereit"
                if known
                else "Missing"
                if known is False
                else "Check after Linux start",
                "source": source,
                "recipe": recipe,
                "installable": tool == "seqviz"
                if host_packages
                else not unsupported_pin
                and (
                    (os.name != "nt" and tool in LINUX_LOCAL)
                    or recipe not in ["manual", "windows-manual"]
                ),
                "version": item.get("version")
                or item.get("commit")
                or PIP.get(tool, "Paketquelle / nach Installation protokolliert"),
                "downloaded": bool(item and (ROOT / item["relative_path"]).is_file()),
                "downloadable": bool(artifact),
                "license_notice": LICENSE if tool == "rfmix" else "",
            }
        )
    reviewed = False
    try:
        record = json.loads(
            (LOG / "rfmix-license-reviewed.json").read_text(encoding="utf-8")
        )
        reviewed = (
            record.get("notice_sha256")
            == hashlib.sha256(
                (APP / "Notices/RFMIX-LICENSE.txt").read_bytes()
            ).hexdigest()
        )
    except (OSError, ValueError):
        pass
    return {
        "task": task,
        "linux": state,
        "needs_linux": needs_linux,
        "requirements": records,
        "license_reviewed": reviewed,
        "ready": not required
        or (not needs_linux or state["running"])
        and all(r["installed"] for r in records),
        "note": "No services were started by this audit.",
    }


def fetch(artifact, license_reviewed=False):
    item = next(i for i in LOCK["items"] if i["id"] == artifact)
    if item.get("license_notice") and not license_reviewed:
        raise ValueError(LICENSE)
    p = (ROOT / item["relative_path"]).resolve()
    if not p.is_relative_to(ROOT.resolve()):
        raise ValueError("Invalid destination path.")
    expected = item.get("expected_sha256")
    if not expected:
        raise ValueError(
            "For this download, a specified SHA256 check value is missing."
        )
    if p.exists():
        if hashlib.file_digest(p.open("rb"), "sha256").hexdigest() != expected:
            raise ValueError("Existing archive deviates from the check value.")
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    part = p.with_suffix(p.suffix + ".part")
    sha = hashlib.sha256()
    with (
        network_io.open_https(
            urllib.request.Request(
                item["url"],
                headers={"User-Agent": "DNAWorkbench-explicit-optional-download"},
            ),
            timeout=90,
        ) as response,
        part.open("wb") as out,
    ):
        while True:
            chunk = response.read(8 * 1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            sha.update(chunk)
    if sha.hexdigest() != expected:
        raise ValueError("Download checksum is not correct.")
    part.replace(p)
    return p


def shell(lines):
    LOG.mkdir(parents=True, exist_ok=True)
    script = LOG / ("install-" + os.urandom(5).hex() + ".sh")
    header = "#!/usr/bin/env bash\nset -euo pipefail\nexport DEBIAN_FRONTEND=noninteractive\nexport PATH=/opt/dna/envs/analysis/bin:/opt/dna/bin:$PATH\nexport PIP_CACHE_DIR=/opt/dna/cache/pip\nmkdir -p /opt/dna/bin /opt/dna/tools /opt/dna/build\n"
    if os.name == "nt":
        text = header + "\n".join(lines) + "\nchown -R dna:dna /opt/dna\n"
        command = [
            windows_executable("wsl.exe"),
            "-d",
            distro_name(ROOT),
            "-u",
            "root",
            "--",
            "bash",
            linux_path(script),
        ]
    else:
        text = header + "\n".join(lines) + "\n"
        command = ["bash", str(script)]
    script.write_bytes(text.encode())
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log = script.with_suffix(".log")
    log.write_bytes(p.stdout)
    if p.returncode:
        raise RuntimeError("Installation fehlgeschlagen. Protokoll: " + str(log))
    return str(log)


def start_linux():
    process = subprocess.run(
        [
            windows_executable("powershell.exe"),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "DNA_Software/Start/DNA.ps1"),
            "-Action",
            "Start",
        ],
        capture_output=True,
    )
    if process.returncode:
        raise RuntimeError(
            process.stdout.decode(errors="replace")
            + process.stderr.decode(errors="replace")
        )
    holder = subprocess.Popen(
        [
            windows_executable("wsl.exe"),
            "-d",
            distro_name(ROOT),
            "-u",
            "dna",
            "--",
            "sleep",
            "infinity",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    LOG.mkdir(parents=True, exist_ok=True)
    (LOG / "linux-session.json").write_text(
        json.dumps(
            {
                "windows_pid": holder.pid,
                "distro": distro_name(ROOT),
                "started": datetime.datetime.now().astimezone().isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return {
        "status": "Linux launched; data carriers, work data and cache are in the app folder."
    }


def pip_requirements(tool):
    return [part for part in PIP[tool].replace("/", " ").split() if part]


def install_on_linux_host(tool):
    """Install a host package on Linux without starting WSL.

    Python modules land in the suite package folder already used by the
    Windows and Linux job runners. PLINK 1.9 is wrapped when the system
    package is present.
    """
    if os.name == "nt" or tool not in TOOLS:
        return None
    if tool == "plink19":
        binary = shutil.which("plink1.9")
        if not binary:
            raise ValueError(
                "Install the plink1.9 package, then retry. Wine and WSL are not used."
            )
        target = publish_linux_bin(Path(binary), "plink19")
        return {
            "tool": tool,
            "status": "Linux file installed",
            "path": str(target),
        }
    if TOOLS[tool][2] in ("pip", "windows-pip") and tool in PIP:
        folder = ROOT / "DNA_Software/Windows/PythonPackages"
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                str(folder),
                *pip_requirements(tool),
            ],
            check=True,
        )
        if tool == "multiqc":
            wrapper = ROOT / "DNA_Software/Linux/bin/multiqc"
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            wrapper.write_text(
                "#!/bin/sh\n"
                "export PYTHONPATH="
                + shlex.quote(str(folder))
                + '"${PYTHONPATH:+:$PYTHONPATH}"\n'
                'exec python3 -m multiqc "$@"\n',
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
        return {
            "tool": tool,
            "status": "Installed into the suite package folder",
            "path": str(folder),
        }
    return None


def install(tool, license_reviewed=False):
    if tool not in TOOLS:
        raise ValueError("Unbekanntes Werkzeug.")
    if tool == "rfmix" and not license_reviewed:
        raise ValueError(LICENSE)
    arm_guest = hardware.windows_arm64()
    if arm_guest and tool in WSL_X64_ONLY:
        raise ValueError(
            "The bundled Linux tool targets x86-64. Use a compatible build on the ARM64 Ubuntu PATH."
        )
    if uses_host_tool_packages():
        if tool == "seqviz":
            import visual_tools

            return visual_tools.install("seqviz")
        if host_tool_available(tool):
            return {
                "tool": tool,
                "status": "Host program is available",
                "path": host_command(tool) or sys.executable,
            }
        raise ValueError(
            "Install a compatible host build in PATH or in the workspace Python environment."
        )
    if os.name != "nt" and tool in LINUX_LOCAL:
        return install_linux_local(tool)
    if os.name != "nt":
        hosted = install_on_linux_host(tool)
        if hosted:
            return hosted
    companion = None
    if os.name == "nt" and tool in WINDOWS_COMPANION:
        companion = extract_windows_companion(tool)
    state = linux_state() if tool not in WINDOWS else {"running": False}
    if tool not in WINDOWS and not state["running"]:
        if companion:
            return companion
        raise ValueError("Linux first explicitly start / set up.")
    source, artifact, recipe = TOOLS[tool]
    lines = []

    def apt(packages):
        lines.extend(
            ["apt-get update", "apt-get install -y --no-install-recommends " + packages]
        )

    def unpack(archive, folder):
        lines.append("mkdir -p " + Q(folder))
        lines.append(
            "python3 -c "
            + Q(
                "import tarfile; tarfile.open("
                + repr(linux_path(archive))
                + ").extractall("
                + repr(folder)
                + ",filter='data')"
            )
        )

    def wrapper(name, body):
        text = "#!/usr/bin/env bash\n" + body + "\n"
        lines.append("printf %s " + Q(text) + " > " + Q("/opt/dna/bin/" + name))
        lines.append("chmod +x " + Q("/opt/dna/bin/" + name))

    if recipe in ["manual", "windows-manual"]:
        raise ValueError(
            "Automatic installation recipe not yet released. Open project page; not issued as installed."
        )
    if recipe == "document-translation":
        import document_processing

        return document_processing.install_translation()
    if recipe == "document-ocr":
        apt(
            "poppler-utils tesseract-ocr "
            + " ".join(
                "tesseract-ocr-" + x
                for x in ["eng", "deu", "tur", "fra", "spa", "pol", "rus", "ukr", "ara"]
            )
        )
        lines.extend(["tesseract --version", "tesseract --list-langs"])
        return {
            "tool": tool,
            "log": shell(lines),
            "status": "OCR installed with nine languages in portable WSL disk",
        }
    if recipe == "windows-pip":
        args = (
            [
                "--no-deps",
                "--require-hashes",
                "-r",
                str(APP / "Locks/pyliftover-windows.txt"),
            ]
            if tool == "pyliftover"
            else ["jupyterlab==4.6.5"]
        )
        if tool == "storybook-pdf":
            args = [
                "reportlab==5.1.0",
                "pypdf==6.21.4",
                "pillow==13.0.0",
                "charset-normalizer==3.5.2",
            ]
        if tool == "document-reader":
            args = ["pypdf==6.21.4"]
        if tool == "helix-3d":
            args = ["manifold3d==3.5.4", "numpy==2.5.4"]
        if tool in ("sequence-python", "biopython", "pyfastx"):
            args = [
                "--no-deps",
                "--require-hashes",
                "-r",
                str(APP / "Locks/sequence-python-windows.txt"),
            ]
        p = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--target",
                str(ROOT / "DNA_Software/Windows/PythonPackages"),
                *args,
            ],
            capture_output=True,
        )
        if p.returncode:
            raise RuntimeError(p.stderr.decode(errors="replace"))
        return {"tool": tool, "status": "Windows-Paket eingerichtet"}
    if recipe == "visual-seqviz":
        import visual_tools

        return visual_tools.install("seqviz")
    if recipe == "windows-ugene":
        archive = fetch(artifact)
        dest = ROOT / "DNA_Software/Windows/UGENE"
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                path = (dest / entry.filename).resolve()
                if not path.is_relative_to(dest.resolve()):
                    raise ValueError("Invalid UGENE archive path")
                if entry.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(z.read(entry))
        if not list(dest.glob("**/ugeneui.exe")):
            raise ValueError("UGENE portable entry point missing")
        return {
            "tool": tool,
            "status": "Portable UGENE extracted; GUI starts only when requested",
        }
    if recipe == "gatk":
        archive = fetch(artifact)
        apt("openjdk-17-jre-headless unzip")
        lines += [
            "mkdir -p /opt/dna/tools",
            "unzip -qo " + Q(linux_path(archive)) + " -d /opt/dna/tools",
            "test -f /opt/dna/tools/gatk-4.7.0.0/gatk-package-4.7.0.0-local.jar",
        ]
        wrapper(
            "gatk",
            'exec /usr/bin/java -jar /opt/dna/tools/gatk-4.7.0.0/gatk-package-4.7.0.0-local.jar "$@"',
        )
        lines.append("/opt/dna/bin/gatk --version")
        return {
            "tool": tool,
            "log": shell(lines),
            "status": "GATK installed and version command checked",
        }
    if recipe == "windows-zip":
        archive = fetch(artifact)
        dest = ROOT / "DNA_Software/Windows" / ("IGV" if tool == "igv" else "Java21")
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                path = (dest / entry.filename).resolve()
                if not path.is_relative_to(dest.resolve()):
                    raise ValueError("Inadmissible archival path.")
                if entry.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(z.read(entry))
        return {"tool": tool, "status": "Windows-Archiv eingerichtet"}
    if tool == "yhaplo":
        archive = fetch(artifact)
        unpack(archive, "/opt/dna/build")
        item = next(i for i in LOCK["items"] if i["id"] == artifact)
        folder = "/opt/dna/build/yhaplo-" + item["commit"]
        lines.append(
            "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_YHAPLO=2.1.17 /opt/dna/envs/analysis/bin/python -m pip install "
            + Q(folder + "[vcf,plot]")
        )
    elif tool in ("peddy", "whatshap", "truvari"):
        apt(
            "python3-venv build-essential zlib1g-dev libbz2-dev liblzma-dev libcurl4-openssl-dev libssl-dev"
        )
        env = "/opt/dna/envs/" + tool
        lines += [
            "python3 -m venv " + Q(env),
            Q(env + "/bin/python")
            + " -m pip install --disable-pip-version-check --report "
            + Q(env + "/pip-report.json")
            + " -r "
            + Q(linux_path(APP / "Locks" / (tool + "-linux.txt"))),
        ]
        wrapper(tool, "exec " + Q(env + "/bin/" + tool) + ' "$@"')
        lines.append(Q(env + "/bin/python") + " -m pip check")
    elif tool in PIP:
        lines.append("/opt/dna/envs/analysis/bin/python -m pip install " + Q(PIP[tool]))
    elif tool in ["samtools", "bcftools"]:
        archive = fetch(tool + "-1-25-tar-bz2")
        apt(
            "build-essential autoconf automake libtool libbz2-dev liblzma-dev libcurl4-openssl-dev libssl-dev libncurses-dev zlib1g-dev"
        )
        unpack(archive, "/opt/dna/build")
        lines += [
            "cd /opt/dna/build/" + tool + "-1.25",
            "./configure --prefix=/opt/dna/tools/" + tool + "-1.25",
            "make -j2",
            "make install",
            "ln -sfn /opt/dna/tools/"
            + tool
            + "-1.25/bin/"
            + tool
            + " /opt/dna/bin/"
            + tool,
        ]
    elif tool == "rfmix":
        archive = fetch(artifact, True)
        apt("build-essential autoconf automake libtool zlib1g-dev")
        unpack(archive, "/opt/dna/build")
        item = next(i for i in LOCK["items"] if i["id"] == artifact)
        folder = "/opt/dna/build/rfmix-" + item["commit"]
        dest = "/opt/dna/tools/rfmix-" + item["commit"][:12]
        lines += [
            "cd " + Q(folder),
            "autoreconf --force --install",
            "./configure --prefix=" + Q(dest),
            "make -j2",
            "make install",
            "ln -sfn " + Q(dest + "/bin/rfmix") + " /opt/dna/bin/rfmix",
        ]
    elif tool == "plink19":
        apt("plink1.9")
        wrapper("plink19", 'exec /usr/bin/plink1.9 "$@"')
    elif tool == "fastp":
        apt("fastp")
    elif tool == "nextflow":
        archive = fetch("nextflow-dist")
        apt("openjdk-21-jre-headless")
        lines += [
            "mkdir -p /opt/dna/cache/nextflow /opt/dna/sources/nextflow-assets",
            "install -m755 " + Q(linux_path(archive)) + " /opt/dna/bin/nextflow",
            "NXF_VER=26.10.5 NXF_HOME=/opt/dna/cache/nextflow /opt/dna/bin/nextflow -version",
        ]
    elif tool in ("sarek", "pgsc-calc"):
        install("nextflow")
        archive = fetch(artifact)
        unpack(archive, "/opt/dna/tools")
        item = next(i for i in LOCK["items"] if i["id"] == artifact)
        folder = (
            "/opt/dna/tools/"
            + ("sarek-" if tool == "sarek" else "pgsc_calc-")
            + item["commit"]
        )
        body = (
            "export NXF_HOME=/opt/dna/cache/nextflow\nexport NXF_ASSETS=/opt/dna/sources/nextflow-assets\nexport NXF_VER=26.10.5\nexport DOCKER_HOST=unix:///run/docker-dna.sock\nexec /opt/dna/bin/nextflow run "
            + Q(folder)
            + " -profile docker -c "
            + Q(linux_path(ROOT / "DNA_Software/Start/dna-nextflow.config"))
            + ' "$@"'
        )
        wrapper(tool, body)
        lines.append("test -f " + Q(folder + "/main.nf"))
    elif tool == "docker":
        apt("docker.io")
    elif tool == "mosdepth":
        if arm_guest:
            apt("mosdepth")
        else:
            lines.append(
                "install -m755 "
                + Q(linux_path(fetch(artifact)))
                + " /opt/dna/bin/mosdepth"
            )
    elif tool == "beagle":
        jar = fetch(artifact)
        apt("openjdk-21-jre-headless")
        wrapper("beagle", "exec java -jar " + Q(linux_path(jar)) + ' "$@"')
    elif tool == "pharmcat":
        jar = fetch(artifact)
        apt("openjdk-21-jre-headless")
        wrapper("pharmcat", "exec java -jar " + Q(linux_path(jar)) + ' "$@"')
    elif tool == "plink2":
        archive = fetch(artifact)
        folder = ROOT / "DNA_Software/Downloads/PLINK2_Linux"
        folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            member = next(n for n in z.namelist() if Path(n).name == "plink2")
            (folder / "plink2").write_bytes(z.read(member))
        lines.append(
            "install -m755 " + Q(linux_path(folder / "plink2")) + " /opt/dna/bin/plink2"
        )
    elif tool == "haplogrep":
        archive = fetch(artifact)
        tree = fetch("haplogrep-default-tree")
        apt("unzip")
        dest = "/opt/dna/tools/haplogrep3"
        lines += [
            "mkdir -p " + dest,
            "tar -xzf " + Q(linux_path(archive)) + " -C " + dest,
            "mkdir -p " + dest + "/trees/phylotree-fu-rcrs-1.3",
            "unzip -o "
            + Q(linux_path(tree))
            + " -d "
            + dest
            + "/trees/phylotree-fu-rcrs-1.3",
        ]
        config = (
            "port: 7001\nworkspace: "
            + json.dumps(linux_path(ROOT / "DNA_Software/UserData/Haplogrep/jobs"))
            + "\nrepositories: []\nphylotrees:\n  - trees/phylotree-fu-rcrs-1.3/tree.yaml\nexamples: []\n"
        )
        lines.append("printf %s " + Q(config) + " > " + dest + "/haplogrep3.yaml")
        wrapper("haplogrep", "cd " + dest + '\nexec ./haplogrep3 "$@"')
    elif tool == "hap-ibd":
        archive = fetch(artifact)
        apt("openjdk-21-jdk-headless")
        unpack(archive, "/opt/dna/build")
        item = next(i for i in LOCK["items"] if i["id"] == artifact)
        folder = "/opt/dna/build/hap-ibd-" + item["commit"]
        lines += [
            "cd " + Q(folder),
            "mkdir -p bin",
            'javac -d bin $(find src -name "*.java")',
            "jar cfe hap-ibd.jar hapibd.HapIbdMain -C bin .",
        ]
        wrapper("hap-ibd", "exec java -jar " + Q(folder + "/hap-ibd.jar") + ' "$@"')
    elif tool == "vep":
        archive = fetch(artifact)
        apt(
            "build-essential perl cpanminus libarchive-zip-perl libdbi-perl libdbd-mysql-perl libjson-perl libperlio-gzip-perl libwww-perl libtext-csv-perl liblist-moreutils-perl"
        )
        unpack(archive, "/opt/dna/build")
        item = next(i for i in LOCK["items"] if i["id"] == artifact)
        folder = "/opt/dna/build/ensembl-vep-" + item["commit"]
        lines += [
            "cd " + Q(folder),
            "perl INSTALL.pl --AUTO a --NO_UPDATE --NO_BIOPERL --NO_TEST",
        ]
        wrapper("vep", "cd " + Q(folder) + '\nexec perl ./vep "$@"')
    else:
        raise ValueError("Installationsrezept fehlt.")
    log = shell(lines)
    record = {
        "tool": tool,
        "source": source,
        "finished": datetime.datetime.now().astimezone().isoformat(),
        "license_reviewed": license_reviewed,
        "log": log,
    }
    (LOG / (tool + "-installation.json")).write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    return record


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        if action == "acknowledge":
            if sys.argv[2] != "rfmix" or "--license-reviewed" not in sys.argv:
                raise ValueError("Explicit license testing is required.")
            LOG.mkdir(parents=True, exist_ok=True)
            (LOG / "rfmix-license-reviewed.json").write_text(
                json.dumps(
                    {
                        "source": TOOLS["rfmix"][0],
                        "notice": LICENSE,
                        "notice_sha256": hashlib.sha256(
                            (APP / "Notices/RFMIX-LICENSE.txt").read_bytes()
                        ).hexdigest(),
                        "confirmed_by_user": True,
                        "time": datetime.datetime.now().astimezone().isoformat(),
                    }
                ),
                encoding="utf-8",
            )
            result = {
                "status": "User information is stored for the license check; this does not grant a license."
            }
        else:
            result = (
                status(
                    sys.argv[2],
                    sys.argv[sys.argv.index("--file") + 1]
                    if "--file" in sys.argv
                    else "",
                )
                if action == "status"
                else start_linux()
                if action == "start"
                else install(sys.argv[2], "--license-reviewed" in sys.argv)
                if action == "install"
                else {
                    "path": str(
                        fetch(TOOLS[sys.argv[2]][1], "--license-reviewed" in sys.argv)
                    )
                }
                if action == "download"
                else None
            )
        if result is None:
            raise ValueError("Unbekannte Aktion")
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
