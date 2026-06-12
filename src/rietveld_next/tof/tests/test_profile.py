"""Tests for TOF bank profile and multi-bank objective helpers."""

from __future__ import annotations

import unittest

from rietveld_next.tof import (
    TimeOfFlightBankBackground,
    TimeOfFlightBankObjectiveBlock,
    TimeOfFlightBankProfileParameters,
    TimeOfFlightCalibrationParameters,
    TimeOfFlightDetectorBank,
    TimeOfFlightHistogramAxis,
    TimeOfFlightReflection,
    assemble_multibank_objective,
    back_to_back_exponential_profile,
    reflection_window,
)


class TimeOfFlightBankProfileTests(unittest.TestCase):
    """Validate M21 TOF profile primitives and objective assembly."""

    def test_background_evaluates_polynomial_on_normalized_tof_axis(self) -> None:
        background = TimeOfFlightBankBackground(
            "bank-1",
            coefficients=(10.0, 0.5, 0.25),
            origin_microseconds=1000.0,
            scale_microseconds=100.0,
        )

        self.assertEqual(background.evaluate((1000.0, 1100.0, 1200.0)), (10.0, 10.75, 12.0))
        self.assertEqual(TimeOfFlightBankBackground.from_dict(background.to_dict()), background)

    def test_background_rejects_empty_coefficients(self) -> None:
        with self.assertRaisesRegex(ValueError, "coefficients"):
            TimeOfFlightBankBackground("bank-1", ())

    def test_profile_parameters_serialize_units_and_window_width(self) -> None:
        parameters = TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.25,
            beta_inverse_microsecond=0.1,
            gaussian_fwhm_microseconds=8.0,
            window_factor=5.0,
        )

        self.assertEqual(parameters.parameter_vector(), (0.25, 0.1, 8.0))
        self.assertEqual(parameters.window_half_width_microseconds, 50.0)
        self.assertEqual(TimeOfFlightBankProfileParameters.from_dict(parameters.to_dict()), parameters)

    def test_profile_parameters_reject_non_positive_decay(self) -> None:
        with self.assertRaisesRegex(ValueError, "alpha_inverse_microsecond"):
            TimeOfFlightBankProfileParameters(
                "bank-1",
                alpha_inverse_microsecond=0.0,
                beta_inverse_microsecond=0.1,
                gaussian_fwhm_microseconds=8.0,
            )

    def test_back_to_back_exponential_profile_normalizes_discrete_area(self) -> None:
        parameters = TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.15,
            beta_inverse_microsecond=0.05,
            gaussian_fwhm_microseconds=20.0,
        )
        centers = (980.0, 990.0, 1000.0, 1010.0, 1020.0, 1030.0)
        widths = (10.0,) * len(centers)

        profile = back_to_back_exponential_profile(
            centers,
            1000.0,
            parameters,
            bin_widths_microseconds=widths,
        )

        area = sum(value * width for value, width in zip(profile, widths, strict=True))
        self.assertAlmostEqual(area, 1.0)
        self.assertGreater(profile[3], profile[1])

    def test_back_to_back_exponential_profile_rejects_width_length_mismatch(self) -> None:
        parameters = TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.15,
            beta_inverse_microsecond=0.05,
            gaussian_fwhm_microseconds=20.0,
        )

        with self.assertRaisesRegex(ValueError, "length"):
            back_to_back_exponential_profile((1000.0, 1010.0), 1000.0, parameters, bin_widths_microseconds=(10.0,))

    def test_back_to_back_exponential_profile_allows_empty_coordinates(self) -> None:
        parameters = TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.15,
            beta_inverse_microsecond=0.05,
            gaussian_fwhm_microseconds=20.0,
        )

        self.assertEqual(back_to_back_exponential_profile((), 1000.0, parameters), ())

    def test_reflection_rejects_negative_intensity(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            TimeOfFlightReflection(d_spacing_angstrom=1.0, intensity=-1.0)

    def test_reflection_window_selects_profile_derived_bin_indices(self) -> None:
        axis = TimeOfFlightHistogramAxis.from_centers(
            (950.0, 975.0, 1000.0, 1025.0, 1050.0),
            bin_width_microseconds=25.0,
            bank_id="bank-1",
        )
        parameters = TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.2,
            beta_inverse_microsecond=0.2,
            gaussian_fwhm_microseconds=10.0,
            window_factor=2.0,
        )

        window = reflection_window(axis, parameters, center_microseconds=1000.0)

        self.assertEqual(window.bin_indices, (2,))
        self.assertEqual(window.to_dict()["bank_id"], "bank-1")

    def test_reflection_window_rejects_mismatched_bank(self) -> None:
        axis = TimeOfFlightHistogramAxis.from_centers(
            (1000.0,),
            bin_width_microseconds=10.0,
            bank_id="bank-1",
        )
        parameters = TimeOfFlightBankProfileParameters(
            "bank-2",
            alpha_inverse_microsecond=0.2,
            beta_inverse_microsecond=0.2,
            gaussian_fwhm_microseconds=10.0,
        )

        with self.assertRaisesRegex(ValueError, "bank_id"):
            reflection_window(axis, parameters, center_microseconds=1000.0)

    def test_bank_objective_block_calculates_background_and_reflections(self) -> None:
        block = _bank_block(
            bank_id="bank-1",
            difc=1000.0,
            centers=(990.0, 1000.0, 1010.0),
            observed=(10.0, 21.0, 10.0),
        )

        calculated = block.calculated_intensities()
        residuals = block.residuals()

        self.assertEqual(len(calculated), 3)
        self.assertGreater(calculated[1], calculated[0])
        self.assertEqual(len(residuals), 3)

    def test_assemble_multibank_objective_returns_labeled_residual_blocks(self) -> None:
        block_a = _bank_block(
            bank_id="bank-a",
            difc=1000.0,
            centers=(990.0, 1000.0, 1010.0),
            observed=(10.0, 21.0, 10.0),
        )
        block_b = _bank_block(
            bank_id="bank-b",
            difc=1200.0,
            centers=(1190.0, 1200.0, 1210.0),
            observed=(9.0, 18.0, 9.0),
            mask=(0,),
        )

        evaluation = assemble_multibank_objective((block_a, block_b), parameters=(1.0, 2.0))

        self.assertEqual(evaluation.parameters, (1.0, 2.0))
        self.assertEqual(len(evaluation.residuals), 5)
        self.assertEqual(evaluation.diagnostics["bank_count"], 2)
        self.assertEqual(
            evaluation.diagnostics["residual_blocks"],
            [
                {"label": "tof:bank-a", "bank_id": "bank-a", "start": 0, "length": 3},
                {"label": "tof:bank-b", "bank_id": "bank-b", "start": 3, "length": 2},
            ],
        )

    def test_assemble_multibank_objective_rejects_duplicate_bank(self) -> None:
        block = _bank_block(
            bank_id="bank-1",
            difc=1000.0,
            centers=(990.0, 1000.0, 1010.0),
            observed=(10.0, 21.0, 10.0),
        )

        with self.assertRaisesRegex(ValueError, "Duplicate"):
            assemble_multibank_objective((block, block))


def _bank_block(
    *,
    bank_id: str,
    difc: float,
    centers: tuple[float, ...],
    observed: tuple[float, ...],
    mask: tuple[int, ...] = (),
) -> TimeOfFlightBankObjectiveBlock:
    calibration = TimeOfFlightCalibrationParameters(difc, bank_id=bank_id)
    bank = TimeOfFlightDetectorBank(
        bank_id,
        two_theta_degrees=145.0,
        detector_count=64,
        calibration=calibration,
        masked_bin_indices=mask,
    )
    axis = TimeOfFlightHistogramAxis.from_centers(
        centers,
        bin_width_microseconds=10.0,
        bank_id=bank_id,
    )
    return TimeOfFlightBankObjectiveBlock(
        bank=bank,
        axis=axis,
        observed=observed,
        background=TimeOfFlightBankBackground(bank_id, (10.0,)),
        profile_parameters=TimeOfFlightBankProfileParameters(
            bank_id,
            alpha_inverse_microsecond=0.1,
            beta_inverse_microsecond=0.1,
            gaussian_fwhm_microseconds=10.0,
            window_factor=3.0,
        ),
        reflections=(TimeOfFlightReflection(d_spacing_angstrom=1.0, intensity=10.0, label="100"),),
    )


if __name__ == "__main__":
    unittest.main()
