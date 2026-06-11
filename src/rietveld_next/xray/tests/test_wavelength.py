"""Tests for X-ray wavelength and Bragg-law helpers."""

from __future__ import annotations

import math
import unittest

from rietveld_next.xray import bragg_two_theta_degrees, validate_wavelength_angstrom


class XrayWavelengthTests(unittest.TestCase):
    """Known-value and validation tests for X-ray helpers."""

    def test_validate_wavelength_accepts_positive_finite_value(self) -> None:
        self.assertEqual(validate_wavelength_angstrom(1.5406), 1.5406)

    def test_validate_wavelength_rejects_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            validate_wavelength_angstrom(0.0)

    def test_bragg_two_theta_known_value(self) -> None:
        self.assertAlmostEqual(bragg_two_theta_degrees(1.0, 1.0), 60.0, places=12)

    def test_bragg_two_theta_rejects_unreachable_condition(self) -> None:
        with self.assertRaisesRegex(ValueError, "unreachable"):
            bragg_two_theta_degrees(1.0, 3.0)

    def test_bragg_two_theta_rejects_non_finite_d_spacing(self) -> None:
        with self.assertRaisesRegex(ValueError, "d_spacing_angstrom must be a finite number"):
            bragg_two_theta_degrees(math.nan, 1.0)


if __name__ == "__main__":
    unittest.main()
