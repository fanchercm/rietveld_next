"""Tests for dependency-free local optimizer infrastructure."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import (
    BoundTransform,
    LocalOptimizerOptions,
    coordinate_search_minimize,
    least_squares_evaluation,
)


class LocalOptimizerTests(unittest.TestCase):
    """Convergence and failure-mode tests for local coordinate search."""

    def test_coordinate_search_converges_on_quadratic(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [parameters[0] - 2.0])

        report = coordinate_search_minimize(
            objective,
            [0.0],
            bounds=[BoundTransform(lower=-5.0, upper=5.0)],
            options=LocalOptimizerOptions(max_iterations=80, initial_step=1.0, tolerance=1.0e-6),
        )

        self.assertTrue(report.converged)
        self.assertEqual(report.status, "converged")
        self.assertAlmostEqual(report.parameters[0], 2.0, places=6)
        self.assertGreater(report.evaluations, 1)
        self.assertGreater(len(report.snapshots), 1)

    def test_coordinate_search_reports_max_iterations(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [parameters[0] - 2.0])

        report = coordinate_search_minimize(
            objective,
            [0.0],
            options=LocalOptimizerOptions(max_iterations=1, initial_step=1.0, tolerance=1.0e-12),
        )

        self.assertFalse(report.converged)
        self.assertEqual(report.status, "max_iterations")

    def test_coordinate_search_uses_strict_improvement_not_step_tolerance(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [1.0e-4 * (parameters[0] - 1.0)])

        report = coordinate_search_minimize(
            objective,
            [0.0],
            options=LocalOptimizerOptions(max_iterations=80, initial_step=1.0, tolerance=1.0e-6),
        )

        self.assertTrue(report.converged)
        self.assertAlmostEqual(report.parameters[0], 1.0, places=6)

    def test_coordinate_search_reports_invalid_initial_model(self) -> None:
        def objective(parameters: tuple[float, ...]):
            raise ValueError("bad model")

        report = coordinate_search_minimize(objective, [0.0])

        self.assertFalse(report.converged)
        self.assertEqual(report.status, "invalid_initial_model")
        self.assertIn("bad model", report.message)

    def test_coordinate_search_rejects_bounds_length_mismatch(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, parameters)

        with self.assertRaisesRegex(ValueError, "bounds length"):
            coordinate_search_minimize(objective, [0.0, 1.0], bounds=[BoundTransform()])


if __name__ == "__main__":
    unittest.main()
