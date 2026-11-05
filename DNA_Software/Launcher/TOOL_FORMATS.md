# Tool input contracts

Each file input declares its supported formats, packing, format versions, reference restrictions and sidecars. `tool.inputs` exposes the contract to GUI, CLI and MCP. These are conservative **suite adapter policies**, not a claim that every upstream version or scientific use is supported. The original tool parser validates records during execution. A readable header does not establish file completeness, identity, coverage or clinical accuracy.

- VCF: bounded content/header probe; declared VCF 4.1–4.3 admitted by the current contract. Other versions need explicit adapter validation; they are not labelled corrupt.
- BCF 2.2: QC, normalize, filter and the explicit VCF/BCF repacking tool. The latter preserves genotypes and build, never invents missing reads.
- FASTQ / FASTA: only packing accepted by the selected adapter. Read pairing, reference applicability and parser validation remain separate requirements.
- BAM/CRAM: binary version checked; CRAM needs the exact original reference. Read phasing requires matching alignment indexes. BAM QC creates its own index in the job output.
- Reference FASTA: decoded input for current alignment/normalization adapters. A `.fa.gz` must be decoded first, not renamed.
- PGEN: matching PSAM and PVAR/PVAR.ZST required.
- Direct ZIP use is restricted to adapters explicitly supporting a single consumer export; otherwise use batch extraction and review payloads.
- ZIP, TAR, TAR.GZ, TAR.BZ2, TAR.XZ, GZIP, BZIP2 and XZ have local extraction paths. 7z, RAR and Zstandard are recognized and blocked with a missing-adapter explanation, rather than silently treated as text. No global host installation is assumed portable.

Archive extraction blocks traversal, symbolic/device links, encryption, case collisions, excessive expansion and incomplete writes. Both the original archive label and inner payload name appear in extracted filenames; exact member paths and parent checksums remain in provenance. Original archives are retained; this release does not irreversibly delete them. Payloads and their archive are not independent DNA measurements.

A rejected selection offers applicable existing steps: check/extract an archive, choose another compatible profile source, convert VCF/BCF, prepare chip genotypes as VCF, or prepare the existing **SNP-only** GRCh37→GRCh38 lift. Conversion is user-started and is not a repair guarantee. Variants cannot reconstruct original FASTQ reads. GRCh38 is not obtained by changing a label.

The source gate runs before job/cache selection in `suite_api.start` and again in direct engine validation. Source suggestions share the same contracts. Existing results retain source and version provenance; no new analysis starts on import without the reviewed batch action.
