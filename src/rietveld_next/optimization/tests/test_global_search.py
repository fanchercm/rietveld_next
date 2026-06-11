"""Tests for deterministic global-search optimization infrastructure."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import BoundTransform, least_squares_evaluation
from rietveld_next.optimization.global_search import (
    DifferentialEvolutionOptions,
    MultiStartOptions,
    SimulatedAnnealingOptions,
    bayesian_optimization_placeholder,
    differential_evolution_minimize,
    mcmc_uncertainty_placeholder,
    multi_start_minimize,
    simulated_annealing_minimize,
)
from rietveld_next.optimization.local import LocalOptimizerOptions


def quadratic_objective(parameters: tuple[float, ...]):
    """Synthetic one-dimensional quadratic objective with a known minimum."""
    return least_squares_evaluation(parameters, [parameters[0] - 2.0])


class GlobalSearchTests(unittest.TestCase):
    """Known-value, determinism, and validation tests for global search."""

    def test_differential_evolution_is_seed_deterministic(self) -> None:
        options = DifferentialEvolutionOptions(
            population_size=6,
            max_generations=8,
            seed=11,
            tolerance=0.0,
        )

        first = differential_evolution_minimize(
            quadratic_objective,
            [BoundTransform(lower=-5.0, upper=5.0)],
            initial_parameters=[-4.0],
            options=options,
        )
        second = differential_evolution_minimize(
            quadratic_objective,
            [BoundTransform(lower=-5.0, upper=5.0)],
            initial_parameters=[-4.0],
            options=options,
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertIn(first.status, {"converged", "max_generations"})
        self.assertLess(first.objective_value, 0.5 * (-4.0 - 2.0) ** 2)
        self.assertGreater(first.evaluations, options.population_size)
        self.assertEqual(first.diagnostics["seed"], 11)
        self.assertGreaterEqual(first.parameters[0], -5.0)
        self.assertLessEqual(first.parameters[0], 5.0)

    def test_differential_evolution_requires_finite_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite lower and upper"):
            differential_evolution_minimize(
                quadratic_objective,
                [BoundTransform(lower=-1.0)],
                options=DifferentialEvolutionOptions(max_generations=1),
            )

    def test_simulated_annealing_is_seed_deterministic(self) -> None:
        options = SimulatedAnnealingOptions(
            max_iterations=12,
            initial_temperature=0.8,
            cooling_rate=0.8,
            proposal_scale=0.75,
            seed=5,
        )

        first = simulated_annealing_minimize(
            quadratic_objective,
            [0.0],
            bounds=[BoundTransform(lower=-5.0, upper=5.0)],
            options=options,
        )
        second = simulated_annealing_minimize(
            quadratic_objective,
            [0.0],
            bounds=[BoundTransform(lower=-5.0, upper=5.0)],
            options=options,
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertLessEqual(first.objective_value, 0.5 * (0.0 - 2.0) ** 2)
        self.assertGreaterEqual(first.diagnostics["accepted_trials"], 1)
        self.assertEqual(first.diagnostics["seed"], 5)

    def test_simulated_annealing_reports_invalid_initial_model(self) -> None:
        def invalid_objective(parameters: tuple[float, ...]):
            raise ValueError(f"invalid at {parameters[0]}")

        report = simulated_annealing_minimize(invalid_objective, [0.0])

        self.assertFalse(report.converged)
        self.assertEqual(report.status, "invalid_initial_model")
        self.assertIn("invalid at", report.message)

    def test_multi_start_runner_chooses_best_local_result(self) -> None:
        report = multi_start_minimize(
            quadratic_objective,
            bounds=[BoundTransform(lower=-5.0, upper=5.0)],
            starts=[[-4.0], [3.25]],
            options=MultiStartOptions(
                seed=3,
                local_options=LocalOptimizerOptions(max_iterations=80, initial_step=1.0, tolerance=1.0e-6),
            ),
        )

        self.assertEqual(report.status, "completed")
        self.assertEqual(len(report.reports), 2)
        self.assertAlmostEqual(report.best_report.parameters[0], 2.0, places=6)
        self.assertLess(report.best_report.objective_value, 1.0e-10)
        self.assertEqual(report.to_dict()["diagnostics"]["start_count"], 2)

    def test_multi_start_generates_reproducible_starts(self) -> None:
        options = MultiStartOptions(
            start_count=3,
            seed=19,
            local_options=LocalOptimizerOptions(max_iterations=1, initial_step=0.25, tolerance=1.0e-6),
        )

        first = multi_start_minimize(
            quadratic_objective,
            bounds=[BoundTransform(lower=-2.0, upper=4.0)],
            options=options,
        )
        second = multi_start_minimize(
            quadratic_objective,
            bounds=[BoundTransform(lower=-2.0, upper=4.0)],
            options=options,
        )

        self.assertEqual(first.starts, second.starts)
        self.assertEqual(first.starts[0], (1.0,))
        self.assertEqual(len(first.starts), 3)

    def test_bayesian_placeholder_is_structured_and_does_not_call_objective(self) -> None:
        calls = 0

        def objective(parameters: tuple[float, ...]):
            nonlocal calls
            calls += 1
            return least_squares_evaluation(parameters, parameters)

        report = bayesian_optimization_placeholder(
            objective,
            [BoundTransform(lower=-1.0, upper=1.0)],
            seed=23,
            max_trials=5,
            acquisition="lower_confidence_bound",
        )

        self.assertEqual(calls, 0)
        self.assertEqual(report.status, "not_implemented")
        self.assertEqual(report.feature, "bayesian_optimization")
        self.assertEqual(report.diagnostics["max_trials"], 5)
        self.assertEqual(report.to_dict()["seed"], 23)

    def test_mcmc_placeholder_records_parameter_metadata(self) -> None:
        calls = 0

        def log_posterior(parameters: tuple[float, ...]) -> float:
            nonlocal calls
            calls += 1
            return -0.5 * sum(value**2 for value in parameters)

        report = mcmc_uncertainty_placeholder(
            log_posterior,
            [1.0, 2.0],
            parameter_labels=["scale", "zero"],
            parameter_units=["counts", "degree"],
            seed=31,
            chains=2,
            draws=16,
        )

        self.assertEqual(calls, 0)
        self.assertEqual(report.status, "not_implemented")
        self.assertEqual(report.parameters, (1.0, 2.0))
        self.assertEqual(report.parameter_units, ("counts", "degree"))
        self.assertEqual(report.diagnostics["draws"], 16)

    def test_mcmc_placeholder_rejects_label_length_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "parameter_labels length"):
            mcmc_uncertainty_placeholder(
                lambda parameters: -sum(parameters),
                [1.0, 2.0],
                parameter_labels=["only_one"],
            )


if __name__ == "__main__":
    unittest.main()
