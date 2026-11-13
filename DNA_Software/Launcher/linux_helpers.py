"""Local data adapters for the Windows DNA launcher. No network or uploads."""

from pathlib import Path
import sys, json, gzip, csv, re, html, collections


def document(folder, title, body):
    p = Path(folder) / "report.html"
    p.write_text(
        '<!doctype html><meta charset="utf-8"><title>'
        + html.escape(title)
        + "</title><style>body{font:16px Segoe UI,Arial;max-width:1100px;margin:40px auto;color:#183047}table{border-collapse:collapse;width:100%}td,th{padding:9px;border-bottom:1px solid #dde4eb;text-align:left}h1{color:#117f78}</style><h1>"
        + html.escape(title)
        + "</h1>"
        + body,
        encoding="utf-8",
    )
    return p


def detected_build(path):
    import zipfile

    text = ""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            candidates = [n for n in z.namelist() if not n.endswith("/")]
            if not candidates:
                return None
            text = z.read(candidates[0])[:30000].decode("utf-8-sig", errors="replace")
    else:
        op = gzip.open if str(path).endswith((".gz", ".bgz")) else open
        with op(path, "rt", encoding="utf-8-sig", errors="replace") as f:
            text = f.read(30000)
    low = text.lower()
    if re.search(r"grch38|hg38|hs38|build[ =:]*(?:38)", low):
        return "GRCh38"
    if re.search(r"grch37|hg19|hs37|build[ =:]*(?:37)", low):
        return "GRCh37"
    return None


def check_build(path, selected):
    known = detected_build(path)
    if known and selected != known:
        raise ValueError(
            "Erkannter Build "
            + known
            + "Wrong with choices"
            + selected
            + "Agree:"
            + str(path)
        )
    return known


class ChipRows:
    """Row view shared by a provider parse and the educational SNP table."""

    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    @property
    def empty(self):
        return not self.rows

    def iterrows(self):
        for rsid, chrom, pos, genotype in self.rows:
            yield (
                rsid,
                collections.SimpleNamespace(chrom=chrom, pos=pos, genotype=genotype),
            )


def synthetic_chip_rows(path):
    """Read the educational SNP table shipped with the sample profiles.

    The snps package only accepts provider exports. The sample file is marked
    DNAWorkbenchSynthetic and is counted here so the inspect workflow still
    writes a result.
    """
    lines = Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines or "DNAWorkbenchSynthetic=true" not in lines[0]:
        return None
    rows = []
    for line in lines[1:]:
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4 or not re.fullmatch(r"rs\d+", parts[0]):
            raise ValueError("Synthetic SNP table has an unreadable row.")
        if not parts[2].isdigit():
            raise ValueError("Synthetic SNP table has a non-numeric position.")
        rows.append((parts[0], parts[1], int(parts[2]), parts[3]))
    if not rows:
        raise ValueError("Synthetic SNP table has no genotype rows.")
    return rows


def inspect_chip(path, out):
    synthetic = synthetic_chip_rows(path)
    if synthetic is not None:
        called = sum(1 for row in synthetic if re.fullmatch(r"[ACGT]{1,2}", row[3]))
        result = dict(
            records=len(synthetic),
            called=called,
            call_rate=float(called / len(synthetic)),
            header_build=None,
            parser_build="synthetic-educational",
            note="Synthetic SNP table counted locally. It is not a provider export and has no genome build.",
        )
        df = ChipRows(synthetic)
    else:
        from snps import SNPs

        s = SNPs(path, resources_dir="/opt/dna/cache/snps")
        frame = s.snps
        if frame.empty:
            raise ValueError(
                "No chip genotypes detected. Please select measured raw data instead of parentage/report files."
            )
        gen = frame.genotype.fillna("").astype(str)
        called = int(gen.str.fullmatch("[ACGT]{1,2}").sum())
        result = dict(
            records=int(len(frame)),
            called=called,
            call_rate=float(called / len(frame)),
            header_build=detected_build(path),
            parser_build=str(s.build),
            note="The parser build can be an assumption if the header is missing.",
        )
        df = frame
    Path(out, "chip-statistics.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False)
    )
    document(
        out,
        "Chip file: format and errors",
        "<pre>"
        + html.escape(json.dumps(result, indent=2, ensure_ascii=False))
        + "</pre>",
    )
    return df


def chip_vcf(path, reference, build, out, sample):
    import pysam

    check_build(path, build)
    df = inspect_chip(path, out)
    fasta = pysam.FastaFile(reference)
    contigs = set(fasta.references)
    records = []
    excluded = collections.Counter()
    for rsid, row in df.iterrows():
        chrom = str(row.chrom)
        pos = int(row.pos)
        gt = str(row.genotype).upper()
        if chrom.startswith("chr"):
            chrom = chrom[3:]
        variants = [chrom, "chr" + chrom]
        if chrom in ["M", "MT"]:
            variants = ["MT", "chrM", "M"]
        contig = next((c for c in variants if c in contigs), None)
        if not contig:
            excluded["contig_nicht_gefunden"] += 1
            continue
        if not re.fullmatch("[ACGT]{1,2}", gt):
            excluded["unbekannt_oder_nicht_snp"] += 1
            continue
        try:
            ref = fasta.fetch(contig, pos - 1, pos).upper()
        except ValueError:
            excluded["position_ausserhalb_referenz"] += 1
            continue
        if ref not in "ACGT" or len(ref) != 1:
            excluded["referenz_unbekannt"] += 1
            continue
        alts = sorted(set(gt) - {ref})
        alleles = [ref] + alts
        encoded = "/".join(str(alleles.index(base)) for base in gt)
        records.append(
            (
                contig,
                pos,
                str(rsid) if re.fullmatch(r"rs\d+", str(rsid)) else ".",
                ref,
                ",".join(alts) or ".",
                encoded,
            )
        )
    order = {c: i for i, c in enumerate(fasta.references)}
    records.sort(key=lambda r: (order[r[0]], r[1]))
    raw = Path(out) / "gemessene_chippositionen.vcf"
    with raw.open("w") as f:
        f.write(
            "##fileformat=VCFv4.2\n##reference="
            + build
            + "\n##source=DNA_Launcher_measured_chip_sites\n"
        )
        f.write(
            "##DNA_Launcher_note=No_imputation_no_missing_to_reference_no_invented_DP_or_GQ\n"
        )
        for c in fasta.references:
            f.write(
                "##contig=<ID="
                + c
                + ",length="
                + str(fasta.get_reference_length(c))
                + ">\n"
            )
        f.write(
            '##FORMAT=<ID=GT,Number=1,Type=String,Description="Measured genotype">\n'
        )
        f.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + sample + "\n"
        )
        for c, p, i, r, a, g in records:
            f.write("\t".join([c, str(p), i, r, a, ".", ".", ".", "GT", g]) + "\n")
    compressed = str(raw) + ".gz"
    pysam.tabix_compress(str(raw), compressed, force=True)
    pysam.tabix_index(compressed, preset="vcf", force=True)
    summary = {
        "exported_measured_sites": len(records),
        "excluded": dict(excluded),
        "build": build,
        "source": str(path),
        "note": "Only existing chip SNPs; no additional genotypes invented.",
    }
    Path(out, "konvertierung.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    document(
        out,
        "Measurede Chippositionen als VCF",
        "<pre>"
        + html.escape(json.dumps(summary, indent=2, ensure_ascii=False))
        + "</pre>",
    )
    if not records:
        raise ValueError("No suitable SNPs exported.")


def compare(a, b, ba, bb, out):
    import pysam

    if ba != bb:
        raise ValueError(
            "The reference builds differ, first harmonize in a controlled manner; no silent build change is made."
        )
    check_build(a, ba)
    check_build(b, bb)

    def calls(path):
        with pysam.VariantFile(path) as v:
            if len(v.header.samples) != 1:
                raise ValueError(
                    "The source comparison expects exactly one sample per VCF. For several people using family functions."
                )
            name = list(v.header.samples)[0]
            for row in v:
                if (
                    len(row.ref) != 1
                    or len(row.alts or []) != 1
                    or len(row.alts[0]) != 1
                ):
                    continue
                if set(row.ref + row.alts[0]) - set("ACGT"):
                    continue
                gt = row.samples[name].get("GT")
                if not gt or any(g is None for g in gt):
                    continue
                bases = tuple(sorted(row.alleles[g] for g in gt))
                yield (
                    (row.contig.removeprefix("chr"), row.pos, row.ref, row.alts[0]),
                    "/".join(bases),
                )

    left = dict(calls(a))
    common = same = conflicts = count_b = 0
    with Path(out, "konflikte.tsv").open("w") as f:
        f.write("Chromosom\tPosition\tREF\tALT\tQuelle_A\tQuelle_B\n")
        for key, gt in calls(b):
            count_b += 1
            if key not in left:
                continue
            common += 1
            if gt == left[key]:
                same += 1
            else:
                conflicts += 1
                f.write("\t".join(map(str, key + (left[key], gt))) + "\n")
    stats = {
        "called_biallelic_snps_a": len(left),
        "called_biallelic_snps_b": count_b,
        "common_called_snps": common,
        "same_genotypes": same,
        "conflicts": conflicts,
        "concordance_on_jointly_called_snps": same / common if common else None,
        "build": ba,
    }
    Path(out, "vergleich.json").write_text(json.dumps(stats, indent=2))
    document(
        out,
        "Source comparison",
        "<pre>"
        + html.escape(json.dumps(stats, indent=2))
        + "</pre><p>Only jointly called biallelic SNPs with matching REF/ALT are compared. Missing positions are not reference calls. This alone does not verify identity or quality.</p>",
    )
    if not common:
        raise ValueError(
            "No directly comparable jointly called SNPs found. Check reference, normalization and data type."
        )


def names(vcf, prefix, out):
    import pysam

    with pysam.VariantFile(vcf) as v:
        old = list(v.header.samples)
    if not old:
        raise ValueError("VCF does not contain samples.")
    new = [
        re.sub("[^A-Za-z0-9_]", "_", prefix) + "_S" + str(i + 1)
        for i in range(len(old))
    ]
    Path(out, "neue_probennamen.txt").write_text("\n".join(new) + "\n")
    with Path(out, "probenzuordnung.tsv").open("w") as f:
        f.write("Original\tLauncher_Name\n")
        for a, b in zip(old, new):
            f.write(a + "\t" + b + "\n")


def pca_count(psam, out):
    n = sum(1 for line in open(psam) if line.strip() and not line.startswith("#"))
    if n < 3:
        raise ValueError(
            "PCA requires at least three samples; additionally suitable reference persons for comparisons of origin."
        )
    Path(out, "pca_k.txt").write_text(str(min(10, n - 1)))
    Path(out, "pca_mode.txt").write_text("approx" if n > 1000 else "")


def pca_plot(eigenvec, labels, out):
    import pandas as pd
    import plotly.express as px

    df = pd.read_csv(eigenvec, sep=r"\s+")
    df.columns = [x.lstrip("#") for x in df.columns]
    df["Population"] = "Not labelled"
    if labels:
        try:
            meta = pd.read_csv(labels, sep=None, engine="python")
        except Exception:
            meta = pd.read_csv(labels, sep=r"\s+")
        if len(meta.columns) == 1:
            meta = pd.read_csv(labels, sep=r"\s+")
        meta.columns = [str(c).lstrip("#") for c in meta.columns]
        idcol = next(
            (c for c in meta if c.lower() in ["iid", "sample", "sampleid", "id"]), None
        )
        pop = next(
            (
                c
                for c in meta
                if c.lower() in ["superpop", "population", "pop", "gruppe"]
            ),
            None,
        )
        if not idcol or not pop:
            raise ValueError("Metadata requires IID/Sample and Population/SuperPop.")
        lookup = dict(zip(meta[idcol].astype(str), meta[pop].astype(str)))
        df["Population"] = df["IID"].astype(str).map(lookup).fillna("Not labelled")
    fig = px.scatter(
        df,
        x="PC1",
        y="PC2",
        color="Population",
        hover_name="IID",
        title="PCA of the selected cohort",
        template="plotly_white",
    )
    fig.update_layout(
        font=dict(family="Segoe UI"), legend_title_text="Referenzbeschriftung"
    )
    fig.write_html(str(Path(out, "pca_interaktiv.html")), include_plotlyjs=True)
    df.to_csv(Path(out, "pca_mit_metadaten.tsv"), sep="\t", index=False)


def score_sheet(prefix, person, out):
    sampleset = re.sub(r"[^a-zA-Z0-9]", "", person) or "Sample"
    with Path(out, "samplesheet.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sampleset", "path_prefix", "chrom", "format"])
        w.writerow([sampleset, prefix, "", "pfile"])


def main():
    action = sys.argv[1]
    a = sys.argv[2:]
    if action == "chip_vcf":
        chip_vcf(*a)
    elif action == "inspect_chip":
        inspect_chip(*a)
    elif action == "compare":
        compare(*a)
    elif action == "names":
        names(*a)
    elif action == "pca_count":
        pca_count(*a)
    elif action == "pca_plot":
        pca_plot(*a)
    elif action == "score_sheet":
        score_sheet(*a)
    elif action == "check_build":
        check_build(*a)
    else:
        raise ValueError("Unbekannter lokaler Helfer: " + action)


if __name__ == "__main__":
    main()
