"""Every pinned download has a Windows and Linux host decision."""

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import engine
import on_demand
import tool_hosts
import system_tools


class ToolHostTests(unittest.TestCase):
    def test_every_pin_has_one_decision(self):
        rows = tool_hosts.rows()
        items = tool_hosts.json.loads(tool_hosts.LOCK.read_text(encoding="utf-8"))[
            "items"
        ]
        self.assertEqual(len(rows), len(items))
        self.assertEqual(len({row["id"] for row in rows}), len(items))

    def test_windows_and_linux_binaries_stay_distinct(self):
        by_id = {row["id"]: row for row in tool_hosts.rows()}
        self.assertEqual(by_id["plink2-linux"]["linux"], "native")
        self.assertEqual(by_id["plink2-windows"]["windows"], "native")
        self.assertEqual(by_id["ubuntu-wsl"]["linux"], "not used")
        self.assertEqual(by_id["mosdepth"]["windows"], "samtools depth")
        self.assertIn("Win-NGS", by_id["samtools-1-23-1-windows"]["note"])
        if os.name == "nt":
            self.assertEqual(tool_hosts.prefer("gramps"), "grampsaio-6-0-8-1-win64-exe")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-23-1-windows")
        else:
            self.assertEqual(tool_hosts.prefer("gramps"), "gramps-6-0-8-1-amd64-snap")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-25-tar-bz2")
        with mock.patch.object(tool_hosts.os, "name", "nt"):
            self.assertEqual(tool_hosts.prefer("plink2"), "plink2-windows")
            self.assertEqual(tool_hosts.prefer("samtools"), "samtools-1-23-1-windows")
            self.assertIsNone(tool_hosts.prefer("mosdepth"))
        self.assertTrue(
            all(
                row["linux"] != "wine" and row["windows"] != "wine"
                for row in tool_hosts.rows()
            )
        )

    def test_linux_host_keeps_a_native_path(self):
        if os.name == "nt":
            self.skipTest("Windows maps drive letters into WSL")
        path = engine.linux(Path(__file__).resolve())
        self.assertFalse(path.startswith("/mnt/"))
        self.assertTrue(path.endswith("test_tool_hosts.py"))

    def test_mac_desktop_path_finds_apple_silicon_homebrew(self):
        with (
            mock.patch.object(system_tools.sys, "platform", "darwin"),
            mock.patch.object(system_tools.platform, "machine", return_value="arm64"),
            mock.patch.object(system_tools.shutil, "which") as which,
        ):
            system_tools.native_sequence_command(on_demand.ROOT, "fastp")
        self.assertEqual(which.call_args.args, ("fastp",))
        self.assertEqual(
            which.call_args.kwargs["path"].split(os.pathsep)[-1], "/opt/homebrew/bin"
        )

    def test_native_brew_install_rechecks_executable(self):
        with (
            mock.patch.object(on_demand, "native_brew", return_value="/brew/bin/brew"),
            mock.patch.object(
                on_demand, "host_command", side_effect=[None, "/brew/bin/bcftools"]
            ),
            mock.patch.object(on_demand.subprocess, "run") as run,
        ):
            result = on_demand.install_native_sequence_tool("bcftools")
        run.assert_called_once_with(
            ["/brew/bin/brew", "install", "bcftools"], check=True
        )
        self.assertEqual(result["path"], "/brew/bin/bcftools")

    def test_kiri_probe_uses_only_the_local_endpoint_and_cached_image(self):
        with (
            mock.patch.object(
                system_tools, "kiri_windows_pipe_exists", return_value=True
            ),
            mock.patch.dict(
                os.environ,
                {"DOCKER_CONTEXT": "remote", "DOCKER_HOST": "tcp://remote:2375"},
            ),
            mock.patch.object(system_tools.platform, "machine", return_value="x86_64"),
            mock.patch.object(Path, "is_socket", return_value=True),
            mock.patch.object(
                system_tools.shutil, "which", return_value=str(Path(__file__).resolve())
            ),
            mock.patch.object(
                system_tools.subprocess,
                "run",
                side_effect=[
                    mock.Mock(returncode=0, stdout="amd64\n"),
                    mock.Mock(
                        returncode=0, stdout='{"Os":"linux","Architecture":"amd64"}'
                    ),
                ],
            ) as run,
        ):
            prefix, env, platform, image = system_tools.kiri_sequence_tool("bcftools")
        self.assertEqual(prefix[1], "--host")
        self.assertTrue(prefix[2].startswith(("npipe://", "unix://")))
        self.assertNotIn("DOCKER_HOST", env)
        self.assertNotIn("DOCKER_CONTEXT", env)
        self.assertEqual(platform, "linux/amd64")
        self.assertEqual(image, system_tools.KIRI_BCFTOOLS_IMAGE)
        self.assertEqual(
            run.call_args.args[0],
            [*prefix, "image", "inspect", "--format", "{{json .}}", image],
        )

    def test_deepvariant_rosetta_requires_working_tensorflow(self):
        executable = str(Path(__file__).resolve())
        for system, outcome in (("darwin", 0), ("darwin", 132), ("linux", 0)):
            with (
                self.subTest(system=system, outcome=outcome),
                mock.patch.object(system_tools.os, "name", "posix"),
                mock.patch.object(system_tools.sys, "platform", system),
                mock.patch.object(
                    system_tools,
                    "Path",
                    mock.Mock(
                        return_value=mock.Mock(
                            is_socket=lambda: True, is_absolute=lambda: True
                        ),
                        home=lambda: mock.MagicMock(),
                    ),
                ),
                mock.patch.object(
                    system_tools.shutil, "which", return_value=executable
                ),
                mock.patch.object(system_tools.os.path, "isabs", return_value=True),
                mock.patch.object(
                    system_tools.subprocess,
                    "run",
                    side_effect=[
                        mock.Mock(returncode=0, stdout="arm64"),
                        mock.Mock(
                            returncode=0, stdout='{"Os":"linux","Architecture":"amd64"}'
                        ),
                        mock.Mock(returncode=outcome, stdout="DNA_DEEPVARIANT_CPU_OK"),
                    ],
                ) as run,
            ):
                route = system_tools.kiri_sequence_tool("deepvariant")
            if system == "darwin" and outcome == 0:
                self.assertEqual(route.platform, "linux/amd64")
                self.assertIn("--network=none", run.call_args.args[0])
                self.assertIn("--pull=never", run.call_args.args[0])
                self.assertIn("/tmp:rw,nosuid,nodev,size=64m", run.call_args.args[0])
            else:
                self.assertIsNone(route)
            self.assertEqual(run.call_count, 3 if system == "darwin" else 1)

    def test_kiri_vep_accepts_only_the_pinned_archive_for_the_engine_architecture(self):
        for arch, image_id in system_tools.KIRI_VEP_IMAGE_IDS.items():
            for reported_id in (image_id, "sha256:" + "0" * 64):
                with (
                    self.subTest(arch=arch, reported_id=reported_id),
                    mock.patch.object(
                        system_tools, "kiri_windows_pipe_exists", return_value=True
                    ),
                    mock.patch.object(Path, "is_socket", return_value=True),
                    mock.patch.object(
                        system_tools.shutil,
                        "which",
                        return_value=str(Path(__file__).resolve()),
                    ),
                    mock.patch.object(
                        system_tools.subprocess,
                        "run",
                        side_effect=[
                            mock.Mock(returncode=0, stdout=arch),
                            mock.Mock(returncode=1, stdout=""),
                            mock.Mock(
                                returncode=0,
                                stdout=json.dumps(
                                    {
                                        "Os": "linux",
                                        "Architecture": arch,
                                        "Id": reported_id,
                                    }
                                ),
                            ),
                        ],
                    ) as run,
                ):
                    route = system_tools.kiri_sequence_tool("vep")
                self.assertEqual(run.call_args.args[0][-1], image_id)
                if reported_id == image_id:
                    self.assertEqual(route.platform, "linux/" + arch)
                    self.assertEqual(route.image, image_id)
                else:
                    self.assertIsNone(route)

    def test_kiri_arm64_engine_requires_an_arm64_image(self):
        image_id = "sha256:" + "a" * 64
        for image_arch in ("arm64", "amd64"):
            with (
                mock.patch.object(
                    system_tools, "kiri_windows_pipe_exists", return_value=True
                ),
                self.subTest(image_arch=image_arch),
                mock.patch.object(
                    system_tools.platform, "machine", return_value="x86_64"
                ),
                mock.patch.object(Path, "is_socket", return_value=True),
                mock.patch.object(
                    system_tools.shutil,
                    "which",
                    return_value=str(Path(__file__).resolve()),
                ),
                mock.patch.object(
                    system_tools.subprocess,
                    "run",
                    side_effect=[
                        mock.Mock(returncode=0, stdout="arm64"),
                        mock.Mock(
                            returncode=0,
                            stdout=json.dumps(
                                {
                                    "Os": "linux",
                                    "Architecture": image_arch,
                                    "Id": image_id,
                                }
                            ),
                        ),
                    ],
                ) as run,
            ):
                route = system_tools.kiri_sequence_tool("fastp")
            self.assertEqual(
                run.call_args.args[0][-1], system_tools.KIRI_SEQUENCE_IMAGE
            )
            if image_arch == "arm64":
                self.assertEqual(
                    (route.platform, route.image), ("linux/arm64", image_id)
                )
            else:
                self.assertIsNone(route)

    def test_supported_tasks_report_kiri_as_ready(self):
        with (
            mock.patch.object(on_demand.hardware, "windows_arm64", return_value=False),
            mock.patch.object(
                on_demand, "linux_state", return_value={"running": False}
            ),
            mock.patch.object(on_demand, "host_tool_available", return_value=False),
            mock.patch.object(
                on_demand, "kiri_sequence_tool", return_value=(["docker"], {})
            ),
        ):
            convert = on_demand.status("variant_convert")
            self.assertTrue(convert["ready"])
            self.assertFalse(convert["needs_linux"])
            self.assertFalse(
                on_demand.status("variant_convert", allow_kiri=False)["ready"]
            )
            self.assertTrue(on_demand.status("vcf_qc")["ready"])
            self.assertTrue(on_demand.status("filter")["ready"])
            self.assertTrue(on_demand.status("merge")["ready"])
            self.assertTrue(on_demand.status("roh")["ready"])
            self.assertTrue(on_demand.status("kinship")["ready"])
            export = on_demand.status("ref_export")
            self.assertTrue(export["ready"])
            self.assertEqual(
                {r["id"] for r in export["requirements"]}, {"plink2", "bcftools"}
            )
            on_demand.kiri_sequence_tool.assert_called_with("ref_export")
            self.assertTrue(on_demand.status("multiqc")["ready"])
            self.assertTrue(on_demand.status("beagle")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("beagle")
            self.assertTrue(on_demand.status("ibd")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("hap-ibd")
            self.assertTrue(on_demand.status("peddy")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("peddy")
            self.assertTrue(on_demand.status("whatshap")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("whatshap")
            for task in ("truvari", "mito", "yhaplo", "pharmcat", "gatk_validate"):
                self.assertTrue(on_demand.status(task)["ready"])
                on_demand.kiri_sequence_tool.assert_called_with(task)
            for task in ("identity", "conflicts"):
                self.assertTrue(on_demand.status(task)["ready"])
                on_demand.kiri_sequence_tool.assert_called_with("pysam")
            self.assertTrue(on_demand.status("pca")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("pca")
            normalization = on_demand.status("normalize")
            self.assertTrue(normalization["ready"])
            self.assertEqual(
                {record["id"] for record in normalization["requirements"]},
                {"samtools", "bcftools"},
            )
            on_demand.kiri_sequence_tool.assert_called_with("normalize")
            self.assertTrue(on_demand.status("fastq_qc")["ready"])
            self.assertTrue(on_demand.status("inspect", "example.bam")["ready"])
            self.assertTrue(on_demand.status("inspect", "chip.txt")["ready"])
            self.assertTrue(on_demand.status("chip_vcf")["ready"])
            on_demand.kiri_sequence_tool.assert_called_with("chip_vcf")
            alignment = on_demand.status("bam_qc")
            self.assertTrue(alignment["ready"])
            self.assertTrue(all(r["installed"] for r in alignment["requirements"]))
            on_demand.kiri_sequence_tool.assert_called_with("bam_qc")

    def test_linux_file_is_installed_without_wsl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "mosdepth"
            blob.write_bytes(b"#!/bin/sh\necho mosdepth\n")
            with (
                mock.patch.object(on_demand, "ROOT", root),
                mock.patch.object(on_demand, "fetch", return_value=blob),
            ):
                result = on_demand.install_linux_local("mosdepth")
            target = root / "DNA_Software/Linux/bin/mosdepth"
            self.assertTrue(target.is_file())
            self.assertTrue(os.access(target, os.X_OK))
            self.assertIn("Linux file", result["status"])

    def test_native_alternative_never_installs_a_pinned_linux_x64_binary(self):
        with (
            mock.patch.object(on_demand, "uses_host_tool_packages", return_value=True),
            mock.patch.object(on_demand, "host_command", return_value=None),
            mock.patch.object(on_demand, "install_on_linux_host", return_value=None),
            mock.patch.object(on_demand, "install_linux_local") as pinned_install,
        ):
            with self.assertRaisesRegex(ValueError, "compatible host build"):
                on_demand.install("mosdepth")
            pinned_install.assert_not_called()

    def test_haplogrep_native_requires_the_expected_local_tree_before_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "haplogrep.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("haplogrep3.jar", b"test")
                bundle.writestr("tree.yaml", "id: synthetic")
            output = mock.Mock(
                returncode=0, stdout=b"Available trees: other", stderr=b""
            )
            with (
                mock.patch.object(on_demand, "ROOT", root),
                mock.patch.object(on_demand, "fetch", return_value=archive),
                mock.patch.object(
                    on_demand.shutil, "which", return_value="/usr/bin/java"
                ),
                mock.patch.object(
                    on_demand.subprocess, "run", return_value=output
                ) as run,
            ):
                wrapper = root / "DNA_Software/UserData/Launcher/Native/bin/haplogrep"
                with self.assertRaisesRegex(ValueError, "local reference tree"):
                    on_demand.install_native_haplogrep()
                self.assertFalse(wrapper.exists())
                output.stdout = b"Available trees: phylotree-fu-rcrs@1.3"
                self.assertEqual(
                    on_demand.install_native_haplogrep()["path"], str(wrapper)
                )
                self.assertEqual(run.call_args.args[0][-1], "trees")
                self.assertIn(' -jar ./haplogrep3.jar "$@"', wrapper.read_text())
                self.assertTrue(Path(run.call_args.args[0][0]).is_absolute())
                config = (
                    root
                    / "DNA_Software/UserData/Launcher/Native/Haplogrep/haplogrep3.yaml"
                )
                self.assertIn("repositories: []", config.read_text())
                self.assertIn(
                    "trees/phylotree-fu-rcrs/1.3/tree.yaml", config.read_text()
                )

    def test_wsl_arm64_plink_install_uses_native_package_and_checks_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(on_demand.os, "name", "nt"),
                mock.patch.object(
                    on_demand.hardware, "windows_arm64", return_value=True
                ),
                mock.patch.object(
                    on_demand, "linux_state", return_value={"running": True}
                ),
                mock.patch.object(on_demand, "extract_windows_companion") as companion,
                mock.patch.object(on_demand, "fetch") as fetch,
                mock.patch.object(on_demand, "LOG", Path(tmp)),
                mock.patch.object(
                    on_demand, "shell", return_value="install.log"
                ) as shell,
            ):
                on_demand.install("plink2")
                lines = shell.call_args.args[0]
                self.assertIn(
                    "apt-get install -y --no-install-recommends plink2", lines
                )
                self.assertIn(
                    "for flag in make-pgen make-king-table pca indep-pairwise export; do",
                    lines,
                )
                self.assertIn("ln -sfn /usr/bin/plink2 /opt/dna/bin/plink2", lines)
                companion.assert_not_called()
                fetch.assert_not_called()

    def test_windows_companion_extracts_the_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "samtools.zip"
            with zipfile.ZipFile(archive, "w") as packed:
                packed.writestr("samtools-1.23.1-windows-ucrt64/samtools.exe", b"MZ")
            with (
                mock.patch.object(on_demand, "ROOT", root),
                mock.patch.object(on_demand, "fetch", return_value=archive),
            ):
                result = on_demand.extract_windows_companion("samtools")
            found = list((root / "DNA_Software/Windows/Samtools").rglob("samtools.exe"))
            self.assertEqual(len(found), 1)
            self.assertIn("Windows file", result["status"])

    def test_place_archive_rejects_parent_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as packed:
                packed.writestr("../outside.txt", "nope")
            with self.assertRaises(ValueError):
                on_demand.place_archive(archive, root / "dest")

    def test_versions_page_matches_the_classifier(self):
        text = (
            Path(__file__)
            .resolve()
            .parents[2]
            .joinpath("docs/VERSIONS.md")
            .read_text(encoding="utf-8")
        )
        table = tool_hosts.markdown_table().strip()
        self.assertIn(table, text)

    def test_macos_launch_uses_system_open(self):
        job = object.__new__(engine.Job)
        with (
            mock.patch.object(engine.sys, "platform", "darwin"),
            mock.patch.object(engine.os, "name", "posix"),
            mock.patch.object(engine.subprocess, "run") as launch,
            mock.patch.object(job, "launch_native_tool") as native,
        ):
            job.task = {"core": "Explorer"}
            job.launch()
            launch.assert_called_once_with(
                ["/usr/bin/open", str(engine.ROOT / "Projects/Launcher")], check=True
            )
            job.task = {"core": "IGV"}
            job.launch()
            native.assert_called_once_with("igv")
            job.task = {"core": "Unsupported"}
            with self.assertRaisesRegex(ValueError, "no adapter"):
                job.launch()

    def test_macos_resolves_jbrowse_2_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "Applications/JBrowse 2.app"
            info = bundle / "Contents/Info.plist"
            info.parent.mkdir(parents=True)
            info.touch()
            with (
                mock.patch.object(system_tools.sys, "platform", "darwin"),
                mock.patch.object(system_tools.Path, "home", return_value=root),
            ):
                self.assertEqual(
                    system_tools.desktop_tool_command(root, "jbrowse"),
                    ["/usr/bin/open", "-a", str(bundle)],
                )

    def test_linux_arm64_uses_host_desktop_tool_instead_of_bundled_x64(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / "bin/ugene"
            file = root / "example file.fa"
            with (
                mock.patch.object(system_tools.sys, "platform", "linux"),
                mock.patch.object(
                    system_tools.platform, "machine", return_value="aarch64"
                ),
                mock.patch.object(system_tools.shutil, "which", return_value=str(tool)),
            ):
                self.assertEqual(
                    system_tools.desktop_tool_command(root, "ugene", file),
                    [str(tool), str(file.resolve())],
                )

    def test_publishing_an_already_installed_linux_binary_preserves_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "DNA_Software/Linux/bin/ugene"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"example")
            with mock.patch.object(on_demand, "ROOT", root):
                self.assertEqual(on_demand.publish_linux_bin(binary, "ugene"), binary)
            self.assertEqual(binary.read_bytes(), b"example")

    def test_native_launch_reports_nonzero_exit(self):
        job = object.__new__(engine.Job)
        with tempfile.TemporaryDirectory() as tmp:
            job.folder = Path(tmp)
            command = [str(job.folder / "ugene"), str(job.folder / "sequence.fa")]
            with (
                mock.patch.object(engine, "desktop_tool_command", return_value=command),
                mock.patch.object(engine.subprocess, "Popen") as spawn,
            ):
                spawn.return_value.wait.return_value = 1
                with self.assertRaisesRegex(RuntimeError, "could not start"):
                    job.launch_native_tool("ugene", command[1])
                self.assertEqual(spawn.call_args.args, (command,))
                self.assertTrue((job.folder / "software.log").is_file())

    def test_linux_status_checks_native_tools_without_wsl(self):
        with (
            mock.patch.object(on_demand.os, "name", "posix"),
            mock.patch.object(on_demand, "uses_host_tool_packages", return_value=False),
            mock.patch.object(on_demand, "host_tool_available", return_value=True),
            mock.patch.object(on_demand, "linux_state") as wsl,
        ):
            for task in ("igv", "bam_qc"):
                status = on_demand.status(task)
                self.assertFalse(status["needs_linux"])
                self.assertTrue(status["ready"])
            wsl.assert_not_called()

    def test_linux_bash_jobs_skip_the_windows_host(self):
        with mock.patch.object(engine.os, "name", "posix"):
            self.assertEqual(engine.wsl_host_bootstrap("inspect"), [])
            self.assertEqual(engine.wsl_host_bootstrap("sarek"), [])
        with (
            mock.patch.object(engine.os, "name", "nt"),
            mock.patch.object(
                engine, "windows_executable", return_value="powershell.exe"
            ),
        ):
            inspect = engine.wsl_host_bootstrap("inspect")
            sarek = engine.wsl_host_bootstrap("sarek")
        self.assertEqual(inspect[0][-1], "Start")
        self.assertEqual([step[-1] for step in sarek], ["Start", "Docker"])

    def test_missing_installation_snapshot_does_not_block_a_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(engine, "ROOT", Path(tmp)):
                recorded = engine.recorded_installation()
        self.assertFalse(recorded["recorded"])
        self.assertIn("PATH", recorded["note"])

    def test_synthetic_chip_inspect_writes_a_count(self):
        import linux_helpers

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "chip.txt"
            out = folder / "out"
            out.mkdir()
            source.write_text(
                "# DNAWorkbenchSynthetic=true\n"
                "# rsid\tchromosome\tposition\tgenotype\n"
                "rs900000001\t1\t3\tAC\n"
                "rs900000002\t1\t6\tAA\n",
                encoding="utf-8",
            )
            frame = linux_helpers.inspect_chip(source, out)
            stats = json.loads((out / "chip-statistics.json").read_text())
        self.assertEqual(stats["records"], 2)
        self.assertEqual(stats["called"], 2)
        self.assertEqual(stats["parser_build"], "synthetic-educational")
        self.assertEqual(len(frame), 2)
        self.assertIsNone(linux_helpers.synthetic_chip_rows(__file__))

    def test_linux_helpers_use_the_host_python_without_the_wsl_env(self):
        if os.name == "nt":
            self.skipTest("Windows jobs keep the WSL Python path")
        with mock.patch.object(Path, "is_file", return_value=False):
            self.assertEqual(engine.analysis_python(), engine.sys.executable)


if __name__ == "__main__":
    unittest.main()
