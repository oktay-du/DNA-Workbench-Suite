# Portable workspace

App-owned profiles, projects, caches and optional modules live beneath the executable folder. Keep that folder writable and preserve its relative layout when moving drives.

Windows x64 needs .NET Framework, WebView2 and, for Linux programs, WSL. Setup may require administrator access and a restart. WSL registration is computer-specific even when its virtual disk is on the SSD. Linux x64 uses the host Python, GTK 3 and WebKitGTK, and runs the pinned Linux programs directly. Windows-only installers are not launched through Wine.

Version 0.18 migrates legacy generated paths to English names before startup. Existing source evidence is retained. Conflicting destinations stop the migration rather than replacing files. Database path updates create a backup before changing registered paths.

Profile exports are the supported transfer and backup format. Credentials protected for one account must be entered again on another computer.
