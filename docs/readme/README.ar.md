<div dir="rtl" lang="ar">

# DNA Workbench Suite

**ملفات الحمض النووي وسجلات العائلة وسير العمل البحثي في ​​مساحة عمل محلية واحدة.**

[تحميل](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [موقع الكتروني](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ar) · [دليل التثبيت](../GETTING_STARTED.md) · [ترجمات](#translations)

قم بتنظيم مصادرك حسب الشخص والمزود، وقارن بين الملفات المتوافقة، واحتفظ بالمدخلات والنتائج وراء كل تحليل.

![جولة في التطبيق مع الوضع الفاتح والداكن ومنتقي اللغة وملفات التعريف الاصطناعية](../images/workspace-demo.gif)

[شاهد جولة التطبيق](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ar#tour) · [معرض لقطة الشاشة](../GALLERY.md)

## ما يمكنك القيام به

- استيراد ملفات DNA والمجلدات والمحفوظات المدعومة. قم بمراجعة الموفر والتنسيق والبنية المرجعية قبل نسخ أي شيء أو نقله.
- تجميع مجموعات البيانات والمستندات والنتائج حسب الملف الشخصي. سجل أصل كل ملف. احتفظ بالقياسات المباشرة منفصلة عن القيم المستنتجة ولاحظ متى تم تعيين المتغيرات لنسخ الكروموسوم.
- التحقق من جودة العينة ومقارنة المصادر. قم بإنشاء إصدار BestDataset لسير العمل الذي يمكنه استخدام نفس البنية المرجعية.
- استكشف المتغيرات وملفات التسلسل باستخدام مشاهدي الجينوم. قارن ملفات تعريف الحمض النووي واربط الملاحظات البحثية بسجلات العائلة وملفات GEDCOM.
- حفظ النتائج مع المدخلات والسجلات الخاصة بهم. تصدير التقارير وعمل نسخة احتياطية من الملفات الشخصية لاستخدامها لاحقًا.
- استخدم المساعد المحلي الاختياري للتنقل في مساحة العمل. يمكنك تكوين الذكاء الاصطناعي الخارجي بشكل منفصل.

[كتالوج الميزات الكاملة](../FEATURES.md) · [التنسيقات المدعومة](../TOOL_FORMATS.md)

## الأدوات وماذا يفعلون

هذه هي الأدوات المحددة التي يدمجها الجناح أو يمكن تشغيله. يختلف التوفر حسب سير العمل ونظام التشغيل. بعض الوحدات والبيانات المرجعية عبارة عن تنزيلات منفصلة.

| أداة | ماذا يفعل |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | يقرأ ويفهرس ويفحص ملفات التسلسل المحاذاة بتنسيقات SAM وBAM وCRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | يقوم بتصفية الملفات المتنوعة وتطبيعها ودمجها وفحصها بتنسيقات VCF وBCF. |
| [fastp](https://github.com/OpenGene/fastp) | يتحقق من جودة قراءة FASTQ ويمكنه قص القراءات أو تصفيتها. |
| [mosdepth](https://github.com/brentp/mosdepth) | يقيس تغطية القراءة من ملفات BAM وCRAM. |
| [MultiQC](https://seqera.io/multiqc/) | يجمع التقارير من أدوات مراقبة الجودة المتعددة في عرض واحد. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | يعمل مع بيانات النمط الجيني لمهام مثل تصفية المتغيرات والارتباط وتحليل المكونات الرئيسية. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | يستخدم بيانات النمط الجيني لاستنتاج المتغيرات الموجودة على نفس النسخة من الكروموسوم. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | يجد أجزاء الحمض النووي المطابقة الموروثة من سلف مشترك. ويستخدم بيانات النمط الجيني مع المتغيرات المخصصة لنسخ الكروموسوم. |
| [WhatsHap](https://github.com/whatshap/whatshap) | يستخدم قراءات التسلسل لتعيين المتغيرات لنسخ الكروموسوم. |
| [Truvari](https://github.com/ACEnglish/truvari) | يقارن المتغيرات الهيكلية في ملفات VCF. |
| [IGV](https://igv.org/doc/desktop/) | يعرض القراءات المتوافقة والمتغيرات ومسارات الجينوم الأخرى في مواقع محددة. |
| [JBrowse](https://jbrowse.org/jb2/) | يتيح لك تصفح التسلسلات المرجعية والمسارات المرتبطة بشكل تفاعلي. |
| [GenomeSpy](https://genomespy.app/) | يعرض المخططات الجينومية التفاعلية مع تسريع رسومات المتصفح. |
| [Gramps](https://www.gramps-project.org/) | ينظم سجلات الأنساب وأشجار العائلة وبيانات GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | يعلق على المتغيرات باستخدام المصادر والتعليقات التوضيحية القابلة للتحديد. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | يتنبأ بكيفية تأثير المتغيرات على الجينات والنصوص والبروتينات. |
| [PharmCAT](https://pharmcat.org/) | إنتاج تقارير بحثية عن علم الوراثة الدوائي من مدخلات النمط الجيني المدعومة. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | يقوم بتشغيل نموذج اللغة المحلية الاختياري على أوقات تشغيل وحدة المعالجة المركزية (CPU) ووحدة معالجة الرسومات (GPU) المتوافقة. |

[إصدارات الأداة والمتطلبات الأساسية](../VERSIONS.md)

## ابدأ

اختر الحزمة التي تتوافق مع نظام التشغيل والمعالج الخاص بك. تسرد صفحة الإصدار تنزيلات x64 وARM64 لـ Windows وLinux وmacOS. بعض البنيات هي معاينات.

1. في Windows، قم باستخراج الأرشيف وتشغيل المشغل. أكمل الإعداد الأساسي عند المطالبة بذلك.
2. في Linux، ابدأ تشغيل قاذفة الغلاف المضمنة مع تثبيت Python وGTK وWebKitGTK.
3. في macOS، احتفظ بالتطبيق بجانب ملفات مساحة العمل المستخرجة. تتطلب المعاينة الإصدار macOS 13 أو إصدار أحدث وPython 3.12 أو إصدار أحدث.
4. ابدأ بالعينات التركيبية المضمنة لتجربة سير العمل دون استخدام الملفات الشخصية.

[تحميل](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [دليل التثبيت](../GETTING_STARTED.md)

## سطر الأوامر والأتمتة

استخدم نفس سجل الأوامر من خلال واجهة سطح المكتب، CLI، وJSON-RPC، وMCP. تعمل الخدمة مقطوعة الرأس على الجهاز المحلي. يمكنك سرد الأوامر وقراءة مخططاتها دون فتح نافذة سطح المكتب.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

يمكن أن يساعدك المساعد الاختياري في التنقل بين النتائج. إجاباتها لا تحل محل البيانات المصدر أو التحليل الذي تم التحقق منه.

> برامج البحوث. تعتمد النتائج على المدخلات والطريقة والمراجع. لا يوفر DNA Workbench Suite تشخيصًا سريريًا.

## المشروع والدعم

تتم صيانته بواسطة Oktay Du / OD بمساعدة الذكاء الاصطناعي.

[الخصوصية](../PRIVACY.md) · [الأمن](../../SECURITY.md) · [رخصة المشروع](../../LICENSE) · [الإبلاغ عن مشكلة](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

دعم المشروع · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## ترجمات

يتضمن التطبيق 36 لغة واجهة غير متصلة بالإنترنت. اختر ترجمة لصفحة المشروع هذه أدناه.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)

</div>
