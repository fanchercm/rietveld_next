"""Tests for dependency-free uncertainty diagnostics."""

from __future__ import annotations

import unittest

from rietveld_next.optimization.uncertainty import (
    correlation_from_covariance,
    covariance_from_jacobian,
    covariance_from_normal_matrix,
)


class UncertaintyDiagnosticTests(unittest.TestCase):
    """Known-value and validation tests for covariance and correlation helpers."""

    def test_covariance_from_jacobian_known_values(self) -> None:
        result = covariance_from_jacobian(
            [[1.0, 0.0], [0.0, 2.0]],
            residual_variance=4.0,
            parameter_labels=["scale", "zero_shift"],
            parameter_units=["dimensionless", "degrees_two_theta"],
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.parameter_labels, ("scale", "zero_shift"))
        self.assertEqual(result.parameter_units, ("dimensionless", "degrees_two_theta"))
        self.assertEqual(result.normal_matrix, [[1.0, 0.0], [0.0, 4.0]])
        self.assertEqual(result.covariance, [[4.0, 0.0], [0.0, 1.0]])
        self.assertEqual(result.standard_uncertainties, [2.0, 1.0])
        self.assertEqual(result.to_dict()["status"], "ok")

    def test_covariance_from_normal_matrix_known_values(self) -> None:
        result = covariance_from_normal_matrix(
            [[4.0, 1.0], [1.0, 3.0]],
            residual_variance=2.0,
            parameter_labels=["a", "b"],
        )

        self.assertEqual(result.status, "ok")
        self.assertAlmostEqual(result.covariance[0][0], 6.0 / 11.0, places=15)
        self.assertAlmostEqual(result.covariance[0][1], -2.0 / 11.0, places=15)
        self.assertAlmostEqual(result.covariance[1][0], -2.0 / 11.0, places=15)
        self.assertAlmostEqual(result.covariance[1][1], 8.0 / 11.0, places=15)

    def test_covariance_reports_singular_status_without_uncertainties(self) -> None:
        result = covariance_from_jacobian(
            [[1.0, 2.0], [2.0, 4.0]],
            parameter_labels=["a", "b"],
        )

        self.assertEqual(result.status, "singular")
        self.assertIsNone(result.covariance)
        self.assertIsNone(result.standard_uncertainties)
        self.assertEqual(result.condition_number, float("inf"))
        self.assertTrue(result.warnings)

    def test_covariance_reports_ill_conditioned_status_without_uncertainties(self) -> None:
        result = covariance_from_normal_matrix(
            [[1.0, 0.0], [0.0, 1e-8]],
            parameter_labels=["a", "b"],
            singular_tolerance=1e-15,
            max_condition_number=1e6,
        )

        self.assertEqual(result.status, "ill_conditioned")
        self.assertIsNone(result.covariance)
        self.assertIsNone(result.standard_uncertainties)
        self.assertGreater(result.condition_number, 1e6)
        self.assertIn("ill-conditioned", result.warnings[-1])

    def test_covariance_rejects_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "row 0 has length"):
            covariance_from_jacobian([[1.0, 2.0]], parameter_labels=["a"])

        with self.assertRaisesRegex(ValueError, "residual_variance must be non-negative"):
            covariance_from_normal_matrix([[1.0]], residual_variance=-1.0)

        with self.assertRaisesRegex(ValueError, "must be symmetric"):
            covariance_from_normal_matrix([[1.0, 0.1], [0.0, 1.0]])

        with self.assertRaisesRegex(ValueError, "sequence of finite numbers"):
            covariance_from_normal_matrix([1.0])

    def test_correlation_from_covariance_known_values_and_high_pair(self) -> None:
        result = correlation_from_covariance(
            [[4.0, 3.8], [3.8, 4.0]],
            parameter_labels=["scale", "background"],
            high_correlation_threshold=0.9,
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.parameter_labels, ("scale", "background"))
        self.assertEqual(result.correlation[0][0], 1.0)
        self.assertEqual(result.correlation[1][1], 1.0)
        self.assertAlmostEqual(result.correlation[0][1], 0.95, places=15)
        self.assertEqual(len(result.high_correlations), 1)
        self.assertEqual(result.high_correlations[0].left_label, "scale")
        self.assertEqual(result.high_correlations[0].right_label, "background")
        self.assertEqual(result.to_dict()["status"], "ok")

    def test_correlation_reports_non_positive_variance(self) -> None:
        result = correlation_from_covariance([[0.0]], parameter_labels=["a"])

        self.assertEqual(result.status, "singular")
        self.assertIsNone(result.correlation)
        self.assertIn("non-positive variance", result.warnings[0])

    def test_correlation_rejects_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be square"):
            correlation_from_covariance([[1.0, 0.0]])

        with self.assertRaisesRegex(ValueError, "high_correlation_threshold"):
            correlation_from_covariance([[1.0]], high_correlation_threshold=1.5)


if __name__ == "__main__":
    unittest.main()
