"""Point-coordinate LiftOver with literal allele preservation and target FASTA checks.

Deliberately limited to SNP calls. Indels/SVs, gVCF blocks, phase and read
alignments require their own pipelines and are reported as not converted.
"""

from pathlib import Path
import gzip, json, sqlite3, sys
import source_store, profile_pipeline as pp


def run(
    person,
    source,
    build,
    target,
    chain,
    reference,
    out,
    log=print,
    cancel=lambda: False,
):
    if build == target or {build, target} != {"GRCh37", "GRCh38"}:
        raise ValueError("Select GRCh37 and GRCh38 as different builds.")
    packages = source_store.ROOT / "DNA_Software/Windows/PythonPackages"
    if str(packages) not in sys.path:
        sys.path.insert(0, str(packages))
    try:
        from pyliftover import LiftOver
    except ImportError:
        raise ValueError("Install dependency pyliftover first via check dependencies.")
    detected = source_store.build_hint(Path(source))
    if detected and detected != build:
        raise ValueError("Source build contradicts file header.")
    # Check the chain direction from its actual assembly-sized chromosome block.
    op = gzip.open if str(chain).endswith(".gz") else open
    expected = {"GRCh37": 249250621, "GRCh38": 248956422}
    with op(chain, "rt") as stream:
        for line in stream:
            c = line.split()
            if c and c[0] == "chain" and c[2] in ("chr1", "1"):
                if int(c[3]) in expected.values() and int(c[3]) != expected[build]:
                    raise ValueError("Chain has the wrong source direction.")
                if int(c[8]) in expected.values() and int(c[8]) != expected[target]:
                    raise ValueError("Chain hat den falschen Ziel-Build.")
                break
    source_sha256 = pp.digest(source, cancel)
    log("Load LiftOver card; no external DNA upload.")
    lo = LiftOver(str(chain))
    fa = pp.Fasta(reference)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any(
        fa.index[n][0] in expected.values() and fa.index[n][0] != expected[target]
        for n in ("1", "chr1")
        if n in fa.index
    ):
        raise ValueError("Ziel-FASTA hat falschen Build.")
    db = sqlite3.connect(out / "mapping.sqlite")
    db.execute(
        "CREATE TABLE loci(chrom TEXT,pos INTEGER,gt TEXT,rsid TEXT,ref TEXT,valid INTEGER,PRIMARY KEY(chrom,pos))"
    )
    stats = {
        "mapped": 0,
        "unmapped": 0,
        "multiple": 0,
        "reference_error": 0,
        "collisions": 0,
    }
    parsed = {}
    complement = str.maketrans("ACGT", "TGCA")
    try:
        with (out / "unmapped.tsv").open("w", encoding="utf-8") as rejected:
            rejected.write("chrom\tpos\treason\n")
            for i, (chromosome, pos, gt, rsid, ref, high, valid) in enumerate(
                pp.calls(source, parsed)
            ):
                if i % 10000 == 0:
                    if cancel():
                        raise InterruptedError("LiftOver abgebrochen.")
                    log(str(i) + " SNP-Aufrufe verarbeitet")
                hits = (
                    lo.convert_coordinate(
                        "chrM" if chromosome == "MT" else "chr" + chromosome, pos - 1
                    )
                    or []
                )
                reason = (
                    "unmapped" if not hits else "multiple" if len(hits) != 1 else ""
                )
                if not reason:
                    targetchrom, targetzero, strand, _ = hits[0]
                    targetchrom = pp.chrom(targetchrom)
                    targetpos = targetzero + 1
                    if strand == "-":
                        gt = "".join(sorted(gt.translate(complement)))
                    try:
                        newref = fa.base(targetchrom, targetpos)
                    except ValueError:
                        reason = "reference_error"
                if reason:
                    stats[reason] += 1
                    rejected.write(f"{chromosome}\t{pos}\t{reason}\n")
                    continue
                try:
                    db.execute(
                        "INSERT INTO loci VALUES(?,?,?,?,?,?)",
                        (targetchrom, targetpos, gt, rsid, newref, valid),
                    )
                except sqlite3.IntegrityError:
                    db.execute(
                        "UPDATE loci SET valid=0 WHERE chrom=? AND pos=?",
                        (targetchrom, targetpos),
                    )
                    stats["collisions"] += 1
            db.commit()
        path = out / "lifted_snps.vcf"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(
                "##fileformat=VCFv4.2\n##reference="
                + target
                + "\n##source=DNAWorkbench_PyLiftOver_0.4.1_SNP_only\n##DNAWorkbenchOriginalSHA256="
                + source_sha256
                + '\n##FILTER=<ID=CoordinateConverted,Description="Coordinate conversion only; original QC retained in source manifest">\n##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t'
                + person
                + "\n"
            )
            for chromosome, pos, gt, rsid, ref in db.execute(
                "SELECT chrom,pos,gt,rsid,ref FROM loci WHERE valid=1 ORDER BY chrom,pos"
            ):
                alt = sorted(set(gt) - {ref})
                alleles = [ref] + alt
                indices = "/".join(str(alleles.index(a)) for a in gt)
                stream.write(
                    f"{chromosome}\t{pos}\t{rsid}\t{ref}\t{','.join(alt) or '.'}\t.\t.\t.\tGT\t{indices}\n"
                )
                stats["mapped"] += 1
        result = {
            "person": person,
            "source_build": build,
            "target_build": target,
            "source": str(source),
            "source_sha256": pp.digest(source, cancel),
            "chain_sha256": pp.digest(chain, cancel),
            "reference_sha256": pp.digest(reference, cancel),
            "stats": stats,
            "input_stats": parsed,
            "scope": "SNP calls only; no phasing, indels, SVs, read realignment or added coverage. Original alleles complemented on reverse mappings and re-encoded against target FASTA.",
        }
        (out / "liftover.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result
    finally:
        db.close()
        fa.close()
