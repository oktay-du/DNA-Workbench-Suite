# Batch preparation and profile storage

Choose files, a complete folder (including subfolders), or all explicitly imported sources of the current profile. Optional format filters can select FASTQ and BAM together, VCF/BCF, reports, GEDCOM or other groups. Private download folders are never enumerated on startup.

The initial pass checks files together without importing or moving them. Review each profile/provider assignment. Unknown versions/builds remain unknown; optional manual declarations cannot contradict a detected build. GRCh37 and GRCh38 can coexist in the same profile and are not silently relabelled or compared as equal coordinates.

After review choose Move (default) or Copy and explicitly confirm. Sources go under `Profiles/<stable profile ID>/Sources/<provider>/<batch>/001-original-name`. Matching sidecar stems and original names are preserved in the registry. Byte-identical files are deduplicated. Move removes sources only after destination verification and successful registration. Registered sources held externally can also be organized without changing their file IDs.

Incomplete read sets are allowed. A first R1 stays usable for read-quality reporting; later R2 imports update the candidate read-pair inventory. Filename matching is a candidate relationship, not proof of sequencing completeness or biological identity. SNP, indel, CNV and other variant sources remain separate measurements. Unrecognized or conflicting files stay reviewable rather than receiving an invented quality certificate.

Automatic continuation uses file-specific adapters: VCF/BCF statistics, BAM/CRAM QC (exact CRAM reference required), report-only FASTQ quality, FASTA statistics, report extraction and GEDCOM parsing. Missing programs/references pause the affected step, while other files continue. No filtered FASTQ copies are created by the default report-only adapter. ZIP payloads requiring extraction or unsupported schemas remain explicitly pending rather than being misclassified as complete genotypes.

The source SNP comparison runs once per relevant profile after file-specific preparation. It is only an observed-SNP comparison, not whole-genome completion, alignment or clinical verification. New imports update availability; they never silently renew Best Selection.

Commands shared by GUI/CLI/MCP: `intake.start`, `intake.list`, `intake.read`, `intake.accept`, `intake.cancel`, `profile.collections`. Batch jobs retain their originating profile and per-file routed outcomes. Importing raw reads does not manufacture BAM/CRAM, variants or measured genotypes.

See TOOL_FORMATS.md for per-adapter compression/version contracts and BEST_DATASET.md for the explicit combined dataset builder, source contribution records and moved-file receipts. ZIP/TAR and supported single-stream compression can now be extracted through the reviewed batch action; originals are retained.
