"""Tests for visualization series transforms."""

from __future__ import annotations

import unittest

from rietveld_next.visualization import difference_series, profile_plot_series


class VisualizationSeriesTests(unittest.TestCase):
    """Validate profile and difference plot data."""

    def test_profile_plot_series_builds_observed_and_calculated(self) -> None:
        series = profile_plot_series(
            [10.0, 20.0],
            [100.0, 120.0],
            [98.0, 121.0],
            x_units="deg",
            intensity_units="counts",
        )

        self.assertEqual([item.label for item in series], ["observed", "calculated"])
        self.assertEqual(series[0].x_units, "deg")
        self.assertEqual(series[0].y_units, "counts")

    def test_difference_series_uses_observed_minus_calculated(self) -> None:
        series = difference_series(
            [1.0, 2.0],
            [10.0, 7.0],
            [8.0, 9.0],
            x_units="tof_us",
            intensity_units="counts",
        )

        self.assertEqual(series.label, "difference")
        self.assertEqual(series.y, (2.0, -2.0))

    def test_length_mismatch_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "lengths must match"):
            profile_plot_series([1.0], [2.0, 3.0], x_units="deg", intensity_units="counts")

    def test_nonfinite_values_raise(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            difference_series([1.0], [float("nan")], [1.0], x_units="deg", intensity_units="counts")


if __name__ == "__main__":
    unittest.main()
