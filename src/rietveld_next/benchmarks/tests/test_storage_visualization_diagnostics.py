"""Tests for storage, visualization, and diagnostics benchmark helpers."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from rietveld_next.benchmarks.results import validate_benchmark_result_dict
from rietveld_next.benchmarks.storage_visualization_diagnostics import (
    compute_residual_diagnostics,
    decimate_profile_extrema,
    run_project_package_storage_benchmark,
    run_residual_diagnostics_benchmark,
    run_visualization_decimation_benchmark,
)


class StorageBenchmarkTests(unittest.TestCase):
    """Validate deterministic project-package benchmark payloads."""

    def test_project_package_storage_benchmark_reports_payload_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            result = run_project_package_storage_benchmark(output_dir=output_dir, point_count=8)

            package_root = Path(str(result.environment["package_root"]))
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.input_size, 8)
            self.assertTrue(package_root.is_relative_to(output_dir))
            self.assertEqual(result.environment["payload_kinds"], ["json_metadata", "profile_table_json"])
            self.assertIn("project.json", result.environment["file_sizes_bytes"])
            self.assertIn("manifest.json", result.environment["file_sizes_bytes"])
            self.assertIn("tables/profile_points.json", result.environment["file_sizes_bytes"])
            self.assertGreater(result.environment["total_package_bytes"], 0)
            self.assertGreaterEqual(result.environment["write_median_seconds"], 0.0)
            self.assertGreaterEqual(result.environment["read_median_seconds"], 0.0)
            self.assertIsNotNone(result.checksum)
            validate_benchmark_result_dict(result.to_dict())

    def test_project_package_storage_benchmark_requires_existing_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"

            with self.assertRaisesRegex(ValueError, "output_dir"):
                run_project_package_storage_benchmark(output_dir=missing)


class VisualizationDecimationTests(unittest.TestCase):
    """Validate extrema-preserving decimation and benchmark reporting."""

    def test_decimate_profile_extrema_preserves_global_extrema(self) -> None:
        decimated = decimate_profile_extrema(
            [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            [0.0, 1.0, 10.0, 2.0, -5.0, 3.0, 4.0, 0.0],
            max_points=6,
        )

        self.assertLessEqual(len(decimated.x), 6)
        self.assertEqual(decimated.preserved_extrema_count, 2)
        self.assertIn(10.0, decimated.y)
        self.assertIn(-5.0, decimated.y)
        self.assertEqual(decimated.original_indices, tuple(sorted(decimated.original_indices)))

    def test_decimate_profile_extrema_returns_small_input_unchanged(self) -> None:
        decimated = decimate_profile_extrema([1.0, 2.0], [3.0, 4.0], max_points=4)

        self.assertEqual(decimated.x, (1.0, 2.0))
        self.assertEqual(decimated.y, (3.0, 4.0))
        self.assertEqual(decimated.original_indices, (0, 1))

    def test_visualization_decimation_benchmark_reports_quality_metric(self) -> None:
        result = run_visualization_decimation_benchmark(point_count=32, max_points=10)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.environment["input_size"], 32)
        self.assertLessEqual(result.environment["output_size"], 10)
        self.assertEqual(result.environment["preserved_extrema_count"], 2)
        validate_benchmark_result_dict(result.to_dict())

    def test_decimate_profile_extrema_rejects_mismatched_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            decimate_profile_extrema([1.0, 2.0], [1.0], max_points=4)


class ResidualDiagnosticsBenchmarkTests(unittest.TestCase):
    """Validate residual diagnostic summaries and benchmark reporting."""

    def test_compute_residual_diagnostics_matches_known_fixture(self) -> None:
        report = compute_residual_diagnostics(
            [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            [1.0, -1.0, 2.0, -2.0, 4.0, 0.0],
            ["bank_a", "bank_a", "bank_b", "bank_b", "bank_b", "bank_a"],
            ["phase_1", "phase_1", "phase_1", "phase_2", "phase_2", "phase_2"],
            bin_count=3,
            outlier_sigma=3.0,
        )

        self.assertTrue(report.all_finite)
        self.assertEqual(report.outlier_indices, (4,))
        self.assertEqual(report.binned_residuals[0]["count"], 2)
        self.assertEqual(report.binned_residuals[0]["mean"], 0.0)
        self.assertEqual(report.binned_residuals[0]["rms"], 1.0)
        self.assertEqual(report.binned_residuals[1]["rms"], 2.0)
        self.assertAlmostEqual(report.bank_summaries["bank_a"]["rms"], math.sqrt(2.0 / 3.0))
        self.assertAlmostEqual(report.phase_summaries["phase_2"]["mean"], 2.0 / 3.0)
        self.assertGreater(report.checksum, 0.0)

    def test_residual_diagnostics_benchmark_reports_counts_and_finite_checks(self) -> None:
        result = run_residual_diagnostics_benchmark(point_count=24, bin_count=4)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.input_size, 24)
        self.assertEqual(result.environment["point_count"], 24)
        self.assertEqual(result.environment["bin_count"], 4)
        self.assertTrue(result.environment["all_diagnostics_finite"])
        self.assertIn("outlier_detection", result.environment["diagnostics_computed"])
        validate_benchmark_result_dict(result.to_dict())

    def test_compute_residual_diagnostics_rejects_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "bank_ids"):
            compute_residual_diagnostics(
                [0.0, 1.0],
                [0.0, 1.0],
                ["bank_a"],
                ["phase_1", "phase_1"],
                bin_count=1,
            )


if __name__ == "__main__":
    unittest.main()
