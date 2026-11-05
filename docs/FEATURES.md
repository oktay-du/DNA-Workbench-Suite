# Features

DNA Workbench combines source-aware imports, profiles, local research workflows and reproducible outputs. Optional tools require their documented dependencies and reference data.

## Workflow catalogue

| ID | Workflow | Tool / platform |
|---|---|---|
| import | Import provider datasets | SQLite · SHA-256 · Original archive |
| inventory | Originale erfassen | SHA-256 · File Register |
| missing | Check missing downloads | File Register · Provider Checklist |
| identity | Compare source identity | BCFtools · Vergleichsskript |
| inspect | Inspect file format | BCFtools · SAMtools · snps |
| vcf_qc | Measure variant quality | BCFtools stats |
| chip_vcf | Convert chip data to VCF | snps · pysam |
| fastq_qc | Check and filter FASTQ copies | fastp |
| bam_qc | Check reads, mapping and coverage | SAMtools · mosdepth |
| multiqc | Combine quality reports | MultiQC |
| sarek | Reanalyse WGS from FASTQ | Nextflow · nf-core Sarek |
| deepvariant | Call variants from alignments | DeepVariant 1.10 · SAMtools · Docker |
| normalize | Normalise VCF | BCFtools norm |
| filter | Filter variants | BCFtools view |
| conflicts | Compare source conflicts | BCFtools · Konfliktbericht |
| merge | Prepare a multi-sample VCF | BCFtools merge |
| roh | Find runs of homozygosity | PLINK 1.9 |
| peddy | Check VCF and pedigree | Peddy |
| whatshap | Phase using sequencing reads | WhatsHap |
| truvari | Compare structural variants | Truvari |
| kinship | Estimate relatedness | PLINK 2 / KING-Verfahren |
| ref_export | Export a reference panel | PLINK 2 · 1000 Genomes / HGDP |
| pca | Visualise ancestry PCA | PLINK 2 · Plotly |
| beagle | Phase genotypes | Beagle 5.5 |
| ibd | Find shared DNA segments | hap-IBD |
| rfmix | Model local ancestry | RFMix 2 |
| ancient | Explore ancient reference data | ADMIXTOOLS 2 · AADR |
| mito | Estimate maternal haplogroup | Haplogrep 3 |
| yhaplo | Estimate paternal haplogroup | yhaplo |
| opencravat_run | Annotate health-related variants | OpenCRAVAT · ClinVar · gnomAD4 |
| vep | Annotate genes and transcripts | Ensembl VEP |
| pharmcat | Explore pharmacogenetics | PharmCAT 3.4 |
| pgs | Calculate a polygenic score | PGS Catalog Calculator |
| report | Create a research report | Lokaler HTML-/Markdown-Bericht |
| export | Export datasets and reports | ZIP-Export · SHA-256 |
| versions | Installation and versions | Installationsregister |
| gramps | Gramps Desktop | Gramps Desktop |
| grampsweb | Gramps Web | Gramps Web |
| igv | IGV Desktop | IGV Desktop |
| jbrowse | JBrowse Desktop | JBrowse Desktop |
| ocgui | OpenCRAVAT interface | OpenCRAVAT interface |
| hapgui | Haplogrep interface | Haplogrep interface |
| jupyter | JupyterLab | JupyterLab |
| terminal | Ubuntu terminal | Ubuntu terminal |
| wslstart | Start Ubuntu | Start Ubuntu |
| wslstop | Stop WSL | Stop WSL |
| backup | Back up Ubuntu as TAR | Back up Ubuntu as TAR |
| powershell | PowerShell | PowerShell |
| cmd | Windows command prompt | Windows command prompt |
| explorer | Open SSD project folder | Open SSD project folder |
| archive_index | Register the existing archive | SQLite · SHA-256 |
| variant_index | Index source variants | SQLite · VCF-Index |
| profile_view | Evidence-backed DNA profile | Source database · Profile documents |
| family | Family tree and inheritance | Lokale Familien-Datenbank · Mendel-Rechner |
| visual | Ancestry and appearance | Lokale Weltkarte · Merkmalsansicht |
| profile_analyze | Compare registered SNP sources | SHA-256 · SQLite · Source comparison |
| profile_generate | Bereinigte SNP-Auswahl erstellen | SQLite · FASTA · Roundtrip exam |
| profile_activate | Prefer tested SNP selection | SHA-256 · Source history |
| liftover_snps | GRCh37 ↔ GRCh38 · SNP-Koordinaten konvertieren | PyLiftover 0.4.1 · FASTA |
| profile_refresh | Best Selection erneuern | Profile pipeline · source portions |
| storybook | Haplogruppen-Bilderbuch exportieren | ReportLab · lokale Anbieterberichte |
| helix_export | Exporting Personal 3D-DNA Helix | Manifold3D · NumPy · lokale Reads |
| avatar_pack | Prepare photo avatar | Profile photo · Prompt · Sources Manifesto |
| sequence_stats | FASTA / FASTQ untersuchen | Lokale Sequenzstatistik · Biopython |
| fasta_collect | FASTA-Sammlung zusammenstellen | Streaming · SQLite · SHA-256 |
| sequence_extract | Sequenzabschnitt extrahieren | pyfastx |
| sequence_transform | Reverse Complement / Translation | Biopython · pyfastx |
| seqviz_view | View sequence with SeqViz | SeqViz · pyfastx |
| gatk_validate | Validate VCF with GATK | GATK · SAMtools |
| ugene | Opening the UGEN | UGENE |
| provider_export | 23andMe-Export auswerten | Lokaler Export-Parser |
| fastq_report | FASTQ quality report without copying reads | fastp |
| variant_convert | Repack VCF / BCF | BCFtools |
| best_dataset | Build / renew BestDataset | Lokale SNP-Pipeline · SHA-256 |
| research_synthesis | Gemeinsamen Forschungsbericht erstellen | Lokale Evidenzsynthese · ReportLab |

## Evidence and outputs

Input fingerprints, source provenance and tool versions accompany saved results. BestDataset creates an explicit versioned selection; it does not manufacture missing measurements. Imported reports, local calculations and manual entries remain distinct.

Local family comparisons require imported evidence and do not access commercial matching databases. Health adapters are research tools, not clinical diagnosis. Ancestry methods require suitable reference panels.

Country artwork coverage varies; custom images can be added manually. Storybooks, maps and avatar prompts retain their evidence labels.

## Sequence lab

[Sequence lab guide](RESEARCH_LAB.md): VCF evidence accounting, six reading frames, IUPAC motif search, five-task model input screening, educational DNA message encoding and local agent handoffs. Two guided workflows reuse the existing source selection and result cache. Reviewed project architectures and integration boundaries are available in the app.
