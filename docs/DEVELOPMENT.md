# Development

## Source and runtime

Keep the Git checkout separate from personal profiles and the installed runtime. The checkout may reside on an external SSD. Edit source here; generated ZIP archives are build outputs.

The Windows host is C# / WebView2. The Linux host is the Python desktop window. Local services, workflows and command validation are Python; embedded views use HTML, CSS and JavaScript. GUI, CLI, JSON and MCP share the typed command registry. See [agent integration](AGENTS.md).

## Contributing

Fetch current changes, create a feature branch, implement a focused change and run relevant synthetic tests. Submit a pull request with behaviour and validation details. Coordinate separate agents through branches or worktrees rather than concurrent edits to the same files.

```powershell
python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"
powershell -NoProfile -File DNA_Software/Launcher/build.ps1
python DNA_Software/Launcher/public_package.py
python DNA_Software/Launcher/release_tools.py --target windows
```

```sh
python3 -m unittest discover -s DNA_Software/Launcher -p "test_*.py"
sh DNA_Software/Launcher/build_linux.sh
```

Use `scripts/Deploy-Local.ps1 -RuntimeRoot <existing-runtime>` to deploy a local build with an executable backup. Close that runtime before deployment. Personal data is not copied into Git.

## Data and distribution

DNA, findings, profiles, credentials, reference genomes, models, runtime caches and WSL disks are excluded from Git. Use the artificial Samples for tests and screenshots. Distribute the Windows and Linux zips through Releases; optional tools and datasets download on demand.

The project website is in `site/`; Pages deploys only that folder and selected documentation images.
