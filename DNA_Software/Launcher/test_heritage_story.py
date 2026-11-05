import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
import heritage_story as story


class HeritageStoryTests(unittest.TestCase):
    def setUp(self):
        p = patch("story_art.slots", return_value={"slots": []})
        p.start()
        self.addCleanup(p.stop)

    def test_group_small_components_without_overlapping_totals(self):
        row = {
            "data": {
                "regions": [
                    {"name": "Large", "percent": 98},
                    {"name": "Small", "percent": 1.5},
                    {"name": "Tiny", "percent": 0.5},
                ]
            }
        }
        major, minor = story.groups(row)
        self.assertEqual(len(major), 1)
        self.assertEqual(sum(r["percent"] for r in minor), 2)

    def test_offline_html_escapes_profile_and_preserves_unknowns(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(story, "ancestry", return_value=None),
            patch("workflows.inheritance_latest", return_value=None),
        ):
            story.create(
                "P",
                {"name": "<script>bad</script>", "residence": "Somewhere"},
                {},
                Path(tmp),
                "en",
            )
            s = (Path(tmp) / "Heritage_Story.html").read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;", s)
            self.assertIn("Still in progress", s)
            self.assertNotIn("<script src=", s)
            self.assertIn("window.print()", s)
            self.assertIn("prefers-reduced-motion", s)

    def test_small_components_are_grouped_and_source_version_preserved(self):
        row = {
            "person": "P",
            "data": {
                "regions": [
                    {"name": "Unknown region", "percent": 99},
                    {"name": "Small region", "percent": 1},
                ],
                "provider": "Synthetic",
                "model": "Example",
                "version": "test-v1",
            },
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(story, "ancestry", return_value=row),
            patch("workflows.inheritance_latest", return_value=None),
        ):
            r = story.create("P", {"name": "Synthetic"}, {}, Path(tmp), "en")
            s = (Path(tmp) / "Heritage_Story.html").read_text(encoding="utf-8")
            self.assertIn("Additional ancestry components", s)
            self.assertIn("test-v1", s)
            self.assertEqual(len(r["minor"]), 1)


if __name__ == "__main__":
    unittest.main()
