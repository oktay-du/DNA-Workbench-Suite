import importlib.util, sys, tempfile, unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "linux", "Linux symlink test")
class LinuxPortabilityTests(unittest.TestCase):
    def test_alias_can_follow_an_app_moved_to_a_new_folder(self):
        source = Path(__file__).resolve().parent.parent / "Start/relocate-linux.py"
        spec = importlib.util.spec_from_file_location("relocate_for_test", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            old = base / "Old Suite"
            new = base / "New Suite"
            linux = base / "linux"
            (old / "DNA_Linux/DNA-SSD").mkdir(parents=True)
            (old / "DNA_Linux/DNA-SSD/ext4.vhdx").touch()
            (linux / "bin").mkdir(parents=True)
            wrapper = linux / "bin/tool"
            wrapper.write_text("#!/bin/bash\ncat /mnt/d/Projects/file.txt\n")
            evidence = old / "Projects/manifest.json"
            evidence.parent.mkdir()
            evidence.write_text('{"path":"/mnt/d/historical"}')
            original = evidence.read_bytes()
            module.relocate(old, linux)
            self.assertEqual((linux / "ssd").resolve(), old)
            self.assertIn(str(linux / "ssd"), wrapper.read_text())
            old.rename(new)
            module.relocate(new, linux)
            self.assertEqual((linux / "ssd").resolve(), new)
            self.assertEqual((new / "Projects/manifest.json").read_bytes(), original)
            self.assertTrue((linux / "cache/tmp").is_dir())


if __name__ == "__main__":
    unittest.main()
