# Architecture

The Windows C# shell embeds WebView2 and a Python loopback service. Vanilla JavaScript renders the workspace; several specialist local views are embedded. Core starts without WSL, optional models or all bioinformatics programs. Preparation is explicit per task.

`catalog.json` describes workflows; `command_bus.py` owns typed commands and schemas; GUI, CLI, newline JSON and MCP use the same command layer. `suite_api.py` coordinates workflow requests. `source_store.py` retains source provenance; `inspector.py` classifies file evidence; `workflow_sources.py` selects compatible inputs; `profile_pipeline.py` handles the constrained reconciliation pipeline. `on_demand.py`, `install-lock.json` and package manifests describe optional installers and artifacts.

Private SQLite state and job outputs live outside code. `portable_paths.py` derives the workspace from the extracted app location. `public_package.py` packages an explicit code list and checksummed synthetic fixture list. Public presentation assets have their own allowlist; personal folders are never traversed for publication.

Add new features through typed commands and a GUI entry, with method/requirements/limits, job ownership, source/output provenance and dependency handling. Do not add arbitrary shell strings as agent commands. Do not substitute UI placeholders for scientific results.
