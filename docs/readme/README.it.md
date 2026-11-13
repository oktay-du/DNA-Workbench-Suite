# DNA Workbench Suite

**File del DNA, documenti di famiglia e flussi di lavoro di ricerca in un unico spazio di lavoro locale.**

[Scarica](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Sito web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=it) · [Guida all'installazione](../GETTING_STARTED.md) · [Traduzioni](#translations)

Organizza le tue fonti per persona e fornitore, confronta file compatibili e mantieni gli input e i risultati dietro ogni analisi.

![Tour dell'app con modalità chiaro e scuro, selettore della lingua e file di profilo sintetici](../images/workspace-demo.gif)

[Guarda il tour dell'app](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=it#tour) · [Galleria di schermate](../GALLERY.md)

## Cosa puoi fare

- Importa file DNA, cartelle e archivi supportati. Controlla il provider, il formato e la build di riferimento prima di copiare o spostare qualsiasi cosa.
- Raggruppare set di dati, documenti e risultati per profilo. Registra l'origine di ogni file. Mantenere le misurazioni dirette separate dai valori dedotti e annotare quando le varianti sono state assegnate alle copie cromosomiche.
- Controlla la qualità del campione e confronta le fonti. Crea uno BestDataset con versione per flussi di lavoro che possono utilizzare la stessa build di riferimento.
- Esplora varianti e file di sequenza con i visualizzatori di genomi. Confronta i profili del DNA e collega gli appunti di ricerca con i documenti di famiglia e i file GEDCOM.
- Salva i risultati con i relativi input e registri. Esporta report ed esegui il backup dei profili per un utilizzo successivo.
- Utilizza l'assistente locale opzionale per navigare nell'area di lavoro. È possibile configurare l'IA esterna separatamente.

[Catalogo completo delle funzionalità](../FEATURES.md) · [Formati supportati](../TOOL_FORMATS.md)

## Strumenti e cosa fanno

Questi sono gli strumenti selezionati che la suite integra o può avviare. La disponibilità varia in base al flusso di lavoro e al sistema operativo. Alcuni moduli e dati di riferimento sono download separati.

| Strumento | Cosa fa |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Legge, indicizza e ispeziona file di sequenziamento allineati nei formati SAM, BAM e CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtra, normalizza, combina e controlla i file varianti nei formati VCF e BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Controlla la qualità di lettura di FASTQ e può tagliare o filtrare le letture. |
| [mosdepth](https://github.com/brentp/mosdepth) | Misura la copertura in lettura dai file BAM e CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Combina i report di più strumenti di controllo qualità in un'unica visualizzazione. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Funziona con dati genotipici per attività quali filtraggio delle varianti, correlazione e analisi delle componenti principali. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Utilizza i dati del genotipo per dedurre quali varianti si trovano sulla stessa copia di un cromosoma. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Trova segmenti di DNA corrispondenti ereditati da un antenato comune. Utilizza dati genotipici con varianti assegnate a copie cromosomiche. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Utilizza letture di sequenziamento per assegnare varianti alle copie cromosomiche. |
| [Truvari](https://github.com/ACEnglish/truvari) | Confronta le varianti strutturali nei file VCF. |
| [IGV](https://igv.org/doc/desktop/) | Visualizza letture allineate, varianti e altre tracce del genoma in posizioni specifiche. |
| [JBrowse](https://jbrowse.org/jb2/) | Consente di sfogliare le sequenze di riferimento e le tracce collegate in modo interattivo. |
| [GenomeSpy](https://genomespy.app/) | Rende grafici genomici interattivi con l'accelerazione grafica del browser. |
| [Gramps](https://www.gramps-project.org/) | Organizza documenti genealogici, alberi genealogici e dati GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Annota le varianti utilizzando fonti e annotatori selezionabili. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Prevede il modo in cui le varianti possono influenzare geni, trascritti e proteine. |
| [PharmCAT](https://pharmcat.org/) | Produce rapporti di ricerca sulla farmacogenetica da input di genotipo supportati. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Esegue il modello in lingua locale opzionale su runtime CPU e GPU compatibili. |

[Versioni e prerequisiti dello strumento](../VERSIONS.md)

## Inizia

Scegli il pacchetto che corrisponde al tuo sistema operativo e processore. La pagina di rilascio elenca i download di x64 e ARM64 per Windows, Linux e macOS. Alcune build sono anteprime.

1. Su Windows, estrai l'archivio ed esegui il launcher. Completa la configurazione del Core quando richiesto.
2. Su Linux, avvia il launcher della shell incluso con Python, GTK e WebKitGTK installati.
3. Su macOS, mantieni l'app accanto ai file dell'area di lavoro estratti. L'anteprima richiede macOS 13 o successivo e Python 3.12 o successivo.
4. Inizia con i campioni sintetici inclusi per provare i flussi di lavoro senza utilizzare file personali.

[Scarica](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Guida all'installazione](../GETTING_STARTED.md)

## Riga di comando e automazione

Utilizzare lo stesso registro dei comandi tramite l'interfaccia desktop, CLI, JSON-RPC e MCP. Il servizio headless viene eseguito sul computer locale. Puoi elencare i comandi e leggerne gli schemi senza aprire una finestra del desktop.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

L'assistente opzionale può aiutarti a navigare tra i risultati. Le sue risposte non sostituiscono i dati di origine o un'analisi verificata.

> Software di ricerca. I risultati dipendono dall'input, dal metodo e dai riferimenti. DNA Workbench Suite non fornisce una diagnosi clinica.

## Progetto e sostegno

Mantenuto da Oktay Du / OD con assistenza AI.

[Privacy](../PRIVACY.md) · [Sicurezza](../../SECURITY.md) · [Licenza del progetto](../../LICENSE) · [Segnala un problema](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Sostieni il progetto · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Traduzioni

L'app include 36 lingue di interfaccia offline. Scegli una traduzione della pagina di questo progetto qui sotto.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
