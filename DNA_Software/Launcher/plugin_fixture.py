"""Synthetic non-human-identifying reads and variants for adapter smoke tests."""

from pathlib import Path
import sys
import pysam


def create(folder):
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=True)
    fasta = root / "synthetic.fa"
    fasta.write_text(">1\n" + "A" * 1000 + "\n")
    pysam.faidx(str(fasta))
    bam = root / "synthetic.bam"
    header = {
        "HD": {"VN": "1.6", "SO": "coordinate"},
        "SQ": [{"SN": "1", "LN": 1000}],
        "RG": [{"ID": "rg1", "SM": "Synthetic", "PL": "ILLUMINA"}],
    }
    with pysam.AlignmentFile(str(bam), "wb", header=header) as output:
        for hap in (0, 1):
            for i in range(10):
                read = pysam.AlignedSegment()
                read.query_name = f"synthetic-{hap}-{i}"
                seq = list("A" * 250)
                if hap:
                    seq[49] = "C"
                    seq[149] = "G"
                read.query_sequence = "".join(seq)
                read.flag = 0
                read.reference_id = 0
                read.reference_start = 50
                read.mapping_quality = 60
                read.cigar = [(0, 250)]
                read.query_qualities = pysam.qualitystring_to_array("I" * 250)
                read.set_tag("RG", "rg1")
                output.write(read)
    pysam.index(str(bam))
    prefix = '##fileformat=VCFv4.2\n##reference=synthetic-GRCh38-coordinate-fixture\n##contig=<ID=1,length=1000>\n##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSynthetic\n'
    (root / "synthetic.vcf").write_text(
        prefix
        + "1\t100\tsynth1\tA\tC\t60\tPASS\t.\tGT\t0/1\n1\t200\tsynth2\tA\tG\t60\tPASS\t.\tGT\t0/1\n"
    )
    svprefix = prefix.replace(
        "#CHROM",
        '##INFO=<ID=END,Number=1,Type=Integer,Description="End position">\n##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Structural variant type">\n##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="Length difference">\n#CHROM',
    )
    sv = root / "structural.vcf"
    sv.write_text(
        svprefix
        + "1\t300\tsynthetic-deletion\t"
        + "A" * 81
        + "\tA\t60\tPASS\tEND=380;SVTYPE=DEL;SVLEN=-80\tGT\t0/1\n"
    )
    pysam.tabix_compress(str(sv), str(sv) + ".gz", force=True)
    pysam.tabix_index(str(sv) + ".gz", preset="vcf", force=True)
    (root / "README.txt").write_text(
        "Entirely synthetic fixture. No personal DNA. Two artificial heterozygous loci, 20 artificial reads, one 80-base deletion. Tests adapter operation, not clinical validity.\n"
    )


if __name__ == "__main__":
    create(sys.argv[1])
