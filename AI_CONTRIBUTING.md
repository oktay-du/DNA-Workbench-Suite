# AI contributor guide

A reusable assignment for coding agents and developers using AI. Read [AGENTS.md](AGENTS.md) and [Contributing](CONTRIBUTING.md) before changing the repository. This guide is an instruction template, not an automatic background task.

## Product direction

DNA Workbench Suite aims to be a comprehensive, local-first genomics workspace: bring feasible DNA-provider and research-service workflows onto the user's PC, organize evidence by person and source, and make tools accessible through a consistent interface.

| Principle | Direction |
|---|---|
| One workspace | Connect source intake, quality review, dataset preparation, family research, ancestry, variant/health research and exports. |
| Evidence first | Keep sources, builds, versions, hashes, quality limits and measured/imputed distinctions traceable. Reuse valid results instead of repeating work. |
| Local by default | Store profiles, results, caches and optional modules beneath the application folder. WSL and other host requirements must be detected and explained. |
| AI optional | Support local chat and generation with suitable local models, plus user-configured external APIs. Core workflows must remain useful without AI. |
| Explicit external access | Users choose online integrations and review sensitive payloads before transmission. Never silently upload DNA, findings or portraits. |
| Consistent control | GUI, CLI, JSON and MCP use the same typed commands and validation. New actions must be discoverable through that registry. |
| Accessible research | Clear navigation, helpful defaults, English source text, German localization, keyboard access and light/dark themes. |
| Responsible integration | Respect upstream licenses and method limits. An adapter or plugin is not permission to redistribute restricted tools or data. |

This is a direction for development, not a claim that every capability already exists. Establish current behavior from source and runnable checks. Software tests do not establish clinical or ancestry accuracy.

## Copy this prompt into your coding agent

```text
Improve DNA Workbench Suite from its current repository state.

Read AGENTS.md, AI_CONTRIBUTING.md, CONTRIBUTING.md and the documentation
relevant to the area you inspect. Follow applicable directory instructions.

1. Inspect the current default branch and working tree. Preserve other people's
   changes. Read recent issues and ALL open, merged and closed pull requests,
   including relevant descriptions, changed files and review discussions.
   If history is unavailable, report that limitation and do not claim that
   duplicate checking succeeded.

2. Identify candidate improvements in security, correctness, functionality,
   performance, caching, reliability, maintainability, accessibility, design,
   navigation or menu/submenu organization. Select exactly ONE concrete,
   evidence-backed improvement with a clear user benefit and bounded scope.
   Avoid broad rewrites and speculative features. Inspect the relevant code
   before deciding; a missing comment or warning is not itself a defect.

3. Check whether the same outcome is already implemented or covered by any
   existing PR. If so, choose a different improvement. Do not repeat a closed
   or rejected proposal under another title. A new issue in the same broad
   category is distinct only when its trigger and intended behavior differ.
   Recheck for overlapping open work immediately before publishing.

4. State the chosen problem, the evidence, the intended behavior and acceptance
   criteria. Use an isolated branch from the current default branch. Make the
   smallest coherent change that solves this one problem. Keep unrelated
   reformatting, dependency upgrades and cleanup out of the change.

5. Validate the actual behavior. Use synthetic fixtures only. Run the checks
   required for affected code and relevant CI gates. For performance changes,
   compare a repeatable before/after measurement. For UI changes, inspect the
   result in both themes, supported languages and a narrow layout, including
   keyboard navigation. Preserve scientific limits and data provenance.
   Never weaken checks, suppress new findings without a source-specific review,
   or claim a skipped/unavailable test passed.

6. Update affected documentation and distribution manifests when needed. Inspect
   the diff for personal data, secrets, downloaded datasets and unrelated edits.
   Commit and open ONE pull request against the upstream default branch, using
   a fork if necessary. Describe the problem, resulting behavior, validation
   and material limitations. Link related issues and relevant duplicate checks.
   Disclose AI assistance briefly; do not invent tests, results or PR links.

7. Stop after the PR. Do not merge it, publish a release, delete branches or
   begin another improvement without a new instruction. If push/PR access is
   unavailable, leave a reviewable commit or patch and explain the exact blocker.
```

## Check existing work

Use GitHub's Issues and Pull requests views or the equivalent API. With the GitHub CLI, start with:

```powershell
gh issue list --repo oktay-du/DNA-Workbench-Suite --state all --limit 100
gh api --paginate 'repos/oktay-du/DNA-Workbench-Suite/pulls?state=all&per_page=100' --jq '.[] | {number,title,state,merged_at,html_url}'
gh pr view <number> --repo oktay-du/DNA-Workbench-Suite --comments
gh pr diff <number> --repo oktay-du/DNA-Workbench-Suite
```

Inspect additional issue pages if the first 100 do not cover the candidate. Title matching is only a first pass: inspect behavior and changed files. Keep a short private list of rejected candidates; the public PR needs only the relevant overlap checks.

## Make one improvement reviewable

| Area | Useful evidence |
|---|---|
| Security | Concrete input-to-sensitive-operation path, existing validation and a meaningful regression or source-specific analysis. Report exploitable vulnerabilities through [private reporting](https://github.com/oktay-du/DNA-Workbench-Suite/security/advisories/new), not a public exploit PR. |
| Correctness and reliability | A reproducible trigger, expected behavior, and a synthetic case that exercises the failure. |
| Speed and caching | Comparable inputs and environment, elapsed time or resource use, cache invalidation and result-equivalence checks. |
| UI and navigation | The actual affected journey, before/after views, language/theme coverage and keyboard behavior. |
| Functionality and adapters | A defined input/output contract, compatible formats/builds, upstream license and explicit dependency requirements. |
| Readability and maintenance | A demonstrated source of mistakes or duplication; preserve behavior and avoid file-wide cosmetic changes. |

Use the repository's documented checks. See [Development](docs/DEVELOPMENT.md), [Security checks](docs/SECURITY_CHECKS.md), [Agent integration](docs/AGENTS.md) and [formats](docs/TOOL_FORMATS.md). Update the public allowlist and integrity/presentation metadata if a packaged file changes; source archives are outputs, never the working copy.

## Pull request handoff

A useful PR contains a concrete trigger and resulting behavior, focused changes, validation evidence, relevant overlap checks and any material limitations. Use the repository PR template. Keep internal planning, raw logs and conversations out of the public description.

Contributors retain responsibility for permissions and applicable component licenses. AI assistance does not establish ownership or scientific validity. Never commit real DNA, findings, family identities, photos, API keys, signed download links or control credentials.
