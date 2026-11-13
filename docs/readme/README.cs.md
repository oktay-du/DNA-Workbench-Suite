# DNA Workbench Suite

**Soubory DNA, rodinné záznamy a výzkumné pracovní postupy v jednom místním pracovním prostoru.**

[Stáhnout](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [webové stránky](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=cs) · [Průvodce instalací](../GETTING_STARTED.md) · [Překlady](#translations)

Uspořádejte své zdroje podle osob a poskytovatelů, porovnejte kompatibilní soubory a uchovejte vstupy a výsledky za každou analýzou.

![Prohlídka aplikací se světlým a tmavým režimem, výběrem jazyka a syntetickými profilovými soubory](../images/workspace-demo.gif)

[Podívejte se na prohlídku aplikace](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=cs#tour) · [Galerie snímků obrazovky](../GALLERY.md)

## Co můžeš dělat

- Importujte soubory DNA, složky a podporované archivy. Než cokoli zkopírujete nebo přesunete, zkontrolujte poskytovatele, formát a referenční sestavení.
- Seskupte datové sady, dokumenty a výsledky podle profilu. Zaznamenejte původ každého souboru. Udržujte přímá měření oddělená od odvozených hodnot a poznamenejte si, kdy byly ke kopiím chromozomů přiřazeny varianty.
- Zkontrolujte kvalitu vzorku a porovnejte zdroje. Sestavte verzovaný BestDataset pro pracovní postupy, které mohou používat stejné referenční sestavení.
- Prozkoumejte varianty a soubory sekvencí pomocí prohlížečů genomu. Porovnejte profily DNA a propojte výzkumné poznámky s rodinnými záznamy a soubory GEDCOM.
- Uložte výsledky s jejich vstupy a protokoly. Exportujte zprávy a zálohujte profily pro pozdější použití.
- K navigaci v pracovním prostoru použijte volitelného místního asistenta. Externí umělou inteligenci můžete nakonfigurovat samostatně.

[Kompletní katalog funkcí](../FEATURES.md) · [Podporované formáty](../TOOL_FORMATS.md)

## Nástroje a co dělají

Toto jsou vybrané nástroje, které sada integruje nebo může spustit. Dostupnost se liší podle pracovního postupu a operačního systému. Některé moduly a referenční data jsou samostatná stahování.

| Nástroj | Co to dělá |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Čte, indexuje a kontroluje zarovnané sekvenční soubory ve formátech SAM, BAM a CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtruje, normalizuje, kombinuje a kontroluje soubory variant ve formátech VCF a BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Kontroluje kvalitu čtení FASTQ a může ořezávat nebo filtrovat čtení. |
| [mosdepth](https://github.com/brentp/mosdepth) | Měří pokrytí čtení ze souborů BAM a CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Kombinuje zprávy z více nástrojů pro kontrolu kvality do jednoho zobrazení. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Pracuje s genotypovými daty pro úkoly, jako je filtrování variant, příbuznost a analýza hlavních komponent. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Používá genotypová data k odvození, které varianty leží na stejné kopii chromozomu. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Najde odpovídající segmenty DNA zděděné od společného předka. Využívá genotypová data s variantami přiřazenými ke kopiím chromozomů. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Používá čtení sekvencí k přiřazení variant ke kopiím chromozomů. |
| [Truvari](https://github.com/ACEnglish/truvari) | Porovná strukturální varianty v souborech VCF. |
| [IGV](https://igv.org/doc/desktop/) | Zobrazuje zarovnaná čtení, varianty a další stopy genomu na konkrétních místech. |
| [JBrowse](https://jbrowse.org/jb2/) | Umožňuje interaktivně procházet referenční sekvence a propojené stopy. |
| [GenomeSpy](https://genomespy.app/) | Vykresluje interaktivní genomické grafy s akcelerací grafiky prohlížeče. |
| [Gramps](https://www.gramps-project.org/) | Organizuje genealogické záznamy, rodokmeny a data GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Anotuje varianty pomocí volitelných zdrojů a anotátorů. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Předpovídá, jak mohou varianty ovlivnit geny, transkripty a proteiny. |
| [PharmCAT](https://pharmcat.org/) | Produkuje farmakogenetické výzkumné zprávy z podporovaných genotypových vstupů. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Spouští volitelný model místního jazyka na kompatibilních CPU a GPU runtime. |

[Verze nástrojů a předpoklady](../VERSIONS.md)

## Začněte

Vyberte balíček, který odpovídá vašemu operačnímu systému a procesoru. Stránka vydání uvádí soubory ke stažení x64 a ARM64 pro Windows, Linux a macOS. Některé sestavení jsou náhledy.

1. Na Windows rozbalte archiv a spusťte spouštěč. Po zobrazení výzvy dokončete nastavení jádra.
2. Na Linux spusťte přiložený spouštěč shellů s nainstalovanými Python, GTK a WebKitGTK.
3. Na macOS ponechte aplikaci vedle extrahovaných souborů pracovního prostoru. Náhled vyžaduje macOS 13 nebo novější a Python 3.12 nebo novější.
4. Začněte s přiloženými syntetickými vzorky a vyzkoušejte pracovní postupy bez použití osobních souborů.

[Stáhnout](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Průvodce instalací](../GETTING_STARTED.md)

## Příkazový řádek a automatizace

Použijte stejný registr příkazů prostřednictvím rozhraní plochy, CLI, JSON-RPC a MCP. Bezhlavá služba běží na místním počítači. Můžete vypisovat příkazy a číst jejich schémata, aniž byste museli otevírat okno plochy.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Volitelný asistent vám může pomoci s navigací ve výsledcích. Jeho odpovědi nenahrazují zdrojová data ani ověřenou analýzu.

> Výzkumný software. Výsledky závisí na vstupu, metodě a odkazech. DNA Workbench Suite neposkytuje klinickou diagnózu.

## Projekt a podpora

Spravuje Oktay Du / OD s pomocí AI.

[soukromí](../PRIVACY.md) · [Bezpečnost](../../SECURITY.md) · [Licence projektu](../../LICENSE) · [Nahlásit problém](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Podpořte projekt · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Překlady

Aplikace obsahuje 36 jazyků offline rozhraní. Níže vyberte překlad této stránky projektu.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
