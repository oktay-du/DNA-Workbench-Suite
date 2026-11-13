import unittest, tempfile, gzip, bz2, lzma, zipfile, tarfile, io, json
from pathlib import Path
import tool_contracts as c, source_store, suite_api, archive_io


class Contracts(unittest.TestCase):
    def test_docker_desktop_mount_preserves_host_path(self):
        import csv
        import engine

        with tempfile.TemporaryDirectory(prefix="dna, test ") as tmp:
            path = Path(tmp).resolve()
            mount = engine.kiri_bind(path, "/input", readonly=True, desktop=True)
        self.assertEqual(
            next(csv.reader([mount])),
            ["type=bind", "source=" + str(path), "target=/input", "readonly"],
        )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, name):
        return next(t for t in suite_api.CAT()["tasks"] if t["id"] == name)

    def gate(self, task, key, p):
        t = self.task(task)
        f = next(f for f in t["fields"] if f["key"] == key)
        m = {"kind": source_store.classify(p.name), **c.probe(p)}
        return c.evaluate(t, f, p, m)

    def vcf(self, version="4.2"):
        return (
            "##fileformat=VCFv"
            + version
            + "\n##reference=GRCh38\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t1\t.\tA\tG\t.\tPASS\t.\n"
        ).encode()

    def test_every_file_field_has_explicit_contract(self):
        for t in suite_api.CAT()["tasks"]:
            for f in t["fields"]:
                if f["kind"] == "file":
                    self.assertTrue(c.contract(t, f)["formats"], (t["id"], f["key"]))

    def test_gzip_vcf_direct_zip_not_direct_for_vcf_tool(self):
        p = self.root / "sample.vcf.gz"
        p.write_bytes(gzip.compress(self.vcf()))
        self.assertTrue(self.gate("vcf_qc", "vcf", p)["accepted"])
        self.assertEqual(c.probe(p)["format_version"], "VCFv4.2")
        z = self.root / "sample.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("sample.vcf", self.vcf())
        r = self.gate("vcf_qc", "vcf", z)
        self.assertFalse(r["accepted"])
        self.assertIn("batch_extract", r["remedies"])

    def test_future_version_is_unverified_not_silently_accepted(self):
        p = self.root / "future.vcf"
        p.write_bytes(self.vcf("9.0"))
        r = self.gate("vcf_qc", "vcf", p)
        self.assertFalse(r["accepted"])
        self.assertIn("validate_format_version", r["remedies"])

    def test_truncated_gzip_and_fake_extension_fail(self):
        p = self.root / "broken.vcf.gz"
        p.write_bytes(gzip.compress(self.vcf())[:-8])
        self.assertFalse(self.gate("vcf_qc", "vcf", p)["accepted"])
        p = self.root / "fake.vcf"
        p.write_text("not a VCF")
        self.assertFalse(self.gate("vcf_qc", "vcf", p)["accepted"])

    def test_single_chip_zip_only_and_multi_payload_requires_batch(self):
        p = self.root / "chip.zip"
        with zipfile.ZipFile(p, "w") as f:
            f.writestr("raw.txt", "rsid chromosome position genotype")
        self.assertTrue(self.gate("chip_vcf", "file", p)["accepted"])
        with zipfile.ZipFile(p, "a") as f:
            f.writestr("second.txt", "other")
        self.assertFalse(self.gate("chip_vcf", "file", p)["accepted"])

    def test_bcf_only_supported_by_declared_adapters(self):
        p = self.root / "x.bcf"
        p.write_bytes(gzip.compress(b"BCF\x02\x02" + b"header"))
        self.assertTrue(self.gate("vcf_qc", "vcf", p)["accepted"])
        self.assertFalse(self.gate("pharmcat", "vcf", p)["accepted"])

    def test_reference_must_be_decoded_and_pgen_sidecars_required(self):
        p = self.root / "ref.fa.gz"
        p.write_bytes(gzip.compress(b">chr1\nACGT\n"))
        self.assertFalse(self.gate("normalize", "reference", p)["accepted"])
        p = self.root / "cohort.pgen"
        p.write_bytes(b"plink")
        self.assertFalse(self.gate("pca", "file", p)["accepted"])
        p.with_suffix(".psam").write_text("#IID")
        p.with_suffix(".pvar").write_text("#CHROM")
        self.assertTrue(self.gate("pca", "file", p)["accepted"])

    def test_archives_keep_outer_and_inner_names_and_sidecar_stems(self):
        p = self.root / "Oktay_genome_2026.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("lane/file.vcf.gz", gzip.compress(self.vcf()))
            z.writestr("lane/file.vcf.gz.tbi", b"index")
        rows = archive_io.unpack(p, self.root / "out")
        names = {Path(x).name for x in rows}
        self.assertIn("Oktay_genome_2026__file.vcf.gz", names)
        self.assertIn("Oktay_genome_2026__file.vcf.gz.tbi", names)
        self.assertTrue(p.exists())
        self.assertIn("lane/file.vcf.gz", rows.values())

    def test_zip_slip_and_case_collision_rejected(self):
        for names in [(".." + "/escape.txt",), ("A.txt", "a.txt")]:
            p = self.root / ("bad" + str(len(names)) + ".zip")
            with zipfile.ZipFile(p, "w") as z:
                for n in names:
                    z.writestr(n, "hello")
            with self.assertRaises(ValueError):
                archive_io.unpack(p, self.root / ("out" + str(len(names))))
        self.assertFalse((self.root / "escape.txt").exists())

    def test_single_streams_and_tar_extracted_checked(self):
        for ext, encode in [
            (".gz", gzip.compress),
            (".bz2", bz2.compress),
            (".xz", lzma.compress),
        ]:
            p = self.root / ("sample.vcf" + ext)
            p.write_bytes(encode(self.vcf()))
            rows = archive_io.unpack(p, self.root / ("out" + ext))
            self.assertEqual(next(Path(x).read_bytes() for x in rows), self.vcf())
        p = self.root / "reads.tar.gz"
        with tarfile.open(p, "w:gz") as z:
            data = b"@r\nACGT\n+\nIIII\n"
            m = tarfile.TarInfo("R1.fastq")
            m.size = len(data)
            z.addfile(m, io.BytesIO(data))
        rows = archive_io.unpack(p, self.root / "tarout")
        self.assertEqual(next(iter(rows.values())), "R1.fastq")

    def test_tar_symlinks_not_followed(self):
        p = self.root / "bad.tar"
        with tarfile.open(p, "w") as z:
            m = tarfile.TarInfo("link")
            m.type = tarfile.SYMTYPE
            m.linkname = "../../elsewhere"
            z.addfile(m)
        with self.assertRaises(ValueError):
            archive_io.unpack(p, self.root / "out")

    def test_unsupported_archive_is_explicit_not_fake_success(self):
        p = self.root / "x.7z"
        p.write_bytes(b"7z\xbc\xaf\x27\x1c")
        self.assertEqual(c.probe(p)["compression"], "7z")
        with self.assertRaisesRegex(ValueError, "no installed portable"):
            archive_io.unpack(p, self.root / "out")

    def test_cancelled_extraction_preserves_source(self):
        p = self.root / "cancel.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("raw.txt", "payload")
        with self.assertRaises(InterruptedError):
            archive_io.unpack(p, self.root / "out", lambda: True)
        self.assertTrue(p.exists())
        self.assertFalse(list((self.root / "out").glob("*.extracting")))

    def test_repacking_is_explicit_and_does_not_change_reference(self):
        import engine, json
        from unittest.mock import patch

        root = self.root / "suite"
        folder = root / "Projects/Launcher/P1/convert"
        folder.mkdir(parents=True)
        vcf = self.root / "source.vcf"
        vcf.write_bytes(self.vcf())
        req = folder / "inputs.json"
        req.write_text(
            json.dumps(
                {
                    "task": "variant_convert",
                    "person": "P1",
                    "inputs": {"vcf": str(vcf), "output_format": "VCF.gz (BGZF)"},
                }
            )
        )
        with patch.object(engine, "ROOT", root):
            job = engine.Job(req)
            try:
                job.validate()
                command = job.shell()
            finally:
                job.log_handle.close()
        self.assertIn("bcftools view -Oz", command)
        self.assertNotIn("liftover", command)
        self.assertNotIn("bcftools norm", command)

    def test_sarek_writes_schema_compatible_samplesheet(self):
        import csv
        import engine
        import on_demand
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.task = {"action": "sarek"}
        job.person = "P001_Ich"
        job.v = {
            "reference": str(self.root / "reference.fa"),
            "r1": str(self.root / "Read One.fastq.gz"),
            "r2": str(self.root / "Read Two.fastq"),
            "sex": "XX",
            "caller": "haplotypecaller",
        }
        with (
            patch.object(
                on_demand,
                "native_pipeline_docker_socket",
                return_value="/run/docker.sock",
            ),
            patch.object(on_demand, "host_command", return_value="/opt/nextflow"),
        ):
            script = job.shell()
        with (self.root / "samplesheet.csv").open(
            newline="", encoding="utf-8"
        ) as sheet:
            sample = next(csv.DictReader(sheet))
        self.assertEqual(sample["sample"], "P001_Ich")
        self.assertEqual(sample["sex"], "XX")
        self.assertEqual(sample["fastq_1"], job.o("r1.fastq.gz"))
        self.assertEqual(sample["fastq_2"], job.o("r2.fastq.gz"))
        self.assertIn("gzip -c -- ", script)
        self.assertIn("-params-file", script)
        self.assertEqual(
            json.loads((self.root / "sarek-params.json").read_text()),
            {"genome": None, "igenomes_ignore": True},
        )
        self.assertIn("nextflow-work", script)

    def test_pgs_samplesheet_uses_alphanumeric_sampleset(self):
        import csv
        from linux_helpers import score_sheet

        score_sheet("/job/genotypes", "P001_Ich", self.root)
        with (self.root / "samplesheet.csv").open(newline="") as sheet:
            sample = next(csv.DictReader(sheet))
        self.assertEqual(sample["sampleset"], "P001Ich")
        self.assertEqual(sample["path_prefix"], "/job/genotypes")

    def test_kiri_conversion_limits_mounts_and_publishes_expected_files(self):
        import csv
        import engine
        from unittest.mock import patch

        source = self.root / "synthetic, sample.vcf"
        source.write_bytes(self.vcf())
        results = self.root / "Results"
        results.mkdir()
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = results
        job.task = {"action": "variant_convert"}
        job.v = {"vcf": str(source), "output_format": "BCF"}
        prefix = ["docker", "--host", "local-kiri"]
        image_id = "sha256:" + "a" * 64

        def run(args, *, env, cancel_command):
            self.assertEqual(args[:4], [*prefix, "run"])
            self.assertIn("--pull=never", args)
            self.assertIn("--platform=linux/arm64", args)
            self.assertIn("--network=none", args)
            self.assertIn("--read-only", args)
            self.assertIn("--cap-drop=ALL", args)
            self.assertEqual(
                cancel_command, [*prefix, "rm", "-f", args[args.index("--name") + 1]]
            )
            mounts = [
                next(csv.reader([args[i + 1]]))
                for i, arg in enumerate(args)
                if arg == "--mount"
            ]
            self.assertEqual(
                mounts[1],
                [
                    "type=bind",
                    "source=" + engine.linux(source),
                    "target=/input",
                    "readonly",
                ],
            )
            self.assertEqual(mounts[0][-1], "target=/output")
            self.assertEqual(len(mounts), 2)
            self.assertIn(image_id, args)
            staging = next(
                p for p in self.root.iterdir() if p.is_dir() and p != results
            )
            (staging / "converted.bcf").write_bytes(b"BCF")
            (staging / "conversion_stats.txt").write_bytes(b"stats")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run, create=True),
        ):
            job.run_with_kiri((prefix, {}, "linux/arm64", image_id))
        self.assertEqual((results / "converted.bcf").read_bytes(), b"BCF")
        self.assertEqual((results / "conversion_stats.txt").read_bytes(), b"stats")
        self.assertEqual(source.read_bytes(), self.vcf())

    def test_kiri_fastq_report_preserves_gzip_suffix_for_paired_reads(self):
        import engine
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "fastq_report"}
        job.v = {
            "r1": str(self.root / "R 1.fastq.gz"),
            "r2": str(self.root / "R 2.fastq"),
        }

        def run(args, **kwargs):
            self.assertIn("--in1 /read1.gz", args[-1])
            self.assertIn("--in2 /read2", args[-1])
            self.assertTrue(any("target=/read1.gz,readonly" in arg for arg in args))
            staging = next(
                p for p in self.root.iterdir() if p.is_dir() and p != job.out
            )
            for filename in ("fastq_quality.html", "fastq_quality.json"):
                (staging / filename).write_text("synthetic")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
        self.assertEqual(
            {p.name for p in job.out.iterdir()},
            {"fastq_quality.html", "fastq_quality.json"},
        )

    def test_kiri_normalization_checks_build_before_launch(self):
        import engine
        from unittest.mock import patch

        source = self.root / "sample.vcf"
        source.write_bytes(
            self.vcf().replace(
                b"##fileformat=VCFv4.2", b"##fileformat=VCFv4.2\n##reference=GRCh38"
            )
        )
        reference = self.root / "reference.fa"
        reference.write_text(">chr1\nACTG\n")
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "normalize"}
        job.v = {"vcf": str(source), "reference": str(reference), "build": "GRCh37"}
        route = (["docker"], {}, "linux/arm64", "image")
        with patch.object(job, "run_process") as run:
            with self.assertRaisesRegex(ValueError, "GRCh38"):
                job.run_with_kiri(route)
            run.assert_not_called()

        job.v["build"] = "GRCh38"
        names = {"normalisiert.vcf.gz", "normalisiert.vcf.gz.tbi", "referenz.fa.fai"}

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertTrue(any("target=/reference,readonly" in arg for arg in args))
            self.assertIn("samtools faidx referenz.fa", args[-1])
            self.assertIn("--check-ref e", args[-1])
            staging = next(
                p for p in self.root.iterdir() if p.is_dir() and p != job.out
            )
            for name in names:
                (staging / name).write_text("synthetic")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            job.run_with_kiri(route)
        self.assertEqual({p.name for p in job.out.iterdir()}, names)

    def test_filter_expression_preserves_thresholds(self):
        from engine import variant_filter_options

        self.assertEqual(variant_filter_options({"pass_only": "All entries"}), [])
        self.assertEqual(
            variant_filter_options({"pass_only": "PASS only", "dp": "12", "gq": 30}),
            ["-i", 'FILTER="PASS" && FMT/DP>=12 && FMT/GQ>=30'],
        )
        with self.assertRaisesRegex(ValueError, "at least 0"):
            variant_filter_options({"dp": -1})

    def test_kiri_merge_preserves_source_order_and_sample_maps(self):
        import engine
        from unittest.mock import patch

        sources = [self.root / name for name in ("first.vcf", "second, input.vcf")]
        for source in sources:
            source.write_bytes(self.vcf())
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "merge"}
        job.v = {"files": [str(p) for p in sources], "build": "GRCh38"}
        route = (["docker"], {}, "linux/arm64", "image")
        result = "getrennte_proben.vcf.gz"

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            for i in (1, 2):
                self.assertTrue(
                    any(f"target=/input_{i},readonly" in arg for arg in args)
                )
                self.assertIn(f"prefix=Source{i}", args[-1])
                self.assertIn(f"bcftools query -l quelle_{i}.vcf.gz", args[-1])
            self.assertIn(
                f"-m none -Oz -o {result} benannt_1.vcf.gz benannt_2.vcf.gz", args[-1]
            )
            staging = next(
                p for p in self.root.iterdir() if p.is_dir() and p != job.out
            )
            (staging / result).write_bytes(b"vcf")
            (staging / (result + ".tbi")).write_bytes(b"index")
            for i in (1, 2):
                sub = staging / f"Source__{i}"
                sub.mkdir()
                (sub / "neue_probennamen.txt").write_text(f"Source{i}_S1\n")
                (sub / "probenzuordnung.tsv").write_text(
                    f"Original\tLauncher_Name\nsame\tSource{i}_S1\n"
                )
                for name in (f"quelle_{i}.vcf.gz", f"benannt_{i}.vcf.gz"):
                    (staging / name).write_bytes(b"vcf")
                    (staging / (name + ".tbi")).write_bytes(b"index")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            sources[1].write_bytes(self.vcf().replace(b"GRCh38", b"GRCh37"))
            with self.assertRaisesRegex(ValueError, "GRCh37"):
                job.run_with_kiri(route)
            process.assert_not_called()
            sources[1].write_bytes(self.vcf())
            job.run_with_kiri(route)
        self.assertTrue((job.out / (result + ".tbi")).is_file())
        for i in (1, 2):
            mapping = job.out / f"Source__{i}" / "probenzuordnung.tsv"
            self.assertIn(f"same\tSource{i}_S1", mapping.read_text())

    def test_kiri_cram_qc_requires_reference_and_publishes_indices_and_report(self):
        import engine
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "bam_qc"}
        job.v = {"bam": str(self.root / "sample.cram")}
        route = (["docker"], {}, "linux/arm64", "image")
        with self.assertRaisesRegex(ValueError, "matching reference"):
            job.run_with_kiri(route)
        job.v["reference"] = str(self.root / "reference.fa")
        output_files = (
            "reads.cram.crai",
            "referenz.fa.fai",
            "flagstat.txt",
            "samtools_stats.txt",
            "abdeckung.mosdepth.global.dist.txt",
            "abdeckung.mosdepth.summary.txt",
            "qualitaetsbericht/multiqc_report.html",
            "qualitaetsbericht/multiqc_data/multiqc_sources.txt",
        )

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertTrue(any("target=/alignment,readonly" in arg for arg in args))
            self.assertTrue(any("target=/reference,readonly" in arg for arg in args))
            command = args[-1]
            self.assertIn("samtools faidx referenz.fa", command)
            self.assertIn("samtools index reads.cram", command)
            self.assertIn("--fasta referenz.fa abdeckung reads.cram", command)
            self.assertIn("multiqc flagstat.txt samtools_stats.txt", command)
            staging = next(
                p for p in self.root.iterdir() if p.is_dir() and p != job.out
            )
            for filename in output_files:
                path = staging / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            job.run_with_kiri(route)
        self.assertEqual(
            {
                p.relative_to(job.out).as_posix()
                for p in job.out.rglob("*")
                if p.is_file()
            },
            set(output_files),
        )

    def test_kiri_plink_jobs_publish_the_same_named_results(self):
        import engine
        from unittest.mock import patch

        source = self.root / "sample.vcf"
        source.write_bytes(self.vcf())
        actions = {
            "roh": (
                "--homozyg --out roh",
                "roh_input.bed roh_input.bim roh_input.fam roh_input.log "
                "roh.hom roh.hom.indiv roh.hom.summary roh.log",
            ),
            "kinship": (
                "--make-king-table --out verwandtschaft",
                "familie.pgen familie.pvar familie.psam familie.log "
                "verwandtschaft.kin0 verwandtschaft.log",
            ),
        }
        for action, (option, files) in actions.items():
            with self.subTest(action=action):
                job = engine.Job.__new__(engine.Job)
                job.folder = self.root / action
                job.out = job.folder / "Results"
                job.out.mkdir(parents=True)
                job.task = {"action": action}
                job.v = {"vcf": str(source)}

                def run(args, **kwargs):
                    self.assertIn(option, args[-1])
                    self.assertTrue(
                        any("target=/input,readonly" in arg for arg in args)
                    )
                    stage = next(p for p in job.folder.iterdir() if p != job.out)
                    for filename in files.split():
                        (stage / filename).write_text("synthetic")

                with (
                    patch.object(job, "log"),
                    patch.object(job, "run_process", side_effect=run),
                ):
                    job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
                self.assertEqual(
                    {p.name for p in job.out.iterdir()}, set(files.split())
                )

    def test_kiri_pca_mounts_only_selected_pgen_sidecars(self):
        import engine
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "pca"}
        source = self.root / "cohort.pgen"
        labels = self.root / "labels.tsv"
        for path in (
            source,
            source.with_suffix(".psam"),
            source.with_suffix(".pvar.zst"),
            labels,
        ):
            path.touch()
        job.v = {"file": str(source), "labels": str(labels)}
        files = {
            "kohorte.pgen",
            "kohorte.pvar",
            "kohorte.psam",
            "kohorte.log",
            "ld.prune.in",
            "ld.log",
            "pca_k.txt",
            "pca.eigenval",
            "pca.eigenvec",
            "pca.log",
            "pca_interaktiv.html",
            "pca_mit_metadaten.tsv",
        }

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertEqual(args.count("--mount"), 6)
            for target in (
                "/cohort.pgen",
                "/cohort.psam",
                "/cohort.pvar.zst",
                "/labels",
                "/pca_helpers.py",
            ):
                self.assertTrue(any(f"target={target},readonly" in arg for arg in args))
            self.assertIn("--pfile /cohort vzs", args[-1])
            self.assertIn("pca_plot pca.eigenvec /labels", args[-1])
            stage = next(p for p in self.root.iterdir() if p.is_dir() and p != job.out)
            for name in files:
                (stage / name).write_text("synthetic")
            (stage / "pca_mode.txt").touch()

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
        self.assertEqual({p.name for p in job.out.iterdir()}, files | {"pca_mode.txt"})

    def test_kiri_beagle_passes_reference_and_keeps_imputation_disabled(self):
        import engine
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "beagle"}
        job.v = {
            "vcf": str(self.root / "cohort.vcf.bgz"),
            "map": str(self.root / "chr1.map"),
            "refpanel": str(self.root / "panel.vcf.gz"),
            "chrom": "1",
        }

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertIn("gt=/input.vcf.gz", args[-1])
            self.assertIn("map=/map", args[-1])
            self.assertIn("ref=/panel.vcf.gz", args[-1])
            self.assertIn("impute=false", args[-1])
            for target in ("/input.vcf.gz", "/map", "/panel.vcf.gz"):
                self.assertTrue(any(f"target={target},readonly" in arg for arg in args))
            stage = next(p for p in self.root.iterdir() if p.is_dir() and p != job.out)
            for name in ("phasiert.vcf.gz", "phasiert.log"):
                (stage / name).write_text("synthetic")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
        self.assertEqual(
            {p.name for p in job.out.iterdir()}, {"phasiert.vcf.gz", "phasiert.log"}
        )

    def test_kiri_hap_ibd_preserves_gzip_input_and_all_three_outputs(self):
        import engine
        from unittest.mock import patch

        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "ibd"}
        job.v = {
            "vcf": str(self.root / "cohort.vcf.bgz"),
            "map": str(self.root / "chr1.map"),
        }
        outputs = {"segmente.ibd.gz", "segmente.hbd.gz", "segmente.log"}

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertIn("gt=/input.vcf.gz map=/map out=segmente nthreads=", args[-1])
            self.assertEqual(args.count("--mount"), 3)
            for target in ("/input.vcf.gz", "/map"):
                self.assertTrue(any(f"target={target},readonly" in arg for arg in args))
            stage = next(p for p in self.root.iterdir() if p.is_dir() and p != job.out)
            for name in outputs - {"segmente.hbd.gz"}:
                (stage / name).write_text("synthetic")
            if complete:
                (stage / "segmente.hbd.gz").write_bytes(gzip.compress(b""))

        route = (["docker"], {}, "linux/arm64", "image")
        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run),
        ):
            complete = False
            with self.assertRaisesRegex(RuntimeError, "expected result files"):
                job.run_with_kiri(route)
            self.assertFalse(list(job.out.iterdir()))
            complete = True
            job.run_with_kiri(route)
        self.assertEqual({p.name for p in job.out.iterdir()}, outputs)

    def test_kiri_reference_export_mounts_selected_panel_files(self):
        import engine
        from unittest.mock import patch

        panel = self.root / "References/HGDP_GRCh38/hgdp_statphase"
        panel.parent.mkdir(parents=True)
        for suffix in (".pgen", ".pvar.zst", ".psam"):
            panel.with_suffix(suffix).write_text("synthetic")
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "ref_export"}
        job.v = {"panel": "HGDP GRCh38", "chrom": "22"}
        route = (["docker"], {}, "linux/arm64", "image")
        names = {
            "referenz_chr22.vcf.gz",
            "referenz_chr22.vcf.gz.tbi",
            "referenz_chr22.log",
        }

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertEqual(args.count("--mount"), 4)
            for suffix in (".pgen", ".pvar.zst", ".psam"):
                self.assertTrue(
                    any(
                        f"source={engine.linux(panel.with_suffix(suffix))},target=/panel{suffix},readonly"
                        in arg
                        for arg in args
                    )
                )
            self.assertIn("--pfile /panel vzs --chr 22", args[-1])
            self.assertIn("-ft referenz_chr22.vcf.gz", args[-1])
            stage = next(
                p
                for p in self.root.iterdir()
                if p not in {job.out, self.root / "References"}
            )
            for name in names:
                (stage / name).write_text("synthetic")

        with (
            patch.object(engine, "ROOT", self.root),
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            job.v["panel"] = "1000 Genomes GRCh38"
            with self.assertRaisesRegex(ValueError, "not installed or incomplete"):
                job.run_with_kiri(route)
            process.assert_not_called()
            job.v["panel"] = "HGDP GRCh38"
            job.run_with_kiri(route)
        self.assertEqual({p.name for p in job.out.iterdir()}, names)

    def test_kiri_peddy_accepts_a_report_without_sex_chromosome_results(self):
        import engine
        from unittest.mock import patch

        source = self.root / "sample.vcf"
        source.write_bytes(self.vcf())
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "peddy"}
        job.v = {
            "vcf": str(source),
            "ped": str(self.root / "family.ped"),
            "build": "GRCh38",
        }
        results = {
            "peddy_input.vcf.gz",
            "peddy_input.vcf.gz.tbi",
            "familien_qc.html",
            "familien_qc.peddy.ped",
            "familien_qc.het_check.csv",
            "familien_qc.ped_check.csv",
            "familien_qc.background_pca.json",
        }

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertTrue(any("target=/pedigree,readonly" in arg for arg in args))
            self.assertIn("--sites hg38 --prefix familien_qc", args[-1])
            stage = next(p for p in self.root.iterdir() if p.is_dir() and p != job.out)
            for name in results:
                (stage / name).write_text("synthetic")

        route = (["docker"], {}, "linux/arm64", "image")
        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            job.v["build"] = "GRCh37"
            with self.assertRaisesRegex(ValueError, "GRCh38"):
                job.run_with_kiri(route)
            process.assert_not_called()
            job.v["build"] = "GRCh38"
            job.run_with_kiri(route)
        self.assertEqual({p.name for p in job.out.iterdir()}, results)

    def test_kiri_whatshap_creates_local_cram_and_reference_indices(self):
        import engine
        from unittest.mock import patch

        source = self.root / "sample.vcf.gz"
        source.write_bytes(gzip.compress(self.vcf()))
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "whatshap"}
        job.v = {
            "vcf": str(source),
            "alignment": str(self.root / "sample.cram"),
            "reference": str(self.root / "reference.fa.bgz"),
            "build": "GRCh38",
        }
        outputs = {"read_phased.vcf", "phase_stats.tsv"}

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            for target in ("/input.vcf.gz", "/alignment", "/reference"):
                self.assertTrue(any(f"target={target},readonly" in arg for arg in args))
            self.assertIn("samtools faidx reference.fa.gz", args[-1])
            self.assertIn(
                "reads.cram && whatshap phase --reference reference.fa.gz", args[-1]
            )
            stage = next(p for p in self.root.iterdir() if p.is_dir() and p != job.out)
            for name in outputs | {"reads.cram.crai", "reference.fa.gz.fai"}:
                (stage / name).write_text("synthetic")

        with (
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            job.v["build"] = "GRCh37"
            with self.assertRaisesRegex(ValueError, "GRCh38"):
                job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
            process.assert_not_called()
            job.v["build"] = "GRCh38"
            job.run_with_kiri((["docker"], {}, "linux/arm64", "image"))
        self.assertEqual({p.name for p in job.out.iterdir()}, outputs)

    def test_kiri_variant_comparison_and_lineage_jobs(self):
        import engine
        from unittest.mock import patch

        cases = {
            "truvari": (
                {"base": "base.vcf", "comparison": "other.vcf", "reference": "ref.fa"},
                "samtools faidx reference.fa && truvari bench",
                (
                    "sv_basis.vcf.gz",
                    "sv_basis.vcf.gz.tbi",
                    "sv_vergleich.vcf.gz",
                    "sv_vergleich.vcf.gz.tbi",
                    "sv_vergleichsergebnis/summary.json",
                ),
            ),
            "mito": (
                {"vcf": "mt.vcf"},
                "--tree phylotree-fu-rcrs@1.3",
                ("mt_input.vcf.gz", "mt_input.vcf.gz.tbi", "haplogroups.txt"),
            ),
            "yhaplo": (
                {"vcf": "y.vcf"},
                "yhaplo -i y_input.vcf.gz -o yhaplo -aao",
                (
                    "y_input.vcf.gz",
                    "y_input.vcf.gz.tbi",
                    "yhaplo/haplogroups.y_input.txt",
                ),
            ),
            "pharmcat": (
                {"vcf": "pharm.vcf"},
                "-o pharmcat -bf pharmakogenetik",
                ("pharmcat/pharmakogenetik.report.html",),
            ),
            "gatk_validate": (
                {"vcf": "input.vcf", "reference": "reference.fa"},
                "--validation-type-to-exclude IDS",
                ("referenz.fa.fai", "referenz.dict"),
            ),
            "compare": (
                {"a": "one.vcf", "b": "two.vcf"},
                "/helpers.py compare /a.vcf /b.vcf GRCh37 GRCh37",
                ("konflikte.tsv", "vergleich.json", "report.html"),
            ),
        }
        route = (["docker"], {}, "linux/arm64", "image")
        for action, (inputs, expected_command, outputs) in cases.items():
            with self.subTest(action=action):
                job = engine.Job.__new__(engine.Job)
                job.folder = self.root / action
                job.out = job.folder / "Results"
                job.out.mkdir(parents=True)
                job.task = {"action": action}
                build = "GRCh38" if action == "pharmcat" else "GRCh37"
                job.v = {"build": build, "build_a": build, "build_b": build}
                for key, name in inputs.items():
                    path = job.folder / name
                    path.write_bytes(self.vcf().replace(b"GRCh38", build.encode()))
                    job.v[key] = str(path)

                def run(args, **kwargs):
                    self.assertIn("--network=none", args)
                    self.assertIn(expected_command, args[-1])
                    self.assertEqual(
                        sum(arg.endswith(",readonly") for arg in args),
                        len(inputs) + (action == "compare"),
                    )
                    stage = next(
                        p for p in job.folder.iterdir() if p.is_dir() and p != job.out
                    )
                    for name in outputs:
                        output = stage / name
                        output.parent.mkdir(exist_ok=True)
                        output.write_text("synthetic")

                with (
                    patch.object(job, "log"),
                    patch.object(job, "run_process", side_effect=run) as process,
                ):
                    if action in {"truvari", "yhaplo"}:
                        job.v["build"] = "GRCh38"
                        with self.assertRaisesRegex(ValueError, "GRCh37"):
                            job.run_with_kiri(route)
                        process.assert_not_called()
                        job.v["build"] = "GRCh37"
                    job.run_with_kiri(route)
                self.assertEqual(
                    {
                        p.relative_to(job.out).as_posix()
                        for p in job.out.rglob("*")
                        if p.is_file()
                    },
                    set(outputs),
                )

    def test_kiri_vep_uses_only_the_versioned_cache_and_input(self):
        import engine
        from unittest.mock import patch

        cache = self.root / "References/VEP/homo_sapiens/116_GRCh38"
        cache.mkdir(parents=True)
        source = self.root / "sample.vcf"
        source.write_bytes(self.vcf())
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "vep"}
        job.v = {"vcf": str(source), "build": "GRCh38"}
        route = (["docker"], {}, "linux/arm64", "image")

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertIn(
                "--offline --cache --dir_cache /cache --cache_version 116 --assembly GRCh38",
                args[-1],
            )
            self.assertTrue(
                any(
                    "target=/cache/homo_sapiens/116_GRCh38,readonly" in arg
                    for arg in args
                )
            )
            self.assertEqual(args.count("--mount"), 3)
            stage = next(
                p
                for p in self.root.iterdir()
                if p.is_dir() and p.name not in {"Results", "References"}
            )
            (stage / "vep_annotation.vcf").write_bytes(self.vcf())

        with (
            patch.object(engine, "ROOT", self.root),
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            with self.assertRaisesRegex(ValueError, "116 GRCh38 cache"):
                job.run_with_kiri(route)
            process.assert_not_called()
            (cache / "info.txt").touch()
            (cache / "1").mkdir()
            (cache / "1/1-1000000.gz").touch()
            job.run_with_kiri(route)
        self.assertEqual((job.out / "vep_annotation.vcf").read_bytes(), self.vcf())

    def test_kiri_opencravat_checks_module_data_and_keeps_reports(self):
        import engine
        from unittest.mock import patch

        modules = self.root / "References/OpenCRAVAT/modules"
        for category, name in (
            ("converters", "vcf-converter"),
            ("mappers", "hg38"),
            ("reporters", "textreporter"),
            ("reporters", "excelreporter"),
            ("annotators", "clinvar"),
            ("annotators", "gnomad4"),
            ("postaggregators", "tagsampler"),
            ("postaggregators", "casecontrol"),
            ("postaggregators", "varmeta"),
            ("postaggregators", "vcfinfo"),
        ):
            path = modules / category / name / (name + ".yml")
            path.parent.mkdir(parents=True)
            path.touch()
        clinvar = modules / "annotators/clinvar/data"
        clinvar.mkdir()
        (clinvar / "clinvar.sqlite").touch()
        gnomad = modules / "annotators/gnomad4/data"
        gnomad.mkdir()
        for chrom in (*range(1, 23), "X"):
            (gnomad / f"chr{chrom}.vcf.gz").touch()
            if chrom != "X":
                (gnomad / f"chr{chrom}.vcf.gz.tbi").touch()
        source = self.root / "sample.vcf"
        source.write_bytes(self.vcf())
        job = engine.Job.__new__(engine.Job)
        job.folder = self.root
        job.out = self.root / "Results"
        job.out.mkdir()
        job.task = {"action": "opencravat_run"}
        job.v = {"vcf": str(source), "build": "GRCh38"}
        route = (["docker"], {}, "linux/arm64", "image")

        def run(args, **kwargs):
            self.assertIn("--network=none", args)
            self.assertTrue(any("target=/modules,readonly" in arg for arg in args))
            self.assertIn("OPENCRAVAT_MD=/modules", args[-1])
            self.assertIn("-l hg38 -a clinvar gnomad4", args[-1])
            stage = next(
                p
                for p in self.root.iterdir()
                if p.is_dir() and p.name not in {"Results", "References"}
            )
            for name in ("varianten.sqlite", "varianten.xlsx"):
                (stage / "annotation" / name).write_text("synthetic")

        with (
            patch.object(engine, "ROOT", self.root),
            patch.object(job, "log"),
            patch.object(job, "run_process", side_effect=run) as process,
        ):
            with self.assertRaisesRegex(ValueError, "OpenCRAVAT modules"):
                job.run_with_kiri(route)
            process.assert_not_called()
            (gnomad / "chrX.vcf.gz.csi").touch()
            job.run_with_kiri(route)
        self.assertEqual(
            {p.name for p in (job.out / "annotation").iterdir()},
            {"varianten.sqlite", "varianten.xlsx"},
        )


if __name__ == "__main__":
    unittest.main()
