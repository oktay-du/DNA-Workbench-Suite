import unittest, tempfile, contextlib, base64, io, json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import source_store, family, suite_api, story_art, profile_files, profile_transfer


class StoryArtTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        for m in (source_store, family, suite_api, profile_transfer):
            self.stack.enter_context(patch.object(m, "ROOT", self.root))
        self.stack.enter_context(
            patch.object(family, "DB", self.root / "family.sqlite")
        )
        with family.connect() as db:
            db.execute(
                "INSERT INTO people VALUES(?,?,0)", ("P1", "Private Profile Name")
            )
        f = io.BytesIO()
        Image.new("RGB", (160, 160), (85, 120, 130)).save(f, format="PNG")
        self.raw = f.getvalue()
        self.url = "data:image/png;base64," + base64.b64encode(self.raw).decode()

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def test_slots_cover_all_catalog_places_and_never_include_private_name_in_prompt(
        self,
    ):
        r = story_art.slots("P1")
        self.assertGreater(len([x for x in r["slots"] if x["kind"] == "country"]), 200)
        self.assertEqual(
            next(x for x in r["slots"] if x["id"] == "farmer")["status"], "bundled"
        )
        self.assertNotIn(
            "Private Profile Name", json.dumps([x["prompt"] for x in r["slots"]])
        )

    def test_upload_registered_as_art_not_clinical_and_reused_without_copy(self):
        a = story_art.upload("P1", "maternal", data_url=self.url)
        b = story_art.upload("P1", "paternal", data_url=self.url)
        self.assertEqual(a["document"], b["document"])
        self.assertEqual(len(list((self.root / "Profiles/P1/Artwork").glob("*"))), 1)
        self.assertEqual(story_art.selected("P1", "maternal")["status"], "custom")
        self.assertTrue(
            any(
                x["kind"] == "design_art"
                for x in profile_files.inventory("P1")["entries"]
            )
        )

    def test_slot_image_follows_manager_rename_and_delete_restore(self):
        a = story_art.upload("P1", "maternal", data_url=self.url)
        id = "document:" + a["document"]
        plan = profile_files.preview("P1", "rename", [id], name="renamed.png")
        profile_files.apply("P1", plan["token"], log=lambda _: None)
        self.assertTrue(
            story_art.selected("P1", "maternal")["custom"]["path"].endswith(
                "renamed.png"
            )
        )
        p = profile_files.preview("P1", "delete", [id])
        deleted = profile_files.apply("P1", p["token"], log=lambda _: None)
        self.assertEqual(story_art.selected("P1", "maternal")["status"], "missing")
        profile_files.restore("P1", deleted["operation"])
        self.assertEqual(story_art.selected("P1", "maternal")["status"], "custom")

    def test_prompt_draft_survives_and_editing_keeps_attached_image(self):
        story_art.save_prompt("P1", "maternal", "Custom generic landscape prompt")
        self.assertEqual(
            story_art.selected("P1", "maternal")["prompt"],
            "Custom generic landscape prompt",
        )
        r = story_art.upload("P1", "maternal", data_url=self.url)
        story_art.save_prompt("P1", "maternal", "New generic landscape prompt")
        slot = story_art.selected("P1", "maternal")
        self.assertEqual(slot["custom"]["document"], r["document"])
        self.assertEqual(slot["prompt"], "New generic landscape prompt")

    def test_invalid_image_and_unknown_slot_rejected(self):
        for kwargs in [
            {"slot": "../bad", "data_url": self.url},
            {"slot": "maternal", "data_url": "data:image/svg+xml;base64,PHN2Zz4="},
            {"slot": "maternal", "data_url": "data:image/png;base64,YmFk"},
        ]:
            with self.assertRaises(Exception):
                story_art.upload("P1", **kwargs)

    def test_modified_artwork_not_silently_accepted(self):
        story_art.upload("P1", "maternal", data_url=self.url)
        r = story_art.selected("P1", "maternal")
        Path(r["custom"]["path"]).write_bytes(b"changed")
        self.assertEqual(story_art.selected("P1", "maternal")["status"], "missing")

    def test_artwork_slot_in_profile_backup(self):
        story_art.upload("P1", "maternal", data_url=self.url)
        profile_transfer.export_profile("P1", log=lambda _: None)
        self.assertIn("artwork_slots", profile_transfer.TABLES)

    def test_story_preview_interactive_only_for_owned_story_task(self):
        p = self.root / "Projects/Launcher/P1/job/Results"
        p.mkdir(parents=True)
        (p / "Heritage_Story.html").write_text("<button>Print</button>")
        (p.parent / "inputs.json").write_text(json.dumps({"task": "storybook"}))
        r = suite_api.dispatch(
            "result-preview",
            {"person": "P1", "job": "job", "file": "Heritage_Story.html"},
        )
        self.assertTrue(r["interactive_story"])
        (p.parent / "inputs.json").write_text(json.dumps({"task": "other"}))
        self.assertFalse(
            suite_api.dispatch(
                "result-preview",
                {"person": "P1", "job": "job", "file": "Heritage_Story.html"},
            )["interactive_story"]
        )

    def test_natural_earth_outlines_and_peru_identity(self):
        a = story_art.atlas()
        self.assertTrue(
            next(x for x in a["countries"] if x["id"] == "pe")["outline_available"]
        )
        self.assertEqual(
            story_art.region_key("Peru"),
            story_art.region_key("Peru · synthetic illustration"),
        )
        self.assertIn("#b76b31", story_art.map_svg("pe"))

    def test_country_without_art_does_not_display_shared_world_scene(self):
        markup = story_art.full_scene(
            {"status": "missing", "default": {"placeholder": True}},
            "Japan",
            "35%",
            "Synthetic example",
            "--world",
            story_art.map_svg("jp"),
        )
        self.assertNotIn("var(--world)", markup)
        self.assertIn("Country artwork not available", markup)
        self.assertIn("<svg", markup)


if __name__ == "__main__":
    unittest.main()
