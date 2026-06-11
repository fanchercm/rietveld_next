"""Tests for optimization diagnostics."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import correlation_matrix_from_covariance, parameter_error_metrics


class OptimizationDiagnosticTests(unittest.TestCase):
    """Known-value and validation tests for optimization diagnostics."""

    def test_parameter_error_metrics_known_values(self) -> None:
        metrics = parameter_error_metrics([2.0, 4.0], [1.0, 2.0])

        self.assertEqual(metrics["max_abs_error"], 2.0)
        self.assertAlmostEqual(metrics["rms_error"], (2.5) ** 0.5, places=15)

    def test_parameter_error_metrics_rejects_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            parameter_error_metrics([1.0], [1.0, 2.0])

    def test_correlation_matrix_from_covariance_known_values(self) -> None:
        matrix = correlation_matrix_from_covariance([[4.0, 1.0], [1.0, 9.0]])

        self.assertEqual(matrix[0][0], 1.0)
        self.assertEqual(matrix[1][1], 1.0)
        self.assertAlmostEqual(matrix[0][1], 1.0 / 6.0, places=15)

    def test_correlation_matrix_rejects_zero_variance(self) -> None:
        with self.assertRaisesRegex(ValueError, "diagonal entry 0"):
            correlation_matrix_from_covariance([[0.0]])


if __name__ == "__main__":
    unittest.main()
