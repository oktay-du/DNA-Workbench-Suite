# Sequence lab

Open **Sequence lab** in the research menu. The profile selected in the top bar is used throughout. Tool cards show their purpose and dependencies; compatible sources and previous results use the same selection and caching rules as other workflows.

1. **Check sources:** audit a genotype VCF or inspect FASTA/FASTQ statistics. A multi-sample VCF requires an explicit sample name. BCF files must first use the existing conversion tool.
2. **Explore sequence:** choose a record and a 1-based inclusive interval. Explore six reading frames with standard code 1 or vertebrate mitochondrial code 2. Optional IUPAC motif search covers both strands and distinguishes definite from possible matches at ambiguous bases. Overlaps are retained; palindromic motifs are not counted twice for strand alone.
3. **Review requirements:** check interval length and ambiguous bases against five DNALongBench tasks before choosing a model. This is input screening, not model installation or inference.
4. **Keep the evidence:** open saved jobs to inspect HTML, JSON and FASTA outputs, rerun explicitly or export. HTML reports include a print/save-PDF button. Motif coordinates are relative to the selected interval; the receipt preserves its original source coordinates and sequence digest.

**Variant evidence review** and **Sequence exploration** are also available under Workflows. The first combines the local VCF accounting audit with BCFtools statistics. The second combines sequence statistics, six-frame/motif exploration and SeqViz. Dependencies are prepared only when needed. Missing inputs pause the guided workflow; profile imports do not automatically start analyses.

## Additional tools

- **DNA message studio** reversibly maps UTF-8 bytes to A/C/G/T. It is an educational encoding, not encryption or personal biological DNA. It exports FASTA, an HTML view and a checksum receipt.
- **Export agent workspace** creates a versioned local evidence snapshot and a guide to registered commands. Report quotations and detailed personal metadata are excluded by default. Raw genotype files and service-control credentials are not packaged. Review the output before sharing it with another AI provider.
- **Project architecture & integrations** lists the reviewed projects, pinned source commits, implementation languages and integration boundaries. The new features are independently implemented; referenced applications are not silently installed or bundled.

The desktop remains C# / WebView2, the shared analysis and command layer Python, and the interface HTML/CSS/JavaScript. GUI, CLI, JSON and MCP invoke the same registered workflows. Run `DNA.cmd schema workflow.sequence_explore` or `DNA.cmd schema research.projects` for current argument schemas.

## Scope

The VCF audit supports plain/gzip/BGZF VCF 4.1–4.5. It reads all records, accounts for filters, no-calls and ploidy, and reports source SHA-256. It does not deduplicate loci, verify reference alleles or infer an individual's complete genome. Indels and structural alleles are not reduced to single letters. `PASS` is a file filter status, not independent biological verification. For complete format/reference validation use the existing BCFtools/GATK tools with matching references. See the [VCF specification](https://samtools.github.io/hts-specs/VCFv4.5.pdf).

Sequence exploration is limited to 100,000 bases and motifs to 64 bases. The report retains at most 5,000 motif positions while counting all matches; the HTML previews at most 200 positions and 3,000 residues per frame. Full translated frames remain in JSON and protein FASTA. Reading frames and motif matches are descriptive sequence operations, not gene discovery or clinical interpretation.

Model task lengths and metrics are sourced from the pinned [DNALongBench project](https://github.com/ma-compbio/DNALONGBENCH/tree/6c43266c6dc85b5529b5a784b880ee88cc1a54b3). Model weights and datasets have separate requirements and licenses.
