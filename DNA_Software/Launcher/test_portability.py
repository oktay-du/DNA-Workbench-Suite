import hashlib, json, os, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import portable_paths, portable_json


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "Suite with spaces"
        self.root.mkdir()
        self.env = patch.dict(os.environ)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_process_caches_are_children_of_app(self):
        portable_paths.configure(self.root)
        for key in (
            "TEMP",
            "TMP",
            "PIP_CACHE_DIR",
            "HF_HOME",
            "APPDATA",
            "LOCALAPPDATA",
            "UV_CACHE_DIR",
            "JUPYTER_RUNTIME_DIR",
        ):
            self.assertTrue(Path(os.environ[key]).is_relative_to(self.root))
            self.assertTrue(Path(os.environ[key]).is_dir())

    def test_previous_roots_are_reread_when_the_record_changes(self):
        portable_paths.configure(self.root)
        renamed = self.base / "Renamed suite"
        self.root.rename(renamed)
        self.root = renamed
        portable_paths.configure(renamed)
        old = str(self.base / "Suite with spaces" / "Projects/p/calls.vcf")
        moved = portable_paths.rebase(old, renamed)
        self.assertEqual(moved, str(renamed / "Projects/p/calls.vcf"))
        self.assertEqual(portable_paths.rebase(old, renamed), moved)
        first = portable_json.loads('{"count": 1, "nested": {"ok": true}}')
        first["count"] = 9
        first["nested"]["ok"] = False
        second = portable_json.loads('{"count": 1, "nested": {"ok": true}}')
        self.assertEqual(second, {"count": 1, "nested": {"ok": True}})
        record = renamed / "DNA_Software/UserData/Launcher/portable-location.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        data["previous_roots"] = []
        record.write_text(json.dumps(data), encoding="utf-8")
        portable_json._CACHE["sentinel"] = {"stale": True}
        self.assertEqual(portable_paths.rebase(old, renamed), old)
        self.assertNotIn("sentinel", portable_json._CACHE)

    def test_move_records_old_location(self):
        portable_paths.configure(self.root)
        new = self.base / "Renamed suite"
        self.root.rename(new)
        data = portable_paths.configure(new)
        self.root = new
        self.assertEqual(data["previous_roots"], [str(self.base / "Suite with spaces")])

    def test_rebase_only_internal_paths(self):
        root = self.root
        old = "F:\\Previous Suite"
        value = {
            "path": old + "\\Projects\\p\\job\\Results\\calls.vcf",
            "outside": "F:\\Other Documents\\report.pdf",
            "note": "See " + old + "\\DNA_Archiv",
            "count": 20,
        }
        result = portable_paths.rebase(value, root, [old])
        self.assertEqual(result["path"], str(root / "Projects/p/job/Results/calls.vcf"))
        self.assertEqual(result["outside"], value["outside"])
        self.assertEqual(result["note"], value["note"])

    def test_rebase_does_not_change_evidence_bytes(self):
        (self.root / "DNA_Archiv").mkdir()
        p = self.root / "manifest.json"
        p.write_text(json.dumps({"path": "F:\\Old\\DNA_Archiv\\p\\calls.vcf"}))
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        with patch.object(
            portable_json,
            "rebase",
            side_effect=lambda v: portable_paths.rebase(v, self.root, ["F:\\Old"]),
        ):
            value = portable_json.loads(p.read_text())
        self.assertTrue(Path(value["path"]).is_relative_to(self.root))
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), before)

    def test_external_private_archive_is_not_claimed_by_relocated_app(self):
        path = "D:/DNA_Archiv/01_Originaldownloads/person/raw.txt"
        self.assertEqual(portable_paths.rebase(path, self.root, ["D:/"]), path)

    def test_traversal_is_not_rebased(self):
        value = "F:\\Old\\DNA_Archiv\\..\\..\\external.txt"
        self.assertEqual(portable_paths.rebase(value, self.root, ["F:\\Old"]), value)

    def test_move_into_old_root_does_not_double_prefix_current_paths(self):
        new = self.base / "Projects/New Suite"
        value = str(new / "DNA_Archiv/p/input.vcf")
        self.assertEqual(portable_paths.rebase(value, new, [str(self.base)]), value)

    def powershell(self, script, **env):
        p = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            timeout=30,
            env=dict(
                os.environ,
                TEST_PS=str(Path(__file__).with_name("Portable.ps1")),
                TEST_ROOT=str(self.root),
                **env,
            ),
        )
        self.assertEqual(p.returncode, 0, p.stderr.decode(errors="replace"))
        return p.stdout.decode("utf-8-sig", errors="replace").strip()

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell")
    def test_mount_retains_nested_folder_and_spaces(self):
        output = self.powershell(". $env:TEST_PS; Get-DnaLinuxRoot $env:TEST_ROOT")
        expected = "/mnt/" + self.root.drive[0].lower() + self.root.as_posix()[2:]
        self.assertEqual(output, expected)

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell")
    def test_distro_identity_matches_powershell(self):
        with patch.object(portable_paths, "registered", return_value=[]):
            expected = portable_paths.distro_name(self.root)
        self.assertEqual(
            self.powershell(". $env:TEST_PS; Get-DnaDistroName $env:TEST_ROOT"),
            expected,
        )

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell")
    def test_swap_update_preserves_other_host_settings(self):
        config = self.base / "fake.wslconfig"
        config.write_text(
            "# keep comment\n[wsl2]\nmemory=9GB\nswap=4GB\nswapFile=C:\\\\old.vhdx\n[experimental]\nfoo=keep\n"
        )
        self.powershell(
            ". $env:TEST_PS; Set-DnaSwapFile $env:TEST_ROOT $env:TEST_CONFIG | ConvertTo-Json",
            TEST_CONFIG=str(config),
        )
        content = config.read_text()
        for item in ("# keep comment", "memory=9GB", "swap=4GB", "foo=keep"):
            self.assertIn(item, content)
        self.assertEqual(content.lower().count("swapfile="), 1)
        self.assertIn(str(self.root).replace("\\", "\\\\"), content)
        self.assertTrue(
            list((self.root / "DNA_Software/UserData/HostBackups").glob("*"))
        )
        self.assertFalse(
            json.loads(
                self.powershell(
                    ". $env:TEST_PS; Set-DnaSwapFile $env:TEST_ROOT $env:TEST_CONFIG | ConvertTo-Json",
                    TEST_CONFIG=str(config),
                )
            )["changed"]
        )

    def test_shell_scripts_are_not_bound_to_drive_d(self):
        base = Path(__file__).resolve().parent.parent / "Start"
        for name in (
            "DNA.ps1",
            "profile-dna.sh",
            "docker-dna.sh",
            "linux-launch.sh",
            "containers-compose.yaml",
        ):
            text = (base / name).read_text(encoding="utf-8-sig")
            self.assertNotIn("/mnt/d", text, name)


if __name__ == "__main__":
    unittest.main()
