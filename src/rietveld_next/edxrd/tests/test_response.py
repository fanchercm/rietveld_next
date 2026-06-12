"""Tests for EDXRD detector response kernels and correction hooks."""

from __future__ import annotations

import math
import unittest

from rietveld_next.edxrd import (
    DeadTimeMetadata,
    DetectorResponseModel,
    EDXRDResponsePeak,
    EnergyHistogramAxis,
    EscapePeakHook,
    GaussianDetectorResponse,
    LowEnergyTailHook,
)


class GaussianDetectorResponseTests(unittest.TestCase):
    """Analytical and validation checks for the Gaussian response kernel."""

    def test_gaussian_integrates_peak_area_on_wide_axis(self) -> None:
        axis = EnergyHistogramAxis(tuple(round(0.1 * index, 10) for index in range(1, 201)))
        kernel = GaussianDetectorResponse(fwhm_keV=0.5)
        peak = EDXRDResponsePeak(energy_keV=10.0, area_counts=250.0, label="p1")

        counts = kernel.integrate_peak(axis, peak)

        self.assertAlmostEqual(sum(counts), 250.0, places=11)
        left = axis.bin_edges_keV.index(9.9)
        right = axis.bin_edges_keV.index(10.0)
        self.assertAlmostEqual(counts[left], counts[right], places=12)
        self.assertEqual(kernel.to_dict()["units"]["density"], "counts / keV")

    def test_gaussian_density_matches_peak_center_known_value(self) -> None:
        kernel = GaussianDetectorResponse(fwhm_keV=0.2)
        peak = EDXRDResponsePeak(energy_keV=20.0, area_counts=1.0)

        density = kernel.density_counts_per_keV((20.0,), peak)[0]

        expected = 1.0 / (kernel.sigma_keV * math.sqrt(2.0 * math.pi))
        self.assertAlmostEqual(density, expected, places=12)

    def test_gaussian_rejects_non_positive_fwhm(self) -> None:
        with self.assertRaisesRegex(ValueError, "fwhm_keV must be positive"):
            GaussianDetectorResponse(fwhm_keV=0.0)

    def test_peak_rejects_negative_area(self) -> None:
        with self.assertRaisesRegex(ValueError, "area_counts must be non-negative"):
            EDXRDResponsePeak(energy_keV=10.0, area_counts=-1.0)


class DetectorResponseHookTests(unittest.TestCase):
    """Validate optional hook composition and provenance behavior."""

    def test_response_model_composes_tail_escape_and_dead_time_metadata(self) -> None:
        axis = EnergyHistogramAxis(tuple(1.0 * index for index in range(1, 31)))
        peak = EDXRDResponsePeak(energy_keV=20.0, area_counts=100.0, label="main")
        model = DetectorResponseModel(
            gaussian=GaussianDetectorResponse(fwhm_keV=0.25),
            low_energy_tail=LowEnergyTailHook(
                fraction=0.10,
                decay_keV=2.0,
                provenance={"assumption": "synthetic_one_sided_tail"},
            ),
            escape_peak=EscapePeakHook(
                escape_energy_keV=5.0,
                fraction=0.20,
                provenance={"detector_line": "synthetic_escape"},
            ),
            dead_time=DeadTimeMetadata(
                model="nonparalyzable",
                correction_applied=False,
                dead_time_seconds=1.0e-6,
                observed_count_rate_hz=10000.0,
                provenance={"source": "metadata_fixture"},
            ),
            provenance={"fixture": "m27_response"},
        )

        result = model.evaluate(axis, (peak,))

        self.assertAlmostEqual(sum(result.component_counts["gaussian"]), 100.0, places=9)
        self.assertGreater(sum(result.component_counts["low_energy_tail"]), 9.0)
        self.assertLess(sum(result.component_counts["low_energy_tail"]), 10.0)
        self.assertAlmostEqual(
            sum(result.bin_counts),
            sum(result.component_counts["gaussian"]) + sum(result.component_counts["low_energy_tail"]),
        )
        self.assertEqual(result.provenance["escape_peak_hook"], "escape_peak")
        self.assertEqual(result.provenance["low_energy_tail.assumption"], "synthetic_one_sided_tail")
        self.assertEqual(result.dead_time.to_dict()["units"]["dead_time"], "s")
        self.assertIn("not detector-validated", model.to_dict()["limitations"])

    def test_escape_hook_rejects_nonphysical_escape_energy_for_peak(self) -> None:
        hook = EscapePeakHook(escape_energy_keV=10.0, fraction=0.5)

        with self.assertRaisesRegex(ValueError, "smaller than every peak energy"):
            hook.split_peaks((EDXRDResponsePeak(energy_keV=8.0, area_counts=1.0),))

    def test_tail_hook_rejects_fraction_outside_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "fraction must be between 0 and 1"):
            LowEnergyTailHook(fraction=1.1, decay_keV=1.0)

    def test_dead_time_metadata_rejects_invalid_boolean(self) -> None:
        with self.assertRaisesRegex(ValueError, "correction_applied must be a boolean"):
            DeadTimeMetadata(model="nonparalyzable", correction_applied="no")

    def test_response_model_rejects_empty_peaks(self) -> None:
        model = DetectorResponseModel(gaussian=GaussianDetectorResponse(fwhm_keV=0.5))
        axis = EnergyHistogramAxis((1.0, 2.0))

        with self.assertRaisesRegex(ValueError, "peaks must contain at least one"):
            model.evaluate(axis, ())


if __name__ == "__main__":
    unittest.main()
