import io, tempfile, unittest, hashlib
from pathlib import Path
from unittest.mock import patch
import dependency_manager as dm, public_package


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.state = self.base / "state"
        self.state.mkdir()
        self.item = {
            "id": "demo",
            "name": "demo.bin",
            "relative_path": "DNA_Software/Downloads/demo.bin",
            "url": "https://example.org/demo.bin",
            "source": "https://example.org/",
            "group": "tools",
            "version": "1.0",
            "expected_sha256": hashlib.sha256(b"test artifact").hexdigest(),
            "expected_bytes": 13,
        }
        self.patches = [
            patch.object(dm, "ROOT", self.base),
            patch.object(dm, "STATE", self.state),
            patch.object(dm, "LOCK", {"app_version": "test", "items": [self.item]}),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_archive_not_claimed_installed(self):
        p = self.base / self.item["relative_path"]
        p.parent.mkdir(parents=True)
        p.write_bytes(b"test artifact")
        row = next(r for r in dm.snapshot()["items"] if r["id"] == "demo")
        self.assertIn("not confirmed as a running tool", row["status"])

    def test_stage_immutable(self):
        with patch.object(dm, "get", return_value=io.BytesIO(b"test artifact")):
            r = dm.stage(["demo"])["items"][0]
        self.assertTrue(Path(r["path"]).is_file())
        self.assertFalse((self.base / self.item["relative_path"]).exists())
        self.assertTrue(r["publisher_hash_verified"])

    def test_checksum_mismatch_never_activated(self):
        with patch.object(dm, "get", return_value=io.BytesIO(b"bad artifact!")):
            r = dm.stage(["demo"])["items"][0]
        self.assertEqual(r["status"], "Failed")
        self.assertFalse((self.base / self.item["relative_path"]).exists())

    def test_restricted_license_not_downloaded(self):
        self.item["license_notice"] = "restricted"
        with patch.object(dm, "get") as get:
            r = dm.stage(["demo"])["items"][0]
            get.assert_not_called()
        self.assertEqual(r["status"], "Failed")

    def test_public_allowlist_has_no_private_directories(self):
        for _, name in public_package.entries():
            self.assertNotIn("DNA_Archiv", name)
            self.assertNotIn("UserData", name)
            self.assertNotIn("Projects", name)
            self.assertNotIn("Logs", name)

    def test_public_allowlist_no_binaries_or_genotypes(self):
        import sample_data

        folder = public_package.HERE / "Public/Samples"
        if not (folder / "manifest.json").exists():
            folder = public_package.ROOT / "Samples"
        approved = {x["path"] for x in sample_data.validate(folder)["files"]}
        for _, name in public_package.entries():
            if name.startswith("Samples/"):
                self.assertIn(
                    name.removeprefix("Samples/"), approved | {"manifest.json"}
                )
            else:
                self.assertNotIn(
                    Path(name).suffix.lower(),
                    [".sqlite", ".vcf", ".bam", ".cram", ".exe", ".vhdx"],
                )

    def test_downgrade_not_offered(self):
        self.assertLess(dm.version("v1.9.9"), dm.version("v1.10.0"))

    def test_clinvar_md5_is_not_claimed_as_publisher_authentication(self):
        import gzip

        base = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
        content = {
            base: gzip.compress(b"##fileformat=VCFv4.2\n"),
            base + ".tbi": b"synthetic index",
        }

        def response(url):
            if url.endswith(".md5"):
                return io.BytesIO(
                    hashlib.md5(content[url[:-4]], usedforsecurity=False)
                    .hexdigest()
                    .encode()
                )
            return io.BytesIO(content[url])

        with patch.object(dm, "get", side_effect=response):
            result = dm.stage_clinvar({"id": "clinvar", "url": base})
        self.assertTrue(result["publisher_md5_matches"])
        self.assertFalse(result["publisher_hash_verified"])
        self.assertEqual(len(result["artifacts"]), 2)
        self.assertIn("not independently publisher-verified", result["integrity_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
