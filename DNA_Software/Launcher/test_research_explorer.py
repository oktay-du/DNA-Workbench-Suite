"""Synthetic contracts for local evidence, sequence and agent exports.

Copyright 2026 Oktay Du / OD. PolyForm Noncommercial 1.0.0.
"""

from pathlib import Path
import gzip
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

import command_bus
import research_explorer as explorer
import suite_api
import tool_contracts


class ResearchExplorerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, name):
        return json.loads((self.out / (name + ".json")).read_text(encoding="utf-8"))

    def vcf(self, rows, samples="Demo"):
        p = self.root / "synthetic.vcf"
        p.write_text(
            "##fileformat=VCFv4.5\n##reference=GRCh38\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
            + samples
            + "\n"
            + "\n".join(rows)
            + "\n",
            encoding="utf-8",
        )
        return p

    def test_audit_accounts_for_every_record_without_coercing_alleles(self):
        path = self.vcf(
            [
                "1\t1\t.\tA\tG\t.\tPASS\t.\tDP:GT\t15:0|1",
                "1\t2\t.\tA\tAT\t.\tPASS\t.\tGT\t0/1",
                "X\t3\t.\tA\tG\t.\t.\t.\tGT\t1",
                "1\t4\t.\tA\tG\t.\tLowQual\t.\tGT\t./1",
                "1\t5\t.\tA\tG\t.\tPASS\t.\tGT\t./.",
                "1\t6\t.\tA\tG\t.\tPASS\t.\tGT\t2/0",
                "1\t7\t.\tA\tG\t.\tPASS\t.\tDP\t10",
                "1\t8\t.\tA\tG\t.\tPASS\t.\tGT\t0/0/1",
                "bad\trow",
            ]
        )
        before = path.read_bytes()
        explorer.audit_vcf("Synthetic", {"vcf": str(path)}, self.out)
        r = self.read("variant-evidence-audit")
        self.assertEqual(r["rows"]["total"], 9)
        self.assertEqual(r["rows"]["pass_called_diploid_snv_records"], 1)
        self.assertEqual(sum(r["genotypes"].values()) + r["rows"]["malformed"], 9)
        self.assertEqual(r["genotypes"]["partial_no_call"], 1)
        self.assertEqual(r["ploidy"]["3"], 1)
        self.assertFalse(r["biologically_verified"])
        self.assertNotIn("0|1", json.dumps(r))
        self.assertEqual(before, path.read_bytes())

    def test_multisample_requires_explicit_selection(self):
        path = self.vcf(["1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t./.\t1/1"], "First\tSecond")
        with self.assertRaisesRegex(ValueError, "Select a sample explicitly"):
            explorer.audit_vcf("Synthetic", {"vcf": str(path)}, self.out)
        self.assertFalse((self.out / "variant-evidence-audit.json").exists())
        explorer.audit_vcf(
            "Synthetic", {"vcf": str(path), "sample": "Second"}, self.out
        )
        self.assertEqual(
            self.read("variant-evidence-audit")["genotypes"], {"called": 1}
        )

    def test_gzip_detected_from_content_and_report_escapes_sample(self):
        p = self.vcf(
            ["1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1"], "<script>alert(1)</script>"
        )
        p.write_bytes(gzip.compress(p.read_bytes()))
        explorer.audit_vcf("Synthetic", {"vcf": str(p)}, self.out)
        text = (self.out / "variant-evidence-audit.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>alert", text)
        self.assertIn("&lt;script&gt;", text)

    def test_truncated_compressed_input_never_yields_completed_receipt(self):
        p = self.vcf(["1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1"])
        p.write_bytes(gzip.compress(p.read_bytes())[:-6])
        with self.assertRaises((EOFError, OSError)):
            explorer.audit_vcf("Synthetic", {"vcf": str(p)}, self.out)
        self.assertFalse((self.out / "variant-evidence-audit.json").exists())

    def test_changed_input_and_cancellation_never_mark_verified(self):
        p = self.vcf(["1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1"])
        with patch.object(
            explorer.sequence_tools, "stable", side_effect=ValueError("changed")
        ):
            with self.assertRaisesRegex(ValueError, "changed"):
                explorer.audit_vcf("Synthetic", {"vcf": str(p)}, self.out)
        self.assertFalse((self.out / "variant-evidence-audit.json").exists())
        with self.assertRaises(InterruptedError):
            explorer.audit_vcf(
                "Synthetic", {"vcf": str(p)}, self.out, cancel=lambda: True
            )

    def test_gt_edge_cases_do_not_become_plausible_diploid_calls(self):
        for keys, value, total, expected in [
            (["GT"], "1/1", 1, "invalid_allele_index"),
            (["GT", "GT"], "0/1:1/1", 2, "malformed_gt"),
            (["GT"], "x/1", 2, "malformed_gt"),
            (["DP", "GT"], "15", 2, "malformed_gt"),
            (["GT"], ".", 2, "no_call"),
        ]:
            self.assertEqual(explorer.genotype_state(keys, value, total)[0], expected)

    def test_motif_overlaps_ambiguity_and_palindrome_deduplication(self):
        hits = explorer.motif_hits("AAAA", "AA")
        self.assertEqual([h["start"] for h in hits["hits"]], [1, 2, 3])
        self.assertEqual(explorer.motif_hits("N", "A")["counts"], {"possible": 2})
        self.assertEqual(
            explorer.motif_hits("ACGT", "ACGT")["hits"][0]["strand"], "+/-"
        )
        self.assertEqual(
            explorer.reverse_complement(explorer.reverse_complement("ARYKMBVDHN")),
            "ARYKMBVDHN",
        )
        with self.assertRaises(ValueError):
            explorer.motif_hits("ACGT", ".*")

    @unittest.skipUnless(importlib.util.find_spec("Bio"), "Optional Biopython")
    def test_six_frames_codes_source_coordinates_and_fasta(self):
        manifest = {"sequence_sha256": "synthetic", "start_1based_inclusive": 10}
        with patch.object(
            explorer.sequence_tools,
            "extract_sequence",
            return_value=("demo", "ATATGATAA", manifest),
        ):
            explorer.explore(
                "Synthetic",
                {
                    "file": "synthetic",
                    "start": "10",
                    "end": "18",
                    "genetic_code": "2",
                    "motif": "ATA",
                },
                self.out,
            )
        data = self.read("sequence-exploration")
        self.assertEqual(data["six_frames"][0]["protein"], "MW*")
        self.assertEqual(len(data["six_frames"]), 6)
        self.assertEqual((self.out / "six-frames.faa").read_text().count(">"), 6)
        self.assertEqual(data["source"]["start_1based_inclusive"], 10)

    def test_exploration_limits_checked_before_large_index(self):
        with patch.object(explorer.sequence_tools, "extract_sequence") as extract:
            with self.assertRaises(ValueError):
                explorer.explore("Synthetic", {"end": "100001"}, self.out)
            extract.assert_not_called()

    def test_model_readiness_is_not_inference(self):
        with patch.object(
            explorer.sequence_tools,
            "extract_sequence",
            return_value=("demo", "ACNT", {}),
        ):
            explorer.model_readiness(
                "Synthetic", {"file": "synthetic", "model_task": "eQTL"}, self.out
            )
        r = self.read("model-input-readiness")["readiness"]
        self.assertEqual(r["required_bases"], 450000)
        self.assertFalse(r["length_matches"])
        self.assertFalse(r["inference_performed"])
        self.assertFalse(r["unambiguous_DNA"])

    def test_utf8_message_round_trip_and_no_overwrite(self):
        explorer.dna_message("Synthetic", {"text": "Hello · Grüß dich 🧬"}, self.out)
        first = self.read("dna-message")
        other = self.root / "decode"
        other.mkdir()
        explorer.dna_message(
            "Synthetic", {"mode": "Decode DNA", "text": first["dna"]}, other
        )
        self.assertEqual(
            json.loads((other / "dna-message.json").read_text(encoding="utf-8"))[
                "text"
            ],
            first["text"],
        )
        with self.assertRaises(FileExistsError):
            explorer.dna_message("Synthetic", {"text": "overwrite"}, self.out)
        self.assertEqual(self.read("dna-message"), first)

    def test_handoff_omits_quotes_by_default_and_never_exports_token(self):
        context = {
            "document_evidence": ["private report"],
            "profile": {"name": "Synthetic", "birth_date": "2000-01-01"},
        }
        with patch("local_ai.evidence", return_value=context):
            explorer.agent_handoff("Synthetic", {}, self.out)
        data = self.read("agent-context")
        self.assertNotIn("document_evidence", data["evidence_snapshot"])
        self.assertNotIn("birth_date", data["evidence_snapshot"]["profile"])
        self.assertFalse(data["policy"]["network_transfer_performed"])
        self.assertFalse(data["policy"]["control_credentials_included"])

    def test_gui_cli_mcp_use_same_workflow_contracts(self):
        manifest = command_bus.manifest()
        ids = {x["id"] for x in manifest["commands"]}
        for name in (
            "sequence_explore",
            "variant_evidence_audit",
            "model_readiness",
            "dna_message",
            "agent_handoff",
        ):
            self.assertIn("workflow." + name, ids)
        self.assertIn("research.projects", ids)
        task = next(
            x for x in suite_api.CAT()["tasks"] if x["id"] == "variant_evidence_audit"
        )
        contract = tool_contracts.contract(task, task["fields"][0])
        self.assertEqual(contract["formats"], ["VCF"])
        self.assertIn("VCFv4.5", contract["versions"])


if __name__ == "__main__":
    unittest.main()
