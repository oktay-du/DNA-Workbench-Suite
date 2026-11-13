# DNA Workbench Suite

**DNA-filer, familjeregister och forskningsarbetsflöden i en lokal arbetsyta.**

[Ladda ner](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Webbplats](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=sv) · [Installationsguide](../GETTING_STARTED.md) · [Översättningar](#translations)

Organisera dina källor efter person och leverantör, jämför kompatibla filer och behåll indata och resultat bakom varje analys.

![Apptur med ljus och mörkt läge, språkväljaren och syntetiska profilfiler](../images/workspace-demo.gif)

[Se apprundan](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=sv#tour) · [Skärmbildsgalleri](../GALLERY.md)

## Vad du kan göra

- Importera DNA-filer, mappar och arkiv som stöds. Granska leverantören, formatet och referensbygget innan du kopierar eller flyttar något.
- Gruppera datamängder, dokument och resultat efter profil. Anteckna varje fils ursprung. Håll direkta mätningar åtskilda från antagna värden och notera när varianter har tilldelats kromosomkopior.
- Kontrollera provkvaliteten och jämför källor. Bygg en version av BestDataset för arbetsflöden som kan använda samma referensbygge.
- Utforska varianter och sekvensfiler med genomvisare. Jämför DNA-profiler och koppla forskningsanteckningar med familjeregister och GEDCOM-filer.
- Spara resultat med sina ingångar och loggar. Exportera rapporter och säkerhetskopiera profiler för senare användning.
- Använd den valfria lokala assistenten för att navigera i arbetsytan. Du kan konfigurera extern AI separat.

[Fullständig funktionskatalog](../FEATURES.md) · [Format som stöds](../TOOL_FORMATS.md)

## Verktyg och vad de gör

Dessa är utvalda verktyg som sviten integrerar eller kan starta. Tillgängligheten varierar beroende på arbetsflöde och operativsystem. Vissa moduler och referensdata är separata nedladdningar.

| Verktyg | Vad den gör |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Läser, indexerar och inspekterar justerade sekvenseringsfiler i formaten SAM, BAM och CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtrerar, normaliserar, kombinerar och inspekterar variantfiler i formaten VCF och BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Kontrollerar FASTQ läskvalitet och kan trimma eller filtrera avläsningar. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mäter läst täckning från BAM- och CRAM-filer. |
| [MultiQC](https://seqera.io/multiqc/) | Kombinerar rapporter från flera kvalitetskontrollverktyg till en vy. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Arbetar med genotypdata för uppgifter som variantfiltrering, släktskap och principal komponentanalys. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Använder genotypdata för att sluta sig till vilka varianter som ligger på samma kopia av en kromosom. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Hittar matchande DNA-segment som ärvts från en gemensam förfader. Den använder genotypdata med varianter tilldelade kromosomkopior. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Använder sekvensläsningar för att tilldela varianter till kromosomkopior. |
| [Truvari](https://github.com/ACEnglish/truvari) | Jämför strukturella varianter i VCF-filer. |
| [IGV](https://igv.org/doc/desktop/) | Visar justerade läsningar, varianter och andra genomspår på specifika platser. |
| [JBrowse](https://jbrowse.org/jb2/) | Låter dig bläddra bland referenssekvenser och länkade spår interaktivt. |
| [GenomeSpy](https://genomespy.app/) | Återger interaktiva genomiska diagram med webbläsargrafikacceleration. |
| [Gramps](https://www.gramps-project.org/) | Organiserar släktregister, släktträd och GEDCOM-data. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Annoterar varianter med hjälp av valbara källor och annotatorer. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Förutsäger hur varianter kan påverka gener, transkript och proteiner. |
| [PharmCAT](https://pharmcat.org/) | Producerar farmakogenetiska forskningsrapporter från stödda genotypingångar. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Kör den valfria lokala språkmodellen på kompatibla CPU- och GPU-körtider. |

[Verktygsversioner och förutsättningar](../VERSIONS.md)

## Kom igång

Välj det paket som matchar ditt operativsystem och processor. Utgivningssidan listar x64 och ARM64 nedladdningar för Windows, Linux och macOS. Vissa versioner är förhandsvisningar.

1. På Windows, extrahera arkivet och kör startprogrammet. Slutför Core-installationen när du uppmanas.
2. På Linux, starta den medföljande skalstartaren med Python, GTK och WebKitGTK installerade.
3. På macOS, håll appen bredvid de extraherade arbetsytefilerna. Förhandsvisningen kräver macOS 13 eller senare och Python 3.12 eller senare.
4. Börja med de medföljande syntetiska proverna för att prova arbetsflödena utan att använda personliga filer.

[Ladda ner](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Installationsguide](../GETTING_STARTED.md)

## Kommandorad och automatisering

Använd samma kommandoregister via skrivbordsgränssnittet, CLI, JSON-RPC och MCP. Den huvudlösa tjänsten körs på den lokala maskinen. Du kan lista kommandon och läsa deras scheman utan att öppna ett skrivbordsfönster.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Den valfria assistenten kan hjälpa dig att navigera i resultat. Dess svar ersätter inte källdata eller en verifierad analys.

> Forskningsprogramvara. Resultaten beror på input, metod och referenser. DNA Workbench Suite ger ingen klinisk diagnos.

## Projekt och support

Underhålls av Oktay Du / OD med AI-hjälp.

[Sekretess](../PRIVACY.md) · [Säkerhet](../../SECURITY.md) · [Projektlicens](../../LICENSE) · [Rapportera ett problem](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Stöd projektet · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Översättningar

Appen innehåller 36 offline-gränssnittsspråk. Välj en översättning av denna projektsida nedan.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
