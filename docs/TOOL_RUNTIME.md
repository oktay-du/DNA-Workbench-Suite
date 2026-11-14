# Tool runtime matrix

This inventory is derived from `catalog.json`, `workflows.RECIPES`,
`on_demand.TOOLS`, `on_demand.REQUIREMENTS` and the Kiri image constants.
The branch started at `origin/main` `177ed4dbd7b4cb720bc9a7452d0e7c3d2511aed8`, which is also the
`v1.0.7` tag. Support statements below record only runs checked for
this change or explicitly attributed to the v1.0.7 release notes.

## Evidence labels

| Label | Meaning |
|---|---|
| `executed` | A real process produced the expected files on that OS and CPU. |
| `emulated` | The target ELF ran under qemu-user after the architecture check. |
| `release-note` | v1.0.7 reports a Windows x64 synthetic run. This change did not repeat it. |
| `package` | CI builds or checks a launcher package, not the optional tool. |
| `route` | Install and start code exists. No execution is recorded here. |
| `not-used` | The current code does not select that route on that target. |

## Counts

- Catalog tasks: 80.
- Shared workflows: 9.
- Installable tools: 47.
- Workflow steps that are not catalog task ids: `parent_origin`.
- Installable tools with a checked AArch64 process run: 1 (`rfmix`).
- Installable tools still without an AArch64 process run: 46.
- Shared workflows with a complete ARM64 track run: 0.

The AArch64 RFMix process run is the Debian arm64 image on
`ubuntu-24.04-arm`, described below. The earlier qemu-user ELF run
remains recorded there as well.

## Shared workflows

Desktop and headless use `workflows.list`, `workflows.plan`,
`workflows.configure`, `workflows.start`, `workflows.status` and
`workflows.cancel`. A track runs its catalog tasks in order.

| Workflow | Steps |
|---|---|
| `variant_review` | `variant_evidence_audit`, `vcf_qc` |
| `sequence_research` | `sequence_stats`, `sequence_explore`, `seqviz_view` |
| `prepare` | `profile_analyze`, `profile_generate`, `profile_activate`, `vcf_qc` |
| `ancestry` | `profile_analyze`, `vcf_qc`, `mito`, `yhaplo`, `rfmix` |
| `health` | `profile_analyze`, `vcf_qc`, `opencravat_run`, `vep` |
| `medication` | `profile_analyze`, `vcf_qc`, `pharmcat` |
| `fitness` | `profile_analyze`, `vcf_qc`, `pgs` |
| `nutrition` | `profile_analyze`, `vcf_qc`, `pgs` |
| `family` | `profile_analyze`, `variant_index`, `parent_origin`, `roh`, `kinship` |

`parent_origin` is calculated inside the family track. It is not a
catalog task and has no separate installer.

## Catalog tasks

The required-tools column follows the non-Windows selection in
`on_demand.mapped`. On Windows, IGV also requires `java-windows`.

| Task | Platform | Kind | Required tools |
|---|---|---|---|
| `import` | Windows | analysis | — |
| `inventory` | Windows | analysis | — |
| `missing` | Windows | analysis | — |
| `identity` | WSL | analysis | `pysam` |
| `inspect` | WSL | analysis | `bcftools`, `samtools`, `snps` |
| `vcf_qc` | WSL | analysis | `bcftools` |
| `chip_vcf` | WSL | analysis | `snps`, `pysam`, `samtools` |
| `fastq_qc` | WSL | analysis | `fastp` |
| `bam_qc` | WSL | analysis | `samtools`, `mosdepth`, `multiqc` |
| `multiqc` | WSL | analysis | `multiqc` |
| `sarek` | WSL | analysis | `nextflow`, `sarek`, `docker`, `samtools` |
| `deepvariant` | WSL | analysis | `deepvariant`, `samtools`, `docker` |
| `normalize` | WSL | analysis | `bcftools`, `samtools` |
| `filter` | WSL | analysis | `bcftools` |
| `conflicts` | WSL | analysis | `pysam` |
| `merge` | WSL | analysis | `bcftools` |
| `roh` | WSL | analysis | `plink19` |
| `peddy` | WSL | analysis | `peddy`, `bcftools` |
| `whatshap` | WSL | analysis | `whatshap`, `samtools` |
| `truvari` | WSL | analysis | `truvari`, `bcftools`, `samtools` |
| `kinship` | WSL | analysis | `plink2` |
| `ref_export` | WSL | analysis | `plink2`, `bcftools` |
| `pca` | WSL | analysis | `plink2`, `plotly` |
| `beagle` | WSL | analysis | `beagle` |
| `ibd` | WSL | analysis | `hap-ibd` |
| `rfmix` | WSL | analysis | `rfmix` |
| `ancient` | WSL | launch | `admixtools` |
| `mito` | WSL | analysis | `haplogrep`, `bcftools` |
| `yhaplo` | WSL | analysis | `yhaplo`, `bcftools` |
| `opencravat_run` | WSL | analysis | `open-cravat`, `opencravat-models` |
| `vep` | WSL | analysis | `vep`, `vep-cache` |
| `pharmcat` | WSL | analysis | `pharmcat` |
| `pgs` | WSL | analysis | `nextflow`, `pgsc-calc`, `plink2`, `docker` |
| `report` | Windows | analysis | — |
| `export` | Windows | analysis | — |
| `versions` | Windows | launch | — |
| `gramps` | Windows / WSL | launch | `gramps` |
| `grampsweb` | Windows / WSL | launch | `docker` |
| `igv` | Windows / WSL | launch | `igv` |
| `jbrowse` | Windows / WSL | launch | `jbrowse` |
| `ocgui` | Windows / WSL | launch | `open-cravat` |
| `hapgui` | Windows / WSL | launch | `haplogrep` |
| `jupyter` | Windows / WSL | launch | `jupyter-windows` |
| `terminal` | Windows / WSL | launch | `linux-shell` |
| `wslstart` | Windows / WSL | launch | `linux-shell` |
| `wslstop` | Windows / WSL | launch | — |
| `backup` | Windows / WSL | launch | — |
| `powershell` | Windows / WSL | launch | — |
| `cmd` | Windows / WSL | launch | — |
| `explorer` | Windows / WSL | launch | — |
| `archive_index` | Windows | analysis | — |
| `variant_index` | Windows | analysis | — |
| `profile_view` | Windows | launch | — |
| `family` | Windows | launch | — |
| `visual` | Windows | launch | — |
| `profile_analyze` | Windows | analysis | `pyliftover` |
| `profile_generate` | Windows | analysis | — |
| `profile_activate` | Windows | analysis | — |
| `liftover_snps` | Windows | analysis | `pyliftover` |
| `profile_refresh` | Windows | analysis | `pyliftover` |
| `storybook` | Windows | analysis | `storybook-pdf` |
| `helix_export` | Windows | analysis | `helix-3d` |
| `avatar_pack` | Windows | analysis | — |
| `sequence_stats` | Windows | analysis | `biopython` |
| `fasta_collect` | Windows | analysis | — |
| `sequence_extract` | Windows | analysis | `pyfastx` |
| `sequence_transform` | Windows | analysis | `biopython`, `pyfastx` |
| `seqviz_view` | Windows | analysis | `pyfastx`, `seqviz` |
| `gatk_validate` | WSL | analysis | `gatk`, `samtools` |
| `ugene` | Windows | launch | `ugene` |
| `provider_export` | Windows | analysis | — |
| `fastq_report` | WSL | analysis | `fastp` |
| `variant_convert` | WSL | analysis | `bcftools` |
| `best_dataset` | Windows | analysis | `pyliftover` |
| `research_synthesis` | Windows | analysis | `storybook-pdf` |
| `variant_evidence_audit` | Windows | analysis | — |
| `sequence_explore` | Windows | analysis | `biopython`, `pyfastx` |
| `model_readiness` | Windows | analysis | `pyfastx` |
| `dna_message` | Windows | analysis | — |
| `agent_handoff` | Windows | analysis | — |

## Installable tools

Version and commit come from `install-lock.json` when the tool has a
pinned artifact. `master` in that file is the lock label, not the
program version printed by the binary. The recipe names the branch in
`on_demand.install`.

| Tool | Lock version | Commit | Recipe | Source |
|---|---|---|---|---|
| `admixtools` | v2.0.1 | `b9be65b5e621` | `manual` | https://github.com/uqrmaie1/admixtools |
| `bcftools` | 1.25 | `09795cc2d3f9` | `samtools` | https://github.com/samtools/bcftools |
| `beagle` | 5.5-27Feb25.75f | `` | `java` | https://faculty.washington.edu/browning/beagle/beagle.html |
| `biopython` | — | `—` | `windows-pip` | https://github.com/biopython/biopython |
| `deepvariant` | — | `—` | `manual` | https://github.com/google/deepvariant |
| `docker` | — | `—` | `docker` | https://github.com/moby/moby |
| `document-ocr` | — | `—` | `document-ocr` | https://github.com/tesseract-ocr/tesseract |
| `document-reader` | — | `—` | `windows-pip` | https://github.com/py-pdf/pypdf |
| `document-translation` | — | `—` | `document-translation` | https://github.com/argosopentech/argos-translate |
| `fastp` | — | `—` | `apt` | https://github.com/OpenGene/fastp |
| `gatk` | 4.7.0.0 | `` | `gatk` | https://github.com/broadinstitute/gatk |
| `gramps` | v6.0.8 | `` | `windows-manual` | https://github.com/gramps-project/gramps |
| `hap-ibd` | master | `a3fdd2d62949` | `hap-ibd` | https://github.com/browning-lab/hap-ibd |
| `haplogrep` | — | `` | `haplogrep` | https://github.com/genepi/haplogrep3 |
| `helix-3d` | — | `—` | `windows-pip` | https://github.com/elalish/manifold |
| `igv` | 2.19.8 | `` | `windows-zip` | https://github.com/igvteam/igv |
| `java-windows` | 21.0.13+9.0.LTS | `` | `windows-zip` | https://github.com/adoptium/temurin21-binaries |
| `jbrowse` | v4.3.0 | `` | `windows-manual` | https://github.com/GMOD/jbrowse-components |
| `jupyter-windows` | — | `—` | `windows-pip` | https://github.com/jupyterlab/jupyterlab |
| `linux-shell` | Ubuntu 24.04 LTS | `` | `manual` | https://github.com/microsoft/WSL |
| `mosdepth` | v0.3.15 | `` | `binary` | https://github.com/brentp/mosdepth |
| `multiqc` | — | `—` | `pip` | https://github.com/MultiQC/MultiQC |
| `nextflow` | 26.10.5 | `` | `nextflow` | https://github.com/nextflow-io/nextflow |
| `open-cravat` | 3.2.4 | `6a561c4c44ae` | `pip` | https://github.com/KarchinLab/open-cravat |
| `opencravat-models` | — | `—` | `opencravat-models` | https://github.com/KarchinLab/open-cravat |
| `peddy` | — | `—` | `isolated-pip` | https://github.com/brentp/peddy |
| `pgsc-calc` | v2.3.0 | `72ee54f2119d` | `nextflow-pipeline` | https://github.com/PGScatalog/pgsc_calc |
| `pharmcat` | v3.4.0 | `` | `java` | https://github.com/PharmGKB/PharmCAT |
| `plink19` | — | `—` | `apt` | https://www.cog-genomics.org/plink/1.9/ |
| `plink2` | b1.3-20261031 | `` | `plink` | https://www.cog-genomics.org/plink/2.0/ |
| `plotly` | — | `—` | `pip` | https://github.com/plotly/plotly.py |
| `pyfastx` | — | `—` | `windows-pip` | https://github.com/lmdu/pyfastx |
| `pyliftover` | — | `—` | `windows-pip` | https://github.com/konstantint/pyliftover |
| `pysam` | — | `—` | `pip` | https://github.com/pysam-developers/pysam |
| `rfmix` | master | `09599c19c69f` | `rfmix` | https://github.com/slowkoni/rfmix |
| `samtools` | 1.25 | `7162950d0988` | `samtools` | https://github.com/samtools/samtools |
| `sarek` | 3.11.0 | `6e9b164daa2a` | `nextflow-pipeline` | https://github.com/nf-core/sarek |
| `sequence-python` | — | `—` | `windows-pip` | https://github.com/biopython/biopython |
| `seqviz` | — | `—` | `visual-seqviz` | https://github.com/Lattice-Automation/seqviz |
| `snps` | — | `—` | `pip` | https://github.com/apriha/snps |
| `storybook-pdf` | — | `—` | `windows-pip` | https://www.reportlab.com/opensource/ |
| `truvari` | — | `—` | `isolated-pip` | https://github.com/ACEnglish/truvari |
| `ugene` | 53.1 | `` | `windows-ugene` | https://github.com/ugeneunipro/ugene |
| `vep` | release/116.3 | `f479099e2a9c` | `vep` | https://github.com/Ensembl/ensembl-vep |
| `vep-cache` | 116-GRCh38 | `` | `vep-cache` | https://www.ensembl.org/info/docs/tools/vep/script/vep_cache.html |
| `whatshap` | — | `—` | `isolated-pip` | https://github.com/whatshap/whatshap |
| `yhaplo` | 2.1.17 | `a705c35023d3` | `pip` | https://github.com/23andMe/yhaplo |

## Selected runtimes

These rows are the external tools called out for ARM64 follow-up.
Other tools stay at `route` until a run is recorded.

| Tool | windows-x64 | windows-arm64 | linux-x64 | linux-arm64 | macos-x64 | macos-arm64 |
|---|---|---|---|---|---|---|
| `rfmix` | release-note | route | executed | executed | route | route |
| `vep` | release-note | route | route | route | route | route |
| `vep-cache` | release-note | route | route | route | route | route |
| `open-cravat` | release-note | route | route | route | route | route |
| `opencravat-models` | release-note | route | route | route | route | route |
| `pgsc-calc` | release-note | route | route | route | route | route |
| `sarek` | release-note | route | route | route | route | route |
| `deepvariant` | release-note | not-used | release-note | not-used | route | route |
| `nextflow` | release-note | route | route | route | route | route |
| `pharmcat` | release-note | route | route | route | route | route |
| `gatk` | release-note | route | route | route | route | route |

Kiri image tags and digests live in `system_tools`. RFMix uses
`dna-workbench/rfmix:1`. VEP uses the pinned index
`docker.io/ensemblorg/ensembl-vep@sha256:6972667883d89b9fa55e5cbe94f1b4c259ebc6bbd178310cef78f617e055eb75` and separate amd64 and arm64 config
digests in `KIRI_VEP_IMAGE_IDS`. DeepVariant's pinned CPU and GPU images
are Linux x64. `kiri_sequence_tool` returns no DeepVariant or Nextflow
image when the engine is ARM64, except the macOS DeepVariant route after
a successful offline x64 TensorFlow probe. That probe was not run here.

### RFMix

- Program version from the pinned source `AC_INIT`: `v2.03-r0`.
- Commit `09599c19c69f81571c7a7aab4cd2d847a9e0633a`.
- Archive SHA-256 `1ca6db8b3e7abb64c7b0e3af44ade69244cf813468c24d687ea26f88a70a4f17`.
- Source: https://github.com/slowkoni/rfmix
- License gate: `acknowledge_rfmix()` writes `DNA_Software/UserData/Launcher/Needed/rfmix-license-reviewed.json` before `fetch`. The notice is `DNA_Software/Launcher/Notices/RFMIX-LICENSE.txt`. Checking the box does not grant a license.
- Kiri install: `install_kiri_rfmix` copies the verified archive, the notice and `DNA_Software/Start/rfmix-march.sh` into the build context, then `install_kiri_image` builds `kiri-rfmix.Dockerfile`. When that builder rejects the docker exporter, the same recipe is built with `docker build -t`, which loads the tag into the engine.
- Image contents: `/usr/local/bin/rfmix` and Debian `bcftools=1.21-1`. The final stage also installs `libstdc++6`, `libgomp1` and `zlib1g`.
- WSL install: `/opt/dna/tools/rfmix-<first 12 hex of the commit>/bin/rfmix` linked from `/opt/dna/bin/rfmix`. The same march script runs there.
- Start: with a matching Kiri image, `Job.run_with_kiri` sorts and indexes both VCFs with BCFtools, then runs `rfmix -f -r -m -g --chromosome --n-threads -o`. Thread count is `hardware.cpu_threads()`: at least 1, at most 8, and one below the visible CPU count when more than one CPU is visible. RFMix has no CUDA, HIP, Vulkan, SYCL or Metal switch. The job checks that `lokale_ancestry.msp.tsv`, `lokale_ancestry.fb.tsv` and `lokale_ancestry.rfmix.Q` are non-empty.
- Prerequisite inputs: phased query VCF, phased reference VCF, reference sample map, genetic map, chromosome 1–22.
- Compiler: upstream `Makefile.am` adds `-march=core2`. AArch64 GCC 13 rejects `core2`. `rfmix-march.sh` keeps that flag on amd64 and x86_64. On arm64 and aarch64 it deletes the flag and leaves the compiler default. On Debian arm64 that default is armv8-a. The script does not add SVE or other optional extensions. Any other architecture stops the build.

Checked AArch64 process, on an x86_64 Ubuntu host because this machine
has no ARM64 CPU and no container engine:

- Host: Linux x86_64, Python 3.12.3, `qemu-aarch64-static`, `aarch64-linux-gnu-g++` 13.3.0.
- The march script was run with `dpkg --print-architecture` reporting `arm64`, then the pinned archive was configured with `--host=aarch64-linux-gnu`.
- `file` reported an ELF 64-bit AArch64 executable. `readelf -h` reported machine AArch64 and flags `0x0`.
- `qemu-aarch64-static -L /usr/aarch64-linux-gnu` printed `RFMIX v2.03-r0`.
- Synthetic input: chromosome 22, 80 phased SNPs, reference samples A1–A4 and B1–B4, query `Q1`, populations PopA and PopB. `--n-threads=1`.
- `lokale_ancestry.rfmix.Q` contained `Q1` with PopA `0.50000` and PopB `0.50000`. The MSP and FB files named both populations and chromosome 22.
- The same fixture on the unpatched x64 build also produced `0.50000` and `0.50000`. Window boundaries differed, so the check is the global proportion and the required files, not identical window edges.
- BCFtools 1.19 on that host sorted and indexed the same VCFs; the x64 binary accepted the compressed files. The image pins BCFtools 1.21.

Debian arm64 image was executed on GitHub `ubuntu-24.04-arm`
(14 November 2026, 00:45 Europe/Berlin, commit `7b1b054`).
Host machine `aarch64`, Python 3.12.16, Docker Engine 28.0.4.
`install("rfmix")` after license acknowledgement built
`dna-workbench/rfmix:1`. The image installed Debian `bcftools` 1.21-1
for arm64. The engine command used `--platform=linux/arm64` and
`--n-threads=3`. The log contains `RFMIX v2.03-r0`. The synthetic
chromosome wrote `Q1` with PopA 0.5 and PopB 0.5.

Debian amd64 image was executed on GitHub `ubuntu-24.04`
(14 November 2026, 00:49 Europe/Berlin, commit `0de8548`).
Host machine `x86_64`. The recorded platform was `linux/amd64`.
The log contains `RFMIX v2.03-r0`. The synthetic chromosome wrote `Q1`
with PopA 0.5 and PopB 0.5. Eleven tests passed.

The architecture script and command checks passed on that same commit
for Windows x64, Windows ARM64, macOS x64 and macOS ARM64. Those jobs
do not build the image. Windows and macOS Kiri use the Linux images
above. macOS runners have no Docker engine, and Apple Silicon runners
do not support the nested virtualization a Linux VM needs. Windows
runners ship a Windows container engine, not the Kiri Linux pipe.

### VEP

- Program version pin: Ensembl VEP `release/116.3`, commit `f479099e2a9c`.
- Image index: `docker.io/ensemblorg/ensembl-vep@sha256:6972667883d89b9fa55e5cbe94f1b4c259ebc6bbd178310cef78f617e055eb75`.
- Config digest amd64: `sha256:8883fa3fe22513f53a6209d037c426916aaf15fd2541f695a63c41c03940dec5`.
- Config digest arm64: `sha256:faa2f666c401a70c7922bd9bf5f53c81570183e57b24aac2f5bd27211403eca8`.
- `prepare_vep_image` pulls that index into the local Kiri engine. `install("vep")` then installs the cache.
- Cache pin: `homo_sapiens_vep_116_GRCh38.tar.gz`, 27644657162 bytes, SHA-256 `014c7dd9bb5ad06665866d62eb80f31ca761197bcb9b59280300676f996e600d`.
- Start with a cache: `vep --offline --cache --dir_cache /cache --cache_version 116 --assembly GRCh38`, network disabled, cache and VCF read-only, output `vep_annotation.vcf`.

The image start is `VEP image start` on `ubuntu-24.04` and
`ubuntu-24.04-arm`. It pulls the pinned index, checks the config digest
for the engine architecture, and runs `vep --help`. That job is not
recorded as passed here. It does not download the cache and does not
write `vep_annotation.vcf`. Windows and macOS runners cannot start this
Linux image; they run the pull and command checks only.

### Next gap

The VEP GRCh38 cache annotation is the remaining VEP gap. The cache
archive is 27644657162 bytes, so it is not part of this image start.
After a recorded annotation: OpenCRAVAT module install, PGS on the
ARM64 profile, Sarek on the x64 emulation profile, then DeepVariant.
DeepVariant stays off Kiri for Windows ARM64 and Linux ARM64. Its
Apple Silicon path still depends on a successful Rosetta probe, which
was not run.

Package builds remain separate from these tool runs. Existing CI builds
Windows x64, Windows ARM64, Linux x64, Linux ARM64, macOS x64 and macOS
ARM64 launcher packages. Those jobs do not execute RFMix, VEP,
OpenCRAVAT, PGS, Sarek or DeepVariant.

