"""Tests for neutron wavelength-dependent absorption hooks."""

from __future__ import annotations

import unittest

from rietveld_next.neutron import (
    ConstantNeutronAbsorption,
    LinearWavelengthNeutronAbsorption,
    evaluate_absorption_transmission,
    validate_wavelength_angstrom,
)


class NeutronAbsorptionHookTests(unittest.TestCase):
    """Validate absorption hook plumbing and bounds checks."""

    def test_none_hook_returns_unit_transmission(self) -> None:
        self.assertEqual(evaluate_absorption_transmission(None, 1.8), 1.0)

    def test_constant_hook_returns_configured_transmission(self) -> None:
        hook = ConstantNeutronAbsorption(transmission=0.75)

        self.assertEqual(hook.transmission_factor(2.4), 0.75)
        self.assertEqual(evaluate_absorption_transmission(hook, 2.4), 0.75)

    def test_linear_hook_evaluates_wavelength_dependence(self) -> None:
        hook = LinearWavelengthNeutronAbsorption(
            reference_wavelength_angstrom=1.8,
            reference_transmission=0.9,
            slope_per_angstrom=-0.1,
        )

        self.assertAlmostEqual(hook.transmission_factor(2.0), 0.88, places=12)

    def test_linear_hook_rejects_out_of_range_evaluation(self) -> None:
        hook = LinearWavelengthNeutronAbsorption(
            reference_wavelength_angstrom=1.0,
            reference_transmission=0.95,
            slope_per_angstrom=0.1,
        )

        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            hook.transmission_factor(2.0)

    def test_hook_validation_rejects_negative_wavelength(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            validate_wavelength_angstrom(0.0)

    def test_hook_validation_rejects_bad_hook_object(self) -> None:
        with self.assertRaisesRegex(ValueError, "transmission_factor"):
            evaluate_absorption_transmission(object(), 1.8)  # type: ignore[arg-type]

    def test_evaluator_rejects_invalid_hook_return(self) -> None:
        class BadHook:
            def transmission_factor(self, wavelength_angstrom: float) -> float:
                return 1.2

        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            evaluate_absorption_transmission(BadHook(), 1.8)


if __name__ == "__main__":
    unittest.main()
