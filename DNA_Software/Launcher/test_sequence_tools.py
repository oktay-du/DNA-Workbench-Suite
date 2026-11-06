import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import sequence_tools as seq


class SequenceToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.out = self.root / "out"
        self.out.mkdir()
        self.a = self.root / "a.fa"
        self.b = self.root / "b.fa"
        self.a.write_text(
            ">same original description\nACGTNN\n>same second record\nTTAA\n"
        )
        self.b.write_text(">another name\nacgtnn\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_concat_renames_colliding_headers_and_keeps_provenance(self):
        before = self.a.read_bytes()
        seq.merge("p", {"files": [str(self.a), str(self.b)]}, self.out, lambda _: None)
        text = (self.out / "sequence-collection.fasta").read_text()
        self.assertEqual(text.count(">"), 3)
        self.assertIn("s001_r0000001", text)
        self.assertIn("s002_r0000001", text)
        data = json.loads((self.out / "merge-manifest.json").read_text())
        self.assertTrue(data["not_for_best_selection"])
        self.assertEqual(data["records_kept"], 3)
        self.assertEqual(self.a.read_bytes(), before)
        self.assertIn(
            "same original description", (self.out / "record-sources.tsv").read_text()
        )

    def test_dedupe_uses_sequence_not_shared_header(self):
        seq.merge(
            "p",
            {"files": [str(self.a), str(self.b)], "deduplicate": "Ja"},
            self.out,
            lambda _: None,
        )
        data = json.loads((self.out / "merge-manifest.json").read_text())
        self.assertEqual(data["records_kept"], 2)
        self.assertEqual(data["identical_sequence_records_removed"], 1)

    def test_invalid_fasta_never_produces_final_collection(self):
        self.a.write_text(">bad\nACGT$\n")
        with self.assertRaises(ValueError):
            seq.merge("p", {"files": [str(self.a)]}, self.out, lambda _: None)
        self.assertFalse((self.out / "sequence-collection.fasta").exists())

    def test_cancellation_preserves_sources(self):
        before = self.a.read_bytes()
        with self.assertRaises(InterruptedError):
            seq.merge(
                "p", {"files": [str(self.a)]}, self.out, lambda _: None, lambda: True
            )
        self.assertEqual(self.a.read_bytes(), before)
        self.assertFalse((self.out / "sequence-collection.fasta").exists())

    def test_stats_distinguish_ambiguity_from_gc(self):
        seq.stats("p", {"files": [str(self.a)]}, self.out, lambda _: None)
        r = json.loads((self.out / "sequence-statistics.json").read_text())["files"][0]
        self.assertEqual(r["bases_scanned"], 10)
        self.assertEqual(r["N_bases"], 2)
        self.assertEqual(r["gc_percent_of_ACGTU"], 25)
        self.assertTrue(r["complete_file_scanned"])

    def test_unwrapped_long_fasta_is_processed_in_bounded_chunks(self):
        self.a.write_text(">long\n" + "ACGT" * 600000 + "\n")
        chunks = [
            len(value) for kind, value in seq.fasta_events(self.a) if kind == "sequence"
        ]
        self.assertEqual(sum(chunks), 2400000)
        self.assertLessEqual(max(chunks), 1024 * 1024)

    @unittest.skipUnless(importlib.util.find_spec("Bio"), "Optional Biopython package")
    def test_fastq_sampling_does_not_claim_full_file(self):
        p = self.root / "reads.fq"
        p.write_text("@one\nACGT\n+\nIIII\n@two\nAAAA\n+\n!!!!\n")
        seq.stats("p", {"files": [str(p)], "read_limit": "1"}, self.out, lambda _: None)
        r = json.loads((self.out / "sequence-statistics.json").read_text())["files"][0]
        self.assertTrue(r["sampled_only"])
        self.assertFalse(r["complete_file_scanned"])
        self.assertEqual(r["Q30_base_calls_in_sample"], 4)

    @unittest.skipUnless(
        importlib.util.find_spec("pyfastx"), "Optional pyfastx package"
    )
    def test_extract_index_is_not_written_next_to_source(self):
        source = self.root / "unique.fa"
        source.write_text(">chr1\nACGTACGT\n")
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        seq.extract(
            "p",
            {"file": str(source), "record": "chr1", "start": "2", "end": "5"},
            self.out,
            lambda _: None,
        )
        self.assertIn("CGTA", (self.out / "extracted.fasta").read_text())
        self.assertTrue((self.out / "source.fxi").exists())
        self.assertFalse(Path(str(source) + ".fxi").exists())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    @unittest.skipUnless(
        importlib.util.find_spec("pyfastx"), "Optional pyfastx package"
    )
    def test_missing_seqviz_writes_a_local_view(self):
        source = self.root / "unique.fa"
        source.write_text(">chr1\nACGTACGT\n")
        with patch("visual_tools.installed", return_value=False):
            seq.view(
                "p",
                {"file": str(source), "record": "chr1", "start": "1", "end": "4"},
                self.out,
                lambda _: None,
            )
        page = (self.out / "sequence-view.html").read_text()
        self.assertIn("ACGT", page)
        self.assertIn("SeqViz bundle is not installed", page)

    @unittest.skipUnless(
        importlib.util.find_spec("pyfastx"), "Optional pyfastx package"
    )
    def test_out_of_range_extract_is_rejected(self):
        source = self.root / "unique.fa"
        source.write_text(">chr1\nACGTACGT\n")
        with self.assertRaises(ValueError):
            seq.extract(
                "p",
                {"file": str(source), "start": "1", "end": "99"},
                self.out,
                lambda _: None,
            )

    @unittest.skipUnless(
        importlib.util.find_spec("Bio") and importlib.util.find_spec("pyfastx"),
        "Optional sequence packages",
    )
    def test_translation_reports_incomplete_codon(self):
        source = self.root / "unique.fa"
        source.write_text(">gene\nATGAAATA\n")
        seq.transform(
            "p",
            {
                "file": str(source),
                "start": "1",
                "end": "8",
                "operation": "Translate frame 1",
            },
            self.out,
            lambda _: None,
        )
        self.assertIn("MK", (self.out / "transformed.fasta").read_text())
        self.assertEqual(
            json.loads((self.out / "transform-manifest.json").read_text())[
                "trailing_bases_not_translated"
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
