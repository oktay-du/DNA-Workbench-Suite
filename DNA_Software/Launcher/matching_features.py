"""Visible implementation/data requirements; no paid-tier or global database claims."""

FEATURES = []


def add(group, id, title, reference, action, description, status="Available locally"):
    FEATURES.append(
        dict(
            group=group,
            id=id,
            title=title,
            reference=reference,
            action=action,
            description=description,
            status=status,
        )
    )


add(
    "Dashboard",
    "dashboard",
    "Local data",
    "Dashboard",
    "dashboard",
    "Profiles, sources, quality evidence, imported segments and research projects.",
)
add(
    "Matching & comparison",
    "many",
    "Local match list",
    "One-to-Many Limited / Tier 1",
    "many",
    "Sorted matches from imported segments in the local stock. Without segment data, no worldwide matches.",
)
add(
    "Matching & comparison",
    "one",
    "Compare two profiles",
    "One-to-One",
    "one",
    "Segment list and cM evidence separate from SNP genotype match. For raw markers, check files first.",
)
add(
    "Matching & comparison",
    "shared",
    "Shared matches",
    "In Common With Matches",
    "shared",
    "Intersection of the local match neighbors of two profiles. No automatic ancestor confirmation.",
)
add(
    "Matching & comparison",
    "parents",
    "Homozygosity / parental context",
    "Are Your Parents Related?",
    "parents",
    "View imported ROH sections or prepare ROH workflow. No exact parental kinship can be derived from ROH alone.",
)
add(
    "Matching & comparison",
    "quality",
    "Filtered segment comparison",
    "One-to-One Q-Matching",
    "one",
    "Own filters for cM, SNP number and existing haplotype data. No replica of the proprietary Q matching model.",
)
add(
    "Segments & triangulation",
    "browser2d",
    "2D chromosome browser",
    "2D Chromosome Browser",
    "browser2d",
    "Display imported segments against reference lengths or observed endpoints.",
)
add(
    "Segments & triangulation",
    "browser3d",
    "Spatial segment view",
    "3D Chromosome Browser",
    "browser3d",
    "Spatially arranged chromosome bars; no measurement of spatial chromatin structure.",
)
add(
    "Segments & triangulation",
    "search",
    "Segment search",
    "Segment Search",
    "search",
    "Filter for chromosome and position window, base pairs are not converted to cM without a genetic map.",
)
add(
    "Segments & triangulation",
    "triangulation",
    "Triangulation candidates",
    "Triangulation",
    "triangulation",
    "All three pair comparisons must overlap in the same area, and phase consistency is only assessed with corresponding imported data.",
)
add(
    "Segments & triangulation",
    "compact",
    "Compact segment map",
    "Compact Segment Mapper",
    "compact",
    "Compact view of the same segment vouchers, without additional genetic conclusion.",
)
add(
    "Segments & triangulation",
    "projects",
    "Ancestor projects",
    "Ancestor Projects",
    "projects",
    "Save profiles and a documented ancestor as a research group with a note.",
)
add(
    "Clustering",
    "clusters",
    "Match groups",
    "AutoCluster Endogamy",
    "clusters",
    "Related components and density of the local match graph. Density is not an endogamy diagnosis.",
)
add(
    "Clustering",
    "kinship",
    "Relatedness overview",
    "AutoKinship",
    "kinship",
    "See existing KING evidence and documented family roles together. No automatic unambiguous pedigree reconstruction.",
)
add(
    "Clustering",
    "segmentgroups",
    "Regional segment groups",
    "AutoSegment / AutoSegment Split",
    "segmentgroups",
    "Divide overlapping segments into regional groups; own disclosed grouping approach.",
)
add(
    "Matrices",
    "autosomal",
    "Autosomal cM matrix",
    "Autosomal",
    "matrix",
    "Pairwise cM totals from non-overlapping imported segments; unknown values remain empty.",
)
add(
    "Matrices",
    "xdna",
    "X-DNA matrix",
    "X-DNA",
    "xdna",
    "Only imported X segments. No application of autosomal kinship thresholds to X DNA.",
)
add(
    "Matrices",
    "overlap",
    "Shared marker positions",
    "Overlap",
    "overlap",
    "Number of shared autosomal SNP test points; fingerprint limit visible.",
)
add(
    "Matrices",
    "identical",
    "Identical SNP genotypes",
    "Fully Identical SNPs",
    "identical",
    "Identical unphased genotypes do not show identical inherited chromosome segments.",
)
add(
    "Matrices",
    "fir",
    "IBD2 / FIR candidates",
    "Fully Identical Region cM's",
    "fir",
    "Overlap of complementary haplotype pairs. Exact cM cuts require a matching genetic map.",
)
add(
    "Matrices",
    "generations",
    "Possible relationship degrees",
    "Generations",
    "kinship",
    "KING degree classes and documented relationships; no clear generation gap.",
)
add(
    "Ancestry & models",
    "ancestry",
    "View ancestry results",
    "Admixture Heritage + Oracle",
    "ancestry",
    "Show existing model estimates. Provider-Oracle coefficients and references are not invented.",
)
add(
    "Ancestry & models",
    "pca",
    "Prepare ancestry PCA",
    "Admixture",
    "task:pca",
    "Prepared common cohort and appropriate reference panel are required. PCA is not an ethnicity percentage calculation.",
    "Analysis workflow",
)
add(
    "Ancestry & models",
    "ancient",
    "Explore ancient references",
    "Archaic DNA Matches",
    "task:ancient",
    "Open ADMIXTOOLS/AADR workflow. Similarity to old samples does not prove direct ancestry.",
    "Analysis workflow",
)
add(
    "GEDCOM & family tree",
    "gedmini",
    "Export local family tree",
    "Mini-GEDCOM Builder",
    "gedmini",
    "Minimal GEDCOM export of documented mother/father links; no invented parents.",
)
add(
    "GEDCOM & family tree",
    "gedsearch",
    "Tree and surname search",
    "GEDCOM Master Search / Surname Search",
    "gedsearch",
    "Search locally imported GEDCOM individuals by name. Originals remain separate.",
)
add(
    "GEDCOM & family tree",
    "mrca",
    "Documented common ancestors",
    "MRCA Search / GEDCOMs & Ancestors",
    "mrca",
    "Seeking common ancestors and pathways in the local family graph or chosen GEDCOM; no DNA evidence.",
)
add(
    "Tools & export",
    "lookup",
    "Local profile and kit search",
    "User Lookup",
    "lookup",
    "Only local profiles and records; no online user directory.",
)
add(
    "Tools & export",
    "imports",
    "Segment, ROH and GEDCOM import",
    "Add Data",
    "imports",
    "CSV, hap-IBD, PLINK-.hom and GEDCOM with expressly chosen person, source and build.",
)
add(
    "Tools & export",
    "relationship",
    "Possible relationships",
    "Relationship Probability",
    "kinship",
    "KING degree classes instead of uncalibrated percentage probabilities. For real relationship posteriors, a validated model is missing.",
)
add(
    "Tools & export",
    "evaluation",
    "Kit quality and data scope",
    "DNA Kit Evaluation",
    "evaluation",
    "View existing file checks, secure QC points and missing data. No universal quality value from the file size.",
)
add(
    "Tools & export",
    "phasing",
    "Prepare phasing",
    "Phasing",
    "task:beagle",
    "Open Beagle with appropriate marker panel and genetic map.",
    "Analysis workflow",
)
add(
    "Tools & export",
    "ibd",
    "Calculate IBD segments",
    "One-to-Many / Segments",
    "task:ibd",
    "Open hap-IBD with comparable phased genotypes and genetic map.",
    "Analysis workflow",
)
add(
    "Tools & export",
    "lazarus",
    "Model missing relatives",
    "Lazarus",
    "family",
    "Open empty family profiles and the single locus inheritance calculator. Don't reconstruct confirmed complete genomes.",
    "Limited hypothesis function",
)
add(
    "Tools & export",
    "twin",
    "Non-transmitted alleles",
    "My Evil Twin",
    "twin",
    "Possible untransferred parent alleles at a QC-occupied autosomal position. No sibling genome.",
    "Limited hypothesis function",
)
add(
    "Tools & export",
    "superkit",
    "Prepare source consensus",
    "Create Super-Kits",
    "superkit",
    "Export a person's source/QC manifesto, not a perfectly declared or artificially replenished master record.",
    "Preparation, not a merged dataset",
)
add(
    "Tools & export",
    "exports",
    "Download lists and CSV",
    "Lists and CSV Downloads",
    "exports",
    "Export tables, receipts and settings displayed.",
)
