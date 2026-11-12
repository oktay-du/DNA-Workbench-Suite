<div align="center">

![DNA Workbench Suite — Your genome. Your workspace.](docs/images/project-banner.svg)

[![Release](https://img.shields.io/github/v/release/oktay-du/DNA-Workbench-Suite?style=flat-square&color=087f8c)](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest)
[![Build](https://github.com/oktay-du/DNA-Workbench-Suite/actions/workflows/build.yml/badge.svg)](https://github.com/oktay-du/DNA-Workbench-Suite/actions/workflows/build.yml)
[![Security checks](https://github.com/oktay-du/DNA-Workbench-Suite/actions/workflows/codeql.yml/badge.svg)](https://github.com/oktay-du/DNA-Workbench-Suite/actions/workflows/codeql.yml)
[![Platforms](https://img.shields.io/badge/desktop-x64%20%2B%20ARM64-243b53?style=flat-square)](docs/GETTING_STARTED.md)

**DNA files, family records and research workflows in one local workspace. 36 offline interface languages.**

[**Download**](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/) · [Getting started](docs/GETTING_STARTED.md) · [Screenshots](docs/GALLERY.md) · [Wiki](https://github.com/oktay-du/DNA-Workbench-Suite/wiki) · [Deutsch](README.de.md)

[Contribute](CONTRIBUTING.md) · [**Improve with AI**](AI_CONTRIBUTING.md) · [Report a bug](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

[Donate with NOWPayments](https://nowpayments.io/donation/oktayd) · [Buy Me a Coffee](https://buymeacoffee.com/okioki)

<a href="https://buymeacoffee.com/okioki"><img src="docs/images/support-qr.jpg" width="88" alt="Buy Me a Coffee donation QR code"></a>

</div>

![Short tour of DNA Workbench showing dark and light mode, the language picker and synthetic profile files](docs/images/workspace-demo.gif)

[Watch the full app tour](https://oktay-du.github.io/DNA-Workbench-Suite/#tour) · [Browse screenshots](docs/GALLERY.md) · [See all interface languages](https://oktay-du.github.io/DNA-Workbench-Suite/#languages)

## Start with your sources. Keep the evidence.

Import supported DNA files and family records, compare compatible sources, follow research workflows and keep the results with their provenance. Optional modules install when needed. Use the same typed commands through the GUI, CLI, JSON or MCP.

| Prepare | Explore | Keep and share |
|---|---|---|
| Batch intake, folders and archives | Genome and sequence tools | Saved results and research reports |
| Provider, format and reference-build review | Family profiles, comparisons and GEDCOM | Profile transfer and backups |
| Content deduplication and explicit move/copy | Supported ancestry and health-research adapters | Ancestry storybooks and educational DNA models |
| Source comparison and versioned BestDataset | Optional local or user-configured API assistance | Traceable exports with source metadata |

[Feature catalogue](docs/FEATURES.md) · [Supported formats](docs/TOOL_FORMATS.md) · [Versions and reference data](docs/VERSIONS.md)

> **Research software.** Results depend on input quality, reference data and the selected method. The suite is not a clinical diagnostic system. Synthetic examples illustrate features; they are not personal genetic findings.

## Get started

**Windows.** Download [DNAWorkbench-Windows-x64.zip](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Windows-x64.zip), extract it into a writable folder, and run `DNA_Launcher.exe`. Core setup downloads portable Python and WebView2 on x64. The [Windows ARM64 preview](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Windows-arm64.zip) uses Windows 11 and WebView2 Evergreen.

**Linux.** Download [DNAWorkbench-Linux-x64.zip](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Linux-x64.zip), extract it into a writable folder, and run `./DNA-Workbench.sh`. An [ARM64 preview](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Linux-arm64.zip) is also available.

**macOS.** Check the [release notes](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) for preview builds. The native WebKit host uses macOS 13 or later and Python 3.12 or later.

Then try the included artificial sample profiles. Import data you are authorized to process, and install the modules needed for your chosen workflow. Application data, downloads and caches stay in the application folder. [Installation and portability →](docs/GETTING_STARTED.md)

## Requirements

| | Windows x64 | Linux x64 |
|---|---|---|
| Release zip | `DNAWorkbench-Windows-x64.zip` | `DNAWorkbench-Linux-x64.zip` |
| Start | `DNA_Launcher.exe` | `./DNA-Workbench.sh` |
| Host | 64-bit Windows and .NET Framework 4.8 | A graphical session, Python 3.12, GTK 3 and WebKitGTK 4.1 |
| First-run runtimes | Core setup downloads portable Python and WebView2 | The host supplies Python and WebKitGTK |
| Build | `DNA_Software/Launcher/build.ps1`, then `release_tools.py --target windows` | `DNA_Software/Launcher/build_linux.sh` |

When a tool publishes both builds, each host uses its own file. That covers PLINK 2, Haplogrep, Gramps, JBrowse, UGENE and Temurin. samtools and bcftools publish source only, so Linux builds 1.25 and Windows uses the Win-NGS 1.23.1 bundles. mosdepth is a Linux binary; Windows coverage uses samtools depth. Wine is not used. WSL remains the Windows host for programs that still have only a Linux file. [Where each program runs →](docs/VERSIONS.md)

## A connected research workspace

The goal is to bring feasible provider and research-service workflows onto the user's PC, with consistent navigation and traceable results. Work without AI, use supported local models, or configure optional external APIs. External integrations have their own requirements and privacy policies; sensitive data must not be sent silently.

Tools integrated or launched by supported adapters include [SAMtools](https://github.com/samtools/samtools), [BCFtools](https://github.com/samtools/bcftools), [PLINK](https://www.cog-genomics.org/plink/2.0/), [IGV](https://github.com/igvteam/igv), [JBrowse](https://github.com/GMOD/jbrowse-components), [GenomeSpy](https://github.com/genome-spy/genome-spy), [OpenCRAVAT](https://github.com/KarchinLab/open-cravat), [VEP](https://github.com/Ensembl/ensembl-vep), [PharmCAT](https://github.com/PharmGKB/PharmCAT) and [Gramps](https://github.com/gramps-project/gramps).

Availability and prerequisites vary by module. Large reference genomes, panels and models are separate downloads. [Component credits and terms →](THIRD_PARTY.md)

## Build one useful improvement

**Developers and coding agents are welcome.** Choose one concrete improvement, check existing issues and PRs, validate the result and submit a focused pull request.

| Contributor | Start here |
|---|---|
| Developer | [Contributing](CONTRIBUTING.md) · [Development guide](docs/DEVELOPMENT.md) |
| Coding agent or AI-assisted developer | [AI contributor guide and copyable prompt](AI_CONTRIBUTING.md) |
| Integration author | [GUI, CLI, JSON and MCP](docs/AGENTS.md) · [Input contracts](docs/TOOL_FORMATS.md) |
| User | [Feedback and improvements](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose) · [Wiki](https://github.com/oktay-du/DNA-Workbench-Suite/wiki) |

The Windows shell uses C# and WebView2. The Linux shell uses Python with GTK 3 and WebKitGTK. Local workflows use Python, and embedded views use HTML, CSS and JavaScript. Choose from 36 interface languages in the toolbar or Settings. Language packs are included for offline use.

<details>
<summary><strong>Development commands</strong></summary>

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"
powershell -NoProfile -File DNA_Software/Launcher/build.ps1
python DNA_Software/Launcher/public_package.py
python DNA_Software/Launcher/release_tools.py --target windows
```

```sh
python3 -m unittest discover -s DNA_Software/Launcher -p "test_*.py"
sh DNA_Software/Launcher/build_linux.sh
```

Use the [synthetic Samples](Samples/README.md). Keep personal DNA, medical records, credentials, runtime databases and downloaded reference datasets out of Git.

</details>

## Project and support

Maintained by **Oktay Du / OD** · **oktaydu@proton.me** · Created with AI assistance.

Designated original contributions are available under [PolyForm Noncommercial 1.0.0](DNA_Software/Launcher/Notices/POLYFORM-NONCOMMERCIAL-1.0.0.md).

[Privacy](docs/PRIVACY.md) · [Research notice](docs/LEGAL.md) · [Security](SECURITY.md).

Support is optional.
