from system_tools import (
    DEEPVARIANT_GPU_PROBE,
    DESKTOP_APPS,
    NATIVE_SEQUENCE_TOOLS,
    desktop_tool_command,
    homebrew_bin,
    kiri_docker,
    KIRI_RFMIX_IMAGE,
    KIRI_VEP_IMAGE,
    KIRI_OPENCRAVAT_IMAGE,
    kiri_task_tool,
    kiri_opencravat_modules,
    kiri_vep_cache,
    kiri_sequence_tool,
    native_sequence_command,
    windows_deepvariant_gpu,
    windows_executable,
)
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
    "vep-cache": (
        "https://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html",
        "vep-cache-116-grch38",
        "vep-cache",
    ),
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
    "opencravat-models": (
        "https://github.com/KarchinLab/open-cravat",
        None,
        "opencravat-models",
    ),
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
    "chip_vcf": ["snps", "pysam", "samtools"],
    "compare": ["pysam"],
    "fastq_qc": ["fastp"],
    "bam_qc": ["samtools", "mosdepth", "multiqc"],
    "multiqc": ["multiqc"],
    "sarek": ["nextflow", "sarek", "docker", "samtools"],
    "deepvariant": ["deepvariant", "samtools", "docker"],
    "normalize": ["bcftools", "samtools"],
    "filter": ["bcftools"],
    "peddy": ["peddy", "bcftools"],
    "whatshap": ["whatshap", "samtools"],
    "truvari": ["truvari", "bcftools", "samtools"],
    "roh": ["plink19"],
    "merge": ["bcftools"],
    "kinship": ["plink2"],
    "ref_export": ["plink2", "bcftools"],
    "pca": ["plink2", "plotly"],
    "beagle": ["beagle"],
    "ibd": ["hap-ibd"],
    "rfmix": ["rfmix"],
    "mito": ["haplogrep", "bcftools"],
    "yhaplo": ["yhaplo", "bcftools"],
    "opencravat_run": ["open-cravat", "opencravat-models"],
    "vep": ["vep", "vep-cache"],
    "pharmcat": ["pharmcat"],
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
            "IGV": ["igv", "java-windows"] if os.name == "nt" else ["igv"],
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

NATIVE_PIPELINES = {"sarek": "sarek", "pgsc-calc": "pgsc_calc"}
NEXTFLOW_DIST = next(i for i in LOCK["items"] if i["id"] == "nextflow-dist")
WINDOWS_KIRI_PIPELINES = {
    "sarek": ("sarek", "samtools"),
    "pgs": ("pgsc-calc", "plink2"),
}


def native_nextflow_path():
    return LOG / NEXTFLOW_DIST["name"]


def windows_kiri_pipeline(task):
    if os.name != "nt" or task not in WINDOWS_KIRI_PIPELINES:
        return None
    tool, prep = WINDOWS_KIRI_PIPELINES[task]
    source = native_pipeline_source(tool)
    if not (source / "main.nf").is_file():
        return None
    launcher = ROOT / NEXTFLOW_DIST["relative_path"]
    if not launcher.is_file():
        return None
    route = kiri_sequence_tool("nextflow")
    if route is None:
        return None
    prep_route = kiri_sequence_tool(prep)
    if prep_route is None or route.platform != prep_route.platform:
        return None
    return route, prep_route, source, launcher


def install_native_nextflow():
    import tempfile

    target = native_nextflow_path()
    source = fetch("nextflow-dist")
    with tempfile.TemporaryDirectory(dir=target.parent) as stage:
        executable = Path(stage) / target.name
        shutil.copyfile(source, executable)
        executable.chmod(0o755)
        executable.replace(target)
    return {
        "tool": "nextflow",
        "status": "Pinned Nextflow launcher installed. Java 17–26 is required.",
        "path": str(target),
    }


def native_pipeline_source(tool):
    artifact = TOOLS[tool][1]
    item = next(i for i in LOCK["items"] if i["id"] == artifact)
    return LOG / "nextflow-pipelines" / (NATIVE_PIPELINES[tool] + "-" + item["commit"])


def native_pipeline_docker_socket():
    docker = host_command("docker")
    if not docker:
        return None
    candidates = (
        (Path.home() / ".kiri/run/docker.sock", Path.home() / ".docker/run/docker.sock")
        if sys.platform == "darwin"
        else (
            Path("/run/kiri/docker.sock"),
            Path.home() / ".docker/desktop/docker.sock",
        )
    )
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    rootless = (
        Path(runtime) / "docker.sock"
        if runtime and Path(runtime).is_absolute()
        else None
    )
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("DOCKER_")
    }
    for path in (*candidates, rootless, Path("/var/run/docker.sock")):
        if not path or not path.is_socket():
            continue
        try:
            result = subprocess.run(
                [
                    docker,
                    "--host",
                    "unix://" + str(path),
                    "version",
                    "--format",
                    "{{.Server.Os}}",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip() == "linux":
                return str(path)
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def deepvariant_docker_socket():
    candidates = (
        Path("/var/run/docker.sock"),
        Path.home() / ".docker/run/docker.sock",
        Path.home() / ".docker/desktop/docker.sock",
    )
    for path in candidates:
        if path.is_socket() and path.resolve().name == "docker.sock":
            resolved = path.resolve()
            if not any(part in {".kiri", "kiri"} for part in resolved.parts):
                return str(path)
    return None


def deepvariant_regular_image(state):
    docker = ["docker"]
    if os.name == "nt":
        if not state["running"] or hardware.windows_arm64():
            return False
        docker = [
            windows_executable("wsl.exe"),
            "-d",
            distro_name(ROOT),
            "-u",
            "dna",
            "--",
            "/usr/bin/docker",
            "--host",
            "unix:///run/docker-dna.sock",
        ]
    else:
        if platform.machine().lower() not in {"amd64", "x86_64"}:
            return False
        endpoint = deepvariant_docker_socket()
        if not endpoint:
            return False
        docker += ["--host", "unix://" + endpoint]
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("DOCKER_")
    }
    try:
        for tag in ("1.10.0", "1.10.0-gpu"):
            result = subprocess.run(
                [
                    *docker,
                    "image",
                    "inspect",
                    "--format",
                    "{{.Os}}/{{.Architecture}}",
                    "google/deepvariant:" + tag,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=4,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0 and result.stdout.strip() == "linux/amd64":
                if tag == "1.10.0":
                    return True
                probe = subprocess.run(
                    [
                        *docker,
                        "run",
                        "--rm",
                        "--pull=never",
                        "--network=none",
                        "--platform",
                        "linux/amd64",
                        "--gpus",
                        "1",
                        "--entrypoint",
                        "/usr/bin/python3",
                        "google/deepvariant:" + tag,
                        "-c",
                        DEEPVARIANT_GPU_PROBE,
                    ],
                    env=env,
                    capture_output=True,
                    timeout=30,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                return probe.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def install_native_pipeline(tool):
    import tempfile

    target = native_pipeline_source(tool)
    if not (target / "main.nf").is_file():
        archive = fetch(TOOLS[tool][1])
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent) as stage:
            place_archive(archive, stage)
            source = Path(stage) / target.name
            if not (source / "main.nf").is_file():
                raise ValueError("The pinned pipeline archive has no main.nf.")
            try:
                source.rename(target)
            except OSError:
                if not (target / "main.nf").is_file():
                    raise
    return {
        "tool": tool,
        "status": "Local pipeline source is available",
        "path": str(target),
    }


def host_command(tool):
    if tool == "nextflow" and os.name != "nt":
        launcher = native_nextflow_path()
        if launcher.is_file() and os.access(launcher, os.X_OK):
            return str(launcher)
    if tool in NATIVE_SEQUENCE_TOOLS and os.name != "nt":
        return native_sequence_command(ROOT, tool)
    if tool == "haplogrep" and os.name != "nt":
        wrapper = ROOT / "DNA_Software/UserData/Launcher/Native/bin/haplogrep"
        if wrapper.is_file() and os.access(wrapper, os.X_OK):
            return str(wrapper)
    return shutil.which(HOST_COMMANDS.get(tool, tool))


def native_brew():
    brew = Path(homebrew_bin()) / "brew"
    if brew.is_file() and os.access(brew, os.X_OK):
        return str(brew)
    return shutil.which("brew")


def install_native_sequence_tool(tool):
    binary = host_command(tool)
    if not binary:
        brew = native_brew()
        if not brew:
            if sys.platform == "darwin":
                raise ValueError("Install Homebrew, then retry the tool installation.")
            raise ValueError(
                f"Install {tool} with your Linux package manager or install Homebrew and retry."
            )
        subprocess.run([brew, "install", tool], check=True)
        binary = host_command(tool)
        if not binary:
            raise ValueError(
                f"{tool} is missing from the job search path after installation."
            )
    return {"tool": tool, "status": "Host program is available", "path": binary}


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
    if tool in NATIVE_PIPELINES and os.name != "nt":
        return (native_pipeline_source(tool) / "main.nf").is_file()
    if tool in DESKTOP_APPS:
        return desktop_tool_command(ROOT, tool) is not None
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
    if source.parent == bindir and source.name == name:
        return target
    if target.exists() or target.is_symlink():
        target.unlink()
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


HAPLOGREP_TREE = "trees/phylotree-fu-rcrs/1.3"
HAPLOGREP_TREE_ID = "phylotree-fu-rcrs@1.3"


def haplogrep_config(workspace):
    return (
        "port: 7001\nworkspace: "
        + json.dumps(str(workspace))
        + f"\nrepositories: []\nphylotrees:\n  - {HAPLOGREP_TREE}/tree.yaml\nexamples: []\n"
    )


def install_native_haplogrep():
    java = shutil.which("java")
    if not java:
        raise ValueError("Install Java 17 or later for this operating system first.")
    java = str(Path(java).resolve())
    dest = ROOT / "DNA_Software/UserData/Launcher/Native/Haplogrep"
    place_archive(fetch("haplogrep3-3-3-2-linux-tar-gz"), dest)
    jar = dest / "haplogrep3.jar"
    tree = dest / HAPLOGREP_TREE
    place_archive(fetch("haplogrep-default-tree"), tree)
    if not jar.is_file() or not (tree / "tree.yaml").is_file():
        raise ValueError("Haplogrep package or reference tree is incomplete.")
    workspace = ROOT / "DNA_Software/UserData/Haplogrep/jobs"
    workspace.mkdir(parents=True, exist_ok=True)
    (dest / "haplogrep3.yaml").write_text(haplogrep_config(workspace), encoding="utf-8")
    result = subprocess.run(
        [java, "-jar", str(jar), "trees"], cwd=dest, capture_output=True, timeout=30
    )
    if result.returncode or HAPLOGREP_TREE_ID.encode() not in result.stdout:
        detail = (
            (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        )
        raise ValueError(
            "Haplogrep could not load its local reference tree. " + detail[-1000:]
        )
    target = ROOT / "DNA_Software/UserData/Launcher/Native/bin/haplogrep"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "#!/bin/sh\ncd "
        + Q(str(dest))
        + " || exit 1\nexec "
        + Q(java)
        + ' -jar ./haplogrep3.jar "$@"\n'
    )
    temp = target.with_suffix(".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.chmod(0o755)
    temp.replace(target)
    return {
        "tool": "haplogrep",
        "status": "Local Java runtime ready",
        "path": str(target),
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


def status(task, filename="", *, allow_kiri=True):
    required = mapped(task, filename)
    host_packages = uses_host_tool_packages()
    needs_linux = os.name == "nt" and any(not skips_wsl(tool) for tool in required)
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
        search_path = "/opt/dna/envs/analysis/bin:/opt/dna/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        if not hardware.windows_arm64():
            search_path = (
                linux_path(ROOT / "DNA_Software/Linux/bin") + ":" + search_path
            )
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
            "PATH=" + search_path,
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
        if arm_guest and tool in {"mosdepth", "plink2"}:
            artifact = None
        if os.name != "nt" and tool == "haplogrep":
            artifact = "haplogrep3-3-3-2-linux-tar-gz"
        known = installed.get(tool)
        item = next((i for i in LOCK["items"] if i["id"] == artifact), {})
        if host_packages:
            if tool in LINUX_LOCAL and tool != "haplogrep":
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
        elif os.name != "nt" and tool in DESKTOP_APPS:
            known = host_tool_available(tool)
            if tool not in LINUX_LOCAL:
                artifact, item = None, {}
        elif os.name != "nt" and tool in LINUX_LOCAL:
            bindir = ROOT / "DNA_Software/Linux/bin"
            if tool == "java-windows":
                known = bool(find_named(ROOT / "DNA_Software/Linux/Java21", "java"))
            elif tool == "haplogrep":
                known = (bindir / "haplogrep").is_file()
            elif tool == "plink2":
                known = (bindir / "plink2").is_file()
            known = known or host_tool_available(tool)
        elif os.name != "nt":
            known = host_tool_available(tool)
        if os.name != "nt" and task in {"sarek", "pgs"} and tool == "docker":
            known = bool(known and native_pipeline_docker_socket())
        if task == "deepvariant" and tool == "deepvariant":
            known = deepvariant_regular_image(state)
        if task == "vep":
            if tool == "vep-cache":
                known = bool(kiri_vep_cache(ROOT))
        if os.name != "nt" and (tool in NATIVE_PIPELINES or tool == "nextflow"):
            installable = True
        elif os.name != "nt" and tool in NATIVE_SEQUENCE_TOOLS:
            bundled_recipe = tool == "mosdepth" and not host_packages
            installable = bool(known or bundled_recipe or native_brew())
        elif host_packages:
            installable = tool in {"seqviz", "haplogrep"}
        else:
            installable = not (os.name != "nt" and tool == "igv") and (
                (os.name != "nt" and tool in LINUX_LOCAL)
                or recipe not in ["manual", "windows-manual"]
            )
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
                "installable": installable,
                "version": item.get("version")
                or item.get("commit")
                or PIP.get(tool, "Paketquelle / nach Installation protokolliert"),
                "downloaded": bool(item and (ROOT / item["relative_path"]).is_file()),
                "downloadable": bool(artifact),
                "license_notice": LICENSE if tool == "rfmix" else "",
            }
        )
    reviewed = rfmix_license_reviewed()
    action = next(
        (entry["action"] for entry in CAT["tasks"] if entry["id"] == task), ""
    )
    kiri_tool = kiri_task_tool(action, required) if allow_kiri else None
    if action == "deepvariant" and allow_kiri and windows_deepvariant_gpu():
        for record in records:
            record.update(installed=True, state="Bereit")
        needs_linux = False
        kiri_tool = None
    if kiri_tool == "rfmix" and not reviewed:
        kiri_tool = None
    if kiri_tool == "vep" and not kiri_vep_cache(ROOT):
        kiri_tool = None
    if kiri_tool == "opencravat_run" and not kiri_opencravat_modules(ROOT):
        kiri_tool = None
    if kiri_tool and any(not record["installed"] for record in records):
        if kiri_sequence_tool(kiri_tool):
            for record in records:
                record.update(installed=True, state="Ready via local Kiri")
            needs_linux = False
    if (
        allow_kiri
        and task in WINDOWS_KIRI_PIPELINES
        and not (state["running"] and all(record["installed"] for record in records))
        and windows_kiri_pipeline(task)
    ):
        for record in records:
            record.update(installed=True, state="Ready via local Kiri")
        needs_linux = False
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


def rfmix_license_reviewed():
    from json import loads

    try:
        record = loads(
            (LOG / "rfmix-license-reviewed.json").read_text(encoding="utf-8")
        )
        return (
            isinstance(record, dict)
            and record.get("confirmed_by_user") is True
            and (
                record.get("notice_sha256")
                == hashlib.sha256(
                    (APP / "Notices/RFMIX-LICENSE.txt").read_bytes()
                ).hexdigest()
            )
        )
    except (OSError, ValueError):
        return False


def acknowledge_rfmix():
    import durable_store

    durable_store.write(
        LOG / "rfmix-license-reviewed.json",
        {
            "source": TOOLS["rfmix"][0],
            "notice": LICENSE,
            "notice_sha256": hashlib.sha256(
                (APP / "Notices/RFMIX-LICENSE.txt").read_bytes()
            ).hexdigest(),
            "confirmed_by_user": True,
            "time": datetime.datetime.now().astimezone().isoformat(),
        },
    )


def install_vep_cache():
    import tempfile

    cache = ROOT / "References/VEP"
    if not kiri_vep_cache(ROOT):
        archive = fetch("vep-cache-116-grch38")
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            stage = Path(directory)
            with tarfile.open(archive, "r|gz") as packed:
                packed.extractall(stage, filter="data")
            source = stage / "homo_sapiens/116_GRCh38"
            if not (source / "info.txt").is_file() or not any(source.glob("*/*.gz")):
                raise ValueError(
                    "The Ensembl archive does not contain the expected cache."
                )
            destination = cache / "homo_sapiens/116_GRCh38"
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                source.rename(destination)
            except OSError:
                if not kiri_vep_cache(ROOT):
                    raise
    return {"tool": "vep-cache", "path": str(cache), "status": "GRCh38 cache ready"}


class ImageBuildFailed(subprocess.CalledProcessError):
    """A Kiri image build failed. The message includes the builder output."""

    def __str__(self):
        captured = (self.stderr or b"") + (self.stdout or b"")
        text = captured.decode("utf-8", "replace").strip()
        base = super().__str__()
        if not text:
            return base
        return base + "\n" + text


def install_kiri_image(prefix, env, recipe, image, build_context):
    import tempfile

    dockerfile = str(ROOT / "DNA_Software/Start" / recipe)
    context = str(build_context)
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "image.tar"
        exported = subprocess.run(
            [
                *prefix,
                "build",
                "--output",
                f"type=docker,dest={archive}",
                "-t",
                image,
                "-f",
                dockerfile,
                context,
            ],
            env=env,
            capture_output=True,
        )
        if exported.returncode == 0:
            subprocess.run([*prefix, "load", "-i", str(archive)], env=env, check=True)
            return
        detail = (exported.stderr or b"") + (exported.stdout or b"")
        if b"exporter is not supported" not in detail.lower():
            raise ImageBuildFailed(
                exported.returncode,
                exported.args,
                exported.stdout,
                exported.stderr,
            )
    subprocess.run(
        [*prefix, "build", "-t", image, "-f", dockerfile, context],
        env=env,
        check=True,
    )


def rfmix_compile_lines(folder, dest, script):
    """Compile the pinned RFMix source after the architecture march check."""
    return [
        "cd " + Q(folder),
        "sh " + Q(script),
        "autoreconf --force --install",
        "./configure --prefix=" + Q(dest),
        "make -j2",
        "make install",
        "ln -sfn " + Q(dest + "/bin/rfmix") + " /opt/dna/bin/rfmix",
    ]


def install_kiri_rfmix(prefix, env):
    import tempfile

    acknowledge_rfmix()
    if not kiri_sequence_tool("rfmix"):
        source = fetch("slowkoni-rfmix", True)
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            shutil.copyfile(source, stage / "rfmix.tar.gz")
            shutil.copyfile(
                APP / "Notices/RFMIX-LICENSE.txt", stage / "RFMIX-LICENSE.txt"
            )
            shutil.copyfile(
                APP.parent / "Start/rfmix-march.sh", stage / "rfmix-march.sh"
            )
            install_kiri_image(
                prefix, env, "kiri-rfmix.Dockerfile", KIRI_RFMIX_IMAGE, stage
            )
    if not kiri_sequence_tool("rfmix"):
        raise RuntimeError("The RFMix image is unavailable in the local Kiri engine.")
    return {"tool": "rfmix", "status": "Ready via local Kiri"}


OPENCRAVAT_MODULE_VERSIONS = {
    "hg38": "1.47.2",
    "vcf-converter": "2.2.1",
    "textreporter": "2.1.0",
    "excelreporter": "2.1.1",
    "tagsampler": "1.1.6",
    "casecontrol": "1.2.0",
    "varmeta": "1.0.0",
    "vcfinfo": "3.2.0",
    "clinvar": "2026.11.01",
    "gnomad4": "4.1.4",
}


def install_opencravat_models(local):
    modules = ROOT / "References/OpenCRAVAT/modules"
    if not local:
        raise ValueError(
            "Start the local Kiri engine before installing OpenCRAVAT modules."
        )
    prefix, env = local
    route = kiri_sequence_tool("opencravat_run")
    if route is None:
        install_kiri_image(
            prefix,
            env,
            "kiri-opencravat.Dockerfile",
            KIRI_OPENCRAVAT_IMAGE,
            ROOT / "DNA_Software/Launcher/Locks",
        )
        route = kiri_sequence_tool("opencravat_run")
    if route is None:
        raise RuntimeError("The OpenCRAVAT image is unavailable in local Kiri.")
    if kiri_opencravat_modules(ROOT):
        return {
            "tool": "opencravat-models",
            "path": str(modules),
            "status": "Modules ready",
        }
    from engine import kiri_bind

    modules.mkdir(parents=True, exist_ok=True)
    command = [
        *prefix,
        "run",
        "--rm",
        "--pull=never",
        "--platform",
        route.platform,
        "--mount",
        kiri_bind(modules, "/modules"),
        "--entrypoint",
        "/bin/sh",
    ]
    setup = ""
    ca = ROOT / "DNA_Software/UserData/Launcher/Nextflow/local-ca.pem"
    if ca.is_file():
        command += ["--mount", kiri_bind(ca, "/local-ca.pem", readonly=True)]
        setup = (
            "cat /etc/ssl/certs/ca-certificates.crt /local-ca.pem >/tmp/ca.pem\n"
            "export REQUESTS_CA_BUNDLE=/tmp/ca.pem\n"
        )
    install_steps = [
        shlex.join(
            ["oc", "module", "install", "--md", "/modules", "-y", "-v", version, name]
        )
        for name, version in OPENCRAVAT_MODULE_VERSIONS.items()
    ]
    subprocess.run(
        [*command, route.image, "-ec", setup + "\n".join(install_steps)],
        env=env,
        check=True,
    )
    if not kiri_opencravat_modules(ROOT):
        raise RuntimeError(
            "OpenCRAVAT did not install all required module files and indices."
        )
    return {
        "tool": "opencravat-models",
        "path": str(modules),
        "status": "Modules ready",
    }


def fetch(artifact, license_reviewed=False):
    import tempfile

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
    expected_size = item.get("expected_bytes")
    if not expected_size:
        with tempfile.TemporaryDirectory(dir=p.parent) as directory:
            return fetch_verified(item, p, Path(directory) / "download.part")
    return fetch_verified(item, p, p.with_suffix(p.suffix + ".part"))


def fetch_verified(item, destination, part):
    if part.is_symlink():
        raise ValueError("Refusing a linked partial download.")
    expected_size = item.get("expected_bytes")
    headers = {"User-Agent": "DNAWorkbench-explicit-optional-download"}
    offset = part.stat().st_size if expected_size and part.is_file() else 0
    if expected_size and offset > expected_size:
        raise ValueError("Partial download is larger than the pinned archive.")
    if offset:
        headers["Range"] = f"bytes={offset}-"
    if not expected_size or offset != expected_size:
        with network_io.open_https(
            urllib.request.Request(item["url"], headers=headers), timeout=90
        ) as response:
            resume = offset and response.status == 206
            if resume and response.headers.get("Content-Range") != (
                f"bytes {offset}-{expected_size - 1}/{expected_size}"
            ):
                raise ValueError("The provider returned an unexpected download range.")
            size = offset if resume else 0
            with part.open("ab" if resume else "wb") as out:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if expected_size and size > expected_size:
                        raise ValueError("Download is larger than the pinned archive.")
                    out.write(chunk)
            if expected_size and size != expected_size:
                raise ValueError("Incomplete download. Retry to resume it.")
    with part.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != item["expected_sha256"]:
        part.unlink()
        raise ValueError("Download checksum is not correct.")
    part.replace(destination)
    return destination


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
    if tool == "rfmix" and not (license_reviewed or rfmix_license_reviewed()):
        raise ValueError(LICENSE)
    if tool == "vep-cache":
        return install_vep_cache()
    if tool in {"rfmix", "vep", "open-cravat", "opencravat-models"}:
        local = kiri_docker()
        if local and tool == "rfmix":
            return install_kiri_rfmix(*local)
        if local and tool == "vep":
            if not kiri_sequence_tool("vep"):
                prefix, env = local
                subprocess.run([*prefix, "pull", KIRI_VEP_IMAGE], env=env, check=True)
            if not kiri_sequence_tool("vep"):
                raise RuntimeError(
                    "The Ensembl VEP image is unavailable in local Kiri."
                )
            return install_vep_cache()
        if tool == "opencravat-models" or (local and tool == "open-cravat"):
            return install_opencravat_models(local)
    if os.name == "nt" and tool in NATIVE_PIPELINES and kiri_sequence_tool("nextflow"):
        state = linux_state()
        if not state["disk"] or state["wrong_location"]:
            fetch("nextflow-dist")
            return install_native_pipeline(tool)
    if os.name != "nt" and tool in NATIVE_PIPELINES:
        return install_native_pipeline(tool)
    if os.name != "nt" and tool == "nextflow":
        return install_native_nextflow()
    arm_guest = hardware.windows_arm64()
    if os.name != "nt" and tool == "haplogrep":
        return install_native_haplogrep()
    if os.name != "nt" and tool in NATIVE_SEQUENCE_TOOLS:
        if (
            tool == "mosdepth"
            and not uses_host_tool_packages()
            and not host_command(tool)
        ):
            return install_linux_local(tool)
        return install_native_sequence_tool(tool)
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
    if os.name != "nt" and tool in DESKTOP_APPS:
        command = desktop_tool_command(ROOT, tool)
        if command:
            return {"tool": tool, "status": "Host program is available"}
        if tool not in LINUX_LOCAL:
            raise ValueError("Install a compatible desktop build on the host.")
    if os.name != "nt" and tool in LINUX_LOCAL:
        return install_linux_local(tool)
    if os.name != "nt":
        hosted = install_on_linux_host(tool)
        if hosted:
            return hosted
    companion = None
    if (
        os.name == "nt"
        and tool in WINDOWS_COMPANION
        and not (arm_guest and tool in {"plink2", "haplogrep"})
    ):
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
        lines += rfmix_compile_lines(
            folder, dest, linux_path(APP.parent / "Start/rfmix-march.sh")
        )
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
            "NXF_VER="
            + Q(NEXTFLOW_DIST["version"])
            + " NXF_HOME=/opt/dna/cache/nextflow /opt/dna/bin/nextflow -version",
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
            "export NXF_HOME=/opt/dna/cache/nextflow\nexport NXF_ASSETS=/opt/dna/sources/nextflow-assets\nexport NXF_VER="
            + Q(NEXTFLOW_DIST["version"])
            + "\nunset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH\nexport DOCKER_HOST=unix:///run/docker-dna.sock\nexec /opt/dna/bin/nextflow run "
            + Q(folder)
            + " -profile docker -c "
            + Q(linux_path(ROOT / "DNA_Software/Start/dna-nextflow.config"))
            + ' "$@"'
        )
        wrapper(tool, body)
        lines.append("test -f " + Q(folder + "/main.nf"))
    elif tool == "docker":
        apt("docker.io")
        lines.append("usermod -aG docker dna")
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
    elif tool == "plink2" and arm_guest:
        apt("plink2")
        lines += [
            "/usr/bin/plink2 --version",
            "for flag in make-pgen make-king-table pca indep-pairwise export; do",
            '  /usr/bin/plink2 --help "$flag" | grep -F -- "--$flag" >/dev/null || {',
            '    printf "Installed PLINK 2 lacks required option: %s\\n" "$flag" >&2',
            "    exit 1",
            "  }",
            "done",
            "ln -sfn /usr/bin/plink2 /opt/dna/bin/plink2",
        ]
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
        apt("unzip openjdk-21-jre-headless")
        dest = "/opt/dna/tools/haplogrep3"
        config = haplogrep_config(
            linux_path(ROOT / "DNA_Software/UserData/Haplogrep/jobs")
        )
        lines += [
            "mkdir -p " + dest,
            "tar -xzf " + Q(linux_path(archive)) + " -C " + dest,
            "mkdir -p " + dest + "/" + HAPLOGREP_TREE,
            "unzip -o " + Q(linux_path(tree)) + " -d " + dest + "/" + HAPLOGREP_TREE,
            "printf %s " + Q(config) + " > " + dest + "/haplogrep3.yaml",
            "(cd "
            + dest
            + " && java -jar ./haplogrep3.jar trees | grep -F -- "
            + Q(HAPLOGREP_TREE_ID)
            + ")",
        ]
        wrapper("haplogrep", "cd " + dest + '\nexec java -jar ./haplogrep3.jar "$@"')
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
            acknowledge_rfmix()
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
