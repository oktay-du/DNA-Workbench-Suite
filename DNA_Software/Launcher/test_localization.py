"""English-source and migration contracts use synthetic files only."""

from pathlib import Path
import json, sqlite3, tempfile, unittest
import localization, layout_migration, portable_paths, portable_json


class LocalizationTests(unittest.TestCase):
    def test_english_is_the_default_source_language(self):
        self.assertEqual(localization.text("Settings"), "Settings")
        self.assertEqual(localization.text("Settings", "de"), "Einstellungen")
        app = Path(__file__).parent
        self.assertFalse((app / "ui-strings.json").exists())
        catalog = json.loads((app / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["categories"][0], "All steps")
        self.assertTrue(all("ä" not in x["title"] for x in catalog["tasks"]))

    def test_interface_languages_have_local_dictionaries_and_flags(self):
        languages = localization.languages()
        self.assertEqual(len(languages), 36)
        self.assertEqual(
            {code for code, row in languages.items() if row.get("dir") == "rtl"},
            {"ar", "fa", "ur"},
        )
        assets = localization.ui_assets()
        for code, row in languages.items():
            with self.subTest(language=code):
                flag = assets[f"/Locales/flags/{row['flag']}.svg"]
                self.assertTrue(flag.read_bytes().startswith(b"<svg"))
                if code != "en":
                    dictionary = localization.dictionary(code)
                    self.assertIn("Language", dictionary)
                    self.assertNotEqual(dictionary["Language"], "Language")
                    self.assertGreaterEqual(len(dictionary), 3000)
        self.assertEqual(localization.dictionary("../project_info"), {})

    def test_legacy_paths_are_rebased_only_inside_the_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / "DNA_Projekte/Launcher/Example/Job/Ergebnisse/result.txt"
            self.assertEqual(
                Path(portable_paths.rebase(str(old), root, [])),
                root / "Projects/Launcher/Example/Job/Results/result.txt",
            )
            outside = str(root.parent / "External/Ergebnisse/result.txt")
            self.assertEqual(layout_migration.path(outside, root), outside)

    def test_database_paths_are_migrated_with_a_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / "family.sqlite"
            with sqlite3.connect(file) as db:
                db.execute("CREATE TABLE docs(path TEXT,name TEXT)")
                db.execute(
                    "INSERT INTO docs VALUES(?,?)",
                    (
                        str(root / "DNA_Projekte/Launcher/P1/Ergebnisse/file.pdf"),
                        "Original person name",
                    ),
                )
                db.commit()
                layout_migration.database(db, root)
                path, name = db.execute("SELECT * FROM docs").fetchone()
                self.assertEqual(
                    Path(path), root / "Projects/Launcher/P1/Results/file.pdf"
                )
                self.assertEqual(name, "Original person name")
            db.close()
            self.assertTrue(
                file.with_name("family.sqlite.before-english-migration.bak").is_file()
            )

    def test_legacy_status_mapping_does_not_translate_report_text(self):
        raw = json.dumps({"status": "Abgeschlossen", "note": "Abgeschlossen"})
        result = portable_json.loads(raw)
        self.assertEqual(result["status"], "Complete")
        self.assertEqual(result["note"], "Abgeschlossen")

    def test_legacy_choices_preserve_free_text_and_sources(self):
        result = portable_json.loads(
            json.dumps(
                {
                    "measurement": "Unbekannt / gemischt",
                    "export_kind": "Automatisch erkennen",
                    "compression_mode": "Manuell",
                    "note": "Manuell",
                    "original_name": "Automatisch erkennen.txt",
                }
            )
        )
        self.assertEqual(result["measurement"], "Unknown / mixed")
        self.assertEqual(result["export_kind"], "Detect automatically")
        self.assertEqual(result["compression_mode"], "Manual")
        self.assertEqual(result["note"], "Manuell")
        self.assertEqual(result["original_name"], "Automatisch erkennen.txt")

    def test_plugin_metadata_and_tool_choices_are_english(self):
        import re, plugin_hub

        app = Path(__file__).parent
        german = re.compile(
            r"\b(?:Deklarative|getrennte|Vorhandener|Optionaler|Lokaler|erstellen|auswerten|erneuern|starten|Automatisch|Manuell|Unbekannt|Lizenzgebundener|Recherche|Spezialanalysen|angebunden|Variantenanalyse|Optionales|Genom-KI|Entwicklerbibliothek|Transkriptomik|Medizinischer|Dateninfrastruktur|Phylogenetik)\b"
        )
        for item in plugin_hub.audit()["projects"]:
            for key in ("analysis", "decision", "category"):
                self.assertIsNone(german.search(item.get(key, "")), (item["id"], key))
        catalog = json.loads((app / "catalog.json").read_text(encoding="utf-8"))
        for task in catalog["tasks"]:
            values = [task["title"], task["description"], task["tools"], task["button"]]
            values += [
                str(field.get(key, ""))
                for field in task["fields"]
                for key in ("label", "choices", "default")
            ]
            for value in values:
                self.assertIsNone(german.search(value), (task["id"], value))
        self.assertIn(
            "Local genomics workspace",
            (app / "Launcher.cs").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
