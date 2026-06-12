"""Tests for benchmark runner CLI skeleton."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from rietveld_next.benchmarks.results import validate_benchmark_result_dict
from rietveld_next.benchmarks.runner import (
    BenchmarkRunnerError,
    main,
    parse_args,
    run_selected_benchmark,
    write_json_output,
    write_markdown_summary,
)


class BenchmarkRunnerTests(unittest.TestCase):
    """Smoke tests for CLI argument handling and output structure."""

    def test_parse_args_selects_family_backend_size_and_iterations(self) -> None:
        args = parse_args(
            [
                "--family",
                "numerical",
                "--backend",
                "rust",
                "--size",
                "medium",
                "--iterations",
                "3",
                "--warmup",
                "1",
            ]
        )

        self.assertEqual(args.family, "numerical")
        self.assertEqual(args.backend, "rust")
        self.assertEqual(args.size, "medium")
        self.assertEqual(args.iterations, 3)
        self.assertEqual(args.warmup, 1)

    def test_parse_args_rejects_zero_iterations(self) -> None:
        with self.assertRaises(BenchmarkRunnerError):
            parse_args(["--iterations", "0"])

    def test_parse_args_rejects_invalid_variant_slug(self) -> None:
        with self.assertRaises(BenchmarkRunnerError):
            parse_args(["--variant", "Bad Variant"])

    def test_rust_backend_skips_without_failing(self) -> None:
        args = parse_args(["--backend", "rust", "--iterations", "2", "--warmup", "1"])

        output = run_selected_benchmark(args)
        result = output["results"][0]

        self.assertEqual(output["schema_version"], "benchmark-run-v1")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["iterations"], 2)
        self.assertEqual(result["warmup"], 1)
        self.assertIn("Rust", result["skip_reason"])
        validate_benchmark_result_dict(result)

    def test_python_backend_runs_small_smoke_benchmark(self) -> None:
        args = parse_args(["--backend", "python", "--size", "small", "--iterations", "1"])

        output = run_selected_benchmark(args)
        result = output["results"][0]

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["name"], "numerical.gaussian_profile.python.small.synthetic")
        self.assertEqual(result["environment"]["dataset"]["sample_count"], 128)
        validate_benchmark_result_dict(result)

    def test_python_backend_skips_unsupported_float32_dtype(self) -> None:
        args = parse_args(["--backend", "python", "--dtype", "float32"])

        output = run_selected_benchmark(args)
        result = output["results"][0]

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["dtype"], "float32")
        self.assertIn("Python float", result["skip_reason"])
        validate_benchmark_result_dict(result)

    def test_main_returns_error_for_invalid_variant(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main(["--variant", "Bad Variant"])

        self.assertEqual(exit_code, 2)
        self.assertIn("variant", stderr.getvalue())

    def test_output_writers_create_directories(self) -> None:
        args = parse_args(["--backend", "rust"])
        output = run_selected_benchmark(args)

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            json_path = base / "nested" / "results" / "benchmark.json"
            markdown_path = base / "nested" / "results" / "benchmark.md"
            write_json_output(output, json_path)
            write_markdown_summary(output, markdown_path)

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema_version"], "benchmark-run-v1")
            self.assertIn("Benchmark Summary", markdown_path.read_text(encoding="utf-8"))

    def test_main_writes_selected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "out" / "result.json"
            markdown_path = Path(tmp) / "out" / "result.md"
            exit_code = main(
                [
                    "--backend",
                    "rust",
                    "--output",
                    str(json_path),
                    "--markdown-output",
                    str(markdown_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())


if __name__ == "__main__":
    unittest.main()
