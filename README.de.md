# DNA Workbench Suite

**DNA-Dateien, Familienunterlagen und Forschungsabläufe in einem lokalen Arbeitsbereich.**

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=de) · [Installationsanleitung](docs/GETTING_STARTED.md) · [Übersetzungen](#translations)

Ordne Quellen nach Person und Anbieter, vergleiche kompatible Dateien und behalte die Eingangsdaten und Ergebnisse jeder Analyse im Blick.

![App-Tour mit hellem und dunklem Design, Sprachauswahl und synthetischen Beispieldateien](docs/images/workspace-demo.gif)

[App-Tour ansehen](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=de#tour) · [Bildergalerie](docs/GALLERY.md)

## Was du mit der Suite machen kannst

- Importiere DNA-Dateien, Ordner und unterstützte Archive. Prüfe Anbieter, Format und Referenzversion, bevor du Dateien kopierst oder verschiebst.
- Ordne Datensätze, Dokumente und Ergebnisse nach Profil. Halte die Herkunft jeder Datei fest. Unterscheide gemessene von geschätzten Werten und dokumentiere, wenn Varianten Chromosomenkopien zugeordnet wurden.
- Prüfe die Probenqualität und vergleiche Quellen. Erstelle einen versionierten BestDataset-Datensatz für Workflows mit derselben Referenzversion.
- Erkunde Varianten und Sequenzdateien in Genom-Viewern. Vergleiche DNA-Profile und verknüpfe Forschungsnotizen mit Familienunterlagen und GEDCOM-Dateien.
- Speichere Ergebnisse mit Eingangsdaten und Protokollen. Exportiere Berichte und sichere Profile.
- Nutze den optionalen lokalen Assistenten, um dich in der App zurechtzufinden. Externe KI lässt sich separat einrichten.

[Vollständige Funktionsübersicht](docs/FEATURES.md) · [Unterstützte Formate](docs/TOOL_FORMATS.md)

## Werkzeuge und ihre Aufgaben

Die Suite bindet diese Werkzeuge ein oder kann sie starten. Die Verfügbarkeit hängt vom Workflow und Betriebssystem ab. Einige Module und Referenzdaten werden separat heruntergeladen.

| Werkzeug | Aufgabe |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Liest, indexiert und prüft ausgerichtete Sequenzdaten in SAM, BAM und CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtert, normalisiert, kombiniert und prüft Variantendateien in VCF und BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Prüft die Qualität von FASTQ-Reads und kann Reads kürzen oder filtern. |
| [mosdepth](https://github.com/brentp/mosdepth) | Berechnet die Sequenzabdeckung aus BAM- und CRAM-Dateien. |
| [MultiQC](https://seqera.io/multiqc/) | Fasst Berichte mehrerer Werkzeuge zur Qualitätskontrolle in einer Ansicht zusammen. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Verarbeitet Genotypdaten für Variantenfilterung, Verwandtschaftsschätzungen und Hauptkomponentenanalysen. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Schätzt aus Genotypdaten, welche Varianten auf derselben Chromosomenkopie liegen. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Sucht gemeinsam geerbte DNA-Segmente in Genotypdaten, deren Varianten Chromosomenkopien zugeordnet wurden. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Verwendet Sequenz-Reads, um Varianten Chromosomenkopien zuzuordnen. |
| [Truvari](https://github.com/ACEnglish/truvari) | Vergleicht Strukturvarianten in VCF-Dateien. |
| [IGV](https://igv.org/doc/desktop/) | Zeigt Reads, Varianten und weitere Genomspuren an ausgewählten Positionen. |
| [JBrowse](https://jbrowse.org/jb2/) | Stellt Referenzsequenzen und zugehörige Spuren interaktiv dar. |
| [GenomeSpy](https://genomespy.app/) | Zeichnet interaktive Genomdiagramme mit Grafikbeschleunigung im Browser. |
| [Gramps](https://www.gramps-project.org/) | Verwaltet Familienbäume, genealogische Unterlagen und GEDCOM-Daten. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Reichert Varianten mit Informationen aus auswählbaren Quellen und Annotationsmodulen an. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Sagt mögliche Auswirkungen von Varianten auf Gene, Transkripte und Proteine voraus. |
| [PharmCAT](https://pharmcat.org/) | Erstellt pharmakogenetische Forschungsberichte aus unterstützten Genotypdaten. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Führt das optionale lokale Sprachmodell mit kompatiblen CPU- und GPU-Laufzeiten aus. |

[Werkzeugversionen und Voraussetzungen](docs/VERSIONS.md)

## Erste Schritte

Wähle das Paket für dein Betriebssystem und deinen Prozessor. Auf der Release-Seite findest du x64- und ARM64-Downloads für Windows, Linux und macOS. Einige Builds sind Vorschauen.

1. Entpacke unter Windows das Archiv und öffne den Launcher. Führe die Grundeinrichtung aus, wenn du dazu aufgefordert wirst.
2. Starte unter Linux das mitgelieferte Shell-Skript. Dafür müssen Python, GTK und WebKitGTK installiert sein.
3. Lass unter macOS die App neben den entpackten Arbeitsbereichsdateien. Die Vorschau benötigt macOS 13 oder neuer und Python 3.12 oder neuer.
4. Probier die Workflows zuerst mit den mitgelieferten synthetischen Beispieldaten aus.

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Installationsanleitung](docs/GETTING_STARTED.md)

## Kommandozeile und Automatisierung

Desktop-Oberfläche, CLI, JSON-RPC und MCP nutzen dieselbe Befehlsregistrierung. Der Headless-Dienst läuft auf deinem Rechner. Du kannst Befehle und ihre Schemata auch ohne Desktop-Fenster aufrufen.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Der optionale Assistent hilft bei der Navigation durch Ergebnisse. Seine Antworten ersetzen weder die Quelldaten noch eine geprüfte Analyse.

> Forschungssoftware. Die Ergebnisse hängen von Eingangsdaten, Methode und Referenzen ab. DNA Workbench Suite stellt keine klinischen Diagnosen.

## Projekt und Unterstützung

Betreut von Oktay Du / OD, mit KI-Unterstützung erstellt.

[Datenschutz](docs/PRIVACY.md) · [Sicherheit](SECURITY.md) · [Projektlizenz](LICENSE) · [Problem melden](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Projekt unterstützen · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Übersetzungen

Die App enthält 36 Oberflächensprachen für die Offline-Nutzung. Wähle hier die Übersetzung dieser Projektseite.

[Deutsch](README.de.md) · [English](README.md) · [Türkçe](docs/readme/README.tr.md) · [Español](docs/readme/README.es.md) · [Français](docs/readme/README.fr.md) · [Português](docs/readme/README.pt.md) · [Italiano](docs/readme/README.it.md) · [Nederlands](docs/readme/README.nl.md) · [Svenska](docs/readme/README.sv.md) · [Ελληνικά](docs/readme/README.el.md) · [Čeština](docs/readme/README.cs.md) · [Română](docs/readme/README.ro.md) · [Magyar](docs/readme/README.hu.md) · [Polski](docs/readme/README.pl.md) · [Українська](docs/readme/README.uk.md) · [Русский](docs/readme/README.ru.md) · [العربية](docs/readme/README.ar.md) · [فارسی](docs/readme/README.fa.md) · [اردو](docs/readme/README.ur.md) · [हिन्दी](docs/readme/README.hi.md) · [नेपाली](docs/readme/README.ne.md) · [ქართული](docs/readme/README.ka.md) · [Հայերեն](docs/readme/README.hy.md) · [Монгол](docs/readme/README.mn.md) · [简体中文](docs/readme/README.zh-Hans.md) · [日本語](docs/readme/README.ja.md) · [한국어](docs/readme/README.ko.md) · [Bahasa Indonesia](docs/readme/README.id.md) · [Bahasa Melayu](docs/readme/README.ms.md) · [Tiếng Việt](docs/readme/README.vi.md) · [ไทย](docs/readme/README.th.md) · [Filipino](docs/readme/README.fil.md) · [አማርኛ](docs/readme/README.am.md) · [Kiswahili](docs/readme/README.sw.md) · [Soomaali](docs/readme/README.so.md) · [Hausa](docs/readme/README.ha.md)
