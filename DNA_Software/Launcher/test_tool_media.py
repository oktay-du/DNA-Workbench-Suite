import unittest, tempfile, contextlib, io
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import tool_media as m


class MediaTests(unittest.TestCase):
    def test_catalog_records_are_not_install_recipes(self):
        with patch(
            "plugin_hub.listing",
            return_value={
                "projects": [
                    {"id": "jbrowse", "task": "", "installable": True, "visual": True}
                ]
            },
        ):
            r = m.catalog()
        self.assertGreater(len(r["tools"]), 100)
        self.assertEqual(r["errors"], [])
        self.assertTrue(
            next(x for x in r["tools"] if x["id"] == "jbrowse")["adapter"][
                "installable"
            ]
        )
        self.assertFalse(next(x for x in r["tools"] if x["id"] == "circos")["adapter"])
        self.assertFalse(any("command" in x for x in r["tools"]))

    def test_bounded_validated_cache_and_provenance(self):
        b = io.BytesIO()
        Image.new("RGB", (160, 150)).save(b, "PNG")
        raw = b.getvalue()
        row = {
            "id": {
                "images": [
                    {
                        "url": "https://raw.githubusercontent.com/official/tool/commit/test.png",
                        "publisher_page": "https://example.org",
                    }
                ]
            }
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(m, "CACHE", Path(tmp)),
            patch.object(m, "media_index", return_value=row),
            patch.object(
                m.network_io,
                "open_https",
                return_value=contextlib.closing(io.BytesIO(raw)),
            ) as net,
        ):
            r = m.picture("id")
            self.assertTrue(r["available"])
            self.assertIn("data:image/png", r["image"])
            self.assertEqual(r["publisher_page"], "https://example.org")
            m.picture("id")
            self.assertEqual(net.call_count, 1)

    def test_unknown_and_bad_source_never_download(self):
        with (
            patch.object(m, "media_index", return_value={}),
            patch.object(m.network_io, "open_https", side_effect=AssertionError),
        ):
            self.assertFalse(m.picture("unknown")["available"])
        with patch.object(
            m,
            "media_index",
            return_value={"id": {"images": [{"url": "http://localhost/secret"}]}},
        ):
            with self.assertRaises(ValueError):
                m.picture("id")


if __name__ == "__main__":
    unittest.main()
