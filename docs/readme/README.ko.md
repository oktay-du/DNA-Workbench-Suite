# DNA Workbench Suite

**단일 로컬 작업 공간에서 DNA 파일, 가족 기록, 연구 워크플로우를 관리하세요.**

[다운로드](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [웹사이트](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ko) · [설치 가이드](../GETTING_STARTED.md) · [번역](#translations)

사람과 공급자별로 소스를 정리하고, 호환되는 파일을 비교하고, 모든 분석 뒤에 입력과 결과를 보관하세요.

![밝은 모드와 어두운 모드, 언어 선택기 및 합성 프로필 파일이 포함된 앱 둘러보기](../images/workspace-demo.gif)

[앱 둘러보기](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ko#tour) · [스크린샷 갤러리](../GALLERY.md)

## 당신이 할 수 있는 일

- DNA 파일, 폴더 및 지원되는 아카이브를 가져옵니다. 무엇이든 복사하거나 이동하기 전에 공급자, 형식 및 참조 빌드를 검토하세요.
- 데이터 세트, 문서 및 결과를 프로필별로 그룹화합니다. 각 파일의 출처를 기록합니다. 추론된 값과 별도로 직접 측정값을 유지하고 변이가 염색체 복사본에 할당된 경우를 기록해 두십시오.
- 샘플 품질을 확인하고 소스를 비교하세요. 동일한 참조 빌드를 사용할 수 있는 워크플로에 대해 버전이 지정된 BestDataset를 빌드합니다.
- 게놈 뷰어를 사용하여 변형 및 서열 파일을 탐색하십시오. DNA 프로필을 비교하고 연구 노트를 가족 기록 및 GEDCOM 파일과 연결하세요.
- 입력 및 로그와 함께 결과를 저장합니다. 나중에 사용할 수 있도록 보고서를 내보내고 프로필을 백업하세요.
- 선택 사항인 로컬 도우미를 사용하여 작업 공간을 탐색하세요. 외부 AI를 별도로 구성할 수 있습니다.

[전체 기능 카탈로그](../FEATURES.md) · [지원되는 형식](../TOOL_FORMATS.md)

## 도구와 그 역할

이는 제품군이 통합하거나 실행할 수 있는 선택된 도구입니다. 가용성은 워크플로 및 운영 체제에 따라 다릅니다. 일부 모듈과 참조 데이터는 별도로 다운로드됩니다.

| 도구 | 기능 |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | SAM, BAM 및 CRAM 형식의 정렬된 시퀀싱 파일을 읽고 색인화하고 검사합니다. |
| [BCFtools](https://samtools.github.io/bcftools/) | VCF 및 BCF 형식의 변형 파일을 필터링, 정규화, 결합 및 검사합니다. |
| [fastp](https://github.com/OpenGene/fastp) | FASTQ 읽기 품질을 확인하고 읽기를 자르거나 필터링할 수 있습니다. |
| [mosdepth](https://github.com/brentp/mosdepth) | BAM 및 CRAM 파일의 읽기 범위를 측정합니다. |
| [MultiQC](https://seqera.io/multiqc/) | 여러 품질 관리 도구의 보고서를 하나의 보기로 결합합니다. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | 변형 필터링, 관련성, 주성분 분석 등의 작업을 위해 유전자형 데이터를 사용합니다. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | 유전자형 데이터를 사용하여 어떤 변이가 동일한 염색체 복사본에 있는지 추론합니다. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | 공통 조상으로부터 물려받은 일치하는 DNA 세그먼트를 찾습니다. 염색체 복사본에 할당된 변이가 있는 유전자형 데이터를 사용합니다. |
| [WhatsHap](https://github.com/whatshap/whatshap) | 시퀀싱 읽기를 사용하여 변이체를 염색체 복사본에 할당합니다. |
| [Truvari](https://github.com/ACEnglish/truvari) | VCF 파일의 구조적 변형을 비교합니다. |
| [IGV](https://igv.org/doc/desktop/) | 특정 위치에 정렬된 읽기, 변형 및 기타 게놈 트랙을 표시합니다. |
| [JBrowse](https://jbrowse.org/jb2/) | 참조 시퀀스와 연결된 트랙을 대화식으로 찾아볼 수 있습니다. |
| [GenomeSpy](https://genomespy.app/) | 브라우저 그래픽 가속을 통해 대화형 게놈 차트를 렌더링합니다. |
| [Gramps](https://www.gramps-project.org/) | 계보 기록, 가계도 및 GEDCOM 데이터를 구성합니다. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | 선택 가능한 소스와 주석자를 사용하여 변형에 주석을 답니다. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | 변이체가 유전자, 전사체 및 단백질에 어떻게 영향을 미칠 수 있는지 예측합니다. |
| [PharmCAT](https://pharmcat.org/) | 지원되는 유전자형 입력을 통해 약물유전학 연구 보고서를 생성합니다. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | 호환 가능한 CPU 및 GPU 런타임에서 선택적 로컬 언어 모델을 실행합니다. |

[도구 버전 및 필수 구성 요소](../VERSIONS.md)

## 시작하기

운영 체제 및 프로세서와 일치하는 패키지를 선택하십시오. 릴리스 페이지에는 Windows, Linux 및 macOS에 대한 x64 및 ARM64 다운로드가 나열되어 있습니다. 일부 빌드는 미리보기입니다.

1. Windows에서 아카이브를 추출하고 런처를 실행합니다. 메시지가 표시되면 Core 설정을 완료합니다.
2. Linux에서 Python, GTK 및 WebKitGTK가 설치된 포함된 셸 실행 프로그램을 시작합니다.
3. macOS에서 추출된 작업 공간 파일 옆에 앱을 유지합니다. 미리보기에는 macOS 13 이상 및 Python 3.12 이상이 필요합니다.
4. 포함된 합성 샘플로 시작하여 개인 파일을 사용하지 않고 워크플로를 시도해 보세요.

[다운로드](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [설치 가이드](../GETTING_STARTED.md)

## 명령줄 및 자동화

데스크탑 인터페이스 CLI, JSON-RPC 및 MCP를 통해 동일한 명령 레지스트리를 사용합니다. 헤드리스 서비스는 로컬 시스템에서 실행됩니다. 데스크톱 창을 열지 않고도 명령을 나열하고 해당 스키마를 읽을 수 있습니다.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

선택적 도우미는 결과를 탐색하는 데 도움을 줄 수 있습니다. 그 답변은 원본 데이터나 검증된 분석을 대체하지 않습니다.

> 연구 소프트웨어. 결과는 입력, 방법 및 참조에 따라 달라집니다. DNA Workbench Suite는 임상 진단을 제공하지 않습니다.

## 프로젝트 및 지원

AI 지원을 통해 Oktay Du / OD에서 유지관리합니다.

[개인 정보 보호](../PRIVACY.md) · [보안](../../SECURITY.md) · [프로젝트 라이선스](../../LICENSE) · [문제 신고](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

프로젝트를 지원하세요 · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## 번역

이 앱에는 36개의 오프라인 인터페이스 언어가 포함되어 있습니다. 아래에서 이 프로젝트 페이지의 번역을 선택하세요.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
