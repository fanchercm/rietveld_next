"""Tests for X-ray calibration workflows and beamline templates."""

from __future__ import annotations

import unittest

from rietveld_next.xray import (
    ZeroShiftCalibrationPoint,
    bragg_two_theta_degrees,
    calibrate_zero_shift,
    default_synchrotron_beamline_template,
)


class XrayCalibrationWorkflowTests(unittest.TestCase):
    """Validate deterministic zero-shift calibration behavior."""

    def test_zero_shift_calibration_recovers_synthetic_shift(self) -> None:
        wavelength = 1.5406
        points = [
            ZeroShiftCalibrationPoint(2.0, bragg_two_theta_degrees(2.0, wavelength) + 0.03),
            ZeroShiftCalibrationPoint(1.5, bragg_two_theta_degrees(1.5, wavelength) + 0.03),
            ZeroShiftCalibrationPoint(1.25, bragg_two_theta_degrees(1.25, wavelength) + 0.03),
        ]

        result = calibrate_zero_shift(points, wavelength_angstrom=wavelength)

        self.assertAlmostEqual(result.zero_shift_degrees, 0.03, places=12)
        self.assertLess(result.rms_residual_degrees, 1.0e-12)
        self.assertEqual(result.to_dict()["units"]["zero_shift"], "degree_two_theta")

    def test_zero_shift_calibration_rejects_empty_points(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            calibrate_zero_shift([], wavelength_angstrom=1.5406)


class SynchrotronBeamlineTemplateTests(unittest.TestCase):
    """Validate beamline metadata template records."""

    def test_default_template_reports_missing_fields(self) -> None:
        template = default_synchrotron_beamline_template(
            facility_name="Example Light Source",
            beamline_name="BL-1",
            detector_name="area-detector",
        )

        self.assertEqual(template.to_dict()["template_type"], "synchrotron_beamline_metadata")
        self.assertEqual(
            template.missing_fields({"wavelength_angstrom": 0.8, "sample_id": "std"}),
            ("scan_id", "detector_distance_mm", "calibration_provenance"),
        )

    def test_template_rejects_empty_required_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "required_log_fields"):
            default_synchrotron_beamline_template(
                facility_name="Example Light Source",
                beamline_name="BL-1",
                detector_name="area-detector",
            ).__class__(
                facility_name="Example Light Source",
                beamline_name="BL-1",
                detector_name="area-detector",
                required_log_fields=("",),
            )


if __name__ == "__main__":
    unittest.main()
