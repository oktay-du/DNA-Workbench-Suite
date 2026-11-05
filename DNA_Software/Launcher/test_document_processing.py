import unittest, tempfile, contextlib
from pathlib import Path
from unittest.mock import patch
import family, source_store, suite_api, profile_documents, document_processing, command_bus


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (family, source_store, suite_api):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.execute("INSERT INTO people VALUES(?,?,0)", ("TEST", "Synthetic"))
        p = self.root / "report.txt"
        p.write_text("Lactose intolerance was not reported.", encoding="utf-8")
        self.doc = profile_documents.index_file(
            "TEST", p, "Synthetic", "2026-11-04", log=lambda _: None
        )

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def test_outputs_keep_original_and_cited_machine_labels(self):
        with patch.object(
            document_processing,
            "translate",
            side_effect=lambda text, source, target: (
                "Translated to " + target + ": " + text
            ),
        ):
            r = document_processing.process(
                {"person": "TEST", "document": self.doc["id"], "source_language": "en"},
                log=lambda _: None,
            )
        self.assertEqual(
            [o["language"] for o in r["generated"]], ["original", "en", "de"]
        )
        hits = profile_documents.search("TEST", "lactose")
        self.assertTrue(
            any(h["review"] == "unreviewed_machine_translation" for h in hits)
        )
        self.assertTrue(
            all(
                "source_document" in h["processing_notes"]
                for h in hits
                if h["kind"].startswith("machine_translation")
            )
        )

    def test_modified_original_blocks_processing(self):
        row = profile_documents.listing("TEST")[0]
        Path(row["path"]).write_text("changed")
        with self.assertRaises(ValueError):
            document_processing.process(
                {"person": "TEST", "document": self.doc["id"], "source_language": "en"}
            )

    def test_other_profile_cannot_process_document(self):
        with family.connect() as db:
            db.execute("INSERT INTO people VALUES(?,?,0)", ("OTHER", "Other"))
        with self.assertRaises(ValueError):
            document_processing.process(
                {"person": "OTHER", "document": self.doc["id"], "source_language": "en"}
            )

    def test_cancellation_does_not_mark_as_success(self):
        with self.assertRaises(InterruptedError):
            document_processing.process(
                {"person": "TEST", "document": self.doc["id"], "source_language": "en"},
                cancel=lambda: True,
            )

    def test_arabic_medical_translation_is_blocked(self):
        with self.assertRaises(ValueError):
            document_processing.process(
                {
                    "person": "TEST",
                    "document": self.doc["id"],
                    "source_language": "ar",
                    "translate": True,
                }
            )

    def test_unsupported_language_not_guessed(self):
        with self.assertRaises(ValueError):
            document_processing.process(
                {
                    "person": "TEST",
                    "document": self.doc["id"],
                    "source_language": "unknown",
                }
            )

    def test_new_actions_are_agent_ready(self):
        ids = {d["id"] for d in command_bus.definitions()}
        self.assertTrue(
            {
                "profile.documents.process",
                "profile.results.publish",
                "result.lookup",
                "research.analysis-saved",
                "menu.findings",
            }
            <= ids
        )


if __name__ == "__main__":
    unittest.main()
