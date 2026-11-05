# Security checks

CodeQL scans C#, Python, JavaScript and workflows. Bandit and Bearer report production-source findings. Python lock files and direct/transitive NuGet dependencies are checked against published vulnerability advisories. Secret scanning and dependency updates are enabled on GitHub.

The suite is a local desktop application. Its authenticated loopback API may read files explicitly selected by the user. Managed profile and job paths must remain within their own workspace directories. Public downloads use verified HTTPS and reject private network destinations; local service calls use a separate loopback-only path.

All raw Bandit and Bearer findings remain in the uploaded report. Reviewed non-vulnerabilities are recorded in `security/ReviewedFindings.json`, with a reason, supporting tests, a source-file hash and a finding fingerprint. Any unreviewed finding fails the audit. Changing a reviewed source file invalidates that review until it is checked again. Do not update hashes or dismiss alerts without reviewing the affected boundary.

Dependency checks cover declared pins and the NuGet project; they do not certify external services, scientific models or every installed optional tool. A successful scan is not a guarantee of security.

## Source quality

| Check | Scope |
| --- | --- |
| [PSScriptAnalyzer 1.25.0](https://github.com/PowerShell/PSScriptAnalyzer) | PowerShell security rules and parser errors |
| [ShellCheck 0.11.0](https://github.com/koalaman/shellcheck) | Shell correctness, quoting and unsafe constructs |
| [actionlint 1.7.12](https://github.com/rhysd/actionlint) | Workflow syntax and expression validation |
| Python AST / Node syntax checks | Syntax errors across tracked Python and JavaScript |
| Synthetic regression tests | Cache invalidation, duplicate handling, input validation and application behavior |

Static checks identify candidates for improvement; they do not rewrite scientific logic or prove that code is faster. Performance changes require representative measurements and regression coverage. Formatting-only changes should be separate from behavior changes. HTML/CSS accessibility and visual checks complement these source checks.

Coverage-guided Atheris fuzzing and source-quality checks run in the build workflow; see [Code quality](QUALITY.md). External badge certification is not required. Main uses mandatory pull requests and automated checks with a solo-maintainer review policy.


## CodeQL eligibility

New PolyForm Noncommercial contributions are source available, not OSI-approved open source. CodeQL CLI jobs are therefore disabled by default. Set the repository variable `ENABLE_LICENSED_CODEQL=true` only after confirming an appropriate entitlement under the [CodeQL terms](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md). This setting does not grant a CodeQL license. Other configured checks remain available independently.

The required checks use .NET build/analyzers, Ruff, ESLint, HTML/CSS validation, Bandit, Bearer, dependency audits, PowerShell/Shell/workflow checks and parser fuzzing. They do not pretend to provide CodeQL taint analysis when CodeQL is disabled. No paid scanner subscription is enabled automatically.
