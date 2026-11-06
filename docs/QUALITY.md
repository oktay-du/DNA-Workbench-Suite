# Code quality and performance

The build workflow checks Python, C#, JavaScript, HTML, CSS, PowerShell, Shell, workflow definitions and the optional R adapter. Development tools are separate from the end-user runtime.

| Tool | Version / configuration | Purpose |
| --- | --- | --- |
| Ruff | 0.17.3, hash-locked | Python errors, unused bindings and consistent formatting |
| .NET analyzers | .NET 8 recommended rules, warnings fail the build | C# correctness, culture-safe protocols and allocation/lookup issues |
| ESLint | 10.14.0 | Recommended JavaScript checks with classic-script globals derived from actual page script groups |
| Prettier | 3.9.10 | JavaScript, HTML and CSS readability |
| Stylelint | 18.0.0 | CSS syntax, unknown properties, invalid colors and duplicate declarations |
| HTML Validate | 11.18.0 | HTML structure, IDs and required attributes |
| jscpd | 5.4.2 | Exact duplicate blocks of at least 12 lines and 100 tokens |
| Atheris | 3.1.0, hash-locked | Coverage-guided parser fuzzing with synthetic seeds |

PSScriptAnalyzer, ShellCheck, actionlint, CodeQL, Bandit, Bearer and dependency audits are described in [Security checks](SECURITY_CHECKS.md). Positive controls verify that the web checks and duplicate detector actually reject invalid examples. Native tests verify catalog serialization and startup defaults after C# changes.

## Run locally

```powershell
python -m pip install --require-hashes -r requirements-quality.txt
ruff check DNA_Software/Launcher scripts fuzz
ruff format --check DNA_Software/Launcher scripts fuzz
npm ci --prefix tools/quality --ignore-scripts
npm audit --prefix tools/quality
node tools/quality/run.mjs
python scripts/Benchmark-Workflows.py --output quality-reports/benchmarks.json
```

Use Node 26 and Python 3.12. Install the three dependencies in `requirements-dev.txt` for the complete synthetic regression suite. On Windows, build with `DNA_Software/Launcher/build.ps1`, then run `scripts/Test-NativeContracts.ps1` using Windows PowerShell. The native compiler remains compatible with C# 5 / .NET Framework 4.8; analyzers are enabled in the SDK project. On Linux, `sh DNA_Software/Launcher/build_linux.sh` writes `DNAWorkbench-Linux-x64.zip`.

Web reports are written to `quality-reports/`. Formatting and fixes are reviewed changes, not automatic modifications to DNA-processing algorithms. The ESLint/config-array minimatch overrides select patched 11.0.4 for GHSA-g3hv-75wg-m249; npm audit and positive-control checks cover the locked tool graph.

## Performance evidence

The job view reads profile and transfer lists once per request. It does not persist a cache of profile results: added jobs, progress and deleted files are refreshed on subsequent requests. Tests enforce both freshness and bounded query counts.

A synthetic local benchmark with eight profiles and 96 jobs measured a median of 486 ms before and 327 ms after this change (three repeats). Profile queries fell from 105 to 1 per view; transfer-list reads fell from 9 to 1. These figures describe that fixture and machine. CI publishes its own timings rather than enforcing a hardware-dependent speed threshold.

## Parser fuzzing

CI copies the two checked-in synthetic seeds into an artifact directory before fuzzing. Atheris runs for 30 seconds with input, time and memory limits. Crashes and the generated corpus are retained as artifacts; the source corpus is never overwritten. The harness imports only local parsers and never reads profiles or starts scientific tools. It complements the deterministic regression tests.
