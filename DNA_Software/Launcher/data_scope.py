"""Evidence-based file scope, separate from commercial product/report entitlements."""

VERSION = "2026-11-03.1"


def describe(result):
    fmt = result.get("format", "Unknown")
    header = result.get("content_header", "").lower()
    n = result.get("called_points", 0)
    counts = result.get("chromosome_counts", {})
    regions = {
        "autosomal": sum(
            v for k, v in counts.items() if k in {str(i) for i in range(1, 23)}
        ),
        "X": result.get("x_called", 0),
        "Y": result.get("y_called", 0),
        "mtDNA": result.get("mt_called", 0),
    }
    kind = "Unknown content"
    scope = "Not determined"
    evidence = []
    notes = []
    measured = fmt in ("Chip/SNP table", "VCF") and n > 0
    imputed = result.get("measurement", "").startswith("Imputed") or any(
        x in header
        for x in ("##imputation", "imputed genotype", "imputed data", "##source=imput")
    )
    if fmt == "VCF":
        kind = (
            "gVCF / Reference blocks and variants"
            if result.get("gvcf_blocks", 0)
            else "VCF / Variantenliste"
        )
        scope = "Genome size not recorded"
        if (
            "whole genome" in header
            or "whole-genome" in header
            or "##assay=wgs" in header
        ):
            scope = "WGS specified in the header; cover not verified"
            evidence.append("Explicit WGS in the file header")
        if (
            "whole exome" in header
            or "whole-exome" in header
            or "##assay=wes" in header
        ):
            scope = "Exome specified in the header; check target regions and cover"
        notes.append(
            "A list of variants occupies neither 100% genome coverage nor 30×sequencing depth."
        )
    elif fmt == "Chip/SNP table":
        kind = "Genotype table / selected markers"
        scope = "Marker-based; no detection of a whole genome"
        notes.append(
            "The table structure may also have been exported from sequence data, and the original measurement technique must be documented separately."
        )
    elif fmt in ("BAM", "CRAM"):
        kind = "Ausgerichtete Sequenzreads"
        scope = "WGS / Exome / Panel not yet distinguished"
        notes.append(
            "Check header, target regions, coverage and quality report with SAMtools / mosdepth."
        )
    elif fmt == "FASTQ":
        kind = "Unaligned sequence reads"
        scope = "WGS / Exome / Panel not yet distinguished"
        notes.append(
            "Check R1/R2, readability, base quality and later coverage; no finished genotypes yet."
        )
    elif fmt == "Ancestry report / segment assignments":
        kind = "Finished interpretation of origin; no raw genotypes"
        scope = "Only origin results of this file"
    elif fmt == "Y-STR table":
        kind = "Y-STR markers / paternal lineage"
        scope = "Targeted Y-markers; no complete Y-sequence test"
    elif fmt == "PDF report":
        kind = "Fertiger Bericht / PDF"
        scope = "Report topic and findings not yet substantively examined"
    elif fmt.startswith("JSON") or fmt.startswith("GEDCOM"):
        kind = "Family tree / genealogy; no DNA measurement data"
        scope = "Genealogische Beziehungen"
    elif fmt == "Match-/Segmenttabelle":
        kind = "Relationship or segment results; no crude genotypes"
        scope = "Existing comparison results only"
    elif fmt.startswith("ZIP"):
        kind = "Archiv / mehrere Inhalte"
        scope = "Members separately review members"
        members = result.get("archive_members", [])
        fastqs = [
            m["name"]
            for m in members
            if m["name"].lower().endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz"))
        ]
        if fastqs:
            evidence.append(
                str(len(fastqs))
                + "FASTQ filenames in the archive; content and R1/R2 pairing still unchecked"
            )
    if imputed:
        notes.append(
            "Imputed values are statistically supplemented and are not confirmed as directly measured DNA points."
        )
    if not regions["Y"]:
        notes.append(
            "No called Y-markers proven: This proves neither a missing Y-test nor XX."
        )
    capabilities = {}
    for key in ("ancestry", "verwandtschaft", "health", "fitness"):
        if measured:
            state = "Check Marker Coverage/References"
            if key == "health":
                state = "Variant annotation possible; no clinical release"
            if key == "fitness":
                state = "Only with a suitable validated model judgeable"
            if imputed:
                state = "Statistical supplemented data; separate examination required"
            if result.get("color") in ("red", "black"):
                state = "Locked until quality/assignment conflict resolved"
        elif fmt in ("BAM", "CRAM", "FASTQ"):
            state = "Zuerst Sequenz-QC / Variantenbestimmung"
        else:
            state = "No suitable raw genotypes detected in this file"
        capabilities[key] = state
    capabilities["y_lineage"] = (
        "Y marker present; check haplogroup cover"
        if regions["Y"]
        else "Y-STR marker present; targeted STR comparison"
        if fmt == "Y-STR table"
        else "Not proven / not yet checked"
    )
    capabilities["mtDNA_Linie"] = (
        "mtDNA markers present; test haplogroup coverage"
        if regions["mtDNA"]
        else "Not proven / not yet checked"
    )
    return {
        "rules": VERSION,
        "kind": kind,
        "scope": scope,
        "regions": regions,
        "variant_types": result.get("variant_types", {}),
        "capabilities": capabilities,
        "evidence": evidence,
        "notes": notes,
        "summary": kind
        + " · "
        + scope
        + " · Y: "
        + str(regions["Y"])
        + " · mtDNA: "
        + str(regions["mtDNA"]),
        "clinical_validation": "Not derivable from file format, vendor or 30x product specification",
    }
