"""Tests for TOF calibration parameter sets."""

from __future__ import annotations

import math
import unittest

from rietveld_next.tof import TimeOfFlightCalibrationParameters


class TimeOfFlightCalibrationParametersTests(unittest.TestCase):
    """Validate calibration metadata, units, and invalid-input behavior."""

    def test_calibration_serializes_parameter_set_deterministically(self) -> None:
        parameters = TimeOfFlightCalibrationParameters(
            18000.0,
            difa_microseconds_per_angstrom_squared=-2.0,
            zero_microseconds=4.5,
            bank_id="bank-1",
            d_spacing_range_angstrom=(0.5, 4.0),
            source="synthetic fixture",
        )

        self.assertEqual(parameters.parameter_vector(), (18000.0, -2.0, 4.5))
        self.assertEqual(
            parameters.to_dict(),
            {
                "calibration_type": "tof_difc_difa_zero",
                "units": {
                    "difc": "microsecond/angstrom",
                    "difa": "microsecond/angstrom^2",
                    "zero": "microsecond",
                    "d_spacing_range": "angstrom",
                },
                "difc_microseconds_per_angstrom": 18000.0,
                "difa_microseconds_per_angstrom_squared": -2.0,
                "zero_microseconds": 4.5,
                "bank_id": "bank-1",
                "d_spacing_range_angstrom": [0.5, 4.0],
                "source": "synthetic fixture",
            },
        )

    def test_calibration_round_trips_from_dict(self) -> None:
        parameters = TimeOfFlightCalibrationParameters(
            12000.0,
            zero_microseconds=-1.25,
            d_spacing_range_angstrom=(0.8, 3.2),
        )

        restored = TimeOfFlightCalibrationParameters.from_dict(parameters.to_dict())

        self.assertEqual(restored, parameters)

    def test_calibration_rejects_non_positive_difc(self) -> None:
        with self.assertRaisesRegex(ValueError, "difc_microseconds_per_angstrom must be positive"):
            TimeOfFlightCalibrationParameters(0.0)

    def test_calibration_rejects_non_finite_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "zero_microseconds"):
            TimeOfFlightCalibrationParameters(18000.0, zero_microseconds=math.nan)

    def test_calibration_rejects_invalid_d_spacing_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            TimeOfFlightCalibrationParameters(18000.0, d_spacing_range_angstrom=(2.0, 2.0))

    def test_calibration_from_dict_rejects_wrong_type_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "calibration_type"):
            TimeOfFlightCalibrationParameters.from_dict(
                {
                    "calibration_type": "other",
                    "difc_microseconds_per_angstrom": 18000.0,
                }
            )


if __name__ == "__main__":
    unittest.main()
