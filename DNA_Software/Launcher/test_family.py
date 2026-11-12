import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import family


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.dbpatch = patch.object(family, "DB", self.path / "family.sqlite")
        self.rootpatch = patch.object(family, "ROOT", self.path)
        self.dbpatch.start()
        self.rootpatch.start()
        with family.connect() as db:
            db.executemany(
                "INSERT INTO people VALUES(?,?,0)",
                [(x, x) for x in ["a", "b", "c", "d"]],
            )

    def tearDown(self):
        self.dbpatch.stop()
        self.rootpatch.stop()
        self.temp.cleanup()

    def test_cycle_blocked(self):
        family.add_link("a", "b", "mother")
        family.add_link("b", "c", "mother")
        with self.assertRaises(ValueError):
            family.add_link("c", "a", "father")

    def test_lineage(self):
        family.add_link("a", "b", "mother")
        family.add_link("b", "c", "mother")
        self.assertEqual(family.lineage("c", "mother"), ["c", "b", "a"])

    def test_partners_not_ancestry(self):
        family.add_link("a", "b", "partner")
        self.assertEqual(family.lineage("b", "mother"), ["b"])

    def test_duplicate_parent_role_blocked(self):
        family.add_link("a", "c", "mother")
        with self.assertRaises(ValueError):
            family.add_link("b", "c", "mother")

    def test_distribution(self):
        self.assertEqual(
            family.distribution(["A", "G"], ["A", "G"]),
            {"A/A": 0.25, "A/G": 0.5, "G/G": 0.25},
        )

    def test_paternal_cousin_explicit_path(self):
        r = family.add_route(
            {
                "anchor": "a",
                "target": "d",
                "relation": "cousin",
                "side": "father",
                "parent": "b",
                "bridge": "c",
                "sibling_role": "brother",
            }
        )
        self.assertEqual(r["path"], ["a", "b", "c", "d"])
        with family.connect() as db:
            links = [tuple(x) for x in db.execute("SELECT a,b,kind FROM links")]
        self.assertIn(("b", "a", "father"), links)
        self.assertIn(("c", "b", "brother"), links)
        self.assertIn(("c", "d", "father"), links)
        self.assertEqual(family.lineage("a", "father"), ["a", "b"])

    def test_route_rollback(self):
        family.add_link("d", "c", "father")
        with self.assertRaises(ValueError):
            family.add_route(
                {
                    "anchor": "a",
                    "target": "d",
                    "relation": "cousin",
                    "side": "father",
                    "parent": "b",
                    "bridge": "c",
                }
            )
        with family.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM links").fetchone()[0], 1)

    def test_empty_profile_binding(self):
        pid = family.placeholder("Unbekannter Onkel")
        family.bind_profile(pid, "a")
        with family.connect() as db:
            self.assertEqual(
                db.execute(
                    "SELECT source_person FROM bindings WHERE person=?", (pid,)
                ).fetchone()[0],
                "a",
            )

    def test_missing_no_prediction(self):
        with patch.object(family, "locus", return_value={"status": "unbekannt"}):
            self.assertNotIn(
                "child_genotypes",
                family.calculate(
                    {"a": "a", "b": "b", "chrom": "1", "build": "GRCh38", "pos": "123"}
                ),
            )

    def test_sex_chromosomes_not_autosomal_model(self):
        with self.assertRaises(ValueError):
            family.calculate({"chrom": "X", "build": "GRCh38"})

    def test_local_http_and_token(self):
        import threading, urllib.request, urllib.error, json

        server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        server.token = "synthetic-test-token"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = "http://127.0.0.1:" + str(server.server_port)
            with urllib.request.urlopen(url) as r:
                self.assertIn(b"synthetic-test-token", r.read())
            req = urllib.request.Request(
                url + "/lines",
                data=b'{"person":"c"}',
                headers={
                    "X-DNA-Token": server.token,
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req) as r:
                self.assertEqual(json.load(r)["maternal"], ["c"])
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(
                    urllib.request.Request(url + "/lines", data=b"{}")
                )
        finally:
            server.shutdown()
            server.server_close()

    def test_quality_report_is_served_inside_the_workspace(self):
        import threading, urllib.request, urllib.error

        folder = self.path / "Projects/Launcher/P1/job_fastp/Results"
        folder.mkdir(parents=True)
        page = "<!doctype html><title>MultiQC</title><h1>Whole report</h1>"
        (folder / "multiqc_report.html").write_text(page, encoding="utf-8")
        (folder / "secret.txt").write_text("private", encoding="utf-8")
        server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        server.token = "synthetic-test-token"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = "http://127.0.0.1:" + str(server.server_port)
            with urllib.request.urlopen(
                url + "/quality-report/P1/job_fastp/multiqc_report.html"
            ) as response:
                body = response.read().decode()
                self.assertIn("Whole report", body)
                self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
            with self.assertRaises(urllib.error.HTTPError) as missing:
                urllib.request.urlopen(url + "/quality-report/P1/job_fastp/secret.txt")
            self.assertEqual(missing.exception.code, 404)
            with self.assertRaises(urllib.error.HTTPError) as escaped:
                urllib.request.urlopen(
                    url + "/quality-report/P1/job_fastp/../../secret.txt"
                )
            self.assertEqual(escaped.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()

    def test_foreign_host_rejected(self):
        import threading, urllib.request, urllib.error

        server = family.ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
        server.token = "test"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:" + str(server.server_port) + "/",
                headers={"Host": "foreign.example"},
            )
            with self.assertRaises(urllib.error.HTTPError) as result:
                urllib.request.urlopen(req)
            self.assertEqual(result.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
