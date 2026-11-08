from system_tools import windows_executable

"""Portable local job runner for DNA Workbench. Never uploads DNA files."""
from portable_paths import distro_name
from pathlib import Path, PurePosixPath
import sys, os, subprocess, shlex, time, datetime, traceback, hashlib, csv, zipfile, html, re, socket, threading, gzip, shutil
import portable_json as json
import source_store
import inspector

ROOT = Path(__file__).resolve().parents[2]
CAT = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
TASKS = {t["id"]: t for t in CAT["tasks"]}
CORE = ROOT / "DNA_Software/Start/DNA.ps1"
NOW = lambda: datetime.datetime.now().astimezone().isoformat()
Q = shlex.quote


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

    def shell(self):
        a = self.task["action"]
        v = self.v
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "source " + Q(linux(ROOT / "DNA_Software/Start/profile-dna.sh")),
            "export PATH=" + Q(linux(ROOT / "DNA_Software/Linux/bin")) + ":$PATH",
            "export PYTHONUNBUFFERED=1",
            "echo $$ > " + Q(linux(self.folder / "linux.pid")),
            "mkdir -p " + Q(self.o()),
            "cd " + Q(self.o()),
        ]
        helper = linux(Path(__file__).with_name("linux_helpers.py"))

        def cmd(*args):
            lines.append(" ".join(Q(str(x)) for x in args))

        def py(*args):
            cmd(analysis_python(), helper, *args)

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
                "-w",
                "4",
            ]
            if v.get("r2"):
                args += ["-I", self.p("r2"), "-O", self.o("gefiltert_R2.fastq.gz")]
            cmd(*args)
        elif a in ["bam_qc", "deepvariant"]:
            source = self.p("bam")
            iscram = source.lower().endswith(".cram")
            if iscram and not v.get("reference"):
                raise ValueError("CRAM requires the exact matching reference FASTA.")
            align = self.o("reads.cram" if iscram else "reads.bam")
            cmd("ln", "-s", source, align)
            rf = reference() if v.get("reference") else None
            cmd("samtools", "quickcheck", "-v", align)
            cmd("samtools", "index", "-@", "4", align)
            if a == "bam_qc":
                extra = ["--reference", rf] if rf else []
                lines.append(
                    " ".join(Q(x) for x in ["samtools", "flagstat", *extra, align])
                    + " > flagstat.txt"
                )
                lines.append(
                    " ".join(Q(x) for x in ["samtools", "stats", *extra, align])
                    + " > samtools_stats.txt"
                )
                cmd(
                    "mosdepth",
                    "-t",
                    "4",
                    "-n",
                    *(["--fasta", rf] if rf else []),
                    self.o("abdeckung"),
                    align,
                )
                cmd("multiqc", self.o(), "-o", self.o("qualitaetsbericht"))
            else:
                dirs = {
                    str(PurePosixPath(source).parent),
                    str(PurePosixPath(self.p("reference")).parent),
                }
                args = ["docker", "run", "--rm", "--user", "1000:1000"]
                for d in sorted(dirs):
                    args += ["-v", d + ":" + d + ":ro"]
                args += [
                    "-v",
                    self.o() + ":" + self.o(),
                    "google/deepvariant:1.10.0",
                    "/opt/deepvariant/bin/run_deepvariant",
                    "--model_type=" + v["model"],
                    "--ref=" + rf,
                    "--reads=" + align,
                    "--output_vcf=" + self.o("varianten.vcf.gz"),
                    "--output_gvcf=" + self.o("varianten.g.vcf.gz"),
                    "--intermediate_results_dir=" + self.o("zwischenschritte"),
                    "--num_shards=4",
                    "--vcf_stats_report=true",
                ]
                cmd(*args)
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
            rf = reference()
            sheet = self.folder / "samplesheet.csv"
            with sheet.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(
                    ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"]
                )
                w.writerow(
                    [
                        self.person,
                        {"XX": 2, "XY": 1}.get(v["sex"], 0),
                        0,
                        self.person,
                        "L001",
                        self.p("r1"),
                        self.p("r2"),
                    ]
                )
            cmd(
                "sarek",
                "--input",
                linux(sheet),
                "--fasta",
                rf,
                "--fasta_fai",
                rf + ".fai",
                "--igenomes_ignore",
                "--skip_tools",
                "baserecalibrator",
                "--tools",
                v["caller"],
                "--outdir",
                self.o("sarek"),
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
                "--thread",
                "2",
            )
        elif a == "variant_convert":
            mode, name = {
                "VCF.gz (BGZF)": ("z", "converted.vcf.gz"),
                "VCF": ("v", "converted.vcf"),
                "BCF": ("b", "converted.bcf"),
            }[v["output_format"]]
            cmd("bcftools", "view", "-O" + mode, "-o", self.o(name), self.p("vcf"))
            lines.append(
                "bcftools stats " + Q(self.o(name)) + " > conversion_stats.txt"
            )
        elif a == "filter":
            terms = []
            if v.get("pass_only") == "PASS only":
                terms.append('FILTER="PASS"')
            elif v.get("pass_only") != "All entries":
                terms.append('(FILTER="PASS" || FILTER=".")')
            for key in ["dp", "gq"]:
                n = int(v.get(key) or 0)
                if n < 0:
                    raise ValueError("Thresholds shall be at least 0.")
                if n:
                    terms.append("FMT/" + key.upper() + ">=" + str(n))
            cmd(
                "bcftools",
                "view",
                *(["-i", " && ".join(terms)] if terms else []),
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
                "-p",
                "4",
                *(["--sites", "hg38"] if v["build"] == "GRCh38" else []),
                "--prefix",
                self.o("familien_qc"),
                ready,
                self.p("ped"),
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
            panel = (
                ROOT
                / "References"
                / (
                    "1000G_GRCh38/all_hg38"
                    if v["panel"].startswith("1000")
                    else "HGDP_GRCh38/hgdp_statphase"
                )
            )
            if not Path(str(panel) + ".psam").is_file():
                raise ValueError(
                    "Reference panel is not installed: "
                    + panel.name
                    + ". The sample set does not include 1000 Genomes or HGDP."
                )
            cmd(
                "plink2",
                "--pfile",
                linux(panel),
                "vzs",
                "--chr",
                v["chrom"],
                "--snps-only",
                "just-acgt",
                "--max-alleles",
                "2",
                "--export",
                "vcf",
                "bgz",
                "--out",
                self.o("referenz_chr" + v["chrom"]),
            )
            cmd(
                "bcftools",
                "index",
                "-ft",
                self.o("referenz_chr" + v["chrom"] + ".vcf.gz"),
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
                "plink2 --pfile "
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
                "nthreads=4",
                *(["ref=" + self.p("refpanel")] if v.get("refpanel") else []),
            )
        elif a == "ibd":
            cmd(
                "hap-ibd",
                "gt=" + self.p("vcf"),
                "map=" + self.p("map"),
                "out=" + self.o("segmente"),
                "nthreads=4",
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
            )
        elif a == "mito":
            ready = prepared(self.p("vcf"), "mt_input")
            cmd(
                "haplogrep",
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
                "/opt/dna/cache/vep",
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
            py("check_build", self.p("vcf"), v["build"])
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
                "--make-pgen",
                "--out",
                self.o("zielgenotypen"),
            )
            py("score_sheet", self.o("zielgenotypen"), self.person, self.o())
            cmd(
                "pgsc-calc",
                "--input",
                self.o("samplesheet.csv"),
                "--scorefile",
                self.p("score"),
                "--target_build",
                v["build"],
                "--outdir",
                self.o("pgs"),
                "--max_cpus",
                "4",
                "--max_memory",
                "10.GB",
            )
        else:
            raise ValueError("Not yet an execution adapter for" + a)
        lines.append('printf "\\nDNA_LAUNCHER_STEP_SUCCESS\\n"')
        return "\n".join(lines) + "\n"

    def run_process(self, args, env=None):
        self.log("> " + subprocess.list2cmdline([str(x) for x in args]))
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
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
                if pidfile.exists():
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

    def windows(self):
        a = self.task["action"]
        v = self.v
        if a == "ugene":
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

    def launch(self):
        core = self.task["core"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
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
            for args in wsl_host_bootstrap(self.task["action"]):
                self.run_process(args)
            atomic(self.folder / "versionen.json", recorded_installation())
            if os.name == "nt":
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
                    ["setsid", "bash", str(self.folder / "ausfuehren.sh")],
                    env=env,
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
            request = Path(sys.argv[2])
            r = json.loads(request.read_text(encoding="utf-8-sig"))
            folder = request.parent
            status = json.loads((folder / "status.json").read_text(encoding="utf-8"))
            try:
                results = inspector.check_batch(
                    r["person"], r["files"], folder, lambda s: print(s, flush=True)
                )
                (folder / "Results").mkdir(exist_ok=True)
                shutil.copyfile(
                    folder / "inspection.json", folder / "Results/check-summary.json"
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
