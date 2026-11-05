# Reference data and large downloads

The complete artifact list, pins, known sizes and source links is in [VERSIONS.md](VERSIONS.md) and [software-data-catalog.json](software-data-catalog.json). The app displays the same catalog in Versions & data. The snapshot was collected on 2026-11-03; a retrieval date is not a publisher's release date. Unknown size/checksum values remain unknown. A local file or directory is not evidence of a successful runtime test.

| Resource | Purpose and prerequisite |
|---|---|
| Exact FASTA + FAI and other indices | Must match alignment/reference identifiers; CRAM may require the exact reference, not merely a similarly named build. |
| Liftover chain | Point-coordinate mapping of supported observed SNPs. Not equivalent to realigning FASTQ or rebuilding all variants. |
| Ensembl VEP cache/annotation | Select species, build and VEP/cache version consistently. |
| ClinVar and gnomAD | Annotation and allele frequencies; preserve review conflicts, date, assembly and data-use terms. |
| 1000 Genomes / HGDP + metadata | Population comparisons require harmonised variants, allele orientation, build and labelled reference samples. Not raw read archives. |
| Genetic maps and phased panels | Needed for supported phasing/IBD workflows; use the matching assembly and chromosome naming. |
| PGS weight files | Score-specific allele/build requirements and population calibration; a score is not an absolute disease probability. |
| AADR | Optional ancient sample comparisons; similarity is not a proven direct ancestor or cultural identity. |
| DeepVariant / other models | Match sequencing technology and resource requirements; not a universal automatic repair step. |
| Local chat runtime/model | Optional llama.cpp CPU runtime and small Qwen model; inference quality and performance depend on hardware. |

Large data, model weights, upstream source archives and personal genomes are **not** included in the source repository. Downloads go to the workspace cache/data folders. Disk needs include download archives, extracted resources, indices and job intermediates; do not budget only for the final VCF. The current installer has no universal clean-host guarantee for every optional package. RFMix requires explicit license eligibility; a download plugin does not override license restrictions.
