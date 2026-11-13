# DNA Workbench Suite

**Pliki DNA, akta rodzinne i przepływy pracy badawczej w jednym lokalnym obszarze roboczym.**

[Pobierz](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Strona internetowa](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=pl) · [Instrukcja instalacji](../GETTING_STARTED.md) · [Tłumaczenia](#translations)

Organizuj źródła według osób i dostawców, porównuj kompatybilne pliki i przechowuj dane wejściowe i wyniki każdej analizy.

![Prezentacja aplikacji z trybem jasnym i ciemnym, selektorem języka i syntetycznymi plikami profili](../images/workspace-demo.gif)

[Obejrzyj prezentację aplikacji](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=pl#tour) · [Galeria zrzutów ekranu](../GALLERY.md)

## Co możesz zrobić

- Importuj pliki DNA, foldery i obsługiwane archiwa. Zanim cokolwiek skopiujesz lub przeniesiesz, przejrzyj dostawcę, format i kompilację referencyjną.
- Grupuj zbiory danych, dokumenty i wyniki według profilu. Zapisz pochodzenie każdego pliku. Trzymaj pomiary bezpośrednie oddzielnie od wartości wywnioskowanych i zanotuj, kiedy do kopii chromosomów przypisano warianty.
- Sprawdź jakość próbki i porównaj źródła. Utwórz wersjonowaną wersję BestDataset dla przepływów pracy, które mogą korzystać z tej samej kompilacji referencyjnej.
- Przeglądaj warianty i pliki sekwencji za pomocą przeglądarek genomu. Porównaj profile DNA i połącz notatki badawcze z dokumentacją rodzinną i plikami GEDCOM.
- Zapisuj wyniki wraz z danymi wejściowymi i dziennikami. Eksportuj raporty i twórz kopie zapasowe profili do późniejszego wykorzystania.
- Użyj opcjonalnego asystenta lokalnego, aby poruszać się po obszarze roboczym. Możesz oddzielnie skonfigurować zewnętrzną sztuczną inteligencję.

[Pełny katalog funkcji](../FEATURES.md) · [Obsługiwane formaty](../TOOL_FORMATS.md)

## Narzędzia i do czego służą

Są to wybrane narzędzia, które pakiet integruje lub może uruchomić. Dostępność zależy od przepływu pracy i systemu operacyjnego. Niektóre moduły i dane referencyjne można pobrać osobno.

| Narzędzie | Co to robi |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Odczytuje, indeksuje i sprawdza dopasowane pliki sekwencjonowania w formatach SAM, BAM i CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtruje, normalizuje, łączy i sprawdza warianty plików w formatach VCF i BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Sprawdza jakość odczytu FASTQ i może przycinać lub filtrować odczyty. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mierzy zasięg odczytu z plików BAM i CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Łączy raporty z wielu narzędzi kontroli jakości w jeden widok. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Współpracuje z danymi genotypowymi do celów takich jak filtrowanie wariantów, pokrewieństwo i analiza głównych składowych. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Wykorzystuje dane dotyczące genotypu, aby wywnioskować, które warianty znajdują się w tej samej kopii chromosomu. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Znajduje pasujące segmenty DNA odziedziczone od wspólnego przodka. Wykorzystuje dane genotypowe z wariantami przypisanymi do kopii chromosomów. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Wykorzystuje odczyty sekwencjonowania, aby przypisać warianty do kopii chromosomów. |
| [Truvari](https://github.com/ACEnglish/truvari) | Porównuje warianty konstrukcyjne w plikach VCF. |
| [IGV](https://igv.org/doc/desktop/) | Wyświetla dopasowane odczyty, warianty i inne ścieżki genomu w określonych lokalizacjach. |
| [JBrowse](https://jbrowse.org/jb2/) | Umożliwia interaktywne przeglądanie sekwencji referencyjnych i powiązanych utworów. |
| [GenomeSpy](https://genomespy.app/) | Renderuje interaktywne wykresy genomowe z akceleracją grafiki przeglądarki. |
| [Gramps](https://www.gramps-project.org/) | Organizuje zapisy genealogiczne, drzewa genealogiczne i dane GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Adnotuje warianty, korzystając z wybranych źródeł i adnotatorów. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Przewiduje, jak warianty mogą wpływać na geny, transkrypty i białka. |
| [PharmCAT](https://pharmcat.org/) | Tworzy raporty z badań farmakogenetycznych na podstawie danych wejściowych dotyczących obsługiwanego genotypu. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Uruchamia opcjonalny model języka lokalnego w zgodnych środowiskach wykonawczych procesora i karty graficznej. |

[Wersje narzędzi i wymagania wstępne](../VERSIONS.md)

## Zacznij

Wybierz pakiet pasujący do Twojego systemu operacyjnego i procesora. Strona wydania zawiera listę plików do pobrania x64 i ARM64 dla Windows, Linux i macOS. Niektóre kompilacje są podglądami.

1. Na Windows rozpakuj archiwum i uruchom program uruchamiający. Po wyświetleniu monitu dokończ konfigurację rdzenia.
2. Na Linux uruchom dołączony program uruchamiający powłokę z zainstalowanymi Python, GTK i WebKitGTK.
3. W przypadku macOS trzymaj aplikację obok wyodrębnionych plików obszaru roboczego. Wersja zapoznawcza wymaga wersji macOS 13 lub nowszej oraz Python 3.12 lub nowszej.
4. Zacznij od dołączonych próbek syntetycznych, aby wypróbować przepływy pracy bez korzystania z plików osobistych.

[Pobierz](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Instrukcja instalacji](../GETTING_STARTED.md)

## Linia poleceń i automatyzacja

Użyj tego samego rejestru poleceń poprzez interfejs pulpitu, CLI, JSON-RPC i MCP. Usługa bezgłowa działa na komputerze lokalnym. Możesz wyświetlać listę poleceń i czytać ich schematy bez otwierania okna pulpitu.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Opcjonalny asystent może pomóc w poruszaniu się po wynikach. Jej odpowiedzi nie zastępują danych źródłowych ani zweryfikowanej analizy.

> Oprogramowanie badawcze. Wyniki zależą od danych wejściowych, metody i literatury. DNA Workbench Suite nie umożliwia diagnozy klinicznej.

## Projekt i wsparcie

Utrzymywany przez Oktay Du / OD przy wsparciu AI.

[Prywatność](../PRIVACY.md) · [Bezpieczeństwo](../../SECURITY.md) · [Licencja na projekt](../../LICENSE) · [Zgłoś problem](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Wesprzyj projekt · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Tłumaczenia

Aplikacja zawiera 36 języków interfejsu offline. Wybierz tłumaczenie tej strony projektu poniżej.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
