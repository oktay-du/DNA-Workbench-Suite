import json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import family, visual_tools as vis


class VisualToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.p = self.root / "demo.vcf"
        self.p.write_text(
            "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t10\trs1\tA\tG\t42\tPASS\t.\n1\t20\trs2\tA\tC\t.\t.\t.\n2\t10\t.\tA\tG\t20\tPASS\t.\n"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_regions_not_full_dataset(self):
        rows, stats = vis.records(self.p, "chr1", 15, 30)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["quality"])
        self.assertFalse(stats["limited"])

    def test_plot_limits_visible(self):
        rows, stats = vis.records(self.p, "1", 1, 30, 1)
        self.assertTrue(stats["limited"])
        self.assertEqual(len(rows), 1)

    def test_bed_zero_based_to_one_based(self):
        p = self.root / "x.bed"
        p.write_text("1\t0\t10\tfeature\n")
        rows, _ = vis.records(p, "1", 1, 10)
        self.assertEqual((rows[0]["pos"], rows[0]["end"]), (1, 11))

    def test_raw_chip_rejected(self):
        with self.assertRaises(ValueError):
            vis.records(self.root / "chip.txt", "1", 1, 100)

    def test_discovery_cannot_install_code(self):
        with self.assertRaises(ValueError):
            vis.install("discovery-random")

    def test_archive_traversal_rejected(self):
        for name in ["../x", "C:/x", "/root/x", "a\\b"]:
            with self.assertRaises(ValueError):
                vis.safe_member(name)

    def test_igv_config_format_explicit_and_index_required(self):
        self.assertEqual(
            vis.track_config("a.vcf", {"input": "/file/input"})["format"], "vcf"
        )
        with self.assertRaises(ValueError):
            vis.track_config("a.bam", {"input": "/file/input"})

    def test_local_reference_index_required(self):
        p = self.root / "a.fa"
        p.write_text(">1\nAAAA\n")
        with self.assertRaises(ValueError):
            vis.reference_files(p)

    def test_private_files_range_head_and_traversal(self):
        job = "a" * 32
        folder = self.root / job
        folder.mkdir()
        source = self.root / "source.bin"
        source.write_bytes(b"0123456789")
        (folder / "manifest.json").write_text(
            json.dumps(
                {
                    "files": {"input": str(source)},
                    "source_size": 10,
                    "source_mtime_ns": source.stat().st_mtime_ns,
                }
            )
        )
        with patch.object(vis, "RUNS", self.root):
            server = ThreadingHTTPServer(("127.0.0.1", 0), family.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = (
                "http://127.0.0.1:"
                + str(server.server_port)
                + "/visual-run/"
                + job
                + "/file/input"
            )
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(url, headers={"Range": "bytes=2-5"})
                ) as r:
                    self.assertEqual(r.status, 206)
                    self.assertEqual(r.read(), b"2345")
                    self.assertEqual(r.headers["Content-Range"], "bytes 2-5/10")
                with urllib.request.urlopen(
                    urllib.request.Request(url, method="HEAD")
                ) as r:
                    self.assertEqual(r.headers["Content-Length"], "10")
                    self.assertEqual(r.read(), b"")
                for suffix in ["../manifest.json", "/arbitrary"]:
                    with self.assertRaises(urllib.error.HTTPError):
                        urllib.request.urlopen(url + suffix)
                source.write_bytes(b"changed")
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(url)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
