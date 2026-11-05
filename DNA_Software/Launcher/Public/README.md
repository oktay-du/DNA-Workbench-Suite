<div align="center">

# DNA Workbench Suite

**Your genome. Your workspace.**

Version 1.0 · Windows x64 · Local genomics research · By OD

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/) · [Getting started](docs/GETTING_STARTED.md) · [Features](docs/FEATURES.md) · [Deutsch](README.de.md)

[Donate with NOWPayments](https://nowpayments.io/donation/oktayd) · [Buy Me a Coffee](https://buymeacoffee.com/okioki)

<a href="https://buymeacoffee.com/okioki"><img src="docs/images/support-qr.jpg" width="120" alt="Buy Me a Coffee donation QR code"></a>

</div>

![Local workspace in light mode, using synthetic data](docs/images/03-overview-light.png)

DNA Workbench Suite brings DNA sources, family records, research tools and reusable results into one Windows application. Keep sources traceable, install optional modules when needed and work with the same commands through the GUI, CLI, JSON or MCP.

## What you can do

| Workspace | Capabilities |
|---|---|
| Sources and quality | Import batches, folders and supported archives; review providers, reference builds and formats; explicitly move or copy files; detect identical content. |
| Dataset preparation | Compare compatible sources, record conflicts and create a versioned BestDataset with source provenance. |
| Genome and sequence | Inspect variants and alignments, explore sequence regions and launch compatible genome browsers. |
| Family | Manage profiles and family links, import GEDCOM and investigate local DNA comparisons, segments and matrices. |
| Research and findings | Run supported ancestry and health-research adapters, retain imported findings and review source-linked results. |
| Reports and creative exports | Export profile backups, reports, ancestry storybooks and educational DNA models. |
| Automation | Reuse saved results and run registered workflows through GUI, CLI, JSON and MCP. Optional AI assistance is configurable. |

Scientific results depend on the selected method, available input and reference data. This is research software, not a clinical diagnostic system. Version 1.0 is not a claim of clinical validation.

## Get started

1. Download and extract **DNAWorkbench-Windows-x64.zip** from [Releases](https://github.com/oktay-du/DNA-Workbench-Suite/releases).
2. Run `DNA_Launcher.exe` from a writable folder.
3. Complete Core setup and open the artificial sample profiles.
4. Import your own authorized data and install the modules needed for a selected workflow.

Application data, downloads and caches use the application folder. Windows x64 and .NET Framework 4.8 are required. WSL and virtualization require host support and may need administrator access and a restart. See [installation and portability](docs/GETTING_STARTED.md).

## Tools and reference data

The suite integrates or launches tools including [SAMtools](https://github.com/samtools/samtools), [BCFtools](https://github.com/samtools/bcftools), [PLINK](https://www.cog-genomics.org/plink/2.0/), [IGV](https://github.com/igvteam/igv), [JBrowse](https://github.com/GMOD/jbrowse-components), [GenomeSpy](https://github.com/genome-spy/genome-spy), [OpenCRAVAT](https://github.com/KarchinLab/open-cravat), [VEP](https://github.com/Ensembl/ensembl-vep), [PharmCAT](https://github.com/PharmGKB/PharmCAT) and [Gramps](https://github.com/gramps-project/gramps).

Availability, installation requirements and license conditions vary by module. Large reference genomes, research panels and AI models are downloaded separately. See [formats](docs/TOOL_FORMATS.md), [versions and reference data](docs/VERSIONS.md) and [component notices](THIRD_PARTY.md).

## Develop and contribute

The Windows shell uses C# and WebView2. Local workflows use Python; the embedded interface uses HTML, CSS and JavaScript. English is the source language, with German localization and light/dark themes.

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"
powershell -NoProfile -File DNA_Software/Launcher/build.ps1
```

Use the [synthetic samples](Samples/README.md) for development. Never submit personal DNA, medical records, credentials or runtime databases. Read [Contributing](CONTRIBUTING.md), [Development](docs/DEVELOPMENT.md) and [Agent integration](docs/AGENTS.md).

## License and contact

Source available under the component terms in [LICENSE](LICENSE). PolyForm Noncommercial applies to the designated original contributions; commercial permissions are available by separate written agreement. Required component notices are collected in [Licenses & Notices](docs/LICENSING.md).

**Oktay Du / OD · oktaydu@proton.me**

Created with AI assistance. [Privacy](docs/PRIVACY.md) · [Research notice](docs/LEGAL.md) · [Security](SECURITY.md) · [Report a bug or suggest an improvement](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose).

Support is optional. The [NOWPayments registration link](https://account.nowpayments.io/de/create-account?link_id=2318328728) is an affiliate link; OD may benefit. Donations do not purchase a commercial license.
