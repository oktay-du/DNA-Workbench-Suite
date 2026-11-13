"""Adversarial fixtures for local inputs, cache metadata and protocol boundaries."""

from pathlib import Path
import tempfile
import unittest
import security_paths
import network_io
import security_sql
import system_tools
from unittest.mock import patch


class SecurityPathTests(unittest.TestCase):
    def test_managed_ids_reject_traversal_and_windows_devices(self):
        for value in (
            "../Other",
            "/tmp/other",
            "C:\\Other",
            "..",
            "x/y",
            "CON",
            "NUL",
            "",
            None,
            "x" * 121,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                security_paths.identifier(value)
        self.assertEqual(security_paths.identifier("P001_Ich"), "P001_Ich")

    def test_artifact_names_cannot_escape_results(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in (
                "../secret.txt",
                "/secret.txt",
                "C:/secret.txt",
                "x/../../secret",
                "x\\secret",
                "./x",
                "x//y",
            ):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    security_paths.contained(folder, value)
            self.assertEqual(
                security_paths.contained(folder, "plots/result.svg"),
                Path(folder) / "plots/result.svg",
            )

    def test_explicit_inputs_can_be_outside_the_app_but_not_urls(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "source.vcf"
            file.write_text("synthetic")
            self.assertEqual(security_paths.input_file(file), file.resolve())
            for value in (
                "https://example.org/file",
                "\\\\server\\share\\file",
                "//server/share/file",
                "C:relative.txt",
            ):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    security_paths.local_path(value)

    def test_inspection_rejects_requests_outside_managed_folders(self):
        import engine

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = root / "check-request.json"
            request.write_text("{}", encoding="utf-8")
            with (
                patch.object(engine, "ROOT", root),
                patch.object(
                    engine.sys, "argv", ["engine.py", "--inspect", str(request)]
                ),
                patch.object(engine.inspector, "check_batch") as check,
            ):
                self.assertEqual(engine.main(), 1)
            check.assert_not_called()

    def test_legacy_inspection_does_not_require_a_job_status_file(self):
        import engine

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "Projects/Source verification/P001_Ich/check"
            target.mkdir(parents=True)
            request = target / "pruefanfrage.json"
            request.write_text(
                '{"person":"P001_Ich","files":["sample.vcf"]}', encoding="utf-8"
            )
            with (
                patch.object(engine, "ROOT", root),
                patch.object(
                    engine.sys, "argv", ["engine.py", "--inspect", str(request)]
                ),
                patch.object(engine.inspector, "check_batch") as check,
            ):
                self.assertEqual(engine.main(), 0)
            self.assertEqual(
                check.call_args.args[:3], ("P001_Ich", ["sample.vcf"], target)
            )

    def test_links_cannot_redirect_managed_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            outside = root / "outside"
            outside.mkdir()
            base = root / "base"
            base.mkdir()
            try:
                (base / "redirect").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation is unavailable for this account")
            with self.assertRaises(ValueError):
                security_paths.contained(base, "redirect/result.txt")

    def test_cache_cannot_reuse_a_job_outside_the_selected_profile(self):
        import result_cache

        task = {"id": "inspect", "kind": "analysis", "fields": []}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                result_cache.lookup(
                    Path(folder),
                    "P1",
                    task,
                    {},
                    [{"job": "../../Other", "task": "inspect", "status": "Complete"}],
                )

    def test_sealed_outputs_detect_changes_missing_files_and_escapes(self):
        import result_cache

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "Results").mkdir()
            file = folder / "Results/result.txt"
            file.write_text("before")
            metadata = file.stat()
            expected = {
                "result.txt": {
                    "bytes": metadata.st_size,
                    "mtime_ns": metadata.st_mtime_ns,
                }
            }
            self.assertTrue(result_cache.outputs_unchanged(folder, expected))
            file.write_text("changed contents")
            self.assertFalse(result_cache.outputs_unchanged(folder, expected))
            file.unlink()
            self.assertFalse(result_cache.outputs_unchanged(folder, expected))
            with self.assertRaises(ValueError):
                result_cache.outputs_unchanged(
                    folder, {"../outside.txt": expected["result.txt"]}
                )

    def test_host_tools_do_not_accept_an_arbitrary_executable(self):
        for name in ("evil.exe", "../wsl.exe", "cmd.exe /c echo unsafe"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                system_tools.windows_executable(name)
        import os

        if os.name == "nt":
            path = Path(system_tools.windows_executable("cmd.exe"))
            self.assertTrue(path.is_absolute())
            self.assertEqual(path.parent.name.lower(), "system32")


class ParserAndSqlTests(unittest.TestCase):
    def test_argument_vector_does_not_interpret_shell_metacharacters(self):
        import engine, sys

        with tempfile.TemporaryDirectory() as folder:
            job = object.__new__(engine.Job)
            job.folder = Path(folder)
            lines = []
            job.log = lines.append
            job.save = lambda: None
            payload = 'value; " & $(echo unsafe) | > unexpected.txt'
            job.run_process(
                [sys.executable, "-c", "import sys; print(sys.argv[1])", payload]
            )
            self.assertIn(payload, lines)
            self.assertFalse((Path(folder) / "unexpected.txt").exists())

    def test_sql_identifiers_cannot_insert_clauses(self):
        self.assertEqual(
            security_sql.identifier("source_metadata"), '"source_metadata"'
        )
        for value in (
            "files; DROP TABLE files",
            'files" WHERE 1=1 --',
            "x/y",
            "x-y",
            "",
            None,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                security_sql.identifier(value)

    def test_gedcom_rejects_adversarial_long_lines_without_backtracking(self):
        import genealogy_research, time

        started = time.monotonic()
        for line in (
            "1 " + " " * 100000 + "!",
            "1 @" + "x" * 100000,
            "9" * 100000 + " NAME A",
            "1 " + "A" * 100000,
        ):
            with self.assertRaises(ValueError):
                genealogy_research.parse("0 HEAD\n" + line + "\n0 TRLR")
        self.assertLess(time.monotonic() - started, 3)

    def test_generated_gedcom_mutations_do_not_escape_parser_bounds(self):
        import genealogy_research

        # Deterministic adversarial mutations are reproducible; no random security token.
        for length in (0, 1, 2, 63, 64, 65, 200, 201, 4096, 65537):
            for value in (
                "@" + "x" * length,
                "NAME" + " " * length + "!",
                "A" * length,
            ):
                try:
                    genealogy_research.parse("0 HEAD\n1 " + value + "\n0 TRLR")
                except ValueError:
                    pass

    def test_profile_database_rejects_escaping_blob_paths(self):
        import sqlite3, profile_transfer, contextlib

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.sqlite"
            with contextlib.closing(sqlite3.connect(source)) as db, db:
                db.execute(
                    "CREATE TABLE blobs(sha256 TEXT PRIMARY KEY,stored_rel TEXT NOT NULL,bytes INTEGER NOT NULL,kind TEXT,detected_build TEXT,members TEXT)"
                )
                db.execute(
                    "INSERT INTO blobs VALUES(?,?,?,?,?,?)",
                    ("a" * 64, "../outside.txt", 1, "Report", "", "[]"),
                )
            with self.assertRaises(ValueError):
                profile_transfer.safe_database(
                    source, root / "stage", {"P1": "P2"}, str(root / "old"), {}
                )

    def test_backup_reports_must_be_present_in_the_checked_manifest(self):
        import profile_transfer

        manifest = {
            "source_person": "P1",
            "files": [{"restore": "Profiles/P1/report.pdf", "sha256": "a" * 64}],
        }
        data = {
            "source_paths": {"C:/old/report.pdf": "Profiles/P1/report.pdf"},
            "documents": [
                {"person": "P1", "path": "C:/old/report.pdf", "sha256": "a" * 64}
            ],
        }
        profile_transfer.validate_source_paths(manifest, data)
        data["documents"][0]["path"] = "C:/private/secret.pdf"
        with self.assertRaises(ValueError):
            profile_transfer.validate_source_paths(manifest, data)
        data["documents"] = []
        data["source_paths"]["C:/old/report.pdf"] = "../private.pdf"
        with self.assertRaises(ValueError):
            profile_transfer.validate_source_paths(manifest, data)

    def test_finding_review_expires_when_source_changes(self):
        import importlib.util, hashlib

        spec = importlib.util.spec_from_file_location(
            "security_audit_test",
            Path(__file__).resolve().parents[2] / "scripts/Security-Audit.py",
        )
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "worker.py"
            file.write_text("original code")
            with patch.object(audit, "ROOT", Path(folder)):
                issue = {
                    "filename": str(file),
                    "test_id": "B603",
                    "code": "1 safe_call()\n",
                }
                path, rule, code_hash = audit.review_identity(issue)
                record = {
                    "path": path,
                    "rule": rule,
                    "code_sha256": code_hash,
                    "file_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                    "reason": "Reviewed argument vector",
                    "tests": ["argument vector test"],
                }
                self.assertTrue(audit.reviewed(issue, [record]))
                file.write_text("changed code")
                self.assertFalse(audit.reviewed(issue, [record]))


class NetworkBoundaryTests(unittest.TestCase):
    def test_download_connections_pin_the_checked_ip_and_keep_hostname_verification(
        self,
    ):
        import ssl

        with (
            patch.object(
                network_io.socket,
                "getaddrinfo",
                return_value=[(2, 1, 6, "", ("8.8.8.8", 443))],
            ),
            patch.object(network_io.socket, "create_connection") as connect,
        ):
            with patch.object(
                network_io.http.client.HTTPSConnection,
                "connect",
                lambda connection: connection._create_connection(
                    (connection.host, connection.port), 10, None
                ),
            ):
                client = network_io.PublicHTTPSConnection("example.org")
                client.connect()
            self.assertEqual(connect.call_args.args[0], ("8.8.8.8", 443))
            self.assertEqual(client.host, "example.org")
            self.assertTrue(client._context.check_hostname)
            self.assertEqual(client._context.verify_mode, ssl.CERT_REQUIRED)

    def test_download_schemes_credentials_and_private_addresses_are_rejected(self):
        for url in (
            "file:///etc/passwd",
            "ftp://example.org/file",
            "http://example.org/file",
            "https://u:p@example.org/file",
            "https://example.org:8443/file",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                network_io.validate_https(url)
        for address in (
            "127.0.0.1",
            "10.0.0.1",
            "192.168.0.1",
            "169.254.169.254",
            "::1",
            "fc00::1",
        ):
            with patch.object(
                network_io.socket,
                "getaddrinfo",
                return_value=[(2, 1, 6, "", (address, 443))],
            ):
                with self.subTest(address=address), self.assertRaises(ValueError):
                    network_io.validate_https("https://example.org/file")

    def test_https_redirect_cannot_downgrade_or_reach_intranet(self):
        handler = network_io.PublicRedirects()
        request = network_io.urllib.request.Request("https://example.org/file")
        with self.assertRaises(ValueError):
            handler.redirect_request(
                request, None, 302, "", {}, "http://example.org/file"
            )
        with patch.object(
            network_io.socket,
            "getaddrinfo",
            return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
        ):
            with self.assertRaises(ValueError):
                handler.redirect_request(
                    request, None, 302, "", {}, "https://internal.test/file"
                )

    def test_local_service_cannot_use_remote_hosts_or_follow_redirects(self):
        for url in (
            "http://example.org:1234/api",
            "http://localhost:1234/api",
            "https://127.0.0.1:1234/api",
            "http://127.0.0.1/api",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                network_io.open_loopback(url)
        with self.assertRaises(ValueError):
            network_io.NoLocalRedirects().redirect_request(
                None, None, 302, "", {}, "https://example.org/"
            )


if __name__ == "__main__":
    unittest.main()
