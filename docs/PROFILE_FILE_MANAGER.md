# Profile file manager

Open **Data → Profile file manager**. The globally selected profile determines the scope. Search or filter datasets, provider findings, local tests, output files, saved result views and software starts. Each row records size, creation/import dates, format/build and the available source snapshot. Expand the source cell for provenance: a specific input file, or the recorded profile/Best Selection snapshot and date. Missing historical metadata remains explicitly unknown.

The profile total counts physical files once, including its database. Job rows and their individual output rows overlap; their sizes must not be added together. Shared tools, reference data, backups and recoverable trash are excluded. GB is decimal; GiB is binary.

## Editing files

- **Add dataset** opens the existing checked import workflow. **Add report** registers a document with local retrieval. **Start a test** opens quality workflows.
- Select one or more rows to export or move to the profile trash. Deleting a test includes its own output files and indexed reports. The preview lists the exact affected records before confirmation.
- Rename an ordinary source or provider document to change its physical filename and database paths, including a paired index where applicable. Technical job IDs and tool-managed output filenames stay stable; their display labels can be renamed. Historical analysis provenance is retained rather than rewritten as if the past calculation used a different input.
- Replace one file with a newly checked import, choosing copy or move. A replacement does not inherit the previous file's provider certainty or quality verification. Identical replacements are detected. Generated tests are replaced by an explicit rerun, not by uploading arbitrary output into a successful test.
- Active jobs and unrelated profiles are protected. Shared file bytes are retained when another live record needs them. Changes to relevant sources withdraw dependent verification and mark affected results for review. Personal details and family links are preserved. Rerunning remains a manual action.

## Recovery and execution records

Trash is reversible and **does not immediately free disk space**. Restore refuses to overwrite occupied or changed files. Ordinary profile exports exclude trash. Dependent results remain review-required until explicitly checked again; restoring a file is not scientific re-verification.

Terminal workflow states are registered in the profile database even without a PDF. The supported family calculations, raw matrix, untransmitted-allele calculation and profile GEDCOM export also save JSON results and execution records. Viewing a saved matching result records a view separately from a new calculation. Launching an external GUI records **Started**, not a completed scientific analysis. Conflicting database/job status is shown as a conflict.

The same typed commands are exposed to GUI, CLI and MCP: `profile.files`, `profile.files.preview`, `profile.files.apply`, `profile.files.restore`, `profile.files.export_paths`, and `research.viewed`. Mutations use expiring, profile-bound review tokens and background jobs. An absent source link cannot be reconstructed with certainty from an arbitrary imported file.
