# DNA Workbench Suite

**Fayilolin DNA, bayanan iyali da gudanar da ayyukan bincike a cikin wurin aiki ɗaya na gida.**

[Zazzagewa](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Yanar Gizo](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ha) · [Jagorar shigarwa](../GETTING_STARTED.md) · [Fassara](#translations)

Tsara tushen ku ta mutum da mai bayarwa, kwatanta fayiloli masu jituwa, da kiyaye abubuwan da aka shigar da sakamako a bayan kowane bincike.

![Ziyarar aikace-aikacen tare da yanayin haske da duhu, mai ɗaukar harshe da fayilolin bayanin martaba na roba](../images/workspace-demo.gif)

[Kalli yawon shakatawa na app](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ha#tour) · [Hoton hoto](../GALLERY.md)

## Abin da za ku iya yi

- Shigo da fayilolin DNA, manyan fayiloli da rumbun adana bayanai masu tallafi. Bincika mai badawa, tsarawa da ginin tunani kafin kwafi ko matsar da wani abu.
- Rukunin bayanai, takardu da sakamako ta bayanin martaba. Yi rikodin asalin kowane fayil. Kiyaye ma'aunai kai tsaye daga ƙididdige ƙididdiga kuma lura lokacin da aka sanya bambance-bambancen zuwa kwafin chromosome.
- Duba ingancin samfurin kuma kwatanta tushe. Gina sigar BestDataset don gudanawar aiki wanda zai iya amfani da ginin tunani iri ɗaya.
- Bincika bambance-bambancen da fayilolin jeri tare da masu kallon kwayoyin halitta. Kwatanta bayanan bayanan DNA kuma haɗa bayanan bincike tare da bayanan iyali da fayilolin GEDCOM.
- Ajiye sakamako tare da abubuwan shigarsu da rajistan ayyukansu. Fitar da rahotanni da adana bayanan martaba don amfani daga baya.
- Yi amfani da zaɓin mataimakin gida don kewaya filin aiki. Kuna iya saita AI na waje daban.

[Cikakken kasida](../FEATURES.md) · [Tsarin tallafi](../TOOL_FORMATS.md)

## Kayan aiki da abin da suke yi

Waɗannan zaɓaɓɓun kayan aikin ne wanda babban ɗakin ya haɗa ko zai iya ƙaddamarwa. Samuwar ya bambanta ta hanyar aiki da tsarin aiki. Wasu samfura da bayanan tunani abubuwan zazzagewa daban ne.

| Kayan aiki | Abin da yake yi |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Yana karantawa, fihirisa da duba fayilolin jeri-jefi a cikin tsarin SAM, BAM da CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Tace, daidaitawa, haɗawa da bincika bambance-bambancen fayiloli a cikin tsarin VCF da BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Yana duba ingancin karatun FASTQ kuma yana iya datsa ko tace karantawa. |
| [mosdepth](https://github.com/brentp/mosdepth) | Matakan karanta ɗaukar hoto daga fayilolin BAM da CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Haɗa rahotanni daga kayan aikin sarrafa inganci da yawa zuwa kallo ɗaya. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Yana aiki tare da bayanan genotype don ayyuka kamar bambance-bambancen tacewa, alaƙa da bincike na babban ɓangaren. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Yana amfani da bayanan genotype don tantance waɗanne bambance-bambancen da ke kan kwafin chromosome iri ɗaya. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Ya nemo madaidaitan sassan DNA da aka gada daga kakanni guda. Yana amfani da bayanan genotype tare da bambance-bambancen da aka sanya wa kwafin chromosome. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Yana amfani da jerin abubuwan karantawa don sanya bambance-bambancen karatu zuwa kwafin chromosome. |
| [Truvari](https://github.com/ACEnglish/truvari) | Yana kwatanta bambance-bambancen tsari a cikin fayilolin VCF. |
| [IGV](https://igv.org/doc/desktop/) | Yana nuna madaidaitan karantawa, bambance-bambancen karatu da sauran waƙoƙin genome a takamaiman wurare. |
| [JBrowse](https://jbrowse.org/jb2/) | Yana ba ku damar bincika jerin abubuwan tunani da waƙoƙin haɗin gwiwa tare. |
| [GenomeSpy](https://genomespy.app/) | Yana ba da ginshiƙi mai mu'amala da genomic tare da haɓakar zane mai lilo. |
| [Gramps](https://www.gramps-project.org/) | Yana tsara bayanan asali, bishiyar iyali da bayanan GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Yana ba da bayanin bambance-bambancen ta amfani da zaɓaɓɓun tushe da annotators. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Yana tsinkaya yadda bambance-bambancen zasu iya shafar kwayoyin halitta, bayanan rubutu da sunadaran. |
| [PharmCAT](https://pharmcat.org/) | Yana samar da rahotannin binciken harhada magunguna daga abubuwan da aka goyan bayan genotype. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Yana gudanar da ƙirar harshe na zaɓi na zaɓi akan CPU da GPU masu dacewa. |

[Siffofin kayan aiki da abubuwan da ake buƙata](../VERSIONS.md)

## Fara

Zaɓi kunshin da ya dace da tsarin aiki da mai sarrafa ku. Shafin sakin ya lissafa abubuwan da aka saukar da x64 da ARM64 don Windows, Linux da macOS. Wasu ginin samfoti ne.

1. A kan Windows, cire ma'ajiyar kuma gudanar da ƙaddamarwa. Cikakkun saitin Core lokacin da aka sa.
2. A kan Linux, fara ƙaddamar da harsashi da aka haɗa tare da shigar Python, GTK da WebKitGTK.
3. A kan macOS, ajiye app kusa da fayilolin filin aiki da aka ciro. Samfotin yana buƙatar macOS 13 ko daga baya da Python 3.12 ko kuma daga baya.
4. Fara da samfuran roba da aka haɗa don gwada ayyukan aiki ba tare da amfani da fayilolin sirri ba.

[Zazzagewa](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Jagorar shigarwa](../GETTING_STARTED.md)

## Layin umarni da aiki da kai

Yi amfani da rajistar umarni iri ɗaya ta hanyar dubawar tebur, CLI, JSON-RPC da MCP. Sabis ɗin mara kai yana aiki akan injin gida. Kuna iya jera umarni kuma karanta tsarin su ba tare da buɗe taga ta tebur ba.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Mataimakin zaɓi na iya taimaka muku kewaya sakamako. Amsoshinsa ba sa maye gurbin bayanan tushen ko ingantaccen bincike.

> Software na bincike. Sakamako ya dogara da shigarwar, hanya da nassoshi. DNA Workbench Suite baya samar da ganewar asibiti.

## Project da tallafi

Oktay Du / OD ya kiyaye shi tare da taimakon AI.

[Keɓantawa](../PRIVACY.md) · [Tsaro](../../SECURITY.md) · [lasisin aikin](../../LICENSE) · [Bayar da rahoto](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Goyi bayan aikin · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Fassara

Ka'idar ta ƙunshi harsunan mu'amala da layi 36. Zaɓi fassarar wannan shafin aikin da ke ƙasa.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
