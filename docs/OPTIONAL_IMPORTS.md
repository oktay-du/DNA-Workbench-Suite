# Guided optional tool and dataset imports

Open **Guided optional imports** in the app. Select a known manifest item and read the upstream license and eligibility conditions. RFMix academic-use terms remain explicit; a checkbox is a user declaration, not a license grant. Research-only or unknown rights do not become unrestricted because installation is manual.

The page shows the exact cache filename, SHA-256 when pinned, planned runtime target and manual staging folder. After reviewing the upstream terms, choose **Download to cache** or **Download for manual review**. The app uses the registered HTTPS URL and checks the pinned SHA-256 before placing a download in the cache. An item without a pinned SHA-256 goes to `DNA_Software/ManualAssets/<asset-id>/`.

If you already have the file, choose **Copy** or **Move**, then **Verify and stage file**. Downloads and local imports preserve any different bytes already at the destination. Staging does not execute anything or mark a component as installed. Installation is a separate action using a reviewed adapter, if available. Preserve upstream license and notice files.

The GUI, CLI, JSON and MCP use the same commands and validation. The commands are `assets.catalog`, `assets.plan`, `assets.download` and `assets.import`.
