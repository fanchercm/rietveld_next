"""Tests for optimization diagnostics."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import (
    correlation_matrix_from_covariance,
    covariance_from_jacobian,
    labeled_correlation_matrix_from_covariance,
    parameter_error_metrics,
)


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

    def test_covariance_from_jacobian_known_values_with_labels_and_units(self) -> None:
        result = covariance_from_jacobian(
            [[1.0, 0.0], [0.0, 2.0]],
            residual_variance=4.0,
            parameter_labels=["scale", "zero_shift"],
            parameter_units=["dimensionless", "degrees_two_theta"],
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.parameter_labels, ("scale", "zero_shift"))
        self.assertEqual(result.parameter_units, ("dimensionless", "degrees_two_theta"))
        self.assertEqual(result.matrix, [[4.0, 0.0], [0.0, 1.0]])
        self.assertEqual(result.to_dict()["status"], "ok")

    def test_covariance_from_jacobian_reports_singular_result(self) -> None:
        result = covariance_from_jacobian(
            [[1.0, 2.0]],
            residual_variance=1.0,
            parameter_labels=["a", "b"],
        )

        self.assertEqual(result.status, "singular")
        self.assertIsNone(result.matrix)
        self.assertTrue(result.warnings)

    def test_covariance_from_jacobian_rejects_shape_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "row 0 has length"):
            covariance_from_jacobian([[1.0, 2.0]], residual_variance=1.0, parameter_labels=["a"])

    def test_labeled_correlation_matrix_preserves_metadata(self) -> None:
        result = labeled_correlation_matrix_from_covariance(
            [[4.0, 1.0], [1.0, 9.0]],
            parameter_labels=["a", "b"],
            parameter_units=["angstrom", "degree"],
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.parameter_labels, ("a", "b"))
        self.assertEqual(result.parameter_units, ("angstrom", "degree"))
        self.assertAlmostEqual(result.matrix[0][1], 1.0 / 6.0, places=15)

    def test_labeled_correlation_matrix_reports_non_positive_variance(self) -> None:
        result = labeled_correlation_matrix_from_covariance([[0.0]], parameter_labels=["a"])

        self.assertEqual(result.status, "singular")
        self.assertIsNone(result.matrix)
        self.assertIn("non-positive variance", result.warnings[0])

    def test_correlation_matrix_rejects_zero_variance(self) -> None:
        with self.assertRaisesRegex(ValueError, "diagonal entry 0"):
            correlation_matrix_from_covariance([[0.0]])


if __name__ == "__main__":
    unittest.main()
