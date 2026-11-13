# DNA Workbench Suite

**Archivos de ADN, registros familiares y flujos de trabajo de investigación en un espacio de trabajo local.**

[Descargar](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Sitio web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=es) · [guía de instalación](../GETTING_STARTED.md) · [Traducciones](#translations)

Organice sus fuentes por persona y proveedor, compare archivos compatibles y mantenga las entradas y los resultados detrás de cada análisis.

![Recorrido por la aplicación con modo claro y oscuro, selector de idioma y archivos de perfil sintéticos](../images/workspace-demo.gif)

[Mira el recorrido por la aplicación](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=es#tour) · [Galería de capturas de pantalla](../GALLERY.md)

## que puedes hacer

- Importe archivos, carpetas y archivos compatibles de DNA. Revise el proveedor, el formato y la compilación de referencia antes de copiar o mover algo.
- Agrupe conjuntos de datos, documentos y resultados por perfil. Registre el origen de cada archivo. Mantenga las mediciones directas separadas de los valores inferidos y observe cuándo se han asignado variantes a copias de cromosomas.
- Verifique la calidad de la muestra y compare fuentes. Cree un BestDataset versionado para flujos de trabajo que puedan usar la misma compilación de referencia.
- Explore variantes y archivos de secuencia con visores de genoma. Compare perfiles de ADN y conecte notas de investigación con registros familiares y archivos GEDCOM.
- Guarde los resultados con sus entradas y registros. Exporte informes y haga copias de seguridad de perfiles para su uso posterior.
- Utilice el asistente local opcional para navegar por el espacio de trabajo. Puede configurar la IA externa por separado.

[Catálogo completo de funciones](../FEATURES.md) · [Formatos soportados](../TOOL_FORMATS.md)

## Herramientas y lo que hacen.

Estas son herramientas seleccionadas que la suite integra o puede lanzar. La disponibilidad varía según el flujo de trabajo y el sistema operativo. Algunos módulos y datos de referencia se descargan por separado.

| Herramienta | que hace |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Lee, indexa e inspecciona archivos de secuenciación alineados en formatos SAM, BAM y CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtra, normaliza, combina e inspecciona archivos variantes en formatos VCF y BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Comprueba la calidad de lectura de FASTQ y puede recortar o filtrar lecturas. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mide la cobertura de lectura de archivos BAM y CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Combina informes de múltiples herramientas de control de calidad en una sola vista. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Trabaja con datos de genotipo para tareas como filtrado de variantes, análisis de relaciones y componentes principales. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Utiliza datos de genotipo para inferir qué variantes se encuentran en la misma copia de un cromosoma. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Encuentra segmentos de ADN coincidentes heredados de un ancestro común. Utiliza datos de genotipo con variantes asignadas a copias de cromosomas. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Utiliza lecturas de secuenciación para asignar variantes a copias de cromosomas. |
| [Truvari](https://github.com/ACEnglish/truvari) | Compara variantes estructurales en archivos VCF. |
| [IGV](https://igv.org/doc/desktop/) | Muestra lecturas alineadas, variantes y otras pistas del genoma en ubicaciones específicas. |
| [JBrowse](https://jbrowse.org/jb2/) | Le permite explorar secuencias de referencia y pistas vinculadas de forma interactiva. |
| [GenomeSpy](https://genomespy.app/) | Representa gráficos genómicos interactivos con aceleración de gráficos del navegador. |
| [Gramps](https://www.gramps-project.org/) | Organiza registros genealógicos, árboles genealógicos y datos GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Anota variantes utilizando fuentes y anotadores seleccionables. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Predice cómo las variantes pueden afectar genes, transcripciones y proteínas. |
| [PharmCAT](https://pharmcat.org/) | Produce informes de investigación farmacogenética a partir de aportaciones de genotipos compatibles. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Ejecuta el modelo de idioma local opcional en tiempos de ejecución de CPU y GPU compatibles. |

[Versiones de herramientas y requisitos previos](../VERSIONS.md)

## empezar

Elija el paquete que coincida con su sistema operativo y procesador. La página de lanzamiento enumera las descargas de x64 y ARM64 para Windows, Linux y macOS. Algunas compilaciones son vistas previas.

1. En Windows, extraiga el archivo y ejecute el iniciador. Complete la configuración del Core cuando se le solicite.
2. En Linux, inicie el iniciador de shell incluido con Python, GTK y WebKitGTK instalados.
3. En macOS, mantenga la aplicación junto a los archivos del espacio de trabajo extraídos. La versión preliminar requiere macOS 13 o posterior y Python 3.12 o posterior.
4. Comience con las muestras sintéticas incluidas para probar los flujos de trabajo sin utilizar archivos personales.

[Descargar](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [guía de instalación](../GETTING_STARTED.md)

## Línea de comando y automatización

Utilice el mismo registro de comandos a través de la interfaz de escritorio, CLI, JSON-RPC y MCP. El servicio sin cabeza se ejecuta en la máquina local. Puede enumerar comandos y leer sus esquemas sin abrir una ventana del escritorio.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

El asistente opcional puede ayudarle a navegar por los resultados. Sus respuestas no reemplazan los datos originales ni un análisis verificado.

> Software de investigación. Los resultados dependen de la entrada, el método y las referencias. DNA Workbench Suite no proporciona un diagnóstico clínico.

## Proyecto y soporte

Mantenido por Oktay Du / OD con asistencia de IA.

[Privacidad](../PRIVACY.md) · [Seguridad](../../SECURITY.md) · [Licencia de proyecto](../../LICENSE) · [Informar un problema](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Apoya el proyecto · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Traducciones

La aplicación incluye 36 idiomas de interfaz sin conexión. Elija una traducción de la página de este proyecto a continuación.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
