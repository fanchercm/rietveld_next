"""Tests for diffraction correction helpers."""

from __future__ import annotations

import math
import unittest

from rietveld_next.diffraction import lorentz_polarization_correction


class LorentzPolarizationCorrectionTests(unittest.TestCase):
    """Known-value and validation tests for CW powder LP correction."""

    def test_unpolarized_ninety_degree_value(self) -> None:
        self.assertAlmostEqual(
            lorentz_polarization_correction(90.0),
            math.sqrt(2.0),
            places=12,
        )

    def test_polarization_fraction_endpoints_are_supported(self) -> None:
        self.assertAlmostEqual(
            lorentz_polarization_correction(90.0, polarization_fraction=0.0),
            2.0 * math.sqrt(2.0),
            places=12,
        )
        self.assertAlmostEqual(
            lorentz_polarization_correction(90.0, polarization_fraction=1.0),
            0.0,
            places=12,
        )

    def test_low_angle_value_is_finite_inside_domain(self) -> None:
        self.assertTrue(math.isfinite(lorentz_polarization_correction(1.0)))

    def test_rejects_zero_two_theta(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 180 degrees"):
            lorentz_polarization_correction(0.0)

    def test_rejects_one_hundred_eighty_two_theta(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 180 degrees"):
            lorentz_polarization_correction(180.0)

    def test_rejects_non_finite_two_theta(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite number"):
            lorentz_polarization_correction(math.nan)

    def test_rejects_invalid_polarization_fraction(self) -> None:
        with self.assertRaisesRegex(ValueError, "polarization_fraction must be between 0 and 1"):
            lorentz_polarization_correction(90.0, polarization_fraction=1.1)


if __name__ == "__main__":
    unittest.main()
