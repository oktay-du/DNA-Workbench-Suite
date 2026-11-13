# DNA Workbench Suite

**DNS-fájlok, családi nyilvántartások és kutatási munkafolyamatok egyetlen helyi munkaterületen.**

[Letöltés](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Weboldal](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=hu) · [Telepítési útmutató](../GETTING_STARTED.md) · [Fordítások](#translations)

Rendszerezze a forrásokat személyek és szolgáltatók szerint, hasonlítsa össze a kompatibilis fájlokat, és tartsa meg minden elemzés mögött a bemeneti adatokat és az eredményeket.

![Alkalmazástúra világos és sötét móddal, nyelvválasztóval és szintetikus profilfájlokkal](../images/workspace-demo.gif)

[Tekintse meg az alkalmazás bemutatóját](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=hu#tour) · [Képernyőkép galéria](../GALLERY.md)

## Mit tehetsz

- Importáljon DNS-fájlokat, mappákat és támogatott archívumokat. Tekintse át a szolgáltatót, a formátumot és a referencia buildet, mielőtt bármit másol vagy áthelyez.
- Adatkészletek, dokumentumok és eredmények csoportosítása profil szerint. Rögzítse az egyes fájlok eredetét. A közvetlen méréseket tartsa elkülönítve a kikövetkeztetett értékektől, és vegye figyelembe, ha változatokat rendeltek a kromoszómamásolatokhoz.
- Ellenőrizze a minta minőségét és hasonlítsa össze a forrásokat. Készítsen egy verziószámú BestDataset-t olyan munkafolyamatokhoz, amelyek ugyanazt a referencia-felépítést használhatják.
- Fedezze fel a változatokat és a szekvenciafájlokat a genomnézegetőkkel. Hasonlítsa össze a DNS-profilokat, és kapcsolja össze a kutatási feljegyzéseket a családi nyilvántartásokkal és a GEDCOM fájlokkal.
- Mentse el az eredményeket bemeneteikkel és naplóikkal. Exportálja a jelentéseket, és készítsen biztonsági másolatot a profilokról későbbi használatra.
- A munkaterületen való navigáláshoz használja az opcionális helyi asszisztenst. A külső AI-t külön is konfigurálhatja.

[Teljes szolgáltatás katalógus](../FEATURES.md) · [Támogatott formátumok](../TOOL_FORMATS.md)

## Eszközök és mit csinálnak

Ezek olyan kiválasztott eszközök, amelyeket a programcsomag integrál, vagy elindíthat. Az elérhetőség munkafolyamattól és operációs rendszertől függően változik. Egyes modulok és referenciaadatok külön letölthetőek.

| Eszköz | Mit csinál |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Beolvassa, indexeli és ellenőrzi a SAM, BAM és CRAM formátumú összehangolt szekvenciális fájlokat. |
| [BCFtools](https://samtools.github.io/bcftools/) | Szűri, normalizálja, egyesíti és ellenőrzi a VCF és BCF formátumú fájlváltozatokat. |
| [fastp](https://github.com/OpenGene/fastp) | Ellenőrzi a FASTQ olvasási minőségét, és szabályozhatja vagy szűrheti a leolvasásokat. |
| [mosdepth](https://github.com/brentp/mosdepth) | Méri a lefedettséget a BAM és CRAM fájlokból. |
| [MultiQC](https://seqera.io/multiqc/) | Több minőségellenőrző eszköz jelentését egyesíti egy nézetben. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Genotípus adatokkal dolgozik olyan feladatokhoz, mint a variánsszűrés, a rokonság és a főkomponens elemzés. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Genotípusadatokat használ annak megállapítására, hogy mely változatok találhatók a kromoszóma ugyanazon másolatán. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Megtalálja a közös őstől örökölt DNS-szegmenseket. A kromoszómamásolatokhoz rendelt variánsokkal genotípus adatokat használ. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Szekvenálási leolvasásokat használ, hogy változatokat rendeljen a kromoszóma másolatokhoz. |
| [Truvari](https://github.com/ACEnglish/truvari) | Összehasonlítja a szerkezeti változatokat a VCF fájlokban. |
| [IGV](https://igv.org/doc/desktop/) | Megjeleníti az igazított leolvasásokat, változatokat és egyéb genomnyomokat meghatározott helyeken. |
| [JBrowse](https://jbrowse.org/jb2/) | Lehetővé teszi, hogy interaktívan böngésszen a referenciasorozatok és a kapcsolódó műsorszámok között. |
| [GenomeSpy](https://genomespy.app/) | Interaktív genomi diagramokat jelenít meg böngésző grafikus gyorsításával. |
| [Gramps](https://www.gramps-project.org/) | Rendszerezi a genealógiai nyilvántartásokat, a családfákat és a GEDCOM adatokat. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Választható források és annotátorok segítségével jegyzi a változatokat. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Megjósolja, hogy a változatok hogyan befolyásolhatják a géneket, a transzkriptumokat és a fehérjéket. |
| [PharmCAT](https://pharmcat.org/) | Farmakogenetikai kutatási jelentéseket készít támogatott genotípus inputokból. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Az opcionális helyi nyelvi modellt futtatja kompatibilis CPU és GPU futási környezeteken. |

[Szerszám verziók és előfeltételek](../VERSIONS.md)

## Kezdje el

Válassza ki az operációs rendszerének és processzorának megfelelő csomagot. A kiadási oldal felsorolja a x64 és ARM64 letöltéseket a Windows, Linux és macOS típusokhoz. Egyes buildek előzetesek.

1. A Windows készüléken bontsa ki az archívumot, és futtassa az indítót. Amikor a rendszer kéri, fejezze be a Core beállítását.
2. A Linux készüléken indítsa el a mellékelt shell-indítót a Python, GTK és WebKitGTK telepítésével.
3. A macOS készüléken tartsa az alkalmazást a kicsomagolt munkaterület-fájlok mellett. Az előnézethez macOS 13 vagy újabb és Python 3.12 vagy újabb verzió szükséges.
4. Kezdje a mellékelt szintetikus mintákkal, és próbálja ki a munkafolyamatokat személyes fájlok használata nélkül.

[Letöltés](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Telepítési útmutató](../GETTING_STARTED.md)

## Parancssor és automatizálás

Ugyanazt a parancs-nyilvántartást használja az asztali felületen keresztül: CLI, JSON-RPC és MCP. A fej nélküli szolgáltatás a helyi gépen fut. Kilistázhatja a parancsokat és elolvashatja a sémáikat anélkül, hogy asztali ablakot nyitna meg.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Az opcionális asszisztens segíthet a találatok navigálásában. Válaszai nem helyettesítik a forrásadatokat vagy az ellenőrzött elemzést.

> Kutató szoftver. Az eredmények a bemenettől, a módszertől és a hivatkozásoktól függenek. A DNA Workbench Suite nem ad klinikai diagnózist.

## Projekt és támogatás

Oktay Du / OD által karbantartott mesterséges intelligencia segítségével.

[Adatvédelem](../PRIVACY.md) · [Biztonság](../../SECURITY.md) · [Projekt engedély](../../LICENSE) · [Probléma bejelentése](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Támogassa a projektet · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Fordítások

Az alkalmazás 36 offline felületi nyelvet tartalmaz. Válassza ki a projekt oldalának fordítását alább.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
