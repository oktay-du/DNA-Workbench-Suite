# DNA Workbench Suite

**የዲኤንኤ ፋይሎች፣ የቤተሰብ መዝገቦች እና የምርምር የስራ ፍሰቶች በአንድ የአካባቢ የስራ ቦታ።**

[አውርድ](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [ድር ጣቢያ](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=am) · [የመጫኛ መመሪያ](../GETTING_STARTED.md) · [ትርጉሞች](#translations)

ምንጮችዎን በሰው እና በአቅራቢ ያደራጁ፣ ተኳዃኝ የሆኑ ፋይሎችን ያወዳድሩ፣ እና ግብዓቶቹን እና ውጤቶቹን ከእያንዳንዱ ትንተና ጀርባ ያስቀምጡ።

![የመተግበሪያ ጉብኝት በብርሃን እና ጨለማ ሁነታ፣ ቋንቋ መራጭ እና ሰው ሠራሽ መገለጫ ፋይሎች](../images/workspace-demo.gif)

[የመተግበሪያውን ጉብኝት ይመልከቱ](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=am#tour) · [የቅጽበታዊ ገጽ እይታ ማዕከለ-ስዕላት](../GALLERY.md)

## ምን ማድረግ ትችላለህ

- የዲኤንኤ ፋይሎችን፣ አቃፊዎችን እና የሚደገፉ ማህደሮችን አስመጣ። ማንኛውንም ነገር ከመቅዳትዎ ወይም ከማንቀሳቀስዎ በፊት አቅራቢውን፣ ቅርጸትን እና የማጣቀሻ ግንባታን ይገምግሙ።
- የቡድን የውሂብ ስብስቦች, ሰነዶች እና ውጤቶች በመገለጫ. የእያንዳንዱን ፋይል አመጣጥ ይመዝግቡ። ቀጥተኛ ልኬቶችን ከተገመቱ እሴቶች ይለዩ እና ተለዋጮች ለክሮሞሶም ቅጂዎች ሲመደቡ ያስተውሉ።
- የናሙናውን ጥራት ይፈትሹ እና ምንጮችን ያወዳድሩ። ተመሳሳዩን የማጣቀሻ ግንባታ ሊጠቀሙ ለሚችሉ የስራ ፍሰቶች የተሻሻለ BestDataset ይገንቡ።
- በጂኖም ተመልካቾች ተለዋጮችን እና ተከታታይ ፋይሎችን ያስሱ። የዲኤንኤ መገለጫዎችን ያወዳድሩ እና የምርምር ማስታወሻዎችን ከቤተሰብ መዛግብት እና GEDCOM ፋይሎች ጋር ያገናኙ።
- ውጤቶችን በግብዓታቸው እና በምዝግብ ማስታወሻዎቻቸው ያስቀምጡ። ሪፖርቶችን ወደ ውጪ ላክ እና መገለጫዎችን ለበኋላ ጥቅም ላይ ማዋል.
- የስራ ቦታውን ለማሰስ የአማራጭ አካባቢያዊ ረዳትን ይጠቀሙ። ውጫዊ AIን ለየብቻ ማዋቀር ይችላሉ።

[ሙሉ የባህሪ ካታሎግ](../FEATURES.md) · [የሚደገፉ ቅርጸቶች](../TOOL_FORMATS.md)

## መሳሪያዎች እና ምን እንደሚሰሩ

እነዚህ ጥቅሎቹ የሚያዋህዳቸው ወይም የሚጀምሩት የተመረጡ መሳሪያዎች ናቸው። ተገኝነት እንደ የስራ ፍሰት እና ስርዓተ ክወና ይለያያል። አንዳንድ ሞጁሎች እና የማጣቀሻ መረጃዎች የተለዩ ውርዶች ናቸው።

| መሳሪያ | ምን ያደርጋል |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | የተጣጣሙ ተከታታይ ፋይሎችን በSAM፣ BAM እና CRAM ቅርጸቶች ያነባል፣ ያመላክታል እና ይመረምራል። |
| [BCFtools](https://samtools.github.io/bcftools/) | የተለያዩ ፋይሎችን በVCF እና BCF ቅርጸቶች ያጣራል፣ መደበኛ ያደርጋል፣ ያጣምራል እና ይመረምራል። |
| [fastp](https://github.com/OpenGene/fastp) | የFASTQ የማንበብ ጥራት ይፈትሻል እና ንባቦችን መከርከም ወይም ማጣራት ይችላል። |
| [mosdepth](https://github.com/brentp/mosdepth) | ከBAM እና CRAM ፋይሎች ሽፋን ማንበብን ይለካል። |
| [MultiQC](https://seqera.io/multiqc/) | ከበርካታ የጥራት መቆጣጠሪያ መሳሪያዎች ሪፖርቶችን ወደ አንድ እይታ ያጣምራል። |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | እንደ ተለዋጭ ማጣሪያ፣ ተዛማጅነት እና ዋና አካል ትንተና ላሉ ተግባራት ከጂኖታይፕ ውሂብ ጋር ይሰራል። |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | የትኞቹ ተለዋጮች በተመሳሳይ የክሮሞሶም ቅጂ ላይ እንደሚገኙ ለማወቅ የጂኖታይፕ መረጃን ይጠቀማል። |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | ከአንድ የጋራ ቅድመ አያት የተወረሱ ተዛማጅ የዲኤንኤ ክፍሎችን ያገኛል። ለክሮሞዞም ቅጂዎች የተመደቡትን የጂኖታይፕ መረጃዎችን ይጠቀማል። |
| [WhatsHap](https://github.com/whatshap/whatshap) | ተለዋጮችን ወደ ክሮሞዞም ቅጂዎች ለመመደብ ተከታታይ ንባቦችን ይጠቀማል። |
| [Truvari](https://github.com/ACEnglish/truvari) | በVCF ፋይሎች ውስጥ ያሉ መዋቅራዊ ልዩነቶችን ያወዳድራል። |
| [IGV](https://igv.org/doc/desktop/) | የተጣጣሙ ንባቦችን፣ ተለዋጮችን እና ሌሎች የጂኖም ትራኮችን በተወሰኑ ቦታዎች ላይ ያሳያል። |
| [JBrowse](https://jbrowse.org/jb2/) | የማጣቀሻ ቅደም ተከተሎችን እና የተገናኙ ትራኮችን በይነተገናኝ እንዲያስሱ ያስችልዎታል። |
| [GenomeSpy](https://genomespy.app/) | ከአሳሽ ግራፊክስ ማጣደፍ ጋር መስተጋብራዊ ጂኖሚክ ገበታዎችን ያቀርባል። |
| [Gramps](https://www.gramps-project.org/) | የዘር ሐረግ መዝገቦችን፣ የቤተሰብ ዛፎችን እና የGEDCOM መረጃን ያደራጃል። |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | ሊመረጡ የሚችሉ ምንጮችን እና ገላጭዎችን በመጠቀም ተለዋጮችን ያብራራል። |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | ተለዋጮች ጂኖች፣ ግልባጮች እና ፕሮቲኖች እንዴት እንደሚነኩ ይተነብያል። |
| [PharmCAT](https://pharmcat.org/) | ከሚደገፉ የጂኖታይፕ ግብዓቶች የፋርማሲዮኔቲክስ ምርምር ሪፖርቶችን ያዘጋጃል። |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | የአማራጭ የአካባቢ ቋንቋ ሞዴል በተኳኋኝ ሲፒዩ እና ጂፒዩ የሩጫ ጊዜዎች ላይ ይሰራል። |

[የመሳሪያ ስሪቶች እና ቅድመ ሁኔታዎች](../VERSIONS.md)

## ጀምር

ከእርስዎ ስርዓተ ክወና እና ፕሮሰሰር ጋር የሚዛመደውን ጥቅል ይምረጡ። የመልቀቂያ ገጹ x64 እና ARM64 ለWindows፣ Linux እና macOS ማውረዶችን ይዘረዝራል። አንዳንድ ግንባታዎች ቅድመ እይታዎች ናቸው።

1. በWindows ላይ ማህደሩን ያውጡ እና አስጀማሪውን ያሂዱ። ሲጠየቁ የኮር ማዋቀርን ያጠናቅቁ።
2. በLinux፣ የተካተተውን የሼል አስጀማሪ በPython፣ GTK እና WebKitGTK በተጫኑ ይጀምሩ።
3. በmacOS ላይ መተግበሪያውን ከተወጡት የስራ ቦታ ፋይሎች ጎን ያቆዩት። ቅድመ እይታው macOS 13 ወይም ከዚያ በላይ እና Python 3.12 ወይም ከዚያ በላይ ያስፈልገዋል።
4. የግል ፋይሎችን ሳይጠቀሙ የስራ ሂደቶችን ለመሞከር በተካተቱት ሰው ሰራሽ ናሙናዎች ይጀምሩ።

[አውርድ](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [የመጫኛ መመሪያ](../GETTING_STARTED.md)

## የትእዛዝ መስመር እና አውቶማቲክ

ተመሳሳዩን የትእዛዝ መዝገብ በዴስክቶፕ በይነገጽ፣ CLI፣ JSON-RPC እና MCP ይጠቀሙ። ጭንቅላት የሌለው አገልግሎት በአካባቢው ማሽን ላይ ይሰራል. የዴስክቶፕ መስኮት ሳይከፍቱ ትዕዛዞችን መዘርዘር እና መርሃግብሮቻቸውን ማንበብ ይችላሉ።

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

የአማራጭ ረዳት ውጤቱን ለማሰስ ሊረዳዎት ይችላል። የእሱ መልሶች የምንጩን መረጃ ወይም የተረጋገጠ ትንታኔን አይተኩም.

> የምርምር ሶፍትዌር. ውጤቶቹ በመግቢያው, ዘዴው እና በማጣቀሻዎች ላይ ይወሰናሉ. DNA Workbench Suite ክሊኒካዊ ምርመራ አያቀርብም.

## ፕሮጀክት እና ድጋፍ

በOktay Du / OD በ AI እገዛ ተጠብቆ የቆየ።

[ግላዊነት](../PRIVACY.md) · [ደህንነት](../../SECURITY.md) · [የፕሮጀክት ፈቃድ](../../LICENSE) · [ችግር ሪፖርት አድርግ](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

ፕሮጀክቱን ይደግፉ · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## ትርጉሞች

መተግበሪያው 36 ከመስመር ውጭ የበይነገጽ ቋንቋዎችን ያካትታል። ከዚህ በታች ያለውን የዚህ ፕሮጀክት ገጽ ትርጉም ይምረጡ።

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
