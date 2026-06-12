"""Tests for magnetic neutron form-factor lookup helpers."""

from __future__ import annotations

import math
import unittest

from rietveld_next.neutron.magnetic import (
    available_magnetic_form_factor_ions,
    evaluate_magnetic_form_factor,
    lookup_magnetic_form_factor_coefficients,
    normalize_magnetic_ion_label,
)


class MagneticFormFactorTests(unittest.TestCase):
    """Known-value and validation tests for the startup magnetic subset."""

    def test_available_ions_are_deterministic(self) -> None:
        self.assertEqual(available_magnetic_form_factor_ions(), ("Fe2+", "Mn2+", "Ni2+"))

    def test_lookup_returns_provenance_and_incomplete_scope_note(self) -> None:
        coefficients = lookup_magnetic_form_factor_coefficients("Fe2+")

        self.assertEqual(coefficients.ion, "Fe2+")
        self.assertEqual(coefficients.angular_momentum, "j0")
        self.assertIn("International Tables", coefficients.source)
        self.assertIn("Small startup subset", coefficients.note)
        self.assertEqual(
            coefficients.to_dict(),
            {
                "ion": "Fe2+",
                "angular_momentum": "j0",
                "a": [0.0263, 0.3668, 0.6188],
                "b_square_angstrom": [34.9597, 15.9435, 5.5935],
                "c": -0.0119,
                "q_units": "inverse_angstrom",
                "expression": "<j0(Q)> = sum_i a_i exp(-b_i * (Q / 4*pi)^2) + c",
                "source": coefficients.source,
                "note": coefficients.note,
            },
        )

    def test_evaluate_zero_scattering_vector_matches_rounded_table_sum(self) -> None:
        self.assertAlmostEqual(evaluate_magnetic_form_factor("Fe2+", 0.0), 1.0, places=12)
        self.assertAlmostEqual(evaluate_magnetic_form_factor("Mn2+", 0.0), 0.9992, places=12)
        self.assertAlmostEqual(evaluate_magnetic_form_factor("Ni2+", 0.0), 0.9998, places=12)

    def test_evaluate_decreases_for_positive_scattering_vector(self) -> None:
        self.assertLess(
            evaluate_magnetic_form_factor("Fe2+", 1.0),
            evaluate_magnetic_form_factor("Fe2+", 0.0),
        )

    def test_evaluate_rejects_negative_scattering_vector(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be non-negative"):
            evaluate_magnetic_form_factor("Fe2+", -0.1)

    def test_evaluate_rejects_non_finite_scattering_vector(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite number"):
            evaluate_magnetic_form_factor("Fe2+", math.inf)

    def test_lookup_normalizes_supported_ion_spellings(self) -> None:
        self.assertEqual(normalize_magnetic_ion_label(" fe+2 "), "Fe2+")
        self.assertEqual(lookup_magnetic_form_factor_coefficients("fe2").ion, "Fe2+")

    def test_lookup_rejects_unknown_ion(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unsupported magnetic form-factor ion"):
            lookup_magnetic_form_factor_coefficients("Co2+")

    def test_lookup_rejects_empty_ion(self) -> None:
        with self.assertRaisesRegex(ValueError, "ion must be a non-empty string"):
            lookup_magnetic_form_factor_coefficients("")

    def test_lookup_rejects_unparseable_ion(self) -> None:
        with self.assertRaisesRegex(ValueError, "element symbol"):
            lookup_magnetic_form_factor_coefficients("Fe")


if __name__ == "__main__":
    unittest.main()
