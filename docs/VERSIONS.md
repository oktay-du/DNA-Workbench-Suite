# Software, reference data and model versions

Pins, archive presence, package metadata and successful execution are different evidence. No private DNA or local account paths are exported. Reference and model licenses remain separate.

Catalog snapshot: 2026-11-08 · suite 1.0.4

Large files are optional and downloaded separately. Retrieval labels are not source publication dates. Unknown sizes/checksums are intentionally left unknown.

## Where the programs run

Reference files are the same on both hosts. A program uses the same project on both hosts when that project publishes both builds. The host then uses its own file. When a project publishes only one operating system, the other host gets the named alternative. Wine is not used. `DNA_Software/Launcher/tool_hosts.py` is the source of this table.

| Pinned id | Windows | Linux | What that means |
|---|---|---|---|
| `python-windows` | native | host Python 3.12 | Windows CPython archive. Linux uses the system Python because the desktop needs GTK bindings. |
| `webview2-runtime` | native | WebKitGTK | Windows WebView2 runtime. Linux uses WebKitGTK 4.1. |
| `grampsaio-6-0-8-1-win64-exe` | native | same release, other file | Windows installer. Linux uses the official gramps_6.0.8 amd64 snap from this release. |
| `jbrowse-desktop-v4-3-0-win-exe` | native | same release, other file | Windows installer. Linux uses the official JBrowse 4.3.0 desktop AppImage. |
| `jbrowse-web-v4-3-0-zip` | browser | browser | Web bundle for both hosts. The desktop app has a separate file per host. |
| `haplogrep3-3-3-2-windows-tar-gz` | native | same release, other file | Windows Haplogrep 3.3.2. Linux uses the Linux tar from the same release. |
| `pharmcat-3-4-0-all-jar` | Java on the host | Java on the host | One jar for both hosts. Windows uses the Temurin Windows JRE. Linux uses the Temurin Linux JRE. |
| `pharmcat-pipeline-3-4-0-tar-gz` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `ubuntu-wsl` | WSL guest | not used | Windows can run a Linux-only program inside this Ubuntu image. A Linux desktop does not install WSL. |
| `igv-2-19-8` | Java on the host | Java on the host | One Java desktop zip for both hosts, with the Temurin JRE for that host. |
| `plink2-windows` | native | same release, other file | Windows PLINK 2. Linux uses the Linux zip from the same build. |
| `openjdk21u-jre-x64-windows-hotspot-21-0-13-9-zip` | native | same release, other file | Windows Temurin 21 JRE. Linux uses java21-linux from the same Adoptium release. |
| `beagle-5-5` | Java on the host | Java on the host | One jar for both hosts, with the Temurin JRE for that host. |
| `samtools-1-25-tar-bz2` | Windows bundle is 1.23.1 | native source | Official samtools 1.25 source. Linux builds it. Windows uses the Win-NGS 1.23.1 bundle because samtools publishes no Windows binary. |
| `bcftools-1-25-tar-bz2` | Windows bundle is 1.23.1 | native source | Official bcftools 1.25 source. Linux builds it. Windows uses the Win-NGS 1.23.1 bundle because bcftools publishes no Windows binary. |
| `mosdepth` | samtools depth | native | Linux static binary. mosdepth publishes no Windows build. Windows coverage uses samtools depth from the Windows samtools bundle. |
| `karchinlab-open-cravat` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `ensembl-ensembl-vep` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `gramps-project-gramps-web` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `gramps-project-gramps-web-api` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `samtools-samtools` | Windows bundle is 1.23.1 | native source | Source checkout of samtools 1.25. Same host split as the release tarball. |
| `samtools-bcftools` | Windows bundle is 1.23.1 | native source | Source checkout of bcftools 1.25. Same host split as the release tarball. |
| `apriha-snps` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `multiqc-multiqc` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `brentp-mosdepth` | samtools depth | native source | mosdepth source. The runnable file is the Linux binary. Windows uses samtools depth. |
| `browning-lab-hap-ibd` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `slowkoni-rfmix` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `23andme-yhaplo` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `pgscatalog-pgsc-calc` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `nextflow-io-nextflow` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `nf-core-sarek` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `google-deepvariant` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `uqrmaie1-admixtools` | WSL or the Windows alternative when one is pinned | native | Linux program or source build. Linux runs it on the host. Windows uses the pinned Windows file when one exists, otherwise WSL. |
| `haplogrep3-3-3-2-linux-tar-gz` | same release, other file | native | Linux Haplogrep 3.3.2. Windows uses the Windows tar from the same release. |
| `plink2-linux` | same release, other file | native | Linux PLINK 2. Windows uses the Windows zip from the same build. |
| `java21-windows` | native | same release, other file | Windows Temurin 21 JRE. Linux uses java21-linux from the same Adoptium release. |
| `nextflow-dist` | Java on the host | Java on the host | One Nextflow distribution for both hosts, with the Temurin JRE for that host. |
| `gatk-4-7-0-0` | Java on the host | Java on the host | One zip for both hosts, with the Temurin JRE for that host. |
| `ugene-53-1-windows` | native | same release, other file | Windows UGENE 53.1. Linux uses the official Linux tar from this release. |
| `gramps-6-0-8-1-amd64-snap` | same release, other file | native | Official Linux snap of Gramps 6.0.8. Windows uses the AIO installer. The snap needs snapd. |
| `jbrowse-desktop-v4-3-0-linux-appimage` | same release, other file | native | Official Linux AppImage of JBrowse desktop 4.3.0. Windows uses the exe installer. |
| `ugene-53-1-linux` | same release, other file | native | Official Linux UGENE 53.1. Windows uses the Windows zip from this release. |
| `java21-linux` | same release, other file | native | Linux Temurin 21 JRE. The SHA-256 is the publisher file from this release. Windows uses the zip. |
| `samtools-1-23-1-windows` | native alternative | official 1.25 source | Unofficial Win-NGS bundle of samtools 1.23.1 for Windows. Not an htslib release. Linux keeps the official 1.25 source. |
| `bcftools-1-23-1-windows` | native alternative | official 1.25 source | Unofficial Win-NGS bundle of bcftools 1.23.1 for Windows. Not an htslib release. Linux keeps the official 1.25 source. |

| Component | Pin / data snapshot | Category | Download size | License / source |
|---|---|---|---|---|
| [cpython-3.12.16+20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz](https://github.com/astral-sh/python-build-standalone) | 3.12.16 | core | 0.02 GiB | [See upstream / Siehe Projektquelle](https://github.com/astral-sh/python-build-standalone) |
| [Microsoft.WebView2.FixedVersionRuntime.156.0.4314.58.x64.cab](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) | 156.0.4314.58 | core | 0.29 GiB | [See upstream / Siehe Projektquelle](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |
| [GrampsAIO-6.0.8--1_win64.exe](https://github.com/gramps-project/gramps) | v6.0.8 | tools | 0.11 GiB | [GPL-2.0](https://github.com/gramps-project/gramps/blob/e9c09a44791def6a6b81079dc7f8cbe8c7e69cc0/COPYING) |
| [jbrowse-desktop-v4.3.0-win.exe](https://github.com/GMOD/jbrowse-components) | v4.3.0 | tools | 0.14 GiB | [Apache-2.0](https://github.com/GMOD/jbrowse-components/blob/6a83698a567eb4119df8afab98b3e5e32632db0f/LICENSE) |
| [jbrowse-web-v4.3.0.zip](https://github.com/GMOD/jbrowse-components) | v4.3.0 | tools | 0.02 GiB | [Apache-2.0](https://github.com/GMOD/jbrowse-components/blob/6a83698a567eb4119df8afab98b3e5e32632db0f/LICENSE) |
| [haplogrep3-3.3.2-windows.tar.gz](https://github.com/genepi/haplogrep3) | v3.3.2 | tools | 0.05 GiB | [See upstream / Siehe Projektquelle](https://github.com/genepi/haplogrep3) |
| [pharmcat-3.4.0-all.jar](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.03 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [pharmcat-pipeline-3.4.0.tar.gz](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.03 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [pharmcat_positions_3.4.0.uniallelic.vcf.bgz](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.00 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [pharmcat_positions_3.4.0.uniallelic.vcf.bgz.csi](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.00 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [pharmcat_positions_3.4.0.vcf.bgz](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.00 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [pharmcat_positions_3.4.0.vcf.bgz.csi](https://github.com/PharmGKB/PharmCAT) | v3.4.0 | tools | 0.00 GiB | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [Ubuntu-24.04-WSL](https://github.com/microsoft/WSL) | Ubuntu 24.04 LTS | linux | 0.36 GiB | [See upstream / Siehe Projektquelle](https://github.com/microsoft/WSL) |
| [IGV_2.19.8](https://igv.org/doc/desktop/DownloadPage/) | 2.19.8 | tools | 0.04 GiB | [See upstream / Siehe Projektquelle](https://igv.org/doc/desktop/DownloadPage/) |
| [PLINK2_Windows](https://www.cog-genomics.org/plink/2.0/) | b1.3-20261031 | tools | 0.01 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/) |
| [ClinVar_GRCh37](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) | retrieved-2026-11-03 | references | 0.19 GiB | [See upstream / Siehe Projektquelle](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) |
| [ClinVar_GRCh37.tbi](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) | retrieved-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) |
| [ClinVar_GRCh38](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) | retrieved-2026-11-03 | references | 0.19 GiB | [See upstream / Siehe Projektquelle](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) |
| [ClinVar_GRCh38.tbi](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) | retrieved-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) |
| [OpenJDK21U-jre_x64_windows_hotspot_21.0.13_9.zip](https://github.com/adoptium/temurin21-binaries) | jdk-21.0.13+9 | tools | 0.05 GiB | [See upstream / Siehe Projektquelle](https://github.com/adoptium/temurin21-binaries) |
| [Beagle_5.5](https://faculty.washington.edu/browning/beagle/beagle.html) | 5.5-27Feb25.75f | tools | 0.00 GiB | [See upstream / Siehe Projektquelle](https://faculty.washington.edu/browning/beagle/beagle.html) |
| [all_hg38.pgen.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 3.16 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [all_hg38_rs_noannot.pvar.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.54 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [hg38_corrected.psam](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [hgdp_statphase.pgen.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 1.61 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [hgdp_statphase.pvar.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.46 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [hgdp.psam](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [hs37d5.fa.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.69 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [GRCh38_full_analysis_set_plus_decoy_hla.fa.zst](https://www.cog-genomics.org/plink/2.0/resources) | download-snapshot-2026-11-03 | references | 0.70 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/resources) |
| [samtools-1.25.tar.bz2](https://github.com/samtools/samtools) | 1.25 | tools | 0.01 GiB | [See upstream / Siehe Projektquelle](https://github.com/samtools/samtools) |
| [bcftools-1.25.tar.bz2](https://github.com/samtools/bcftools) | 1.25 | tools | 0.01 GiB | [See upstream / Siehe Projektquelle](https://github.com/samtools/bcftools) |
| [mosdepth](https://github.com/brentp/mosdepth) | v0.3.15 | tools | 0.02 GiB | [See upstream / Siehe Projektquelle](https://github.com/brentp/mosdepth) |
| [Haplogrep_default_tree](https://github.com/genepi/phylotree-fu-rcrs) | 1.3 | references | 0.01 GiB | [See upstream / Siehe Projektquelle](https://github.com/genepi/phylotree-fu-rcrs) |
| [KarchinLab/open-cravat](https://github.com/KarchinLab/open-cravat) | 3.2.4 | sources | 0.00 GiB | [MIT](https://github.com/KarchinLab/open-cravat) |
| [Ensembl/ensembl-vep](https://github.com/Ensembl/ensembl-vep) | release/116.3 | sources | 0.06 GiB | [Apache-2.0](https://github.com/Ensembl/ensembl-vep) |
| [gramps-project/gramps-web](https://github.com/gramps-project/gramps-web) | v26.11.0 | sources | 0.00 GiB | [AGPL-3.0](https://github.com/gramps-project/gramps-web) |
| [gramps-project/gramps-web-api](https://github.com/gramps-project/gramps-web-api) | v3.25.1 | sources | 0.00 GiB | [AGPL-3.0](https://github.com/gramps-project/gramps-web-api) |
| [samtools/samtools](https://github.com/samtools/samtools) | 1.25 | sources | 0.01 GiB | [NOASSERTION](https://github.com/samtools/samtools) |
| [samtools/bcftools](https://github.com/samtools/bcftools) | 1.25 | sources | 0.00 GiB | [NOASSERTION](https://github.com/samtools/bcftools) |
| [apriha/snps](https://github.com/apriha/snps) | v2.12.1 | sources | 0.00 GiB | [BSD-3-Clause](https://github.com/apriha/snps/blob/f9a7443c3075b2187f788cf3a4c18979576f4513/LICENSE.txt) |
| [MultiQC/MultiQC](https://github.com/MultiQC/MultiQC) | v1.35 | sources | 0.01 GiB | [GPL-3.0](https://github.com/MultiQC/MultiQC) |
| [brentp/mosdepth](https://github.com/brentp/mosdepth) | v0.3.15 | sources | 0.00 GiB | [MIT](https://github.com/brentp/mosdepth) |
| [browning-lab/hap-ibd](https://github.com/browning-lab/hap-ibd) | master | sources | 0.00 GiB | [Apache-2.0](https://github.com/browning-lab/hap-ibd/blob/a3fdd2d6294903387ee29d2f67ce6260593b681f/LICENSE-2.0.txt) |
| [slowkoni/rfmix](https://github.com/slowkoni/rfmix) | master | sources | 0.00 GiB | [Stanford noncommercial academic research; separate license otherwise](https://github.com/slowkoni/rfmix/blob/09599c19c69f81571c7a7aab4cd2d847a9e0633a/README.md) |
| [23andMe/yhaplo](https://github.com/23andMe/yhaplo) | 2.1.17 | sources | 0.01 GiB | [NOASSERTION](https://github.com/23andMe/yhaplo) |
| [PGScatalog/pgsc_calc](https://github.com/PGScatalog/pgsc_calc) | v2.3.0 | sources | 0.01 GiB | [Apache-2.0](https://github.com/PGScatalog/pgsc_calc/blob/72ee54f2119d2fe65ac671327342dfc412bd0a3b/LICENSE) |
| [nextflow-io/nextflow](https://github.com/nextflow-io/nextflow) | v26.10.5 | sources | 0.01 GiB | [Apache-2.0](https://github.com/nextflow-io/nextflow) |
| [nf-core/sarek](https://github.com/nf-core/sarek) | 3.11.0 | sources | 0.01 GiB | [MIT](https://github.com/nf-core/sarek/blob/6e9b164daa2a54c98f7dda538645d340c561ac24/LICENSE) |
| [google/deepvariant](https://github.com/google/deepvariant) | v1.10.0 | sources | 0.10 GiB | [BSD-3-Clause](https://github.com/google/deepvariant) |
| [uqrmaie1/admixtools](https://github.com/uqrmaie1/admixtools) | v2.0.1 | sources | 0.06 GiB | [See upstream / Siehe Projektquelle](https://github.com/uqrmaie1/admixtools) |
| [PGS_Catalog_Metadata](https://www.pgscatalog.org/downloads/) | metadata-snapshot-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://www.pgscatalog.org/downloads/) |
| [GRCh37_to_GRCh38_chain](https://genome.ucsc.edu/) | downloaded-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://genome.ucsc.edu/) |
| [GRCh38_to_GRCh37_chain](https://genome.ucsc.edu/) | downloaded-2026-11-03 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://genome.ucsc.edu/) |
| [Beagle_map_GRCh37](https://faculty.washington.edu/browning/beagle/beagle.html) | GRCh37 | references | 0.02 GiB | [See upstream / Siehe Projektquelle](https://faculty.washington.edu/browning/beagle/beagle.html) |
| [Beagle_map_GRCh38](https://faculty.washington.edu/browning/beagle/beagle.html) | GRCh38 | references | 0.04 GiB | [See upstream / Siehe Projektquelle](https://faculty.washington.edu/browning/beagle/beagle.html) |
| [VEP_cache_116_GRCh38](https://ftp.ensembl.org/pub/current_variation/indexed_vep_cache/) | 116-GRCh38 | references | 25.75 GiB | [See upstream / Siehe Projektquelle](https://ftp.ensembl.org/pub/current_variation/indexed_vep_cache/) |
| [aadr_v66.p1__README.docx](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [v66.p1_1240K.aadr.patch.PUB.geno](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 6.63 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [v66.p1_1240K.aadr.patch.PUB.ind](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [v66.p1_1240K.aadr.patch.PUB.snp](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 0.07 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [v66.p1_1240K.aadr.PUB.anno](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 0.01 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [v66.p1__files.md5sum](https://doi.org/10.7910/DVN/FFIDCW) | Dataverse-v14-AADR-v66.p1 | references | 0.00 GiB | [See upstream / Siehe Projektquelle](https://doi.org/10.7910/DVN/FFIDCW) |
| [haplogrep3-3.3.2-linux.tar.gz](https://github.com/genepi/haplogrep3/releases/download/v3.3.2/haplogrep3-3.3.2-linux.tar.gz) | Unknown / Unbekannt | tools | 0.05 GiB | [See upstream / Siehe Projektquelle](https://github.com/genepi/haplogrep3/releases/download/v3.3.2/haplogrep3-3.3.2-linux.tar.gz) |
| [plink2_linux_x86_64_20261031.zip](https://www.cog-genomics.org/plink/2.0/) | b1.3-20261031 | tools | 0.01 GiB | [See upstream / Siehe Projektquelle](https://www.cog-genomics.org/plink/2.0/) |
| [OpenJDK21U-jre_x64_windows_hotspot_21.0.13_9.zip](https://github.com/adoptium/temurin21-binaries) | 21.0.13+9.0.LTS | tools | 0.05 GiB | [See upstream / Siehe Projektquelle](https://github.com/adoptium/temurin21-binaries) |
| [nextflow-26.10.5-dist](https://github.com/nextflow-io/nextflow) | 26.10.5 | pipelines | 0.05 GiB | [Apache-2.0](https://github.com/nextflow-io/nextflow) |
| [gatk-4.7.0.0.zip](https://github.com/broadinstitute/gatk) | 4.7.0.0 | tools | 0.65 GiB | [Apache-2.0](https://github.com/broadinstitute/gatk/blob/0cde69eed30339f5978cbb1ac6e5cf3662f9e1f8/LICENSE.TXT) |
| [ugene-53.1-win-x86-64.zip](https://github.com/ugeneunipro/ugene) | 53.1 | tools | 0.35 GiB | [GPL-2.0](https://github.com/ugeneunipro/ugene/blob/559b098575cd281e30f86ff72a5ceea065a700bd/LICENSE.txt) |
| [gramps_6.0.8-1_amd64.snap](https://github.com/gramps-project/gramps) | v6.0.8 | tools | 0.09 GiB | [GPL-2.0](https://github.com/gramps-project/gramps/blob/e9c09a44791def6a6b81079dc7f8cbe8c7e69cc0/COPYING) |
| [jbrowse-desktop-v4.3.0-linux.AppImage](https://github.com/GMOD/jbrowse-components) | v4.3.0 | tools | 0.11 GiB | [Apache-2.0](https://github.com/GMOD/jbrowse-components/blob/6a83698a567eb4119df8afab98b3e5e32632db0f/LICENSE) |
| [ugene-53.1-linux-x86-64.tar.gz](https://github.com/ugeneunipro/ugene) | 53.1 | tools | 0.47 GiB | [GPL-2.0](https://github.com/ugeneunipro/ugene/blob/559b098575cd281e30f86ff72a5ceea065a700bd/LICENSE.txt) |
| [OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz](https://github.com/adoptium/temurin21-binaries) | 21.0.13+9 | tools | 0.05 GiB | [See upstream / Siehe Projektquelle](https://github.com/adoptium/temurin21-binaries) |
| [samtools-1.23.1-windows-ucrt64.zip](https://github.com/win-ngs/samtools-windows-bundle) | 1.23.1 | tools | 0.01 GiB | [MIT](https://github.com/samtools/samtools) |
| [bcftools-1.23.1-windows-ucrt64.zip](https://github.com/win-ngs/bcftools-windows-bundle) | 1.23.1 | tools | 0.02 GiB | [MIT](https://github.com/samtools/bcftools) |
| [@genome-spy/core](https://github.com/genome-spy/genome-spy) | 1.2.0 | visualization | Unknown | [MIT](https://github.com/genome-spy/genome-spy) |
| [igv](https://github.com/igvteam/igv.js) | 3.8.10 | visualization | Unknown | [MIT](https://github.com/igvteam/igv.js) |
| [jbrowse](https://github.com/GMOD/jbrowse-components) | 4.3.0 | visualization | Unknown | [Apache-2.0](https://github.com/GMOD/jbrowse-components) |
| [pygenomeviz](https://github.com/moshi4/pyGenomeViz) | 1.7.0 | visualization | Unknown | [MIT](https://github.com/moshi4/pyGenomeViz) |
| [pycirclize](https://github.com/moshi4/pyCirclize) | 1.10.1 | visualization | Unknown | [MIT](https://github.com/moshi4/pyCirclize) |
| [dna_features_viewer](https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer) | 3.1.5 | visualization | Unknown | [MIT](https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer) |
| [seqviz](https://github.com/Lattice-Automation/seqviz) | 3.10.25 | visualization | Unknown | [MIT](https://github.com/Lattice-Automation/seqviz) |
| [ctranslate2](https://pypi.org/project/ctranslate2/) | 4.8.5 | document translation runtime | 0.02 GiB | [MIT](https://pypi.org/project/ctranslate2/) |
| [sentencepiece](https://pypi.org/project/sentencepiece/) | 0.2.2 | document translation runtime | 0.00 GiB | [Apache-2.0](https://pypi.org/project/sentencepiece/) |
| [numpy](https://pypi.org/project/numpy/) | 2.5.4 | document translation runtime | 0.01 GiB | [BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0](https://pypi.org/project/numpy/) |
| [PyYAML](https://pypi.org/project/PyYAML/) | 6.0.3 | document translation runtime | 0.00 GiB | [See upstream](https://pypi.org/project/PyYAML/) |
| [argostranslate](https://pypi.org/project/argostranslate/) | 1.11.0 | document translation runtime | 0.00 GiB | [See official distribution license](https://pypi.org/project/argostranslate/) |
| [sacremoses](https://pypi.org/project/sacremoses/) | 0.2.0 | document translation runtime | 0.00 GiB | [See official distribution license](https://pypi.org/project/sacremoses/) |
| [click](https://pypi.org/project/click/) | 8.5.0 | document translation runtime | 0.00 GiB | [BSD-3-Clause](https://pypi.org/project/click/) |
| [joblib](https://pypi.org/project/joblib/) | 1.6.0 | document translation runtime | 0.00 GiB | [BSD-3-Clause](https://pypi.org/project/joblib/) |
| [regex](https://pypi.org/project/regex/) | 2026.9.29 | document translation runtime | 0.00 GiB | [Apache-2.0 AND CNRI-Python](https://pypi.org/project/regex/) |
| [tqdm](https://pypi.org/project/tqdm/) | 4.70.1 | document translation runtime | 0.00 GiB | [See official distribution license](https://pypi.org/project/tqdm/) |
| [colorama](https://pypi.org/project/colorama/) | 0.4.6 | document translation runtime | 0.00 GiB | [See official distribution license](https://pypi.org/project/colorama/) |
| [cloudpickle](https://pypi.org/project/cloudpickle/) | 3.1.2 | document translation runtime | 0.00 GiB | [See distribution license](https://pypi.org/project/cloudpickle/) |
| [Argos ar to en](https://github.com/argosopentech/argospm-index) | 1.0 | offline translation model (disabled) | 0.08 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos en to de](https://github.com/argosopentech/argospm-index) | 1.3 | offline translation model | 0.14 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos fr to en](https://github.com/argosopentech/argospm-index) | 1.9 | offline translation model | 0.06 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos de to en](https://github.com/argosopentech/argospm-index) | 1.3 | offline translation model | 0.14 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos pl to en](https://github.com/argosopentech/argospm-index) | 1.9 | offline translation model | 0.07 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos ru to en](https://github.com/argosopentech/argospm-index) | 1.9 | offline translation model | 0.15 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos es to en](https://github.com/argosopentech/argospm-index) | 1.9 | offline translation model | 0.27 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [Argos tr to en](https://github.com/argosopentech/argospm-index) | 1.5 | offline translation model | 0.11 GiB | [See model package/upstream terms; weights are not redistributed](https://github.com/argosopentech/argospm-index) |
| [llama.cpp CPU runtime](https://github.com/ggml-org/llama.cpp) | b12068 | optional-ai | Unknown | [MIT](https://github.com/ggml-org/llama.cpp) |
| [Qwen3-0.6B · Q8_0](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF) | 23749fefcc72300e3a2ad315e1317431b06b590a | optional-ai | 0.60 GiB | [Apache-2.0](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF) |

## Python distribution inventory

Versions below were read from this installation’s distribution metadata. They are an environment snapshot, not a required bundled installation or proof that every package was exercised.

| Package | Version | Declared license |
|---|---|---|
| [annotated-types](https://pypi.org/project/annotated-types/) | 0.8.0 | MIT |
| [anyio](https://pypi.org/project/anyio/) | 4.16.0 | MIT |
| [argon2-cffi](https://pypi.org/project/argon2-cffi/) | 25.1.0 | MIT |
| [argon2-cffi-bindings](https://pypi.org/project/argon2-cffi-bindings/) | 26.1.0 | MIT |
| [argostranslate](https://pypi.org/project/argostranslate/) | 1.11.0 | UNKNOWN |
| [arrow](https://pypi.org/project/arrow/) | 1.4.0 | See distribution license |
| [asttokens](https://pypi.org/project/asttokens/) | 3.0.2 | Apache 2.0 |
| [async-lru](https://pypi.org/project/async-lru/) | 2.4.0 | MIT License |
| [atomicwrites](https://pypi.org/project/atomicwrites/) | 1.4.1 | MIT |
| [attrs](https://pypi.org/project/attrs/) | 26.1.0 | MIT |
| [babel](https://pypi.org/project/babel/) | 2.18.0 | BSD-3-Clause |
| [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) | 4.15.0 | MIT License |
| [biopython](https://pypi.org/project/biopython/) | 1.88 | LicenseRef-Biopython-License-Agreement |
| [bleach](https://pypi.org/project/bleach/) | 6.4.0 | Apache Software License |
| [boto3](https://pypi.org/project/boto3/) | 1.43.123 | Apache-2.0 |
| [botocore](https://pypi.org/project/botocore/) | 1.43.123 | Apache-2.0 |
| [certifi](https://pypi.org/project/certifi/) | 2026.10.23 | MPL-2.0 |
| [cffi](https://pypi.org/project/cffi/) | 2.1.1 | MIT-0 |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/) | 3.5.2 | MIT |
| [click](https://pypi.org/project/click/) | 8.5.0 | BSD-3-Clause |
| [cloudpickle](https://pypi.org/project/cloudpickle/) | 3.1.2 | BSD-3-Clause |
| [colorama](https://pypi.org/project/colorama/) | 0.4.6 | See distribution license |
| [coloredlogs](https://pypi.org/project/coloredlogs/) | 15.0.1 | MIT |
| [colormath2](https://pypi.org/project/colormath2/) | 3.0.3 | BSD-3-Clause |
| [comm](https://pypi.org/project/comm/) | 0.2.3 | See distribution license |
| [ctranslate2](https://pypi.org/project/ctranslate2/) | 4.8.5 | MIT |
| [debugpy](https://pypi.org/project/debugpy/) | 1.8.22 | MIT |
| [defusedxml](https://pypi.org/project/defusedxml/) | 0.7.1 | PSFL |
| [executing](https://pypi.org/project/executing/) | 2.3.0 | MIT |
| [fastjsonschema](https://pypi.org/project/fastjsonschema/) | 2.22.3 | BSD-3-Clause |
| [fqdn](https://pypi.org/project/fqdn/) | 1.6.0 | MPL-2.0 |
| [h11](https://pypi.org/project/h11/) | 0.16.0 | MIT |
| [httpcore](https://pypi.org/project/httpcore/) | 1.0.9 | BSD-3-Clause |
| [httpx](https://pypi.org/project/httpx/) | 0.28.1 | BSD-3-Clause |
| [humanfriendly](https://pypi.org/project/humanfriendly/) | 10.0 | MIT |
| [humanize](https://pypi.org/project/humanize/) | 4.16.0 | MIT |
| [idna](https://pypi.org/project/idna/) | 3.20 | BSD-3-Clause |
| [importlib_metadata](https://pypi.org/project/importlib_metadata/) | 10.1.0 | Apache-2.0 |
| [ipykernel](https://pypi.org/project/ipykernel/) | 7.4.0 | BSD-3-Clause |
| [ipython](https://pypi.org/project/ipython/) | 9.18.1 | BSD-3-Clause |
| [ipython_pygments_lexers](https://pypi.org/project/ipython_pygments_lexers/) | 1.1.1 | See distribution license |
| [isoduration](https://pypi.org/project/isoduration/) | 20.11.0 | UNKNOWN |
| [jedi](https://pypi.org/project/jedi/) | 0.20.1 | MIT |
| [Jinja2](https://pypi.org/project/Jinja2/) | 3.1.6 | See distribution license |
| [jmespath](https://pypi.org/project/jmespath/) | 1.1.0 | MIT |
| [joblib](https://pypi.org/project/joblib/) | 1.6.0 | BSD-3-Clause |
| [json5](https://pypi.org/project/json5/) | 0.17.3 | Apache-2.0 |
| [jsonpointer](https://pypi.org/project/jsonpointer/) | 3.8 | Modified BSD License |
| [jsonschema](https://pypi.org/project/jsonschema/) | 4.26.0 | MIT |
| [jsonschema-specifications](https://pypi.org/project/jsonschema-specifications/) | 2025.9.1 | MIT |
| [jupyter-events](https://pypi.org/project/jupyter-events/) | 0.12.1 | See distribution license |
| [jupyter-lsp](https://pypi.org/project/jupyter-lsp/) | 2.3.1 | BSD-3-Clause |
| [jupyter_builder](https://pypi.org/project/jupyter_builder/) | 1.2.4 | Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MIT |
| [jupyter_client](https://pypi.org/project/jupyter_client/) | 8.10.0 | See distribution license |
| [jupyter_core](https://pypi.org/project/jupyter_core/) | 5.9.1 | BSD-3-Clause |
| [jupyter_server](https://pypi.org/project/jupyter_server/) | 2.21.1 | See distribution license |
| [jupyter_server_terminals](https://pypi.org/project/jupyter_server_terminals/) | 0.5.4 | See distribution license |
| [jupyterlab](https://pypi.org/project/jupyterlab/) | 4.6.5 | See distribution license |
| [jupyterlab_pygments](https://pypi.org/project/jupyterlab_pygments/) | 0.3.0 | See distribution license |
| [jupyterlab_server](https://pypi.org/project/jupyterlab_server/) | 2.28.1 | See distribution license |
| [kaleido](https://pypi.org/project/kaleido/) | 0.2.1 | MIT |
| [lark](https://pypi.org/project/lark/) | 1.3.1 | MIT |
| [manifold3d](https://pypi.org/project/manifold3d/) | 3.5.4 | See distribution license |
| [Markdown](https://pypi.org/project/Markdown/) | 3.11.2 | BSD-3-Clause |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/) | 4.2.0 | See distribution license |
| [MarkupSafe](https://pypi.org/project/MarkupSafe/) | 3.0.4 | BSD-3-Clause |
| [matplotlib-inline](https://pypi.org/project/matplotlib-inline/) | 0.2.2 | BSD-3-Clause |
| [mdurl](https://pypi.org/project/mdurl/) | 0.1.2 | See distribution license |
| [mistune](https://pypi.org/project/mistune/) | 3.4.0 | BSD-3-Clause |
| [multiqc](https://pypi.org/project/multiqc/) | 1.35 | See distribution license |
| [narwhals](https://pypi.org/project/narwhals/) | 2.28.0 | MIT |
| [natsort](https://pypi.org/project/natsort/) | 8.4.0 | MIT |
| [nbclient](https://pypi.org/project/nbclient/) | 0.11.0 | See distribution license |
| [nbconvert](https://pypi.org/project/nbconvert/) | 7.17.2 | See distribution license |
| [nbformat](https://pypi.org/project/nbformat/) | 5.11.1 | See distribution license |
| [nest-asyncio2](https://pypi.org/project/nest-asyncio2/) | 1.7.4 | BSD |
| [networkx](https://pypi.org/project/networkx/) | 3.7 | BSD-3-Clause |
| [notebook_shim](https://pypi.org/project/notebook_shim/) | 0.2.4 | See distribution license |
| [numpy](https://pypi.org/project/numpy/) | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| [packaging](https://pypi.org/project/packaging/) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [pandas](https://pypi.org/project/pandas/) | 3.1.0 | BSD-3-Clause |
| [pandocfilters](https://pypi.org/project/pandocfilters/) | 1.5.1 | BSD-3-Clause |
| [parso](https://pypi.org/project/parso/) | 0.8.7 | MIT |
| [pillow](https://pypi.org/project/pillow/) | 13.0.0 | MIT-CMU |
| [platformdirs](https://pypi.org/project/platformdirs/) | 4.14.3 | MIT |
| [plotly](https://pypi.org/project/plotly/) | 7.1.0 | MIT |
| [polars](https://pypi.org/project/polars/) | 2.1.0 | See distribution license |
| [polars-runtime-32](https://pypi.org/project/polars-runtime-32/) | 2.1.0 | See distribution license |
| [polars-runtime-compat](https://pypi.org/project/polars-runtime-compat/) | 2.1.0 | See distribution license |
| [prometheus_client](https://pypi.org/project/prometheus_client/) | 0.26.0 | Apache-2.0 AND BSD-2-Clause |
| [prompt_toolkit](https://pypi.org/project/prompt_toolkit/) | 3.0.53 | See distribution license |
| [psutil](https://pypi.org/project/psutil/) | 7.2.2 | BSD-3-Clause |
| [pure_eval](https://pypi.org/project/pure_eval/) | 0.2.4 | MIT |
| [pyarrow](https://pypi.org/project/pyarrow/) | 26.0.0 | Apache-2.0 |
| [pycparser](https://pypi.org/project/pycparser/) | 3.12 | BSD-3-Clause |
| [pydantic](https://pypi.org/project/pydantic/) | 2.14.2 | MIT |
| [pydantic_core](https://pypi.org/project/pydantic_core/) | 2.50.2 | MIT |
| [pyfastx](https://pypi.org/project/pyfastx/) | 2.3.1 | MIT |
| [Pygments](https://pypi.org/project/Pygments/) | 2.21.0 | BSD-2-Clause |
| [pyliftover](https://pypi.org/project/pyliftover/) | 0.4.1 | MIT |
| [pypdf](https://pypi.org/project/pypdf/) | 6.21.4 | BSD-3-Clause |
| [pyreadline3](https://pypi.org/project/pyreadline3/) | 3.5.6 | BSD |
| [python-dateutil](https://pypi.org/project/python-dateutil/) | 2.9.0.post0 | Dual License |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | 1.2.4 | BSD-3-Clause |
| [python-json-logger](https://pypi.org/project/python-json-logger/) | 4.2.0 | BSD-2-Clause |
| [pywinpty](https://pypi.org/project/pywinpty/) | 3.1.2 | See distribution license |
| [PyYAML](https://pypi.org/project/PyYAML/) | 6.0.3 | MIT |
| [pyzmq](https://pypi.org/project/pyzmq/) | 27.2.0 | BSD-3-Clause |
| [referencing](https://pypi.org/project/referencing/) | 0.37.0 | MIT |
| [regex](https://pypi.org/project/regex/) | 2026.9.29 | Apache-2.0 AND CNRI-Python |
| [reportlab](https://pypi.org/project/reportlab/) | 5.1.0 | BSD license (see license.txt for details), Copyright (c) 2000-2025, ReportLab Inc. |
| [requests](https://pypi.org/project/requests/) | 2.34.2 | Apache-2.0 |
| [rfc3339-validator](https://pypi.org/project/rfc3339-validator/) | 0.1.4 | MIT license |
| [rfc3986-validator](https://pypi.org/project/rfc3986-validator/) | 0.1.1 | MIT license |
| [rfc3987-syntax](https://pypi.org/project/rfc3987-syntax/) | 1.1.0 | MIT |
| [rich](https://pypi.org/project/rich/) | 15.0.0 | MIT |
| [rich-click](https://pypi.org/project/rich-click/) | 1.9.9 | See distribution license |
| [rpds-py](https://pypi.org/project/rpds-py/) | 2026.9.1 | MIT |
| [s3transfer](https://pypi.org/project/s3transfer/) | 0.19.3 | Apache License 2.0 |
| [sacremoses](https://pypi.org/project/sacremoses/) | 0.2.0 | See distribution license |
| [scipy](https://pypi.org/project/scipy/) | 1.18.1 | See distribution license |
| [Send2Trash](https://pypi.org/project/Send2Trash/) | 2.1.0 | BSD-3-Clause |
| [sentencepiece](https://pypi.org/project/sentencepiece/) | 0.2.2 | Apache-2.0 |
| [six](https://pypi.org/project/six/) | 1.17.0 | MIT |
| [snps](https://pypi.org/project/snps/) | 2.12.1 | BSD 3-Clause License |
| [soupsieve](https://pypi.org/project/soupsieve/) | 3.0.4 | MIT |
| [spectra](https://pypi.org/project/spectra/) | 0.1.0 | MIT |
| [stack-data](https://pypi.org/project/stack-data/) | 0.6.3 | MIT |
| [terminado](https://pypi.org/project/terminado/) | 0.18.1 | See distribution license |
| [tiktoken](https://pypi.org/project/tiktoken/) | 0.14.0 | See distribution license |
| [tinycss2](https://pypi.org/project/tinycss2/) | 1.5.1 | See distribution license |
| [tornado](https://pypi.org/project/tornado/) | 6.6 | Apache-2.0 |
| [tqdm](https://pypi.org/project/tqdm/) | 4.70.1 | MPL-2.0 AND MIT |
| [traitlets](https://pypi.org/project/traitlets/) | 5.16.1 | See distribution license |
| [typeguard](https://pypi.org/project/typeguard/) | 4.6.0 | MIT |
| [typing-inspection](https://pypi.org/project/typing-inspection/) | 0.4.4 | MIT |
| [typing_extensions](https://pypi.org/project/typing_extensions/) | 4.16.0 | PSF-2.0 |
| [tzdata](https://pypi.org/project/tzdata/) | 2026.6 | Apache-2.0 |
| [uri-template](https://pypi.org/project/uri-template/) | 1.3.0 | MIT License |
| [urllib3](https://pypi.org/project/urllib3/) | 2.8.0 | MIT |
| [wcwidth](https://pypi.org/project/wcwidth/) | 0.9.4 | See distribution license |
| [webcolors](https://pypi.org/project/webcolors/) | 25.10.0 | BSD-3-Clause |
| [webencodings](https://pypi.org/project/webencodings/) | 0.6.1 | See distribution license |
| [websocket-client](https://pypi.org/project/websocket-client/) | 1.9.2 | Apache-2.0 |
| [zipp](https://pypi.org/project/zipp/) | 4.1.2 | MIT |
