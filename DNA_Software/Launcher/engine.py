from system_tools import (
    DEEPVARIANT_GPU_PROBE,
    desktop_tool_command,
    homebrew_bin,
    KIRI_NEXTFLOW_SOCKET,
    KIRI_TASK_TOOLS,
    kiri_task_tool,
    kiri_opencravat_modules,
    kiri_vep_cache,
    kiri_sequence_tool,
    linux_x64_bundle,
    windows_deepvariant_gpu,
    windows_executable,
)

"""Portable local job runner for DNA Workbench. Never uploads DNA files."""
from portable_paths import distro_name
from pathlib import Path, PurePosixPath
import sys, os, subprocess, shlex, time, datetime, traceback, hashlib, csv, zipfile, html, re, socket, threading, gzip, shutil
import portable_json as json
import source_store
import security_paths
import inspector
import hardware
import platform

ROOT = Path(__file__).resolve().parents[2]
CAT = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
TASKS = {t["id"]: t for t in CAT["tasks"]}
CORE = ROOT / "DNA_Software/Start/DNA.ps1"
NOW = lambda: datetime.datetime.now().astimezone().isoformat()
Q = shlex.quote
VARIANT_FORMATS = {
    "VCF.gz (BGZF)": ("z", "converted.vcf.gz"),
    "VCF": ("v", "converted.vcf"),
    "BCF": ("b", "converted.bcf"),
}


def variant_filter_options(values):
    terms = []
    if values.get("pass_only") == "PASS only":
        terms.append('FILTER="PASS"')
    elif values.get("pass_only") != "All entries":
        terms.append('(FILTER="PASS" || FILTER=".")')
    for key in ("dp", "gq"):
        threshold = int(values.get(key) or 0)
        if threshold < 0:
            raise ValueError("Thresholds shall be at least 0.")
        if threshold:
            terms.append("FMT/" + key.upper() + ">=" + str(threshold))
    return ["-i", " && ".join(terms)] if terms else []


def reference_panel(values):
    panels = {
        "1000 Genomes GRCh38": "1000G_GRCh38/all_hg38",
        "HGDP GRCh38": "HGDP_GRCh38/hgdp_statphase",
    }
    selected = values.get("panel")
    if selected not in panels:
        raise ValueError("Select an installed GRCh38 reference panel.")
    prefix = ROOT / "References" / panels[selected]
    suffixes = (".pgen", ".pvar.zst", ".psam")
    if any(not prefix.with_suffix(suffix).is_file() for suffix in suffixes):
        raise ValueError(
            "Reference panel is not installed or incomplete: " + prefix.name
        )
    chrom = values.get("chrom")
    if chrom not in {str(n) for n in range(1, 23)}:
        raise ValueError("Select a chromosome between 1 and 22.")
    return prefix, suffixes, chrom


def kiri_bind(path, target, readonly=False, *, desktop=False):
    import io

    source = str(Path(path).resolve()) if desktop else linux(path)
    fields = ["type=bind", "source=" + source, "target=" + target]
    if readonly:
        fields.append("readonly")
    value = io.StringIO()
    csv.writer(value).writerow(fields)
    return value.getvalue().removesuffix("\r\n")


def atomic(path, obj):
    import durable_store

    durable_store.write(path, obj)


def linux(path):
    """Path inside the Linux tool host.

    On Windows that host is the WSL distro, so a drive-letter file becomes
    /mnt/<drive>/... On Linux the file is already on the host and is used as-is.
    """
    p = Path(path).resolve()
    if os.name != "nt":
        return p.as_posix()
    if len(p.drive) != 2 or p.drive[1] != ":":
        raise ValueError(
            "Select local drive files for WSL. Copy network files to the SSD first."
        )
    return "/mnt/" + p.drive[0].lower() + "/" + p.as_posix()[3:]


def analysis_python():
    """Interpreter for the bash job helpers.

    Windows runs those helpers inside WSL, where the portable env lives at
    /opt/dna. Linux uses that env when it is present and the host Python otherwise.
    """
    bundled = "/opt/dna/envs/analysis/bin/python"
    if os.name != "nt" and not Path(bundled).is_file():
        return sys.executable
    return bundled


def recorded_installation():
    """Copy the Windows setup snapshot when one exists.

    Linux jobs do not create that WSL verification file. They still record that
    no snapshot was available instead of failing before the tool runs.
    """
    path = ROOT / "DNA_Software/Logs/installation-verification.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "recorded": False,
        "note": "This host has no installation-verification snapshot. The job uses the tools on its PATH.",
    }


def wsl_host_bootstrap(action):
    """Prepare the Windows WSL distro before a bash job.

    Native Linux already runs the same script with the host shell, so it does
    not call PowerShell or wsl.exe.
    """
    if os.name != "nt":
        return []

    def powershell(step):
        return [
            windows_executable("powershell.exe"),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(CORE),
            "-Action",
            step,
        ]

    commands = [powershell("Start")]
    if action in ["sarek", "deepvariant", "pgs"]:
        commands.append(powershell("Docker"))
    return commands


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def page(path, title, body):
    path.write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>'
        + html.escape(title)
        + '</title><style>body{font:16px Segoe UI,Arial;max-width:1080px;margin:40px auto;color:#193047;padding:20px}h1{color:#07877f}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #dee5ed}pre{white-space:pre-wrap;background:#f1f5f7;padding:20px}a{color:#087f82}@media print{button{display:none}}</style><button onclick="window.print()">Print / save as PDF</button><h1>'
        + html.escape(title)
        + "</h1>"
        + body
        + "</html>",
        encoding="utf-8",
    )


class Job:
    def __init__(self, request):
        self.request_path = Path(request).resolve()
        self.folder = self.request_path.parent
        if not self.folder.is_relative_to((ROOT / "Projects/Launcher").resolve()):
            raise ValueError("Unexpected job folder.")
        self.r = json.loads(self.request_path.read_text(encoding="utf-8-sig"))
        self.task = TASKS[self.r["task"]]
        self.v = self.r.get("inputs", {})
        self.id = self.folder.name
        self.out = self.folder / "Results"
        self.out.mkdir(exist_ok=True)
        self.person = self.r.get("person", "P001_Ich")
        if not re.fullmatch("[A-Za-z0-9_-]+", self.person):
            raise ValueError("Invalid person identifier.")
        self.log_path = self.folder / "auftrag.log"
        self.log_handle = self.log_path.open("a", encoding="utf-8", buffering=1)
        self.state = {
            "id": self.id,
            "task": self.task["id"],
            "title": self.task["title"],
            "person": self.person,
            "started": NOW(),
            "updated": NOW(),
            "status": "Preparing",
            "pid": os.getpid(),
            "output": str(self.out),
            "kind": self.task["kind"],
            "inputs": self.v,
            "steps": [],
        }
        self.save()

    def save(self):
        self.state["updated"] = NOW()
        atomic(self.folder / "status.json", self.state)
        if self.state.get("status") in ("Complete", "Failed", "Cancelled", "Started"):
            import execution_journal

            execution_journal.register(self.folder)

    def log(self, s):
        s = str(s)
        self.log_handle.write(s + "\n")
        print(s, flush=True)

    def validate(self):
        for f in self.task["fields"]:
            val = self.v.get(f["key"], "")
            if f["required"] and (not val or str(val).startswith("Please select")):
                raise ValueError("Please select Entry:" + f["label"])
            if val and f["kind"] in ["file", "folder"]:
                vals = val if isinstance(val, list) else [val]
                for p in vals:
                    if not Path(p).exists():
                        raise ValueError("File/folder not accessible:" + str(p))
                    if f["kind"] == "file" and not Path(p).is_file():
                        raise ValueError("Select a file:" + str(p))
        import tool_contracts, workflow_sources

        for field in self.task["fields"]:
            value = self.v.get(field["key"])
            if field["kind"] != "file" or not value:
                continue
            for path in value if isinstance(value, list) else [value]:
                meta = workflow_sources.metadata(path)
                meta["build"] = meta.get("build") or self.v.get("build", "")
                gate = tool_contracts.evaluate(self.task, field, path, meta)
                if not gate["accepted"]:
                    raise ValueError(field["label"] + ": " + "; ".join(gate["issues"]))

    def p(self, key):
        return linux(self.v[key])

    def o(self, name=""):
        return linux(self.out / name)

    def shell(self, kiri_pipeline=False):
        a = self.task["action"]
        v = self.v
        cpu_limit = hardware.cpu_threads()
        # Resolve the Linux-visible CPU count at execution time, including a smaller WSL allocation.
        threads = '"$dna_threads"'
        extra_threads = '"$((dna_threads - 1))"'
        heavy_workers = '"$((dna_threads < 4 ? dna_threads : 4))"'
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            *(
                [
                    ("DNA_WSL_PROFILE=1 " if os.name == "nt" else "")
                    + "source "
                    + Q(linux(ROOT / "DNA_Software/Start/profile-dna.sh")),
                ]
                if sys.platform != "darwin" and not kiri_pipeline
                else []
            ),
            *(
                ["export PATH=" + Q(linux(ROOT / "DNA_Software/Linux/bin")) + ":$PATH"]
                if not kiri_pipeline
                and (
                    (os.name == "nt" and not hardware.windows_arm64())
                    or linux_x64_bundle()
                )
                else []
            ),
            *(["export PATH=$PATH:" + Q(homebrew_bin())] if os.name != "nt" else []),
            "export PYTHONUNBUFFERED=1",
            "dna_threads=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)",
            f"(( dna_threads <= {cpu_limit} )) || dna_threads={cpu_limit}",
            "export DNA_WORKBENCH_CPUS=$dna_threads",
            *(
                ["echo $$ > " + Q(linux(self.folder / "linux.pid"))]
                if not kiri_pipeline
                else []
            ),
            "mkdir -p " + Q(self.o()),
            "cd " + Q(self.o()),
        ]
        helper = linux(Path(__file__).with_name("linux_helpers.py"))

        def cmd(*args, thread_options=(), replace_shell=False):
            command, *arguments = args
            head = ("exec " if replace_shell else "") + Q(command)
            if command in {"plink19", "plink2"}:
                head += " --threads " + threads
            if (
                command == "bcftools"
                and arguments[0] in {"index", "norm", "view", "merge"}
                or command == "samtools"
                and arguments[0] == "index"
            ):
                # HTSlib counts these workers in addition to the main thread.
                flag = "-@" if command == "samtools" else "--threads"
                thread_options = (*thread_options, flag, extra_threads)
            lines.append(
                " ".join([head, *(Q(str(x)) for x in arguments), *thread_options])
            )

        def py(*args):
            cmd(
                "/usr/bin/python3" if kiri_pipeline else analysis_python(),
                helper,
                *args,
            )

        def pipeline(tool, *args, thread_options=(), params_file=None):
            work = linux(self.folder / "nextflow-work")
            params_options = ["-params-file", linux(params_file)] if params_file else []
            if os.name == "nt" and not kiri_pipeline:
                cmd(
                    tool,
                    "-w",
                    work,
                    *params_options,
                    *args,
                    thread_options=thread_options,
                )
                return
            import on_demand

            source = on_demand.native_pipeline_source(tool)
            endpoint = (
                "/var/run/docker.sock"
                if kiri_pipeline
                else on_demand.native_pipeline_docker_socket()
            )
            profile = "docker"
            if (
                not kiri_pipeline
                and sys.platform == "darwin"
                and platform.machine().lower() in {"arm64", "aarch64"}
            ):
                if tool == "sarek":
                    profile += ",emulate_amd64"
                elif tool == "pgsc-calc":
                    profile += ",arm"
            lines.extend(
                [
                    "test -f "
                    + Q(linux(source / "main.nf"))
                    + " || { printf '%s\\n' "
                    + Q("Install the pinned pipeline through the tool library: " + tool)
                    + " >&2; exit 1; }",
                    *(
                        [
                            "printf '%s\\n' "
                            + Q(
                                "Start a local Docker-compatible engine before running "
                                + tool
                            )
                            + " >&2; exit 1"
                        ]
                        if not endpoint
                        else []
                    ),
                    "unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH",
                    "export DOCKER_HOST="
                    + Q("unix://" + (endpoint or "/var/run/docker.sock")),
                    "export NXF_HOME="
                    + Q(linux(ROOT / "DNA_Software/UserData/Launcher/Nextflow")),
                    "export NXF_VER=" + Q(on_demand.NEXTFLOW_DIST["version"]),
                ]
            )
            if kiri_pipeline:
                lines.append("export DOCKER_CONFIG=/tmp/dna-nextflow-docker")
            cmd(
                "/opt/dna-nextflow"
                if kiri_pipeline
                else on_demand.host_command("nextflow") or "nextflow",
                "run",
                linux(source),
                "-profile",
                profile,
                "-c",
                linux(ROOT / "DNA_Software/Start/dna-nextflow.config"),
                "-w",
                work,
                *params_options,
                *args,
                thread_options=thread_options,
                replace_shell=kiri_pipeline,
            )

        def prepared(source, name):
            target = self.o(name + ".vcf.gz")
            cmd(
                "bcftools",
                "sort",
                source,
                "-m",
                "1G",
                "-Oz",
                "-o",
                target,
                "-T",
                self.o(name + "_sort.XXXXXX"),
            )
            cmd("bcftools", "index", "-ft", target)
            return target

        def reference():
            source = self.p("reference")
            dest = self.o("referenz.fa")
            cmd("ln", "-s", source, dest)
            cmd("samtools", "faidx", dest)
            return dest

        def plink_input():
            source = self.p("file")
            dest = self.o("kohorte")
            common = [
                "--chr",
                "1-22",
                "--max-alleles",
                "2",
                "--snps-only",
                "just-acgt",
                "--geno",
                "0.05",
                "--make-pgen",
                "--out",
                dest,
            ]
            if source.endswith(".pgen"):
                prefix = source[:-5]
                flags = ["--pfile", prefix]
                if Path(self.v["file"]).with_suffix(".pvar.zst").exists():
                    flags += ["vzs"]
                cmd("plink2", *flags, *common)
            else:
                cmd("plink2", "--vcf", source, *common)
            return dest

        if a == "gatk_validate":
            py("check_build", self.p("vcf"), v["build"])
            reference_path = reference()
            cmd(
                "gatk",
                "CreateSequenceDictionary",
                "-R",
                reference_path,
                "-O",
                self.o("referenz.dict"),
            )
            cmd(
                "gatk",
                "ValidateVariants",
                "-V",
                self.p("vcf"),
                "-R",
                reference_path,
                "--validation-type-to-exclude",
                "IDS",
            )
        elif a == "inspect":
            source = self.p("file")
            name = source.lower()
            if name.endswith((".vcf", ".vcf.gz", ".bcf", ".vcf.bgz")):
                lines.append("bcftools view -h " + Q(source) + " > vcf_header.txt")
                lines.append("bcftools stats " + Q(source) + " > vcf_statistik.txt")
            elif name.endswith((".bam", ".cram")):
                cmd("samtools", "quickcheck", "-v", source)
                lines.append(
                    "samtools view -H " + Q(source) + " > alignment_header.txt"
                )
            else:
                py("inspect_chip", source, self.o())
        elif a == "chip_vcf":
            py(
                "chip_vcf",
                self.p("file"),
                reference(),
                v["build"],
                self.o(),
                self.person,
            )
        elif a == "vcf_qc":
            lines.append(
                "bcftools stats -s - " + Q(self.p("vcf")) + " > vcf_statistik.txt"
            )
        elif a == "compare":
            if v["build_a"] != v["build_b"]:
                raise ValueError(
                    "The selected builds differ, but first harmonize in a controlled manner."
                )
            py(
                "compare",
                self.p("a"),
                self.p("b"),
                v["build_a"],
                v["build_b"],
                self.o(),
            )
        elif a == "fastq_qc":
            args = [
                "fastp",
                "-i",
                self.p("r1"),
                "-o",
                self.o("gefiltert_R1.fastq.gz"),
                "-h",
                self.o("fastp.html"),
                "-j",
                self.o("fastp.json"),
            ]
            if v.get("r2"):
                args += ["-I", self.p("r2"), "-O", self.o("gefiltert_R2.fastq.gz")]
            cmd(*args, thread_options=("-w", threads))
        elif a in ["bam_qc", "deepvariant"]:
            source = self.p("bam")
            iscram = source.lower().endswith(".cram")
            if iscram and not v.get("reference"):
                raise ValueError("CRAM requires the exact matching reference FASTA.")
            align = self.o("reads.cram" if iscram else "reads.bam")
            cmd("ln", "-s", source, align)
            rf = reference() if v.get("reference") else None
            cmd("samtools", "quickcheck", "-v", align)
            cmd("samtools", "index", align)
            if a == "bam_qc":
                extra = ["--reference", rf] if rf else []
                lines.append(
                    "samtools flagstat -@ "
                    + extra_threads
                    + " "
                    + " ".join(Q(x) for x in [*extra, align])
                    + " > flagstat.txt"
                )
                lines.append(
                    "samtools stats -@ "
                    + extra_threads
                    + " "
                    + " ".join(Q(x) for x in [*extra, align])
                    + " > samtools_stats.txt"
                )
                cmd(
                    "mosdepth",
                    "-n",
                    *(["--fasta", rf] if rf else []),
                    self.o("abdeckung"),
                    align,
                    thread_options=("-t", threads),
                )
                cmd("multiqc", self.o(), "-o", self.o("qualitaetsbericht"))
            else:
                dirs = {
                    str(PurePosixPath(source).parent),
                    str(PurePosixPath(self.p("reference")).parent),
                }
                cpu_image = "google/deepvariant:1.10.0"
                gpu_image = cpu_image + "-gpu"
                if os.name != "nt":
                    import on_demand

                    endpoint = on_demand.deepvariant_docker_socket()
                    lines.append(
                        "unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH"
                    )
                    if endpoint:
                        lines.append("export DOCKER_HOST=" + Q("unix://" + endpoint))
                    else:
                        lines.append(
                            "printf '%s\\n' 'Start the local Docker engine for DeepVariant.' >&2; exit 1"
                        )
                lines += [
                    "deepvariant_gpu=()",
                    "deepvariant_image=" + Q(cpu_image),
                    "if docker image inspect " + Q(gpu_image) + " >/dev/null 2>&1 && "
                    "timeout 30s docker run --rm --pull=never --platform linux/amd64 --gpus 1 "
                    "--network=none --entrypoint /usr/bin/python3 "
                    + Q(gpu_image)
                    + " -c "
                    + Q(DEEPVARIANT_GPU_PROBE)
                    + " >/dev/null 2>&1; then",
                    "  deepvariant_gpu=(--gpus 1)",
                    "  deepvariant_image=" + Q(gpu_image),
                    "fi",
                    'docker image inspect "$deepvariant_image" >/dev/null 2>&1 || '
                    "{ printf '%s\\n' 'The selected DeepVariant image is missing locally.' >&2; exit 1; }",
                ]
                args = ["--user", "1000:1000"]
                for d in sorted(dirs):
                    args += ["-v", d + ":" + d + ":ro"]
                args += ["-v", self.o() + ":" + self.o()]
                caller = [
                    "/opt/deepvariant/bin/run_deepvariant",
                    "--model_type=" + v["model"],
                    "--ref=" + rf,
                    "--reads=" + align,
                    "--output_vcf=" + self.o("varianten.vcf.gz"),
                    "--output_gvcf=" + self.o("varianten.g.vcf.gz"),
                    "--intermediate_results_dir=" + self.o("zwischenschritte"),
                    "--vcf_stats_report=true",
                ]
                lines.append(
                    'docker run --rm --pull=never --network=none --platform linux/amd64 "${deepvariant_gpu[@]}" '
                    + " ".join(Q(arg) for arg in args)
                    + ' "$deepvariant_image" '
                    + " ".join(Q(arg) for arg in caller)
                    + " --num_shards="
                    + heavy_workers
                )
        elif a == "multiqc":
            if not Path(v["folder"]).is_dir():
                raise ValueError("Select a quality report folder.")
            packages = linux(ROOT / "DNA_Software/Windows/PythonPackages")
            lines.append(
                "PYTHONPATH="
                + Q(packages)
                + "${PYTHONPATH:+:$PYTHONPATH} python3 -m multiqc "
                + Q(self.p("folder"))
                + " -o "
                + Q(self.o())
            )
        elif a == "sarek":
            rf = self.o("referenz.fa") if kiri_pipeline else reference()
            reads = []
            for key in ("r1", "r2"):
                source = self.p(key)
                target = self.o(key + ".fastq.gz")
                if source.lower().endswith(".gz"):
                    cmd("ln", "-s", source, target)
                else:
                    lines.append("gzip -c -- " + Q(source) + " > " + Q(target))
                reads.append(target)
            sheet = self.folder / "samplesheet.csv"
            with sheet.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(
                    ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"]
                )
                w.writerow(
                    [
                        self.person,
                        {"XX": "XX", "XY": "XY"}.get(v["sex"], "NA"),
                        0,
                        self.person,
                        "L001",
                        *reads,
                    ]
                )
            params_file = self.folder / "sarek-params.json"
            atomic(params_file, {"genome": None, "igenomes_ignore": True})
            pipeline(
                "sarek",
                "--input",
                linux(sheet),
                "--fasta",
                rf,
                "--fasta_fai",
                rf + ".fai",
                "--skip_tools",
                "baserecalibrator",
                "--tools",
                v["caller"],
                "--outdir",
                self.o("sarek"),
                params_file=params_file,
            )
        elif a == "normalize":
            py("check_build", self.p("vcf"), v["build"])
            cmd(
                "bcftools",
                "norm",
                "-f",
                reference(),
                "-m",
                "-any",
                "--check-ref",
                "e",
                "-Oz",
                "-o",
                self.o("normalisiert.vcf.gz"),
                self.p("vcf"),
            )
            cmd("bcftools", "index", "-ft", self.o("normalisiert.vcf.gz"))
        elif a == "fastq_report":
            cmd(
                "fastp",
                "--in1",
                self.p("r1"),
                *(["--in2", self.p("r2")] if v.get("r2") else []),
                "--disable_adapter_trimming",
                "--disable_quality_filtering",
                "--disable_length_filtering",
                "--html",
                self.o("fastq_quality.html"),
                "--json",
                self.o("fastq_quality.json"),
                thread_options=("--thread", threads),
            )
        elif a == "variant_convert":
            mode, name = VARIANT_FORMATS[v["output_format"]]
            cmd("bcftools", "view", "-O" + mode, "-o", self.o(name), self.p("vcf"))
            lines.append(
                "bcftools stats " + Q(self.o(name)) + " > conversion_stats.txt"
            )
        elif a == "filter":
            cmd(
                "bcftools",
                "view",
                *variant_filter_options(v),
                "-Oz",
                "-o",
                self.o("gefiltert.vcf.gz"),
                self.p("vcf"),
            )
            cmd("bcftools", "index", "-ft", self.o("gefiltert.vcf.gz"))
            lines.append(
                "bcftools stats "
                + Q(self.o("gefiltert.vcf.gz"))
                + " > filter-statistics.txt"
            )
        elif a == "merge":
            files = v["files"]
            if len(files) < 2:
                raise ValueError("Select at least two normalized VCF files.")
            ready = []
            for i, source in enumerate(files, 1):
                py("check_build", linux(source), v["build"])
                sub = self.out / ("Source__" + str(i))
                sub.mkdir(exist_ok=True)
                item = prepared(linux(source), "quelle_" + str(i))
                py("names", item, "Source" + str(i), linux(sub))
                dest = self.o("benannt_" + str(i) + ".vcf.gz")
                cmd(
                    "bcftools",
                    "reheader",
                    "-s",
                    linux(sub / "neue_probennamen.txt"),
                    "-o",
                    dest,
                    item,
                )
                cmd("bcftools", "index", "-ft", dest)
                ready.append(dest)
            cmd(
                "bcftools",
                "merge",
                "-m",
                "none",
                "-Oz",
                "-o",
                self.o("getrennte_proben.vcf.gz"),
                *ready,
            )
            cmd("bcftools", "index", "-ft", self.o("getrennte_proben.vcf.gz"))
        elif a == "roh":
            cmd(
                "plink19",
                "--vcf",
                self.p("vcf"),
                "--double-id",
                "--chr",
                "1-22",
                "--snps-only",
                "just-acgt",
                "--biallelic-only",
                "strict",
                "--make-bed",
                "--out",
                self.o("roh_input"),
            )
            cmd(
                "plink19",
                "--bfile",
                self.o("roh_input"),
                "--homozyg",
                "--out",
                self.o("roh"),
            )
        elif a == "peddy":
            py("check_build", self.p("vcf"), v["build"])
            ready = prepared(self.p("vcf"), "peddy_input")
            cmd(
                "peddy",
                "--plot",
                *(["--sites", "hg38"] if v["build"] == "GRCh38" else []),
                "--prefix",
                self.o("familien_qc"),
                ready,
                self.p("ped"),
                thread_options=("-p", heavy_workers),
            )
        elif a == "whatshap":
            py("check_build", self.p("vcf"), v["build"])
            cmd("samtools", "quickcheck", "-v", self.p("alignment"))
            cmd(
                "whatshap",
                "phase",
                "--reference",
                self.p("reference"),
                "--output",
                self.o("read_phased.vcf"),
                self.p("vcf"),
                self.p("alignment"),
            )
            cmd(
                "whatshap",
                "stats",
                "--tsv",
                self.o("phase_stats.tsv"),
                self.o("read_phased.vcf"),
            )
        elif a == "truvari":
            py("check_build", self.p("base"), v["build"])
            py("check_build", self.p("comparison"), v["build"])
            base = prepared(self.p("base"), "sv_basis")
            comparison = prepared(self.p("comparison"), "sv_vergleich")
            cmd(
                "truvari",
                "bench",
                "-b",
                base,
                "-c",
                comparison,
                "-f",
                self.p("reference"),
                "-o",
                self.o("sv_vergleichsergebnis"),
            )
        elif a == "kinship":
            cmd(
                "plink2",
                "--vcf",
                self.p("vcf"),
                "--chr",
                "1-22",
                "--snps-only",
                "just-acgt",
                "--max-alleles",
                "2",
                "--geno",
                "0.05",
                "--make-pgen",
                "--out",
                self.o("familie"),
            )
            cmd(
                "plink2",
                "--pfile",
                self.o("familie"),
                "--make-king-table",
                "--out",
                self.o("verwandtschaft"),
            )
        elif a == "ref_export":
            panel, _, chrom = reference_panel(v)
            cmd(
                "plink2",
                "--pfile",
                linux(panel),
                "vzs",
                "--chr",
                chrom,
                "--snps-only",
                "just-acgt",
                "--max-alleles",
                "2",
                "--export",
                "vcf",
                "bgz",
                "--out",
                self.o("referenz_chr" + chrom),
            )
            cmd(
                "bcftools",
                "index",
                "-ft",
                self.o("referenz_chr" + chrom + ".vcf.gz"),
            )
        elif a == "pca":
            prefix = plink_input()
            cmd(
                "plink2",
                "--pfile",
                prefix,
                "--indep-pairwise",
                "200",
                "50",
                "0.2",
                "--out",
                self.o("ld"),
            )
            py("pca_count", prefix + ".psam", self.o())
            lines.append(
                "plink2 --threads "
                + threads
                + " --pfile "
                + Q(prefix)
                + " --extract "
                + Q(self.o("ld.prune.in"))
                + ' --pca "$(cat pca_k.txt)" $(cat pca_mode.txt) --out '
                + Q(self.o("pca"))
            )
            py(
                "pca_plot",
                self.o("pca.eigenvec"),
                self.p("labels") if v.get("labels") else "",
                self.o(),
            )
        elif a == "beagle":
            cmd(
                "beagle",
                "gt=" + self.p("vcf"),
                "map=" + self.p("map"),
                "chrom=" + v["chrom"],
                "out=" + self.o("phasiert"),
                "impute=false",
                *(["ref=" + self.p("refpanel")] if v.get("refpanel") else []),
                thread_options=("nthreads=" + threads,),
            )
        elif a == "ibd":
            cmd(
                "hap-ibd",
                "gt=" + self.p("vcf"),
                "map=" + self.p("map"),
                "out=" + self.o("segmente"),
                thread_options=("nthreads=" + threads,),
            )
        elif a == "rfmix":
            target = prepared(self.p("query"), "ziel")
            panel = prepared(self.p("refpanel"), "referenz")
            cmd(
                "rfmix",
                "-f",
                target,
                "-r",
                panel,
                "-m",
                self.p("samplemap"),
                "-g",
                self.p("map"),
                "--chromosome=" + v["chrom"],
                "-o",
                self.o("lokale_ancestry"),
                thread_options=("--n-threads=" + threads,),
            )
        elif a == "mito":
            ready = prepared(self.p("vcf"), "mt_input")
            import on_demand

            haplogrep = on_demand.host_command("haplogrep") if os.name != "nt" else None
            cmd(
                haplogrep or "haplogrep",
                "classify",
                "--input",
                ready,
                "--output",
                self.o("haplogroups.txt"),
                "--tree",
                "phylotree-fu-rcrs@1.3",
            )
        elif a == "yhaplo":
            if v["build"] != "GRCh37":
                raise ValueError(
                    "yhaplo requires GRCh37 here. Don't circumvent by renaming the build."
                )
            py("check_build", self.p("vcf"), v["build"])
            ready = prepared(self.p("vcf"), "y_input")
            cmd("yhaplo", "-i", ready, "-o", self.o("yhaplo"), "-aao")
        elif a == "opencravat_run":
            py("check_build", self.p("vcf"), v["build"])
            cmd(
                "oc",
                "run",
                self.p("vcf"),
                "-l",
                "hg38" if v["build"] == "GRCh38" else "hg19",
                "-a",
                "clinvar",
                "gnomad4",
                "-d",
                self.o("annotation"),
                "-n",
                "varianten",
                "-t",
                "text",
                "excel",
                thread_options=("--mp", '"$((dna_threads < 2 ? dna_threads : 2))"'),
            )
        elif a == "vep":
            if v["build"] != "GRCh38":
                raise ValueError(
                    "The installed VEP cache is GRCh38. For GRCh37, first use the appropriate cache or validated harmonization."
                )
            py("check_build", self.p("vcf"), v["build"])
            cmd(
                "vep",
                "--offline",
                "--cache",
                "--dir_cache",
                linux(ROOT / "References/VEP"),
                "--cache_version",
                "116",
                "--assembly",
                "GRCh38",
                "--input_file",
                self.p("vcf"),
                "--output_file",
                self.o("vep_annotation.vcf"),
                "--vcf",
                "--symbol",
                "--canonical",
                "--no_stats",
                thread_options=("--fork", heavy_workers),
            )
        elif a == "pharmcat":
            if v["build"] != "GRCh38":
                raise ValueError("PharmCAT requires the appropriate GRCh38-VCF.")
            py("check_build", self.p("vcf"), v["build"])
            cmd(
                "pharmcat",
                "-vcf",
                self.p("vcf"),
                "-o",
                self.o("pharmcat"),
                "-bf",
                "pharmakogenetik",
            )
        elif a == "pgs":
            if not kiri_pipeline:
                py("check_build", self.p("vcf"), v["build"])
                cmd("plink2", *self.pgs_prepare_args())
            py("score_sheet", self.o("zielgenotypen"), self.person, self.o())
            pipeline(
                "pgsc-calc",
                "--input",
                self.o("samplesheet.csv"),
                "--scorefile",
                self.p("score"),
                "--target_build",
                v["build"],
                "--outdir",
                self.o("pgs"),
                "--max_memory",
                "10.GB",
                thread_options=("--max_cpus", threads),
            )
        else:
            raise ValueError("Not yet an execution adapter for" + a)
        if not kiri_pipeline:
            lines.append('printf "\\nDNA_LAUNCHER_STEP_SUCCESS\\n"')
        return "\n".join(lines) + "\n"

    def pgs_prepare_args(self):
        return [
            "--vcf",
            self.p("vcf"),
            "--chr",
            "1-22",
            "--snps-only",
            "just-acgt",
            "--max-alleles",
            "2",
            "--make-pgen",
            "--out",
            self.o("zielgenotypen"),
        ]

    def run_process(
        self,
        args,
        env=None,
        start_new_session=False,
        cancel_command=None,
        cancel_timeout=10,
    ):
        self.log("> " + subprocess.list2cmdline([str(x) for x in args]))
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            start_new_session=start_new_session,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        def read():
            try:
                for line in proc.stdout:
                    self.log(line.rstrip())
            finally:
                proc.stdout.close()

        thread = threading.Thread(target=read, daemon=True)
        thread.start()
        while proc.poll() is None:
            self.save()
            if (self.folder / "abbrechen.request").exists():
                pidfile = self.folder / "linux.pid"
                if pidfile.exists() and not cancel_command:
                    pgid = pidfile.read_text().strip()
                    if pgid.isdigit() and os.name == "nt":
                        subprocess.run(
                            [
                                windows_executable("wsl.exe"),
                                "-d",
                                distro_name(ROOT),
                                "-u",
                                "dna",
                                "--",
                                "kill",
                                "-TERM",
                                "--",
                                "-" + pgid,
                            ],
                            capture_output=True,
                            timeout=10,
                        )
                    elif pgid.isdigit():
                        try:
                            os.killpg(int(pgid), 15)
                        except ProcessLookupError:
                            pass
                proc.terminate()
                if cancel_command:
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    try:
                        cleanup = subprocess.run(
                            cancel_command,
                            env=env,
                            capture_output=True,
                            timeout=cancel_timeout,
                        )
                        if (
                            cleanup.returncode
                            and b"No such container" not in cleanup.stderr
                        ):
                            self.log(
                                "Kiri could not confirm that the cancelled container was removed."
                            )
                    except (OSError, subprocess.TimeoutExpired):
                        self.log(
                            "Kiri could not confirm that the cancelled container was removed."
                        )
                thread.join(3)
                raise InterruptedError("Order cancelled on request.")
            time.sleep(1)
        thread.join(5)
        if proc.returncode:
            raise RuntimeError(
                "Tool with error code"
                + str(proc.returncode)
                + " beendet. Details stehen im Protokoll."
            )

    def run_kiri_pipeline(self, setup):
        import uuid
        import on_demand

        route, prep, source, launcher = setup
        if sha(launcher) != on_demand.NEXTFLOW_DIST["expected_sha256"]:
            raise ValueError("The local Nextflow launcher failed its SHA-256 check.")
        action = self.task["action"]
        helper = Path(__file__).with_name("linux_helpers.py")
        config = ROOT / "DNA_Software/Start/dna-nextflow.config"
        cache = ROOT / "DNA_Software/UserData/Launcher/Nextflow"
        cache.mkdir(parents=True, exist_ok=True)
        script = self.folder / "ausfuehren.sh"
        text = self.shell(kiri_pipeline=True)
        script.write_bytes(text.encode("utf-8"))
        (self.folder / "command.txt").write_text(text, encoding="utf-8")
        job_path = linux(self.folder)
        inputs = {
            "sarek": ("reference", "r1", "r2"),
            "pgs": ("vcf", "score"),
        }[action]
        prep_script = self.folder / "kiri-pipeline-prep.sh"
        prep_script.write_text(
            "#!/bin/bash\nset -euo pipefail\n"
            + (
                "ln -s -- "
                + Q(self.p("reference"))
                + " "
                + Q(self.o("referenz.fa"))
                + "\nsamtools faidx "
                + Q(self.o("referenz.fa"))
                + "\n"
                if action == "sarek"
                else shlex.join(
                    [
                        "plink2",
                        "--threads",
                        str(hardware.cpu_threads()),
                        *self.pgs_prepare_args(),
                    ]
                )
                + "\n"
            ),
            encoding="utf-8",
            newline="\n",
        )
        if action == "pgs":
            from linux_helpers import check_build

            check_build(self.v["vcf"], self.v["build"])
        paths = dict.fromkeys(Path(self.v[key]).resolve() for key in inputs)
        binds = [kiri_bind(self.folder, job_path)]
        binds.extend(kiri_bind(path, linux(path), readonly=True) for path in paths)
        token = "dna-nextflow-" + uuid.uuid4().hex

        def start(container, selected_route, mounts, args, *, network):
            prefix, env, container_platform, image = selected_route
            command = [
                *prefix,
                "run",
                "--rm",
                "--pull=never",
                "--platform",
                container_platform,
                "--name",
                container,
                "--workdir",
                job_path,
                "--network",
                network,
                "--entrypoint",
                "/bin/bash",
            ]
            for mount in mounts:
                command.extend(["--mount", mount])
            self.run_process(
                [*command, image, *args],
                env=env,
                cancel_command=[
                    *prefix,
                    *(
                        ["stop", "--time", "15"]
                        if network == "bridge"
                        else ["rm", "-f"]
                    ),
                    container,
                ],
                cancel_timeout=30 if network == "bridge" else 10,
            )

        self.log("Using local Kiri for " + action + ".")
        prep_input = Path(self.v[inputs[0]]).resolve()
        start(
            token + "-prep",
            prep,
            [binds[0], kiri_bind(prep_input, linux(prep_input), readonly=True)],
            [linux(prep_script)],
            network="none",
        )
        mounts = [
            *binds,
            kiri_bind(launcher, "/opt/dna-nextflow", readonly=True),
            kiri_bind(cache, linux(cache)),
            kiri_bind(source, linux(source), readonly=True),
            kiri_bind(helper, linux(helper), readonly=True),
            kiri_bind(config, linux(config), readonly=True),
            "type=bind,source=" + KIRI_NEXTFLOW_SOCKET + ",target=/var/run/docker.sock",
        ]
        extra_ca = cache / "local-ca.pem"
        prelude = "export NXF_ANSI_LOG=false; "
        if extra_ca.is_file():
            mounts.append(kiri_bind(extra_ca, "/opt/dna-local-ca.pem", readonly=True))
            prelude += (
                'cp "$JAVA_HOME/lib/security/cacerts" /tmp/dna-cacerts; '
                "keytool -importcert -noprompt -alias dna-local-ca "
                "-file /opt/dna-local-ca.pem -keystore /tmp/dna-cacerts -storepass changeit; "
                "cat /etc/ssl/certs/ca-certificates.crt /opt/dna-local-ca.pem > /tmp/dna-ca-bundle.pem; "
                "export NXF_OPTS=-Djavax.net.ssl.trustStore=/tmp/dna-cacerts "
                "CURL_CA_BUNDLE=/tmp/dna-ca-bundle.pem; "
            )
        start(
            token,
            route,
            mounts,
            ["-ec", prelude + "exec /bin/bash " + Q(linux(script))],
            network="bridge",
        )

    def run_with_kiri(self, route, *, gpu=False):
        import tempfile
        import uuid

        prefix, env, container_platform, image = route
        action = self.task["action"]
        threads = hardware.cpu_threads()
        if gpu:
            info = subprocess.run(
                [*prefix, "info", "--format", "{{.NCPU}}"],
                env=env,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            threads = min(threads, max(1, int(info.stdout.strip())))
        directories = []
        file_mounts = []
        if action == "variant_convert":
            mode, name = VARIANT_FORMATS[self.v["output_format"]]
            inputs = {"vcf": "/input"}
            names = [name, "conversion_stats.txt"]
            command = (
                f"bcftools view -O{mode} -o {name} /input && "
                f"bcftools stats {name} > conversion_stats.txt"
            )
        elif action == "vcf_qc":
            inputs = {"vcf": "/input"}
            names = ["vcf_statistik.txt"]
            command = "bcftools stats -s - /input > vcf_statistik.txt"
        elif action == "beagle":
            chrom = self.v["chrom"]
            if chrom not in {str(n) for n in range(1, 23)}:
                raise ValueError("Select a chromosome between 1 and 22.")
            vcf = (
                "/input.vcf.gz"
                if self.v["vcf"].lower().endswith((".gz", ".bgz"))
                else "/input.vcf"
            )
            inputs = {"vcf": vcf, "map": "/map"}
            command_args = [
                "java",
                "-Djava.io.tmpdir=/output",
                "-jar",
                "/opt/beagle/beagle.jar",
                "gt=" + vcf,
                "map=/map",
                "chrom=" + chrom,
                "out=phasiert",
                "impute=false",
                f"nthreads={threads}",
            ]
            if self.v.get("refpanel"):
                inputs["refpanel"] = "/panel.vcf.gz"
                command_args.append("ref=/panel.vcf.gz")
            names = ["phasiert.vcf.gz", "phasiert.log"]
            command = shlex.join(command_args)
        elif action == "ibd":
            vcf = "/input.vcf"
            if self.v["vcf"].lower().endswith((".gz", ".bgz")):
                vcf += ".gz"
            inputs = {"vcf": vcf, "map": "/map"}
            names = ["segmente.ibd.gz", "segmente.hbd.gz", "segmente.log"]
            command = (
                "java -Djava.io.tmpdir=/output -jar /opt/hap-ibd/hap-ibd.jar "
                f"gt={vcf} map=/map out=segmente nthreads={threads}"
            )
        elif action == "truvari":
            from linux_helpers import check_build

            for key in ("base", "comparison"):
                check_build(self.v[key], self.v["build"])
            inputs = {
                "base": "/base",
                "comparison": "/comparison",
                "reference": "/reference",
            }
            reference = "reference.fa"
            if self.v["reference"].lower().endswith((".gz", ".bgz")):
                reference += ".gz"
            names = ["sv_vergleichsergebnis/summary.json"]
            directories.append("sv_vergleichsergebnis")
            commands = []
            for source, target in (
                ("/base", "sv_basis"),
                ("/comparison", "sv_vergleich"),
            ):
                vcf_name = target + ".vcf.gz"
                names.extend((vcf_name, vcf_name + ".tbi"))
                commands.extend(
                    [
                        f"bcftools sort -m 1G -Oz -o {vcf_name} -T {target}_sort.XXXXXX {source}",
                        f"bcftools index --threads {threads - 1} -ft {vcf_name}",
                    ]
                )
            commands.extend(
                [
                    f"ln -s /reference {reference}",
                    f"samtools faidx {reference}",
                    f"truvari bench -b sv_basis.vcf.gz -c sv_vergleich.vcf.gz -f {reference} -o sv_vergleichsergebnis",
                ]
            )
            command = " && ".join(commands)
        elif action == "mito":
            inputs = {"vcf": "/input"}
            names = ["mt_input.vcf.gz", "mt_input.vcf.gz.tbi", "haplogroups.txt"]
            command = (
                "bcftools sort -m 1G -Oz -o mt_input.vcf.gz -T mt_sort.XXXXXX /input "
                f"&& bcftools index --threads {threads - 1} -ft mt_input.vcf.gz "
                "&& cd /opt/haplogrep "
                "&& java -Djava.io.tmpdir=/output -jar haplogrep3.jar classify "
                "--input /output/mt_input.vcf.gz --output /output/haplogroups.txt "
                "--tree phylotree-fu-rcrs@1.3"
            )
        elif action == "yhaplo":
            from linux_helpers import check_build

            if self.v["build"] != "GRCh37":
                raise ValueError("yhaplo requires GRCh37.")
            check_build(self.v["vcf"], "GRCh37")
            inputs = {"vcf": "/input"}
            names = [
                "y_input.vcf.gz",
                "y_input.vcf.gz.tbi",
                "yhaplo/haplogroups.y_input.txt",
            ]
            directories.append("yhaplo")
            command = (
                "bcftools sort -m 1G -Oz -o y_input.vcf.gz -T y_sort.XXXXXX /input "
                f"&& bcftools index --threads {threads - 1} -ft y_input.vcf.gz "
                "&& yhaplo -i y_input.vcf.gz -o yhaplo -aao"
            )
        elif action == "rfmix":
            import on_demand

            if not on_demand.rfmix_license_reviewed():
                raise ValueError(on_demand.LICENSE)
            chrom = self.v["chrom"]
            if chrom not in {str(n) for n in range(1, 23)}:
                raise ValueError("Select a chromosome between 1 and 22.")
            inputs = {
                "query": "/query",
                "refpanel": "/panel",
                "samplemap": "/samples",
                "map": "/map",
            }
            names = [
                "ziel.vcf.gz",
                "ziel.vcf.gz.tbi",
                "referenz.vcf.gz",
                "referenz.vcf.gz.tbi",
                "lokale_ancestry.msp.tsv",
                "lokale_ancestry.fb.tsv",
                "lokale_ancestry.rfmix.Q",
            ]
            commands = ["cd /tmp"]
            for target, source in (("ziel", "/query"), ("referenz", "/panel")):
                commands.extend(
                    [
                        f"bcftools sort -m 1G -Oz -o {target}.vcf.gz -T {target}_sort.XXXXXX {source}",
                        f"bcftools index --threads {threads - 1} -ft {target}.vcf.gz",
                    ]
                )
            commands.append(
                "rfmix -f ziel.vcf.gz -r referenz.vcf.gz -m /samples -g /map "
                f"--chromosome={chrom} --n-threads={threads} -o lokale_ancestry"
            )
            commands.extend(f"cat {name} > /output/{name}" for name in names)
            command = " && ".join(commands)
        elif action == "opencravat_run":
            from linux_helpers import check_build

            build = self.v["build"]
            if build not in {"GRCh37", "GRCh38"}:
                raise ValueError("Select GRCh37 or GRCh38.")
            check_build(self.v["vcf"], build)
            modules = kiri_opencravat_modules(ROOT)
            if not modules:
                raise ValueError(
                    "Install the OpenCRAVAT modules in References/OpenCRAVAT/modules."
                )
            vcf = (
                "/input.vcf.gz"
                if self.v["vcf"].lower().endswith((".gz", ".bgz"))
                else "/input.vcf"
            )
            inputs = {"vcf": vcf}
            file_mounts.append((modules, "/modules"))
            names = ["annotation/varianten.sqlite"]
            directories.append("annotation")
            assembly = "hg38" if build == "GRCh38" else "hg19"
            command = (
                "HOME=/tmp TMPDIR=/tmp OPENCRAVAT_MD=/modules "
                f"oc run {vcf} -l {assembly} -a clinvar gnomad4 -d annotation "
                f"-n varianten -t text excel --mp {min(threads, 2)}"
            )
        elif action == "vep":
            from linux_helpers import check_build

            if self.v["build"] != "GRCh38":
                raise ValueError(
                    "Ensembl VEP requires the GRCh38 cache for this workflow."
                )
            check_build(self.v["vcf"], "GRCh38")
            cache = kiri_vep_cache(ROOT)
            if not cache:
                raise ValueError(
                    "Install the Ensembl VEP 116 GRCh38 cache in References/VEP."
                )
            vcf = (
                "/input.vcf.gz"
                if self.v["vcf"].lower().endswith((".gz", ".bgz"))
                else "/input.vcf"
            )
            inputs = {"vcf": vcf}
            file_mounts.append(
                (
                    cache / "homo_sapiens" / "116_GRCh38",
                    "/cache/homo_sapiens/116_GRCh38",
                )
            )
            names = ["vep_annotation.vcf"]
            command = (
                "vep --offline --cache --dir_cache /cache --cache_version 116 --assembly GRCh38 "
                f"--input_file {vcf} --output_file STDOUT --vcf --symbol "
                f"--canonical --no_stats --fork {min(threads, 4)} > vep_annotation.vcf"
            )
        elif action == "pharmcat":
            from linux_helpers import check_build

            if self.v["build"] != "GRCh38":
                raise ValueError("PharmCAT requires the appropriate GRCh38-VCF.")
            check_build(self.v["vcf"], "GRCh38")
            vcf = "/input.vcf"
            if self.v["vcf"].lower().endswith((".gz", ".bgz")):
                vcf += ".gz"
            inputs = {"vcf": vcf}
            names = []
            directories.append("pharmcat")
            command = (
                "mkdir pharmcat && java -Djava.io.tmpdir=/output -jar /opt/pharmcat/pharmcat.jar "
                f"-vcf {vcf} -o pharmcat -bf pharmakogenetik "
                "&& find pharmcat -type f -name '*.report.html' -size +0c -print -quit "
                "| grep -q ."
            )
        elif action == "gatk_validate":
            from linux_helpers import check_build

            check_build(self.v["vcf"], self.v["build"])
            vcf = (
                "/input.vcf.gz"
                if self.v["vcf"].lower().endswith((".gz", ".bgz"))
                else "/input.vcf"
            )
            reference = (
                "referenz.fa.gz"
                if self.v["reference"].lower().endswith((".gz", ".bgz"))
                else "referenz.fa"
            )
            inputs = {"vcf": "/variants", "reference": "/reference"}
            names = [reference + ".fai", "referenz.dict"]
            if reference.endswith(".gz"):
                names.append(reference + ".gzi")
            gatk = "java -Djava.io.tmpdir=/tmp -jar /opt/gatk/gatk-package-4.7.0.0-local.jar"
            local_vcf = vcf.removeprefix("/")
            index = (
                f" && {gatk} IndexFeatureFile -I {local_vcf}"
                if local_vcf.endswith(".gz")
                else ""
            )
            command = (
                f"cd /tmp && ln -s /variants {local_vcf} && ln -s /reference {reference} && samtools faidx {reference} "
                f"&& {gatk} CreateSequenceDictionary -R {reference} -O referenz.dict "
                f"{index} && {gatk} ValidateVariants -V {local_vcf} -R {reference} --validation-type-to-exclude IDS"
                + "".join(f" && cat {name} > /output/{name}" for name in names)
            )
        elif action == "compare":
            from linux_helpers import check_build

            builds = self.v["build_a"], self.v["build_b"]
            if builds[0] != builds[1] or builds[0] not in {"GRCh37", "GRCh38"}:
                raise ValueError(
                    "Select matching reference builds before comparing sources."
                )
            inputs = {}
            for key, build in zip(("a", "b"), builds):
                source = self.v[key]
                check_build(source, build)
                inputs[key] = f"/{key}.vcf" + (
                    ".gz" if source.lower().endswith((".gz", ".bgz")) else ""
                )
            file_mounts.append(
                (Path(__file__).with_name("linux_helpers.py"), "/helpers.py")
            )
            names = ["konflikte.tsv", "vergleich.json", "report.html"]
            command = shlex.join(
                [
                    "python",
                    "/helpers.py",
                    "compare",
                    inputs["a"],
                    inputs["b"],
                    *builds,
                    ".",
                ]
            )
        elif action == "whatshap":
            from linux_helpers import check_build

            check_build(self.v["vcf"], self.v["build"])
            vcf = "/input.vcf"
            if self.v["vcf"].lower().endswith((".gz", ".bgz")):
                vcf += ".gz"
            alignment = (
                "reads.cram"
                if self.v["alignment"].lower().endswith(".cram")
                else "reads.bam"
            )
            reference = "reference.fa"
            if self.v["reference"].lower().endswith((".gz", ".bgz")):
                reference += ".gz"
            inputs = {"vcf": vcf, "alignment": "/alignment", "reference": "/reference"}
            names = ["read_phased.vcf", "phase_stats.tsv"]
            command = (
                f"ln -s /reference {reference} && ln -s /alignment {alignment} "
                f"&& samtools faidx {reference} && samtools quickcheck -v {alignment} "
                f"&& samtools index -@ {threads - 1} {alignment} "
                f"&& whatshap phase --reference {reference} --output read_phased.vcf {vcf} {alignment} "
                "&& whatshap stats --tsv phase_stats.tsv read_phased.vcf"
            )
        elif action == "peddy":
            from linux_helpers import check_build

            build = self.v["build"]
            check_build(self.v["vcf"], build)
            inputs = {"vcf": "/input", "ped": "/pedigree"}
            names = [
                "peddy_input.vcf.gz",
                "peddy_input.vcf.gz.tbi",
                "familien_qc.html",
                "familien_qc.peddy.ped",
                "familien_qc.het_check.csv",
                "familien_qc.ped_check.csv",
            ]
            sites = " --sites hg38" if build == "GRCh38" else ""
            command = (
                "bcftools sort -m 1G -Oz -o peddy_input.vcf.gz -T peddy_sort.XXXXXX /input "
                f"&& bcftools index --threads {threads - 1} -ft peddy_input.vcf.gz "
                "&& mkdir -p .tmp "
                "&& HOME=/output/.tmp TMPDIR=/output/.tmp MPLCONFIGDIR=/output/.tmp MPLBACKEND=Agg "
                f"peddy --plot -p {min(threads, 4)}{sites} --prefix familien_qc peddy_input.vcf.gz /pedigree"
            )
        elif action == "multiqc":
            inputs = {"folder": "/input"}
            names = ["multiqc_report.html"]
            directories.append("multiqc_data")
            command = (
                "mkdir -p .tmp && HOME=/output/.tmp TMPDIR=/output/.tmp "
                "XDG_CACHE_HOME=/output/.tmp multiqc /input -o /output"
            )
        elif action == "roh":
            inputs = {"vcf": "/input"}
            names = [
                "roh_input.bed",
                "roh_input.bim",
                "roh_input.fam",
                "roh_input.log",
                "roh.hom",
                "roh.hom.indiv",
                "roh.hom.summary",
                "roh.log",
            ]
            command = (
                f"plink19 --threads {threads} --vcf /input --double-id --chr 1-22 "
                "--snps-only just-acgt --biallelic-only strict --make-bed --out roh_input "
                f"&& plink19 --threads {threads} --bfile roh_input --homozyg --out roh"
            )
        elif action == "kinship":
            inputs = {"vcf": "/input"}
            names = [
                "familie.pgen",
                "familie.pvar",
                "familie.psam",
                "familie.log",
                "verwandtschaft.kin0",
                "verwandtschaft.log",
            ]
            command = (
                f"plink2 --threads {threads} --vcf /input --chr 1-22 "
                "--snps-only just-acgt --max-alleles 2 --geno 0.05 --make-pgen --out familie "
                f"&& plink2 --threads {threads} --pfile familie --make-king-table --out verwandtschaft"
            )
        elif action == "ref_export":
            panel, suffixes, chrom = reference_panel(self.v)
            inputs = {}
            file_mounts.extend(
                (panel.with_suffix(suffix), "/panel" + suffix) for suffix in suffixes
            )
            prefix_name = "referenz_chr" + chrom
            names = [
                prefix_name + ".vcf.gz",
                prefix_name + ".vcf.gz.tbi",
                prefix_name + ".log",
            ]
            command = (
                f"plink2 --threads {threads} --pfile /panel vzs --chr {chrom} "
                f"--snps-only just-acgt --max-alleles 2 --export vcf bgz --out {prefix_name} "
                f"&& bcftools index --threads {threads - 1} -ft {names[0]}"
            )
        elif action == "pca":
            source = Path(self.v["file"])
            inputs = {"file": "/input"}
            flags = "--vcf /input"
            if source.suffix.lower() == ".pgen":
                compressed = source.with_suffix(".pvar.zst").is_file()
                pvar_suffix = ".pvar.zst" if compressed else ".pvar"
                inputs["file"] = "/cohort.pgen"
                file_mounts.extend(
                    (source.with_suffix(suffix), "/cohort" + suffix)
                    for suffix in (".psam", pvar_suffix)
                )
                flags = "--pfile /cohort" + (" vzs" if compressed else "")
            labels = "''"
            if self.v.get("labels"):
                inputs["labels"] = "/labels"
                labels = "/labels"
            file_mounts.append(
                (Path(__file__).with_name("linux_helpers.py"), "/pca_helpers.py")
            )
            names = [
                "kohorte.pgen",
                "kohorte.pvar",
                "kohorte.psam",
                "kohorte.log",
                "ld.prune.in",
                "ld.log",
                "pca_k.txt",
                "pca.eigenval",
                "pca.eigenvec",
                "pca.log",
                "pca_interaktiv.html",
                "pca_mit_metadaten.tsv",
            ]
            command = (
                f"plink2 --threads {threads} {flags} --chr 1-22 --max-alleles 2 "
                "--snps-only just-acgt --geno 0.05 --make-pgen --out kohorte "
                f"&& plink2 --threads {threads} --pfile kohorte --indep-pairwise 200 50 0.2 --out ld "
                "&& /opt/pca/bin/python /pca_helpers.py pca_count kohorte.psam . "
                f"&& plink2 --threads {threads} --pfile kohorte --extract ld.prune.in "
                '--pca "$(cat pca_k.txt)" $(cat pca_mode.txt) --out pca '
                f"&& /opt/pca/bin/python /pca_helpers.py pca_plot pca.eigenvec {labels} ."
            )
        elif action == "filter":
            inputs = {"vcf": "/input"}
            names = [
                "gefiltert.vcf.gz",
                "gefiltert.vcf.gz.tbi",
                "filter-statistics.txt",
            ]
            view = shlex.join(
                [
                    "bcftools",
                    "view",
                    *variant_filter_options(self.v),
                    "--threads",
                    str(threads - 1),
                    "-Oz",
                    "-o",
                    names[0],
                    "/input",
                ]
            )
            command = (
                f"{view} && bcftools index --threads {threads - 1} -ft gefiltert.vcf.gz "
                "&& bcftools stats gefiltert.vcf.gz > filter-statistics.txt"
            )
        elif action == "normalize":
            from linux_helpers import check_build

            check_build(self.v["vcf"], self.v["build"])
            inputs = {"vcf": "/input", "reference": "/reference"}
            names = [
                "normalisiert.vcf.gz",
                "normalisiert.vcf.gz.tbi",
                "referenz.fa.fai",
            ]
            command = (
                "ln -s /reference referenz.fa && samtools faidx referenz.fa "
                f"&& bcftools norm --threads {threads - 1} -f referenz.fa "
                "-m -any --check-ref e -Oz -o normalisiert.vcf.gz /input "
                f"&& bcftools index --threads {threads - 1} -ft normalisiert.vcf.gz"
            )
        elif action == "merge":
            from linux_helpers import check_build

            sources = self.v["files"]
            if len(sources) < 2:
                raise ValueError("Select at least two normalized VCF files.")
            inputs = {}
            merged = "getrennte_proben.vcf.gz"
            names = [merged, merged + ".tbi"]
            commands = []
            ready = []
            for index, source in enumerate(sources, 1):
                check_build(source, self.v["build"])
                target = f"/input_{index}"
                file_mounts.append((source, target))
                sub = f"Source__{index}"
                directories.append(sub)
                sorted_vcf = f"quelle_{index}.vcf.gz"
                renamed_vcf = f"benannt_{index}.vcf.gz"
                names_file = f"{sub}/neue_probennamen.txt"
                map_file = f"{sub}/probenzuordnung.tsv"
                names.extend(
                    [
                        sorted_vcf,
                        sorted_vcf + ".tbi",
                        renamed_vcf,
                        renamed_vcf + ".tbi",
                        names_file,
                        map_file,
                    ]
                )
                ready.append(renamed_vcf)
                # Query the same sorted header used by the native pysam helper.
                sample_map = (
                    'BEGIN { print "Original\tLauncher_Name" > mapping } '
                    '{ name = prefix "_S" NR; print name; print $0 "\t" name > mapping } '
                    "END { if (NR == 0) exit 1 }"
                )
                commands += [
                    f"mkdir {sub}",
                    f"bcftools sort -m 1G -Oz -o {sorted_vcf} -T quelle_{index}_sort.XXXXXX {target}",
                    f"bcftools index --threads {threads - 1} -ft {sorted_vcf}",
                    f"bcftools query -l {sorted_vcf} > {sub}/original_samples.txt",
                    f"test -s {sub}/original_samples.txt",
                    shlex.join(
                        [
                            "awk",
                            "-v",
                            f"prefix=Source{index}",
                            "-v",
                            f"mapping={map_file}",
                            sample_map,
                            f"{sub}/original_samples.txt",
                        ]
                    )
                    + f" > {names_file}",
                    f"rm {sub}/original_samples.txt",
                    f"bcftools reheader -s {names_file} -o {renamed_vcf} {sorted_vcf}",
                    f"bcftools index --threads {threads - 1} -ft {renamed_vcf}",
                ]
            commands += [
                f"bcftools merge --threads {threads - 1} -m none -Oz -o {merged} "
                + " ".join(ready),
                f"bcftools index --threads {threads - 1} -ft {merged}",
            ]
            command = " && ".join(commands)
        elif action == "chip_vcf":
            from linux_helpers import check_build

            check_build(self.v["file"], self.v["build"])
            reference = "referenz.fa"
            if self.v["reference"].lower().endswith((".gz", ".bgz")):
                reference += ".gz"
            inputs = {"file": "/chip", "reference": "/reference"}
            file_mounts.append(
                (Path(__file__).with_name("linux_helpers.py"), "/helpers.py")
            )
            names = [
                "chip-statistics.json",
                "report.html",
                "konvertierung.json",
                "gemessene_chippositionen.vcf",
                "gemessene_chippositionen.vcf.gz",
                "gemessene_chippositionen.vcf.gz.tbi",
                reference + ".fai",
            ]
            if reference.endswith(".gz"):
                names.append(reference + ".gzi")
            command = (
                f"ln -s /reference {reference} && samtools faidx {reference} && "
                + shlex.join(
                    [
                        "python",
                        "/helpers.py",
                        "chip_vcf",
                        "/chip",
                        reference,
                        self.v["build"],
                        ".",
                        self.person,
                    ]
                )
            )
        elif action == "inspect":
            inputs = {"file": "/input"}
            if self.v["file"].lower().endswith((".vcf", ".vcf.gz", ".vcf.bgz", ".bcf")):
                names = ["vcf_header.txt", "vcf_statistik.txt"]
                command = (
                    "bcftools view -h /input > vcf_header.txt && "
                    "bcftools stats /input > vcf_statistik.txt"
                )
            elif self.v["file"].lower().endswith((".bam", ".cram")):
                names = ["alignment_header.txt"]
                command = (
                    "samtools quickcheck -v /input && "
                    "samtools view -H /input > alignment_header.txt"
                )
            else:
                file_mounts.append(
                    (Path(__file__).with_name("linux_helpers.py"), "/helpers.py")
                )
                names = ["chip-statistics.json", "report.html"]
                command = "python /helpers.py inspect_chip /input ."
        elif action == "deepvariant":
            model = self.v["model"]
            if model not in {"WGS", "WES", "PACBIO"}:
                raise ValueError("Select the model matching the sequencing technology.")
            alignment = (
                "reads.cram" if self.v["bam"].lower().endswith(".cram") else "reads.bam"
            )
            reference = "referenz.fa"
            if self.v["reference"].lower().endswith((".gz", ".bgz")):
                reference += ".gz"
            inputs = {"bam": "/alignment", "reference": "/reference"}
            names = [
                "varianten.vcf.gz",
                "varianten.g.vcf.gz",
                reference + ".fai",
                alignment + (".crai" if alignment.endswith(".cram") else ".bai"),
            ]
            command = (
                f"ln -s /reference {reference} && ln -s /alignment {alignment} "
                f"&& samtools faidx {reference} && samtools quickcheck -v {alignment} "
                f"&& samtools index -@ {threads - 1} {alignment} && mkdir .tmp "
                "&& HOME=/output/.tmp TMPDIR=/output/.tmp "
                + ("" if gpu else "CUDA_VISIBLE_DEVICES= ")
                + f"/opt/deepvariant/bin/run_deepvariant --model_type={model} "
                f"--ref={reference} --reads={alignment} --output_vcf=varianten.vcf.gz "
                "--output_gvcf=varianten.g.vcf.gz --vcf_stats_report=true "
                f"--num_shards={min(threads, 4)}"
            )
        elif action == "bam_qc":
            cram = self.v["bam"].lower().endswith(".cram")
            reference = self.v.get("reference")
            if cram and not reference:
                raise ValueError("CRAM requires the exact matching reference FASTA.")
            align = "reads.cram" if cram else "reads.bam"
            inputs = {"bam": "/alignment"}
            names = [
                align + (".crai" if cram else ".bai"),
                "flagstat.txt",
                "samtools_stats.txt",
                "abdeckung.mosdepth.global.dist.txt",
                "abdeckung.mosdepth.summary.txt",
            ]
            commands = [f"ln -s /alignment {align}"]
            if reference:
                inputs["reference"] = "/reference"
                commands += [
                    "ln -s /reference referenz.fa",
                    "samtools faidx referenz.fa",
                ]
                names.append("referenz.fa.fai")
            ref_option = " --reference referenz.fa" if reference else ""
            fasta_option = " --fasta referenz.fa" if reference else ""
            commands += [
                f"samtools quickcheck -v {align}",
                f"samtools index {align}",
                f"samtools flagstat -@ {threads - 1}{ref_option} {align} > flagstat.txt",
                f"samtools stats -@ {threads - 1}{ref_option} {align} > samtools_stats.txt",
                f"mosdepth -n -t {threads}{fasta_option} abdeckung {align}",
                "mkdir -p .tmp",
                "HOME=/output/.tmp TMPDIR=/output/.tmp XDG_CACHE_HOME=/output/.tmp "
                "multiqc flagstat.txt samtools_stats.txt abdeckung.mosdepth.summary.txt "
                "abdeckung.mosdepth.global.dist.txt -o qualitaetsbericht",
            ]
            command = " && ".join(commands)
            names.append("qualitaetsbericht/multiqc_report.html")
            directories.append("qualitaetsbericht")
        elif action in {"fastq_qc", "fastq_report"}:
            inputs = {"r1": "/read1"}
            if self.v.get("r2"):
                inputs["r2"] = "/read2"
            inputs = {
                key: target + (".gz" if self.v[key].endswith(".gz") else "")
                for key, target in inputs.items()
            }
            read1 = inputs["r1"]
            if action == "fastq_qc":
                names = ["fastp.html", "fastp.json", "gefiltert_R1.fastq.gz"]
                command = f"fastp -i {read1} -o gefiltert_R1.fastq.gz -h fastp.html -j fastp.json"
                if "r2" in inputs:
                    names.append("gefiltert_R2.fastq.gz")
                    command += f" -I {inputs['r2']} -O gefiltert_R2.fastq.gz"
            else:
                names = ["fastq_quality.html", "fastq_quality.json"]
                command = (
                    f"fastp --in1 {read1} --disable_adapter_trimming "
                    "--disable_quality_filtering --disable_length_filtering "
                    "--html fastq_quality.html --json fastq_quality.json"
                )
                if "r2" in inputs:
                    command += f" --in2 {inputs['r2']}"
            command += f" --thread {threads}"
        else:
            raise ValueError("This task has no Kiri execution route.")
        container = "dna-workbench-" + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(dir=self.folder) as staging:
            if action == "opencravat_run":
                (Path(staging) / "annotation").mkdir()
            if action in {"gatk_validate", "vep", "rfmix"}:
                for name in names:
                    (Path(staging) / name).touch()
            args = [
                *prefix,
                "run",
                "--rm",
                "--name",
                container,
                "--pull=never",
                "--platform=" + container_platform,
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--cpus",
                str(threads),
                "--mount",
                kiri_bind(staging, "/output", desktop=gpu),
                "--workdir",
                "/output",
                "--entrypoint",
                "/bin/sh",
            ]
            if action == "chip_vcf" or (
                action == "inspect" and command.startswith("python")
            ):
                args.extend(["--tmpfs", "/opt/dna/cache/snps:rw,mode=1777"])
            if gpu:
                args.extend(["--gpus", "1"])
            if action in {"gatk_validate", "rfmix"}:
                args.extend(["--tmpfs", "/tmp:rw,nosuid,nodev,mode=1777"])
            if action == "opencravat_run":
                args.extend(
                    [
                        "--tmpfs",
                        "/tmp:rw,nosuid,nodev,mode=1777",
                        "--tmpfs",
                        "/usr/local/lib/python3.12/site-packages/cravat/workspace:rw,nosuid,nodev,mode=1777",
                        "--tmpfs",
                        "/usr/local/lib/python3.12/site-packages/cravat/metrics:rw,nosuid,nodev,mode=1777",
                    ]
                )
            file_mounts.extend((self.v[key], target) for key, target in inputs.items())
            for source, target in file_mounts:
                args.extend(
                    ["--mount", kiri_bind(source, target, readonly=True, desktop=gpu)]
                )
            if os.name != "nt":
                args.extend(["--user", f"{os.getuid()}:{os.getgid()}"])
            self.log(
                "Using local Docker for " + action + "."
                if gpu
                else "Using local Kiri for " + action + "."
            )
            self.run_process(
                [
                    *args,
                    image,
                    "-ec",
                    command,
                ],
                env=env,
                cancel_command=[*prefix, "rm", "-f", container],
            )
            outputs = [Path(staging) / name for name in names]
            if any(
                p.is_symlink() or not p.is_file() or not p.stat().st_size
                for p in outputs
            ):
                raise RuntimeError("Kiri did not produce all expected result files.")
            for directory in directories:
                report = Path(staging) / directory
                if (
                    not report.is_dir()
                    or report.is_symlink()
                    or any(
                        p.is_symlink() or not (p.is_file() or p.is_dir())
                        for p in report.rglob("*")
                    )
                ):
                    raise RuntimeError(
                        "Kiri returned an unexpected entry in the report."
                    )
            for directory in directories:
                (Path(staging) / directory).rename(self.out / directory)
            for path in outputs:
                if path.parent == Path(staging):
                    path.replace(self.out / path.name)
            if action == "peddy":
                for path in Path(staging).glob("familien_qc.*"):
                    if path.is_file() and not path.is_symlink():
                        path.replace(self.out / path.name)
            if action == "deepvariant":
                for pattern in (
                    "varianten*.tbi",
                    "varianten*.html",
                    "referenz.fa.gz.gzi",
                ):
                    for path in Path(staging).glob(pattern):
                        if path.is_file() and not path.is_symlink():
                            path.replace(self.out / path.name)
            if action == "pca":
                for name in ("ld.prune.out", "pca_mode.txt"):
                    path = Path(staging) / name
                    if path.is_file() and not path.is_symlink():
                        path.replace(self.out / name)

    def windows(self):
        a = self.task["action"]
        v = self.v
        if a == "ugene":
            if os.name != "nt":
                self.launch_native_tool("ugene", v.get("file"))
                return
            candidates = list(
                (ROOT / "DNA_Software/Windows/UGENE").glob("**/ugeneui.exe")
            )
            if len(candidates) != 1:
                raise ValueError("Install the optional portable UGENE package first")
            args = [str(candidates[0])] + ([v["file"]] if v.get("file") else [])
            subprocess.Popen(
                args,
                cwd=str(self.out),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        elif a == "provider_export":
            import provider_exports

            provider_exports.inspect_export(
                self.person,
                v,
                self.out,
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
            )
        elif a in (
            "variant_evidence_audit",
            "sequence_explore",
            "model_readiness",
            "dna_message",
            "agent_handoff",
        ):
            import research_explorer

            fn = {
                "variant_evidence_audit": research_explorer.audit_vcf,
                "sequence_explore": research_explorer.explore,
                "model_readiness": research_explorer.model_readiness,
                "dna_message": research_explorer.dna_message,
                "agent_handoff": research_explorer.agent_handoff,
            }[a]
            fn(
                self.person,
                v,
                self.out,
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
            )
        elif a in (
            "sequence_stats",
            "fasta_collect",
            "sequence_extract",
            "sequence_transform",
            "seqviz_view",
        ):
            import sequence_tools

            fn = {
                "sequence_stats": sequence_tools.stats,
                "fasta_collect": sequence_tools.merge,
                "sequence_extract": sequence_tools.extract,
                "sequence_transform": sequence_tools.transform,
                "seqviz_view": sequence_tools.view,
            }[a]
            fn(
                self.person,
                v,
                self.out,
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
            )
        elif a in ("storybook", "helix_export", "avatar_pack"):
            import creative_exports

            fn = {
                "storybook": creative_exports.storybook,
                "helix_export": creative_exports.helix,
                "avatar_pack": creative_exports.avatar_pack,
            }[a]
            fn(self.person, v, self.out, self.log)
        elif a == "profile_analyze":
            import profile_pipeline

            chain = Path(
                v.get("chain") or ROOT / "References/LiftOver/hg19ToHg38.over.chain.gz"
            )
            reference = Path(
                v.get("reference")
                or ROOT
                / "References/FASTA_GRCh38/GRCh38_full_analysis_set_plus_decoy_hla.fa"
            )
            report = profile_pipeline.analyze(
                self.person,
                self.out,
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
                target="GRCh38" if v.get("target") == "GRCh38" else "separate",
                chain=chain if chain.is_file() else None,
                reference=reference if reference.is_file() else None,
            )
            if not any(
                s.get("status") == "analyzed" and s.get("called", 0) > 0
                for s in report["sources"]
            ):
                raise ValueError(
                    "No eligible SNP genotype sources. Read/report/SV-only files use their own type-specific workflows; no SNP comparison was completed."
                )
        elif a == "profile_refresh":
            import profile_pipeline

            atomic(
                self.out / "refresh.json",
                profile_pipeline.refresh(
                    self.person,
                    self.out,
                    self.log,
                    lambda: (self.folder / "abbrechen.request").exists(),
                ),
            )
        elif a == "research_synthesis":
            import research_synthesis

            research_synthesis.build(self.person, self.out, self.log)
        elif a == "best_dataset":
            import best_dataset

            atomic(
                self.out / "BestDataset-result.json",
                best_dataset.build(
                    self.person,
                    self.out,
                    v["build"],
                    v["reference"],
                    v.get("chain")
                    or ROOT / "References/LiftOver/hg19ToHg38.over.chain.gz",
                    self.log,
                    lambda: (self.folder / "abbrechen.request").exists(),
                ),
            )
        elif a == "profile_generate":
            import profile_pipeline

            analysis = v.get("analysis")
            if not analysis:
                available = sorted(
                    (ROOT / "Projects/Launcher" / self.person).glob(
                        "*/Results/analysis.json"
                    ),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if not available:
                    raise ValueError("First analyze all profile files.")
                analysis = str(available[0].parent)
            profile_pipeline.generate(
                self.person,
                analysis,
                self.out,
                v["build"],
                v["reference"],
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
            )
        elif a == "profile_activate":
            import profile_pipeline

            atomic(
                self.out / "activation.json",
                profile_pipeline.activate(
                    self.person,
                    v["folder"],
                    lambda: (self.folder / "abbrechen.request").exists(),
                ),
            )
        elif a == "liftover_snps":
            import snp_liftover

            snp_liftover.run(
                self.person,
                v["file"],
                v["build"],
                v["target"],
                v["chain"],
                v["reference"],
                self.out,
                self.log,
                lambda: (self.folder / "abbrechen.request").exists(),
            )
        elif a == "import":
            checks = Path(v.get("checked_folder", ""))
            if not checks.is_dir() or not (checks / "inspection.json").exists():
                raise ValueError(
                    "Please check the files in the import window first and view the result."
                )
            payloads = [
                json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(checks.glob("*_inspection.json"))
            ]
            for source in v["files"]:
                found = next(
                    (
                        r
                        for r in payloads
                        if Path(r["path"]).resolve() == Path(source).resolve()
                    ),
                    None,
                )
                if not found:
                    raise ValueError("File not pre-checked:" + str(source))
                st = Path(source).stat()
                if st.st_size != found["bytes"] or st.st_mtime_ns != found["mtime_ns"]:
                    raise ValueError("File has changed since checking." + str(source))
                if found["color"] in ["red", "black"]:
                    raise ValueError(
                        "Import halted due to file error or severe assignment conflict:"
                        + str(source)
                    )
            provider = v["provider"].strip()
            info = []
            groups = {}
            for source in v["files"]:
                found = next(
                    r
                    for r in payloads
                    if Path(r["path"]).resolve() == Path(source).resolve()
                )
                chosen = (
                    found["provider"]
                    if provider in ["", "Detect automatically"]
                    else provider
                )
                groups.setdefault(chosen or "Unknown", []).append(source)
            expected = {str(Path(r["path"]).resolve()): r["sha256"] for r in payloads}
            for chosen, files in groups.items():
                info.append(
                    source_store.import_batch(
                        self.person,
                        files,
                        chosen,
                        v.get("label", ""),
                        v.get("declared_build", "")
                        if v.get("declared_build") in ["GRCh37", "GRCh38"]
                        else "",
                        v.get("measurement", "Unknown"),
                        v.get("note", ""),
                        self.log,
                        lambda: (self.folder / "abbrechen.request").exists(),
                        expected,
                        storage_mode={"Verschieben": "move", "Kopieren": "copy"}.get(
                            v.get("storage_mode"), v.get("storage_mode", "copy")
                        ),
                    )
                )
            db = source_store.connect(self.person)
            db.execute(
                "CREATE TABLE IF NOT EXISTS inspections(sha256 TEXT PRIMARY KEY,payload TEXT NOT NULL,checked TEXT)"
            )
            for r in payloads:
                db.execute(
                    "INSERT OR REPLACE INTO inspections VALUES(?,?,?)",
                    (r["sha256"], json.dumps(r, ensure_ascii=False), r["checked"]),
                )
            db.commit()
            db.close()
            atomic(self.out / "import_register.json", info)
            page(
                self.out / "import.html",
                "Local dataset import",
                "<pre>"
                + html.escape(json.dumps(info, indent=2, ensure_ascii=False))
                + "</pre><p>Files remain separated by source. No genotypes were merged.</p>",
            )
        elif a == "archive_index":
            atomic(
                self.out / "archive-register.json",
                source_store.index_archive(
                    self.person,
                    self.log,
                    lambda: (self.folder / "abbrechen.request").exists(),
                ),
            )
        elif a == "variant_index":
            atomic(
                self.out / "varianten_index.json",
                source_store.index_vcfs(
                    self.person,
                    v["files"],
                    v.get("fallback", "")
                    if v.get("fallback", "").startswith("GRCh")
                    else "",
                    self.log,
                    lambda: (self.folder / "abbrechen.request").exists(),
                ),
            )
        elif a in ["inventory", "checklist"]:
            rows = []
            for source in v["files"]:
                p = Path(source)
                row = {
                    "file": str(p),
                    "name": p.name,
                    "bytes": p.stat().st_size,
                    "person_assignment": self.person,
                    "provider": v.get("provider", "Unknown"),
                }
                if a == "inventory":
                    self.log("SHA-256: " + p.name)
                    row["sha256"] = sha(p)
                    if zipfile.is_zipfile(p):
                        with zipfile.ZipFile(p) as z:
                            row["zip_members"] = [
                                {"name": i.filename, "bytes": i.file_size}
                                for i in z.infolist()
                            ]
                rows.append(row)
                self.save()
            atomic(
                self.out / "file-register.json",
                {"files": rows, "note": v.get("note", "")},
            )
            table = (
                "<table><tr><th>File</th><th>Bytes</th><th>SHA-256</th></tr>"
                + "".join(
                    "<tr><td>"
                    + html.escape(r["name"])
                    + "</td><td>"
                    + str(r["bytes"])
                    + '</td><td style="word-break:break-all">'
                    + r.get("sha256", "not calculated in this step")
                    + "</td></tr>"
                    for r in rows
                )
                + "</table>"
            )
            if a == "checklist":
                types = {
                    "Reads FASTQ": (".fastq", ".fastq.gz", ".fq.gz"),
                    "BAM/CRAM": (".bam", ".cram"),
                    "Alignment-Index": (".bai", ".crai", ".csi"),
                    "Variants": (".vcf", ".vcf.gz", ".bcf"),
                    "Provider reports": (".pdf",),
                    "Chip raw data": (".csv", ".txt", ".zip"),
                }
                table += (
                    "<h2>File types in the selection</h2><ul>"
                    + "".join(
                        "<li>"
                        + html.escape(label)
                        + ": "
                        + (
                            "Present"
                            if any(r["name"].lower().endswith(exts) for r in rows)
                            else "Not found"
                        )
                        + "</li>"
                        for label, exts in types.items()
                    )
                    + "</ul><p>Record sample date, sample identity, exact reference, checksums, quality report and measured/imputed status. Archive contents alone do not establish completeness.</p>"
                )
            page(self.out / "report.html", self.task["title"], table)
        elif a == "report":
            alljobs = []
            for p in (ROOT / "Projects/Launcher" / self.person).glob("*/status.json"):
                try:
                    j = json.loads(p.read_text())
                    if j["id"] != self.id:
                        alljobs.append(j)
                except (ValueError, OSError, KeyError, TypeError) as error:
                    self.log("Skipped unreadable job metadata: " + str(error))
            alljobs.sort(key=lambda j: j.get("started", ""))
            rows = "".join(
                "<tr><td>"
                + html.escape(j["started"])
                + "</td><td>"
                + html.escape(j["title"])
                + "</td><td>"
                + html.escape(j["status"])
                + '</td><td><a href="'
                + html.escape(Path(j["output"]).as_uri(), quote=True)
                + '">Results folder</a></td></tr>'
                for j in alljobs
            )
            body = (
                "<p>Profile ID: "
                + html.escape(self.person)
                + " · Created: "
                + html.escape(NOW())
                + "</p><p>Local research overview; not a diagnosis or clinical confirmation.</p><p>"
                + html.escape(v.get("note", ""))
                + "</p><table><tr><th>Date</th><th>Job</th><th>Status</th><th>Evidence</th></tr>"
                + rows
                + "</table>"
            )
            page(self.out / "results-overview.html", "DNA: sources and results", body)
            atomic(self.out / "jobs.json", alljobs)
            (self.out / "notes.md").write_text(
                "# Research Overview"
                + self.person
                + "\n\n"
                + v.get("note", "")
                + "\n\nSources, parameters and outputs are recorded per job. Clinical confirmation must be documented separately.\n",
                encoding="utf-8",
            )
        elif a == "export":
            manifest = []
            files = v["files"]
            automatic = v.get("compression_mode", "Automatic") != "Manual"
            already = (
                ".gz",
                ".bgz",
                ".zip",
                ".bcf",
                ".pgen",
                ".bed",
                ".bam",
                ".cram",
                ".jpg",
                ".png",
                ".pdf",
            )
            packaging = (
                (
                    "Without archive (folder)"
                    if len(files) == 1 and files[0].lower().endswith(already)
                    else "ZIP"
                )
                if automatic
                else v.get("packaging", "ZIP")
            )
            level = (
                6
                if automatic
                else int(str(v.get("compression_level", "6")).split(" ")[0])
            )
            if not 0 <= level <= 9:
                raise ValueError("The compression stage shall be between 0 and 9.")
            if packaging.startswith("GZIP"):
                if len(files) != 1:
                    raise ValueError(
                        "GZIP supports exactly one file here. Select ZIP for several files."
                    )
                source = Path(files[0])
                target = self.out / (source.name + ".gz")
                with (
                    source.open("rb") as inp,
                    gzip.open(target, "wb", compresslevel=level) as out,
                ):
                    shutil.copyfileobj(inp, out, 8 * 1024 * 1024)
                manifest.append(
                    {
                        "source": str(source),
                        "export": target.name,
                        "source_sha256": sha(source),
                        "sha256": sha(target),
                    }
                )
            elif packaging == "ZIP":
                target = self.out / (self.person + "_Datensatz.zip")
                with zipfile.ZipFile(
                    target,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=max(1, level),
                ) as z:
                    for i, source in enumerate(files, 1):
                        p = Path(source)
                        self.log("Export: " + p.name)
                        inside = str(i).zfill(3) + "/" + p.name
                        method = (
                            zipfile.ZIP_STORED
                            if level == 0
                            or automatic
                            and p.name.lower().endswith(already)
                            else zipfile.ZIP_DEFLATED
                        )
                        z.write(
                            p,
                            inside,
                            compress_type=method,
                            compresslevel=None
                            if method == zipfile.ZIP_STORED
                            else level,
                        )
                        manifest.append(
                            {
                                "source": str(p),
                                "archive_path": inside,
                                "sha256": sha(p),
                                "compression": "stored"
                                if method == zipfile.ZIP_STORED
                                else "deflate",
                            }
                        )
                    z.writestr(
                        "file-register.json",
                        json.dumps(manifest, indent=2, ensure_ascii=False),
                    )
            else:
                target = self.out / "Files"
                target.mkdir()
                for i, source in enumerate(files, 1):
                    p = Path(source)
                    dest = target / (str(i).zfill(3) + "_" + p.name)
                    shutil.copy2(p, dest)
                    digest = sha(dest)
                    if digest != sha(p):
                        raise ValueError("Export copy differs from the source.")
                    manifest.append(
                        {"source": str(p), "export": dest.name, "sha256": digest}
                    )
            atomic(
                self.out / "export-checksums.json",
                {
                    "packaging": packaging,
                    "automatic": automatic,
                    "level": level,
                    "output": target.name,
                    "sha256": sha(target) if target.is_file() else None,
                    "files": manifest,
                },
            )
        elif a in ["family", "visual"]:
            subprocess.Popen([str(ROOT / "DNA_Launcher.exe"), "--" + a])
        elif a == "versions":
            subprocess.Popen(
                [
                    windows_executable("notepad.exe"),
                    str(ROOT / "DNA_Software/INSTALLATIONSSTATUS.md"),
                ]
            )
        else:
            raise ValueError("Unbekannte Windows-Aktion.")

    def launch_native_tool(self, tool, filename=None):
        command = desktop_tool_command(ROOT, tool, filename)
        if not command:
            raise ValueError(
                f"Install a compatible desktop build of {tool}. For genome tracks, "
                "IGV.js and JBrowse Web are available through the tool gallery."
                if tool in {"igv", "jbrowse"}
                else f"Install a compatible desktop build of {tool}."
            )
        # Desktop apps outlive the job. Record an immediate startup failure.
        with (self.folder / "software.log").open("ab") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            code = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return
        if code:
            raise RuntimeError(f"{tool} could not start. See software.log.")

    def launch(self):
        core = self.task["core"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if os.name != "nt":
            if core in {"Gramps", "IGV", "JBrowse"}:
                self.launch_native_tool(core.lower())
                return
            if core == "Explorer":
                folder = str(ROOT / "Projects/Launcher")
                if sys.platform == "darwin":
                    subprocess.run(["/usr/bin/open", folder], check=True)
                    return
                if Path("/usr/bin/xdg-open").is_file():
                    subprocess.run(["/usr/bin/xdg-open", folder], check=True)
                    return
            raise ValueError(
                "This desktop shortcut has no adapter for this operating system."
            )
        if core == "Explorer":
            os.startfile(str(ROOT / "Projects/Launcher"))
            return
        if core in ["PowerShell", "Cmd"]:
            subprocess.Popen(
                [windows_executable("powershell.exe"), "-NoExit", "-NoProfile"]
                if core == "PowerShell"
                else [windows_executable("cmd.exe")],
                cwd=ROOT / "Projects",
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return
        args = [
            windows_executable("powershell.exe"),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(CORE),
            "-Action",
            core,
        ]
        if core in ["Start", "StopAll", "Export"]:
            self.run_process(args)
            return
        if core in ["Linux", "Jupyter"]:
            subprocess.Popen(
                args, cwd=ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return
        urls = {
            "OpenCRAVAT": ("http://localhost:8042", 8042),
            "Haplogrep": ("http://localhost:7001", 7001),
            "Admixtools": ("http://localhost:7070", 7070),
        }
        with (self.folder / "software.log").open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                args, stdout=log, stderr=subprocess.STDOUT, creationflags=flags
            )
        if core in urls:
            url, port = urls[core]
            for i in range(180):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                        pass
                    os.startfile(url)
                    return
                except OSError:
                    if proc.poll() is not None:
                        raise RuntimeError(
                            "The interface could not be started. See software.log."
                        )
                    self.save()
                    time.sleep(1)
            raise RuntimeError("Time-out at start. See software.log.")
        time.sleep(2)
        if proc.poll() not in [None, 0]:
            raise RuntimeError("Softwarestart fehlgeschlagen. Siehe software.log.")

    def execute(self, preview=False):
        self.validate()
        self.state["status"] = "Preview" if preview else "Running"
        self.save()
        self.log(self.task["title"] + " · " + self.person)
        linux_action = self.task["platform"] == "WSL" and self.task["kind"] != "launch"
        if linux_action:
            text = self.shell()
            (self.folder / "ausfuehren.sh").write_bytes(text.encode("utf-8"))
            (self.folder / "command.txt").write_text(text, encoding="utf-8")
        else:
            (self.folder / "command.txt").write_text(
                self.task["description"] + "\n\n" + self.task["help"], encoding="utf-8"
            )
        if preview:
            self.state["status"] = "Preview"
            self.state["finished"] = NOW()
            self.save()
            return
        import tool_inputs

        biological = set(tool_inputs.source_fields(self.task))
        manifest = self.r.get("input_manifest", {"sources": []})
        sources = manifest.setdefault("sources", [])
        for field in self.task["fields"]:
            if field["key"] not in biological or field["kind"] != "file":
                continue
            value = self.v.get(field["key"], [])
            for path in value if isinstance(value, list) else [value]:
                if not path:
                    continue
                p = Path(path).resolve()
                st = p.stat()
                entry = next(
                    (
                        x
                        for x in sources
                        if x.get("field") == field["key"] and x.get("path") == str(p)
                    ),
                    None,
                )
                if entry is None:
                    entry = {"field": field["key"], "path": str(p)}
                    sources.append(entry)
                if not entry.get("sha256"):
                    self.log("Record source checksum: " + p.name)
                    entry["sha256"] = sha(p)
                    if (p.stat().st_size, p.stat().st_mtime_ns) != (
                        st.st_size,
                        st.st_mtime_ns,
                    ):
                        raise ValueError("Input changed while hashing.")
                entry.update(bytes=st.st_size, mtime_ns=st.st_mtime_ns)
        self.r["input_manifest"] = manifest
        atomic(self.request_path, self.r)
        atomic(
            self.out / "source-provenance.json",
            {
                "person": self.person,
                "task": self.task["id"],
                "app_version": json.loads(
                    Path(__file__)
                    .with_name("install-lock.json")
                    .read_text(encoding="utf-8")
                )["app_version"],
                "inputs": manifest,
            },
        )
        if self.task["action"] == "launch":
            self.launch()
        elif linux_action:
            kiri = None
            kiri_pipeline = None
            action = self.task["action"]
            gpu_route = windows_deepvariant_gpu() if action == "deepvariant" else None
            if os.name == "nt" and action in {"sarek", "pgs"}:
                import on_demand

                if not on_demand.status(self.task["id"], allow_kiri=False)["ready"]:
                    kiri_pipeline = on_demand.windows_kiri_pipeline(action)
            if not gpu_route and action in KIRI_TASK_TOOLS:
                import on_demand

                filename = self.v.get("file", "") if action == "inspect" else ""
                required = on_demand.mapped(self.task["id"], filename)
                kiri_tool = kiri_task_tool(action, required)
                if kiri_tool == "vep" and not kiri_vep_cache(ROOT):
                    kiri_tool = None
                if kiri_tool == "opencravat_run" and not kiri_opencravat_modules(ROOT):
                    kiri_tool = None
                if kiri_tool == "rfmix" and not on_demand.rfmix_license_reviewed():
                    kiri_tool = None
                if kiri_tool:
                    if not on_demand.status(
                        self.task["id"], filename, allow_kiri=False
                    )["ready"]:
                        kiri = kiri_sequence_tool(kiri_tool)
            if not gpu_route and not kiri and not kiri_pipeline:
                for args in wsl_host_bootstrap(self.task["action"]):
                    self.run_process(args)
            atomic(self.folder / "versionen.json", recorded_installation())
            if gpu_route:
                self.run_with_kiri(gpu_route, gpu=True)
            elif kiri_pipeline:
                self.run_kiri_pipeline(kiri_pipeline)
            elif kiri:
                self.run_with_kiri(kiri)
            elif os.name == "nt":
                self.run_process(
                    [
                        windows_executable("wsl.exe"),
                        "-d",
                        distro_name(ROOT),
                        "-u",
                        "dna",
                        "--",
                        "env",
                        "DNA_LAUNCHER_JOB=" + self.id,
                        "setsid",
                        "bash",
                        linux(self.folder / "ausfuehren.sh"),
                    ]
                )
            else:
                env = os.environ.copy()
                env["DNA_LAUNCHER_JOB"] = self.id
                self.run_process(
                    ["bash", str(self.folder / "ausfuehren.sh")],
                    env=env,
                    start_new_session=True,
                )
        else:
            self.windows()
        for entry in sources if self.task["action"] != "import" else []:
            p = Path(entry["path"])
            if not p.is_file() or (p.stat().st_size, p.stat().st_mtime_ns) != (
                entry.get("bytes"),
                entry.get("mtime_ns"),
            ):
                raise ValueError(
                    "Input changed during processing; result not marked complete."
                )
        self.state["status"] = (
            "Started" if self.task["kind"] == "launch" else "Complete"
        )
        self.state["finished"] = NOW()
        self.state["outputs"] = [
            str(p.relative_to(self.out))
            for p in self.out.rglob("*")
            if p.is_file() and not p.is_symlink()
        ]
        self.save()
        if self.task["kind"] != "launch" and self.task["id"] not in (
            "import",
            "archive_index",
            "variant_index",
            "profile_activate",
            "profile_refresh",
            "export",
        ):
            try:
                import analysis_reports

                self.state["research_report"] = analysis_reports.publish(
                    self.folder, self.person, self.task["id"]
                )
            except Exception as report_error:
                self.state["research_report"] = {
                    "status": "report_pending",
                    "error": str(report_error),
                }
                self.log(
                    "Analysis completed; PDF/index preparation needs attention: "
                    + str(report_error)
                )
        if self.task["kind"] != "launch":
            import result_cache

            result_cache.seal(self.folder)
        self.state["outputs"] = [
            str(p.relative_to(self.out))
            for p in self.out.rglob("*")
            if p.is_file() and not p.is_symlink()
        ]
        self.save()
        self.log("Fertig. Results: " + str(self.out))


def main():
    job = None
    try:
        if sys.argv[1] == "--library":
            print(json.dumps(source_store.listing(sys.argv[2]), ensure_ascii=False))
            return 0
        if sys.argv[1] == "--new-person":
            print(source_store.new_person(sys.argv[2]))
            return 0
        if sys.argv[1] == "--providers":
            print(json.dumps(inspector.PROVIDERS, ensure_ascii=False))
            return 0
        if sys.argv[1] == "--profile":
            print(json.dumps(source_store.profile(sys.argv[2]), ensure_ascii=False))
            return 0
        if sys.argv[1] == "--inspect":
            request = security_paths.input_file(sys.argv[2])
            folder = request.parent
            project_root = (ROOT / "Projects").resolve()
            verification = (project_root / "Source verification").resolve()
            launcher = (project_root / "Launcher").resolve()
            legacy = request.name == "pruefanfrage.json" and folder.is_relative_to(
                verification
            )
            if not legacy and (
                request.name != "check-request.json"
                or not folder.is_relative_to(launcher)
            ):
                raise ValueError("Unexpected inspection request path.")
            r = json.loads(request.read_text(encoding="utf-8-sig"))
            if legacy:
                inspector.check_batch(
                    r["person"], r["files"], folder, lambda s: print(s, flush=True)
                )
                return 0
            status_file = security_paths.contained(folder, "status.json")
            results_folder = security_paths.contained(folder, "Results")
            summary_file = security_paths.contained(
                results_folder, "check-summary.json"
            )
            status = json.loads(status_file.read_text(encoding="utf-8"))
            try:
                results = inspector.check_batch(
                    r["person"], r["files"], folder, lambda s: print(s, flush=True)
                )
                results_folder.mkdir(exist_ok=True)
                shutil.copyfile(
                    security_paths.contained(folder, "inspection.json"), summary_file
                )
                atomic(
                    folder / "inputs.json",
                    {
                        "person": r["person"],
                        "task": "inspection",
                        "inputs": {"files": r["files"]},
                        "input_manifest": {
                            "sources": [
                                {
                                    k: item.get(k)
                                    for k in (
                                        "path",
                                        "sha256",
                                        "bytes",
                                        "mtime_ns",
                                        "checked",
                                        "build",
                                    )
                                }
                                for item in results
                            ]
                        },
                    },
                )
                status.update(
                    status="Complete",
                    finished=NOW(),
                    kind="analysis",
                    outputs=["check-summary.json"],
                )
                atomic(folder / "status.json", status)
                import execution_journal

                execution_journal.register(folder)
                return 0
            except Exception as error:
                status.update(status="Failed", error=str(error), finished=NOW())
                atomic(folder / "status.json", status)
                atomic(
                    folder / "inputs.json",
                    {
                        "person": r["person"],
                        "task": "inspection",
                        "inputs": {"files": r["files"]},
                    },
                )
                import execution_journal

                execution_journal.register(folder)
                raise
        job = Job(sys.argv[1])
        job.execute("--preview" in sys.argv)
    except BaseException as e:
        if job:
            job.log(str(e))
            job.log(traceback.format_exc())
            job.state["status"] = (
                "Cancelled" if isinstance(e, InterruptedError) else "Failed"
            )
            job.state["error"] = str(e)
            job.state["finished"] = NOW()
            job.save()
        else:
            print(traceback.format_exc(), file=sys.stderr)
        return 1
    finally:
        if job:
            job.log_handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
