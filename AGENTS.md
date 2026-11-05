# Repository instructions

## Boundaries

Publish application source, synthetic Samples, reviewed screenshots and documentation only. Never commit personal DNA, medical reports, profiles, secrets, WSL disks, downloaded datasets or runtime caches. Do not scan a user archive implicitly. Imports, file moves and BestDataset renewal are explicit actions. Do not close unrelated browsers or interrupt downloads.

Preserve source hashes, reference builds, versions and measured/imputed distinctions. Do not claim a perfect genome, diagnosis, exact ancestry or reliable facial reconstruction. Preserve manually entered profile and family information during DNA refreshes.

## Architecture and development

C# / WebView2 hosts the Windows application. Python runs local services and typed commands; HTML, CSS and JavaScript implement embedded views. GUI, CLI, JSON and MCP share the command registry. See docs/AGENTS.md and docs/DEVELOPMENT.md.

Inspect git status before editing. Use focused branches and commits. Do not discard another contributor's work. Generated source ZIPs are distribution artifacts: never unpack one over the working checkout.

Run relevant synthetic tests with `python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`. Build with `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`. Scientific validation and clean-host installation are separate checks.

Version 1.0 is research software. Consult LICENSE and component notices before reusing or distributing code or data.
