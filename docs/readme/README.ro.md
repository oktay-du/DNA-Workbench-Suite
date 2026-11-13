# DNA Workbench Suite

**Fișiere ADN, înregistrări de familie și fluxuri de lucru de cercetare într-un singur spațiu de lucru local.**

[Descărcați](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Site-ul web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ro) · [Ghid de instalare](../GETTING_STARTED.md) · [Traduceri](#translations)

Organizați-vă sursele după persoană și furnizor, comparați fișierele compatibile și păstrați intrările și rezultatele în spatele fiecărei analize.

![Tur al aplicației cu modul de lumină și întuneric, selectorul de limbă și fișierele de profil sintetice](../images/workspace-demo.gif)

[Urmărește turul aplicației](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ro#tour) · [Galerie de capturi de ecran](../GALLERY.md)

## Ce poți face

- Importați fișiere ADN, foldere și arhive acceptate. Examinați furnizorul, formatați și versiunea de referință înainte de a copia sau muta ceva.
- Grupați seturi de date, documente și rezultate după profil. Înregistrați originea fiecărui fișier. Păstrați măsurătorile directe separate de valorile deduse și notați când variantele au fost atribuite copiilor cromozomilor.
- Verificați calitatea probei și comparați sursele. Creați o versiune BestDataset pentru fluxuri de lucru care pot folosi aceeași versiune de referință.
- Explorați variante și fișiere de secvență cu vizualizatoare de genom. Comparați profilurile ADN și conectați notele de cercetare cu înregistrările de familie și fișierele GEDCOM.
- Salvați rezultatele cu intrările și jurnalele lor. Exportați rapoarte și faceți copii de rezervă ale profilurilor pentru utilizare ulterioară.
- Utilizați asistentul local opțional pentru a naviga în spațiul de lucru. Puteți configura AI extern separat.

[Catalog complet de caracteristici](../FEATURES.md) · [Formate acceptate](../TOOL_FORMATS.md)

## Instrumente și ceea ce fac

Acestea sunt instrumente selectate pe care suita le integrează sau le poate lansa. Disponibilitatea variază în funcție de fluxul de lucru și sistemul de operare. Unele module și date de referință sunt descărcări separate.

| Instrument | Ce face |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Citește, indexează și inspectează fișierele de secvențiere aliniate în formatele SAM, BAM și CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtrează, normalizează, combină și inspectează fișierele variante în formatele VCF și BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Verifică calitatea citirii FASTQ și poate tăia sau filtra citirile. |
| [mosdepth](https://github.com/brentp/mosdepth) | Măsoară acoperirea de citire din fișierele BAM și CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Combină rapoartele din mai multe instrumente de control al calității într-o singură vizualizare. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Funcționează cu date genotipului pentru sarcini precum filtrarea variantelor, înrudirea și analiza componentelor principale. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Utilizează datele genotipului pentru a deduce care variante se află pe aceeași copie a unui cromozom. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Găsește segmente de ADN care se potrivesc moștenite de la un strămoș comun. Utilizează datele genotipului cu variante atribuite copiilor cromozomilor. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Utilizează citirile de secvențiere pentru a atribui variante copiilor cromozomilor. |
| [Truvari](https://github.com/ACEnglish/truvari) | Compară variantele structurale din fișierele VCF. |
| [IGV](https://igv.org/doc/desktop/) | Afișează citiri aliniate, variante și alte urme ale genomului în anumite locații. |
| [JBrowse](https://jbrowse.org/jb2/) | Vă permite să răsfoiți interactiv secvențele de referință și melodiile legate. |
| [GenomeSpy](https://genomespy.app/) | Redă diagrame genomice interactive cu accelerarea grafică a browserului. |
| [Gramps](https://www.gramps-project.org/) | Organizează înregistrările genealogice, arbori genealogic și date GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Adnotează variante folosind surse și adnotatori selectabili. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Prezice modul în care variantele pot afecta genele, transcrierile și proteinele. |
| [PharmCAT](https://pharmcat.org/) | Produce rapoarte de cercetare farmacogenetică din intrări de genotip susținute. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Rulează modelul opțional în limba locală pe timpii de execuție compatibile cu CPU și GPU. |

[Versiuni de instrumente și cerințe preliminare](../VERSIONS.md)

## Începeți

Alegeți pachetul care se potrivește cu sistemul de operare și procesorul dvs. Pagina de lansare listează descărcări x64 și ARM64 pentru Windows, Linux și macOS. Unele versiuni sunt previzualizări.

1. Pe Windows, extrageți arhiva și rulați lansatorul. Finalizați configurarea Core când vi se solicită.
2. Pe Linux, porniți lansatorul shell inclus cu Python, GTK și WebKitGTK instalate.
3. Pe macOS, păstrați aplicația lângă fișierele din spațiul de lucru extrase. Previzualizarea necesită macOS 13 sau o versiune ulterioară și Python 3.12 sau o versiune ulterioară.
4. Începeți cu mostrele sintetice incluse pentru a încerca fluxurile de lucru fără a utiliza fișiere personale.

[Descărcați](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Ghid de instalare](../GETTING_STARTED.md)

## Linie de comandă și automatizare

Utilizați același registru de comenzi prin interfața desktop, CLI, JSON-RPC și MCP. Serviciul fără cap rulează pe mașina locală. Puteți enumera comenzi și puteți citi schemele acestora fără a deschide o fereastră de pe desktop.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Asistentul opțional vă poate ajuta să navigați prin rezultate. Răspunsurile sale nu înlocuiesc datele sursă sau o analiză verificată.

> Software de cercetare. Rezultatele depind de intrare, metodă și referințe. DNA Workbench Suite nu oferă un diagnostic clinic.

## Proiect și sprijin

Întreținut de Oktay Du / OD cu asistență AI.

[Confidențialitate](../PRIVACY.md) · [Securitate](../../SECURITY.md) · [Licență de proiect](../../LICENSE) · [Raportați o problemă](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Susține proiectul · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Traduceri

Aplicația include 36 de limbi de interfață offline. Alegeți mai jos o traducere a acestei pagini de proiect.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
