# DNA Workbench Suite

**DNA ファイル、家族記録、研究ワークフローを 1 つのローカル ワークスペースにまとめます。**

[ダウンロード](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [ウェブサイト](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ja) · [インストールガイド](../GETTING_STARTED.md) · [翻訳](#translations)

ソースを個人およびプロバイダーごとに整理し、互換性のあるファイルを比較し、すべての分析の背後にある入力と結果を保管します。

![ライト モードとダーク モード、言語ピッカー、合成プロファイル ファイルを含むアプリ ツアー](../images/workspace-demo.gif)

[アプリツアーを見る](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ja#tour) · [スクリーンショットギャラリー](../GALLERY.md)

## できること

- DNA ファイル、フォルダー、サポートされているアーカイブをインポートします。何かをコピーまたは移動する前に、プロバイダー、形式、参照ビルドを確認してください。
- データセット、ドキュメント、結果をプロファイルごとにグループ化します。各ファイルの起源を記録します。直接の測定値を推定値から切り離して保管し、染色体コピーに変異が割り当てられた時点に注意してください。
- サンプルの品質を確認し、ソースを比較します。同じ参照ビルドを使用できるワークフロー用に、バージョン管理された BestDataset をビルドします。
- ゲノム ビューアを使用してバリアントとシーケンス ファイルを探索します。 DNA プロファイルを比較し、研究ノートを家族の記録や GEDCOM ファイルと関連付けます。
- 結果を入力およびログとともに保存します。後で使用できるようにレポートをエクスポートし、プロファイルをバックアップします。
- オプションのローカル アシスタントを使用して、ワークスペースを移動します。外部 AI を個別に構成できます。

[全機能カタログ](../FEATURES.md) · [サポートされている形式](../TOOL_FORMATS.md)

## ツールとその機能

これらは、スイートに統合されるか、起動できる選択されたツールです。利用できるかどうかはワークフローとオペレーティング システムによって異なります。一部のモジュールと参照データは個別にダウンロードされます。

| ツール | 何をするのか |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | SAM、BAM、および CRAM 形式のアライメントされたシーケンス ファイルを読み取り、インデックス付けし、検査します。 |
| [BCFtools](https://samtools.github.io/bcftools/) | VCF および BCF 形式のバリアント ファイルをフィルタリング、正規化、結合、検査します。 |
| [fastp](https://github.com/OpenGene/fastp) | FASTQ の読み取り品質をチェックし、読み取りをトリミングまたはフィルターできます。 |
| [mosdepth](https://github.com/brentp/mosdepth) | BAM および CRAM ファイルからの読み取りカバレッジを測定します。 |
| [MultiQC](https://seqera.io/multiqc/) | 複数の品質管理ツールからのレポートを 1 つのビューに結合します。 |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | バリアント フィルタリング、関連性、主成分分析などのタスクで遺伝子型データを処理します。 |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | 遺伝子型データを使用して、染色体の同じコピー上にどのバリアントがあるかを推測します。 |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | 共通の祖先から受け継いだ、一致する DNA セグメントを見つけます。染色体コピーに割り当てられたバリアントを含む遺伝子型データを使用します。 |
| [WhatsHap](https://github.com/whatshap/whatshap) | シーケンス読み取りを使用して、染色体コピーにバリアントを割り当てます。 |
| [Truvari](https://github.com/ACEnglish/truvari) | VCF ファイル内の構造バリアントを比較します。 |
| [IGV](https://igv.org/doc/desktop/) | 特定の位置に位置合わせされたリード、バリアント、およびその他のゲノム トラックを表示します。 |
| [JBrowse](https://jbrowse.org/jb2/) | リファレンス シーケンスとリンクされたトラックをインタラクティブに参照できます。 |
| [GenomeSpy](https://genomespy.app/) | ブラウザーのグラフィックスアクセラレーションを使用して、インタラクティブなゲノムチャートをレンダリングします。 |
| [Gramps](https://www.gramps-project.org/) | 系図記録、家系図、GEDCOM データを整理します。 |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | 選択可能なソースとアノテーターを使用してバリアントに注釈を付けます。 |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | 変異体が遺伝子、転写物、タンパク質にどのような影響を与えるかを予測します。 |
| [PharmCAT](https://pharmcat.org/) | サポートされている遺伝子型入力から薬理遺伝学研究レポートを作成します。 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | 互換性のある CPU および GPU ランタイムでオプションのローカル言語モデルを実行します。 |

[ツールのバージョンと前提条件](../VERSIONS.md)

## 始めましょう

オペレーティング システムとプロセッサに一致するパッケージを選択してください。リリース ページには、Windows、Linux、および macOS の x64 および ARM64 のダウンロードがリストされています。一部のビルドはプレビューです。

1. Windows で、アーカイブを抽出し、ランチャーを実行します。プロンプトが表示されたら、コアのセットアップを完了します。
2. Linux では、Python、GTK、WebKitGTK がインストールされた状態で付属のシェル ランチャーを起動します。
3. macOS では、抽出されたワークスペース ファイルの横にアプリを保持します。プレビューには、macOS 13 以降および Python 3.12 以降が必要です。
4. 付属の合成サンプルから始めて、個人ファイルを使用せずにワークフローを試してください。

[ダウンロード](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [インストールガイド](../GETTING_STARTED.md)

## コマンドラインと自動化

デスクトップ インターフェイス (CLI、JSON-RPC、および MCP) を通じて同じコマンド レジストリを使用します。ヘッドレス サービスはローカル マシン上で実行されます。デスクトップ ウィンドウを開かずにコマンドをリストし、そのスキーマを読み取ることができます。

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

オプションのアシスタントは、結果のナビゲートに役立ちます。その答えは、ソース データや検証済みの分析に代わるものではありません。

> ソフトウェアを研究します。結果は入力、メソッド、参照によって異なります。 DNA Workbench Suite は臨床診断を提供しません。

## プロジェクトとサポート

AI 支援を備えた Oktay Du / OD によって保守されます。

[プライバシー](../PRIVACY.md) · [セキュリティ](../../SECURITY.md) · [プロジェクトライセンス](../../LICENSE) · [問題を報告する](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

プロジェクトをサポートする · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## 翻訳

アプリには 36 のオフライン インターフェイス言語が含まれています。以下からこのプロジェクト ページの翻訳を選択してください。

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
