"""Tests for deterministic synthetic benchmark datasets."""

from __future__ import annotations

import unittest

from rietveld_next.benchmarks.datasets import (
    ProfileDatasetPreset,
    generate_synthetic_gaussian_profile_dataset,
    profile_dataset_presets,
)


class SyntheticProfileDatasetTests(unittest.TestCase):
    """Validation tests for synthetic Gaussian profile fixtures."""

    def test_same_seed_produces_identical_dataset(self) -> None:
        first = generate_synthetic_gaussian_profile_dataset(size="small", seed=42)
        second = generate_synthetic_gaussian_profile_dataset(size="small", seed=42)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.metadata["seed"], 42)
        self.assertEqual(first.metadata["x_unit"], "degree_two_theta")
        self.assertEqual(first.metadata["width_unit"], "degree_two_theta_fwhm")

    def test_presets_include_small_medium_and_large(self) -> None:
        presets = profile_dataset_presets()

        self.assertEqual(sorted(presets), ["large", "medium", "small"])
        self.assertLess(presets["small"].sample_count, presets["medium"].sample_count)
        self.assertLess(presets["medium"].sample_count, presets["large"].sample_count)

    def test_zero_peak_edge_case_has_zero_intensity(self) -> None:
        preset = ProfileDatasetPreset(
            name="edge",
            sample_count=4,
            peak_count=0,
            x_min_degrees=1.0,
            x_max_degrees=2.0,
        )

        dataset = generate_synthetic_gaussian_profile_dataset(size="edge", seed=0, preset=preset)

        self.assertEqual(dataset.peaks, ())
        self.assertEqual(dataset.intensities_counts, (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(dataset.metadata["peak_count"], 0)

    def test_generator_rejects_unknown_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "size must be one of"):
            generate_synthetic_gaussian_profile_dataset(size="tiny")

    def test_preset_rejects_single_sample_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2"):
            ProfileDatasetPreset(
                name="bad",
                sample_count=1,
                peak_count=1,
                x_min_degrees=1.0,
                x_max_degrees=2.0,
            )

    def test_generator_rejects_negative_seed(self) -> None:
        with self.assertRaisesRegex(ValueError, "seed"):
            generate_synthetic_gaussian_profile_dataset(seed=-1)


if __name__ == "__main__":
    unittest.main()
