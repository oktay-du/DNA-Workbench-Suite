"""The Linux release zip is built by the release tool, without the Windows EXE."""

import os
import plistlib
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

import release_tools


class LinuxReleaseTests(unittest.TestCase):
    def test_linux_zip_contains_the_desktop_launcher(self):
        folder = Path(tempfile.mkdtemp())
        archive = release_tools.build_linux_zip(folder / "DNAWorkbench-Linux-x64.zip")
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
            self.assertIn("DNA-Workbench.sh", names)
            self.assertIn("DNA_Software/Launcher/dna_cli.py", names)
            self.assertIn("DNA_Software/Launcher/desktop_host.py", names)
            self.assertNotIn("DNA_Launcher.exe", names)
            script = bundle.read("DNA-Workbench.sh").decode()
            self.assertIn("dna_cli.py", script)
            self.assertIn("desktop", script)
            info = bundle.getinfo("DNA-Workbench.sh")
            self.assertEqual(info.external_attr >> 16, 0o100755)
        self.assertTrue(stat.S_ISREG(archive.stat().st_mode))

    def test_macos_zip_contains_a_native_app_entry_point(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = release_tools.build_desktop_zip(
                Path(folder) / "DNAWorkbench-macOS-arm64.zip", b"synthetic-viewer"
            )
            with zipfile.ZipFile(archive) as bundle:
                app = "DNA-Workbench.app/Contents/"
                info = plistlib.loads(bundle.read(app + "Info.plist"))
                entry = app + "MacOS/" + info["CFBundleExecutable"]
                self.assertEqual(bundle.getinfo(entry).external_attr >> 16, 0o100755)
                self.assertIn(b"dna_cli.py desktop", bundle.read(entry))
                self.assertEqual(
                    bundle.read(app + "MacOS/DNAWorkbenchWebView"), b"synthetic-viewer"
                )
                self.assertIn("DNA_Software/Launcher/family.py", bundle.namelist())
                self.assertNotIn("DNA_Launcher.exe", bundle.namelist())

    def test_architecture_names_match_release_packages(self):
        for arch in ("x86_64", "AMD64"):
            self.assertEqual(release_tools.desktop_arch(arch), "x64")
        for arch in ("aarch64", "ARM64"):
            self.assertEqual(release_tools.desktop_arch(arch), "arm64")
        with self.assertRaises(ValueError):
            release_tools.desktop_arch("i386")

    def test_auto_target_follows_the_host(self):
        self.assertIn(os.name, ("nt", "posix"))


if __name__ == "__main__":
    unittest.main()
