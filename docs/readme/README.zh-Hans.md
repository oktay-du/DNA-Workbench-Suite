# DNA Workbench Suite

**DNA 文件、家庭记录和研究工作流程集中在一个本地工作空间中。**

[下载](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [网站](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=zh-Hans) · [安装指南](../GETTING_STARTED.md) · [翻译](#translations)

按人和提供者组织您的资源，比较兼容的文件，并保留每次分析背后的输入和结果。

![具有明暗模式、语言选择器和合成配置文件的应用程序导览](../images/workspace-demo.gif)

[观看应用导览](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=zh-Hans#tour) · [截图库](../GALLERY.md)

## 你能做什么

- 导入 DNA 文件、文件夹和支持的档案。在复制或移动任何内容之前，请检查提供程序、格式和参考版本。
- 按配置文件对数据集、文档和结果进行分组。记录每个文件的来源。将直接测量值与推断值分开，并注意何时将变异分配给染色体拷贝。
- 检查样品质量并比较来源。为可以使用相同参考版本的工作流程构建版本化的 BestDataset。
- 使用基因组查看器探索变体和序列文件。比较 DNA 图谱并将研究笔记与家庭记录和 GEDCOM 文件联系起来。
- 保存结果及其输入和日志。导出报告并备份配置文件以供以后使用。
- 使用可选的本地助手来导航工作区。您可以单独配置外部AI。

[全功能目录](../FEATURES.md) · [支持的格式](../TOOL_FORMATS.md)

## 工具及其用途

这些是套件集成或可以启动的精选工具。可用性因工作流程和操作系统而异。某些模块和参考数据是单独下载的。

| 工具 | 它的作用 |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | 读取、索引和检查 SAM、BAM 和 CRAM 格式的比对测序文件。 |
| [BCFtools](https://samtools.github.io/bcftools/) | 过滤、规范化、组合和检查 VCF 和 BCF 格式的变体文件。 |
| [fastp](https://github.com/OpenGene/fastp) | 检查 FASTQ 读取质量并可以修剪或过滤读取。 |
| [mosdepth](https://github.com/brentp/mosdepth) | 测量 BAM 和 CRAM 文件的读取覆盖率。 |
| [MultiQC](https://seqera.io/multiqc/) | 将多个质量控制工具的报告合并到一个视图中。 |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | 使用基因型数据执行变异过滤、相关性和主成分分析等任务。 |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | 使用基因型数据来推断哪些变异位于染色体的同一副本上。 |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | 查找从共同祖先继承的匹配 DNA 片段。它使用基因型数据以及分配给染色体副本的变体。 |
| [WhatsHap](https://github.com/whatshap/whatshap) | 使用测序读数将变体分配给染色体拷贝。 |
| [Truvari](https://github.com/ACEnglish/truvari) | 比较 VCF 文件中的结构变体。 |
| [IGV](https://igv.org/doc/desktop/) | 显示特定位置的对齐读数、变体和其他基因组轨迹。 |
| [JBrowse](https://jbrowse.org/jb2/) | 允许您以交互方式浏览参考序列和链接的轨道。 |
| [GenomeSpy](https://genomespy.app/) | 通过浏览器图形加速呈现交互式基因组图表。 |
| [Gramps](https://www.gramps-project.org/) | 组织家谱记录、家谱和 GEDCOM 数据。 |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | 使用可选择的来源和注释器来注释变体。 |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | 预测变异如何影响基因、转录本和蛋白质。 |
| [PharmCAT](https://pharmcat.org/) | 根据支持的基因型输入生成药物遗传学研究报告。 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | 在兼容的 CPU 和 GPU 运行时上运行可选的本地语言模型。 |

[工具版本和先决条件](../VERSIONS.md)

## 开始使用

选择与您的操作系统和处理器相匹配的软件包。发布页面列出了 Windows、Linux 和 macOS 的 x64 和 ARM64 下载。有些版本是预览版。

1. 在 Windows 上，提取存档并运行启动器。出现提示时完成核心设置。
2. 在 Linux 上，启动安装了 Python、GTK 和 WebKitGTK 的附带 shell 启动器。
3. 在 macOS 上，将应用程序放在提取的工作区文件旁边。预览需要 macOS 13 或更高版本以及 Python 3.12 或更高版本。
4. 从包含的合成示例开始，在不使用个人文件的情况下尝试工作流程。

[下载](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [安装指南](../GETTING_STARTED.md)

## 命令行和自动化

通过桌面界面 CLI、JSON-RPC 和 MCP 使用相同的命令注册表。无头服务在本地计算机上运行。您可以列出命令并读取其架构，而无需打开桌面窗口。

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

可选的助手可以帮助您导航结果。它的答案不会取代源数据或经过验证的分析。

> 研究软件。结果取决于输入、方法和参考。 DNA Workbench Suite 不提供临床诊断。

## 项目与支持

由 Oktay Du / OD 在 AI 协助下维护。

[隐私](../PRIVACY.md) · [安全性](../../SECURITY.md) · [项目许可](../../LICENSE) · [报告问题](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

支持项目 · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## 翻译

该应用程序包括 36 种离线界面语言。在下面选择该项目页面的翻译。

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
