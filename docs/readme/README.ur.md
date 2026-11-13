<div dir="rtl" lang="ur">

# DNA Workbench Suite

**ایک مقامی ورک اسپیس میں ڈی این اے فائلیں، فیملی ریکارڈ اور ریسرچ ورک فلو۔**

[ڈاؤن لوڈ کریں۔](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [ویب سائٹ](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ur) · [انسٹالیشن گائیڈ](../GETTING_STARTED.md) · [ترجمے](#translations)

اپنے ذرائع کو شخص اور فراہم کنندہ کے لحاظ سے ترتیب دیں، مطابقت پذیر فائلوں کا موازنہ کریں، اور ہر تجزیہ کے پیچھے ان پٹ اور نتائج کو رکھیں۔

![لائٹ اور ڈارک موڈ کے ساتھ ایپ ٹور، لینگویج چننے والا اور مصنوعی پروفائل فائلز](../images/workspace-demo.gif)

[ایپ ٹور دیکھیں](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ur#tour) · [اسکرین شاٹ گیلری](../GALLERY.md)

## آپ کیا کر سکتے ہیں

- ڈی این اے فائلیں، فولڈرز اور معاون آرکائیوز درآمد کریں۔ کسی بھی چیز کو نقل کرنے یا منتقل کرنے سے پہلے فراہم کنندہ، فارمیٹ اور ریفرنس کی تعمیر کا جائزہ لیں۔
- ڈیٹا سیٹس، دستاویزات اور نتائج کو پروفائل کے لحاظ سے گروپ کریں۔ ہر فائل کی اصلیت کو ریکارڈ کریں۔ براہ راست پیمائش کو قیاس شدہ قدروں سے الگ رکھیں اور نوٹ کریں کہ کب متغیرات کو کروموسوم کاپیوں کو تفویض کیا گیا ہے۔
- نمونے کے معیار کو چیک کریں اور ذرائع کا موازنہ کریں۔ ورک فلوز کے لیے ایک ورژن والا BestDataset بنائیں جو ایک ہی ریفرنس بلڈ کو استعمال کر سکے۔
- جینوم ناظرین کے ساتھ مختلف حالتوں اور ترتیب والی فائلوں کو دریافت کریں۔ ڈی این اے پروفائلز کا موازنہ کریں اور تحقیقی نوٹس کو فیملی ریکارڈز اور GEDCOM فائلوں سے جوڑیں۔
- نتائج کو ان کے ان پٹ اور لاگز کے ساتھ محفوظ کریں۔ بعد میں استعمال کے لیے رپورٹیں اور بیک اپ پروفائلز برآمد کریں۔
- ورک اسپیس کو نیویگیٹ کرنے کے لیے اختیاری مقامی اسسٹنٹ کا استعمال کریں۔ آپ بیرونی AI کو الگ سے ترتیب دے سکتے ہیں۔

[مکمل فیچر کیٹلاگ](../FEATURES.md) · [تائید شدہ فارمیٹس](../TOOL_FORMATS.md)

## اوزار اور وہ کیا کرتے ہیں۔

یہ منتخب کردہ ٹولز ہیں جو سویٹ کو ضم کرتا ہے یا لانچ کر سکتا ہے۔ ورک فلو اور آپریٹنگ سسٹم کے لحاظ سے دستیابی مختلف ہوتی ہے۔ کچھ ماڈیولز اور حوالہ ڈیٹا علیحدہ ڈاؤن لوڈز ہیں۔

| ٹول | یہ کیا کرتا ہے |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | SAM، BAM اور CRAM فارمیٹس میں منسلک ترتیب والی فائلوں کو پڑھتا، انڈیکس کرتا اور ان کا معائنہ کرتا ہے۔ |
| [BCFtools](https://samtools.github.io/bcftools/) | VCF اور BCF فارمیٹس میں مختلف فائلوں کو فلٹر، نارمل، یکجا اور معائنہ کرتا ہے۔ |
| [fastp](https://github.com/OpenGene/fastp) | FASTQ پڑھنے کے معیار کو چیک کرتا ہے اور ریڈز کو ٹرم یا فلٹر کر سکتا ہے۔ |
| [mosdepth](https://github.com/brentp/mosdepth) | BAM اور CRAM فائلوں سے کوریج پڑھنے کے اقدامات۔ |
| [MultiQC](https://seqera.io/multiqc/) | متعدد کوالٹی کنٹرول ٹولز کی رپورٹس کو ایک منظر میں یکجا کرتا ہے۔ |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | کاموں کے لیے جین ٹائپ ڈیٹا کے ساتھ کام کرتا ہے جیسے کہ متغیر فلٹرنگ، تعلق اور پرنسپل جزو تجزیہ۔ |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | یہ اندازہ لگانے کے لیے جین ٹائپ ڈیٹا کا استعمال کرتا ہے کہ کروموسوم کی ایک ہی کاپی پر کون سی قسمیں موجود ہیں۔ |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | مشترکہ آباؤ اجداد سے وراثت میں ملنے والے ڈی این اے سیگمنٹس کو تلاش کرتا ہے۔ یہ کروموسوم کاپیوں کو تفویض کردہ مختلف حالتوں کے ساتھ جین ٹائپ ڈیٹا کا استعمال کرتا ہے۔ |
| [WhatsHap](https://github.com/whatshap/whatshap) | کروموسوم کاپیوں کو متغیرات تفویض کرنے کے لیے ترتیب وار پڑھنے کا استعمال کرتا ہے۔ |
| [Truvari](https://github.com/ACEnglish/truvari) | VCF فائلوں میں ساختی تغیرات کا موازنہ کرتا ہے۔ |
| [IGV](https://igv.org/doc/desktop/) | مخصوص مقامات پر الائنڈ ریڈز، ویریئنٹس اور دیگر جینوم ٹریک دکھاتا ہے۔ |
| [JBrowse](https://jbrowse.org/jb2/) | آپ کو حوالہ کے سلسلے اور منسلک ٹریکس کو انٹرایکٹو طریقے سے براؤز کرنے دیتا ہے۔ |
| [GenomeSpy](https://genomespy.app/) | براؤزر گرافکس ایکسلریشن کے ساتھ انٹرایکٹو جینومک چارٹس پیش کرتا ہے۔ |
| [Gramps](https://www.gramps-project.org/) | نسب کے ریکارڈ، خاندانی درخت اور GEDCOM ڈیٹا کو منظم کرتا ہے۔ |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | قابل انتخاب ذرائع اور تشریح کاروں کا استعمال کرتے ہوئے متغیرات کی تشریح کرتا ہے۔ |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | پیشن گوئی کرتا ہے کہ مختلف قسمیں جینز، ٹرانسکرپٹس اور پروٹین کو کیسے متاثر کر سکتی ہیں۔ |
| [PharmCAT](https://pharmcat.org/) | معاون جینی ٹائپ ان پٹس سے فارماکوجنیٹکس ریسرچ رپورٹس تیار کرتا ہے۔ |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | ہم آہنگ CPU اور GPU رن ٹائمز پر اختیاری مقامی زبان کا ماڈل چلاتا ہے۔ |

[ٹول ورژن اور شرائط](../VERSIONS.md)

## شروع کرو

وہ پیکیج منتخب کریں جو آپ کے آپریٹنگ سسٹم اور پروسیسر سے مماثل ہو۔ ریلیز کا صفحہ Windows، Linux اور macOS کے لیے x64 اور ARM64 ڈاؤن لوڈز کی فہرست دیتا ہے۔ کچھ تعمیرات پیش نظارہ ہیں۔

1. Windows پر، آرکائیو کو نکالیں اور لانچر چلائیں۔ جب اشارہ کیا جائے تو کور سیٹ اپ مکمل کریں۔
2. Linux پر، Python، GTK اور WebKitGTK انسٹال کے ساتھ شامل شیل لانچر شروع کریں۔
3. macOS پر، ایپ کو نکالی گئی ورک اسپیس فائلوں کے پاس رکھیں۔ پیش نظارہ کے لیے macOS 13 یا بعد کا اور Python 3.12 یا اس کے بعد کا ہونا ضروری ہے۔
4. ذاتی فائلوں کا استعمال کیے بغیر ورک فلو کو آزمانے کے لیے شامل مصنوعی نمونوں سے شروع کریں۔

[ڈاؤن لوڈ کریں۔](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [انسٹالیشن گائیڈ](../GETTING_STARTED.md)

## کمانڈ لائن اور آٹومیشن

ڈیسک ٹاپ انٹرفیس، CLI، JSON-RPC اور MCP کے ذریعے ایک ہی کمانڈ رجسٹری کا استعمال کریں۔ ہیڈ لیس سروس مقامی مشین پر چلتی ہے۔ آپ ڈیسک ٹاپ ونڈو کھولے بغیر کمانڈز کی فہرست بنا سکتے ہیں اور ان کے اسکیموں کو پڑھ سکتے ہیں۔

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

اختیاری معاون آپ کو نتائج پر تشریف لانے میں مدد کر سکتا ہے۔ اس کے جوابات ماخذ ڈیٹا یا تصدیق شدہ تجزیہ کی جگہ نہیں لیتے ہیں۔

> ریسرچ سافٹ ویئر۔ نتائج کا انحصار ان پٹ، طریقہ اور حوالہ جات پر ہے۔ DNA Workbench Suite طبی تشخیص فراہم نہیں کرتا ہے۔

## پروجیکٹ اور سپورٹ

AI کی مدد کے ساتھ Oktay Du / OD کے ذریعہ برقرار رکھا گیا ہے۔

[رازداری](../PRIVACY.md) · [سیکورٹی](../../SECURITY.md) · [پروجیکٹ لائسنس](../../LICENSE) · [ایک مسئلہ کی اطلاع دیں۔](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

منصوبے کی حمایت کریں۔ · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## ترجمے

ایپ میں 36 آف لائن انٹرفیس زبانیں شامل ہیں۔ ذیل میں اس منصوبے کے صفحہ کا ترجمہ منتخب کریں۔

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)

</div>
