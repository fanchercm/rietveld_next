"""Tests for profile benchmark smoke hooks."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks.profiles import (
    GAUSSIAN_FLOAT32_ABS_TOLERANCE,
    GAUSSIAN_FLOAT64_ABS_TOLERANCE,
    GaussianComparisonMismatch,
    compare_gaussian_profile_outputs,
    run_profile_windowing_benchmark,
    run_pseudo_voigt_profile_benchmark,
    run_rust_jax_gaussian_comparison,
)
from rietveld_next.benchmarks.results import validate_benchmark_result_dict


class ProfileBenchmarkTests(unittest.TestCase):
    """Smoke tests for issue-scoped profile benchmarks."""

    def test_compare_gaussian_outputs_uses_strict_float64_tolerance(self) -> None:
        report = compare_gaussian_profile_outputs([1.0, 0.5], [1.0, 0.5 + 1.0e-13], dtype="float64")

        self.assertLessEqual(report.max_abs_error, GAUSSIAN_FLOAT64_ABS_TOLERANCE)
        self.assertEqual(report.value_count, 2)
        self.assertLess(report.checksum_abs_error, GAUSSIAN_FLOAT64_ABS_TOLERANCE)

    def test_compare_gaussian_outputs_reports_relaxed_float32_tolerance(self) -> None:
        report = compare_gaussian_profile_outputs([1.0], [1.0 + 1.0e-6], dtype="float32")

        self.assertEqual(report.abs_tolerance, GAUSSIAN_FLOAT32_ABS_TOLERANCE)
        self.assertLessEqual(report.max_abs_error, GAUSSIAN_FLOAT32_ABS_TOLERANCE)

    def test_compare_gaussian_outputs_includes_errors_in_mismatch(self) -> None:
        with self.assertRaisesRegex(
            GaussianComparisonMismatch,
            "max_abs_error=.*max_rel_error=.*checksum_abs_error",
        ):
            compare_gaussian_profile_outputs([1.0], [2.0], dtype="float64")

    def test_rust_jax_comparison_skips_without_rust_fixture(self) -> None:
        result = run_rust_jax_gaussian_comparison(input_size=8)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.backend, "rust_jax")
        self.assertIn("Rust Gaussian profile output was not supplied", result.skip_reason or "")
        validate_benchmark_result_dict(result.to_dict())

    def test_pseudo_voigt_profile_benchmark_runs_small_smoke_case(self) -> None:
        result = run_pseudo_voigt_profile_benchmark(size="small", iterations=1, seed=7)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "pseudo_voigt_profile")
        self.assertEqual(result.environment["dataset"]["size"], "small")
        self.assertEqual(result.environment["dataset"]["variant"], "pseudo_voigt")
        self.assertEqual(result.environment["evaluated_point_peak_pairs"], 128 * 3)
        self.assertGreater(result.checksum or 0.0, 0.0)
        validate_benchmark_result_dict(result.to_dict())

    def test_pseudo_voigt_profile_benchmark_supports_medium_preset(self) -> None:
        result = run_pseudo_voigt_profile_benchmark(size="medium", iterations=1, seed=1)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 2048)
        self.assertEqual(result.environment["peak_count"], 12)

    def test_profile_windowing_benchmark_reports_pair_reduction_and_error(self) -> None:
        result = run_profile_windowing_benchmark(size="medium", iterations=1, seed=0, width_factor=12.0)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.name, "profile_windowing")
        self.assertLess(
            result.environment["windowed_point_peak_pairs"],
            result.environment["dense_point_peak_pairs"],
        )
        self.assertGreater(result.environment["point_peak_pair_reduction_fraction"], 0.0)
        self.assertLessEqual(result.environment["max_abs_error"], result.environment["abs_tolerance"])
        self.assertLess(
            result.environment["windowed_pair_memory_bytes"],
            result.environment["dense_pair_memory_bytes"],
        )
        validate_benchmark_result_dict(result.to_dict())

    def test_profile_benchmarks_reject_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "iterations"):
            run_pseudo_voigt_profile_benchmark(iterations=0)
        with self.assertRaisesRegex(ValueError, "width_factor"):
            run_profile_windowing_benchmark(width_factor=0.0)


if __name__ == "__main__":
    unittest.main()
