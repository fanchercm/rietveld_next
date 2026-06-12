"""Tests for EDXRD calibration workflows and import templates."""

from __future__ import annotations

import unittest

from rietveld_next.edxrd import (
    EDXRDCalibrationPoint,
    default_edxrd_import_template,
    fit_fixed_angle_edxrd_calibration,
    fit_edxrd_channel_energy_calibration,
    fixed_angle_bragg_d_spacing_angstrom,
)


class EDXRDCalibrationWorkflowTests(unittest.TestCase):
    """Validate channel-to-energy calibration fixtures."""

    def test_linear_calibration_recovers_known_coefficients(self) -> None:
        points = (
            EDXRDCalibrationPoint(channel=0.0, energy_keV=10.0, label="a"),
            EDXRDCalibrationPoint(channel=10.0, energy_keV=15.0, label="b"),
            EDXRDCalibrationPoint(channel=20.0, energy_keV=20.0, label="c"),
        )

        result = fit_edxrd_channel_energy_calibration(points, polynomial_order=1)

        self.assertAlmostEqual(result.coefficients_keV_by_channel_power[0], 10.0)
        self.assertAlmostEqual(result.coefficients_keV_by_channel_power[1], 0.5)
        self.assertLess(result.rms_residual_keV, 1.0e-12)
        self.assertEqual(result.provenance["fit_method"], "unweighted_normal_equations")
        self.assertEqual(
            tuple(round(edge, 12) for edge in result.to_axis(channel_count=2).bin_edges_keV),
            (10.0, 10.5, 11.0),
        )

    def test_calibration_rejects_singular_points(self) -> None:
        points = (
            EDXRDCalibrationPoint(channel=1.0, energy_keV=10.0),
            EDXRDCalibrationPoint(channel=1.0, energy_keV=11.0),
        )

        with self.assertRaisesRegex(ValueError, "duplicate channels"):
            fit_edxrd_channel_energy_calibration(points, polynomial_order=1)

    def test_fixed_angle_workflow_recovers_quadratic_coefficients(self) -> None:
        coefficients = (8.0, 0.25, 0.01)
        channels = (0.0, 1.0, 2.0, 3.0)
        energies = tuple(
            coefficients[0] + coefficients[1] * channel + coefficients[2] * channel * channel
            for channel in channels
        )
        d_spacings = tuple(
            fixed_angle_bragg_d_spacing_angstrom(energy, 60.0)
            for energy in energies
        )

        result = fit_fixed_angle_edxrd_calibration(
            channels=channels,
            d_spacings_angstrom=d_spacings,
            two_theta_degrees=60.0,
            polynomial_order=2,
            labels=("p1", "p2", "p3", "p4"),
            provenance={"fixture": "synthetic_exact"},
        )

        for observed, expected in zip(result.coefficients_keV_by_channel_power, coefficients, strict=True):
            self.assertAlmostEqual(observed, expected, places=11)
        self.assertLess(result.max_abs_residual_keV, 1.0e-11)
        self.assertEqual(result.provenance["reference_geometry"], "fixed_angle_bragg")


class EDXRDImportTemplateTests(unittest.TestCase):
    """Validate import template diagnostics."""

    def test_default_import_template_reports_missing_fields(self) -> None:
        template = default_edxrd_import_template()

        diagnostics = template.validate_payload(
            columns=("channel",),
            metadata={"energy_calibration": {"c0": 10.0}},
        )

        self.assertEqual(
            diagnostics,
            (
                "missing required column: counts",
                "missing required metadata: two_theta_degrees",
                "missing required metadata: detector_id",
            ),
        )
        self.assertEqual(template.to_dict()["energy_units"], "keV")

    def test_import_template_accepts_complete_payload(self) -> None:
        template = default_edxrd_import_template()

        self.assertEqual(
            template.validate_payload(
                columns=("channel", "counts"),
                metadata={
                    "energy_calibration": {"coefficients_keV_by_channel_power": [10.0, 0.5]},
                    "two_theta_degrees": 6.0,
                    "detector_id": "det-1",
                },
            ),
            (),
        )

    def test_import_template_parses_spectrum_rows(self) -> None:
        template = default_edxrd_import_template()

        spectrum = template.parse_spectrum_rows(
            (
                {"channel": 0, "counts": 100.0, "uncertainty": 10.0},
                {"channel": 1, "counts": 121.0, "uncertainty": 11.0},
            )
        )

        self.assertEqual(spectrum.channels, (0.0, 1.0))
        self.assertEqual(spectrum.counts, (100.0, 121.0))
        self.assertEqual(spectrum.uncertainties, (10.0, 11.0))
        self.assertEqual(spectrum.to_dict()["point_count"], 2)

    def test_import_template_rejects_non_monotonic_channels(self) -> None:
        template = default_edxrd_import_template()

        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            template.parse_spectrum_rows(
                (
                    {"channel": 1, "counts": 100.0},
                    {"channel": 1, "counts": 121.0},
                )
            )

    def test_import_template_fits_calibration_from_standard_rows(self) -> None:
        template = default_edxrd_import_template()
        rows = (
            {"channel": 0.0, "d_spacing_angstrom": fixed_angle_bragg_d_spacing_angstrom(10.0, 60.0), "label": "a"},
            {"channel": 2.0, "d_spacing_angstrom": fixed_angle_bragg_d_spacing_angstrom(11.0, 60.0), "label": "b"},
            {"channel": 4.0, "d_spacing_angstrom": fixed_angle_bragg_d_spacing_angstrom(12.0, 60.0), "label": "c"},
        )

        result = template.fit_calibration_from_standard_rows(
            rows,
            two_theta_degrees=60.0,
            polynomial_order=1,
        )

        self.assertAlmostEqual(result.coefficients_keV_by_channel_power[0], 10.0)
        self.assertAlmostEqual(result.coefficients_keV_by_channel_power[1], 0.5)
        self.assertEqual(result.provenance["template"], template.name)


if __name__ == "__main__":
    unittest.main()
