# DNA Workbench Suite

**DNA-bestanden, familiedossiers en onderzoeksworkflows in één lokale werkruimte.**

[Downloaden](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=nl) · [Installatiehandleiding](../GETTING_STARTED.md) · [Vertalingen](#translations)

Organiseer uw bronnen op persoon en provider, vergelijk compatibele bestanden en bewaar de invoer en resultaten achter elke analyse.

![App-rondleiding met lichte en donkere modus, de taalkiezer en synthetische profielbestanden](../images/workspace-demo.gif)

[Bekijk de app-tour](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=nl#tour) · [Galerij met screenshots](../GALLERY.md)

## Wat je kunt doen

- Importeer DNA-bestanden, mappen en ondersteunde archieven. Controleer de provider, het formaat en de referentieopbouw voordat u iets kopieert of verplaatst.
- Groepeer datasets, documenten en resultaten op profiel. Noteer de oorsprong van elk bestand. Houd directe metingen gescheiden van afgeleide waarden en noteer wanneer varianten zijn toegewezen aan chromosoomkopieën.
- Controleer de monsterkwaliteit en vergelijk bronnen. Bouw een BestDataset met versiebeheer voor workflows die dezelfde referentiebuild kunnen gebruiken.
- Ontdek varianten en sequentiebestanden met genoomviewers. Vergelijk DNA-profielen en koppel onderzoeksnotities aan familiedossiers en GEDCOM-bestanden.
- Bewaar resultaten met hun invoer en logboeken. Exporteer rapporten en maak een back-up van profielen voor later gebruik.
- Gebruik de optionele lokale assistent om door de werkruimte te navigeren. U kunt externe AI afzonderlijk configureren.

[Catalogus met volledige functionaliteit](../FEATURES.md) · [Ondersteunde formaten](../TOOL_FORMATS.md)

## Gereedschappen en wat ze doen

Dit zijn geselecteerde tools die de suite integreert of kan starten. De beschikbaarheid varieert per workflow en besturingssysteem. Sommige modules en referentiegegevens zijn afzonderlijke downloads.

| Gereedschap | Wat het doet |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Leest, indexeert en inspecteert uitgelijnde sequencing-bestanden in de formaten SAM, BAM en CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtert, normaliseert, combineert en inspecteert variantbestanden in de formaten VCF en BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Controleert de leeskwaliteit van de FASTQ en kan metingen bijsnijden of filteren. |
| [mosdepth](https://github.com/brentp/mosdepth) | Meet de dekking uit BAM- en CRAM-bestanden. |
| [MultiQC](https://seqera.io/multiqc/) | Combineert rapporten van meerdere kwaliteitscontroletools in één weergave. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Werkt met genotypegegevens voor taken zoals variantfiltering, verwantschap en analyse van hoofdcomponenten. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Gebruikt genotypegegevens om af te leiden welke varianten op dezelfde kopie van een chromosoom liggen. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Vindt overeenkomende DNA-segmenten die zijn geërfd van een gemeenschappelijke voorouder. Het maakt gebruik van genotypegegevens waarbij varianten worden toegewezen aan chromosoomkopieën. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Gebruikt sequencing-metingen om varianten aan chromosoomkopieën toe te wijzen. |
| [Truvari](https://github.com/ACEnglish/truvari) | Vergelijkt structurele varianten in VCF-bestanden. |
| [IGV](https://igv.org/doc/desktop/) | Geeft uitgelijnde waarden, varianten en andere genoomtracks op specifieke locaties weer. |
| [JBrowse](https://jbrowse.org/jb2/) | Hiermee kunt u interactief door referentiereeksen en gekoppelde tracks bladeren. |
| [GenomeSpy](https://genomespy.app/) | Rendert interactieve genomische grafieken met browser grafische versnelling. |
| [Gramps](https://www.gramps-project.org/) | Organiseert genealogische gegevens, stambomen en GEDCOM-gegevens. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Annoteert varianten met behulp van selecteerbare bronnen en annotators. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Voorspelt hoe varianten genen, transcripten en eiwitten kunnen beïnvloeden. |
| [PharmCAT](https://pharmcat.org/) | Produceert farmacogenetische onderzoeksrapporten op basis van ondersteunde genotype-inputs. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Voert het optionele lokale taalmodel uit op compatibele CPU- en GPU-runtimes. |

[Toolversies en vereisten](../VERSIONS.md)

## Ga aan de slag

Kies het pakket dat bij jouw besturingssysteem en processor past. Op de releasepagina staan ​​x64- en ARM64-downloads voor Windows, Linux en macOS. Sommige builds zijn previews.

1. Pak op Windows het archief uit en voer het opstartprogramma uit. Voltooi de Core-installatie wanneer daarom wordt gevraagd.
2. Start op de Linux de meegeleverde shell-launcher terwijl Python, GTK en WebKitGTK zijn geïnstalleerd.
3. Bewaar op macOS de app naast de uitgepakte werkruimtebestanden. Voor de preview is macOS 13 of hoger en Python 3.12 of hoger vereist.
4. Begin met de meegeleverde synthetische voorbeelden om de workflows uit te proberen zonder persoonlijke bestanden te gebruiken.

[Downloaden](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Installatiehandleiding](../GETTING_STARTED.md)

## Commandoregel en automatisering

Gebruik hetzelfde opdrachtregister via de desktopinterface, CLI, JSON-RPC en MCP. De headless-service draait op de lokale machine. U kunt opdrachten weergeven en hun schema's lezen zonder een bureaubladvenster te openen.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

De optionele assistent kan u helpen bij het navigeren door de resultaten. De antwoorden vervangen niet de brongegevens of een geverifieerde analyse.

> Onderzoekssoftware. Resultaten zijn afhankelijk van de input, werkwijze en referenties. DNA Workbench Suite biedt geen klinische diagnose.

## Projecten en ondersteuning

Onderhouden door Oktay Du / OD met AI-assistentie.

[Privacy](../PRIVACY.md) · [Beveiliging](../../SECURITY.md) · [Projectlicentie](../../LICENSE) · [Meld een probleem](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Steun het project · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Vertalingen

De app bevat 36 offline interfacetalen. Kies hieronder een vertaling van deze projectpagina.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
