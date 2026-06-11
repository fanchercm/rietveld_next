"""Tests for diffraction scattering lookup and Miller-index helpers."""

from __future__ import annotations

import math
import unittest

from rietveld_next.diffraction import (
    available_xray_form_factor_symbols,
    equivalent_miller_indices_by_sign_permutation,
    evaluate_xray_form_factor,
    lookup_xray_form_factor_coefficients,
    simple_miller_multiplicity,
)


class XRayFormFactorTests(unittest.TestCase):
    """Known-value and validation tests for the startup form-factor subset."""

    def test_available_symbols_are_deterministic(self) -> None:
        self.assertEqual(available_xray_form_factor_symbols(), ("C", "O", "Si"))

    def test_lookup_returns_provenance_and_incomplete_scope_note(self) -> None:
        coefficients = lookup_xray_form_factor_coefficients("Si")

        self.assertEqual(coefficients.symbol, "Si")
        self.assertIn("International Tables", coefficients.source)
        self.assertIn("Small startup subset", coefficients.note)

    def test_evaluate_zero_scattering_vector_matches_coefficient_sum(self) -> None:
        self.assertAlmostEqual(evaluate_xray_form_factor("C", 0.0), 5.9992, places=12)
        self.assertAlmostEqual(evaluate_xray_form_factor("O", 0.0), 7.9994, places=12)
        self.assertAlmostEqual(evaluate_xray_form_factor("Si", 0.0), 13.9976, places=12)

    def test_evaluate_decreases_for_positive_scattering_vector(self) -> None:
        self.assertLess(evaluate_xray_form_factor("C", 1.0), evaluate_xray_form_factor("C", 0.0))

    def test_evaluate_rejects_negative_scattering_vector(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be non-negative"):
            evaluate_xray_form_factor("C", -0.1)

    def test_evaluate_rejects_non_finite_scattering_vector(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite number"):
            evaluate_xray_form_factor("C", math.inf)

    def test_lookup_rejects_unknown_symbol(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unsupported X-ray form-factor symbol"):
            lookup_xray_form_factor_coefficients("Fe")

    def test_lookup_rejects_empty_symbol(self) -> None:
        with self.assertRaisesRegex(ValueError, "symbol must be a non-empty string"):
            lookup_xray_form_factor_coefficients("")


class MillerMultiplicityTests(unittest.TestCase):
    """Tests for simple sign/permutation Miller-index multiplicity."""

    def test_simple_miller_multiplicity_counts_general_case(self) -> None:
        self.assertEqual(simple_miller_multiplicity((1, 2, 3)), 48)

    def test_simple_miller_multiplicity_counts_repeated_and_zero_indices(self) -> None:
        self.assertEqual(simple_miller_multiplicity((1, 1, 0)), 12)
        self.assertEqual(simple_miller_multiplicity((1, 0, 0)), 6)
        self.assertEqual(simple_miller_multiplicity((0, 0, 0)), 1)

    def test_equivalent_miller_indices_are_deterministically_sorted(self) -> None:
        equivalents = equivalent_miller_indices_by_sign_permutation((1, 0, 0))

        self.assertEqual(equivalents, ((-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0), (1, 0, 0)))

    def test_miller_multiplicity_rejects_wrong_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly three"):
            simple_miller_multiplicity((1, 2))

    def test_miller_multiplicity_rejects_non_integer_index(self) -> None:
        with self.assertRaisesRegex(ValueError, "k must be an integer"):
            simple_miller_multiplicity((1, 1.5, 0))

    def test_miller_multiplicity_rejects_bool_index(self) -> None:
        with self.assertRaisesRegex(ValueError, "h must be an integer"):
            simple_miller_multiplicity((True, 0, 0))


if __name__ == "__main__":
    unittest.main()
