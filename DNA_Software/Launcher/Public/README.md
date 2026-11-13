# DNA Workbench Suite

**DNA files, family records and research workflows in one local workspace.**

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/) · [Installation guide](docs/GETTING_STARTED.md) · [Translations](#translations)

Organize your sources by person and provider, compare compatible files, and keep the inputs and results behind every analysis.

![App tour with light and dark mode, the language picker and synthetic profile files](docs/images/workspace-demo.gif)

[Watch the app tour](https://oktay-du.github.io/DNA-Workbench-Suite/#tour) · [Screenshot gallery](docs/GALLERY.md)

## What you can do

- Import DNA files, folders and supported archives. Review the provider, format and reference build before you copy or move anything.
- Group datasets, documents and results by profile. Record each file's origin. Keep direct measurements separate from inferred values and note when variants have been assigned to chromosome copies.
- Check sample quality and compare sources. Build a versioned BestDataset for workflows that can use the same reference build.
- Explore variants and sequence files with genome viewers. Compare DNA profiles and connect research notes with family records and GEDCOM files.
- Save results with their inputs and logs. Export reports and back up profiles for later use.
- Use the optional local assistant to navigate the workspace. You can configure external AI separately.

[Full feature catalogue](docs/FEATURES.md) · [Supported formats](docs/TOOL_FORMATS.md)

## Tools and what they do

These are selected tools the suite integrates or can launch. Availability varies by workflow and operating system. Some modules and reference data are separate downloads.

| Tool | What it does |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Reads, indexes and inspects aligned sequencing files in SAM, BAM and CRAM formats. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filters, normalizes, combines and inspects variant files in VCF and BCF formats. |
| [fastp](https://github.com/OpenGene/fastp) | Checks FASTQ read quality and can trim or filter reads. |
| [mosdepth](https://github.com/brentp/mosdepth) | Measures read coverage from BAM and CRAM files. |
| [MultiQC](https://seqera.io/multiqc/) | Combines reports from multiple quality-control tools into one view. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Works with genotype data for tasks such as variant filtering, relatedness and principal component analysis. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Uses genotype data to infer which variants lie on the same copy of a chromosome. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Finds matching DNA segments inherited from a common ancestor. It uses genotype data with variants assigned to chromosome copies. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Uses sequencing reads to assign variants to chromosome copies. |
| [Truvari](https://github.com/ACEnglish/truvari) | Compares structural variants in VCF files. |
| [IGV](https://igv.org/doc/desktop/) | Displays aligned reads, variants and other genome tracks at specific locations. |
| [JBrowse](https://jbrowse.org/jb2/) | Lets you browse reference sequences and linked tracks interactively. |
| [GenomeSpy](https://genomespy.app/) | Renders interactive genomic charts with browser graphics acceleration. |
| [Gramps](https://www.gramps-project.org/) | Organizes genealogy records, family trees and GEDCOM data. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Annotates variants using selectable sources and annotators. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Predicts how variants may affect genes, transcripts and proteins. |
| [PharmCAT](https://pharmcat.org/) | Produces pharmacogenetics research reports from supported genotype inputs. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Runs the optional local language model on compatible CPU and GPU runtimes. |

[Tool versions and prerequisites](docs/VERSIONS.md)

## Get started

Choose the package that matches your operating system and processor. The release page lists x64 and ARM64 downloads for Windows, Linux and macOS. Some builds are previews.

1. On Windows, extract the archive and run the launcher. Complete Core setup when prompted.
2. On Linux, start the included shell launcher with Python, GTK and WebKitGTK installed.
3. On macOS, keep the app beside the extracted workspace files. The preview requires macOS 13 or later and Python 3.12 or later.
4. Start with the included synthetic samples to try the workflows without using personal files.

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Installation guide](docs/GETTING_STARTED.md)

## Command line and automation

Use the same command registry through the desktop interface, CLI, JSON-RPC and MCP. The headless service runs on the local machine. You can list commands and read their schemas without opening a desktop window.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

The optional assistant can help you navigate results. Its answers do not replace the source data or a verified analysis.

> Research software. Results depend on the input, method and references. DNA Workbench Suite does not provide a clinical diagnosis.

## Project and support

Maintained by Oktay Du / OD with AI assistance.

[Privacy](docs/PRIVACY.md) · [Security](SECURITY.md) · [Project license](LICENSE) · [Report a problem](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Support the project · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Translations

The app includes 36 offline interface languages. Choose a translation of this project page below.

[Deutsch](README.de.md) · [English](README.md) · [Türkçe](docs/readme/README.tr.md) · [Español](docs/readme/README.es.md) · [Français](docs/readme/README.fr.md) · [Português](docs/readme/README.pt.md) · [Italiano](docs/readme/README.it.md) · [Nederlands](docs/readme/README.nl.md) · [Svenska](docs/readme/README.sv.md) · [Ελληνικά](docs/readme/README.el.md) · [Čeština](docs/readme/README.cs.md) · [Română](docs/readme/README.ro.md) · [Magyar](docs/readme/README.hu.md) · [Polski](docs/readme/README.pl.md) · [Українська](docs/readme/README.uk.md) · [Русский](docs/readme/README.ru.md) · [العربية](docs/readme/README.ar.md) · [فارسی](docs/readme/README.fa.md) · [اردو](docs/readme/README.ur.md) · [हिन्दी](docs/readme/README.hi.md) · [नेपाली](docs/readme/README.ne.md) · [ქართული](docs/readme/README.ka.md) · [Հայերեն](docs/readme/README.hy.md) · [Монгол](docs/readme/README.mn.md) · [简体中文](docs/readme/README.zh-Hans.md) · [日本語](docs/readme/README.ja.md) · [한국어](docs/readme/README.ko.md) · [Bahasa Indonesia](docs/readme/README.id.md) · [Bahasa Melayu](docs/readme/README.ms.md) · [Tiếng Việt](docs/readme/README.vi.md) · [ไทย](docs/readme/README.th.md) · [Filipino](docs/readme/README.fil.md) · [አማርኛ](docs/readme/README.am.md) · [Kiswahili](docs/readme/README.sw.md) · [Soomaali](docs/readme/README.so.md) · [Hausa](docs/readme/README.ha.md)
