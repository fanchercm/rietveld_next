"""Tests for optional local optimizer adapter contracts."""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from rietveld_next.optimization import (
    BoundTransform,
    ConvergenceReport,
    OptimizerSnapshot,
    RustLocalOptimizerRequest,
    RustOptimizerBound,
    ScipyOptimizerOptions,
    least_squares_evaluation,
    run_rust_local_optimizer,
    scipy_levenberg_marquardt_minimize,
    scipy_trust_region_minimize,
)


class _FakeBounds:
    def __init__(self, lower: list[float], upper: list[float]) -> None:
        self.lower = lower
        self.upper = upper


class _FakeScipyOptimize:
    Bounds = _FakeBounds

    @staticmethod
    def minimize(fun, initial, *, method, bounds, options):
        value = fun([2.0])
        return SimpleNamespace(
            success=True,
            status=1,
            message=f"{method} ok",
            nit=2,
            nfev=3,
            fun=value,
            x=[2.0],
        )

    @staticmethod
    def least_squares(fun, initial, *, method, max_nfev, xtol, ftol, gtol):
        residuals = fun([2.0])
        cost = 0.5 * sum(value * value for value in residuals)
        return SimpleNamespace(
            success=True,
            status=1,
            message=f"{method} ok",
            njev=2,
            nfev=4,
            cost=cost,
            x=[2.0],
        )


class AdapterTests(unittest.TestCase):
    """SciPy adapter and Rust protocol behavior."""

    def test_trust_region_reports_dependency_unavailable(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [parameters[0] - 2.0])

        report = scipy_trust_region_minimize(objective, [0.0], scipy_optimize=None)

        self.assertFalse(report.converged)
        self.assertEqual(report.status, "dependency_unavailable")
        self.assertEqual(report.diagnostics["dependency"], "scipy.optimize")

    def test_trust_region_uses_scipy_like_module(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [parameters[0] - 2.0])

        report = scipy_trust_region_minimize(
            objective,
            [0.0],
            bounds=[BoundTransform(lower=-5.0, upper=5.0)],
            options=ScipyOptimizerOptions(max_evaluations=10, tolerance=1.0e-7),
            scipy_optimize=_FakeScipyOptimize,
        )

        self.assertTrue(report.converged)
        self.assertEqual(report.diagnostics["adapter"], "trust_region")
        self.assertAlmostEqual(report.parameters[0], 2.0)
        self.assertEqual(len(report.snapshots), 2)

    def test_levenberg_marquardt_uses_residuals(self) -> None:
        def objective(parameters: tuple[float, ...]):
            return least_squares_evaluation(parameters, [parameters[0] - 2.0])

        report = scipy_levenberg_marquardt_minimize(
            objective,
            [0.0],
            scipy_optimize=_FakeScipyOptimize,
        )

        self.assertTrue(report.converged)
        self.assertEqual(report.diagnostics["adapter"], "levenberg_marquardt")
        self.assertAlmostEqual(report.objective_value, 0.0)

    def test_rust_request_is_json_compatible_and_bounded(self) -> None:
        request = RustLocalOptimizerRequest(
            objective_name="synthetic_quadratic",
            initial_parameters=(1.0,),
            bounds=(RustOptimizerBound(lower=0.0, upper=2.0),),
            options={"max_iterations": 4},
        )

        self.assertEqual(
            request.to_dict(),
            {
                "objective_name": "synthetic_quadratic",
                "initial_parameters": [1.0],
                "bounds": [{"lower": 0.0, "upper": 2.0}],
                "options": {"max_iterations": 4},
            },
        )

    def test_rust_backend_protocol_returns_convergence_report(self) -> None:
        request = RustLocalOptimizerRequest("synthetic_quadratic", (1.0,))
        report = ConvergenceReport(
            status="converged",
            message="ok",
            converged=True,
            iterations=1,
            evaluations=2,
            objective_value=0.0,
            parameters=(2.0,),
            snapshots=(OptimizerSnapshot(iteration=1, parameters=(2.0,), objective_value=0.0),),
            diagnostics={"backend": "rust-test-double"},
        )

        class Backend:
            def optimize(self, request: RustLocalOptimizerRequest) -> ConvergenceReport:
                return report

        self.assertIs(run_rust_local_optimizer(Backend(), request), report)

    def test_rust_backend_protocol_rejects_invalid_result(self) -> None:
        request = RustLocalOptimizerRequest("synthetic_quadratic", (1.0,))

        class Backend:
            def optimize(self, request: RustLocalOptimizerRequest) -> str:
                return "bad"

        with self.assertRaisesRegex(ValueError, "ConvergenceReport"):
            run_rust_local_optimizer(Backend(), request)


if __name__ == "__main__":
    unittest.main()
