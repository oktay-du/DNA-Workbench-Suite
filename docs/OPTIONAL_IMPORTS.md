# Guided optional tool and dataset imports

Open **Guided optional imports** in the app. Select a known manifest item and read the upstream license and eligibility conditions. RFMix academic-use terms remain explicit; a checkbox is a user declaration, not a license grant. Research-only or unknown rights do not become unrestricted because installation is manual.

The page shows the exact download/cache filename, SHA-256 when pinned, planned runtime target and a separate manual-staging folder. All Windows locations are below the current application root; Linux targets are inside its managed WSL disk. Use the original publisher to obtain files for which you have permission. Choose Copy or Move explicitly.

A pinned hash must match before import. Existing different bytes are not overwritten. Unknown-hash files remain in `DNA_Software/ManualAssets/<asset-id>/` for manual review. Staging does not execute anything or mark a component as installed. Installation is a separate action using a reviewed adapter, if available; other tools require the publisher's manual installation instructions. The configured paths and cache names can also be used directly in Explorer. Preserve upstream license/NOTICE files.

CLI/JSON/MCP commands: `assets.catalog`, `assets.plan`, `assets.import`. The same declarations and validation are used by the GUI. Imports do not bypass authentication, payment, eligibility, consent, a restricted data-use agreement or a missing third-party license.
