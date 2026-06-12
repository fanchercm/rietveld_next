"""Tests for generic optimization objective helpers."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import (
    ObjectiveSpec,
    ObjectiveRegistry,
    default_objective_registry,
    invalid_model_evaluation,
    least_squares_evaluation,
    poisson_deviance_evaluation,
)


class ObjectiveHelperTests(unittest.TestCase):
    """Known-value and validation tests for objective helpers."""

    def test_least_squares_linear_loss_known_value(self) -> None:
        evaluation = least_squares_evaluation([1.0], [2.0, -1.0])

        self.assertEqual(evaluation.objective_value, 2.5)
        self.assertEqual(evaluation.residuals, (2.0, -1.0))
        self.assertEqual(evaluation.status, "ok")

    def test_least_squares_huber_limits_large_residual(self) -> None:
        evaluation = least_squares_evaluation([1.0], [3.0], loss="huber", loss_scale=1.0)

        self.assertEqual(evaluation.objective_value, 2.5)

    def test_least_squares_rejects_unknown_loss(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown loss"):
            least_squares_evaluation([1.0], [1.0], loss="bad")

    def test_invalid_model_evaluation_is_structured(self) -> None:
        evaluation = invalid_model_evaluation([1.0], "negative intensity", component="profile")

        self.assertEqual(evaluation.status, "invalid")
        self.assertEqual(evaluation.message, "negative intensity")
        self.assertEqual(evaluation.diagnostics["component"], "profile")

    def test_poisson_deviance_zero_when_counts_match(self) -> None:
        evaluation = poisson_deviance_evaluation([1.0], [10.0, 0.0], [10.0, 1.0])

        self.assertAlmostEqual(evaluation.objective_value, 2.0, places=15)
        self.assertEqual(len(evaluation.residuals), 2)

    def test_poisson_deviance_rejects_non_positive_expected(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected\\[0\\] must be positive"):
            poisson_deviance_evaluation([1.0], [1.0], [0.0])

    def test_objective_registry_rejects_duplicate_names(self) -> None:
        registry = ObjectiveRegistry()
        registry.register("quadratic", lambda parameters: least_squares_evaluation(parameters, parameters))

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register("quadratic", lambda parameters: least_squares_evaluation(parameters, parameters))

        self.assertEqual(registry.names(), ("quadratic",))

    def test_default_registry_selects_gaussian_robust_and_poisson_objectives(self) -> None:
        registry = default_objective_registry(
            [
                ObjectiveSpec(
                    name="gaussian_least_squares",
                    observed=(10.0, 12.0),
                    calculated=(9.0, 13.0),
                    sigma=(1.0, 2.0),
                ),
                ObjectiveSpec(
                    name="robust_least_squares",
                    observed=(10.0,),
                    calculated=(7.0,),
                    loss="huber",
                    loss_scale=1.0,
                ),
                ObjectiveSpec(
                    name="poisson_deviance",
                    observed=(10.0, 0.0),
                    calculated=(10.0, 1.0),
                ),
            ]
        )

        self.assertEqual(registry.names(), ("gaussian_least_squares", "poisson_deviance", "robust_least_squares"))
        gaussian = registry.get("gaussian_least_squares")([1.0])
        robust = registry.get("robust_least_squares")([1.0])
        poisson = registry.get("poisson_deviance")([1.0])

        self.assertEqual(gaussian.residuals, (1.0, -0.5))
        self.assertAlmostEqual(gaussian.objective_value, 0.625, places=15)
        self.assertEqual(robust.diagnostics["loss"], "huber")
        self.assertEqual(robust.objective_value, 2.5)
        self.assertEqual(poisson.diagnostics["objective"], "poisson_deviance")
        self.assertAlmostEqual(poisson.objective_value, 2.0, places=15)

    def test_objective_spec_rejects_unknown_builtin(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown built-in objective"):
            ObjectiveSpec(name="not_real", observed=(1.0,), calculated=(1.0,))

    def test_objective_spec_freezes_mutable_input_sequences(self) -> None:
        observed = [2.0]
        calculated = [1.0]
        spec = ObjectiveSpec(
            name="gaussian_least_squares",
            observed=observed,  # type: ignore[arg-type]
            calculated=calculated,  # type: ignore[arg-type]
        )
        objective = default_objective_registry([spec]).get("gaussian_least_squares")

        observed[0] = 20.0
        calculated[0] = 10.0

        evaluation = objective([0.0])
        self.assertEqual(spec.observed, (2.0,))
        self.assertEqual(spec.calculated, (1.0,))
        self.assertEqual(evaluation.residuals, (1.0,))


if __name__ == "__main__":
    unittest.main()
