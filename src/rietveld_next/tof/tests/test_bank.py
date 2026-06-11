"""Tests for TOF detector-bank entities."""

from __future__ import annotations

import unittest

from rietveld_next.tof import TimeOfFlightCalibrationParameters, TimeOfFlightDetectorBank


class TimeOfFlightDetectorBankTests(unittest.TestCase):
    """Validate detector-bank metadata, geometry, and calibration linkage."""

    def test_detector_bank_serializes_geometry_and_calibration(self) -> None:
        calibration = TimeOfFlightCalibrationParameters(18000.0, bank_id="bank-1")
        bank = TimeOfFlightDetectorBank(
            "bank-1",
            two_theta_degrees=145.0,
            detector_count=128,
            name="backscattering",
            sample_to_detector_m=2.4,
            calibration=calibration,
        )

        self.assertEqual(
            bank.to_dict(),
            {
                "entity_type": "tof_detector_bank",
                "bank_id": "bank-1",
                "two_theta_degrees": 145.0,
                "detector_count": 128,
                "units": {
                    "two_theta": "degree",
                    "sample_to_detector": "meter",
                },
                "name": "backscattering",
                "sample_to_detector_m": 2.4,
                "calibration": calibration.to_dict(),
            },
        )

    def test_detector_bank_round_trips_from_dict(self) -> None:
        bank = TimeOfFlightDetectorBank(
            "bank-2",
            two_theta_degrees=90.0,
            detector_count=64,
            calibration=TimeOfFlightCalibrationParameters(12000.0, bank_id="bank-2"),
        )

        restored = TimeOfFlightDetectorBank.from_dict(bank.to_dict())

        self.assertEqual(restored, bank)

    def test_detector_bank_rejects_invalid_angle(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than 0 and less than 180"):
            TimeOfFlightDetectorBank("bank-1", two_theta_degrees=180.0, detector_count=1)

    def test_detector_bank_rejects_invalid_detector_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "detector_count must be positive"):
            TimeOfFlightDetectorBank("bank-1", two_theta_degrees=90.0, detector_count=0)

    def test_detector_bank_rejects_mismatched_calibration_bank(self) -> None:
        calibration = TimeOfFlightCalibrationParameters(18000.0, bank_id="bank-2")

        with self.assertRaisesRegex(ValueError, "calibration bank_id"):
            TimeOfFlightDetectorBank(
                "bank-1",
                two_theta_degrees=90.0,
                detector_count=8,
                calibration=calibration,
            )

    def test_detector_bank_from_dict_rejects_wrong_type_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "entity_type"):
            TimeOfFlightDetectorBank.from_dict(
                {
                    "entity_type": "other",
                    "bank_id": "bank-1",
                    "two_theta_degrees": 90.0,
                    "detector_count": 8,
                }
            )


if __name__ == "__main__":
    unittest.main()
