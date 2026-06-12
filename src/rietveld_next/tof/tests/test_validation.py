"""Tests for TOF validation fixtures, diagnostics, and workflow specs."""

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
    TimeOfFlightSyntheticBenchmarkSpec,
    event_mode_provenance_placeholder,
    gsasii_tof_comparison_fixture,
    run_tof_synthetic_benchmark,
    tof_calibration_wizard_spec,
    tof_diagnostic_plot_data,
)


class TimeOfFlightValidationTests(unittest.TestCase):
    """Validate M22 TOF workflow and validation helpers."""

    def test_synthetic_benchmark_returns_reproducible_smoke_result(self) -> None:
        spec = TimeOfFlightSyntheticBenchmarkSpec(
            bank_count=2,
            bins_per_bank=7,
            bin_width_microseconds=10.0,
            residual_step=0.1,
            repeat_count=2,
        )

        first = run_tof_synthetic_benchmark(spec)
        second = run_tof_synthetic_benchmark(spec)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.residual_count, 14)
        self.assertEqual(first.bank_labels, ("tof:bank-1", "tof:bank-2"))
        self.assertGreater(first.objective_value, 0.0)

    def test_synthetic_benchmark_rejects_tiny_workload(self) -> None:
        with self.assertRaisesRegex(ValueError, "bins_per_bank"):
            TimeOfFlightSyntheticBenchmarkSpec(bins_per_bank=2)

    def test_calibration_wizard_spec_maps_steps_to_api_calls(self) -> None:
        steps = tof_calibration_wizard_spec("bank-1", (1.0, 1.5, 2.0))

        self.assertEqual([step.step_id for step in steps], [
            "load-axis",
            "define-bank",
            "fit-calibration",
            "preview-centers",
            "assemble-objective",
        ])
        self.assertIn("TimeOfFlightCalibrationParameters", steps[2].api_call)
        self.assertEqual(steps[0].to_dict()["required_inputs"][0], "centers_microseconds")

    def test_calibration_wizard_spec_rejects_empty_standards(self) -> None:
        with self.assertRaisesRegex(ValueError, "standard_d_spacings"):
            tof_calibration_wizard_spec("bank-1", ())

    def test_diagnostic_plot_data_contains_unmasked_series_and_objective_residuals(self) -> None:
        block = _diagnostic_block(masked_bin_indices=(0,))

        data = tof_diagnostic_plot_data(block)

        self.assertEqual(data.bank_id, "bank-1")
        self.assertEqual(len(data.tof_microseconds), 3)
        self.assertEqual(data.unmasked_bin_indices, (1, 2))
        self.assertEqual(len(data.objective_residuals), 2)
        self.assertEqual(data.to_dict()["units"]["tof"], "microsecond")

    def test_diagnostic_plot_data_rejects_wrong_block_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "TimeOfFlightBankObjectiveBlock"):
            tof_diagnostic_plot_data(object())  # type: ignore[arg-type]

    def test_event_mode_placeholder_records_explicit_unsupported_status(self) -> None:
        placeholder = event_mode_provenance_placeholder(
            "bank-1",
            "events.nxs",
            reduction_state="histogrammed_elsewhere",
        )

        self.assertFalse(placeholder.supported)
        self.assertEqual(placeholder.to_dict()["provenance_type"], "tof_event_mode_placeholder")
        self.assertEqual(placeholder.to_dict()["event_source"], "events.nxs")

    def test_event_mode_placeholder_rejects_empty_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "event_source"):
            event_mode_provenance_placeholder("bank-1", "")

    def test_gsasii_fixture_compares_synthetic_peak_centers_with_tolerance(self) -> None:
        calibration = TimeOfFlightCalibrationParameters(
            18000.0,
            difa_microseconds_per_angstrom_squared=-2.0,
            zero_microseconds=4.5,
        )
        fixture = gsasii_tof_comparison_fixture(calibration, (1.0, 1.5))

        result = fixture.compare(calibration.peak_positions_microseconds((1.0, 1.5)))

        self.assertTrue(result.passed)
        self.assertEqual(result.compared_peak_count, 2)
        self.assertEqual(fixture.to_dict()["reference"], "GSAS-II synthetic DIFC/DIFA/zero fixture")

    def test_gsasii_fixture_detects_out_of_tolerance_peak_centers(self) -> None:
        fixture = gsasii_tof_comparison_fixture(
            TimeOfFlightCalibrationParameters(1000.0),
            (1.0,),
            tolerance_microseconds=0.1,
        )

        result = fixture.compare((1000.2,))

        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.max_abs_error_microseconds, 0.2)


def _diagnostic_block(*, masked_bin_indices: tuple[int, ...] = ()) -> TimeOfFlightBankObjectiveBlock:
    calibration = TimeOfFlightCalibrationParameters(1000.0, bank_id="bank-1")
    bank = TimeOfFlightDetectorBank(
        "bank-1",
        two_theta_degrees=145.0,
        detector_count=64,
        calibration=calibration,
        masked_bin_indices=masked_bin_indices,
    )
    axis = TimeOfFlightHistogramAxis.from_centers(
        (990.0, 1000.0, 1010.0),
        bin_width_microseconds=10.0,
        bank_id="bank-1",
    )
    return TimeOfFlightBankObjectiveBlock(
        bank=bank,
        axis=axis,
        observed=(10.0, 21.0, 10.0),
        background=TimeOfFlightBankBackground("bank-1", (10.0,)),
        profile_parameters=TimeOfFlightBankProfileParameters(
            "bank-1",
            alpha_inverse_microsecond=0.1,
            beta_inverse_microsecond=0.1,
            gaussian_fwhm_microseconds=10.0,
            window_factor=3.0,
        ),
        reflections=(TimeOfFlightReflection(d_spacing_angstrom=1.0, intensity=10.0),),
    )


if __name__ == "__main__":
    unittest.main()
