# DNA Workbench Suite

**एक ही स्थानीय कार्यक्षेत्र में डीएनए फ़ाइलें, पारिवारिक रिकॉर्ड और अनुसंधान कार्यप्रवाह।**

[डाउनलोड करें](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [वेबसाइट](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=hi) · [इंस्टालेशन गाइड](../GETTING_STARTED.md) · [अनुवाद](#translations)

अपने स्रोतों को व्यक्ति और प्रदाता के आधार पर व्यवस्थित करें, संगत फ़ाइलों की तुलना करें, और प्रत्येक विश्लेषण के पीछे इनपुट और परिणाम रखें।

![लाइट और डार्क मोड, भाषा पिकर और सिंथेटिक प्रोफ़ाइल फ़ाइलों के साथ ऐप टूर](../images/workspace-demo.gif)

[ऐप टूर देखें](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=hi#tour) · [स्क्रीनशॉट गैलरी](../GALLERY.md)

## आप क्या कर सकते हैं

- डीएनए फ़ाइलें, फ़ोल्डर और समर्थित अभिलेखागार आयात करें। कुछ भी कॉपी करने या स्थानांतरित करने से पहले प्रदाता, प्रारूप और संदर्भ निर्माण की समीक्षा करें।
- प्रोफ़ाइल के आधार पर डेटासेट, दस्तावेज़ और परिणाम समूहित करें। प्रत्येक फ़ाइल का मूल रिकॉर्ड करें. प्रत्यक्ष माप को अनुमानित मानों से अलग रखें और ध्यान दें कि क्रोमोसोम प्रतियों को कब वेरिएंट निर्दिष्ट किया गया है।
- नमूना गुणवत्ता की जाँच करें और स्रोतों की तुलना करें। वर्कफ़्लो के लिए एक संस्करण BestDataset बनाएं जो समान संदर्भ बिल्ड का उपयोग कर सके।
- जीनोम दर्शकों के साथ वेरिएंट और अनुक्रम फ़ाइलों का अन्वेषण करें। डीएनए प्रोफाइल की तुलना करें और शोध नोट्स को पारिवारिक रिकॉर्ड और GEDCOM फ़ाइलों से जोड़ें।
- उनके इनपुट और लॉग के साथ परिणाम सहेजें। रिपोर्ट निर्यात करें और बाद में उपयोग के लिए प्रोफ़ाइल का बैकअप लें।
- कार्यस्थल पर नेविगेट करने के लिए वैकल्पिक स्थानीय सहायक का उपयोग करें। आप बाह्य AI को अलग से कॉन्फ़िगर कर सकते हैं.

[पूर्ण सुविधा सूची](../FEATURES.md) · [समर्थित प्रारूप](../TOOL_FORMATS.md)

## उपकरण और वे क्या करते हैं

ये चयनित उपकरण हैं जिन्हें सुइट एकीकृत करता है या लॉन्च कर सकता है। उपलब्धता वर्कफ़्लो और ऑपरेटिंग सिस्टम के अनुसार भिन्न होती है। कुछ मॉड्यूल और संदर्भ डेटा अलग-अलग डाउनलोड हैं।

| औज़ार | यह क्या करता है |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | SAM, BAM और CRAM स्वरूपों में संरेखित अनुक्रमण फ़ाइलों को पढ़ता है, अनुक्रमित करता है और उनका निरीक्षण करता है। |
| [BCFtools](https://samtools.github.io/bcftools/) | VCF और BCF स्वरूपों में भिन्न फ़ाइलों को फ़िल्टर, सामान्यीकृत, संयोजित और निरीक्षण करता है। |
| [fastp](https://github.com/OpenGene/fastp) | FASTQ पढ़ने की गुणवत्ता की जाँच करता है और पढ़े गए को ट्रिम या फ़िल्टर कर सकता है। |
| [mosdepth](https://github.com/brentp/mosdepth) | माप BAM और CRAM फ़ाइलों से कवरेज पढ़ते हैं। |
| [MultiQC](https://seqera.io/multiqc/) | अनेक गुणवत्ता-नियंत्रण उपकरणों की रिपोर्टों को एक दृश्य में संयोजित करता है। |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | वेरिएंट फ़िल्टरिंग, संबंधितता और प्रमुख घटक विश्लेषण जैसे कार्यों के लिए जीनोटाइप डेटा के साथ काम करता है। |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | यह अनुमान लगाने के लिए जीनोटाइप डेटा का उपयोग करता है कि कौन से वेरिएंट क्रोमोसोम की एक ही प्रतिलिपि पर स्थित हैं। |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | एक सामान्य पूर्वज से विरासत में मिले डीएनए खंडों का मिलान ढूँढता है। यह गुणसूत्र प्रतियों को निर्दिष्ट वेरिएंट के साथ जीनोटाइप डेटा का उपयोग करता है। |
| [WhatsHap](https://github.com/whatshap/whatshap) | गुणसूत्र प्रतियों में वेरिएंट निर्दिष्ट करने के लिए अनुक्रमण रीड्स का उपयोग करता है। |
| [Truvari](https://github.com/ACEnglish/truvari) | VCF फ़ाइलों में संरचनात्मक वेरिएंट की तुलना करता है। |
| [IGV](https://igv.org/doc/desktop/) | विशिष्ट स्थानों पर संरेखित रीड्स, वेरिएंट और अन्य जीनोम ट्रैक प्रदर्शित करता है। |
| [JBrowse](https://jbrowse.org/jb2/) | आपको संदर्भ अनुक्रम और लिंक किए गए ट्रैक को इंटरैक्टिव रूप से ब्राउज़ करने देता है। |
| [GenomeSpy](https://genomespy.app/) | ब्राउज़र ग्राफ़िक्स त्वरण के साथ इंटरैक्टिव जीनोमिक चार्ट प्रस्तुत करता है। |
| [Gramps](https://www.gramps-project.org/) | वंशावली रिकॉर्ड, पारिवारिक पेड़ और GEDCOM डेटा व्यवस्थित करता है। |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | चयन योग्य स्रोतों और एनोटेटर्स का उपयोग करके वेरिएंट को एनोटेट करता है। |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | भविष्यवाणी करता है कि वेरिएंट जीन, प्रतिलेख और प्रोटीन को कैसे प्रभावित कर सकते हैं। |
| [PharmCAT](https://pharmcat.org/) | समर्थित जीनोटाइप इनपुट से फार्माकोजेनेटिक्स अनुसंधान रिपोर्ट तैयार करता है। |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | संगत सीपीयू और जीपीयू रनटाइम पर वैकल्पिक स्थानीय भाषा मॉडल चलाता है। |

[टूल संस्करण और पूर्वापेक्षाएँ](../VERSIONS.md)

## आरंभ करें

वह पैकेज चुनें जो आपके ऑपरेटिंग सिस्टम और प्रोसेसर से मेल खाता हो। रिलीज़ पेज में Windows, Linux और macOS के लिए x64 और ARM64 डाउनलोड सूचीबद्ध हैं। कुछ बिल्ड पूर्वावलोकन हैं.

1. Windows पर, संग्रह निकालें और लॉन्चर चलाएँ। संकेत मिलने पर कोर सेटअप पूरा करें।
2. Linux पर, शामिल शेल लॉन्चर को Python, GTK और WebKitGTK स्थापित करके प्रारंभ करें।
3. macOS पर, ऐप को निकाली गई वर्कस्पेस फ़ाइलों के पास रखें। पूर्वावलोकन के लिए macOS 13 या बाद का संस्करण और Python 3.12 या बाद का संस्करण आवश्यक है।
4. व्यक्तिगत फ़ाइलों का उपयोग किए बिना वर्कफ़्लो आज़माने के लिए शामिल सिंथेटिक नमूनों से शुरुआत करें।

[डाउनलोड करें](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [इंस्टालेशन गाइड](../GETTING_STARTED.md)

## कमांड लाइन और स्वचालन

डेस्कटॉप इंटरफ़ेस, CLI, JSON-RPC और MCP के माध्यम से समान कमांड रजिस्ट्री का उपयोग करें। हेडलेस सेवा स्थानीय मशीन पर चलती है। आप डेस्कटॉप विंडो खोले बिना कमांडों को सूचीबद्ध कर सकते हैं और उनके स्कीमा पढ़ सकते हैं।

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

वैकल्पिक सहायक आपको परिणामों को नेविगेट करने में मदद कर सकता है। इसके उत्तर स्रोत डेटा या सत्यापित विश्लेषण को प्रतिस्थापित नहीं करते हैं।

> अनुसंधान सॉफ्टवेयर. परिणाम इनपुट, विधि और संदर्भ पर निर्भर करते हैं। DNA Workbench Suite नैदानिक ​​निदान प्रदान नहीं करता है।

## परियोजना और समर्थन

AI सहायता से Oktay Du / OD द्वारा रखरखाव किया गया।

[गोपनीयता](../PRIVACY.md) · [सुरक्षा](../../SECURITY.md) · [प्रोजेक्ट लाइसेंस](../../LICENSE) · [किसी समस्या की रिपोर्ट करें](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

परियोजना का समर्थन करें · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## अनुवाद

ऐप में 36 ऑफ़लाइन इंटरफ़ेस भाषाएँ शामिल हैं। नीचे इस प्रोजेक्ट पृष्ठ का अनुवाद चुनें।

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
