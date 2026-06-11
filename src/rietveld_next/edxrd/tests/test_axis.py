"""Tests for the EDXRD energy histogram axis model."""

from __future__ import annotations

import math
import unittest

from rietveld_next.edxrd import EnergyHistogramAxis


class EnergyHistogramAxisTests(unittest.TestCase):
    """Validate energy-axis geometry and calibration behavior."""

    def test_axis_derives_centers_widths_and_channel_metadata(self) -> None:
        axis = EnergyHistogramAxis((20.0, 20.5, 21.5), channel_start=10)

        self.assertEqual(axis.bin_count, 2)
        self.assertEqual(axis.centers_keV, (20.25, 21.0))
        self.assertEqual(axis.widths_keV, (0.5, 1.0))
        self.assertEqual(
            axis.to_dict(),
            {
                "axis_type": "energy",
                "units": "keV",
                "channel_start": 10,
                "bin_edges_keV": [20.0, 20.5, 21.5],
            },
        )

    def test_axis_from_linear_calibration_uses_edge_convention(self) -> None:
        axis = EnergyHistogramAxis.from_linear_calibration(
            channel_count=3,
            offset_keV=5.0,
            gain_keV_per_channel=0.5,
            channel_start=2,
        )

        self.assertEqual(axis.bin_edges_keV, (6.0, 6.5, 7.0, 7.5))
        self.assertEqual(axis.centers_keV, (6.25, 6.75, 7.25))

    def test_axis_from_polynomial_calibration_uses_edge_convention(self) -> None:
        axis = EnergyHistogramAxis.from_polynomial_calibration(
            channel_count=3,
            coefficients_keV_by_channel_power=(5.0, 0.5, 0.25),
            channel_start=2,
        )

        self.assertEqual(axis.bin_edges_keV, (7.0, 8.75, 11.0, 13.75))
        self.assertEqual(axis.widths_keV, (1.75, 2.25, 2.75))

    def test_axis_rejects_non_monotonic_energy_edges(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            EnergyHistogramAxis((20.0, 19.0))

    def test_axis_rejects_non_finite_energy_edge(self) -> None:
        with self.assertRaisesRegex(ValueError, "bin_edges_keV\\[1\\]"):
            EnergyHistogramAxis((20.0, math.nan))

    def test_linear_calibration_rejects_non_positive_gain(self) -> None:
        with self.assertRaisesRegex(ValueError, "gain_keV_per_channel must be positive"):
            EnergyHistogramAxis.from_linear_calibration(
                channel_count=2,
                offset_keV=10.0,
                gain_keV_per_channel=0.0,
            )

    def test_polynomial_calibration_rejects_missing_slope(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least two coefficients"):
            EnergyHistogramAxis.from_polynomial_calibration(
                channel_count=2,
                coefficients_keV_by_channel_power=(10.0,),
            )

    def test_polynomial_calibration_rejects_non_monotonic_edges(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            EnergyHistogramAxis.from_polynomial_calibration(
                channel_count=2,
                coefficients_keV_by_channel_power=(10.0, -1.0),
            )


if __name__ == "__main__":
    unittest.main()
