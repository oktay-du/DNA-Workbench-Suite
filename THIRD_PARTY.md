# Third-party components

Included components retain their listed licenses, copyright notices and permissions. See docs/LICENSING.md for component scope.

- Design workflow reference: Mustafa Kendigüzel, `claude-code-ui-agents`, MIT, copyright 2025. Retained notice: `DNA_Software/Launcher/Notices/UI-PROMPTS-LICENSE.txt`.

- Microsoft WebView2 SDK / Fixed Version Runtime: Microsoft terms. Official packages are downloaded from NuGet and Microsoft; SDK license files travel with the embedded payload. Runtime CAB and its license files remain separate.
- Natural Earth land outlines: public domain. Source and archive SHA-256 are in world-land.json.
- Language picker flags: [flag-icons 7.6.0](https://github.com/lipis/flag-icons), MIT. The notice is included at `DNA_Software/Launcher/Notices/FLAG-ICONS-LICENSE.txt`.
- Heritage place names: Unicode CLDR, Unicode License v3; notice in Notices/UNICODE-LICENSE.txt. The German culture summaries and decorative patterns are our own text/design.
- Heritage photographs: individual Creative Commons/public-domain terms apply. Titles, authors, source pages, license links and SHA-256 are retained in heritage-images.json and shown next to each image. They are not relicensed under our project licenses.
- Python / python-build-standalone: PSF and included component licenses; distributed as an unmodified official archive downloaded by the installer.
- Ubuntu and Debian packages: respective package licenses and sources, downloaded through official repositories.
- SAMtools, BCFtools, PLINK, OpenCRAVAT, VEP, Gramps and other optional projects: see their source projects and versioned download manifest. Source archives are not bundled as our own code.
- RFMix is free for academic research use only; other use requires a separate Stanford license. It is excluded from unattended installation and generic update downloads. The explicit optional installer requires the user to review and affirm eligibility; that declaration does not grant a license. The required notice is retained in DNA_Software/Launcher/Notices/RFMIX-LICENSE.txt.
- ClinVar, gnomAD, 1000 Genomes, HGDP, AADR and other references have distinct data-use, attribution and redistribution terms. Download availability is not proof of unrestricted redistribution. Obtain directly from original providers and retain metadata.

Before a public binary release, complete the third-party license inventory and test installation on a clean supported Windows host. No commercial-provider reports, private genotypes or account data belong in this repository.

- Visualization adapters use separately installed GenomeSpy (MIT), IGV.js (MIT), JBrowse (Apache-2.0), pyGenomeViz (MIT), pyCirclize (MIT) and DNA Features Viewer (MIT). Upstream package notices remain with their installations.
- Peddy (MIT), WhatsHap (MIT), Truvari (MIT), Sarek (MIT), PGS Calculator (Apache-2.0), PharmCAT (MPL-2.0), Gramps (GPL-2.0) and the other audited projects remain separate components. The project license policy does not replace their obligations. See project-audit.json for source/license links and pinned research commits.
- peddy_compat.py applies a documented, hash-guarded one-line NumPy API compatibility change to Peddy 0.4.8 while preserving its MIT notice and original-file backup. No complete third-party source archive is included in this app package.

- Optional PyLiftover 0.4.1 (MIT) is installed separately with pinned distribution hashes for point-coordinate mapping. No chain files or personal DNA are bundled. The adapter is limited to observed SNP genotypes; see PROFILE_PIPELINE.md.

## Project source and license index

The list includes integrated adapters and researched optional projects. Listing is not proof of installation, validation or redistribution permission. Full upstream source archives are not bundled.

| Project | Pinned research commit | Declared license |
|---|---|---|
| [genome-spy/genome-spy](https://github.com/genome-spy/genome-spy) | `482e9a1d42d5b6bb1c293737a9cf0b647f229f3e` | [MIT](https://github.com/genome-spy/genome-spy/blob/482e9a1d42d5b6bb1c293737a9cf0b647f229f3e/LICENSE) |
| [igvteam/igv.js](https://github.com/igvteam/igv.js) | `b5d64807ee940a2eaf9a64b093f71445e9a3c620` | [MIT](https://github.com/igvteam/igv.js/blob/b5d64807ee940a2eaf9a64b093f71445e9a3c620/LICENSE) |
| [GMOD/jbrowse-components](https://github.com/GMOD/jbrowse-components) | `6a83698a567eb4119df8afab98b3e5e32632db0f` | [Apache-2.0](https://github.com/GMOD/jbrowse-components/blob/6a83698a567eb4119df8afab98b3e5e32632db0f/LICENSE) |
| [moshi4/pyGenomeViz](https://github.com/moshi4/pyGenomeViz) | `fb137ded78d56b1d55229309d500aa54c80e3abe` | [MIT](https://github.com/moshi4/pyGenomeViz/blob/fb137ded78d56b1d55229309d500aa54c80e3abe/LICENSE) |
| [moshi4/pyCirclize](https://github.com/moshi4/pyCirclize) | `5a0f36111a4bbfab3e3d765e7365a1108f891dcb` | [MIT](https://github.com/moshi4/pyCirclize/blob/5a0f36111a4bbfab3e3d765e7365a1108f891dcb/LICENSE) |
| [Edinburgh-Genome-Foundry/DnaFeaturesViewer](https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer) | `049bbe4e3063e90ae9b0f88ac7e92f47b735d38a` | [MIT](https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer/blob/049bbe4e3063e90ae9b0f88ac7e92f47b735d38a/LICENSE) |
| [apriha/snps](https://github.com/apriha/snps) | `f9a7443c3075b2187f788cf3a4c18979576f4513` | [BSD-3-Clause](https://github.com/apriha/snps/blob/f9a7443c3075b2187f788cf3a4c18979576f4513/LICENSE.txt) |
| [brentp/peddy](https://github.com/brentp/peddy) | `1d340cd3e87623c8c58b4a82b18f33ba532101aa` | [MIT](https://github.com/brentp/peddy/blob/1d340cd3e87623c8c58b4a82b18f33ba532101aa/LICENSE) |
| [whatshap/whatshap](https://github.com/whatshap/whatshap) | `6697f41d3ae41d616a4daffb8116ad5bb364a0b1` | [MIT](https://github.com/whatshap/whatshap/blob/6697f41d3ae41d616a4daffb8116ad5bb364a0b1/LICENSE) |
| [ACEnglish/truvari](https://github.com/ACEnglish/truvari) | `c3a59e59bff81559d6e9f45062c3c8e29589cec3` | [MIT](https://github.com/ACEnglish/truvari/blob/c3a59e59bff81559d6e9f45062c3c8e29589cec3/LICENSE) |
| [nf-core/sarek](https://github.com/nf-core/sarek) | `6e9b164daa2a54c98f7dda538645d340c561ac24` | [MIT](https://github.com/nf-core/sarek/blob/6e9b164daa2a54c98f7dda538645d340c561ac24/LICENSE) |
| [PGScatalog/pgsc_calc](https://github.com/PGScatalog/pgsc_calc) | `72ee54f2119d2fe65ac671327342dfc412bd0a3b` | [Apache-2.0](https://github.com/PGScatalog/pgsc_calc/blob/72ee54f2119d2fe65ac671327342dfc412bd0a3b/LICENSE) |
| [PharmGKB/PharmCAT](https://github.com/PharmGKB/PharmCAT) | `8e6f81b9372da54f9281d452cd171253c6a8974f` | [MPL-2.0](https://github.com/PharmGKB/PharmCAT/blob/8e6f81b9372da54f9281d452cd171253c6a8974f/LICENSE) |
| [browning-lab/hap-ibd](https://github.com/browning-lab/hap-ibd) | `a3fdd2d6294903387ee29d2f67ce6260593b681f` | [Apache-2.0](https://github.com/browning-lab/hap-ibd/blob/a3fdd2d6294903387ee29d2f67ce6260593b681f/LICENSE-2.0.txt) |
| [slowkoni/rfmix](https://github.com/slowkoni/rfmix) | `09599c19c69f81571c7a7aab4cd2d847a9e0633a` | [Stanford noncommercial academic research; separate license otherwise](https://github.com/slowkoni/rfmix/blob/09599c19c69f81571c7a7aab4cd2d847a9e0633a/README.md) |
| [gramps-project/gramps](https://github.com/gramps-project/gramps) | `e9c09a44791def6a6b81079dc7f8cbe8c7e69cc0` | [GPL-2.0](https://github.com/gramps-project/gramps/blob/e9c09a44791def6a6b81079dc7f8cbe8c7e69cc0/COPYING) |
| [ablab/mgra](https://github.com/ablab/mgra) | `fb8125f5a507e3b169e89cedd6842a564e222001` | [GPL-2.0](https://github.com/ablab/mgra/blob/fb8125f5a507e3b169e89cedd6842a564e222001/LICENSE) |
| [fenderglass/Ragout](https://github.com/fenderglass/Ragout) | `5f2caaeaf935db6e01aae68ba8b93c46ddf18f10` | [NOASSERTION](https://github.com/fenderglass/Ragout/blob/5f2caaeaf935db6e01aae68ba8b93c46ddf18f10/LICENSE) |
| [Jerrythafast/FDSTools](https://github.com/Jerrythafast/FDSTools) | `5cad6d057fd2f16bd77f9aa2420e920ccfcc7aa6` | [GPL-3.0](https://github.com/Jerrythafast/FDSTools/tree/5cad6d057fd2f16bd77f9aa2420e920ccfcc7aa6) |
| [LANL-Bioinformatics/MeGAMerge](https://github.com/LANL-Bioinformatics/MeGAMerge) | `616ed05b2b3d117a4407b5a8927dc1ab9b44a1f1` | [Check upstream license files separately ](https://github.com/LANL-Bioinformatics/MeGAMerge/tree/616ed05b2b3d117a4407b5a8927dc1ab9b44a1f1) |]
| [biopython/biopython](https://github.com/biopython/biopython) | `49fefbc675e08f3ab6741896d08397952ce4dd9c` | [Biopython License Agreement / teilweise BSD-3-Clause](https://github.com/biopython/biopython/blob/49fefbc675e08f3ab6741896d08397952ce4dd9c/LICENSE.rst) |
| [broadinstitute/gatk](https://github.com/broadinstitute/gatk) | `0cde69eed30339f5978cbb1ac6e5cf3662f9e1f8` | [Apache-2.0](https://github.com/broadinstitute/gatk/blob/0cde69eed30339f5978cbb1ac6e5cf3662f9e1f8/LICENSE.TXT) |
| [galaxyproject/galaxy](https://github.com/galaxyproject/galaxy) | `66760b892698397b0558a28ba168298179ed0444` | [Check upstream license files separately ](https://github.com/galaxyproject/galaxy/tree/66760b892698397b0558a28ba168298179ed0444) |]
| [vgteam/vg](https://github.com/vgteam/vg) | `453e6c01bb412186eaa948fd1bb413d45c089f0e` | [Check upstream and third-party components separately ](https://github.com/vgteam/vg/tree/453e6c01bb412186eaa948fd1bb413d45c089f0e) |]
| [dib-lab/khmer](https://github.com/dib-lab/khmer) | `fb65d21eaedf0d397d49ae3debc578897f9d6eb4` | [Check upstream license files separately ](https://github.com/dib-lab/khmer/tree/fb65d21eaedf0d397d49ae3debc578897f9d6eb4) |]
| [bowang-lab/BioReason](https://github.com/bowang-lab/BioReason) | `684ff7c09eb1d65e70925c114a7a05a1fcc0403f` | [Apache-2.0; test model weights separately](https://github.com/bowang-lab/BioReason/tree/684ff7c09eb1d65e70925c114a7a05a1fcc0403f) |]
| [songlab-cal/gpn](https://github.com/songlab-cal/gpn) | `dc5fd287599f2955a79d010bca0e0f7f8178c67e` | [MIT; test model weights separately ](https://github.com/songlab-cal/gpn/tree/dc5fd287599f2955a79d010bca0e0f7f8178c67e) |]
| [Lattice-Automation/seqviz](https://github.com/Lattice-Automation/seqviz) | `7a0e8f4c45ad5f4d076178f54f08f071e91d7b6a` | [MIT](https://github.com/Lattice-Automation/seqviz/blob/7a0e8f4c45ad5f4d076178f54f08f071e91d7b6a/LICENSE) |
| [samtools/htsjdk](https://github.com/samtools/htsjdk) | `3b92d7b7bbb7046828627dc203a220f9fa560d77` | [Check upstream license files separately ](https://github.com/samtools/htsjdk/tree/3b92d7b7bbb7046828627dc203a220f9fa560d77) |]
| [lmdu/pyfastx](https://github.com/lmdu/pyfastx) | `7d82c66b1f5d079d6b7d46f878d156cbaa6c01aa` | [MIT](https://github.com/lmdu/pyfastx/blob/7d82c66b1f5d079d6b7d46f878d156cbaa6c01aa/LICENSE) |
| [ugeneunipro/ugene](https://github.com/ugeneunipro/ugene) | `559b098575cd281e30f86ff72a5ceea065a700bd` | [GPL-2.0](https://github.com/ugeneunipro/ugene/blob/559b098575cd281e30f86ff72a5ceea065a700bd/LICENSE.txt) |
| [guigolab/tmerge](https://github.com/guigolab/tmerge) | `5f9dee7d262913ca481716c2845d6e1b12c7bec7` | [MIT](https://github.com/guigolab/tmerge/tree/5f9dee7d262913ca481716c2845d6e1b12c7bec7) |
| [uio-bmi/NucMerge](https://github.com/uio-bmi/NucMerge) | `0f1f76d20e9e3f6a1642162f150f8eb36e4c41af` | [MPL-2.0](https://github.com/uio-bmi/NucMerge/tree/0f1f76d20e9e3f6a1642162f150f8eb36e4c41af) |
| [bawee/merge-genbank](https://github.com/bawee/merge-genbank) | `021e53300ce4e4d60e4462e1c2e38e2fc1ad95e3` | [Unclear](https://github.com/bawee/merge-genbank/tree/021e53300ce4e4d60e4462e1c2e38e2fc1ad95e3) |]
| [CodeX-HL7-FHIR-Accelerator/GenomeX-DataExchange](https://github.com/CodeX-HL7-FHIR-Accelerator/GenomeX-DataExchange) | `df269af5f2d69ccf5bf9aad3433a721a1574616a` | [Unresolved / Check guide separately ](https://github.com/CodeX-HL7-FHIR-Accelerator/GenomeX-DataExchange/tree/df269af5f2d69ccf5bf9aad3433a721a1574616a) | ](https://github.com/CodeX-HL7-FHIR-Accelerator/GenomeX-DataExchange/tree/df269af5f2d69ccf5bf9aad3433a721a1574616a)]
| [mh11/VILMAA](https://github.com/mh11/VILMAA) | `59d7c269aeb9f7ddfaf794efd3094879a16a07bd` | [Apache-2.0](https://github.com/mh11/VILMAA/tree/59d7c269aeb9f7ddfaf794efd3094879a16a07bd) |
| [reinator/splace](https://github.com/reinator/splace) | `16bf0529aba4c7d24dd0510a2ff17f1f3509d3f2` | [GPL-3.0](https://github.com/reinator/splace/tree/16bf0529aba4c7d24dd0510a2ff17f1f3509d3f2) |
| [sgalla32/concatenate_genome](https://github.com/sgalla32/concatenate_genome) | `b2afd74909ee9da6451d2b2608c98925a29285f6` | [Unexplained](https://github.com/sgalla32/concatenate_genome/tree/b2afd74909ee9da6451d2b2608c98925a29285f6) |]
| [huggingface/carbon](https://github.com/huggingface/carbon) | `4ca3ce3e5c55e5821d6068bac5c6e3806027a26f` | [Apache-2.0; Test model weights separately](https://github.com/huggingface/carbon/tree/4ca3ce3e5c55e5821d6068bac5c6e3806027a26f) |]
| [HazyResearch/hyena-dna](https://github.com/HazyResearch/hyena-dna) | `d553021b483b82980aa4b868b37ec2d4332e198a` | [Apache-2.0; Test model weights separately ](https://github.com/HazyResearch/hyena-dna/tree/d553021b483b82980aa4b868b37ec2d4332e198a) |]

The [Python distribution inventory](docs/VERSIONS.md) lists installed package versions and declared license metadata. Where metadata says “see distribution license”, consult the linked original package and its included license files. This is not a legal clearance of every optional use. The public source does not bundle these distributions.

## Document processing additions

Local OCR uses Tesseract (Apache-2.0), its language data and Ubuntu Poppler packages (GPL family; see upstream package terms). Offline translation uses CTranslate2 (MIT), SentencePiece (Apache-2.0), Argos model packages (review each upstream model terms), NumPy (BSD-3-Clause) and PyYAML (MIT). ReportLab and pypdf retain their upstream BSD licenses. Model archives and WSL binaries are optional external downloads, not redistributed as suite-owned code. See [sources and exact pins](docs/RESULTS_AND_FINDINGS.md).

Design reference: [8B genealogy website template](https://github.com/8bsite/genealogy-website-template), MIT, copyright 2026 8B. Original implementation in this suite; no template code, third-party animation runtimes, stock portraits or fictional family details are bundled.

## Painted story assets and geographic outlines

The four paintings listed in `DNA_Software/Launcher/heritage-art.json` were generated for this project with the built-in imagegen tool. No Freepik premium illustration was copied. They are explicitly labelled artistic interpretations. User-uploaded artwork is private profile content and is excluded from distribution. Natural Earth map data are [public domain](https://www.naturalearthdata.com/about/terms-of-use/); source: [Natural Earth vector](https://github.com/nvkelso/natural-earth-vector), © respective contributors waived claims under those terms. Converted map source SHA-256 is retained in atlas-countries.json. UNESCO pages are linked for context; their photographs are not bundled by this change.


## GenoCAT and optional API adapters

[GenoCAT](https://github.com/hms-dbmi/genocat) catalog MIT, copyright upstream authors; the license is retained in `DNA_Software/Launcher/Notices/GENOCAT-LICENSE.txt`. Tool metadata snapshot 2022-10-06. Screenshots/example images remain separate upstream works, loaded on demand into a private local cache with attribution; they are not redistributed here. OpenAI API access is an optional external service under its [service terms](https://openai.com/policies/services-agreement/), not bundled model code. No OpenAI SDK dependency was added; the adapter uses Python standard-library HTTPS.

Design workflow reference: [claude-code-ui-agents](https://github.com/mustafakendiguzel/claude-code-ui-agents), MIT. The retained notice is in `DNA_Software/Launcher/Notices/UI-PROMPTS-LICENSE.txt`. Design articles are references, not bundled implementations.

## Development checks

The development workflow uses [Ruff](https://github.com/astral-sh/ruff) (MIT), [ESLint](https://github.com/eslint/eslint) (MIT), [Prettier](https://github.com/prettier/prettier) (MIT), [Stylelint](https://github.com/stylelint/stylelint) (MIT), [HTML Validate](https://gitlab.com/html-validate/html-validate) (MIT), [jscpd](https://github.com/kucherenko/jscpd) (MIT) and [Atheris](https://github.com/google/atheris) (Apache-2.0). These tools are installed separately for development; their binaries are not bundled into the desktop application. Exact versions and lock files are documented in [Code quality](docs/QUALITY.md).


## Complete manifest inventory and development tools

The [dependency inventory](docs/DEPENDENCY_LICENSES.md) records reviewed optional projects, locked Python dependencies, the npm development graph and host/CI tools with upstream links. The machine-readable copy is `DNA_Software/Launcher/third-party-inventory.json`. These are upstream declarations, not an unconditional license-compatibility certification. Preserve complete copyright, license and NOTICE files from each actual distribution; a name/link alone does not replace those obligations.

7-Zip is an optional user-installed utility, not bundled with or used by the built-in ZIP/TAR extractor. Its [license](https://www.7-zip.org/license.txt) includes LGPL terms, unRAR restrictions and BSD portions. Python standard-library archive handling is covered by Python's notices. Security/development tooling includes Ruff, Bandit, Bearer, CodeQL, pip-audit, PSScriptAnalyzer, ShellCheck, actionlint, Atheris, ESLint, Prettier, HTML Validate, Stylelint and jscpd; these are separate development tools, not all shipped in the Windows EXE. CodeQL CLI terms differ from the MIT query-library license. Bearer uses Elastic License 2.0. Downloadable Ubuntu packages retain their individual `/usr/share/doc/*/copyright` notices and source availability through their package repositories.

CodeQL CLI analysis of the new non-OSI contributions requires appropriate entitlement. Its CI jobs are disabled by default; `ENABLE_LICENSED_CODEQL=true` is an explicit operator configuration after rights review. Historical MIT-release scans are retained. The CodeQL upload Action and MIT query sources do not themselves grant rights to the proprietary CLI.
