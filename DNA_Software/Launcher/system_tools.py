"""Resolve Windows host tools from the OS directory rather than the working folder."""

from pathlib import Path
from typing import NamedTuple
import os
import json
import platform
import re
import shutil
import subprocess
import sys

HOST_TOOLS = {
    "wsl.exe": "System32/wsl.exe",
    "powershell.exe": "System32/WindowsPowerShell/v1.0/powershell.exe",
    "cmd.exe": "System32/cmd.exe",
    "notepad.exe": "System32/notepad.exe",
    "expand.exe": "System32/expand.exe",
}


def windows_executable(name):
    if name not in HOST_TOOLS:
        raise ValueError("Unknown Windows host tool")
    if os.name != "nt":
        raise OSError("This action requires Windows")
    import ctypes

    directory = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetWindowsDirectoryW(directory, len(directory))
    if not 0 < length < len(directory):
        raise OSError("Cannot locate the Windows directory")
    result = Path(directory.value) / HOST_TOOLS[name]
    if not result.is_file():
        raise OSError("Windows host tool is not installed: " + name)
    return str(result)


DESKTOP_APPS = {
    "gramps": (("gramps",), ("Gramps",)),
    "igv": (("igv",), ("IGV",)),
    "jbrowse": (
        ("jbrowse-desktop", "jbrowse-desktop.AppImage"),
        ("JBrowse 2", "JBrowse Desktop"),
    ),
    "ugene": (("ugene", "ugeneui"), ("UGENE",)),
}


NATIVE_SEQUENCE_TOOLS = frozenset({"samtools", "bcftools", "fastp", "mosdepth"})
KIRI_BCFTOOLS_IMAGE = (
    "quay.io/biocontainers/bcftools@"
    "sha256:8c35865074cbcbeb59217e9cf1f7819ccc12301811bf0c086d57b364f3fa175b"
)
KIRI_LOCAL_BCFTOOLS_IMAGE = "dna-workbench/bcftools:1.21-1"
KIRI_SEQUENCE_IMAGE = "dna-workbench/sequence-tools:1"
KIRI_ALIGNMENT_IMAGE = "dna-workbench/alignment-qc:1"
KIRI_PLINK_IMAGE = "dna-workbench/plink:2"
KIRI_PCA_IMAGE = "dna-workbench/pca:1"
KIRI_BEAGLE_IMAGE = "dna-workbench/beagle:1"
KIRI_HAP_IBD_IMAGE = "dna-workbench/hap-ibd:1"
KIRI_PEDDY_IMAGE = "dna-workbench/peddy:1"
KIRI_WHATSHAP_IMAGE = "dna-workbench/whatshap:1"
KIRI_TRUVARI_IMAGE = "dna-workbench/truvari:1"
KIRI_HAPLOGREP_IMAGE = "dna-workbench/haplogrep:1"
KIRI_YHAPLO_IMAGE = "dna-workbench/yhaplo:1"
KIRI_PHARMCAT_IMAGE = "dna-workbench/pharmcat:1"
KIRI_GATK_IMAGE = "dna-workbench/gatk:1"
KIRI_VARIANTS_IMAGE = "dna-workbench/variants:2"
KIRI_OPENCRAVAT_IMAGE = "dna-workbench/opencravat:1"
KIRI_RFMIX_IMAGE = "dna-workbench/rfmix:1"
KIRI_NEXTFLOW_SOCKET = "/var/lib/kiri-daemon/.kiri/run/docker.sock"
KIRI_NEXTFLOW_IMAGE = (
    "docker.io/nextflow/nextflow@"
    "sha256:0fb911ca7a96ca9632f8b4387affbc8f402b0fd06d4d2e41993563173c724d0e"
)
KIRI_NEXTFLOW_IMAGE_ID = (
    "sha256:d1578f61b730db2661159ba868628a074466716d7758f218b88123f60f08b282"
)
KIRI_DEEPVARIANT_IMAGE = (
    "docker.io/google/deepvariant@"
    "sha256:962e5a83b1d76aae6990625d47102785f791603f2138aa1fa9aa4fb6a2eecbe6"
)
# Config digest from the pinned manifest. Docker archives may omit RepoDigests.
KIRI_DEEPVARIANT_IMAGE_ID = (
    "sha256:96e40015101d9178131fe129456345a225c0bd3c3dfe6c7da79a8355b3710506"
)
DEEPVARIANT_GPU_PROBE = (
    "import tensorflow as tf; "
    "tf.config.set_soft_device_placement(False)\n"
    "with tf.device('/GPU:0'):\n"
    "    assert float(tf.linalg.matmul(tf.ones([1,1]), tf.ones([1,1])).numpy()[0,0]) == 1"
)
DEEPVARIANT_GPU_IMAGE = (
    "docker.io/google/deepvariant@"
    "sha256:78fb1bb960f3b74a4308b62ba8b6232723d4c75e16a4a50f0d810d7086467dd1"
)
KIRI_VEP_IMAGE = (
    "docker.io/ensemblorg/ensembl-vep@"
    "sha256:6972667883d89b9fa55e5cbe94f1b4c259ebc6bbd178310cef78f617e055eb75"
)
# Config digests from the pinned index's Linux manifests. Docker archives may omit RepoDigests.
KIRI_VEP_IMAGE_IDS = {
    "amd64": "sha256:8883fa3fe22513f53a6209d037c426916aaf15fd2541f695a63c41c03940dec5",
    "arm64": "sha256:faa2f666c401a70c7922bd9bf5f53c81570183e57b24aac2f5bd27211403eca8",
}
KIRI_TASK_TOOLS = {
    "variant_convert": {"bcftools"},
    "vcf_qc": {"bcftools"},
    "filter": {"bcftools"},
    "merge": {"bcftools"},
    "normalize": {"bcftools", "samtools"},
    "inspect": {"bcftools", "samtools", "snps"},
    "fastq_qc": {"fastp"},
    "fastq_report": {"fastp"},
    "bam_qc": {"samtools", "mosdepth", "multiqc"},
    "multiqc": {"multiqc"},
    "roh": {"plink19"},
    "kinship": {"plink2"},
    "ref_export": {"plink2", "bcftools"},
    "pca": {"plink2", "plotly"},
    "beagle": {"beagle"},
    "ibd": {"hap-ibd"},
    "peddy": {"peddy", "bcftools"},
    "whatshap": {"whatshap", "samtools"},
    "truvari": {"truvari", "bcftools", "samtools"},
    "mito": {"haplogrep", "bcftools"},
    "yhaplo": {"yhaplo", "bcftools"},
    "pharmcat": {"pharmcat"},
    "gatk_validate": {"gatk", "samtools"},
    "compare": {"pysam"},
    "chip_vcf": {"snps", "pysam", "samtools"},
    "vep": {"vep", "vep-cache"},
    "opencravat_run": {"open-cravat", "opencravat-models"},
    "rfmix": {"rfmix"},
    "deepvariant": {"deepvariant", "samtools", "docker"},
}


def kiri_opencravat_modules(root):
    modules = root / "References/OpenCRAVAT/modules"
    required = {
        "converters": ("vcf-converter",),
        "mappers": ("hg38",),
        "reporters": ("textreporter", "excelreporter"),
        "annotators": ("clinvar", "gnomad4"),
        "postaggregators": ("tagsampler", "casecontrol", "varmeta", "vcfinfo"),
    }
    if any(
        not (modules / category / name / (name + ".yml")).is_file()
        for category, names in required.items()
        for name in names
    ):
        return None
    if not (modules / "annotators/clinvar/data/clinvar.sqlite").is_file():
        return None
    gnomad = modules / "annotators/gnomad4/data"
    for chrom in (*range(1, 23), "X"):
        vcf = gnomad / f"chr{chrom}.vcf.gz"
        if not vcf.is_file() or not any(
            vcf.with_name(vcf.name + suffix).is_file() for suffix in (".tbi", ".csi")
        ):
            return None
    return modules


def kiri_vep_cache(root):
    cache = root / "References" / "VEP"
    assembly = cache / "homo_sapiens" / "116_GRCh38"
    return (
        cache
        if (assembly / "info.txt").is_file() and any(assembly.glob("*/*.gz"))
        else None
    )


def kiri_task_tool(action, required):
    tools = KIRI_TASK_TOOLS.get(action, ())
    if len(tools) > 1 and action != "inspect" and set(required) == tools:
        return action
    if len(required) == 1 and required[0] in tools:
        return required[0]
    return None


class KiriRoute(NamedTuple):
    prefix: list[str]
    env: dict[str, str]
    platform: str
    image: str


def windows_deepvariant_gpu():
    if os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}:
        return None
    docker = shutil.which("docker")
    if not docker or not Path(docker).is_absolute():
        return None
    prefix = [docker, "--host", "npipe:////./pipe/dockerDesktopLinuxEngine"]
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("DOCKER_")}
    try:
        result = subprocess.run(
            [
                *prefix,
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
                DEEPVARIANT_GPU_IMAGE,
                "-c",
                DEEPVARIANT_GPU_PROBE,
            ],
            env=env,
            capture_output=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0:
        return KiriRoute(prefix, env, "linux/amd64", DEEPVARIANT_GPU_IMAGE)
    return None


def kiri_windows_pipe_exists():
    import ctypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    wait = kernel.WaitNamedPipeW
    wait.argtypes = (ctypes.c_wchar_p, ctypes.c_uint32)
    if wait(r"\\.\pipe\kiri", 1):
        return True
    # The endpoint also exists when all instances are busy or the wait timed out.
    return ctypes.get_last_error() in {121, 231}


def kiri_docker():
    if os.name == "nt":
        endpoint = "npipe:////./pipe/kiri"
        if not kiri_windows_pipe_exists():
            return None
    elif sys.platform == "darwin":
        endpoint = "unix://" + str(Path.home() / ".kiri/run/docker.sock")
    elif sys.platform.startswith("linux"):
        endpoint = "unix:///run/kiri/docker.sock"
    else:
        return None
    if endpoint.startswith("unix://") and not Path(endpoint[7:]).is_socket():
        return None
    search = os.environ.get("PATH", os.defpath).split(os.pathsep)
    search = [directory for directory in search if os.path.isabs(directory)]
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        search.append(str(Path(os.environ["LOCALAPPDATA"]) / "Kiri/bin"))
    elif sys.platform == "darwin":
        search.append(str(Path.home() / ".kiri/bin"))
    elif sys.platform.startswith("linux"):
        search.append("/usr/libexec/kiri")
    docker = shutil.which("docker", path=os.pathsep.join(search))
    if not docker or not Path(docker).is_absolute():
        return None
    # An explicit socket must win over any configured context or remote host.
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("DOCKER_")
    }
    return [docker, "--host", endpoint], env


def kiri_sequence_tool(tool):
    """Select a cached image for the local Kiri engine's architecture."""
    if tool not in {
        "bcftools",
        "samtools",
        "fastp",
        "bam_qc",
        "normalize",
        "multiqc",
        "plink19",
        "plink2",
        "ref_export",
        "pca",
        "beagle",
        "hap-ibd",
        "peddy",
        "whatshap",
        "truvari",
        "mito",
        "yhaplo",
        "pharmcat",
        "gatk_validate",
        "pysam",
        "snps",
        "chip_vcf",
        "vep",
        "opencravat_run",
        "rfmix",
        "deepvariant",
        "nextflow",
    }:
        return None
    local = kiri_docker()
    if not local:
        return None
    args, env = local

    def probe(*command, timeout=4):
        result = subprocess.run(
            [*args, *command],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    try:
        architecture = probe("version", "--format", "{{.Server.Arch}}").lower()
        architecture = {
            "amd64": "amd64",
            "x86_64": "amd64",
            "arm64": "arm64",
            "aarch64": "arm64",
        }.get(architecture)
        if not architecture:
            return None
        rosetta = (
            tool == "deepvariant"
            and architecture == "arm64"
            and sys.platform == "darwin"
        )
        if (
            tool in {"deepvariant", "nextflow"}
            and architecture != "amd64"
            and not rosetta
        ):
            return None
        image_architecture = "amd64" if rosetta else architecture
        candidates = [
            {
                "bam_qc": KIRI_ALIGNMENT_IMAGE,
                "multiqc": KIRI_ALIGNMENT_IMAGE,
                "plink19": KIRI_PLINK_IMAGE,
                "plink2": KIRI_PLINK_IMAGE,
                "ref_export": KIRI_PLINK_IMAGE,
                "pca": KIRI_PCA_IMAGE,
                "beagle": KIRI_BEAGLE_IMAGE,
                "hap-ibd": KIRI_HAP_IBD_IMAGE,
                "peddy": KIRI_PEDDY_IMAGE,
                "whatshap": KIRI_WHATSHAP_IMAGE,
                "truvari": KIRI_TRUVARI_IMAGE,
                "mito": KIRI_HAPLOGREP_IMAGE,
                "yhaplo": KIRI_YHAPLO_IMAGE,
                "pharmcat": KIRI_PHARMCAT_IMAGE,
                "gatk_validate": KIRI_GATK_IMAGE,
                "pysam": KIRI_VARIANTS_IMAGE,
                "snps": KIRI_VARIANTS_IMAGE,
                "chip_vcf": KIRI_VARIANTS_IMAGE,
                "vep": KIRI_VEP_IMAGE,
                "opencravat_run": KIRI_OPENCRAVAT_IMAGE,
                "rfmix": KIRI_RFMIX_IMAGE,
                "deepvariant": KIRI_DEEPVARIANT_IMAGE,
                "nextflow": KIRI_NEXTFLOW_IMAGE,
            }.get(tool, KIRI_SEQUENCE_IMAGE)
        ]
        if tool in {"plink19", "plink2"}:
            candidates.append("dna-workbench/plink:1")
        if tool == "pysam":
            candidates.append("dna-workbench/variants:1")
        if tool == "deepvariant":
            candidates.append(KIRI_DEEPVARIANT_IMAGE_ID)
        if tool == "nextflow":
            candidates.append(KIRI_NEXTFLOW_IMAGE_ID)
        if tool == "vep":
            candidates.append(KIRI_VEP_IMAGE_IDS[image_architecture])
        if tool == "bcftools":
            candidates.append(KIRI_LOCAL_BCFTOOLS_IMAGE)
            if architecture == "amd64":
                candidates.insert(0, KIRI_BCFTOOLS_IMAGE)
        for candidate in candidates:
            details = probe("image", "inspect", "--format", "{{json .}}", candidate)
            if not details:
                continue
            image = json.loads(details)
            if not isinstance(image, dict):
                continue
            if (
                image.get("Os") != "linux"
                or image.get("Architecture") != image_architecture
            ):
                continue
            if candidate.startswith("sha256:"):
                if image.get("Id") != candidate:
                    continue
            elif "@sha256:" not in candidate:
                # Kiri 0.2 omits image labels from inspect. This tag is created
                # by the explicit local setup, then resolved to an immutable ID.
                image_id = image.get("Id", "")
                if not isinstance(image_id, str) or not re.fullmatch(
                    r"sha256:[0-9a-f]{64}", image_id
                ):
                    continue
                candidate = image_id
            container_platform = "linux/" + image_architecture
            if (
                rosetta
                and probe(
                    "run",
                    "--rm",
                    "--pull=never",
                    "--platform",
                    container_platform,
                    "--network=none",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:rw,nosuid,nodev,size=64m",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "-e",
                    "CUDA_VISIBLE_DEVICES=",
                    "--entrypoint",
                    "/usr/bin/python3",
                    candidate,
                    "-c",
                    "import tensorflow as tf; "
                    "assert float(tf.reduce_sum(tf.nn.conv2d(tf.ones([1,3,3,1]), "
                    "tf.ones([2,2,1,1]), strides=1, padding='VALID')).numpy()) == 16; "
                    "print('DNA_DEEPVARIANT_CPU_OK')",
                    timeout=30,
                )
                != "DNA_DEEPVARIANT_CPU_OK"
            ):
                return None
            return KiriRoute(args, env, container_platform, candidate)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    return None


def linux_x64_bundle():
    return sys.platform.startswith("linux") and platform.machine().lower() in {
        "x86_64",
        "amd64",
    }


def homebrew_bin():
    if sys.platform == "darwin":
        if platform.machine().lower() in {"arm64", "aarch64"}:
            return "/opt/homebrew/bin"
        return "/usr/local/bin"
    return "/home/linuxbrew/.linuxbrew/bin"


def native_sequence_command(root, tool):
    """Use the same directory order as native analysis scripts."""
    path = os.environ.get("PATH", os.defpath).split(os.pathsep)
    path = [directory for directory in path if os.path.isabs(directory)]
    if sys.platform.startswith("linux"):
        path[:0] = ["/opt/dna/envs/analysis/bin", "/opt/dna/bin"]
    if linux_x64_bundle():
        path.insert(0, str(root / "DNA_Software/Linux/bin"))
    path.append(homebrew_bin())
    return shutil.which(tool, path=os.pathsep.join(path))


def desktop_tool_command(root, tool, filename=None):
    """Resolve a supported native desktop program and its argument vector."""
    linux_names, mac_names = DESKTOP_APPS[tool]
    arguments = [str(Path(filename).resolve())] if filename else []
    if sys.platform == "darwin":
        for folder in (Path("/Applications"), Path.home() / "Applications"):
            for name in mac_names:
                bundle = folder / (name + ".app")
                if (bundle / "Contents/Info.plist").is_file():
                    return ["/usr/bin/open", "-a", str(bundle), *arguments]
        return None
    if not sys.platform.startswith("linux"):
        return None
    if linux_x64_bundle():
        folder = root / "DNA_Software/Linux/bin"
        for name in linux_names:
            binary = folder / name
            if binary.is_file() and os.access(binary, os.X_OK):
                return [str(binary), *arguments]
    for name in linux_names:
        binary = shutil.which(name)
        if binary:
            return [str(Path(binary).resolve()), *arguments]
    return None
