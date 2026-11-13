# DNA Workbench Suite

**File DNA, catatan keluarga, dan alur kerja penelitian di satu ruang kerja lokal.**

[Unduh](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Situs web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=id) · [Panduan instalasi](../GETTING_STARTED.md) · [Terjemahan](#translations)

Atur sumber Anda berdasarkan orang dan penyedia, bandingkan file yang kompatibel, dan simpan masukan serta hasil di balik setiap analisis.

![Tur aplikasi dengan mode terang dan gelap, pemilih bahasa, dan file profil sintetis](../images/workspace-demo.gif)

[Tonton tur aplikasi](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=id#tour) · [Galeri tangkapan layar](../GALLERY.md)

## Apa yang bisa Anda lakukan

- Impor file DNA, folder dan arsip yang didukung. Tinjau penyedia, format, dan referensi sebelum Anda menyalin atau memindahkan apa pun.
- Kelompokkan kumpulan data, dokumen, dan hasil berdasarkan profil. Catat asal setiap file. Pisahkan pengukuran langsung dari nilai yang disimpulkan dan catat kapan varian telah ditetapkan pada salinan kromosom.
- Periksa kualitas sampel dan bandingkan sumber. Bangun BestDataset berversi untuk alur kerja yang dapat menggunakan build referensi yang sama.
- Jelajahi varian dan urutan file dengan penampil genom. Bandingkan profil DNA dan hubungkan catatan penelitian dengan catatan keluarga dan file GEDCOM.
- Simpan hasil dengan masukan dan lognya. Ekspor laporan dan cadangan profil untuk digunakan nanti.
- Gunakan asisten lokal opsional untuk menavigasi ruang kerja. Anda dapat mengonfigurasi AI eksternal secara terpisah.

[Katalog fitur lengkap](../FEATURES.md) · [Format yang didukung](../TOOL_FORMATS.md)

## Alat dan apa yang mereka lakukan

Ini adalah alat terpilih yang diintegrasikan atau dapat diluncurkan oleh suite tersebut. Ketersediaan bervariasi berdasarkan alur kerja dan sistem operasi. Beberapa modul dan data referensi diunduh secara terpisah.

| Alat | Apa fungsinya |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Membaca, mengindeks, dan memeriksa file pengurutan yang selaras dalam format SAM, BAM, dan CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Memfilter, menormalkan, menggabungkan, dan memeriksa file varian dalam format VCF dan BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Memeriksa kualitas baca FASTQ dan dapat memangkas atau memfilter bacaan. |
| [mosdepth](https://github.com/brentp/mosdepth) | Mengukur cakupan baca dari file BAM dan CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Menggabungkan laporan dari beberapa alat kontrol kualitas ke dalam satu tampilan. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Bekerja dengan data genotipe untuk tugas-tugas seperti pemfilteran varian, keterkaitan, dan analisis komponen utama. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Menggunakan data genotipe untuk menyimpulkan varian mana yang terdapat pada salinan kromosom yang sama. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Menemukan segmen DNA yang cocok yang diwarisi dari nenek moyang yang sama. Ia menggunakan data genotipe dengan varian yang ditetapkan pada salinan kromosom. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Menggunakan pembacaan sekuensing untuk menetapkan varian pada salinan kromosom. |
| [Truvari](https://github.com/ACEnglish/truvari) | Membandingkan varian struktural dalam file VCF. |
| [IGV](https://igv.org/doc/desktop/) | Menampilkan pembacaan yang selaras, varian, dan trek genom lainnya di lokasi tertentu. |
| [JBrowse](https://jbrowse.org/jb2/) | Memungkinkan Anda menelusuri urutan referensi dan menghubungkan trek secara interaktif. |
| [GenomeSpy](https://genomespy.app/) | Merender bagan genom interaktif dengan akselerasi grafis browser. |
| [Gramps](https://www.gramps-project.org/) | Mengatur catatan silsilah, silsilah keluarga, dan data GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Memberi anotasi pada varian menggunakan sumber dan anotator yang dapat dipilih. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Memprediksi bagaimana varian dapat memengaruhi gen, transkrip, dan protein. |
| [PharmCAT](https://pharmcat.org/) | Menghasilkan laporan penelitian farmakogenetika dari input genotipe yang didukung. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Menjalankan model bahasa lokal opsional pada runtime CPU dan GPU yang kompatibel. |

[Versi alat dan prasyarat](../VERSIONS.md)

## Mulailah

Pilih paket yang cocok dengan sistem operasi dan prosesor Anda. Halaman rilis mencantumkan unduhan x64 dan ARM64 untuk Windows, Linux, dan macOS. Beberapa build adalah pratinjau.

1. Di Windows, ekstrak arsip dan jalankan peluncur. Selesaikan pengaturan Inti saat diminta.
2. Pada Linux, mulai peluncur shell yang disertakan dengan Python, GTK, dan WebKitGTK terinstal.
3. Di macOS, simpan aplikasi di samping file ruang kerja yang diekstraksi. Pratinjau memerlukan macOS 13 atau lebih baru dan Python 3.12 atau lebih baru.
4. Mulailah dengan sampel sintetis yang disertakan untuk mencoba alur kerja tanpa menggunakan file pribadi.

[Unduh](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Panduan instalasi](../GETTING_STARTED.md)

## Baris perintah dan otomatisasi

Gunakan registri perintah yang sama melalui antarmuka desktop, CLI, JSON-RPC dan MCP. Layanan tanpa kepala berjalan di mesin lokal. Anda dapat membuat daftar perintah dan membaca skemanya tanpa membuka jendela desktop.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Asisten opsional dapat membantu Anda menavigasi hasil. Jawabannya tidak menggantikan data awal atau analisis terverifikasi.

> Perangkat lunak penelitian. Hasil tergantung pada masukan, metode dan referensi. DNA Workbench Suite tidak memberikan diagnosis klinis.

## Proyek dan dukungan

Dikelola oleh Oktay Du / OD dengan bantuan AI.

[Privasi](../PRIVACY.md) · [Keamanan](../../SECURITY.md) · [Lisensi proyek](../../LICENSE) · [Laporkan masalah](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Dukung proyek ini · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Terjemahan

Aplikasi ini mencakup 36 bahasa antarmuka offline. Pilih terjemahan halaman proyek di bawah ini.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
