# DNA Workbench Suite

**Mga DNA file, mga tala ng pamilya at mga workflow ng pananaliksik sa isang lokal na workspace.**

[I-download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fil) · [Gabay sa pag-install](../GETTING_STARTED.md) · [Mga pagsasalin](#translations)

Ayusin ang iyong mga source ayon sa tao at provider, ihambing ang mga katugmang file, at panatilihin ang mga input at resulta sa likod ng bawat pagsusuri.

![App tour na may light at dark mode, ang tagapili ng wika at mga synthetic na profile file](../images/workspace-demo.gif)

[Panoorin ang app tour](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fil#tour) · [Gallery ng screenshot](../GALLERY.md)

## Kung ano ang magagawa mo

- Mag-import ng mga DNA file, folder at sinusuportahang archive. Suriin ang provider, format at reference build bago mo kopyahin o ilipat ang anuman.
- Igrupo ang mga dataset, dokumento at resulta ayon sa profile. Itala ang pinagmulan ng bawat file. Panatilihing hiwalay ang mga direktang pagsukat sa mga hinuha na halaga at tandaan kung kailan naitalaga ang mga variant sa mga kopya ng chromosome.
- Suriin ang kalidad ng sample at ihambing ang mga mapagkukunan. Bumuo ng may bersyon na BestDataset para sa mga workflow na maaaring gumamit ng parehong reference na build.
- I-explore ang mga variant at sequence file na may mga genome viewer. Ihambing ang mga profile ng DNA at ikonekta ang mga tala sa pananaliksik sa mga talaan ng pamilya at mga GEDCOM na file.
- I-save ang mga resulta gamit ang kanilang mga input at log. I-export ang mga ulat at i-back up ang mga profile para magamit sa ibang pagkakataon.
- Gamitin ang opsyonal na lokal na assistant para mag-navigate sa workspace. Maaari mong i-configure nang hiwalay ang external AI.

[Buong katalogo ng tampok](../FEATURES.md) · [Mga sinusuportahang format](../TOOL_FORMATS.md)

## Mga tool at kung ano ang kanilang ginagawa

Ito ang mga napiling tool na isinasama o maaaring ilunsad ng suite. Nag-iiba-iba ang availability ayon sa workflow at operating system. Ang ilang mga module at reference na data ay magkahiwalay na pag-download.

| Tool | Ano ang ginagawa nito |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Nagbabasa, nag-i-index at nag-iinspeksyon ng mga naka-align na sequencing na file sa SAM, BAM at CRAM na mga format. |
| [BCFtools](https://samtools.github.io/bcftools/) | Sinasala, ginagawang normal, pinagsasama, at sinisiyasat ang mga variant na file sa mga format na VCF at BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Sinusuri ang kalidad ng pagbabasa ng FASTQ at maaaring i-trim o i-filter ang mga nabasa. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mga panukalang read coverage mula sa BAM at CRAM file. |
| [MultiQC](https://seqera.io/multiqc/) | Pinagsasama-sama ang mga ulat mula sa maraming tool sa pagkontrol sa kalidad sa isang view. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Gumagana sa data ng genotype para sa mga gawain tulad ng variant na pag-filter, pagkakaugnay at pagsusuri ng pangunahing bahagi. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Gumagamit ng data ng genotype upang mahinuha kung aling mga variant ang nasa parehong kopya ng isang chromosome. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Naghahanap ng tumutugmang mga segment ng DNA na minana mula sa isang karaniwang ninuno. Gumagamit ito ng data ng genotype na may mga variant na nakatalaga sa mga kopya ng chromosome. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Gumagamit ng mga sequencing read para magtalaga ng mga variant sa mga kopya ng chromosome. |
| [Truvari](https://github.com/ACEnglish/truvari) | Inihahambing ang mga variant ng istruktura sa VCF file. |
| [IGV](https://igv.org/doc/desktop/) | Nagpapakita ng mga nakahanay na pagbabasa, variant at iba pang genome track sa mga partikular na lokasyon. |
| [JBrowse](https://jbrowse.org/jb2/) | Hinahayaan kang mag-browse ng mga pagkakasunud-sunod ng sanggunian at mga naka-link na track nang interactive. |
| [GenomeSpy](https://genomespy.app/) | Nagre-render ng mga interactive na genomic chart na may browser graphics acceleration. |
| [Gramps](https://www.gramps-project.org/) | Nag-aayos ng mga talaan ng genealogy, mga puno ng pamilya at data ng GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Nag-annotate ng mga variant gamit ang mga mapipiling source at annotator. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Hinuhulaan kung paano maaaring makaapekto ang mga variant sa mga gene, transcript, at protina. |
| [PharmCAT](https://pharmcat.org/) | Gumagawa ng mga ulat sa pananaliksik sa pharmacogenetics mula sa mga sinusuportahang genotype input. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Pinapatakbo ang opsyonal na modelo ng lokal na wika sa mga katugmang CPU at GPU runtime. |

[Mga bersyon ng tool at mga kinakailangan](../VERSIONS.md)

## Magsimula

Piliin ang package na tumutugma sa iyong operating system at processor. Inililista ng pahina ng paglabas ang x64 at ARM64 na mga download para sa Windows, Linux at macOS. Ang ilang mga build ay mga preview.

1. Sa Windows, i-extract ang archive at patakbuhin ang launcher. Kumpletuhin ang Core setup kapag na-prompt.
2. Sa Linux, simulan ang kasamang shell launcher na may Python, GTK at WebKitGTK na naka-install.
3. Sa macOS, panatilihin ang app sa tabi ng mga na-extract na workspace file. Ang preview ay nangangailangan ng macOS 13 o mas bago at Python 3.12 o mas bago.
4. Magsimula sa mga kasamang sintetikong sample upang subukan ang mga daloy ng trabaho nang hindi gumagamit ng mga personal na file.

[I-download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Gabay sa pag-install](../GETTING_STARTED.md)

## Command line at automation

Gamitin ang parehong command registry sa pamamagitan ng desktop interface, CLI, JSON-RPC at MCP. Ang walang ulo na serbisyo ay tumatakbo sa lokal na makina. Maaari mong ilista ang mga command at basahin ang kanilang mga schema nang hindi nagbubukas ng desktop window.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Matutulungan ka ng opsyonal na assistant na mag-navigate sa mga resulta. Hindi pinapalitan ng mga sagot nito ang pinagmulang data o isang na-verify na pagsusuri.

> Software ng pananaliksik. Ang mga resulta ay nakasalalay sa input, pamamaraan at mga sanggunian. Ang DNA Workbench Suite ay hindi nagbibigay ng klinikal na diagnosis.

## Proyekto at suporta

Pinapanatili ng Oktay Du / OD sa tulong ng AI.

[Pagkapribado](../PRIVACY.md) · [Seguridad](../../SECURITY.md) · [Lisensya ng proyekto](../../LICENSE) · [Mag-ulat ng problema](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Suportahan ang proyekto · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Mga pagsasalin

Kasama sa app ang 36 na offline na mga wika sa interface. Pumili ng pagsasalin ng pahina ng proyektong ito sa ibaba.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
