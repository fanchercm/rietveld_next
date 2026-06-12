"""Tests for EDXRD residual diagnostics."""

from __future__ import annotations

import unittest

from rietveld_next.edxrd import (
    EnergyHistogramAxis,
    compute_edxrd_residual_diagnostics,
)


class EDXRDResidualDiagnosticsTests(unittest.TestCase):
    """Validate residual convention, weighting, and input checks."""

    def test_residual_diagnostics_compute_weighted_summary(self) -> None:
        axis = EnergyHistogramAxis((10.0, 11.0, 12.0, 13.0))

        diagnostics = compute_edxrd_residual_diagnostics(
            axis,
            observed_counts=(11.0, 18.0, 33.0),
            calculated_counts=(10.0, 20.0, 30.0),
            uncertainties_counts=(1.0, 2.0, 3.0),
            fitted_parameter_count=1,
            provenance={"fixture": "unit"},
        )

        self.assertEqual(diagnostics.residuals_counts, (1.0, -2.0, 3.0))
        self.assertEqual(diagnostics.weighted_residuals, (1.0, -1.0, 1.0))
        self.assertAlmostEqual(diagnostics.rmse_counts, (14.0 / 3.0) ** 0.5)
        self.assertAlmostEqual(diagnostics.reduced_chi_square or 0.0, 1.5)
        self.assertEqual(diagnostics.to_dict()["residual_convention"], "observed - calculated")

    def test_residual_diagnostics_without_uncertainties_reports_unweighted_residuals(self) -> None:
        axis = EnergyHistogramAxis((10.0, 11.0, 12.0))

        diagnostics = compute_edxrd_residual_diagnostics(
            axis,
            observed_counts=(1.0, 3.0),
            calculated_counts=(2.0, 1.0),
        )

        self.assertEqual(diagnostics.weighted_residuals, (-1.0, 2.0))
        self.assertIsNone(diagnostics.reduced_chi_square)

    def test_residual_diagnostics_rejects_shape_mismatch(self) -> None:
        axis = EnergyHistogramAxis((10.0, 11.0, 12.0))

        with self.assertRaisesRegex(ValueError, "observed_counts length"):
            compute_edxrd_residual_diagnostics(
                axis,
                observed_counts=(1.0,),
                calculated_counts=(1.0, 2.0),
            )

    def test_residual_diagnostics_rejects_non_positive_uncertainty(self) -> None:
        axis = EnergyHistogramAxis((10.0, 11.0))

        with self.assertRaisesRegex(ValueError, "uncertainties_counts values must be positive"):
            compute_edxrd_residual_diagnostics(
                axis,
                observed_counts=(1.0,),
                calculated_counts=(1.0,),
                uncertainties_counts=(0.0,),
            )


if __name__ == "__main__":
    unittest.main()
