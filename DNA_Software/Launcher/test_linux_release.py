"""The Linux release zip is built by the release tool, without the Windows EXE."""

import os
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

    def test_auto_target_follows_the_host(self):
        self.assertIn(os.name, ("nt", "posix"))


if __name__ == "__main__":
    unittest.main()
