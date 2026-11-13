# DNA Workbench Suite

**ไฟล์ DNA บันทึกครอบครัว และขั้นตอนการวิจัยในพื้นที่ทำงานในพื้นที่แห่งเดียว**

[ดาวน์โหลด](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [เว็บไซต์](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=th) · [คู่มือการติดตั้ง](../GETTING_STARTED.md) · [การแปล](#translations)

จัดระเบียบแหล่งที่มาของคุณตามบุคคลและผู้ให้บริการ เปรียบเทียบไฟล์ที่เข้ากันได้ และเก็บอินพุตและผลลัพธ์ไว้เบื้องหลังการวิเคราะห์ทุกครั้ง

![ทัวร์ชมแอปพร้อมโหมดสว่างและมืด ตัวเลือกภาษา และไฟล์โปรไฟล์สังเคราะห์](../images/workspace-demo.gif)

[ดูทัวร์ชมแอป](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=th#tour) · [แกลเลอรี่ภาพหน้าจอ](../GALLERY.md)

## สิ่งที่คุณสามารถทำได้

- นำเข้าไฟล์ DNA โฟลเดอร์ และไฟล์เก็บถาวรที่รองรับ ตรวจสอบผู้ให้บริการ จัดรูปแบบ และบิลด์อ้างอิงก่อนที่คุณจะคัดลอกหรือย้ายสิ่งใดๆ
- จัดกลุ่มชุดข้อมูล เอกสาร และผลลัพธ์ตามโปรไฟล์ บันทึกที่มาของแต่ละไฟล์ แยกการวัดโดยตรงออกจากค่าที่อนุมาน และจดบันทึกเมื่อมีการกำหนดตัวแปรให้กับสำเนาโครโมโซม
- ตรวจสอบคุณภาพตัวอย่างและเปรียบเทียบแหล่งที่มา สร้าง BestDataset เวอร์ชันสำหรับเวิร์กโฟลว์ที่สามารถใช้บิลด์อ้างอิงเดียวกันได้
- สำรวจตัวแปรและไฟล์ลำดับด้วยโปรแกรมดูจีโนม เปรียบเทียบโปรไฟล์ DNA และเชื่อมต่อบันทึกการวิจัยกับบันทึกครอบครัวและไฟล์ GEDCOM
- บันทึกผลลัพธ์ด้วยอินพุตและบันทึก ส่งออกรายงานและสำรองข้อมูลโปรไฟล์เพื่อใช้ในภายหลัง
- ใช้ผู้ช่วยท้องถิ่นที่เป็นตัวเลือกเพื่อนำทางในพื้นที่ทำงาน คุณสามารถกำหนดค่า AI ภายนอกแยกกันได้

[แคตตาล็อกคุณสมบัติเต็มรูปแบบ](../FEATURES.md) · [รูปแบบที่รองรับ](../TOOL_FORMATS.md)

## เครื่องมือและสิ่งที่พวกเขาทำ

เครื่องมือเหล่านี้คือเครื่องมือที่เลือกซึ่งชุดโปรแกรมจะรวมหรือสามารถเปิดใช้งานได้ ความพร้อมใช้งานจะแตกต่างกันไปตามเวิร์กโฟลว์และระบบปฏิบัติการ โมดูลและข้อมูลอ้างอิงบางส่วนมีการดาวน์โหลดแยกกัน

| เครื่องมือ | มันทำอะไร |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | อ่าน จัดทำดัชนี และตรวจสอบไฟล์ลำดับที่สอดคล้องกันในรูปแบบ SAM, BAM และ CRAM |
| [BCFtools](https://samtools.github.io/bcftools/) | กรอง ปรับมาตรฐาน รวมและตรวจสอบไฟล์รูปแบบ VCF และ BCF |
| [fastp](https://github.com/OpenGene/fastp) | ตรวจสอบคุณภาพการอ่านของ FASTQ และสามารถตัดหรือกรองการอ่านได้ |
| [mosdepth](https://github.com/brentp/mosdepth) | วัดความครอบคลุมการอ่านจากไฟล์ BAM และ CRAM |
| [MultiQC](https://seqera.io/multiqc/) | รวมรายงานจากเครื่องมือควบคุมคุณภาพหลายรายการไว้ในมุมมองเดียว |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | ทำงานร่วมกับข้อมูลจีโนไทป์สำหรับงานต่างๆ เช่น การกรองตัวแปร ความเกี่ยวข้อง และการวิเคราะห์องค์ประกอบหลัก |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | ใช้ข้อมูลจีโนไทป์เพื่ออนุมานว่าตัวแปรใดอยู่บนสำเนาโครโมโซมเดียวกัน |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | ค้นหาส่วน DNA ที่ตรงกันซึ่งสืบทอดมาจากบรรพบุรุษร่วมกัน ใช้ข้อมูลจีโนไทป์ที่มีตัวแปรที่กำหนดให้กับสำเนาโครโมโซม |
| [WhatsHap](https://github.com/whatshap/whatshap) | ใช้การอ่านลำดับเพื่อกำหนดตัวแปรให้กับสำเนาโครโมโซม |
| [Truvari](https://github.com/ACEnglish/truvari) | เปรียบเทียบตัวแปรโครงสร้างในไฟล์ VCF |
| [IGV](https://igv.org/doc/desktop/) | แสดงการอ่าน ตัวแปร และแทร็กจีโนมอื่นๆ ที่สอดคล้อง ณ ตำแหน่งเฉพาะ |
| [JBrowse](https://jbrowse.org/jb2/) | ให้คุณเรียกดูลำดับการอ้างอิงและแทร็กที่เชื่อมโยงแบบโต้ตอบได้ |
| [GenomeSpy](https://genomespy.app/) | แสดงผลแผนภูมิจีโนมเชิงโต้ตอบด้วยการเร่งความเร็วกราฟิกของเบราว์เซอร์ |
| [Gramps](https://www.gramps-project.org/) | จัดระเบียบบันทึกลำดับวงศ์ตระกูล แผนภูมิลำดับวงศ์ตระกูล และข้อมูล GEDCOM |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | คำอธิบายประกอบตัวแปรโดยใช้แหล่งที่มาและคำอธิบายประกอบที่เลือกได้ |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | คาดการณ์ว่าตัวแปรต่างๆ อาจส่งผลต่อยีน ข้อความถอดเสียง และโปรตีนอย่างไร |
| [PharmCAT](https://pharmcat.org/) | สร้างรายงานการวิจัยทางเภสัชพันธุศาสตร์จากอินพุตจีโนไทป์ที่รองรับ |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | รันโมเดลภาษาท้องถิ่นที่เป็นตัวเลือกบนรันไทม์ของ CPU และ GPU ที่เข้ากันได้ |

[เวอร์ชันของเครื่องมือและข้อกำหนดเบื้องต้น](../VERSIONS.md)

## เริ่มต้นเลย

เลือกแพ็คเกจที่ตรงกับระบบปฏิบัติการและโปรเซสเซอร์ของคุณ หน้าเผยแพร่แสดงรายการดาวน์โหลด x64 และ ARM64 สำหรับ Windows, Linux และ macOS บางรุ่นเป็นเพียงการแสดงตัวอย่าง

1. บน Windows ให้แยกไฟล์เก็บถาวรและรัน Launcher ตั้งค่า Core ให้เสร็จสิ้นเมื่อได้รับแจ้ง
2. บน Linux ให้สตาร์ทเชลล์ลอนเชอร์ที่มาพร้อมกับ Python, GTK และ WebKitGTK ที่ติดตั้งไว้
3. บน macOS ให้เก็บแอปไว้ข้างไฟล์พื้นที่ทำงานที่แตกออกมา การแสดงตัวอย่างต้องใช้ macOS 13 หรือใหม่กว่า และ Python 3.12 หรือใหม่กว่า
4. เริ่มต้นด้วยตัวอย่างสังเคราะห์ที่รวมไว้เพื่อลองใช้เวิร์กโฟลว์โดยไม่ต้องใช้ไฟล์ส่วนบุคคล

[ดาวน์โหลด](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [คู่มือการติดตั้ง](../GETTING_STARTED.md)

## บรรทัดคำสั่งและระบบอัตโนมัติ

ใช้รีจีสทรีคำสั่งเดียวกันผ่านอินเทอร์เฟซเดสก์ท็อป CLI, JSON-RPC และ MCP บริการ headless ทำงานบนเครื่องท้องถิ่น คุณสามารถแสดงรายการคำสั่งและอ่านสคีมาได้โดยไม่ต้องเปิดหน้าต่างเดสก์ท็อป

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

ตัวช่วยเสริมสามารถช่วยคุณนำทางผลลัพธ์ได้ คำตอบไม่ได้แทนที่ข้อมูลต้นฉบับหรือการวิเคราะห์ที่ได้รับการตรวจสอบแล้ว

> ซอฟต์แวร์วิจัย ผลลัพธ์ขึ้นอยู่กับอินพุต วิธีการ และการอ้างอิง DNA Workbench Suite ไม่ได้ให้การวินิจฉัยทางคลินิก

## โครงการและการสนับสนุน

ดูแลโดย Oktay Du / OD พร้อมความช่วยเหลือจาก AI

[ความเป็นส่วนตัว](../PRIVACY.md) · [ความปลอดภัย](../../SECURITY.md) · [ใบอนุญาตโครงการ](../../LICENSE) · [รายงานปัญหา](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

สนับสนุนโครงการ · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## การแปล

แอปนี้มีภาษาอินเทอร์เฟซแบบออฟไลน์ 36 ภาษา เลือกคำแปลของหน้าโครงการด้านล่างนี้

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
