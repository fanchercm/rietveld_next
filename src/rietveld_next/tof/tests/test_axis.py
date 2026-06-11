"""Tests for the TOF histogram axis model."""

from __future__ import annotations

import math
import unittest

from rietveld_next.tof import TimeOfFlightHistogramAxis


class TimeOfFlightHistogramAxisTests(unittest.TestCase):
    """Validate TOF bin geometry and invalid-input behavior."""

    def test_axis_derives_centers_widths_and_metadata(self) -> None:
        axis = TimeOfFlightHistogramAxis((1000.0, 1010.0, 1030.0), bank_id="bankA")

        self.assertEqual(axis.bin_count, 2)
        self.assertEqual(axis.centers_microseconds, (1005.0, 1020.0))
        self.assertEqual(axis.widths_microseconds, (10.0, 20.0))
        self.assertEqual(
            axis.to_dict(),
            {
                "axis_type": "tof",
                "units": "microsecond",
                "bank_id": "bankA",
                "bin_edges_microseconds": [1000.0, 1010.0, 1030.0],
            },
        )

    def test_uniform_axis_from_centers_is_deterministic(self) -> None:
        axis = TimeOfFlightHistogramAxis.from_centers((1010.0, 1020.0), bin_width_microseconds=10.0)

        self.assertEqual(axis.bin_edges_microseconds, (1005.0, 1015.0, 1025.0))
        self.assertEqual(axis.centers_microseconds, (1010.0, 1020.0))

    def test_axis_rejects_non_monotonic_edges(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            TimeOfFlightHistogramAxis((1000.0, 1000.0, 1010.0))

    def test_axis_rejects_non_finite_edge(self) -> None:
        with self.assertRaisesRegex(ValueError, "bin_edges_microseconds\\[1\\]"):
            TimeOfFlightHistogramAxis((1000.0, math.inf))

    def test_axis_rejects_non_positive_tof(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive microsecond"):
            TimeOfFlightHistogramAxis((-1.0, 10.0))


if __name__ == "__main__":
    unittest.main()
