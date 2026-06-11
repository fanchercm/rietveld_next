"""Tests for diffraction profile kernels."""

from __future__ import annotations

import math
import unittest

from rietveld_next.diffraction import (
    Reflection,
    gaussian_profile,
    lorentzian_profile,
    peak_window_indices,
    plan_reflection_batches,
    pseudo_voigt_profile,
    thompson_cox_hastings_profile,
)


class GaussianProfileTests(unittest.TestCase):
    """Known-value and validation tests for the Gaussian profile kernel."""

    def test_gaussian_profile_matches_peak_height_formula(self) -> None:
        values = gaussian_profile([0.0], center=0.0, fwhm=2.0, area=3.0)
        expected = 3.0 * math.sqrt(4.0 * math.log(2.0) / math.pi) / 2.0

        self.assertAlmostEqual(values[0], expected, places=15)

    def test_gaussian_profile_is_half_at_half_fwhm_offset(self) -> None:
        center_value = gaussian_profile([0.0], center=0.0, fwhm=2.0)[0]
        half_width_value = gaussian_profile([1.0], center=0.0, fwhm=2.0)[0]

        self.assertAlmostEqual(half_width_value / center_value, 0.5, places=15)

    def test_gaussian_profile_empty_axis_is_empty(self) -> None:
        self.assertEqual(gaussian_profile([], center=0.0, fwhm=1.0), [])

    def test_gaussian_profile_rejects_non_positive_fwhm(self) -> None:
        with self.assertRaisesRegex(ValueError, "fwhm must be positive"):
            gaussian_profile([0.0], center=0.0, fwhm=0.0)

    def test_gaussian_profile_rejects_non_finite_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "x\\[1\\] must be a finite number"):
            gaussian_profile([0.0, math.inf], center=0.0, fwhm=1.0)


class LorentzianProfileTests(unittest.TestCase):
    """Known-value and validation tests for the Lorentzian profile kernel."""

    def test_lorentzian_profile_matches_peak_height_formula(self) -> None:
        values = lorentzian_profile([0.0], center=0.0, fwhm=2.0, area=3.0)
        expected = 3.0 * 2.0 / (math.pi * 2.0)

        self.assertAlmostEqual(values[0], expected, places=15)

    def test_lorentzian_profile_is_half_at_half_fwhm_offset(self) -> None:
        center_value = lorentzian_profile([0.0], center=0.0, fwhm=2.0)[0]
        half_width_value = lorentzian_profile([1.0], center=0.0, fwhm=2.0)[0]

        self.assertAlmostEqual(half_width_value / center_value, 0.5, places=15)

    def test_lorentzian_profile_rejects_negative_fwhm(self) -> None:
        with self.assertRaisesRegex(ValueError, "fwhm must be positive"):
            lorentzian_profile([0.0], center=0.0, fwhm=-1.0)


class PseudoVoigtProfileTests(unittest.TestCase):
    """Synthetic and validation tests for pseudo-Voigt profile kernels."""

    def test_pseudo_voigt_eta_zero_matches_gaussian(self) -> None:
        axis = [-1.0, 0.0, 1.0]

        self.assertEqual(
            pseudo_voigt_profile(axis, center=0.0, fwhm=1.0, eta=0.0),
            gaussian_profile(axis, center=0.0, fwhm=1.0),
        )

    def test_pseudo_voigt_eta_one_matches_lorentzian(self) -> None:
        axis = [-1.0, 0.0, 1.0]

        self.assertEqual(
            pseudo_voigt_profile(axis, center=0.0, fwhm=1.0, eta=1.0),
            lorentzian_profile(axis, center=0.0, fwhm=1.0),
        )

    def test_pseudo_voigt_rejects_invalid_eta(self) -> None:
        with self.assertRaisesRegex(ValueError, "eta must be between 0 and 1"):
            pseudo_voigt_profile([0.0], center=0.0, fwhm=1.0, eta=1.5)

    def test_thompson_cox_hastings_pure_gaussian_limit(self) -> None:
        values = thompson_cox_hastings_profile(
            [0.0],
            center=0.0,
            gaussian_fwhm=2.0,
            lorentzian_fwhm=0.0,
        )

        self.assertAlmostEqual(values[0], gaussian_profile([0.0], center=0.0, fwhm=2.0)[0], places=15)

    def test_thompson_cox_hastings_rejects_zero_widths(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one"):
            thompson_cox_hastings_profile([0.0], center=0.0, gaussian_fwhm=0.0, lorentzian_fwhm=0.0)


class PeakWindowTests(unittest.TestCase):
    """Tests for deterministic peak window selection."""

    def test_peak_window_indices_returns_slice_bounds(self) -> None:
        self.assertEqual(
            peak_window_indices([-2.0, -1.0, 0.0, 1.0, 2.0], center=0.0, fwhm=0.5, width_factor=2.0),
            (1, 4),
        )

    def test_peak_window_indices_handles_empty_axis(self) -> None:
        self.assertEqual(peak_window_indices([], center=0.0, fwhm=1.0), (0, 0))

    def test_peak_window_indices_rejects_unsorted_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "sorted"):
            peak_window_indices([0.0, -1.0, 1.0], center=0.0, fwhm=1.0)


class ReflectionBatchTests(unittest.TestCase):
    """Tests for deterministic reflection batching."""

    def test_plan_reflection_batches_sorts_by_center_then_id(self) -> None:
        batches = plan_reflection_batches(
            [
                Reflection("c", center=2.0, fwhm=0.1),
                Reflection("b", center=1.0, fwhm=0.1),
                Reflection("a", center=1.0, fwhm=0.1),
            ],
            max_batch_size=2,
        )

        self.assertEqual([batch.reflection_ids for batch in batches], [("a", "b"), ("c",)])
        self.assertEqual((batches[0].center_min, batches[0].center_max), (1.0, 1.0))

    def test_plan_reflection_batches_rejects_duplicate_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate reflection id"):
            plan_reflection_batches(
                [Reflection("a", center=0.0, fwhm=0.1), Reflection("a", center=1.0, fwhm=0.1)],
                max_batch_size=2,
            )


if __name__ == "__main__":
    unittest.main()
