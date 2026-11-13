"""Catalog, workflow and tool inventory used by docs/TOOL_RUNTIME.md."""

from pathlib import Path
import json

import on_demand
import system_tools
import workflows

BASE_SHA = "177ed4dbd7b4cb720bc9a7452d0e7c3d2511aed8"
# Checked AArch64 process evidence in this change. Not a native-hardware claim.
AARCH64_PROCESS = {"rfmix"}
TARGETS = (
    "windows-x64",
    "windows-arm64",
    "linux-x64",
    "linux-arm64",
    "macos-x64",
    "macos-arm64",
)


def catalog():
    return json.loads(
        Path(__file__).with_name("catalog.json").read_text(encoding="utf-8")
    )["tasks"]


def task_tools(task):
    action = task.get("action", "")
    if action in on_demand.REQUIREMENTS:
        return list(on_demand.REQUIREMENTS[action])
    try:
        return list(on_demand.mapped(task["id"]))
    except ValueError:
        return []


def pin(tool):
    artifact = on_demand.TOOLS[tool][1]
    if not artifact:
        return None
    return next(item for item in on_demand.LOCK["items"] if item["id"] == artifact)


def open_linux_arm64_tools():
    return sorted(set(on_demand.TOOLS) - AARCH64_PROCESS)


def _cell(text):
    return str(text).replace("|", "/")


def render():
    tasks = catalog()
    task_ids = {task["id"] for task in tasks}
    lines = [
        "# Tool runtime matrix",
        "",
        "This inventory is derived from `catalog.json`, `workflows.RECIPES`,",
        "`on_demand.TOOLS`, `on_demand.REQUIREMENTS` and the Kiri image constants.",
        f"The branch started at `origin/main` `{BASE_SHA}`, which is also the",
        "`v1.0.7` tag. Support statements below record only runs checked for",
        "this change or explicitly attributed to the v1.0.7 release notes.",
        "",
        "## Evidence labels",
        "",
        "| Label | Meaning |",
        "|---|---|",
        "| `executed` | A real process produced the expected files on that OS and CPU. |",
        "| `emulated` | The target ELF ran under qemu-user after the architecture check. |",
        "| `release-note` | v1.0.7 reports a Windows x64 synthetic run. This change did not repeat it. |",
        "| `package` | CI builds or checks a launcher package, not the optional tool. |",
        "| `route` | Install and start code exists. No execution is recorded here. |",
        "| `not-used` | The current code does not select that route on that target. |",
        "",
        "## Counts",
        "",
        f"- Catalog tasks: {len(tasks)}.",
        f"- Shared workflows: {len(workflows.RECIPES)}.",
        f"- Installable tools: {len(on_demand.TOOLS)}.",
        "- Workflow steps that are not catalog task ids: `parent_origin`.",
        f"- Installable tools with a checked AArch64 process run: {len(AARCH64_PROCESS)} (`rfmix`).",
        f"- Installable tools still without an AArch64 process run: {len(open_linux_arm64_tools())}.",
        "- Shared workflows with a complete ARM64 track run: 0.",
        "",
        "The AArch64 RFMix evidence is an emulated ELF run, described below.",
        "It is not a native ARM64 machine and not yet the Debian image.",
        "The image run is the `RFMix synthetic run on Linux ARM64` GitHub Actions job.",
        "That job is not described as passed here.",
        "",
        "## Shared workflows",
        "",
        "Desktop and headless use `workflows.list`, `workflows.plan`,",
        "`workflows.configure`, `workflows.start`, `workflows.status` and",
        "`workflows.cancel`. A track runs its catalog tasks in order.",
        "",
        "| Workflow | Steps |",
        "|---|---|",
    ]
    for name in workflows.RECIPES:
        steps = ", ".join(f"`{step}`" for step in workflows.RECIPES[name][3])
        lines.append(f"| `{name}` | {steps} |")
    lines += [
        "",
        "`parent_origin` is calculated inside the family track. It is not a",
        "catalog task and has no separate installer.",
        "",
        "## Catalog tasks",
        "",
        "| Task | Platform | Kind | Required tools |",
        "|---|---|---|---|",
    ]
    for task in tasks:
        tools = ", ".join(f"`{tool}`" for tool in task_tools(task)) or "—"
        lines.append(
            f"| `{task['id']}` | {_cell(task.get('platform', ''))} | "
            f"{_cell(task.get('kind', ''))} | {tools} |"
        )
    lines += [
        "",
        "## Installable tools",
        "",
        "Version and commit come from `install-lock.json` when the tool has a",
        "pinned artifact. `master` in that file is the lock label, not the",
        "program version printed by the binary. The recipe names the branch in",
        "`on_demand.install`.",
        "",
        "| Tool | Lock version | Commit | Recipe | Source |",
        "|---|---|---|---|---|",
    ]
    for tool in sorted(on_demand.TOOLS):
        source, _artifact, recipe = on_demand.TOOLS[tool]
        item = pin(tool)
        version = item.get("version", "—") if item else "—"
        commit = item.get("commit", "")[:12] if item else "—"
        lines.append(
            f"| `{tool}` | {_cell(version)} | `{commit}` | `{recipe}` | {source} |"
        )
    lines += [
        "",
        "## Selected runtimes",
        "",
        "These rows are the external tools called out for ARM64 follow-up.",
        "Other tools stay at `route` until a run is recorded.",
        "",
        "| Tool | windows-x64 | windows-arm64 | linux-x64 | linux-arm64 | macos-x64 | macos-arm64 |",
        "|---|---|---|---|---|---|---|",
        "| `rfmix` | release-note | route | route | emulated | route | route |",
        "| `vep` | release-note | route | route | route | route | route |",
        "| `vep-cache` | release-note | route | route | route | route | route |",
        "| `open-cravat` | release-note | route | route | route | route | route |",
        "| `opencravat-models` | release-note | route | route | route | route | route |",
        "| `pgsc-calc` | release-note | route | route | route | route | route |",
        "| `sarek` | release-note | route | route | route | route | route |",
        "| `deepvariant` | release-note | not-used | release-note | not-used | route | route |",
        "| `nextflow` | release-note | route | route | route | route | route |",
        "| `pharmcat` | release-note | route | route | route | route | route |",
        "| `gatk` | release-note | route | route | route | route | route |",
        "",
        "Kiri image tags and digests live in `system_tools`. RFMix uses",
        f"`{system_tools.KIRI_RFMIX_IMAGE}`. VEP uses the pinned index",
        f"`{system_tools.KIRI_VEP_IMAGE}` and separate amd64 and arm64 config",
        "digests in `KIRI_VEP_IMAGE_IDS`. DeepVariant's pinned CPU and GPU images",
        "are Linux x64. `kiri_sequence_tool` returns no DeepVariant or Nextflow",
        "image when the engine is ARM64, except the macOS DeepVariant route after",
        "a successful offline x64 TensorFlow probe. That probe was not run here.",
        "",
        "### RFMix",
        "",
        "- Program version from the pinned source `AC_INIT`: `v2.03-r0`.",
        "- Commit `09599c19c69f81571c7a7aab4cd2d847a9e0633a`.",
        "- Archive SHA-256 `1ca6db8b3e7abb64c7b0e3af44ade69244cf813468c24d687ea26f88a70a4f17`.",
        "- Source: https://github.com/slowkoni/rfmix",
        "- License gate: `acknowledge_rfmix()` writes `DNA_Software/UserData/Launcher/Needed/rfmix-license-reviewed.json` before `fetch`. The notice is `DNA_Software/Launcher/Notices/RFMIX-LICENSE.txt`. Checking the box does not grant a license.",
        "- Kiri install: `install_kiri_rfmix` copies the verified archive, the notice and `DNA_Software/Start/rfmix-march.sh` into the build context, then `install_kiri_image` builds `kiri-rfmix.Dockerfile`.",
        "- Image contents: `/usr/local/bin/rfmix` and Debian `bcftools=1.21-1`. The final stage also installs `libstdc++6`, `libgomp1` and `zlib1g`.",
        "- WSL install: `/opt/dna/tools/rfmix-<first 12 hex of the commit>/bin/rfmix` linked from `/opt/dna/bin/rfmix`. The same march script runs there.",
        "- Start: with a matching Kiri image, `Job.run_with_kiri` sorts and indexes both VCFs with BCFtools, then runs `rfmix -f -r -m -g --chromosome --n-threads -o`. Thread count is `hardware.cpu_threads()`: at least 1, at most 8, and one below the visible CPU count when more than one CPU is visible. RFMix has no CUDA, HIP, Vulkan, SYCL or Metal switch. The job checks that `lokale_ancestry.msp.tsv`, `lokale_ancestry.fb.tsv` and `lokale_ancestry.rfmix.Q` are non-empty.",
        "- Prerequisite inputs: phased query VCF, phased reference VCF, reference sample map, genetic map, chromosome 1–22.",
        "- Compiler: upstream `Makefile.am` adds `-march=core2`. AArch64 GCC 13 rejects `core2`. `rfmix-march.sh` keeps that flag on amd64 and x86_64. On arm64 and aarch64 it deletes the flag and leaves the compiler default. On Debian arm64 that default is armv8-a. The script does not add SVE or other optional extensions. Any other architecture stops the build.",
        "",
        "Checked AArch64 process, on an x86_64 Ubuntu host because this machine",
        "has no ARM64 CPU and no container engine:",
        "",
        "- Host: Linux x86_64, Python 3.12.3, `qemu-aarch64-static`, `aarch64-linux-gnu-g++` 13.3.0.",
        "- The march script was run with `dpkg --print-architecture` reporting `arm64`, then the pinned archive was configured with `--host=aarch64-linux-gnu`.",
        "- `file` reported an ELF 64-bit AArch64 executable. `readelf -h` reported machine AArch64 and flags `0x0`.",
        "- `qemu-aarch64-static -L /usr/aarch64-linux-gnu` printed `RFMIX v2.03-r0`.",
        "- Synthetic input: chromosome 22, 80 phased SNPs, reference samples A1–A4 and B1–B4, query `Q1`, populations PopA and PopB. `--n-threads=1`.",
        "- `lokale_ancestry.rfmix.Q` contained `Q1` with PopA `0.50000` and PopB `0.50000`. The MSP and FB files named both populations and chromosome 22.",
        "- The same fixture on the unpatched x64 build also produced `0.50000` and `0.50000`. Window boundaries differed, so the check is the global proportion and the required files, not identical window edges.",
        "- BCFtools 1.19 on that host sorted and indexed the same VCFs; the x64 binary accepted the compressed files. The image pins BCFtools 1.21.",
        "",
        "Native Linux ARM64 container execution, license acknowledgement through",
        '`install("rfmix")`, and the engine\'s Kiri command are what',
        "`DNA_RFMIX_SMOKE=1` runs on `ubuntu-24.04-arm`. Until that job is green,",
        "do not describe the Debian image as executed on ARM64 hardware.",
        "Apple Silicon uses the same ARM64 image recipe inside Kiri and was not run.",
        "Windows ARM64 WSL uses the same script and was not run.",
        "",
        "### Next gap",
        "",
        "VEP is the next route that already has an arm64 image digest and a",
        "resumable SHA-256 cache installer, and has no ARM64 run. After that:",
        "OpenCRAVAT module install, PGS on the ARM64 profile, Sarek on the x64",
        "emulation profile, then DeepVariant. DeepVariant stays off Kiri for",
        "Windows ARM64 and Linux ARM64. Its Apple Silicon path still depends on",
        "a successful Rosetta probe, which was not run.",
        "",
        "Package builds remain separate from these tool runs. Existing CI builds",
        "Windows x64, Windows ARM64, Linux x64, Linux ARM64, macOS x64 and macOS",
        "ARM64 launcher packages. Those jobs do not execute RFMix, VEP,",
        "OpenCRAVAT, PGS, Sarek or DeepVariant.",
        "",
    ]
    missing = [
        step
        for recipe in workflows.RECIPES.values()
        for step in recipe[3]
        if step not in task_ids and step != "parent_origin"
    ]
    if missing:
        raise ValueError(
            "Workflow steps missing from the catalog: " + ", ".join(missing)
        )
    return "\n".join(lines) + "\n"
