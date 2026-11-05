# 23andMe exports

The importer distinguishes raw measured genotype TXT, imputed VCF, phased genotype data, ancestry-composition CSV, family-tree JSON and PDF report summaries.

Measured, imputed and statistically phased data remain separate. An ancestry CSV contains interpreted regions, not additional measured genotypes. Family-tree JSON contributes genealogy metadata. PDF findings retain their original source and date.

Inspect the file's declared version, reference build and provenance before processing. Unknown metadata stay unknown until reviewed. Imputed or phased exports are not treated as clinically verified measurements.


## Current download bundles

- Raw Data: a ZIP containing one genotype TXT. Batch preparation preserves container/payload names and imports the TXT.
- Phased Genotype Data: a ZIP can contain `phased_genome_...txt` plus multiple `phased_genome_statistical_...txt` files. Import all through Batch preparation; each member remains separate with shared container lineage. These are derived arrangements, not three independent DNA tests. Statistical order does not by itself label mother/father.
- Imputed Genotype Data R6: chromosome-partitioned BCF files, including separate X non-PAR/PAR1/PAR2 partitions, are supported as a bundle inventory and reviewed batch import. BCF 2.2 headers are inspected locally; With follow-up tools enabled, BCFtools converts each partition to BGZF VCF, runs statistics and registers it with parent/container lineage for downstream comparison. The ZIP is not a VCF. Conversion cannot turn imputed values into measurements. Never blindly combine overlapping X intervals.

R6/build/chip versions are confirmed only from content or explicit provider metadata; filename hints stay provisional. No actual private files were used by the synthetic compatibility tests.
