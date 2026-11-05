import unittest, json, gzip
from contextlib import closing
from pathlib import Path
from test_profile_pipeline import ProfilePipelineTests
import best_dataset, source_store, profile_pipeline as pp


class BestDatasetTests(ProfilePipelineTests):
    # Reuse only fixture helpers, not the inherited regression suite.
    def test_versioned_dataset_roundtrip_and_all_source_names(self):
        self.source("Dante_v1")
        self.source("Sequencing_v2")
        out = self.folder("bundle")
        r = best_dataset.build(self.pid, out, "GRCh38", self.fa, log=lambda _: None)
        dest = Path(r["folder"])
        self.assertEqual(dest.parent.parent.name, "BestDataset")
        self.assertEqual(len(r["files"]), 6)
        m = json.loads((dest / "manifest.json").read_text())
        self.assertEqual(len(m["source_aliases"]), 2)
        self.assertEqual(
            {a["provider"] for a in m["source_aliases"]}, {"Dante_v1", "Sequencing_v2"}
        )
        self.assertEqual(sum(x["primary_snps"] for x in m["source_contributions"]), 3)
        self.assertEqual(
            len((dest / "variant_provenance.tsv").read_text().splitlines()), 4
        )
        for n in ["vcf", "txt", "tsv"]:
            with gzip.open(dest / ("best_selection." + n + ".gz"), "rb") as f:
                self.assertEqual(
                    f.read(), (dest / ("best_selection." + n)).read_bytes()
                )
        self.assertEqual(pp.summary(self.pid)["sets"][0]["folder"], str(dest))
        self.assertFalse(m["validation"]["clinical_validation"])

    def test_failed_renewal_keeps_current_and_previous_version(self):
        self.source()
        r = best_dataset.build(
            self.pid, self.folder("bundle"), "GRCh38", self.fa, log=lambda _: None
        )
        pointer = source_store.profile_dir(self.pid) / "BestDataset/current.json"
        before = pointer.read_bytes()
        with self.assertRaises(ValueError):
            best_dataset.build(
                self.pid, self.folder("failed"), "GRCh37", self.fa, log=lambda _: None
            )
        self.assertEqual(before, pointer.read_bytes())
        self.assertTrue(Path(r["folder"]).is_dir())

    def test_same_bytes_have_separate_provenance_records(self):
        row = self.source("first")
        original = Path(row["path"])
        copy = self.root / "second.vcf"
        copy.write_bytes(original.read_bytes())
        imported = source_store.import_batch(
            self.pid,
            [str(copy)],
            "Other provider",
            "Other version",
            storage_mode="move",
            version="v2",
            log=lambda _: None,
        )
        self.assertEqual(imported["operations"][0]["target"], str(original))
        self.assertFalse(copy.exists())
        receipt = Path(imported["operations"][0]["receipt"])
        self.assertTrue(receipt.exists())
        d = json.loads(receipt.read_text())
        self.assertEqual(d["provider"], "Other provider")
        self.assertEqual(d["sha256"], row["sha256"])
        self.assertEqual(d["stored_name"], original.name)
        with closing(source_store.connect(self.pid)) as db:
            db.execute(
                "INSERT INTO source_metadata VALUES(?,?,?)",
                (
                    imported["ids"][0],
                    json.dumps({"declared_version": "v2", "measurement": "Measured"}),
                    "now",
                ),
            )
            db.commit()
        rows = source_store.listing(self.pid)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({x["path"] for x in rows}), 1)
        self.assertEqual(
            next(x for x in rows if x["provider"] == "Other provider")[
                "declared_version"
            ],
            "v2",
        )
        self.assertEqual(
            next(x for x in rows if x["provider"] == "first")["declared_version"], ""
        )
        a, report = self.analysis()
        self.assertEqual(
            sum(x["status"] == "duplicate-bytes" for x in report["sources"]), 1
        )

    def test_cli_gui_mcp_share_new_workflow_declaration(self):
        import command_bus

        commands = command_bus.manifest()["commands"]
        self.assertTrue(any("best_dataset" in str(x) for x in commands))


# unittest normally inherits tests: retain the common setup/helpers, exclude parent test methods.
for name in dir(ProfilePipelineTests):
    if name.startswith("test_") and name not in BestDatasetTests.__dict__:
        setattr(BestDatasetTests, name, None)
del ProfilePipelineTests
if __name__ == "__main__":
    unittest.main()
