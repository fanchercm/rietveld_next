"""Tests for X-ray fundamental-parameters skeleton hooks."""

from __future__ import annotations

import math
import unittest

from rietveld_next.xray import (
    ConstantAxialDivergence,
    ConstantDetectorResolution,
    EmissionLine,
    EmissionSpectrum,
    FundamentalParametersProfileModel,
    TwoDimensionalIntegrationMetadata,
    evaluate_axial_divergence_fwhm,
    evaluate_detector_resolution_fwhm,
    xray_fundamental_parameters_capabilities,
)


class XrayFundamentalParametersTests(unittest.TestCase):
    """Validate M17 X-ray hook skeletons and profile composition."""

    def test_emission_spectrum_records_units_and_weighted_wavelength(self) -> None:
        spectrum = EmissionSpectrum(
            (
                EmissionLine("Cu Kalpha1", 1.5406, relative_intensity=2.0),
                EmissionLine("Cu Kalpha2", 1.5444, relative_intensity=1.0),
            ),
            reference_label="Cu Kalpha1",
        )

        self.assertEqual(spectrum.reference_wavelength_angstrom, 1.5406)
        self.assertAlmostEqual(
            spectrum.weighted_wavelength_angstrom,
            (2.0 * 1.5406 + 1.5444) / 3.0,
            places=12,
        )
        self.assertEqual(spectrum.normalized_weights(), (2.0 / 3.0, 1.0 / 3.0))
        self.assertEqual(spectrum.to_dict()["units"]["wavelength"], "angstrom")

    def test_emission_spectrum_rejects_zero_total_intensity(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one emission line"):
            EmissionSpectrum((EmissionLine("Cu Kalpha1", 1.5406, relative_intensity=0.0),))

    def test_hooks_compose_with_gaussian_profile_evaluation(self) -> None:
        spectrum = EmissionSpectrum((EmissionLine("synthetic", 1.0, relative_intensity=1.0),))
        model = FundamentalParametersProfileModel(
            spectrum,
            base_gaussian_fwhm_degrees=3.0,
            axial_divergence_hook=ConstantAxialDivergence(4.0),
            detector_resolution_hook=ConstantDetectorResolution(12.0),
        )

        profile = model.evaluate_profile([20.0], center_two_theta_degrees=20.0, area=26.0)

        self.assertEqual(model.effective_fwhm_degrees(20.0), 13.0)
        expected_peak_height = 26.0 * math.sqrt(4.0 * math.log(2.0) / math.pi) / 13.0
        self.assertAlmostEqual(profile[0], expected_peak_height, places=12)

    def test_profile_model_rejects_missing_positive_width(self) -> None:
        model = FundamentalParametersProfileModel(
            EmissionSpectrum((EmissionLine("synthetic", 1.0),)),
            base_gaussian_fwhm_degrees=0.0,
        )

        with self.assertRaisesRegex(ValueError, "effective FWHM must be positive"):
            model.effective_fwhm_degrees(20.0)

    def test_hook_evaluators_reject_invalid_interfaces(self) -> None:
        with self.assertRaisesRegex(ValueError, "axial_fwhm_degrees"):
            evaluate_axial_divergence_fwhm(object(), 20.0)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "detector_fwhm_degrees"):
            evaluate_detector_resolution_fwhm(object(), 20.0)  # type: ignore[arg-type]

    def test_2d_integration_metadata_links_profile_to_image_provenance(self) -> None:
        metadata = TwoDimensionalIntegrationMetadata(
            "integration-1",
            "images/raw_001.tif",
            "profiles/raw_001.xy",
            azimuth_range_degrees=(-45.0, 45.0),
            integration_software="synthetic-integrator 0.1",
            provenance="unit-test fixture",
        )
        model = FundamentalParametersProfileModel(
            EmissionSpectrum((EmissionLine("synthetic", 1.0),)),
            base_gaussian_fwhm_degrees=0.1,
            integration_metadata=metadata,
        )

        payload = model.to_dict()

        self.assertEqual(payload["integration_metadata"]["integration_id"], "integration-1")
        self.assertEqual(payload["integration_metadata"]["units"]["azimuth"], "degree")
        self.assertEqual(payload["integration_metadata"]["azimuth_range_degrees"], [-45.0, 45.0])

    def test_2d_integration_metadata_rejects_invalid_azimuth_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "lower bound"):
            TwoDimensionalIntegrationMetadata(
                "integration-1",
                "images/raw_001.tif",
                "profiles/raw_001.xy",
                azimuth_range_degrees=(45.0, -45.0),
            )

    def test_capability_registration_records_hook_parameters_and_units(self) -> None:
        capabilities = xray_fundamental_parameters_capabilities()

        self.assertEqual(len(capabilities), 1)
        payload = capabilities[0].to_dict()
        self.assertEqual(payload["name"], "xray.fundamental_parameters.profile_skeleton")
        self.assertEqual(payload["supported_radiation_types"], ["lab_xray_cw", "synchrotron_xray_cw"])
        self.assertIn("axial_fwhm_degrees", payload["parameter_names"])
        self.assertEqual(payload["units"]["detector_fwhm_degrees"], "degree")
        self.assertFalse(payload["supports_derivatives"])


if __name__ == "__main__":
    unittest.main()
