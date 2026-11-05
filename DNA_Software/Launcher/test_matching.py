import json, tempfile, unittest, threading, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
import family, matching, genealogy_research as ged


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patches = [
            patch.object(family, "DB", self.root / "family.sqlite"),
            patch.object(family, "ROOT", self.root),
            patch.object(matching, "signature", side_effect=lambda p: "source-" + p),
        ]
        for p in self.patches:
            p.start()
        with family.connect() as db:
            db.executemany("INSERT INTO people VALUES(?,?,0)", [(p, p) for p in "abcd"])

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def load(self, text=None):
        return matching.import_segments(
            {
                "build": "GRCh38",
                "source": "Synthetic phased fixture",
                "text": text
                or "a,b,chrom,start,end,cm,hap1,hap2\na,b,1,100,300,10,1,1\na,c,1,150,350,11,1,1\nb,c,1,175,275,8,1,1",
            }
        )

    def test_import_build_shared_and_phase(self):
        self.assertEqual(self.load()["segments"], 3)
        items = matching.segments()
        self.assertEqual(matching.shared_matches("a", "b", items), ["c"])
        self.assertTrue(
            matching.triangulation("a", items)["candidates"][0]["phase_consistent"]
        )
        self.assertEqual(matching.segments("GRCh37"), [])
        self.assertEqual(matching.graph_clusters(items)["groups"][0]["edges"], 3)

    def test_duplicates_rejected(self):
        self.load()
        with self.assertRaises(ValueError):
            self.load()

    def test_stale_sources_excluded(self):
        self.load()
        with patch.object(matching, "signature", return_value="changed"):
            self.assertEqual(matching.segments(), [])

    def test_invalid_pair_and_coordinates_atomic(self):
        with self.assertRaises(ValueError):
            self.load("a,b,chrom,start,end,cm\na,a,1,100,300,9")
        with self.assertRaises(ValueError):
            self.load("a,b,chrom,start,end,cm\na,b,1,300,100,9")
        self.assertEqual(matching.segments(), [])

    def test_overlap_not_double_counted_and_fir(self):
        self.load(
            "a,b,chrom,start,end,cm,hap1,hap2\na,b,1,100,300,10,1,1\na,b,1,150,350,12,2,2"
        )
        rows = matching.segments()
        self.assertIsNone(matching.pair_summary(rows)["total_cm"])
        self.assertEqual(len(matching.fir_candidates(rows)), 1)

    def test_incomplete_phase_not_confirmed(self):
        self.load(
            "a,b,chrom,start,end,cm\na,b,1,100,300,10\na,c,1,150,350,11\nb,c,1,175,275,8"
        )
        self.assertFalse(
            matching.triangulation("a", matching.segments())["candidates"][0][
                "phase_consistent"
            ]
        )

    def test_trio_distinct(self):
        with self.assertRaises(ValueError):
            matching.untransmitted({"a": "a", "b": "b", "child": "a"})

    def test_gedcom_export_import_and_mrca(self):
        family.add_link("a", "b", "father")
        family.add_link("a", "c", "father")
        result = ged.mrca({"a": "b", "b": "c"})
        self.assertEqual(result["common_ancestors"][0]["id"], "a")
        result = ged.import_file(
            {"text": ged.mini_export()["text"], "label": "Synthetic family"}
        )
        self.assertEqual(result["people"], 4)
        self.assertEqual(result["relationships"], 2)
        with self.assertRaises(ValueError):
            ged.parse(
                "0 HEAD\n0 @I1@ INDI\n0 @F@ FAM\n1 HUSB @I1@\n1 CHIL @I1@\n0 TRLR"
            )

    def test_http_token_assets_and_feature_registry(self):
        server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        server.token = "test-token"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = "http://127.0.0.1:" + str(server.server_port)
        try:
            html = urllib.request.urlopen(url + "/research").read().decode()
            self.assertRegex(html, r'DNA_RESEARCH_TOKEN\s*=\s*"test-token"')
            self.assertIn(
                b"function show", urllib.request.urlopen(url + "/matching.js").read()
            )
            req = urllib.request.Request(
                url + "/research/gedcom-index",
                data=b"{}",
                headers={"X-DNA-Token": "test-token"},
            )
            self.assertEqual(json.load(urllib.request.urlopen(req))["people"], [])
            req = urllib.request.Request(url + "/research/analysis", data=b"{}")
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(req)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
