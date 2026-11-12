# DNA Workbench Suite

**Version 1.0.6 · Windows und Linux mit x64 und ARM64 · Lokale Genomforschung**

Eine Anwendung für Windows und Linux: DNA-Quelldateien, Familienprofile, Forschungswerkzeuge und wiederverwendbare Ergebnisse. Die Oberfläche bietet 36 Sprachen offline sowie ein helles und ein dunkles Design.

[Download](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest) · [Englische Dokumentation](README.md) · [Website](https://oktay-du.github.io/DNA-Workbench-Suite/)

![App-Vorschau mit Designwechsel, Sprachauswahl und synthetischen Beispieldateien](docs/images/workspace-demo.gif)

[Alle Sprachen und App-Tour](https://oktay-du.github.io/DNA-Workbench-Suite/#languages) · [ARM64- und macOS-Vorschauen](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest)

## Anforderungen

| | Windows x64 | Linux x64 |
|---|---|---|
| Paket | [DNAWorkbench-Windows-x64.zip](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Windows-x64.zip) | [DNAWorkbench-Linux-x64.zip](https://github.com/oktay-du/DNA-Workbench-Suite/releases/latest/download/DNAWorkbench-Linux-x64.zip) |
| Start | `DNA_Launcher.exe` | `./DNA-Workbench.sh` |
| Desktop | .NET Framework 4.8 und WebView2 | Python 3.12, GTK 3 und WebKitGTK 4.1 |
| Linux-Programme | laufen in WSL | laufen direkt auf dem Host |

Nach dem Entpacken unter Windows `DNA_Launcher.exe` starten und Core einrichten. Unter Linux `./DNA-Workbench.sh` starten. Mit den künstlichen Beispieldaten beginnen. Optionale Module werden bei Bedarf installiert. WSL ist nur unter Windows nötig und kann Administratorrechte und einen Neustart brauchen. Für Gramps, JBrowse Desktop und UGENE gibt es getrennte Windows- und Linux-Pakete. Die Auswahl auf ARM64 hängt vom jeweiligen Werkzeug ab. [Welche Programme auf welchem System laufen](docs/VERSIONS.md).

Forschungssoftware, kein klinisches Diagnosesystem. Quelldaten und Ergebnisse bleiben standardmäßig lokal. Für optionale externe Dienste gelten eigene Datenschutzbedingungen.

Für die ausgewiesenen eigenen Beiträge gilt [PolyForm Noncommercial 1.0.0](DNA_Software/Launcher/Notices/POLYFORM-NONCOMMERCIAL-1.0.0.md).

[Datenschutz](docs/PRIVACY.md) · Kontakt: **oktaydu@proton.me**

Mit KI-Unterstützung erstellt. Freiwillige Unterstützung: [NOWPayments](https://nowpayments.io/donation/oktayd) · [Buy Me a Coffee](https://buymeacoffee.com/okioki).
