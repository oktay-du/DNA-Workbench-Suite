# Results, findings and local document processing

DNA Workbench 0.14.0-dev stores completed tests by tool, selected profile(s), actual input paths/file state, reference inputs and parameters. Reopening the same selection displays its saved result. Use **Recalculate / Rerun** to explicitly run it again. Choosing another parent-child pair, changing a source/reference or changing a parameter needs its own first run. Importing files never starts an analysis automatically. Older results remain in Jobs and profile backups.

The check mark means a completed local run with the recorded input/output state, not clinical verification. Fast reuse checks file size and modification time; it is not a new whole-genome cryptographic or biological validation. Imported provider reports, calculated evidence, imputed genotypes and self-reported information stay distinct. Existing legacy jobs without the new provenance record remain available in Jobs; they are not silently certified as current.

## Findings

Each profile has a permanent random UUID independent of its editable name. The **Findings & local tests** page stores original reports, page-cited extracted text, OCR results, English/German translations, local-analysis PDFs and manually attributed information. The local AI can retrieve both imported and locally generated evidence. Contradictions are preserved; no majority-vote diagnosis or automatic clinical truth promotion is performed.

Completed local analysis workflows generate a research overview PDF and JSON artifact manifest. Original tool outputs remain authoritative artifacts and are separately exportable. Where the optional PDF runtime is missing, the completed analysis is retained and its status records `report_pending`; install the PDF tools and use **Publish local test PDFs**. Large genome outputs are listed without another expensive full-file hash pass. A summary PDF cannot replace a full clinical laboratory report.

## Local OCR and translation

- OCR: Tesseract 5.3.4 and Poppler 24.02 on the tested Ubuntu 24.04 host, installed through Ubuntu packages inside the suite WSL disk. Other hosts record their actual repository versions.
- OCR languages: English, German, Turkish, French, Spanish, Polish, Russian, Ukrainian and Arabic. Select languages to fit the document. OCR is limited to 100 pages per report; check low-confidence words, negations, units and numbers manually.
- Offline translation: CTranslate2 4.8.5, SentencePiece 0.2.2, NumPy 2.5.4 and PyYAML 6.0.3. Eight Argos translation packages (Arabic/German/Turkish/French/Spanish/Polish/Russian to English, plus English to German), roughly 1.01 GiB compressed in total. Ukrainian OCR is supported; a Ukrainian translation model is not bundled/configured. Arabic translation is disabled after a synthetic medical-term test mistranslated lactose intolerance; Arabic OCR remains supported.
- Model versions, HTTPS sources, exact sizes and recorded SHA-256 values are listed in `DNA_Software/Launcher/document-packages.json`. Model hashes were recorded from upstream HTTPS downloads, not a signed upstream checksum list.
- Windows-visible model location: `<suite>/DNA_Software/Models/DocumentTranslation`; download cache: `<suite>/DNA_Software/Downloads/DocumentModels`. Weights are optional downloads and excluded from the public source/EXE package.
- Original reports are retained. Derived text is labelled `ocr_extraction` or `machine_translation_en/de` and keeps its source document hash and processing metadata. A translation is not an independently confirming test.
- English and German exports are stored beside original OCR text and `processing-provenance.json` in the profile Reports directory. Translation is CPU-only and never sends the report to an online translation service.

Upstream: [Tesseract](https://github.com/tesseract-ocr/tesseract), [Tesseract language data](https://github.com/tesseract-ocr/tessdata_fast), [Poppler](https://poppler.freedesktop.org/), [Argos Translate](https://github.com/argosopentech/argos-translate), [model index](https://github.com/argosopentech/argospm-index), [CTranslate2](https://github.com/OpenNMT/CTranslate2), [SentencePiece](https://github.com/google/sentencepiece), [ReportLab](https://www.reportlab.com/opensource/), [pypdf](https://github.com/py-pdf/pypdf). Review the upstream package/model licenses; optional installation does not waive license obligations.

## Transfer and agent access

Profile export creates a checksummed folder with sources, reports, OCR/translation outputs, personal metadata, local analyses and family-link stubs. Shared software/reference/model installations are separate. Import checks UUID and hashes before activation. Replacing the same UUID requires explicit confirmation and creates a pre-import backup; changed local state after preview invalidates the import check. Backups contain private, unencrypted information.

GUI actions use the shared typed command catalog. CLI/JSON/MCP commands include `result.lookup`, `workflow.<id>` (`rerun: true` for explicit recomputation), `research.analysis-saved`, `profile.documents.process`, `profile.results.publish`, `profile.export`, `profile.import.check` and `profile.import`. `menu.findings` opens the findings page. Lookup commands never launch an initial analysis.
