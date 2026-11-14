# Shared workflows and autofill

Choose Workflows in the sidebar, keep the active profile selected, plan a track and click Run available steps. Tracks cover file preparation, ancestry/lineages, health annotation, medication, fitness, nutrition and family transmission. The diagram shows each task, reused outputs, missing input and a persisted execution log. Percentage is completed steps divided by total, not an ETA.

Completed exact-selection results are reused across tracks and individual tool windows, using existing source/reference/parameter/output-state checks. A changed source is not silently accepted as the old result. Workflow configuration remembers valid reference/score/panel inputs with its originating tool/run and date. Missing paths are not autofilled. Current compatible biological-source ranking takes precedence over old sources. Fitness and nutrition score choices are scoped separately; no universal validated nutrition/fitness score is invented.

Use Inputs / open tool, fill the remaining fields, then Use for workflow. This saves configuration without executing a tool. Starting a track is explicit; imports never start it. Missing tools/services expose the existing dependency setup action, rather than automatically starting large downloads. Missing reference panels remain open. Without the GRCh38 chain/FASTA, the initial unconfigured comparison keeps builds separate; it does not claim a conversion occurred. Configure GRCh38 explicitly when those references exist.

The runner processes steps sequentially and prevents an unrelated suite task from starting concurrently. Profile switches leave runs active and visible in Jobs; the workflow page reloads persisted state. Closing the hosting process interrupts a track; reopening records this and requires an explicit new start, reusing completed child tasks. Cancellation is requested through the active child process. Blocked/failed steps do not receive a completion check.

Family links remain in the graph database. The family track can index compatible child variants and calculate a bounded trio subset from already indexed, measured child/mother/father sources. Parental profiles must have suitable indexed calls; the current implementation does not silently index all relatives. Only PASS autosomal SNPs with DP ≥10 and GQ ≥20 are considered, up to 200,001 indexed records per participant. Discordant source calls are excluded. A maternal/paternal allele pair is saved only if the measured trio permits exactly one pair. Ambiguous and incompatible sites are counted separately. This is not genome-wide phasing, IBD inference or clinical verification. mtDNA/Y/X lineage rules are explanatory expectations, never copied into the child's measured dataset. A father normally contributes Y to a son, not to a daughter; mtDNA is normally maternal for both. Source changes make saved evidence non-current.

All track operations have typed GUI/CLI/MCP commands: workflows.list, workflows.plan, workflows.configure, workflows.start, workflows.status, workflows.cancel and inheritance.read. Output summaries and supported no-report tools are registered in the same per-profile database/file manager.

## Optional local Kiri route for file checks and conversion

The suite can use Kiri when the regular tool route is unavailable. This covers VCF/BCF conversion, quality statistics, filtering, reference-based normalization and multi-sample VCF merging, as well as VCF/BCF and BAM/CRAM inspection and FASTQ quality reports and filtering. A merge checks each input's detected build and writes a sample-name mapping for each source. Set up [Kiri](https://docs.runkiri.com/install/) locally. From the project root, prepare the CPU image once on that computer:

```sh
docker --context kiri build -t dna-workbench/sequence-tools:1 - < DNA_Software/Start/kiri-sequence-tools.Dockerfile
```

In Windows PowerShell, pipe the recipe to Docker:

```powershell
Get-Content -Raw DNA_Software/Start/kiri-sequence-tools.Dockerfile | docker --context kiri build -t dna-workbench/sequence-tools:1 -
```

This packages the prebuilt Debian binaries for Kiri's native CPU architecture. The command sends only the Dockerfile, with no directory as build context. Keep this tag for the suite recipe. Build again when changing the recipe or when the image is removed. The previous local BCFtools-only image remains usable for operations that only require BCFtools. Normalization also needs SAMtools to create the reference index.

On x64, the existing pinned BCFtools 1.25 image is also supported and takes priority if cached:

```sh
docker --context kiri pull --platform linux/amd64 quay.io/biocontainers/bcftools@sha256:8c35865074cbcbeb59217e9cf1f7819ccc12301811bf0c086d57b364f3fa175b
```

The suite checks its local Kiri endpoint for an image matching the engine's architecture. The locally built ARM64 image runs on Windows ARM64, Linux ARM64 and Apple Silicon without x64 emulation. Jobs run with networking disabled, read-only mounts for the selected files, and a separate output folder. Windows uses Kiri's WSL2 engine.

For the complete BAM/CRAM quality report and standalone MultiQC report aggregation, prepare the separate image with SAMtools, mosdepth and MultiQC:

```sh
docker --context kiri build -t dna-workbench/alignment-qc:1 - < DNA_Software/Start/kiri-alignment-qc.Dockerfile
```

```powershell
Get-Content -Raw DNA_Software/Start/kiri-alignment-qc.Dockerfile | docker --context kiri build -t dna-workbench/alignment-qc:1 -
```

CRAM requires the exact matching reference FASTA. The job creates the alignment and reference indices in its own work folder and keeps the SAMtools statistics, mosdepth summaries and MultiQC report with the results.

For runs of homozygosity (PLINK 1.9), KING kinship tables (PLINK 2) and indexed GRCh38 reference-panel export (PLINK 2 and BCFtools), prepare the PLINK image once:

```sh
docker --context kiri build -t dna-workbench/plink:2 - < DNA_Software/Start/kiri-plink.Dockerfile
```

```powershell
Get-Content -Raw DNA_Software/Start/kiri-plink.Dockerfile | docker --context kiri build -t dna-workbench/plink:2 -
```

Reference-panel export requires the installed panel's `.pgen`, `.pvar.zst` and `.psam` files. It mounts those files individually and writes a chromosome VCF with its Tabix index. The previous `dna-workbench/plink:1` image remains usable for ROH and KING.

For PCA and its offline interactive chart, prepare the PLINK 2 and Plotly image:

```sh
docker --context kiri build -t dna-workbench/pca:1 - < DNA_Software/Start/kiri-pca.Dockerfile
```

```powershell
Get-Content -Raw DNA_Software/Start/kiri-pca.Dockerfile | docker --context kiri build -t dna-workbench/pca:1 -
```

PCA accepts a VCF or a PGEN cohort with matching PSAM and PVAR files. The selected cohort, sidecars and optional population labels are mounted individually and read-only. The HTML includes Plotly for offline viewing.

For Beagle 5.5 phasing, prepare the Java image:

```sh
docker --context kiri build -t dna-workbench/beagle:1 - < DNA_Software/Start/kiri-beagle.Dockerfile
```

```powershell
Get-Content -Raw DNA_Software/Start/kiri-beagle.Dockerfile | docker --context kiri build -t dna-workbench/beagle:1 -
```

The image build verifies the downloaded Beagle JAR against the suite's pinned checksum. The job receives the selected VCF, map and optional reference panel as read-only files and preserves the existing `impute=false` setting.

For hap-ibd segment analysis, prepare its Java image once:

```sh
docker --context kiri build -t dna-workbench/hap-ibd:1 - < DNA_Software/Start/kiri-hap-ibd.Dockerfile
```

```powershell
Get-Content -Raw DNA_Software/Start/kiri-hap-ibd.Dockerfile | docker --context kiri build -t dna-workbench/hap-ibd:1 -
```

The build verifies the pinned source archive and compiles the JAR. The job reads the phased VCF and genetic map and writes the compressed IBD and HBD results and the tool log. An empty segment list is a valid result.

For pedigree quality checks with peddy, build the image with the suite's Python dependency list. From the project root:

```sh
docker --context kiri build -t dna-workbench/peddy:1 -f DNA_Software/Start/kiri-peddy.Dockerfile DNA_Software/Launcher/Locks
```

The build context is the dependency-lock directory. The job mounts the chosen VCF and pedigree as read-only files, checks the detected genome build, and uses peddy's GRCh38 sites when selected. Optional reports such as the sex-check CSV depend on the input.

For WhatsHap read-backed phasing, prepare the image once:

```sh
docker --context kiri build -t dna-workbench/whatshap:1 -f DNA_Software/Start/kiri-whatshap.Dockerfile DNA_Software/Launcher/Locks
```

The build verifies the pinned WhatsHap wheel or source archive. On ARM64 it compiles the wheel once. The job mounts the VCF, alignment and exact reference read-only, creates temporary alignment and reference indices, and saves the phased VCF and statistics.

Prepare the following images for structural-variant comparison, mitochondrial haplogroup classification, and Y-chromosome haplogroup classification. Run the commands from the project root in Bash or PowerShell:

```sh
docker --context kiri build -t dna-workbench/truvari:1 -f DNA_Software/Start/kiri-truvari.Dockerfile DNA_Software/Launcher/Locks
docker --context kiri build -t dna-workbench/haplogrep:1 -f DNA_Software/Start/kiri-haplogrep.Dockerfile DNA_Software/Launcher/Locks
docker --context kiri build -t dna-workbench/yhaplo:1 -f DNA_Software/Start/kiri-yhaplo.Dockerfile DNA_Software/Launcher/Locks
```

Truvari verifies the detected build of both VCFs and creates its reference index in the job folder. HaploGrep uses the bundled, checksum-verified Phylotree Forensic Update 1.3 tree. Yhaplo retains the GRCh37 requirement and uses the pinned source archive. All three jobs run without network access.

PharmCAT reports, GATK variant validation and single-sample VCF comparison use the following images:

```sh
docker --context kiri build -t dna-workbench/pharmcat:1 -f DNA_Software/Start/kiri-pharmcat.Dockerfile DNA_Software/Launcher/Locks
docker --context kiri build -t dna-workbench/gatk:1 -f DNA_Software/Start/kiri-gatk.Dockerfile DNA_Software/Launcher/Locks
docker --context kiri build -t dna-workbench/variants:2 -f DNA_Software/Start/kiri-variants.Dockerfile DNA_Software/Launcher/Locks
```

PharmCAT checks for GRCh38 and writes the report to the job folder. GATK prepares the reference dictionary and index locally. VCF comparison runs the suite's existing comparison helper and requires matching builds. The variants image also supports chip inspection and measured chip-to-VCF export with the suite's existing `snps` parser and a temporary cache.

Ensembl VEP can run offline using its official 116.1 image for x64 and ARM64. Pull the pinned image into Kiri:

```sh
docker --context kiri pull docker.io/ensemblorg/ensembl-vep@sha256:6972667883d89b9fa55e5cbe94f1b4c259ebc6bbd178310cef78f617e055eb75
```

If Kiri's registry access fails, use a trusted registry client on the same computer to save this pinned image as a Docker archive. Select `linux/amd64` or `linux/arm64` to match the Kiri engine, then run `docker --context kiri load -i vep.tar`. The suite also recognizes the pinned image ID after an archive import.

Install **Ensembl VEP 116 human GRCh38 cache** from Guided optional imports or install VEP from the tool library with Kiri running. The installer resumes partial downloads, checks the pinned SHA-256, and extracts the cache to `References/VEP/homo_sapiens/116_GRCh38`. The job mounts the cache and selected VCF read-only and writes `vep_annotation.vcf` with networking disabled.

Install OpenCRAVAT or its annotation modules through the tool library with Kiri running. To build the OpenCRAVAT 3.2.4 image manually:

```sh
docker --context kiri build -t dna-workbench/opencravat:1 -f DNA_Software/Start/kiri-opencravat.Dockerfile DNA_Software/Launcher/Locks
```

Place the trusted OpenCRAVAT modules directory under `References/OpenCRAVAT/modules`, with the hg38 mapper and its data, the VCF converter, the text and Excel reporters, ClinVar, gnomAD4, and the standard postaggregators `tagsampler`, `casecontrol`, `varmeta` and `vcfinfo`. gnomAD4 needs the chromosome files and their Tabix or CSI indices for chromosomes 1–22 and X. The job mounts that module tree and the selected VCF read-only and runs without network access.

DeepVariant has a Kiri CPU route on x64 Windows, Linux and macOS. Load the official CPU image:

```sh
docker --context kiri pull docker.io/google/deepvariant@sha256:962e5a83b1d76aae6990625d47102785f791603f2138aa1fa9aa4fb6a2eecbe6
```

The official 1.10.0 CPU and GPU images are Linux x64. On Apple Silicon, install Rosetta for Linux containers and add `--platform linux/amd64` to the pull command. DNA Workbench selects that image only if a short, offline TensorFlow CPU test succeeds inside Kiri. This is an emulated CPU route. Windows and Linux ARM64 do not use this image via Kiri.

The GPU route uses a GPU-capable Docker engine and the NVIDIA runtime. On Windows x64, the app can use Docker Desktop's Linux engine directly while Kiri remains the default Docker context. Load the pinned GPU image with `docker --context desktop-linux pull docker.io/google/deepvariant@sha256:78fb1bb960f3b74a4308b62ba8b6232723d4c75e16a4a50f0d810d7086467dd1`. The app runs a small TensorFlow operation on the GPU before selecting the image. Kiri uses CPU execution.

The tool library can build and install RFMix in local Kiri after the license acknowledgement. For a manual build, place the verified source archive identified by `slowkoni-rfmix` in a dedicated build folder as `rfmix.tar.gz`. Copy `DNA_Software/Launcher/Notices/RFMIX-LICENSE.txt` and `DNA_Software/Start/rfmix-march.sh` into that folder. The script keeps the upstream `-march=core2` flag on x64. On ARM64 it removes that flag, because AArch64 GCC rejects it, and compiles with the image compiler's default instruction set. Recorded runtimes are in [Tool runtime matrix](TOOL_RUNTIME.md). From the project root:

```sh
docker --context kiri build -t dna-workbench/rfmix:1 -f DNA_Software/Start/kiri-rfmix.Dockerfile <build-folder>
```

Sarek and PGS Catalog Calculator use host Nextflow on macOS and Linux. Install Nextflow and the pinned pipeline through the tool library, and have Java 17–26 and a running local Docker-compatible engine available. Sarek also needs SAMtools, and PGS Catalog Calculator needs PLINK 2. Jobs use a per-job Nextflow work directory. On Apple Silicon the app requests the upstream Sarek x64 emulation profile and the PGS ARM64 profile. Sarek needs an engine with x64 emulation enabled.

Windows uses the suite's WSL route when it is ready. On Windows x64, Kiri can run the pipeline when that route is unavailable. Prepare the pinned Nextflow image and the suite's sequence-tools image for Sarek or PLINK 2 image for PGS. Then install the pipeline from the tool library to stage its verified source and the Nextflow distribution:

```sh
docker --context kiri pull docker.io/nextflow/nextflow@sha256:0fb911ca7a96ca9632f8b4387affbc8f402b0fd06d4d2e41993563173c724d0e
```

Nextflow uses Kiri's local engine socket to start pipeline task containers. It may download plugins and pull the images needed for individual tasks. In an environment with an approved local TLS inspection CA, place its PEM certificate at `DNA_Software/UserData/Launcher/Nextflow/local-ca.pem` to let the Nextflow runner verify HTTPS requests. Registry pulls run through the engine and use its separate trust configuration. Each task still requires an image compatible with the selected engine and CPU. The Windows Kiri runner image is x64.

For the local PGS workflow with a scoring file and without an ancestry reference, the tested pipeline used the following task images. When Kiri cannot access the registry, import these images from Docker archives made on the same computer with a trusted registry client. Preserve the upstream tags when importing:

- `ghcr.io/pgscatalog/pygscatalog:pgscatalog-utils-2.0.4`
- `ghcr.io/pgscatalog/plink2:2.00a5.10`
- `ghcr.io/pgscatalog/zstd:2-beta`
- `ghcr.io/pgscatalog/report:2-beta`
- `ghcr.io/pgscatalog/pyyaml:6.0`

## Heritage export and themes

Storybook now generates an offline Heritage_Story.html alongside the PDF and a source JSON. Use the existing View result action for the HTML, its Print / export PDF control for the web layout, or the separate PDF file. The latest explicit ancestry display result is labelled with provider/model/version. Components ≥2% receive their own pages; smaller components are grouped. Haplogroup routes require a supported source report; archaic variant counts are not relabelled as percentages. Missing results remain Still in progress. Current trio evidence is displayed as counts/positions, never painted as whole phased chromosome blocks.

Archive/Studio switches style. App theme files and extension rules are described in DNA_Software/Launcher/THEMES.md. Public cultural catalogs contain sourced context and attributed photos; generic entries remain labelled unfinished. No remote fonts, image requests or animation scripts are needed to read the exported HTML. The separate generated PDF has a simpler page layout.
