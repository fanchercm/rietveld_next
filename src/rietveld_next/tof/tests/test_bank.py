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

    def test_detector_bank_serializes_sorted_mask_indices(self) -> None:
        bank = TimeOfFlightDetectorBank(
            "bank-1",
            two_theta_degrees=90.0,
            detector_count=8,
            masked_bin_indices=(3, 1),
        )

        self.assertEqual(bank.masked_bin_indices, (1, 3))
        self.assertEqual(bank.to_dict()["masked_bin_indices"], [1, 3])
        self.assertEqual(TimeOfFlightDetectorBank.from_dict(bank.to_dict()), bank)

    def test_detector_bank_mask_propagates_into_residual_vector(self) -> None:
        bank = TimeOfFlightDetectorBank(
            "bank-1",
            two_theta_degrees=90.0,
            detector_count=8,
            masked_bin_indices=(1, 3),
        )

        residuals = bank.masked_residual_vector(
            observed=(10.0, 12.0, 9.5, 8.0),
            calculated=(9.0, 13.0, 9.0, 7.0),
            sigma=(2.0, 0.5, 0.25, 1.0),
        )

        self.assertEqual(residuals, [0.5, 2.0])
        self.assertEqual(bank.unmasked_bin_indices(4), (0, 2))

    def test_detector_bank_mask_allows_empty_residual_vector_without_masks(self) -> None:
        bank = TimeOfFlightDetectorBank("bank-1", two_theta_degrees=90.0, detector_count=8)

        self.assertEqual(bank.masked_residual_vector((), ()), [])

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

    def test_detector_bank_rejects_duplicate_mask_indices(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            TimeOfFlightDetectorBank(
                "bank-1",
                two_theta_degrees=90.0,
                detector_count=8,
                masked_bin_indices=(1, 1),
            )

    def test_detector_bank_rejects_mask_index_outside_residual_length(self) -> None:
        bank = TimeOfFlightDetectorBank(
            "bank-1",
            two_theta_degrees=90.0,
            detector_count=8,
            masked_bin_indices=(4,),
        )

        with self.assertRaisesRegex(ValueError, "less than bin_count"):
            bank.masked_residual_vector((1.0, 2.0), (1.0, 2.0))

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
