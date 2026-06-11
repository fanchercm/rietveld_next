"""Tests for workflow parametric models."""

from __future__ import annotations

import unittest

from rietveld_next.workflows import (
    ParametricExpression,
    PressureParameterModel,
    TemperatureParameterModel,
)


class ParametricModelTests(unittest.TestCase):
    """Validate safe expression and simple external-variable models."""

    def test_expression_evaluates_with_units_and_assumptions(self) -> None:
        expression = ParametricExpression(
            "a0 + alpha * (temperature_k - 300)",
            "angstrom",
            {"model": "linear"},
        )

        self.assertAlmostEqual(
            expression.evaluate({"a0": 5.0, "alpha": 0.01, "temperature_k": 320.0}),
            5.2,
        )
        self.assertEqual(expression.to_dict()["units"], "angstrom")

    def test_expression_rejects_unsafe_syntax(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported expression"):
            ParametricExpression("__import__('os').system('echo bad')", "dimensionless")

    def test_temperature_and_pressure_models_validate_bounds(self) -> None:
        temperature_model = TemperatureParameterModel("cell.a", 4.0, 0.002, 300.0, "angstrom")
        pressure_model = PressureParameterModel("cell.a", 4.0, -0.01, 0.0, "angstrom")

        self.assertAlmostEqual(temperature_model.value_at(350.0), 4.1)
        self.assertAlmostEqual(pressure_model.value_at(2.0), 3.98)
        self.assertEqual(temperature_model.as_parametric_model().parameter, "cell.a")

        with self.assertRaisesRegex(ValueError, "temperature_k must be non-negative"):
            temperature_model.value_at(-1.0)
        with self.assertRaisesRegex(ValueError, "pressure_gpa must be non-negative"):
            pressure_model.value_at(-0.5)


if __name__ == "__main__":
    unittest.main()
