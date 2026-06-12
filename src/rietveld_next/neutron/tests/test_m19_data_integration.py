"""Tests for M19 neutron data-integration interfaces."""

from __future__ import annotations

import unittest

from rietveld_next.neutron import (
    ContainerBackgroundModel,
    JointNeutronWeightingModel,
    NeutronDatasetWeighting,
    check_neutron_uncertainties,
    import_mantid_reduced_data,
)
from rietveld_next.neutron.validation_examples import run_nuclear_neutron_validation_example


class NeutronM19DataIntegrationTests(unittest.TestCase):
    """Validate container background, import, weighting, and uncertainty APIs."""

    def test_container_background_interpolates_scaled_additive_intensity(self) -> None:
        model = ContainerBackgroundModel(
            axis_values=[10.0, 20.0, 30.0],
            intensity_values=[2.0, 4.0, 8.0],
            scale=0.5,
            source="synthetic vanadium can",
        )

        self.assertEqual(model.evaluate(20.0), 2.0)
        self.assertEqual(model.evaluate(25.0), 3.0)
        self.assertEqual(model.to_dict()["axis_unit"], "degrees_two_theta")

    def test_container_background_rejects_non_monotonic_axis(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            ContainerBackgroundModel([10.0, 10.0], [1.0, 2.0])

    def test_mantid_import_accepts_bin_edge_shape_and_positive_uncertainties(self) -> None:
        dataset = import_mantid_reduced_data(
            {
                "X": [10.0, 20.0, 30.0],
                "Y": [5.0, 7.0],
                "E": [0.5, 0.7],
            },
            dataset_id="bank1",
        )

        self.assertEqual(dataset.axis_values, (15.0, 25.0))
        self.assertEqual(dataset.sigma_values, (0.5, 0.7))
        self.assertEqual(dataset.to_dict()["metadata"]["x_shape"], "bin_edges")

    def test_mantid_import_rejects_unsupported_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "length N"):
            import_mantid_reduced_data({"X": [1.0, 2.0, 3.0, 4.0], "Y": [1.0]})

    def test_joint_weighting_records_assumptions_and_combines_residuals(self) -> None:
        model = JointNeutronWeightingModel(
            [
                NeutronDatasetWeighting(
                    "bank1",
                    relative_weight=4.0,
                    assumptions=("Gaussian independent counting uncertainties",),
                ),
                NeutronDatasetWeighting(
                    "bank2",
                    weighting_scheme="unit",
                    assumptions=("synthetic unweighted monitor-normalized data",),
                ),
            ]
        )

        residuals = model.combined_weighted_residuals(
            {
                "bank1": {"observed": [12.0, 9.0], "calculated": [10.0, 8.0], "sigma": [2.0, 1.0]},
                "bank2": {"observed": [3.0], "calculated": [1.0]},
            }
        )

        self.assertEqual(residuals, (2.0, 2.0, 2.0))
        payload = model.to_dict()
        self.assertEqual(payload["dataset_weightings"][0]["likelihood_model"], "independent_gaussian")
        self.assertEqual(payload["dataset_weightings"][0]["weighting_scheme"], "inverse_variance")
        self.assertEqual(
            payload["dataset_weightings"][0]["assumptions"],
            ["Gaussian independent counting uncertainties"],
        )

    def test_joint_weighting_rejects_missing_sigmas_for_inverse_variance(self) -> None:
        weighting = NeutronDatasetWeighting("bank1")

        with self.assertRaisesRegex(ValueError, "sigma is required"):
            weighting.weighted_residuals([1.0], [0.0])

    def test_uncertainty_checks_report_warnings_and_errors_structurally(self) -> None:
        warning = check_neutron_uncertainties([100.0], [0.00001], minimum_relative_sigma=1.0e-6)
        error = check_neutron_uncertainties([10.0, 20.0], [1.0])
        non_finite = check_neutron_uncertainties([10.0], [float("nan")])

        self.assertEqual(warning.status, "warning")
        self.assertEqual(warning.diagnostics[0].code, "below_relative_sigma_floor")
        self.assertEqual(error.status, "error")
        self.assertEqual(error.diagnostics[0].code, "sigma_length_mismatch")
        self.assertEqual(non_finite.status, "error")
        self.assertEqual(non_finite.diagnostics[0].code, "non_finite_sigma")

    def test_nuclear_neutron_validation_example_runs(self) -> None:
        result = run_nuclear_neutron_validation_example()

        self.assertEqual(result.status, "passed")
        self.assertAlmostEqual(result.amplitude_fm, 19.145, places=12)
        self.assertIn("not a cross-software validation benchmark", result.assumptions)


if __name__ == "__main__":
    unittest.main()
