# Repository instructions

For an explicitly requested autonomous improvement task, follow [AI_CONTRIBUTING.md](AI_CONTRIBUTING.md). Select one bounded improvement, inspect existing PRs and stop after opening the PR. Reading this file alone does not authorize a new task.

## Boundaries

Publish application source, synthetic Samples, reviewed screenshots and documentation only. Never commit personal DNA, medical reports, profiles, secrets, WSL disks, downloaded datasets or runtime caches. Do not scan a user archive implicitly. Imports, file moves and BestDataset renewal are explicit actions. Do not close unrelated browsers or interrupt downloads.

Preserve source hashes, reference builds, versions and measured/imputed distinctions. Do not claim a perfect genome, diagnosis, exact ancestry or reliable facial reconstruction. Preserve manually entered profile and family information during DNA refreshes.

## Architecture and development

C# / WebView2 hosts the Windows application. Python runs local services and typed commands; HTML, CSS and JavaScript implement embedded views. GUI, CLI, JSON and MCP share the command registry. See docs/AGENTS.md and docs/DEVELOPMENT.md.

Inspect git status before editing. Use focused branches and commits. Do not discard another contributor's work. Generated source ZIPs are distribution artifacts: never unpack one over the working checkout.

Run relevant synthetic tests with `python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`. Build with `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`. Scientific validation and clean-host installation are separate checks.

Version 1.0 is research software. Consult LICENSE and component notices before reusing or distributing code or data.

## Cursor Cloud specific instructions

Cloud Agent machines are Ubuntu with Python 3.12. The Windows launcher, `DNA_Software/Launcher/build.ps1`, and `scripts/Test-NativeContracts.ps1` run in Windows CI. On this VM, use the Python core.

- Login shells resolve `node` to Node 26.13.0 from `~/.local/bin` (the image also ships Node 22 at `/exec-daemon/node`). Ruff 0.17.3 is on `PATH` after install. Quality packages live in `tools/quality/node_modules`.
- Synthetic tests: `python3 -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`. Most cases run here. Failures that assume a Windows drive letter, Windows credential encryption, or a case-insensitive path (`Results` vs `results`) are expected on Linux and are covered by the Windows CI job.
- Quality: `ruff check DNA_Software/Launcher scripts fuzz`, `ruff format --check DNA_Software/Launcher scripts fuzz`, and `node tools/quality/run.mjs`.
- Headless workspace: `python3 DNA_Software/Launcher/dna_cli.py serve`, then open `http://127.0.0.1:<port>/app`. `commands` and `schema` work without the service. `DNA_Software/UserData/Launcher/control.json` holds the loopback credential; do not print, screenshot, or commit it. `sample.create` adds the four synthetic demo profiles (Alex, Robin, Sam, and Taylor Example).
- Desktop-only actions, including Family tree, report `NO_GUI` until `DNA_Launcher.exe` is attached on Windows or `dna_cli.py desktop` is running on Linux. Leave the headless process running in its own tmux session when you still need the UI.
