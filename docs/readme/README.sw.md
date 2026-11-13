# DNA Workbench Suite

**Faili za DNA, rekodi za familia na mtiririko wa kazi wa utafiti katika nafasi moja ya kazi ya ndani.**

[Pakua](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Tovuti](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=sw) · [Mwongozo wa ufungaji](../GETTING_STARTED.md) · [Tafsiri](#translations)

Panga vyanzo vyako kibinafsi na mtoa huduma, linganisha faili zinazooana, na uhifadhi maingizo na matokeo nyuma ya kila uchanganuzi.

![Ziara ya programu iliyo na hali nyepesi na nyeusi, kiteua lugha na faili za wasifu za syntetisk](../images/workspace-demo.gif)

[Tazama ziara ya programu](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=sw#tour) · [Matunzio ya picha kiwamba](../GALLERY.md)

## Unachoweza kufanya

- Ingiza faili za DNA, folda na kumbukumbu zinazotumika. Kagua mtoa huduma, muundo na muundo wa marejeleo kabla ya kunakili au kuhamisha chochote.
- Panga seti za data, hati na matokeo kulingana na wasifu. Rekodi asili ya kila faili. Weka vipimo vya moja kwa moja tofauti na thamani zilizokisiwa na kumbuka wakati vibadala vimekabidhiwa nakala za kromosomu.
- Angalia ubora wa sampuli na ulinganishe vyanzo. Unda toleo la BestDataset kwa mtiririko wa kazi ambao unaweza kutumia muundo sawa wa marejeleo.
- Gundua anuwai na upange faili ukitumia vitazamaji vya jenomu. Linganisha wasifu wa DNA na uunganishe maelezo ya utafiti na rekodi za familia na faili za GEDCOM.
- Hifadhi matokeo kwa pembejeo na kumbukumbu zao. Hamisha ripoti na uhifadhi nakala za wasifu kwa matumizi ya baadaye.
- Tumia msaidizi wa hiari wa ndani ili kuabiri nafasi ya kazi. Unaweza kusanidi AI ya nje kando.

[Katalogi kamili ya kipengele](../FEATURES.md) · [Miundo inayotumika](../TOOL_FORMATS.md)

## Zana na wanachofanya

Hizi ni zana zilizochaguliwa ambazo Suite inaunganisha au inaweza kuzindua. Upatikanaji hutofautiana kwa mtiririko wa kazi na mfumo wa uendeshaji. Baadhi ya moduli na data ya marejeleo ni vipakuliwa tofauti.

| Zana | Inafanya nini |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Husoma, kuorodhesha na kukagua faili za mpangilio zilizopangiliwa katika umbizo la SAM, BAM na CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Vichujio, kurekebisha, kuchanganya na kukagua faili lahaja katika umbizo la VCF na BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Hukagua ubora wa FASTQ na inaweza kupunguza au kuchuja usomaji. |
| [mosdepth](https://github.com/brentp/mosdepth) | Hupima chanjo iliyosomwa kutoka kwa faili za BAM na CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Inachanganya ripoti kutoka kwa zana nyingi za kudhibiti ubora hadi mwonekano mmoja. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Hufanya kazi na data ya aina ya jeni kwa kazi kama vile uchujaji wa kibadala, uhusiano na uchanganuzi mkuu wa vipengele. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Hutumia data ya aina ya jeni kubaini ni vibadala gani viko kwenye nakala sawa ya kromosomu. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Hupata sehemu zinazolingana za DNA zilizorithiwa kutoka kwa babu mmoja. Inatumia data ya aina ya jeni iliyo na vibadala vilivyogawiwa nakala za kromosomu. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Hutumia usomaji wa mpangilio ili kugawa vibadala kwa nakala za kromosomu. |
| [Truvari](https://github.com/ACEnglish/truvari) | Inalinganisha vibadala vya miundo katika faili za VCF. |
| [IGV](https://igv.org/doc/desktop/) | Huonyesha usomaji uliopangiliwa, vibadala na nyimbo zingine za jenomu katika maeneo mahususi. |
| [JBrowse](https://jbrowse.org/jb2/) | Hukuwezesha kuvinjari mfuatano wa marejeleo na nyimbo zilizounganishwa kwa maingiliano. |
| [GenomeSpy](https://genomespy.app/) | Hutoa chati shirikishi za jeni na kuongeza kasi ya michoro ya kivinjari. |
| [Gramps](https://www.gramps-project.org/) | Hupanga rekodi za nasaba, miti ya familia na data ya GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Hufafanua vibadala kwa kutumia vyanzo na vifafanuzi vinavyoweza kuchaguliwa. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Hutabiri jinsi vibadala vinaweza kuathiri jeni, nakala na protini. |
| [PharmCAT](https://pharmcat.org/) | Hutoa ripoti za utafiti wa pharmacojenetiki kutoka kwa pembejeo za aina za jeni zinazotumika. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Huendesha muundo wa hiari wa lugha ya ndani kwenye nyakati za uendeshaji za CPU na GPU zinazooana. |

[Matoleo ya zana na sharti](../VERSIONS.md)

## Anza

Chagua kifurushi kinacholingana na mfumo wako wa uendeshaji na kichakataji. Ukurasa wa kutolewa unaorodhesha vipakuliwa vya x64 na ARM64 kwa Windows, Linux na macOS. Baadhi ya miundo ni hakikisho.

1. Kwenye Windows, toa kumbukumbu na uendeshe kizindua. Kamilisha usanidi wa Msingi unapoombwa.
2. Kwenye Linux, anza kizindua ganda kilichojumuishwa na Python, GTK na WebKitGTK zilizosakinishwa.
3. Kwenye macOS, weka programu kando ya faili za nafasi ya kazi zilizotolewa. Onyesho la kuchungulia linahitaji macOS 13 au matoleo mapya zaidi na Python 3.12 au matoleo mapya zaidi.
4. Anza na sampuli za syntetisk zilizojumuishwa ili kujaribu utendakazi bila kutumia faili za kibinafsi.

[Pakua](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Mwongozo wa ufungaji](../GETTING_STARTED.md)

## Mstari wa amri na otomatiki

Tumia sajili sawa ya amri kupitia kiolesura cha eneo-kazi, CLI, JSON-RPC na MCP. Huduma isiyo na kichwa inaendesha kwenye mashine ya ndani. Unaweza kuorodhesha amri na kusoma schema zao bila kufungua dirisha la eneo-kazi.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Mratibu wa hiari anaweza kukusaidia kupata matokeo. Majibu yake hayachukui nafasi ya data chanzo au uchanganuzi uliothibitishwa.

> Programu ya utafiti. Matokeo hutegemea ingizo, mbinu na marejeleo. DNA Workbench Suite haitoi uchunguzi wa kimatibabu.

## Mradi na msaada

Imedumishwa na Oktay Du / OD kwa usaidizi wa AI.

[Faragha](../PRIVACY.md) · [Usalama](../../SECURITY.md) · [Leseni ya mradi](../../LICENSE) · [Ripoti tatizo](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Saidia mradi · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Tafsiri

Programu inajumuisha lugha 36 za kiolesura cha nje ya mtandao. Chagua tafsiri ya ukurasa huu wa mradi hapa chini.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
