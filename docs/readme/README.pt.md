# DNA Workbench Suite

**Arquivos de DNA, registros familiares e fluxos de trabalho de pesquisa em um espaço de trabalho local.**

[Baixar](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Site](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=pt) · [Guia de instalação](../GETTING_STARTED.md) · [Traduções](#translations)

Organize suas fontes por pessoa e fornecedor, compare arquivos compatíveis e mantenha as entradas e os resultados por trás de cada análise.

![Tour pelo aplicativo com modo claro e escuro, seletor de idioma e arquivos de perfil sintético](../images/workspace-demo.gif)

[Assista ao tour do aplicativo](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=pt#tour) · [Galeria de capturas de tela](../GALLERY.md)

## O que você pode fazer

- Importe arquivos DNA, pastas e arquivos suportados. Revise o provedor, o formato e a construção de referência antes de copiar ou mover qualquer coisa.
- Agrupe conjuntos de dados, documentos e resultados por perfil. Registre a origem de cada arquivo. Mantenha as medições diretas separadas dos valores inferidos e observe quando as variantes foram atribuídas às cópias cromossômicas.
- Verifique a qualidade da amostra e compare as fontes. Crie um BestDataset com versão para fluxos de trabalho que podem usar a mesma construção de referência.
- Explore variantes e arquivos de sequência com visualizadores de genoma. Compare perfis de DNA e conecte notas de pesquisa com registros familiares e arquivos GEDCOM.
- Salve os resultados com suas entradas e logs. Exporte relatórios e faça backup de perfis para uso posterior.
- Use o assistente local opcional para navegar na área de trabalho. Você pode configurar a IA externa separadamente.

[Catálogo completo de recursos](../FEATURES.md) · [Formatos suportados](../TOOL_FORMATS.md)

## Ferramentas e o que elas fazem

Estas são ferramentas selecionadas que o pacote integra ou pode lançar. A disponibilidade varia de acordo com o fluxo de trabalho e o sistema operacional. Alguns módulos e dados de referência são downloads separados.

| Ferramenta | O que isso faz |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Lê, indexa e inspeciona arquivos de sequenciamento alinhados nos formatos SAM, BAM e CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Filtra, normaliza, combina e inspeciona arquivos variantes nos formatos VCF e BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Verifica a qualidade de leitura do FASTQ e pode cortar ou filtrar leituras. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mede a cobertura de leitura dos arquivos BAM e CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Combina relatórios de diversas ferramentas de controle de qualidade em uma única visualização. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Trabalha com dados genotípicos para tarefas como filtragem de variantes, parentesco e análise de componentes principais. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Usa dados genotípicos para inferir quais variantes estão na mesma cópia de um cromossomo. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Encontra segmentos de DNA correspondentes herdados de um ancestral comum. Ele usa dados genotípicos com variantes atribuídas a cópias cromossômicas. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Usa leituras de sequenciamento para atribuir variantes às cópias dos cromossomos. |
| [Truvari](https://github.com/ACEnglish/truvari) | Compara variantes estruturais em arquivos VCF. |
| [IGV](https://igv.org/doc/desktop/) | Exibe leituras alinhadas, variantes e outros rastros de genoma em locais específicos. |
| [JBrowse](https://jbrowse.org/jb2/) | Permite navegar interativamente por sequências de referência e trilhas vinculadas. |
| [GenomeSpy](https://genomespy.app/) | Renderiza gráficos genômicos interativos com aceleração gráfica do navegador. |
| [Gramps](https://www.gramps-project.org/) | Organiza registros genealógicos, árvores genealógicas e dados GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Anota variantes usando fontes e anotadores selecionáveis. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Prevê como as variantes podem afetar genes, transcrições e proteínas. |
| [PharmCAT](https://pharmcat.org/) | Produz relatórios de pesquisa farmacogenética a partir de informações genotípicas apoiadas. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Executa o modelo de idioma local opcional em tempos de execução de CPU e GPU compatíveis. |

[Versões e pré-requisitos da ferramenta](../VERSIONS.md)

## Comece

Escolha o pacote que corresponde ao seu sistema operacional e processador. A página de lançamento lista downloads de x64 e ARM64 para Windows, Linux e macOS. Algumas compilações são visualizações.

1. No Windows, extraia o arquivo e execute o inicializador. Conclua a configuração do Core quando solicitado.
2. No Linux, inicie o iniciador de shell incluído com Python, GTK e WebKitGTK instalados.
3. No macOS, mantenha o aplicativo ao lado dos arquivos extraídos do espaço de trabalho. A visualização requer macOS 13 ou posterior e Python 3.12 ou posterior.
4. Comece com as amostras sintéticas incluídas para testar os fluxos de trabalho sem usar arquivos pessoais.

[Baixar](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Guia de instalação](../GETTING_STARTED.md)

## Linha de comando e automação

Use o mesmo registro de comando por meio da interface da área de trabalho, CLI, JSON-RPC e MCP. O serviço headless é executado na máquina local. Você pode listar comandos e ler seus esquemas sem abrir uma janela da área de trabalho.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

O assistente opcional pode ajudá-lo a navegar pelos resultados. Suas respostas não substituem os dados originais ou uma análise verificada.

> Software de pesquisa. Os resultados dependem da entrada, método e referências. DNA Workbench Suite não fornece um diagnóstico clínico.

## Projeto e suporte

Mantido por Oktay Du / OD com assistência de IA.

[Privacidade](../PRIVACY.md) · [Segurança](../../SECURITY.md) · [Licença do projeto](../../LICENSE) · [Informar um problema](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Apoie o projeto · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Traduções

O aplicativo inclui 36 idiomas de interface offline. Escolha uma tradução desta página do projeto abaixo.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
