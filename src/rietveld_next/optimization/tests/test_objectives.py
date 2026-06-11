"""Tests for generic optimization objective helpers."""

from __future__ import annotations

import unittest

from rietveld_next.optimization import (
    ObjectiveRegistry,
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


if __name__ == "__main__":
    unittest.main()
