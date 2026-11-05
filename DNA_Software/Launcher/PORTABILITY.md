# Portable workspace

App-owned profiles, projects, caches and optional modules live beneath the executable folder. Keep that folder writable and preserve its relative layout when moving drives.

Windows x64, .NET Framework, WebView2 host support and WSL virtualisation remain host requirements. Setup may require administrator access and a restart. WSL registration is computer-specific even when its virtual disk is on the SSD.

Version 0.18 migrates legacy generated paths to English names before startup. Existing source evidence is retained. Conflicting destinations stop the migration rather than replacing files. Database path updates create a backup before changing registered paths.

Profile exports are the supported transfer and backup format. Credentials protected for one Windows account must be entered again on another computer.
