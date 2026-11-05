# Contributing

Contributions are welcome under the applicable file terms described in [licensing scope](docs/LICENSING.md). Contributors retain copyright; commercial relicensing of their additions requires their permission. Third-party licenses remain separate. Work on a branch and submit a focused pull request with the concrete problem, resulting behaviour, relevant validation and limits.

Read the architecture and workflow method notes first. Agree on command schemas, profile ownership, file types/build semantics and output contracts before changing multiple layers. For parallel human/agent work, use separate Git worktrees and non-overlapping responsibilities; integrate and test the complete journey afterwards. More agents or subscriptions are not required.

Keep changes small and reviewable. Add meaningful synthetic regressions for data integrity, security or scientific boundary changes. Validate navigation, focus, narrow layouts and both themes for UI changes. Do not add fake results, bypass input quality checks, automatically launch large jobs on import or assume a bigger/newer file is better.

Never submit personal DNA, names of real relatives, signed provider links, real clinical PDFs, photos, tokens, local control files or database exports. Use only the Samples fixtures or generated temporary data. A clinical or ancestry method needs an explicit source, version and documented limitations; passing software tests is not clinical validation.

Before proposing an optional tool, record its original project, pin, source artifact, license, disk requirements, entry point and a small runnable test. A plugin/download button cannot avoid upstream license terms. Keep attribution and upstream notices with any permitted adaptation.

Run the documented unittest command, build the EXE on Windows, test affected sample journeys and inspect the public package allowlist before release. Clean-host and specialised-tool results must identify the tested environment instead of implying universal support.
