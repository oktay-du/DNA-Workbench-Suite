# DNA Workbench Suite

**Tệp DNA, hồ sơ gia đình và quy trình nghiên cứu trong một không gian làm việc cục bộ.**

[Tải xuống](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Trang web](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=vi) · [Hướng dẫn cài đặt](../GETTING_STARTED.md) · [Bản dịch](#translations)

Sắp xếp các nguồn của bạn theo người và nhà cung cấp, so sánh các tệp tương thích và lưu giữ thông tin đầu vào cũng như kết quả sau mỗi phân tích.

![Tham quan ứng dụng với chế độ sáng và tối, bộ chọn ngôn ngữ và tệp hồ sơ tổng hợp](../images/workspace-demo.gif)

[Xem chuyến tham quan ứng dụng](https://oktay-du.github.io/DNA-Workbench-Suite/?lang=vi#tour) · [Thư viện ảnh chụp màn hình](../GALLERY.md)

## Bạn có thể làm gì

- Nhập tệp DNA, thư mục và kho lưu trữ được hỗ trợ. Xem lại nhà cung cấp, định dạng và bản dựng tham chiếu trước khi bạn sao chép hoặc di chuyển bất cứ thứ gì.
- Nhóm bộ dữ liệu, tài liệu và kết quả theo hồ sơ. Ghi lại nguồn gốc của mỗi tập tin. Giữ các phép đo trực tiếp tách biệt với các giá trị được suy ra và lưu ý khi các biến thể đã được gán cho các bản sao nhiễm sắc thể.
- Kiểm tra chất lượng mẫu và so sánh các nguồn. Xây dựng BestDataset được phiên bản cho các quy trình công việc có thể sử dụng cùng một bản dựng tham chiếu.
- Khám phá các biến thể và tệp trình tự với trình xem bộ gen. So sánh hồ sơ DNA và kết nối các ghi chú nghiên cứu với hồ sơ gia đình và tệp GEDCOM.
- Lưu kết quả với đầu vào và nhật ký của họ. Xuất báo cáo và sao lưu hồ sơ để sử dụng sau.
- Sử dụng trợ lý cục bộ tùy chọn để điều hướng không gian làm việc. Bạn có thể định cấu hình riêng AI bên ngoài.

[Danh mục đầy đủ tính năng](../FEATURES.md) · [Các định dạng được hỗ trợ](../TOOL_FORMATS.md)

## Công cụ và chức năng của chúng

Đây là những công cụ được chọn mà bộ tích hợp hoặc có thể khởi chạy. Tính khả dụng thay đổi tùy theo quy trình làm việc và hệ điều hành. Một số mô-đun và dữ liệu tham khảo được tải xuống riêng biệt.

| Công cụ | Nó làm gì |
| --- | --- |
| [SAMtools](https://www.htslib.org/) | Đọc, lập chỉ mục và kiểm tra các tệp tuần tự được căn chỉnh ở các định dạng SAM, BAM và CRAM. |
| [BCFtools](https://samtools.github.io/bcftools/) | Lọc, chuẩn hóa, kết hợp và kiểm tra các tệp biến thể ở định dạng VCF và BCF. |
| [fastp](https://github.com/OpenGene/fastp) | Kiểm tra chất lượng đọc FASTQ và có thể cắt hoặc lọc các lần đọc. |
| [mosdepth](https://github.com/brentp/mosdepth) | Đo phạm vi đọc từ các tệp BAM và CRAM. |
| [MultiQC](https://seqera.io/multiqc/) | Kết hợp các báo cáo từ nhiều công cụ kiểm soát chất lượng vào một chế độ xem. |
| [PLINK](https://www.cog-genomics.org/plink/2.0/) | Hoạt động với dữ liệu kiểu gen cho các tác vụ như lọc biến thể, mức độ liên quan và phân tích thành phần chính. |
| [Beagle](https://faculty.washington.edu/browning/beagle/beagle.html) | Sử dụng dữ liệu kiểu gen để suy ra những biến thể nào nằm trên cùng một bản sao của nhiễm sắc thể. |
| [hap-ibd](https://github.com/browning-lab/hap-ibd) | Tìm các đoạn DNA phù hợp được thừa hưởng từ một tổ tiên chung. Nó sử dụng dữ liệu kiểu gen với các biến thể được gán cho các bản sao nhiễm sắc thể. |
| [WhatsHap](https://github.com/whatshap/whatshap) | Sử dụng các lần đọc trình tự để gán các biến thể cho các bản sao nhiễm sắc thể. |
| [Truvari](https://github.com/ACEnglish/truvari) | So sánh các biến thể cấu trúc trong tệp VCF. |
| [IGV](https://igv.org/doc/desktop/) | Hiển thị các lần đọc, biến thể và dấu vết bộ gen khác được căn chỉnh tại các vị trí cụ thể. |
| [JBrowse](https://jbrowse.org/jb2/) | Cho phép bạn duyệt các chuỗi tham chiếu và các bản nhạc được liên kết một cách tương tác. |
| [GenomeSpy](https://genomespy.app/) | Hiển thị biểu đồ gen tương tác với khả năng tăng tốc đồ họa của trình duyệt. |
| [Gramps](https://www.gramps-project.org/) | Tổ chức hồ sơ phả hệ, cây gia phả và dữ liệu GEDCOM. |
| [OpenCRAVAT](https://docs.opencravat.org/en/latest/Home.html) | Chú thích các biến thể bằng cách sử dụng các nguồn và chú thích có thể chọn. |
| [Ensembl VEP](https://www.ensembl.org/info/docs/tools/vep/index.html) | Dự đoán các biến thể có thể ảnh hưởng đến gen, bản phiên mã và protein như thế nào. |
| [PharmCAT](https://pharmcat.org/) | Tạo báo cáo nghiên cứu dược động học từ đầu vào kiểu gen được hỗ trợ. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Chạy mô hình ngôn ngữ địa phương tùy chọn trên thời gian chạy CPU và GPU tương thích. |

[Phiên bản công cụ và điều kiện tiên quyết](../VERSIONS.md)

## Bắt đầu

Chọn gói phù hợp với hệ điều hành và bộ xử lý của bạn. Trang phát hành liệt kê các bản tải xuống x64 và ARM64 cho Windows, Linux và macOS. Một số bản dựng là bản xem trước.

1. Trên Windows, giải nén kho lưu trữ và chạy trình khởi chạy. Hoàn tất thiết lập Core khi được nhắc.
2. Trên Linux, khởi động trình khởi chạy shell đi kèm với cài đặt Python, GTK và WebKitGTK.
3. Trên macOS, giữ ứng dụng bên cạnh các tệp không gian làm việc đã được giải nén. Bản xem trước yêu cầu macOS 13 trở lên và Python 3.12 trở lên.
4. Bắt đầu với các mẫu tổng hợp đi kèm để thử quy trình làm việc mà không cần sử dụng tệp cá nhân.

[Tải xuống](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Hướng dẫn cài đặt](../GETTING_STARTED.md)

## Dòng lệnh và tự động hóa

Sử dụng cùng một sổ đăng ký lệnh thông qua giao diện máy tính để bàn, CLI, JSON-RPC và MCP. Dịch vụ không đầu chạy trên máy cục bộ. Bạn có thể liệt kê các lệnh và đọc lược đồ của chúng mà không cần mở cửa sổ màn hình nền.

```text
python DNA_Software/Launcher/dna_cli.py commands
python DNA_Software/Launcher/dna_cli.py serve
```

Trợ lý tùy chọn có thể giúp bạn điều hướng kết quả. Câu trả lời của nó không thay thế dữ liệu nguồn hoặc phân tích đã được xác minh.

> Phần mềm nghiên cứu. Kết quả phụ thuộc vào đầu vào, phương pháp và tài liệu tham khảo. DNA Workbench Suite không cung cấp chẩn đoán lâm sàng.

## Dự án và hỗ trợ

Được duy trì bởi Oktay Du / OD với sự hỗ trợ của AI.

[Quyền riêng tư](../PRIVACY.md) · [Bảo mật](../../SECURITY.md) · [Giấy phép dự án](../../LICENSE) · [Báo cáo sự cố](https://github.com/oktay-du/DNA-Workbench-Suite/issues/new/choose)

Hỗ trợ dự án · [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments](https://nowpayments.io/donation/oktayd) · [Patreon](https://www.patreon.com/Oktaydu/gift)

<a name="translations"></a>

## Bản dịch

Ứng dụng bao gồm 36 ngôn ngữ giao diện ngoại tuyến. Chọn bản dịch của trang dự án này bên dưới.

[Deutsch](../../README.de.md) · [English](../../README.md) · [Türkçe](README.tr.md) · [Español](README.es.md) · [Français](README.fr.md) · [Português](README.pt.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Svenska](README.sv.md) · [Ελληνικά](README.el.md) · [Čeština](README.cs.md) · [Română](README.ro.md) · [Magyar](README.hu.md) · [Polski](README.pl.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [اردو](README.ur.md) · [हिन्दी](README.hi.md) · [नेपाली](README.ne.md) · [ქართული](README.ka.md) · [Հայերեն](README.hy.md) · [Монгол](README.mn.md) · [简体中文](README.zh-Hans.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Bahasa Melayu](README.ms.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Filipino](README.fil.md) · [አማርኛ](README.am.md) · [Kiswahili](README.sw.md) · [Soomaali](README.so.md) · [Hausa](README.ha.md)
