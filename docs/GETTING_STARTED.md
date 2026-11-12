# Installation and first analysis

## Requirements

| | Windows x64 | Linux x64 |
|---|---|---|
| Release zip | `DNAWorkbench-Windows-x64.zip` | `DNAWorkbench-Linux-x64.zip` |
| Start | `DNA_Launcher.exe` | `./DNA-Workbench.sh` |
| Desktop | .NET Framework 4.8 and WebView2 | Python 3.12, GTK 3 and WebKitGTK 4.1 |
| Python for the app | Downloaded by Core setup | The host Python |
| Linux analysis tools | A Linux-only program runs inside WSL | The same program runs on the host |
| Tools with both builds | PLINK 2, Haplogrep, Gramps, JBrowse, UGENE and Temurin each use the Windows file | Those same releases use the Linux file |
| No official Windows binary | samtools and bcftools use the Win-NGS 1.23.1 bundles. mosdepth has no Windows build, so coverage uses samtools depth | Official samtools and bcftools 1.25 source, plus the Linux mosdepth binary |

On Debian and Ubuntu the desktop packages are `python3`, `python3-gi`, `gir1.2-gtk-3.0` and `gir1.2-webkit2-4.1`.

## Windows release

Extract `DNAWorkbench-Windows-x64.zip` into a writable SSD folder. Run `DNA_Launcher.exe` without administrator privileges for normal work. First-run Core setup downloads verified pinned Python and WebView2 archives, caches them under `DNA_Software/Downloads` and installs them under `DNA_Software/Windows`. Allow enough room for archives and extracted runtimes. The app code is embedded in the EXE; the source ZIP is not required to launch it.

Prefer an ordinary user-writable folder, not Program Files. Keep a backup of the complete workspace. Do not disconnect the SSD during a write, analysis or WSL operation.

The Windows build is `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`, then `python DNA_Software/Launcher/public_package.py` and `python DNA_Software/Launcher/release_tools.py --target windows`.

## Linux release

Extract `DNAWorkbench-Linux-x64.zip` into a writable folder and run `./DNA-Workbench.sh`. The script opens the workspace in a local window. It does not open the system browser.

`sh DNA_Software/Launcher/build_linux.sh` creates that zip on Linux from the public file list. It does not compile `DNA_Launcher.exe`. `DNA_Software/Launcher/build_linux_appimage.sh` can also write an AppImage; that AppImage still uses the host Python and WebKitGTK.

Linux programs such as samtools, bcftools, PLINK2 Linux and Haplogrep Linux run on this host. Windows-only pins stay unused. WSL is not installed.

## ARM64 and macOS previews

- **Windows ARM64.** Extract the ARM64 ZIP and run `DNA_Launcher.exe` on Windows 11 ARM64 with WebView2 Evergreen. Core installs portable ARM64 Python. Optional WSL setup uses Ubuntu ARM64.
- **Linux ARM64.** Extract the ARM64 ZIP and run `./DNA-Workbench.sh` with native Python 3.12, GTK 3 and WebKitGTK 4.1. Install compatible native tool builds where the published x64 pins do not apply.
- **macOS.** Check the release assets for an Intel or Apple Silicon preview. Keep `DNA-Workbench.app` beside the extracted workspace files and use macOS 13 or later with Python 3.12 or later. The ZIP is an unsigned development preview.

Run `python DNA_Software/Launcher/dna_cli.py serve` for a local headless service. Run `commands` or `schema` through the same CLI to inspect available operations.

## Folder layout

| Folder beside the EXE | Contents |
|---|---|
| `Samples` | Public synthetic fixtures and checksum manifest |
| `DNA_Software/Launcher` | Extracted app modules and pinned catalogs |
| `DNA_Software/Windows` | Python, optional packages, viewers and local AI |
| `DNA_Software/Downloads` | Reusable download cache |
| `DNA_Software/UserData` | Private profile databases, settings and local control credentials |
| `Profiles/<stable ID>/Sources` | Explicitly imported provider/version sources and provenance |
| `Profiles/<stable ID>/BestDataset` | Versioned preferred variants or checked read/alignment assets |
| `Projects` | Jobs, reports and generated outputs |
| `References` | Downloaded reference data, annotations and panels |
| `DNA_Linux` | Optional WSL distribution storage |

## Optional WSL on Windows

Core does not require Ubuntu. A Linux workflow offers preparation when needed. PowerShell checks WSL host support; enabling Windows features can require elevation and reboot. The suite's distro VHDX and chosen swap location are stored beside the EXE, but distro registration and Windows features are host-specific. On a different PC, repeat the host check/registration. This is workspace portability, not a guarantee of zero host changes. Existing unrelated WSL workloads are not automatically shut down. See [portable implementation notes](../DNA_Software/Launcher/PORTABILITY.md) and [where each program runs](VERSIONS.md).

## Explore safely

Open Sample data, review its synthetic notice and load the four profiles. This is explicit and idempotent. Packaged fixtures remain intact; tiny local archive copies are made so everyone can retry the examples. Artificial samples are blocked from health, haplogroup and ancestry inference tasks.

For a real processing example, choose Alex, open Sequence tools → Inspect FASTA / FASTQ sequences, review the auto-selected inputs and start the workflow. Jobs shows its profile, status and output folder. Inspect the resulting sequence statistics; these are statistics of synthetic files, not human genome quality.

## Import your own data

Create/select the correct person, then open Batch file preparation. Select individual files or complete folders and subfolders; optionally filter file categories. Choose provider or automatic detection; inspect headers and build evidence. Unknown means unknown. Run Check files before Import. Choose move or copy explicitly. Move removes the external source only after verified destination and registration; same-name files receive numbered names, and files from external download archives are handled only after explicit selection. Private download folders can stay outside the app workspace.

Do not interrupt downloads while importing. Imputed/phased exports, report PDFs, ancestry CSVs and family JSON carry different evidence from directly measured genotypes. Do not relabel them as equivalent WGS data.

## Choose the next step

Inspect source quality and build compatibility before comparing or reconciling sources. Profile analysis is queued only when clicked. Review conflicts before generating a best selection. Generated outputs retain provenance; unknown or unresolved calls are not silently repaired. Archive originals separately. Health, ancestry and kinship workflows need appropriate input types and reference resources; see the method panel of each workflow.

## Update and troubleshoot

Versions & data lists pins and source links. The dependency UI separates availability, downloaded archives and historical checks. Keep active versions until a candidate update is checked. Public app self-updates require a configured release repository; none is configured in this prepared snapshot. If Core fails, inspect the setup log and retry repair. Do not delete personal databases as a troubleshooting shortcut.

## Combined research

In each eligible tool choose Best choice or Select multiple providers / datasets. Review the selected groups and continue; compatible child jobs reuse exact saved results. Missing prerequisites stay pending. Use Build / renew BestDataset to publish a new preferred generation explicitly. Read/alignment QC and SNP consensus are distinct products; neither is a perfect genome. See [source groups and BestDataset](SOURCE_GROUPS.md).
