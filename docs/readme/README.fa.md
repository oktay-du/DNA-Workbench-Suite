<div dir="rtl" lang="fa">

# DNA Workbench Suite

**فایل‌های DNA، سوابق خانوادگی و گردش کار تحقیقاتی در یک فضای کاری محلی.**

[دانلود کنید](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [وب سایت](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fa) · [راهنمای نصب](../GETTING_STARTED.md) · [ترجمه ها](#translations)

منابع خود را بر اساس شخص و ارائه دهنده سازماندهی کنید، فایل های سازگار را مقایسه کنید، و ورودی ها و نتایج را پشت هر تجزیه و تحلیل نگه دارید.

![تور برنامه با حالت روشن و تاریک، انتخابگر زبان و فایل‌های نمایه مصنوعی](../images/workspace-demo.gif)

[تور برنامه را تماشا کنید](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=fa#tour) · [گالری اسکرین شات](../GALLERY.md)

## کاری که می توانید انجام دهید

- فایل های DNA، پوشه ها و بایگانی های پشتیبانی شده را وارد کنید. قبل از اینکه هر چیزی را کپی یا جابجا کنید، ارائه‌دهنده، قالب و ساختار مرجع را بررسی کنید.
- مجموعه داده ها، اسناد و نتایج را بر اساس نمایه گروه بندی کنید. منشا هر فایل را ثبت کنید. اندازه‌گیری‌های مستقیم را از مقادیر استنباط شده جدا نگه دارید و زمانی را که واریته‌ها به نسخه‌های کروموزوم اختصاص داده شده‌اند، یادداشت کنید.
- کیفیت نمونه را بررسی کنید و منابع را مقایسه کنید. یک BestDataset نسخه‌بندی‌شده برای گردش‌های کاری بسازید که می‌تواند از همان ساختار مرجع استفاده کند.
- انواع و فایل های توالی را با نمایشگرهای ژنوم کاوش کنید. پروفایل های DNA را مقایسه کنید و یادداشت های تحقیقاتی را با سوابق خانوادگی و فایل های GEDCOM متصل کنید.
- نتایج را با ورودی ها و گزارش های آنها ذخیره کنید. گزارش ها را صادر کنید و از پروفایل ها برای استفاده بعدی نسخه پشتیبان تهیه کنید.
- از دستیار محلی اختیاری برای پیمایش در فضای کاری استفاده کنید. می توانید هوش مصنوعی خارجی را جداگانه پیکربندی کنید.

[کاتالوگ امکانات کامل](../FEATURES.md) · [فرمت های پشتیبانی شده](../TOOL_FORMATS.md)

## ابزارها و کاری که انجام می دهند

اینها ابزارهای انتخابی هستند که مجموعه ادغام می کند یا می تواند راه اندازی کند. در دسترس بودن بسته به گردش کار و سیستم عامل متفاوت است. برخی از ماژول ها و داده های مرجع دانلود جداگانه هستند.

| ابزار | کاری که انجام می دهد |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | فایل‌های ترتیب‌بندی را در قالب‌های SAM، BAM و CRAM می‌خواند، فهرست‌بندی و بازرسی می‌کند. |
| [BCFtools](https://samtools.github.io/bcftools/) | فایل‌های مختلف را در قالب‌های VCF و BCF فیلتر، عادی، ترکیب و بررسی می‌کند. |
| [fastp](https://github.com/OpenGene/fastp) | کیفیت خواندن FASTQ را بررسی می‌کند و می‌تواند خواندن را اصلاح یا فیلتر کند. |
| [mosdepth](https://github.com/brentp/mosdepth) | پوشش خواندن را از فایل های BAM و CRAM اندازه گیری می کند. |
| [MultiQC](https://seqera.io/multiqc/) | گزارش‌ها را از چندین ابزار کنترل کیفیت در یک نمای ترکیب می‌کند. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | با داده‌های ژنوتیپ برای کارهایی مانند فیلتر کردن انواع، ارتباط و تجزیه و تحلیل اجزای اصلی کار می‌کند. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | از داده‌های ژنوتیپ برای استنباط اینکه کدام گونه‌ها روی یک کپی از یک کروموزوم قرار دارند، استفاده می‌کند. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | بخش های DNA منطبق را که از یک اجداد مشترک به ارث رسیده است را پیدا می کند. از داده های ژنوتیپ با انواعی که به نسخه های کروموزوم اختصاص داده شده اند استفاده می کند. |
| [WhatsHap](https://github.com/whatshap/whatshap) | از خواندن توالی برای تخصیص انواع به کپی های کروموزوم استفاده می کند. |
| [Truvari](https://github.com/ACEnglish/truvari) | انواع ساختاری را در فایل های VCF مقایسه می کند. |
| [IGV](https://igv.org/doc/desktop/) | خواندن تراز، انواع و دیگر آهنگ های ژنوم را در مکان های خاص نمایش می دهد. |
| [JBrowse](https://jbrowse.org/jb2/) | به شما امکان می دهد دنباله های مرجع و آهنگ های پیوند داده شده را به صورت تعاملی مرور کنید. |
| [GenomeSpy](https://genomespy.app/) | نمودارهای ژنومی تعاملی را با شتاب گرافیک مرورگر ارائه می دهد. |
| [Gramps](https://www.gramps-project.org/) | سوابق شجره نامه، شجره نامه ها و داده های GEDCOM را سازماندهی می کند. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | انواع را با استفاده از منابع و حاشیه نویس های قابل انتخاب حاشیه نویسی می کند. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | پیش بینی می کند که چگونه انواع ممکن است بر ژن ها، رونوشت ها و پروتئین ها تأثیر بگذارند. |
| [PharmCAT](https://pharmcat.org/) | گزارش های تحقیقات فارماکوژنتیک را از ورودی های ژنوتیپ پشتیبانی شده تولید می کند. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | مدل زبان محلی اختیاری را روی زمان‌های اجرا CPU و GPU سازگار اجرا می‌کند. |

[نسخه های ابزار و پیش نیازها](../VERSIONS.md)

## شروع کنید

بسته ای را انتخاب کنید که با سیستم عامل و پردازنده شما مطابقت دارد. صفحه انتشار دانلودهای x64 و ARM64 را برای Windows، Linux و macOS فهرست می‌کند. برخی از ساخت ها پیش نمایش هستند.

1. در Windows، آرشیو را استخراج کرده و لانچر را اجرا کنید. وقتی از شما خواسته شد، تنظیمات هسته را کامل کنید.
2. در Linux، لانچر پوسته همراه را با نصب Python، GTK و WebKitGTK راه اندازی کنید.
3. در macOS، برنامه را در کنار فایل های فضای کاری استخراج شده نگه دارید. پیش نمایش به macOS 13 یا جدیدتر و Python 3.12 یا بالاتر نیاز دارد.
4. با نمونه‌های مصنوعی موجود شروع کنید تا بدون استفاده از فایل‌های شخصی، جریان‌های کاری را امتحان کنید.

[دانلود کنید](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [راهنمای نصب](../GETTING_STARTED.md)

## خط فرمان و اتوماسیون

از همان رجیستری فرمان از طریق رابط دسکتاپ، CLI، JSON-RPC و MCP استفاده کنید. سرویس هدلس روی ماشین محلی اجرا می شود. می توانید دستورات را فهرست کنید و طرحواره های آنها را بدون باز کردن پنجره دسکتاپ بخوانید.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

دستیار اختیاری می تواند به شما در پیمایش نتایج کمک کند. پاسخ های آن جایگزین داده های منبع یا تجزیه و تحلیل تایید شده نمی شود.

> نرم افزار تحقیق. نتایج به ورودی، روش و مراجع بستگی دارد. DNA Workbench Suite تشخیص بالینی ارائه نمی دهد.

## پروژه و پشتیبانی

توسط Oktay Du / OD با کمک هوش مصنوعی نگهداری می شود.

[حریم خصوصی](../PRIVACY.md) · [امنیت](../../SECURITY.md) · [مجوز پروژه](../../LICENSE) · [یک مشکل را گزارش کنید](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

از پروژه حمایت کنید · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## ترجمه ها

این برنامه شامل 36 زبان رابط آفلاین است. ترجمه این صفحه پروژه را در زیر انتخاب کنید.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)

</div>
