"""Linux desktop window stays on the loopback workspace and does not use a browser."""

import shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import Mock
import desktop_host


class DesktopHostTests(unittest.TestCase):
    def test_embedded_command_owns_the_service_without_a_browser(self):
        info = Path("/tmp/service.json")
        command = desktop_host.embedded_command(info, "python3")
        self.assertEqual(command[0], "python3")
        self.assertTrue(command[1].endswith("family.py"))
        self.assertEqual(command[2:], ["--embedded", str(info)])
        self.assertNotIn("--headless", command)

    def test_workspace_url_is_only_the_local_app(self):
        self.assertEqual(
            desktop_host.workspace_url("http://127.0.0.1:43123"),
            "http://127.0.0.1:43123/app",
        )
        self.assertEqual(
            desktop_host.workspace_url("http://127.0.0.1:43123/"),
            "http://127.0.0.1:43123/app",
        )

    def test_workspace_url_rejects_anything_except_loopback(self):
        for url in (
            "http://localhost:9/app",
            "https://127.0.0.1:9/app",
            "http://127.0.0.1/app",
            "http://10.0.2.2:9/app",
            "http://user:secret@127.0.0.1:9/app",
            "file:///tmp/app.html",
        ):
            with self.assertRaises(ValueError):
                desktop_host.workspace_url(url)

    def test_wait_for_service_reads_the_ready_file(self):
        folder = Path(tempfile.mkdtemp())
        info = folder / "service.json"
        try:
            info.write_text('{"url": "http://127.0.0.1:9"}', encoding="utf-8")
            process = Mock()
            process.poll.return_value = None
            self.assertEqual(
                desktop_host.wait_for_service(info, process, timeout=1),
                {"url": "http://127.0.0.1:9"},
            )
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_wait_for_service_reports_a_startup_failure(self):
        process = Mock()
        process.poll.return_value = 1
        process.stderr.read.return_value = b"already running"
        with self.assertRaises(RuntimeError) as error:
            desktop_host.wait_for_service(
                Path("/no/such/service.json"), process, timeout=1
            )
        self.assertIn("already running", str(error.exception))


if __name__ == "__main__":
    unittest.main()
