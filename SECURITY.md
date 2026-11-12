# Security

DNA Workbench by OD is an experimental local research application. Use synthetic data in public issues. Never attach personal DNA, family databases, photographs, access tokens, signed download URLs, wallet secrets or medical records.

Report security vulnerabilities privately using [Report a vulnerability](https://github.com/oktay-du/DNA-Workbench-Suite/security/advisories/new). Private vulnerability reporting is enabled. Use a minimal synthetic reproduction; do not attach personal DNA or medical records.

Local SHA-256 manifests detect differences against a local baseline, not publisher identity. The application is currently unsigned. Obfuscation, anti-debugging and reverse-engineering-proof guarantees are not provided. Source code is MIT licensed; third-party components retain their licenses.

CLI, JSON, GUI and MCP commands share validation. Local control credentials must not be published. Imported reports and tool output are untrusted data, never instructions to execute.


Optional API features are disabled initially. Saving a key does not contact the provider. Keys are encrypted for the current account: Windows CurrentUser DPAPI, or AES-GCM on Linux with the account key kept outside the suite folder. They require re-entry after moving to another account or computer. Every external AI request requires a visible text review and explicit consent. Profile evidence is excluded by default. See [API boundary and limitations](docs/API_AI.md). Provider output never executes tool calls automatically].

## Automated checks

CodeQL analyses C# through an explicit project build, and scans Python, JavaScript and workflow definitions. Pull requests receive dependency review. Dependabot proposes reviewed updates for Actions, Python and NuGet. These checks require no external scanner subscription or API key.
