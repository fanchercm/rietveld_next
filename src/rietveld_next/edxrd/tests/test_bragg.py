"""Tests for fixed-angle EDXRD Bragg conversions."""

from __future__ import annotations

import math
import unittest

from rietveld_next.edxrd import (
    HC_KEV_ANGSTROM,
    fixed_angle_bragg_d_spacing_angstrom,
    fixed_angle_bragg_energy_keV,
)


class FixedAngleBraggConversionTests(unittest.TestCase):
    """Known-value and validation tests for EDXRD geometry helpers."""

    def test_fixed_angle_energy_known_value(self) -> None:
        self.assertAlmostEqual(
            fixed_angle_bragg_energy_keV(1.0, 60.0),
            HC_KEV_ANGSTROM,
            places=12,
        )

    def test_fixed_angle_d_spacing_round_trip(self) -> None:
        energy = fixed_angle_bragg_energy_keV(2.0, 30.0, order=2)

        self.assertAlmostEqual(
            fixed_angle_bragg_d_spacing_angstrom(energy, 30.0, order=2),
            2.0,
            places=12,
        )

    def test_fixed_angle_energy_rejects_zero_angle(self) -> None:
        with self.assertRaisesRegex(ValueError, "two_theta_degrees must be positive"):
            fixed_angle_bragg_energy_keV(1.0, 0.0)

    def test_fixed_angle_d_spacing_rejects_non_finite_energy(self) -> None:
        with self.assertRaisesRegex(ValueError, "energy_keV must be a finite number"):
            fixed_angle_bragg_d_spacing_angstrom(math.nan, 60.0)

    def test_fixed_angle_conversion_rejects_invalid_order(self) -> None:
        with self.assertRaisesRegex(ValueError, "order must be a positive integer"):
            fixed_angle_bragg_energy_keV(1.0, 60.0, order=0)


if __name__ == "__main__":
    unittest.main()
