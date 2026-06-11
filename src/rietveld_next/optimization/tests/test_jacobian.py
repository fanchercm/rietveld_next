"""Tests for dependency-free Jacobian helpers."""

from __future__ import annotations

import unittest

from rietveld_next.optimization.jacobian import (
    SparseJacobian,
    SparseJacobianEntry,
    finite_difference_jacobian,
    gradient_check,
    polynomial_background_residual_jacobian,
    scale_residual_derivative,
)


class SparseJacobianTests(unittest.TestCase):
    """Known-value and validation tests for sparse Jacobian storage."""

    def test_sparse_jacobian_merges_entries_and_round_trips_dense(self) -> None:
        jacobian = SparseJacobian(
            2,
            3,
            (
                SparseJacobianEntry(0, 1, 2.0),
                SparseJacobianEntry(0, 1, 3.0),
                SparseJacobianEntry(1, 2, -1.5),
            ),
            parameter_labels=("scale", "background", "zero_shift"),
            parameter_units=("dimensionless", "counts", "degree"),
        )

        self.assertEqual(jacobian.entries, (SparseJacobianEntry(0, 1, 5.0), SparseJacobianEntry(1, 2, -1.5)))
        self.assertEqual(jacobian.to_dense(), [[0.0, 5.0, 0.0], [0.0, 0.0, -1.5]])
        self.assertEqual(jacobian.column(1), (5.0, 0.0))
        self.assertEqual(jacobian.parameter_units, ("dimensionless", "counts", "degree"))

    def test_sparse_jacobian_rejects_entry_outside_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside row_count"):
            SparseJacobian(1, 1, (SparseJacobianEntry(1, 0, 1.0),))

    def test_sparse_jacobian_rejects_ragged_dense_matrix(self) -> None:
        with self.assertRaisesRegex(ValueError, "rectangular"):
            SparseJacobian.from_dense([[1.0], [1.0, 2.0]])

    def test_sparse_jacobian_rejects_non_sequence_metadata(self) -> None:
        with self.assertRaisesRegex(ValueError, "parameter_labels"):
            SparseJacobian.from_dense([[1.0]], parameter_labels="scale")


class FiniteDifferenceJacobianTests(unittest.TestCase):
    """Finite-difference fallback tests against deterministic fixtures."""

    def test_finite_difference_jacobian_matches_linear_residuals(self) -> None:
        def residuals(parameters: tuple[float, ...]) -> tuple[float, ...]:
            scale, offset = parameters
            return (2.0 * scale + offset, -scale + 3.0 * offset)

        jacobian = finite_difference_jacobian(
            residuals,
            [1.5, -0.25],
            step_size=1.0e-6,
            parameter_labels=("scale", "offset"),
            parameter_units=("dimensionless", "counts"),
        )

        dense = jacobian.to_dense()
        self.assertAlmostEqual(dense[0][0], 2.0, places=9)
        self.assertAlmostEqual(dense[0][1], 1.0, places=9)
        self.assertAlmostEqual(dense[1][0], -1.0, places=9)
        self.assertAlmostEqual(dense[1][1], 3.0, places=9)
        self.assertEqual(jacobian.parameter_labels, ("scale", "offset"))

    def test_finite_difference_uses_backward_step_at_upper_bound(self) -> None:
        def residuals(parameters: tuple[float, ...]) -> tuple[float, ...]:
            return (parameters[0] ** 2,)

        jacobian = finite_difference_jacobian(
            residuals,
            [1.0],
            step_size=1.0e-4,
            bounds=[(0.0, 1.0)],
        )

        self.assertAlmostEqual(jacobian.to_dense()[0][0], 1.9999, places=8)

    def test_finite_difference_rejects_initial_value_outside_bounds(self) -> None:
        def residuals(parameters: tuple[float, ...]) -> tuple[float, ...]:
            return (parameters[0],)

        with self.assertRaisesRegex(ValueError, "outside bounds"):
            finite_difference_jacobian(residuals, [2.0], bounds=[(0.0, 1.0)])


class AnalyticDerivativeTests(unittest.TestCase):
    """Known-value tests for analytic scale and background derivatives."""

    def test_scale_residual_derivative_uses_observed_minus_calculated_sign(self) -> None:
        derivative = scale_residual_derivative([10.0, -4.0], sigma=[2.0, 4.0])

        self.assertEqual(derivative, (-5.0, 1.0))

    def test_scale_residual_derivative_rejects_non_positive_sigma(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            scale_residual_derivative([1.0], sigma=[0.0])

    def test_polynomial_background_residual_jacobian_known_basis(self) -> None:
        jacobian = polynomial_background_residual_jacobian(
            [0.0, 2.0, 4.0],
            2,
            sigma=[1.0, 2.0, 4.0],
            x_origin=2.0,
            x_scale=2.0,
        )

        self.assertEqual(jacobian.parameter_labels, ("background_c0", "background_c1", "background_c2"))
        self.assertEqual(
            jacobian.to_dense(),
            [
                [-1.0, 1.0, -1.0],
                [-0.5, -0.0, -0.0],
                [-0.25, -0.25, -0.25],
            ],
        )

    def test_polynomial_background_rejects_negative_degree(self) -> None:
        with self.assertRaisesRegex(ValueError, "degree"):
            polynomial_background_residual_jacobian([1.0], -1)


class GradientCheckTests(unittest.TestCase):
    """Gradient-check utility tests."""

    def test_gradient_check_passes_for_analytic_linear_jacobian(self) -> None:
        def residuals(parameters: tuple[float, ...]) -> tuple[float, ...]:
            return (2.0 * parameters[0] - parameters[1], parameters[0] + 4.0 * parameters[1])

        analytic = SparseJacobian.from_dense([[2.0, -1.0], [1.0, 4.0]])

        result = gradient_check(
            residuals,
            [0.5, -1.0],
            analytic,
            step_size=1.0e-6,
            absolute_tolerance=1.0e-8,
            relative_tolerance=1.0e-8,
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.column_count, 2)

    def test_gradient_check_reports_mismatched_entry(self) -> None:
        def residuals(parameters: tuple[float, ...]) -> tuple[float, ...]:
            return (parameters[0],)

        result = gradient_check(
            residuals,
            [1.0],
            [[2.0]],
            step_size=1.0e-6,
            absolute_tolerance=1.0e-9,
            relative_tolerance=1.0e-9,
        )

        self.assertFalse(result.passed)
        self.assertEqual(len(result.failures), 1)
        self.assertIn("row 0, column 0", result.failures[0])


if __name__ == "__main__":
    unittest.main()
