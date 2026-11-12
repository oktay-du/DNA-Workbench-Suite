from pathlib import Path
import json

OUT = Path(__file__).with_name("catalog.json")
tasks = []


def field(
    key,
    label,
    kind="file",
    required=True,
    help="",
    choices=None,
    multi=False,
    default="",
):
    return dict(
        key=key,
        label=label,
        kind=kind,
        required=required,
        help=help,
        choices=choices or [],
        multi=multi,
        default=default,
    )


vcf = lambda key="vcf", label="VCF / VCF.gz": field(
    key,
    label,
    help="Variants file. Original remains unchanged; results end up in the order folder.",
)
ref = lambda required=True: field(
    "reference",
    "Matching reference FASTA",
    required=required,
    help="Must match the input file. In addition, check the original laboratory reference / checksum for CRAM.",
)
build = lambda key="build", label="Reference genome": field(
    key,
    label,
    "choice",
    choices=["Please select", "GRCh37", "GRCh38"],
    default="Please select",
    help="The coordinate system, not the measurement or download year.",
)
chrom = lambda: field(
    "chrom",
    "Chromosome",
    "choice",
    choices=[str(x) for x in range(1, 23)],
    default="1",
    help="Phasing and local origin are performed per chromosome.",
)


def add(
    id,
    category,
    title,
    description,
    tools,
    action,
    fields=None,
    help="",
    step=0,
    label="Start job",
    platform="WSL",
    kind="analysis",
):
    tasks.append(
        dict(
            id=id,
            category=category,
            title=title,
            description=description,
            tools=tools,
            action=action,
            fields=fields or [],
            help=help,
            step=step,
            button=label,
            platform=platform,
            kind=kind,
        )
    )


add(
    "inventory",
    "Files & sources",
    "Register original files",
    "Select files, create checksums and document origin.",
    "SHA-256 · File Register",
    "inventory",
    [
        field("files", "Original files", multi=True),
        field(
            "provider",
            "Provider",
            "choice",
            choices=[
                "Unknown",
                "23andMe",
                "MyHeritage",
                "Nebula",
                "Sequencing.com",
                "National Geographic",
                "Andere",
            ],
        ),
        field("note", "Sample / source note", "text", False),
    ],
    "Originals are only read. ZIP content is listed; archives are not overwritten or unpacked unchecked. A selection of people documents your assignment and does not yet prove genetic identity.",
    1,
    platform="Windows",
)
add(
    "missing",
    "Files & sources",
    "Check missing downloads",
    "Create a checklist for existing and still needed file types.",
    "File Register · Provider Checklist",
    "checklist",
    [field("files", "Available files", multi=True)],
    "For a WGS recalculation, FASTQ or BAM/CRAM, index and exact reference are often missing. VCF, gVCF, measured chip data, imputed data and vendor reports are kept separately. The launcher does not upload personal DNA data to vendors.",
    2,
    platform="Windows",
    label="Create checklist",
)
add(
    "identity",
    "Files & sources",
    "Compare source identity",
    "Test two VCFs on common SNPs for genotype compliance.",
    "BCFtools · comparison script",
    "compare",
    [
        vcf("a", "First-source VCF"),
        vcf("b", "Second-source VCF"),
        build("build_a", "First-source build"),
        build("build_b", "Second-source build"),
    ],
    "Both files must use the same coordinate system and comparable alleles, compared with measured biallelical SNP calls; missing digits remain unknown, high match is a hint, not a single proof of identity, and chip files are prepared beforehand in their own conversion step.",
    3,
)
add(
    "inspect",
    "Quality & formats",
    "Inspect file format",
    "Read headers, references, samples and quality statistics.",
    "BCFtools · SAMtools · snps",
    "inspect",
    [field("file", "VCF, BAM/CRAM or chip data")],
    "VCF: header and variant statistics. BAM/CRAM: header and file checker. Chip: format/build detection and error values. No quality values are invented and no original files are changed.",
    4,
)
add(
    "vcf_qc",
    "Quality & formats",
    "Measure variant quality",
    "Generate statistics on FILTER, genotypes, depth and quality fields.",
    "BCFtools stats",
    "vcf_qc",
    [vcf()],
    "DP/GQ are not included in every data set. A VCF variant does not show complete genomic coverage. PASS shares of different callers are not a direct ranking of the laboratories.",
    5,
)
add(
    "chip_vcf",
    "Quality & formats",
    "Convert chip data to VCF",
    "Transfer measured SNPs with matching FASTA into a documented VCF.",
    "snps · pysam",
    "chip_vcf",
    [field("file", "23andMe / MyHeritage raw data or ZIP"), build(), ref()],
    "Only actually existing SNP genotypes are output; no imputation, no filling up of unknown positions; I/D codes and inconclusively reproducible entries are counted and omitted; the reference is read from the selected FASTA; a detected deviant build leads to cancellation.",
)
add(
    "fastq_qc",
    "Quality & formats",
    "Check and filter FASTQ copies",
    "Check base quality and adapters; generate filtered R1/R2 working copies.",
    "fastp",
    "fastq_qc",
    [
        field("r1", "FASTQ R1 (.fastq.gz)"),
        field("r2", "FASTQ R2 (.fastq.gz)", required=False),
    ],
    "Paired-end data requires the associated R1 / R2 files. The output can be large. Original reads are preserved. The fastp HTML report documents the applied filters.",
)
add(
    "bam_qc",
    "Quality & formats",
    "Check reads, mapping and coverage",
    "Calculate alignment statistics and coverage in your own work folder.",
    "SAMtools · mosdepth",
    "bam_qc",
    [field("bam", "BAM or CRAM"), ref(False)],
    "For CRAM, the exact matching reference is required; a missing index is created alongside a reference in the work folder, not the original; the analysis evaluates mapping and coverage; an average depth does not replace a region check.",
)
add(
    "multiqc",
    "Quality & formats",
    "Combine quality reports",
    "Select a folder with fastp, SAMtools and other quality reports.",
    "MultiQC",
    "multiqc",
    [field("folder", "Quality report folder", "folder")],
    "MultiQC summarizes supported reports; it does not subsequently calculate missing readings and does not automatically evaluate clinical usability.",
)
add(
    "sarek",
    "WGS & variants",
    "Reanalyse WGS from FASTQ",
    "Start a local Sarek pipeline with your reads and reference.",
    "Nextflow · nf-core Sarek",
    "sarek",
    [
        field("r1", "FASTQ R1"),
        field("r2", "FASTQ R2"),
        ref(),
        field(
            "sex",
            "Chromosome complement for the pipeline",
            "choice",
            choices=["Not specified", "XX", "XY"],
        ),
        field(
            "caller",
            "Variant caller",
            "choice",
            choices=["strelka", "haplotypecaller", "deepvariant"],
            default="strelka",
        ),
    ],
    "This large computational step can run long and take up a lot of SSD space. A new samplesheet with a personal identifier is created. Without additional known variants, the base recalibration is skipped and this is documented in the plan. Sequencing, reference and model must fit the sample.",
    6,
)
add(
    "deepvariant",
    "WGS & variants",
    "Call variants from alignments",
    "From BAM/CRAM and a suitable reference, generate a new VCF and gVCF.",
    "DeepVariant 1.10 · SAMtools · Docker",
    "deepvariant",
    [
        field("bam", "BAM or CRAM"),
        ref(),
        field(
            "model",
            "Model / sequencing technology",
            "choice",
            choices=["WGS", "WES", "PACBIO"],
            default="WGS",
        ),
    ],
    "CPU execution with built-in model. Not for chip data. The model must match your reads; WGS is not an automatic confirmation for any sequencing technique. Original alignments remain unchanged.",
)
add(
    "normalize",
    "WGS & variants",
    "Normalise VCF",
    "Check reference alleles, align variants to the left and split multiple alleles.",
    "BCFtools norm",
    "normalize",
    [vcf(), build(), ref()],
    "It only changes presentation and normalization, and a reference error stops the job, and this step doesn't make a build change and doesn't correct supposedly incorrect genotypes without evidence.",
    7,
)
add(
    "filter",
    "WGS & variants",
    "Filter variants",
    "Select FILTER and optionally DP/GQ and generate a new filtered VCF.",
    "BCFtools view",
    "filter",
    [
        vcf(),
        field(
            "pass_only",
            "FILTER selection",
            "choice",
            choices=["Pass and unset filter", "PASS only", "All entries"],
        ),
        field("dp", "Minimum FORMAT/DP (0 = disabled)", "text", False, default="0"),
        field("gq", "Minimum FORMAT/GQ (0 = disabled)", "text", False, default="0"),
    ],
    "DP/GQ thresholds are used only on request. If these fields are missing, a requested DP/GQ filtering is terminated. The quality of different callers remains separately traceable.",
)
add(
    "conflicts",
    "WGS & variants",
    "Compare source conflicts",
    "Shared variants and genotype deviations as a report.",
    "BCFtools · conflict report",
    "compare",
    [
        vcf("a", "Normalised first-source VCF"),
        vcf("b", "Normalised second-source VCF"),
        build("build_a", "First-source build"),
        build("build_b", "Second-source build"),
    ],
    "No preferred truth is chosen and nothing is filled in silently. SNPs with different REF/ALT representations do not count as directly comparable. Sources and errors remain separate.",
    8,
)
add(
    "merge",
    "Family & ancestry",
    "Prepare a multi-sample VCF",
    "Compile sources as separate samples, with documented sample names.",
    "BCFtools merge",
    "merge",
    [field("files", "Normalised VCFs with matching reference", multi=True), build()],
    "The sources are merged as separate sample columns, thus preventing multiple files from becoming an improved common genotype.",
)
add(
    "roh",
    "Family & ancestry",
    "Find runs of homozygosity",
    "Calculate ROH with PLINK 1.9 from an appropriate genotype marker panel.",
    "PLINK 1.9",
    "roh",
    [vcf()],
    "Requires a representative genotype panel with homozygous reference positions. A pure variant VCF is unsuitable for this. PLINK standard parameters must match the marker density. ROH does not prove an exact parental relationship.",
)
add(
    "peddy",
    "Family & ancestry",
    "Check VCF and pedigree",
    "Peddy checks genotype proximity, outliers, and specified family roles.",
    "Peddy",
    "peddy",
    [
        vcf("vcf", "Multi-sample VCF"),
        field("ped", "PED file with matching sample IDs"),
        build(),
    ],
    "Requires sufficient common measured markers, matching sample identifiers and PED. XX/XY clues and origin PCA are limited estimates, not proof of identity or ancestry.",
)
add(
    "whatshap",
    "WGS & variants",
    "Phase using sequencing reads",
    "WhatsHap uses matching reads in addition to statistical reference panels.",
    "WhatsHap",
    "whatshap",
    [vcf(), field("alignment", "BAM / CRAM from the same sample"), ref(), build()],
    "VCF, reference, read groups and sample must fit together. Missing phase remains unknown. Source files remain intact.",
)
add(
    "truvari",
    "Quality & formats",
    "Compare structural variants",
    "Compare two compatible SV VCFs using explicit parameters.",
    "Truvari",
    "truvari",
    [
        vcf("base", "Comparison baseline (SV VCF)"),
        vcf("comparison", "Comparison SV VCF"),
        ref(),
        build(),
    ],
    "The basis is only a truth record if this is independently proven. A comparison of two providers does not prove error-free. Standard SV thresholds may be unsuitable for the caller.",
)
add(
    "kinship",
    "Family & ancestry",
    "Estimate relatedness",
    "Calculate KING coefficients for a prepared multi-person VCF.",
    "PLINK 2 / KING-Verfahren",
    "kinship",
    [vcf("vcf", "Multi-sample VCF")],
    "Uses autosomal biallelial SNPs and removes markers with many errors. Coefficients are indications of genetic proximity. They are not an automatic pedigree reconstruction and not a legal pedigree.",
    9,
)
add(
    "ref_export",
    "Family & ancestry",
    "Export a reference panel",
    "1000 genomes or HGDP for a chromosome as VCF.",
    "PLINK 2 · 1000 Genomes / HGDP",
    "ref_export",
    [
        field(
            "panel",
            "Reference panel",
            "choice",
            choices=["1000 Genomes GRCh38", "HGDP GRCh38"],
        ),
        chrom(),
    ],
    "The installed panels are located on GRCh38. They serve as comparison groups; they must not be mixed with GRCh37 target coordinates.",
)
add(
    "pca",
    "Family & ancestry",
    "Visualise ancestry PCA",
    "Represent a prepared common cohort after LD thinning as PCA.",
    "PLINK 2 · Plotly",
    "pca",
    [
        field("file", "Common VCF or PLINK .pgen file"),
        field("labels", "Population metadata (.psam / CSV / TSV)", required=False),
    ],
    "For ancestry comparisons, input must include your samples AND suitable references, export panels if necessary and compile them with harmonised target samples, and without references, the PCA only shows differences within the selected group, and the graph does not produce ethnicity percentages.",
    10,
)
add(
    "beagle",
    "Family & ancestry",
    "Phase genotypes",
    "Statistical phasing of associated alleles with an optional reference panel.",
    "Beagle 5.5",
    "beagle",
    [
        vcf(),
        field("map", "Genetic map in Beagle / PLINK format"),
        chrom(),
        field("refpanel", "Phased reference panel, VCF.gz", required=False),
    ],
    "Additional position imputation is disabled. Phasing is a statistical estimate. Genetic map, reference panel, chromosome name and build must match.",
)
add(
    "ibd",
    "Family & ancestry",
    "Find shared DNA segments",
    "Calculate IBD segments from phased genotypes.",
    "hap-IBD",
    "ibd",
    [
        vcf("vcf", "Phased multi-sample VCF"),
        field("map", "Genetic map in PLINK format"),
    ],
    "Required phased, comparable markers without missing alleles. Small segments can be uncertain. Genetic segment length in cM and simple base pair distance are different.",
)
add(
    "rfmix",
    "Family & ancestry",
    "Model local ancestry",
    "Model origin along a chromosome with labeled reference samples.",
    "RFMix 2",
    "rfmix",
    [
        vcf("query", "Phased target VCF"),
        vcf("refpanel", "Phased reference VCF"),
        field("samplemap", "Reference samples and populations"),
        field("map", "Genetic map for RFMix"),
        chrom(),
    ],
    "Requires curated reference populations and correctly phased data, the results depend on the reference selection, according to the project, the license is aimed at academic research; the project license is in the repository.",
)
add(
    "ancient",
    "Family & ancestry",
    "Explore ancient reference data",
    "Open ADMIXTOOLS with graphical interface and examine AADR as a reference.",
    "ADMIXTOOLS 2 · AADR",
    "launch",
    help="The interface provides historical models and f-statistics. AADR is under DNA_references. Reference populations and model assumptions must be chosen consciously. Similarity to ancient samples does not prove direct ancestry from a particular person or culture.",
    label="Opening ADMIXTOOLS",
    kind="launch",
)
add(
    "mito",
    "Family & ancestry",
    "Estimate maternal haplogroup",
    "Evaluate an mtDNA-VCF with the installed Phylotree.",
    "Haplogrep 3",
    "mito",
    [vcf("vcf", "VCF with mitochondrial positions")],
    "A pure list of variants is not a complete indication of coverage. Missing mtDNA entries must not be considered as safely measured reference bases.",
    11,
)
add(
    "yhaplo",
    "Family & ancestry",
    "Estimate paternal haplogroup",
    "Examine Y-DNA data with yhaplo.",
    "yhaplo",
    "yhaplo",
    [vcf("vcf", "VCF with Y-chromosome positions"), build()],
    "The installed yhaplo database uses GRCh37. For GRCh38, first create a validated matching data set. Without sufficiently meaningful Y positions, no reliable allocation is possible.",
)
add(
    "opencravat_run",
    "Health & traits",
    "Annotate health-related variants",
    "Annotate ClinVar and gnomAD locally and generate tables.",
    "OpenCRAVAT · ClinVar · gnomAD4",
    "opencravat_run",
    [vcf(), build()],
    "Uses only the local annotators ClinVar and gnomAD4. Contradictory or unclear variants are not diagnoses. A missing entry is not an exclusion of disease. genotype quality and clinical confirmation remain to be assessed separately.",
    12,
)
add(
    "vep",
    "Health & traits",
    "Annotate genes and transcripts",
    "Use the local Ensembl VEP cache 116 for GRCh38.",
    "Ensembl VEP",
    "vep",
    [vcf(), build()],
    "The installed cache is GRCh38. GRCh37 files cannot simply be referred to as GRCh38 here. Build change must be validated separately. Consequence predictions are not automatic clinical evaluation.",
)
add(
    "pharmcat",
    "Health & traits",
    "Explore pharmacogenetics",
    "Evaluate a suitable GRCh38-VCF with PharmCAT.",
    "PharmCAT 3.4",
    "pharmcat",
    [vcf(), build()],
    "Requires suitable and sufficiently fully measured genotypes. Unknown positions are not added to reference genotypes by the launcher. Complex genes and structural variants can limit the significance. The report does not replace a medical drug decision.",
    13,
)
add(
    "pgs",
    "Health & traits",
    "Calculate a polygenic score",
    "Apply a published weighting model to your prepared genotypes.",
    "PGS Catalog Calculator",
    "pgs",
    [vcf(), build(), field("score", "PGS weights (.txt / .txt.gz)")],
    "A model must fit the feature, build, population and question. The launcher calculates scores without re-interpretation into an absolute risk of disease. The weighting file is explicitly selected; missing variants and brand overlap are visible in the pipeline report.",
)
add(
    "report",
    "Reports & management",
    "Create a research report",
    "Create a printable source and results report for that person.",
    "Local HTML / Markdown report",
    "report",
    [field("note", "Additional personal note", "text", False)],
    "The report links the jobs, inputs, versions, and results created in the launcher, it doesn't invent diagnoses and marks the evaluation as a research overview, and in the browser you can print it as a PDF.",
    14,
    platform="Windows",
    label="Create report",
)
add(
    "export",
    "Reports & management",
    "Export selected findings",
    "Enter reports and supporting documents into a clearly named ZIP.",
    "ZIP export · SHA-256",
    "export",
    [field("files", "Reports and evidence to export", multi=True)],
    "Only the explicitly selected files are copied. The same file names are given separate subfolders. The ZIP and the source files are given checksums. Large raw data is not attached unasked.",
    15,
    platform="Windows",
    label="Create export",
)
add(
    "versions",
    "Reports & management",
    "Installation and versions",
    "Open the documented installation, tool versions and exams.",
    "Installationsregister",
    "versions",
    help="Shows the stored start tests and public sample runs, which confirm the setup of the tools, not the quality of a personal DNA sample.",
    platform="Windows",
    label="Opening of registers",
    kind="launch",
)
apps = [
    (
        "gramps",
        "Gramps Desktop",
        "Gramps",
        "pedigree, persons, sources and genealogical reports.",
    ),
    (
        "grampsweb",
        "Gramps Web",
        "GrampsWeb",
        "Interactive pedigree and chromosome views. Create your own local owner account when you first visit.",
    ),
    (
        "igv",
        "IGV Desktop",
        "IGV",
        "Visually control reads, coverage and variants. Select BAM/CRAM including index and appropriate reference in the program.",
    ),
    (
        "jbrowse",
        "JBrowse Desktop",
        "JBrowse",
        "Genome browser with tracks for variants and sequence data.",
    ),
    (
        "ocgui",
        "OpenCRAVAT interface",
        "OpenCRAVAT",
        "Local variation interface. Select input files in the interface.",
    ),
    (
        "hapgui",
        "Haplogrep interface",
        "Haplogrep",
        "mtDNA classification with the installed reference tree version.",
    ),
    (
        "jupyter",
        "JupyterLab",
        "Jupyter",
        "Own analyses, diagrams and notebooks. The local access address appears in the started window.",
    ),
    (
        "terminal",
        "Ubuntu terminal",
        "Linux",
        "Use all installed Linux commands and start your own SSD container runtime.",
    ),
    (
        "wslstart",
        "Start Ubuntu",
        "Start",
        "Launches Ubuntu and the container runtime without terminal windows.",
    ),
    (
        "wslstop",
        "Stop WSL",
        "StopAll",
        "Terminate ALL WSL distributions on this computer and the shared paging file, and ongoing WSL evaluations are interrupted.",
    ),
    (
        "backup",
        "Back up Ubuntu as TAR",
        "Export",
        "Finish DNA SSD and write a full WSL export to the SSD, which can take a lot of space.",
    ),
    (
        "powershell",
        "PowerShell",
        "PowerShell",
        "Open Windows PowerShell in the SSD Project folder.",
    ),
    ("cmd", "Windows command prompt", "Cmd", "Open CMD in the SSD project folder."),
    (
        "explorer",
        "Open SSD project folder",
        "Explorer",
        "Open results, orders and input registers in the Explorer.",
    ),
]
for id, title, core, desc in apps:
    add(
        id,
        "Tools & system",
        title,
        desc,
        title,
        "launch",
        help=desc,
        label="Open",
        kind="launch",
        platform="Windows / WSL",
    )
    tasks[-1]["core"] = core
next(t for t in tasks if t["id"] == "ancient")["core"] = "Admixtools"
add(
    "import",
    "Files & sources",
    "Import provider datasets",
    "Assign multiple files to a provider, dataset and a person.",
    "SQLite · SHA-256 · Original archive",
    "import",
    [
        field("files", "Files in this dataset", multi=True),
        field("provider", "Provider", "text"),
        field("label", "Dataset name", "text", False),
        field(
            "declared_build",
            "Reference build",
            "choice",
            choices=["Unknown", "GRCh37", "GRCh38"],
        ),
        field(
            "measurement",
            "Genotype origin / measurement",
            "choice",
            choices=["Unknown / mixed", "Measured", "Imputed", "Phased/derived"],
        ),
        field("note", "Sample / kit note", "text", False),
    ],
    "Import here means locally on your SSD. Move or copy files outside of your personal archive can be selected. Files in your existing personal archive are registered there. SHA-256 detects identical file bytes; repeated vendor imports are documented separately as sources. No genotypes are blindly merged.",
    1,
    platform="Windows",
    label="Import locally",
)
tasks.insert(0, tasks.pop())
add(
    "archive_index",
    "Files & sources",
    "Register the existing archive",
    "Include the existing provider subfolders of this person in the database.",
    "SQLite · SHA-256",
    "archive_index",
    help="Automatic scanning of an existing archive is no longer available. Choose the files or folders explicitly in Batch file preparation. This action records that reminder and does not walk private download folders.",
    platform="Windows",
    label="Register profile archive",
)
add(
    "variant_index",
    "Files & sources",
    "Index source variants",
    "Store genotypes and quality fields from selected VCFs separately.",
    "SQLite · VCF index",
    "variant_index",
    [
        field("files", "Registered VCF / VCF.gz sources", multi=True),
        field(
            "fallback",
            "Build for sources without metadata",
            "choice",
            choices=["Source/Unknown", "GRCh37", "GRCh38"],
        ),
    ],
    "Import files to source management first. Variants, samples, build, GT, DP, GQ and FILTER remain connected to their source file. Missing calls are not added and conflicting sources are not automatically unified. Large VCFs require time and additional database space.",
    platform="Windows",
    label="Index variants",
)
export = next(t for t in tasks if t["id"] == "export")
export["title"] = "Export datasets and reports"
export["fields"] += [
    field(
        "compression_mode",
        "Compression",
        "choice",
        choices=["Automatic (recommended)", "Manual"],
    ),
    field(
        "packaging",
        "Manual packaging",
        "choice",
        choices=["ZIP", "GZIP (individual file)", "Without archive (folder)"],
    ),
    field(
        "compression_level",
        "Manual compression level",
        "choice",
        choices=["6 balanced", "1 fast", "9 maximum", "0 uncompressed"],
    ),
]
export["help"] += (
    "Automatic: multiple files as ZIP; already compressed content is not re-compressed; individual compressed files are copied unchanged; manually select packaging and level itself; GZIP is packaging, not genotype conversion; for indexable VCF exports, use the master work path."
)
add(
    "profile_view",
    "Files & sources",
    "Evidence-backed DNA profile",
    "View source quality, XX/XY notes and results per person.",
    "Source database · Profile documents",
    "profile_view",
    help="XX/XY is indicated as a preliminary indication if there are sufficient X/Y markers; if there are too few or conflicting data, it remains indeterminate. The marker test does not confirm a chromosome number. Haplogroups require suitable positions and analysis. ABO/Rh remains unknown without a validated procedure.",
    platform="Windows",
    kind="launch",
    label="Opening profile",
)
OUT.write_text(
    json.dumps(
        dict(
            version=1,
            categories=[
                "All steps",
                "Files & sources",
                "Quality & formats",
                "WGS & variants",
                "Family & ancestry",
                "Health & traits",
                "Reports & management",
                "Tools & system",
            ],
            tasks=tasks,
        ),
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
add(
    "family",
    "Family & ancestry",
    "Family tree and inheritance",
    "Link profiles, track mother/father lines and calculate individual genotype inheritances.",
    "Lokale Familien-Datenbank · Mendel-Rechner",
    "family",
    help="Opens the local pedigree page. Parents, children and partners are explicitly linked. Hypothetical individuals remain separate from measurement data. Single-position inheritance requires indexed QC-labeled genotypes marked as measured. No automatic disease, blood type or hair color prediction and no partner compatibility value.",
    platform="Windows",
    kind="launch",
    label="Opening the Family Page",
)
add(
    "visual",
    "Family & ancestry",
    "Ancestry and appearance",
    "Offline world map, origin parts and schematic avatar with feature probabilities.",
    "Lokale Weltkarte · Merkmalsansicht",
    "visual",
    help="Shows imported structured analysis results separated by person, vendor, model and version. No direct feature prediction from raw DNA yet. Unknown features remain neutral. The avatar is a schematic illustration; not a facial reconstruction.",
    platform="Windows",
    kind="launch",
    label="Opening up origin and appearance",
)
next(t for t in tasks if t["id"] == "import")["fields"].append(
    field(
        "storage_mode",
        "File handling",
        "choice",
        choices=["Verschieben", "Kopieren"],
        default="Verschieben",
        help="Move removes external source files only after the checked and registered destination. Copy them. Existing identical bytes are not re-stored.",
    )
)

add(
    "profile_analyze",
    "Quality & formats",
    "Analyse all profile files",
    "Check all registered sources, fully compare SNP calls and document conflicts per build.",
    "SHA-256 · SQLite · Source comparison",
    "profile_analyze",
    [
        field(
            "target",
            "Vergleichs-Build",
            "choice",
            choices=["GRCh38", "Getrennt belassen"],
            default="GRCh38",
        ),
        field("chain", "GRCh37→GRCh38-Chain (leer = Suite-Referenz)", required=False),
        field("reference", "GRCh38-FASTA (leer = Suite-Referenz)", required=False),
    ],
    help="Background job. GRCh37 SNPs can be mapped with matching chain and target FASTA for comparison to GRCh38; original coordinates are preserved. Alternatively, keep builds separate. BAM/CRAM/FASTQ, reports and unsupported formats are listed but not interpreted as genotypes. Absent variants are not reference genotypes. Match is not clinical validation. Large files can take a long time.",
    platform="Windows",
    label="Starting with profile analysis",
)
add(
    "profile_generate",
    "WGS & variants",
    "Create a cleaned SNP selection",
    "From the complete profile analysis, a comprehensible best selection of observed SNPs can be generated.",
    "SQLite · FASTA · Roundtrip exam",
    "profile_generate",
    [
        field(
            "analysis",
            "Completed analysis folder (empty = latest profile analysis)",
            "folder",
            False,
        ),
        build(),
        ref(),
    ],
    "Only explicitly measured sources of the same build. Conflicts are omitted; individual SNPs require PASS/DP≥10/GQ≥20, otherwise matching sources with at least one VCF. Provider uploads are not automatically independent measurements. No indels/SVs, no imputation, and no complete genome. Outputs: VCF, generic TXT, TSV, exclusion report, and provenance manifest. Activate only after testing as preferred.",
    platform="Windows",
    label="Create SNP selection",
)
add(
    "profile_activate",
    "WGS & variants",
    "Prefer tested SNP selection",
    "Register validated editions and prefer for suitable SNP tools.",
    "SHA-256 · Source history",
    "profile_activate",
    [field("folder", "Result folder of the SNP selection", "folder")],
    "Re-checks sources and result checksums. Originals are preserved and marked as used in the selection. Priority is given to SNP-QC, ROH, Beagle and PGS. Complete original WGS files remain necessary for indels/SVs and comprehensive health analyses.",
    platform="Windows",
    label="Activate preferred set",
)
add(
    "liftover_snps",
    "WGS & variants",
    "GRCh37 ↔ GRCh38 · Convert SNP coordinates",
    "Convert uniquely mapped SNP calls with target FASTA and Chain.",
    "PyLiftover 0.4.1 · FASTA",
    "liftover_snps",
    [
        field("file", "VCF or chip SNP file"),
        build(),
        field(
            "target",
            "Ziel-Build",
            "choice",
            choices=["GRCh38", "GRCh37"],
            default="GRCh38",
        ),
        field("chain", "Passende LiftOver-Chain (.chain.gz)"),
        ref(),
    ],
    "Only SNPs, no indels/SVs, gVCF blocks, phase or reads. Reverse strand is complemented and GT is recoded against the target reference. Ambiguous/unmapped locations and target collisions are reported. No resequencing and no coverage addition.",
    platform="Windows",
    label="Start SNP liftover",
)

add(
    "profile_refresh",
    "Quality & formats",
    "Renew Best Selection",
    "Re-analyze profile sources, create SNP selection and replace current selections.",
    "Profile pipeline · source portions",
    "profile_refresh",
    help="New imports only show a hint. Only the button creates a renewal order. It starts immediately or waits behind running orders. Analysis, creation and activation are part of this explicitly started order. Previous orders remain as a history; current.json is switched to the new validated version. If there are errors, the previous version remains.",
    platform="Windows",
    label="Refresh now",
)
add(
    "storybook",
    "Reports & management",
    "Export a haplogroup storybook",
    "Mother line, father line, Neanderthal and today as an illustrated PDF with sources.",
    "ReportLab · local provider reports",
    "storybook",
    [
        field("maternal_report", "Maternal Haplogroup Report (PDF)", required=False),
        field("paternal_report", "Paternal Haplogroup Report (PDF)", required=False),
        field("archaic_report", "Neanderthal report (PDF)", required=False),
        field(
            "language",
            "Output language",
            "choice",
            choices=["German", "English"],
            default="English",
        ),
    ],
    help="Supports personal 23andMe haplogroup and Neanderthal reports. Missing or unknown data is still in progress. Routes are broad, schematic regional models from the selected reports, no journeys of individual ancestors. 45% customer comparison is not a DNA component. No new haplogroup calculation.",
    platform="Windows",
    label="Create storybook",
)
add(
    "helix_export",
    "Reports & management",
    "Exporting Personal 3D-DNA Helix",
    "30 coherent Q30 bases from a FASTQ read as labeled STL and colored 3MF.",
    "Manifold3D · NumPy · local reads",
    "helix_export",
    [field("file", "FASTQ / FASTQ.gz")],
    help="A contiguous observed read piece, no composite VCF SNPs and no validated personal haplotype; base pair teaching model and schematic backbone; no atomic molecular model; STL is geometrically combined and tested; printer and material may require supports or adjustments.",
    platform="Windows",
    label="Create 3D print files",
)
add(
    "avatar_pack",
    "Reports & management",
    "Prepare photo avatar",
    "Export profile photo, uniform style and optional proven origin in a local design package.",
    "Profile photo · Prompt · Sources Manifesto",
    "avatar_pack",
    [
        field(
            "include_ancestry",
            "Include origin in design",
            "choice",
            choices=["No", "Yes"],
            default="No",
        )
    ],
    help="Select profile photo first under My Profile. Export photo, design prompt and selected structured origin results as ZIP. The small text AI does not produce images. An image generator is required for rendering; finished PNG/JPEG can be selected as profile photo. No genetic facial reconstruction.",
    platform="Windows",
    label="Export design package",
)
add(
    "sequence_stats",
    "Sequence tools",
    "Inspect FASTA / FASTQ",
    "Test sequence lengths, GC, unknown bases and FASTQ quality with visible sample size.",
    "Local sequence statistics · Biopython",
    "sequence_stats",
    [
        field("files", "FASTA / FASTQ files", multi=True),
        field("read_limit", "Maximum FASTQ reads to inspect", "text", default="10000"),
    ],
    help="FASTA is read in full. FASTQ is limited by default to 10,000 reads. Sequence numbers and Q30 bases are not verified genotypes, WGS coverage, and clinical quality certificate. Originals remain unchanged.",
    platform="Windows",
    label="Create sequence statistics",
)
add(
    "fasta_collect",
    "Sequence tools",
    "Create a FASTA collection",
    "Merge FASTA entries with unique identifiers, source list and optional sequence deduplication.",
    "Streaming · SQLite · SHA-256",
    "fasta_collect",
    [
        field("files", "FASTA files", multi=True),
        field(
            "deduplicate",
            "Remove identical sequences",
            "choice",
            choices=["No", "Yes"],
            default="No",
        ),
    ],
    help="Depends on sequence entries; no alignment, no variant consensus and no genome error correction; each output is given a unique identifier, the old header is in the source list; it is not automatically registered as a best selection.",
    platform="Windows",
    label="Create FASTA collection",
)
seq_fields = lambda: [
    field("file", "FASTA / FASTQ file"),
    field("record", "Sequence record (blank = first record)", "text", False),
    field("start", "Start (1-based, inclusive)", "text", default="1"),
    field("end", "End (inclusive)", "text", default="1000"),
]
add(
    "sequence_extract",
    "Sequence tools",
    "Extract a sequence interval",
    "Read a section from FASTA or FASTQ; index and output remain in the order.",
    "pyfastx",
    "sequence_extract",
    seq_fields(),
    help="Coordinates refer to the selected sequence entry, not to a random reference build, up to 5 million bases per section. The index is created in the order folder. A large genome/FASTQ index can take time and a lot of SSD space.",
    platform="Windows",
    label="Extract interval",
)
add(
    "sequence_transform",
    "Sequence tools",
    "Reverse Complement / Translation",
    "Complement a selected section or translate it in the first reading frame.",
    "Biopython · pyfastx",
    "sequence_transform",
    seq_fields()
    + [
        field(
            "operation",
            "Sequence operation",
            "choice",
            choices=["Reverse complement", "Translate frame 1"],
            default="Reverse complement",
        )
    ],
    help="Translation uses the standard code and explicitly selected section, incomplete final codons are documented and omitted, no gene discovery, disease prediction or profile change.",
    platform="Windows",
    label="Transform sequence",
)
add(
    "seqviz_view",
    "Sequence tools",
    "View sequence with SeqViz",
    "Linear and circular sequence view locally in the EXE; additionally offline export.",
    "SeqViz · pyfastx",
    "seqviz_view",
    seq_fields(),
    help="Up to 50,000 bases per view. DNA remains local, no automatic transfer to project sites. A representation is not a check of genetic identity or variant quality. The interactive view opens from the finished job.",
    platform="Windows",
    label="Create SeqViz view",
)
add(
    "variant_evidence_audit",
    "Quality & formats",
    "Audit variant evidence",
    "Read every VCF record and account for no-calls, filters, ploidy and selected-sample evidence.",
    "Local VCF accounting · Python",
    "variant_evidence_audit",
    [
        vcf(),
        field(
            "sample", "VCF sample (required when multiple samples exist)", "text", False
        ),
    ],
    help="VCF 4.1–4.5, plain or gzip/BGZF. Reports counts without exporting genotypes. No automatic first-sample choice, allele truncation, diagnosis, deduplication or WGS completeness claim. Use BCF conversion first for binary files.",
    platform="Windows",
    label="Audit VCF",
)
add(
    "sequence_explore",
    "Sequence tools",
    "Explore six frames & motifs",
    "Explore both strands, six reading frames, IUPAC motifs and sequence composition.",
    "Biopython · pyfastx",
    "sequence_explore",
    seq_fields()
    + [
        field("motif", "IUPAC motif (optional, up to 64 bases)", "text", False),
        field(
            "genetic_code", "Genetic code", "choice", choices=["1", "2"], default="1"
        ),
    ],
    help="At most 100,000 bases. Code 1 is standard; code 2 is vertebrate mitochondrial. Neither code nor biological origin is inferred. Overlapping motif hits retain uncertainty, strand and interval coordinates. Export HTML, JSON and six protein frames; no gene prediction.",
    platform="Windows",
    label="Explore sequence",
)
add(
    "model_readiness",
    "Sequence tools",
    "Check sequence model inputs",
    "Check sequence length and ambiguity against five long-range benchmark tasks before installing models.",
    "Local readiness check · pyfastx",
    "model_readiness",
    seq_fields()
    + [
        field(
            "model_task",
            "Benchmark task",
            "choice",
            choices=[
                "Enhancer–target gene",
                "eQTL",
                "Contact map",
                "Regulatory activity",
                "Transcription initiation",
            ],
            default="Enhancer–target gene",
        )
    ],
    help="Reports required input length and evaluation metric from DNALongBench. No weights or reference datasets are downloaded. This does not execute AI inference, estimate GPU memory or establish personal health validity.",
    platform="Windows",
    label="Check model input",
)
add(
    "dna_message",
    "Sequence tools",
    "DNA message studio",
    "Encode UTF-8 text into an educational DNA alphabet, or decode the same format.",
    "Local UTF-8 / 2-bit encoding",
    "dna_message",
    [
        field(
            "mode",
            "Operation",
            "choice",
            choices=["Encode text", "Decode DNA"],
            default="Encode text",
        ),
        field(
            "text",
            "Text or encoded DNA",
            "text",
            default="DNA Workbench sample",
        ),
    ],
    help="Maximum 4096 UTF-8 bytes or 16,384 DNA symbols. Export a FASTA and a source receipt. This is reversible encoding, not encryption, laboratory synthesis or personal genetic data.",
    platform="Windows",
    label="Create message",
)
add(
    "agent_handoff",
    "Tools & system",
    "Export agent workspace",
    "Create a local evidence snapshot and typed command guide for an external or local AI assistant.",
    "Versioned JSON · Shared command registry",
    "agent_handoff",
    [
        field(
            "include_quotes",
            "Include report quotations and profile details",
            "choice",
            choices=["No", "Yes"],
            default="No",
        )
    ],
    help="Uses the active profile. Default export omits report quotations and detailed personal metadata. No raw genotype files or control credentials are included. Review the output before sharing; this action does not contact an AI provider.",
    platform="Windows",
    label="Export agent context",
)
add(
    "gatk_validate",
    "Quality & formats",
    "Validate VCF with GATK",
    "Check format, alleles and reference compliance of a VCF with matching FASTA.",
    "GATK · SAMtools",
    "gatk_validate",
    [vcf(), build(), ref()],
    help="ValidateVariants checks structure and reference consistency, not the biological correctness of all genotypes. Without dbSNP, the IDS comparison is omitted.",
    platform="WSL",
    label="Start GATK validation",
)
add(
    "ugene",
    "Tools & system",
    "Opening the UGEN",
    "Optional portable sequence and alignment surface start.",
    "UGENE",
    "ugene",
    [field("file", "Open file in UGENE (optional)", required=False)],
    help="Separate GPL application; download and install via the dependencies menu. Starts only on explicit click. Save projects and exports in the app folder.",
    platform="Windows",
    kind="launch",
    label="Start UGENE",
)
add(
    "provider_export",
    "Files & sources",
    "Inspect 23andMe exports",
    "Check report, origin segments, pedigree JSON, raw data, R6 or phased data as separate sources.",
    "Local export parser",
    "provider_export",
    [
        field("file", "23andMe export file"),
        field(
            "export_kind",
            "Export type",
            "choice",
            choices=[
                "Detect automatically",
                "Reports Summary",
                "Ancestry Composition CSV",
                "Family Tree JSON",
                "Raw Data TXT",
                "Imputed Genotype Data R6",
                "Phased Genotype Data",
            ],
            default="Detect automatically",
        ),
    ],
    help="PDF is a report, CSV contains origin segments, JSON is first inventoried structurally. Unknown tree schemes do not generate family links. R6 is imputed and exclusively for research; phasing is no further measurement. ZIP with several VCFs is extracted first individually. Edition: JSON and HTML in the order folder; no automatic profile change.",
    platform="Windows",
    label="Examining exports",
)
catalog = json.loads(OUT.read_text(encoding="utf-8"))
tasks.append(
    {
        "id": "fastq_report",
        "category": "Quality & formats",
        "title": "FASTQ quality report without copying reads",
        "description": "Check all selected FASTQ reads with fastp; save only HTML/JSON reports.",
        "tools": "fastp",
        "action": "fastq_report",
        "fields": [
            {
                "key": "r1",
                "label": "FASTQ R1",
                "kind": "file",
                "required": True,
                "multi": False,
            },
            {
                "key": "r2",
                "label": "FASTQ R2",
                "kind": "file",
                "required": False,
                "multi": False,
            },
        ],
        "help": "Report-only: original reads remain unchanged. No filtered FASTQ copies or inferred genotypes.",
        "step": 0,
        "button": "Create report",
        "platform": "WSL",
        "kind": "analysis",
    }
)
tasks.append(
    {
        "id": "variant_convert",
        "category": "Quality & formats",
        "title": "Repack VCF / BCF",
        "description": "Convert variant formats without adding genotypes or relabelling reference builds.",
        "tools": "BCFtools",
        "action": "variant_convert",
        "platform": "WSL",
        "kind": "analysis",
        "step": 0,
        "button": "Convert",
        "help": "VCF, VCF.gz (BGZF) or BCF. Only the display is converted; no liftover, no error correction and no missing reads are generated. Original remains. The header is checked by the BCFtools parser in the course.",
        "fields": [
            {
                "key": "vcf",
                "label": "VCF / BCF",
                "kind": "file",
                "required": True,
                "multi": False,
            },
            {
                "key": "output_format",
                "label": "Output format",
                "kind": "choice",
                "required": True,
                "default": "VCF.gz (BGZF)",
                "choices": ["VCF.gz (BGZF)", "VCF", "BCF"],
            },
        ],
    }
)
tasks.append(
    {
        "id": "best_dataset",
        "category": "Files & sources",
        "title": "Build / renew BestDataset",
        "description": "Compare imported sources, select supported observed SNPs and publish a preferred versioned dataset with provenance.",
        "tools": "Lokale SNP-Pipeline · SHA-256",
        "action": "best_dataset",
        "platform": "Windows",
        "kind": "analysis",
        "step": 0,
        "button": "Build BestDataset",
        "help": "No perfect or complete genome reconstruction. Conflicts, unknown measurements and missing positions are not invented. Current issue: VCF/TXT/TSV and GZIP, provenance per SNP and source; Reads/Alignments remain linked original sources. BCF/PLINK via explicit conversion. Previous versions are preserved. Only the button starts the update.",
        "fields": [
            {
                "key": "build",
                "label": "Ziel-Build",
                "kind": "choice",
                "required": True,
                "choices": ["Automatic", "GRCh37", "GRCh38"],
                "default": "Automatic",
            },
            {
                "key": "reference",
                "label": "Matching reference FASTA",
                "kind": "file",
                "required": False,
                "multi": False,
            },
            {
                "key": "chain",
                "label": "Passende LiftOver-Chain (.chain.gz)",
                "kind": "file",
                "required": False,
                "multi": False,
            },
        ],
    }
)
tasks.append(
    {
        "id": "research_synthesis",
        "category": "Reports & management",
        "title": "Create a combined research report",
        "description": "Compile source reports, local tests and final profiles with proof of origin.",
        "tools": "Local evidence synthesis · ReportLab",
        "action": "research_synthesis",
        "platform": "Windows",
        "kind": "analysis",
        "step": 0,
        "button": "Create combined report",
        "fields": [],
        "help": "Chip data can be used for suitable measured positions. Non-comparable origin models, diseases or risk scores are not blindly averaged. Documented comparable model metadata and marker-related weights are a prerequisite for an exploratory numerical summary. Original reports are preserved.",
    }
)
catalog["tasks"] = tasks
if "Sequence tools" not in catalog["categories"]:
    catalog["categories"].insert(4, "Sequence tools")
OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(tasks), "Launcher-Funktionen erstellt")
