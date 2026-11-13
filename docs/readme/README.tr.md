# DNA Workbench Suite

**DNA dosyaları, aile kayıtları ve araştırma iş akışları tek bir yerel çalışma alanında.**

[İndir](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Web sitesi](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=tr) · [Kurulum kılavuzu](../GETTING_STARTED.md) · [Çeviriler](#translations)

Kaynaklarınızı kişiye ve sağlayıcıya göre düzenleyin, uyumlu dosyaları karşılaştırın ve girdileri ve sonuçları her analizin arkasında tutun.

![Açık ve koyu mod, dil seçici ve sentetik profil dosyalarıyla uygulama turu](../images/workspace-demo.gif)

[Uygulama turunu izleyin](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=tr#tour) · [Ekran görüntüsü galerisi](../GALLERY.md)

## Ne yapabilirsin

- DNA dosyalarını, klasörlerini ve desteklenen arşivleri içe aktarın. Herhangi bir şeyi kopyalamadan veya taşımadan önce sağlayıcıyı, formatı ve referans yapısını inceleyin.
- Veri kümelerini, belgeleri ve sonuçları profile göre gruplayın. Her dosyanın kaynağını kaydedin. Doğrudan ölçümleri, çıkarsanan değerlerden ayrı tutun ve varyantların kromozom kopyalarına ne zaman atandığını not edin.
- Örnek kalitesini kontrol edin ve kaynakları karşılaştırın. Aynı referans yapısını kullanabilen iş akışları için sürümlendirilmiş bir BestDataset oluşturun.
- Genom görüntüleyicilerle varyantları ve dizi dosyalarını keşfedin. DNA profillerini karşılaştırın ve araştırma notlarını aile kayıtları ve GEDCOM dosyalarıyla birleştirin.
- Sonuçları girdileri ve günlükleriyle birlikte kaydedin. Raporları dışa aktarın ve profilleri daha sonra kullanmak üzere yedekleyin.
- Çalışma alanında gezinmek için isteğe bağlı yerel asistanı kullanın. Harici AI'yi ayrı olarak yapılandırabilirsiniz.

[Tam özellik kataloğu](../FEATURES.md) · [Desteklenen formatlar](../TOOL_FORMATS.md)

## Araçlar ve yaptıkları

Bunlar, paketin entegre ettiği veya başlatabileceği seçilmiş araçlardır. Kullanılabilirlik iş akışına ve işletim sistemine göre değişir. Bazı modüller ve referans verileri ayrı indirmelerdir.

| Araç | Ne işe yarar |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | SAM, BAM ve CRAM formatlarındaki hizalanmış sıralama dosyalarını okur, indeksler ve inceler. |
| [BCFtools](https://samtools.github.io/bcftools/) | VCF ve BCF formatlarındaki değişken dosyaları filtreler, normalleştirir, birleştirir ve inceler. |
| [fastp](https://github.com/OpenGene/fastp) | FASTQ okuma kalitesini kontrol eder ve okumaları kırpabilir veya filtreleyebilir. |
| [mosdepth](https://github.com/brentp/mosdepth) | BAM ve CRAM dosyalarından okuma kapsamını ölçer. |
| [MultiQC](https://seqera.io/multiqc/) | Birden fazla kalite kontrol aracından gelen raporları tek bir görünümde birleştirir. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Varyant filtreleme, ilişki ve temel bileşen analizi gibi görevler için genotip verileriyle çalışır. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Bir kromozomun aynı kopyasında hangi varyantların bulunduğunu anlamak için genotip verilerini kullanır. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Ortak bir atadan miras kalan eşleşen DNA parçalarını bulur. Kromozom kopyalarına atanan varyantlarla birlikte genotip verilerini kullanır. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Varyantları kromozom kopyalarına atamak için sıralama okumalarını kullanır. |
| [Truvari](https://github.com/ACEnglish/truvari) | VCF dosyalarındaki yapısal değişkenleri karşılaştırır. |
| [IGV](https://igv.org/doc/desktop/) | Belirli konumlardaki hizalanmış okumaları, varyantları ve diğer genom izlerini görüntüler. |
| [JBrowse](https://jbrowse.org/jb2/) | Referans dizilerine ve bağlantılı parçalara etkileşimli olarak göz atmanızı sağlar. |
| [GenomeSpy](https://genomespy.app/) | Tarayıcı grafik hızlandırmasıyla etkileşimli genomik çizelgeler oluşturur. |
| [Gramps](https://www.gramps-project.org/) | Şecere kayıtlarını, aile ağaçlarını ve GEDCOM verilerini düzenler. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Seçilebilir kaynakları ve ek açıklamaları kullanarak varyantlara açıklama ekler. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Varyantların genleri, transkriptleri ve proteinleri nasıl etkileyebileceğini tahmin eder. |
| [PharmCAT](https://pharmcat.org/) | Desteklenen genotip girdilerinden farmakogenetik araştırma raporları üretir. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | İsteğe bağlı yerel dil modelini uyumlu CPU ve GPU çalışma zamanlarında çalıştırır. |

[Araç sürümleri ve önkoşullar](../VERSIONS.md)

## Başlayın

İşletim sisteminize ve işlemcinize uygun paketi seçin. Sürüm sayfası, Windows, Linux ve macOS için x64 ve ARM64 indirmelerini listeler. Bazı yapılar önizlemedir.

1. Windows'de arşivi çıkarın ve başlatıcıyı çalıştırın. İstendiğinde Çekirdek kurulumunu tamamlayın.
2. Linux'de, Python, GTK ve WebKitGTK kurulu olarak birlikte verilen kabuk başlatıcıyı başlatın.
3. macOS'de uygulamayı çıkarılan çalışma alanı dosyalarının yanında tutun. Önizleme, macOS 13 veya üzerini ve Python 3.12 veya üzerini gerektirir.
4. Kişisel dosyaları kullanmadan iş akışlarını denemek için dahil edilen sentetik örneklerle başlayın.

[İndir](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Kurulum kılavuzu](../GETTING_STARTED.md)

## Komut satırı ve otomasyon

CLI, JSON-RPC ve MCP masaüstü arayüzü aracılığıyla aynı komut kaydını kullanın. Başsız hizmet yerel makinede çalışır. Bir masaüstü penceresi açmadan komutları listeleyebilir ve şemalarını okuyabilirsiniz.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

İsteğe bağlı asistan, sonuçlarda gezinmenize yardımcı olabilir. Cevapları kaynak verilerin veya doğrulanmış bir analizin yerini almaz.

> Yazılımı araştırın. Sonuçlar girdiye, yönteme ve referanslara bağlıdır. DNA Workbench Suite klinik bir tanı sağlamaz.

## Proje ve destek

Yapay zeka yardımıyla Oktay Du / OD tarafından bakımı yapılıyor.

[Gizlilik](../PRIVACY.md) · [Güvenlik](../../SECURITY.md) · [Proje lisansı](../../LICENSE) · [Sorun bildir](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Projeyi destekleyin · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Çeviriler

Uygulama 36 çevrimdışı arayüz dili içerir. Aşağıdan bu proje sayfasının çevirisini seçin.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
