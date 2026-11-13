"""RFMix architecture guard and optional synthetic execution."""

import json
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import engine
import on_demand
import system_tools

ROOT = Path(__file__).resolve().parents[2]
MARCH = ROOT / "DNA_Software/Start/rfmix-march.sh"
RECIPE = ROOT / "DNA_Software/Start/kiri-rfmix.Dockerfile"
UPSTREAM_MAKE = (
    "CFLAGS += -ggdb -Wall -march=core2\nCXXFLAGS += -ggdb -Wall -march=core2\n"
)


def write_fixture(folder):
    """Phased synthetic chromosome. Populations are deliberately separable."""
    count = 80
    references = [f"A{i}" for i in range(1, 5)] + [f"B{i}" for i in range(1, 5)]

    def reference_call(sample, index):
        alternate = sample.startswith("B")
        if index % 17 == 0:
            alternate = not alternate
        return "1|1" if alternate else "0|0"

    def query_call(_sample, index):
        return "0|1" if index < count // 2 else "1|0"

    def vcf(path, samples, call):
        lines = [
            "##fileformat=VCFv4.2",
            "##source=DNAWorkbenchSynthetic",
            "##DNAWorkbenchSynthetic=true",
            "##reference=synthetic-educational-v1",
            "##contig=<ID=22,length=1000000>",
            "##FORMAT=<ID=GT,Number=1,Type=String,Description="
            '"Synthetic phased genotype">',
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
            + "\t".join(samples),
        ]
        for index in range(count):
            genotypes = "\t".join(call(sample, index) for sample in samples)
            lines.append(
                f"22\t{1000 + index * 1000}\tsynthetic_{index}\tA\tC\t60\tPASS\t.\tGT\t"
                + genotypes
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    vcf(folder / "query.vcf", ["Q1"], query_call)
    vcf(folder / "reference.vcf", references, reference_call)
    (folder / "samples.tsv").write_text(
        "".join(
            f"{sample}\t{'PopA' if sample.startswith('A') else 'PopB'}\n"
            for sample in references
        ),
        encoding="utf-8",
    )
    positions = list(range(0, count, 5)) + [count - 1]
    (folder / "map.tsv").write_text(
        "#chrom\tpos\tcm\n"
        + "".join(
            f"22\t{1000 + index * 1000}\t{index * 0.01:.4f}\n" for index in positions
        ),
        encoding="utf-8",
    )


class RfmixMarchTests(unittest.TestCase):
    def test_arm64_drops_core2_and_keeps_debug_flags(self):
        result, text = self._run("arm64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("-march=core2", text)
        self.assertIn("CFLAGS += -ggdb -Wall", text)
        self.assertIn("CXXFLAGS += -ggdb -Wall", text)

    def test_aarch64_uname_spelling_drops_core2(self):
        result, text = self._run("aarch64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("-march=core2", text)

    def test_amd64_keeps_the_upstream_flag(self):
        result, text = self._run("amd64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(text, UPSTREAM_MAKE)

    def test_x86_64_keeps_the_upstream_flag(self):
        result, text = self._run("x86_64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("-march=core2", text)

    def test_other_architectures_stop(self):
        result, _text = self._run("ppc64le")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("amd64 and arm64 only", result.stderr)

    def _run(self, architecture):
        if shutil.which("sh") is None:
            self.skipTest("sh is not on PATH")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Makefile.am").write_text(UPSTREAM_MAKE, encoding="utf-8")
            bindir = root / "bin"
            bindir.mkdir()
            dpkg = bindir / "dpkg"
            dpkg.write_text(
                "#!/bin/sh\n"
                '[ "$1" = "--print-architecture" ] && printf "%s\\n" '
                + architecture
                + "\n",
                encoding="utf-8",
            )
            dpkg.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                ["sh", str(MARCH)],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            return result, (root / "Makefile.am").read_text(encoding="utf-8")

    def test_image_recipe_and_wsl_lines_use_the_same_script(self):
        recipe = RECIPE.read_text(encoding="utf-8")
        self.assertIn("COPY rfmix-march.sh /tmp/rfmix-march.sh", recipe)
        self.assertIn("sh /tmp/rfmix-march.sh", recipe)
        self.assertIn(
            "1ca6db8b3e7abb64c7b0e3af44ade69244cf813468c24d687ea26f88a70a4f17",
            recipe,
        )
        lines = on_demand.rfmix_compile_lines(
            "/src", "/opt/rfmix", "/work/rfmix-march.sh"
        )
        self.assertIn("sh /work/rfmix-march.sh", "\n".join(lines))
        self.assertIn("autoreconf --force --install", lines)


class RfmixCommandTests(unittest.TestCase):
    def test_shell_requests_only_the_supported_thread_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Projects/Launcher/job"
            folder.mkdir(parents=True)
            inputs = folder / "inputs"
            inputs.mkdir()
            write_fixture(inputs)
            request = folder / "inputs.json"
            request.write_text(
                json.dumps(
                    {
                        "task": "rfmix",
                        "person": "Synthetic",
                        "inputs": {
                            "query": str(inputs / "query.vcf"),
                            "refpanel": str(inputs / "reference.vcf"),
                            "samplemap": str(inputs / "samples.tsv"),
                            "map": str(inputs / "map.tsv"),
                            "chrom": "22",
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(engine, "ROOT", root):
                job = engine.Job(request)
                try:
                    job.validate()
                    script = job.shell()
                finally:
                    job.log_handle.close()
        self.assertIn("--chromosome=22", script)
        self.assertIn("--n-threads=", script)
        self.assertNotIn("cuda", script.lower())
        self.assertNotIn("--gpus", script)


class RfmixImageBuildTests(unittest.TestCase):
    def test_unsupported_docker_exporter_builds_the_tag_directly(self):
        calls = []

        def run(command, **_kwargs):
            calls.append(list(command))
            if "--output" in command:
                return subprocess.CompletedProcess(
                    command,
                    1,
                    b"",
                    b"Docker exporter is not supported for the docker driver.\n",
                )
            return subprocess.CompletedProcess(command, 0, b"", b"")

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(on_demand.subprocess, "run", side_effect=run):
                on_demand.install_kiri_image(
                    ["docker", "--host", "unix:///run/kiri/docker.sock"],
                    {},
                    "kiri-rfmix.Dockerfile",
                    "dna-workbench/rfmix:1",
                    Path(tmp),
                )
        self.assertEqual(len(calls), 2)
        self.assertIn("--output", calls[0])
        self.assertNotIn("--output", calls[1])
        self.assertIn("-t", calls[1])
        self.assertIn("dna-workbench/rfmix:1", calls[1])
        self.assertNotIn("load", calls[1])

    def test_compile_failure_is_not_retried(self):
        def run(command, **_kwargs):
            return subprocess.CompletedProcess(command, 1, b"", b"make: error\n")

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(on_demand.subprocess, "run", side_effect=run) as mocked:
                with self.assertRaises(subprocess.CalledProcessError):
                    on_demand.install_kiri_image(
                        ["docker"],
                        {},
                        "kiri-rfmix.Dockerfile",
                        "dna-workbench/rfmix:1",
                        Path(tmp),
                    )
        self.assertEqual(mocked.call_count, 1)


class RfmixSmokeTests(unittest.TestCase):
    def test_requested_smoke_fails_without_the_engine(self):
        with (
            patch.dict(os.environ, {"DNA_RFMIX_SMOKE": "1"}),
            patch.object(on_demand, "kiri_docker", return_value=None),
        ):
            with self.assertRaisesRegex(AssertionError, "Docker socket"):
                self.test_engine_runs_the_synthetic_chromosome()

    def test_engine_runs_the_synthetic_chromosome(self):
        if os.environ.get("DNA_RFMIX_SMOKE") != "1":
            self.skipTest("Set DNA_RFMIX_SMOKE=1 to build and run the RFMix image.")
        if on_demand.kiri_docker() is None:
            self.fail("DNA_RFMIX_SMOKE=1 requires the local Kiri or Docker socket.")
        on_demand.install("rfmix", license_reviewed=True)
        route = system_tools.kiri_sequence_tool("rfmix")
        self.assertIsNotNone(route)
        machine = platform.machine().lower()
        expected = "linux/arm64" if machine in {"arm64", "aarch64"} else "linux/amd64"
        self.assertEqual(route.platform, expected)
        folder = ROOT / "Projects/Launcher/rfmix-smoke"
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        inputs = folder / "inputs"
        inputs.mkdir()
        write_fixture(inputs)
        request = folder / "inputs.json"
        request.write_text(
            json.dumps(
                {
                    "task": "rfmix",
                    "person": "Synthetic",
                    "inputs": {
                        "query": str(inputs / "query.vcf"),
                        "refpanel": str(inputs / "reference.vcf"),
                        "samplemap": str(inputs / "samples.tsv"),
                        "map": str(inputs / "map.tsv"),
                        "chrom": "22",
                    },
                }
            ),
            encoding="utf-8",
        )
        job = engine.Job(request)
        try:
            job.validate()
            job.run_with_kiri(route)
            log = job.log_path.read_text(encoding="utf-8")
        finally:
            job.log_handle.close()
        self.assertIn("RFMIX v2.03-r0", log)
        ancestry = (job.out / "lokale_ancestry.rfmix.Q").read_text(encoding="utf-8")
        self.assertIn("#sample\tPopA\tPopB", ancestry)
        row = next(
            line.split("\t")
            for line in ancestry.splitlines()
            if line.startswith("Q1\t")
        )
        first, second = float(row[1]), float(row[2])
        self.assertAlmostEqual(first + second, 1.0, places=3)
        self.assertGreater(first, 0.2)
        self.assertGreater(second, 0.2)
        segments = (job.out / "lokale_ancestry.msp.tsv").read_text(encoding="utf-8")
        self.assertIn("PopA=0", segments)
        self.assertIn("PopB=1", segments)
        self.assertTrue(any(line.startswith("22\t") for line in segments.splitlines()))
        forward = (job.out / "lokale_ancestry.fb.tsv").read_text(encoding="utf-8")
        self.assertIn("#reference_panel_population:\tPopA\tPopB", forward)
        print(
            "RFMIX_SMOKE "
            + json.dumps(
                {
                    "machine": machine,
                    "platform": route.platform,
                    "version": "v2.03-r0",
                    "sample": "Q1",
                    "pop_a": first,
                    "pop_b": second,
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
