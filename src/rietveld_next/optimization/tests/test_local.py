"""Tests for dependency-free local optimizer infrastructure."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import (
    BoundTransform,
    ConvergenceReport,
    LocalOptimizerOptions,
    OptimizerSnapshot,
    coordinate_search_minimize,
    least_squares_evaluation,
    restore_optimizer_snapshot,
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
        self.assertAlmostEqual(report.parameter_shifts[0], 2.0, places=6)
        self.assertIn("parameter_shifts", report.to_dict())

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

    def test_restore_optimizer_snapshot_returns_exact_copy(self) -> None:
        state = {"phase": {"scale": 1.5}, "parameters": [{"name": "scale", "value": 1.5}]}
        snapshot = OptimizerSnapshot(
            iteration=3,
            parameters=(1.5,),
            objective_value=0.25,
            snapshot_id="stable",
            model_state=state,
        )

        restored = restore_optimizer_snapshot([snapshot], snapshot_id="stable")

        self.assertEqual(restored, state)
        restored["phase"]["scale"] = 9.0
        self.assertEqual(snapshot.model_state["phase"]["scale"], 1.5)

    def test_restore_optimizer_snapshot_rejects_parameter_only_snapshot(self) -> None:
        snapshot = OptimizerSnapshot(iteration=0, parameters=(1.0,), objective_value=0.5)

        with self.assertRaisesRegex(ValueError, "model_state"):
            restore_optimizer_snapshot([snapshot], iteration=0)

    def test_convergence_report_records_parameter_shifts_without_snapshots(self) -> None:
        report = ConvergenceReport(
            status="completed",
            message="done",
            converged=True,
            iterations=0,
            evaluations=1,
            objective_value=0.0,
            parameters=(2.0, 3.0),
        )

        self.assertEqual(report.parameter_shifts, (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
