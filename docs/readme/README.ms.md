# DNA Workbench Suite

**Fail DNA, rekod keluarga dan aliran kerja penyelidikan dalam satu ruang kerja tempatan.**

[Muat turun](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [laman web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ms) · [Panduan pemasangan](../GETTING_STARTED.md) · [Terjemahan](#translations)

Susun sumber anda mengikut orang dan pembekal, bandingkan fail yang serasi dan simpan input dan hasil di sebalik setiap analisis.

![Lawatan apl dengan mod terang dan gelap, pemilih bahasa dan fail profil sintetik](../images/workspace-demo.gif)

[Tonton lawatan apl](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=ms#tour) · [Galeri tangkapan skrin](../GALLERY.md)

## Apa yang anda boleh lakukan

- Import fail DNA, folder dan arkib yang disokong. Semak pembekal, format dan binaan rujukan sebelum anda menyalin atau memindahkan apa-apa.
- Kumpulan set data, dokumen dan keputusan mengikut profil. Rekodkan asal setiap fail. Pastikan ukuran langsung diasingkan daripada nilai yang disimpulkan dan perhatikan apabila varian telah diberikan kepada salinan kromosom.
- Semak kualiti sampel dan bandingkan sumber. Bina BestDataset versi untuk aliran kerja yang boleh menggunakan binaan rujukan yang sama.
- Terokai varian dan fail jujukan dengan penonton genom. Bandingkan profil DNA dan sambungkan nota penyelidikan dengan rekod keluarga dan fail GEDCOM.
- Simpan hasil dengan input dan log mereka. Eksport laporan dan sandarkan profil untuk kegunaan kemudian.
- Gunakan pembantu tempatan pilihan untuk menavigasi ruang kerja. Anda boleh mengkonfigurasi AI luaran secara berasingan.

[Katalog ciri penuh](../FEATURES.md) · [Format yang disokong](../TOOL_FORMATS.md)

## Alat dan apa yang mereka lakukan

Ini adalah alat terpilih yang digabungkan atau boleh dilancarkan oleh suite. Ketersediaan berbeza mengikut aliran kerja dan sistem pengendalian. Sesetengah modul dan data rujukan adalah muat turun yang berasingan.

| alat | Apa yang dilakukannya |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Membaca, mengindeks dan memeriksa fail penjujukan sejajar dalam format SAM, BAM dan CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Menapis, menormalkan, menggabungkan dan memeriksa fail varian dalam format VCF dan BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Memeriksa kualiti bacaan FASTQ dan boleh memangkas atau menapis bacaan. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mengukur liputan membaca daripada fail BAM dan CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Menggabungkan laporan daripada berbilang alat kawalan kualiti ke dalam satu paparan. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Berfungsi dengan data genotip untuk tugasan seperti penapisan varian, perkaitan dan analisis komponen utama. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Menggunakan data genotip untuk membuat kesimpulan varian yang terletak pada salinan kromosom yang sama. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Menemui segmen DNA yang sepadan yang diwarisi daripada nenek moyang yang sama. Ia menggunakan data genotip dengan varian yang diberikan kepada salinan kromosom. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Menggunakan bacaan penjujukan untuk menetapkan varian kepada salinan kromosom. |
| [Truvari](https://github.com/ACEnglish/truvari) | Membandingkan varian struktur dalam fail VCF. |
| [IGV](https://igv.org/doc/desktop/) | Memaparkan bacaan sejajar, varian dan jejak genom lain di lokasi tertentu. |
| [JBrowse](https://jbrowse.org/jb2/) | Membolehkan anda menyemak imbas urutan rujukan dan trek dipautkan secara interaktif. |
| [GenomeSpy](https://genomespy.app/) | Memaparkan carta genomik interaktif dengan pecutan grafik penyemak imbas. |
| [Gramps](https://www.gramps-project.org/) | Menyusun rekod salasilah, salasilah keluarga dan data GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Menganotasi varian menggunakan sumber dan anotasi yang boleh dipilih. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Ramalkan cara varian boleh mempengaruhi gen, transkrip dan protein. |
| [PharmCAT](https://pharmcat.org/) | Menghasilkan laporan penyelidikan farmakogenetik daripada input genotip yang disokong. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Menjalankan model bahasa tempatan pilihan pada masa jalan CPU dan GPU yang serasi. |

[Versi alat dan prasyarat](../VERSIONS.md)

## Mulakan

Pilih pakej yang sepadan dengan sistem pengendalian dan pemproses anda. Halaman keluaran menyenaraikan muat turun x64 dan ARM64 untuk Windows, Linux dan macOS. Sesetengah binaan adalah pratonton.

1. Pada Windows, ekstrak arkib dan jalankan pelancar. Lengkapkan persediaan Teras apabila digesa.
2. Pada Linux, mulakan pelancar shell yang disertakan dengan Python, GTK dan WebKitGTK dipasang.
3. Pada macOS, simpan apl di sebelah fail ruang kerja yang diekstrak. Pratonton memerlukan macOS 13 atau lebih baru dan Python 3.12 atau lebih baru.
4. Mulakan dengan sampel sintetik yang disertakan untuk mencuba aliran kerja tanpa menggunakan fail peribadi.

[Muat turun](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Panduan pemasangan](../GETTING_STARTED.md)

## Barisan arahan dan automasi

Gunakan pendaftaran arahan yang sama melalui antara muka desktop, CLI, JSON-RPC dan MCP. Perkhidmatan tanpa kepala dijalankan pada mesin tempatan. Anda boleh menyenaraikan arahan dan membaca skemanya tanpa membuka tetingkap desktop.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Pembantu pilihan boleh membantu anda menavigasi hasil. Jawapannya tidak menggantikan data sumber atau analisis yang disahkan.

> Perisian penyelidikan. Keputusan bergantung pada input, kaedah dan rujukan. DNA Workbench Suite tidak memberikan diagnosis klinikal.

## Projek dan sokongan

Dikekalkan oleh Oktay Du / OD dengan bantuan AI.

[Privasi](../PRIVACY.md) · [Keselamatan](../../SECURITY.md) · [Lesen projek](../../LICENSE) · [Laporkan masalah](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Sokong projek · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Terjemahan

Aplikasi ini termasuk 36 bahasa antara muka luar talian. Pilih terjemahan halaman projek ini di bawah.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
