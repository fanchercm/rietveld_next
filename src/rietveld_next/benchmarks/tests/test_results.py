"""Tests for benchmark result records and optional-backend skip policy."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from types import ModuleType, SimpleNamespace

from rietveld_next.benchmarks.jax_gaussian import run_jax_gaussian_microbenchmark
from rietveld_next.benchmarks.results import (
    BENCHMARK_RESULT_SCHEMA_VERSION,
    BenchmarkResult,
    BenchmarkTiming,
    benchmark_result_schema,
    skipped_benchmark,
    validate_benchmark_result_dict,
)


class BenchmarkResultTests(unittest.TestCase):
    """Validation tests for benchmark result records."""

    def test_completed_result_serializes_timing(self) -> None:
        result = BenchmarkResult(
            name="gaussian_profile",
            backend="rust",
            status="ok",
            dtype="float64",
            input_size=16,
            iterations=3,
            warmup=1,
            checksum=12.5,
            timing=BenchmarkTiming(
                median_seconds=0.2,
                min_seconds=0.1,
                max_seconds=0.3,
                compile_seconds=None,
            ),
            environment={"compiler": "rustc"},
        )

        self.assertEqual(result.to_dict()["backend"], "rust")
        self.assertEqual(result.to_dict()["environment"], {"compiler": "rustc"})
        self.assertEqual(result.to_dict()["schema_version"], BENCHMARK_RESULT_SCHEMA_VERSION)
        self.assertIsNone(result.to_dict()["memory_peak_bytes"])

    def test_skipped_result_requires_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "skip_reason"):
            BenchmarkResult(
                name="gaussian_profile",
                backend="jax",
                status="skipped",
                dtype="float64",
                input_size=16,
                iterations=0,
                warmup=0,
                checksum=None,
            )

    def test_timing_rejects_negative_runtime(self) -> None:
        with self.assertRaisesRegex(ValueError, "timing.min_seconds must be non-negative"):
            BenchmarkTiming(
                median_seconds=0.2,
                min_seconds=-0.1,
                max_seconds=0.3,
            )

    def test_result_rejects_non_finite_checksum(self) -> None:
        with self.assertRaisesRegex(ValueError, "checksum must be a finite number"):
            BenchmarkResult(
                name="gaussian_profile",
                backend="rust",
                status="ok",
                dtype="float64",
                input_size=16,
                iterations=3,
                warmup=1,
                checksum=float("nan"),
                timing=BenchmarkTiming(
                    median_seconds=0.2,
                    min_seconds=0.1,
                    max_seconds=0.3,
                ),
            )

    def test_result_rejects_non_json_environment(self) -> None:
        with self.assertRaisesRegex(ValueError, "environment"):
            BenchmarkResult(
                name="gaussian_profile",
                backend="rust",
                status="ok",
                dtype="float64",
                input_size=16,
                iterations=3,
                warmup=1,
                checksum=1.0,
                timing=BenchmarkTiming(
                    median_seconds=0.2,
                    min_seconds=0.1,
                    max_seconds=0.3,
                ),
                environment={"bad": object()},
            )

    def test_skipped_benchmark_helper(self) -> None:
        result = skipped_benchmark(
            name="gaussian_profile",
            backend="jax",
            dtype="float64",
            input_size=16,
            reason="JAX is not installed.",
            iterations=2,
            warmup=1,
        )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.skip_reason, "JAX is not installed.")
        self.assertEqual(result.iterations, 2)
        self.assertEqual(result.warmup, 1)

    def test_schema_documents_required_fields(self) -> None:
        schema = benchmark_result_schema()

        self.assertEqual(schema["properties"]["schema_version"]["const"], BENCHMARK_RESULT_SCHEMA_VERSION)
        self.assertIn("memory_peak_bytes", schema["required"])
        self.assertIn("compile_seconds", schema["properties"]["timing"]["required"])
        self.assertIs(schema["properties"]["timing"]["additionalProperties"], False)

    def test_schema_validates_rust_style_result(self) -> None:
        result = BenchmarkResult(
            name="numerical.gaussian_profile.rust.small.synthetic",
            backend="rust",
            status="ok",
            dtype="float64",
            input_size=128,
            iterations=10,
            warmup=2,
            checksum=123.0,
            timing=BenchmarkTiming(
                median_seconds=0.002,
                min_seconds=0.001,
                max_seconds=0.003,
                compile_seconds=0.01,
            ),
            environment={"compiler": "rustc", "cpu": "test"},
            memory_peak_bytes=4096,
        )

        validate_benchmark_result_dict(result.to_dict())

    def test_schema_validates_python_jax_style_skipped_result(self) -> None:
        result = skipped_benchmark(
            name="numerical.gaussian_profile.jax.small.synthetic",
            backend="jax",
            dtype="float64",
            input_size=128,
            iterations=1,
            warmup=0,
            reason="JAX is not installed.",
            environment={"python_version": "3.test"},
        )

        validate_benchmark_result_dict(result.to_dict())

    def test_schema_validation_rejects_invalid_result(self) -> None:
        result = skipped_benchmark(
            name="numerical.gaussian_profile.jax.small.synthetic",
            backend="jax",
            dtype="float64",
            input_size=128,
            reason="JAX is not installed.",
        ).to_dict()
        result["status"] = "unknown"

        with self.assertRaisesRegex(ValueError, "status"):
            validate_benchmark_result_dict(result)

    def test_schema_validation_rejects_extra_timing_field(self) -> None:
        result = BenchmarkResult(
            name="numerical.gaussian_profile.python.small.synthetic",
            backend="python",
            status="ok",
            dtype="float64",
            input_size=128,
            iterations=1,
            warmup=0,
            checksum=1.0,
            timing=BenchmarkTiming(0.2, 0.1, 0.3),
        ).to_dict()
        result["timing"]["unexpected"] = 0.0

        with self.assertRaisesRegex(ValueError, "timing must contain"):
            validate_benchmark_result_dict(result)

    def test_jax_benchmark_skips_when_import_unavailable(self) -> None:
        real_import = __import__

        def blocked_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "jax" or name.startswith("jax."):
                raise ImportError("blocked in test")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            result = run_jax_gaussian_microbenchmark(input_size=8, iterations=1)

        self.assertEqual(result.status, "skipped")
        self.assertIn("JAX", result.skip_reason or "")

    def test_jax_benchmark_skips_float64_when_x64_disabled(self) -> None:
        fake_jax = ModuleType("jax")
        fake_jax.__version__ = "test"  # type: ignore[attr-defined]
        fake_jax.config = SimpleNamespace(read=lambda key: False if key == "jax_enable_x64" else None)  # type: ignore[attr-defined]
        fake_jnp = ModuleType("jax.numpy")

        with patch.dict("sys.modules", {"jax": fake_jax, "jax.numpy": fake_jnp}):
            result = run_jax_gaussian_microbenchmark(input_size=8, iterations=1, dtype="float64")

        self.assertEqual(result.status, "skipped")
        self.assertIn("float64", result.skip_reason or "")


if __name__ == "__main__":
    unittest.main()
