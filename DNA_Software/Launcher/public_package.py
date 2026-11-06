"""Explicit source allowlist: never recurse through personal project/data folders."""

from pathlib import Path
import hashlib, json, shutil, zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
LAUNCHER = [
    "test_jobs_performance.py",
    "Locks/foundation-linux.in",
    "Locks/foundation-linux.txt",
    "security_sql.py",
    "security_paths.py",
    "network_io.py",
    "system_tools.py",
    "test_security_boundaries.py",
    "Notices/UI-PROMPTS-LICENSE.txt",
    "Launcher.cs",
    "Startup.cs",
    "LegacyLayout.cs",
    "localization.py",
    "layout_migration.py",
    "test_localization.py",
    "legacy-layout.json",
    "Locales/de.json",
    "Locales/de-intents.json",
    "Dependencies.cs",
    "app.manifest",
    "build.ps1",
    "DNAWorkbench.csproj",
    "make_catalog.py",
    "catalog.json",
    "engine.py",
    "inspector.py",
    "source_store.py",
    "linux_helpers.py",
    "family.py",
    "family.html",
    "family_verification.py",
    "visual_store.py",
    "visual.html",
    "world-land.json",
    "setup.ps1",
    "setup-linux-public.sh",
    "install-foundation.sh",
    "dependency_manager.py",
    "install-lock.json",
    "fetch_webview_sdk.py",
    "fetch_webview_runtime.py",
    "fetch_world.py",
    "prepare_embedded.py",
    "public_package.py",
    "test_family.py",
    "test_family_verification.py",
    "test_quality.py",
    "test_visual.py",
    "test_embedded_service.py",
    "test_dependencies.py",
]
LAUNCHER += [
    "matching.py",
    "matching_features.py",
    "matching.html",
    "matching.js",
    "matching.css",
    "genealogy_research.py",
    "test_matching.py",
    "DNA_COMPARISONS.md",
]
LAUNCHER += [
    "plugin_hub.py",
    "peddy_compat.py",
    "plugin_fixture.py",
    "plugins.html",
    "plugins.js",
    "project-audit.json",
    "test_plugins.py",
    "test_plugin_workflows.py",
    "PLUGINS_AND_LICENSES.md",
]
LAUNCHER += [
    "ModernShell.cs",
    "suite_api.py",
    "app.html",
    "app.css",
    "app.js",
    "shared-ui.js",
    "shared-ui.css",
    "local_ai.py",
    "mcp_dna.py",
    "ai-packages.json",
    "test_import_mode.py",
    "test_suite_api.py",
    "test_local_ai.py",
]
LAUNCHER += [
    "derived_sources.py",
    "best_assets.py",
    "source_batch.py",
    "research_synthesis.py",
    "test_source_batch.py",
    "SOURCE_GROUPS.md",
    "best_dataset.py",
    "test_best_dataset.py",
    "BEST_DATASET.md",
    "archive_io.py",
    "tool_contracts.py",
    "test_tool_contracts.py",
    "TOOL_FORMATS.md",
    "tool_inputs.py",
    "tool-wizard.js",
    "test_tool_inputs.py",
]
LAUNCHER += [
    "profile_collections.py",
    "batch_intake.py",
    "intake-ui.js",
    "test_batch_intake.py",
    "BATCH_PREPARATION.md",
]
LAUNCHER += [
    "cloud_ai.py",
    "cloud-ui.js",
    "tool_media.py",
    "catalog-ui.js",
    "genocat-catalog.json",
    "tool-media.json",
    "Notices/GENOCAT-LICENSE.txt",
    "API_AI.md",
    "GENOCAT.md",
    "test_cloud_ai.py",
    "test_tool_media.py",
]
LAUNCHER += [
    "story_art.py",
    "artwork-ui.js",
    "heritage-art.json",
    "atlas-countries.json",
    "test_story_art.py",
]
LAUNCHER += ["heritage_story.py", "themes.css", "THEMES.md", "test_heritage_story.py"]
LAUNCHER += ["workflows.py", "workflows-ui.js", "test_workflows.py"]
LAUNCHER += [
    "profile_files.py",
    "profile-files.js",
    "execution_journal.py",
    "test_profile_files.py",
]
LAUNCHER += ["comparison_cache.py", "test_comparison_cache.py"]
LAUNCHER += [
    "analysis_reports.py",
    "document_processing.py",
    "test_document_processing.py",
    "document-packages.json",
    "Locks/document-translation-windows.txt",
]
LAUNCHER += ["result_cache.py", "test_result_cache.py"]
LAUNCHER += [
    "workflow_sources.py",
    "test_workflow_sources.py",
    "PROFILE_SOURCES_AND_RESULTS.md",
]
LAUNCHER += [
    "profile_pipeline.py",
    "snp_liftover.py",
    "test_profile_pipeline.py",
    "PROFILE_PIPELINE.md",
]
LAUNCHER += ["Locks/pyliftover-windows.txt"]
LAUNCHER += [
    "portable_paths.py",
    "portable_json.py",
    "Portable.ps1",
    "test_portability.py",
    "PORTABILITY.md",
]
LAUNCHER += ["portable-check.ps1"]
LAUNCHER += ["test_portability_linux.py"]
LAUNCHER += [
    "sequence_tools.py",
    "test_sequence_tools.py",
    "SEQUENCE_TOOLS.md",
    "Locks/sequence-python-windows.txt",
]
LAUNCHER += [
    "provider_exports.py",
    "test_provider_exports.py",
    "release_tools.py",
    "project_info.json",
    "release-integrity.json",
    "23ANDME_EXPORTS.md",
    "SECURITY_AND_RELEASE.md",
]
LAUNCHER += [
    "support-qr.jpg",
    "feedback.py",
    "feedback-ui.js",
    "optional_assets.py",
    "test_optional_assets.py",
    "Notices/LEGACY-MIT-LICENSE.txt",
    "Notices/COMPONENT-SCOPE.json",
    "Notices/POLYFORM-NONCOMMERCIAL-1.0.0.md",
    "test_feedback.py",
    "project-notices.json",
    "third-party-inventory.json",
]
LAUNCHER += ["design-tokens.css", "workbench-ui.css", "ui-components.js"]
LAUNCHER += [
    "research_explorer.py",
    "durable_store.py",
    "test_research_explorer.py",
    "test_durable_store.py",
    "research-projects.json",
]
LAUNCHER += [
    "release_catalog.py",
    "sample_data.py",
    "release-ui.js",
    "test_public_samples.py",
]
LAUNCHER += [
    "profile_identity.py",
    "profile_transfer.py",
    "profile_documents.py",
    "profile-extras.js",
    "test_profile_transfer.py",
]
LAUNCHER += ["Public/presentation-manifest.json"]
LAUNCHER += ["Public/.gitattributes"]
LAUNCHER += [
    "Public/" + name
    for name in [
        "README.md",
        "LICENSE",
        "THIRD_PARTY.md",
        "SECURITY.md",
        "RELEASING.md",
        "FUNDING.yml",
        "build.yml",
        ".gitignore",
    ]
]
LAUNCHER += [
    "person_profile.py",
    "profile-page.js",
    "creative_exports.py",
    "test_profile_experience.py",
    "PROFILES_AND_EXPORTS.md",
]
LAUNCHER += [
    "command_bus.py",
    "agent_control.py",
    "agent_client.py",
    "dna_cli.py",
    "desktop_host.py",
    "test_desktop_host.py",
    "build_linux_appimage.sh",
    "agent.js",
    "DNA.cmd",
    "test_agent_control.py",
    "AGENT_CONTROL.md",
    "agent-projects.json",
]
LAUNCHER += [
    "Locks/" + name
    for name in [
        "peddy-linux.txt",
        "whatshap-linux.txt",
        "truvari-linux.txt",
        "pycirclize-windows.txt",
        "dnafeaturesviewer-windows.txt",
        "pygenomeviz-windows.txt",
    ]
]
START = [
    "DNA.ps1",
    "docker-dna.sh",
    "relocate-linux.py",
    "profile-dna.sh",
    "linux-launch.sh",
    "admixtools-gui.R",
    "containers-compose.yaml",
    "dna-nextflow.config",
]
LAUNCHER += [
    "OnDemand.cs",
    "on_demand.py",
    "Notices/RFMIX-LICENSE.txt",
    "test_on_demand.py",
]
LAUNCHER += ["data_scope.py", "test_data_scope.py", "DATA_SCOPE.md"]
LAUNCHER += [
    "VisualTools.cs",
    "visual_tools.py",
    "visual_plot.py",
    "extended_plot.py",
    "visual-viewer.html",
    "visual-packages.json",
    "test_visual_tools.py",
    "GENOME_VISUALIZATION.md",
]
LAUNCHER += [
    "heritage.py",
    "heritage.js",
    "heritage.css",
    "heritage-places.json",
    "heritage-images.json",
    "build_heritage_catalog.py",
    "fetch_heritage_images.py",
    "test_heritage.py",
    "Notices/UNICODE-LICENSE.txt",
    "CULTURAL_ATLAS.md",
]


def entries():
    if (HERE / "DNA.cmd").is_file():
        yield HERE / "DNA.cmd", "DNA.cmd"
    for name in LAUNCHER:
        source = HERE / name
        if source.exists():
            yield source, "DNA_Software/Launcher/" + name
    # Only image files explicitly named in the public, curated attribution manifest.
    if (HERE / "heritage-images.json").is_file():
        import re

        for entry in json.loads(
            (HERE / "heritage-images.json").read_text(encoding="utf-8")
        )["images"]:
            name = entry["file"]
            if not re.fullmatch("[a-z0-9_-]+[.]jpg", name):
                raise ValueError("Invalid cultural image path.")
            source = HERE / "heritage-assets" / name
            if source.is_file():
                yield source, "DNA_Software/Launcher/heritage-assets/" + name
    for row in json.loads((HERE / "heritage-art.json").read_text(encoding="utf-8"))[
        "images"
    ]:
        name = row["file"]
        source = HERE / name
        if (
            not __import__("re").fullmatch(r"heritage-art/[a-z0-9-]+[.]png", name)
            or hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]
        ):
            raise ValueError("Invalid generated artwork manifest")
        yield source, "DNA_Software/Launcher/" + name
    for name in START:
        source = ROOT / "DNA_Software/Start" / name
        if source.exists():
            yield source, "DNA_Software/Start/" + name
    # Only named, checksummed synthetic fixtures. Never recurse an arbitrary data folder.
    samples = HERE / "Public/Samples"
    if not (samples / "manifest.json").is_file():
        samples = ROOT / "Samples"
    if (samples / "manifest.json").is_file():
        import sample_data

        manifest = sample_data.validate(samples)
        for row in manifest["files"]:
            yield samples / row["path"], "Samples/" + row["path"]
        yield samples / "manifest.json", "Samples/manifest.json"


def payload():
    out = HERE / "core-payload.zip"
    integrity = [
        {"path": target, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        for source, target in entries()
        if source.name != "release-integrity.json"
    ]
    (HERE / "release-integrity.json").write_text(
        json.dumps(
            {
                "version": json.loads(
                    (HERE / "install-lock.json").read_text(encoding="utf-8")
                )["app_version"],
                "files": integrity,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for source, target in entries():
            z.write(source, target)
        for name in [
            "Microsoft.Web.WebView2.Core.dll",
            "Microsoft.Web.WebView2.WinForms.dll",
            "WebView2Loader.dll",
        ]:
            z.write(HERE / "WebView2" / name, name)
        for source in (HERE / "WebView2").glob("*LICENSE*"):
            z.write(source, "DNA_Software/Launcher/WebView2/" + source.name)
    print("Core payload:", out.stat().st_size, "bytes")


def presentation_entries():
    import re

    manifest = HERE / "Public/presentation-manifest.json"
    if not manifest.is_file():
        return
    for row in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        name = row["path"]
        if not (
            name
            in (
                "README.de.md",
                "CONTRIBUTING.md",
                "AI_CONTRIBUTING.md",
                "docs/examples/combined-research.pdf",
                "site/index.html",
                "site/privacy.html",
                "site/legal.html",
                "site/style.css",
                "site/images/03-overview-light.png",
                "site/images/provider-selection.png",
                "site/images/08-workflow.png",
                "site/images/support-qr.jpg",
                ".github/ISSUE_TEMPLATE/bug_report.yml",
                ".github/ISSUE_TEMPLATE/feature_request.yml",
            )
            or re.fullmatch(
                r"docs/(?:[A-Z_]+\.md|software-data-catalog\.json|images/[a-z0-9-]+\.(?:png|jpg|svg))",
                name,
            )
        ):
            raise ValueError("Unapproved public presentation path")
        source = HERE / "Public" / name
        if not source.is_file():
            source = ROOT / name
        if (
            source.is_symlink()
            or not source.resolve().is_relative_to((HERE / "Public").resolve())
            and not source.resolve().is_relative_to(ROOT.resolve())
        ):
            raise ValueError("Presentation path outside public roots")
        if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Presentation checksum mismatch: " + name)
        yield source, name


def package():
    dest = ROOT / "DNAWorkbench_Source"
    dest.mkdir(exist_ok=True)
    copied = []
    for source, target in entries():
        p = dest / target
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, p)
        if p.suffix == ".sh":
            p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
        if p.suffix == ".ps1":
            p.write_text(p.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
        copied.append(
            {
                "path": target,
                "sha256": hashlib.file_digest(p.open("rb"), "sha256").hexdigest(),
            }
        )
    for name in [
        "README.md",
        "LICENSE",
        "THIRD_PARTY.md",
        "SECURITY.md",
        "RELEASING.md",
        ".gitignore",
        ".gitattributes",
    ]:
        p = HERE / "Public" / name
        if p.exists():
            shutil.copy2(p, dest / name)
    (dest / ".github/workflows").mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "Public/FUNDING.yml", dest / ".github/FUNDING.yml")
    ci = HERE / "Public/build.yml"
    if ci.exists():
        shutil.copy2(ci, dest / ".github/workflows/build.yml")
    extra = []
    for source, target in presentation_entries():
        p = dest / target
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, p)
        extra.append(
            {"path": target, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        )
    for name in [
        "AGENTS.md",
        ".editorconfig",
        "pyproject.toml",
        "eslint.config.mjs",
        ".prettierrc.json",
        ".stylelintrc.json",
        ".htmlvalidate.json",
        "requirements-quality.in",
        "requirements-quality.txt",
        "requirements-fuzz.in",
        "requirements-fuzz.txt",
        "scripts/Benchmark-Workflows.py",
        "scripts/Test-NativeContracts.ps1",
        "tools/quality/package.json",
        "tools/quality/package-lock.json",
        "tools/quality/run.mjs",
        "fuzz/fuzz_parsers.py",
        "fuzz/corpus/gedcom/minimal.ged",
        "fuzz/corpus/gedcom/malformed.ged",
        "requirements-dev.txt",
        "requirements-security.txt",
        "NuGet.Config",
        ".github/dependabot.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/workflows/codeql.yml",
        ".github/workflows/pages.yml",
        "scripts/Seal-Source.py",
        "scripts/Deploy-Local.ps1",
        "scripts/Security-Audit.py",
        "security/ReviewedFindings.json",
    ]:
        source = ROOT / name
        if source.is_file():
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            extra.append(
                {
                    "path": name,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )
    copied += extra
    (dest / "source-manifest.json").write_text(
        json.dumps(copied, indent=2), encoding="utf-8"
    )
    archive = ROOT / "DNAWorkbench_Source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for row in copied:
            z.write(dest / row["path"], row["path"])
        for name in [
            "README.md",
            "LICENSE",
            "THIRD_PARTY.md",
            "SECURITY.md",
            "RELEASING.md",
            ".gitignore",
            ".gitattributes",
            "source-manifest.json",
            ".github/workflows/build.yml",
            ".github/FUNDING.yml",
        ]:
            if (dest / name).exists():
                z.write(dest / name, name)
    print(
        "Public source package:",
        dest,
        "·",
        len(copied),
        "source files; no personal data",
    )


if __name__ == "__main__":
    import sys

    payload() if "--payload" in sys.argv else package()
