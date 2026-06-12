"""Tests for deterministic optimizer analysis helpers."""

from __future__ import annotations

import unittest

from rietveld_next.optimization.analysis import (
    ModelSelectionInput,
    compare_optimizer_results,
    create_seed_plan,
    derive_optimizer_seed,
    detect_overparameterization,
    rank_model_selection,
    recommend_parameter_freezing,
    score_model_selection,
)


class OptimizationAnalysisTests(unittest.TestCase):
    """Known-value, determinism, and validation tests for analysis helpers."""

    def test_compare_optimizer_results_ranks_by_objective_and_flags_shift(self) -> None:
        report = compare_optimizer_results(
            [
                {"objective_value": 2.0, "parameters": [1.0, 3.0], "status": "converged", "converged": True},
                {"objective_value": 1.5, "parameters": [1.5, 2.5], "status": "converged", "converged": True},
                {"objective_value": 1.5 + 1.0e-13, "parameters": [5.0, 2.5], "status": "max_iterations", "converged": False},
            ],
            labels=["local", "global", "restart"],
            objective_tolerance=1.0e-12,
            parameter_tolerance=0.25,
        )

        self.assertEqual(report.best_label, "global")
        self.assertEqual([row.label for row in report.rows], ["global", "restart", "local"])
        self.assertTrue(report.rows[1].equivalent_to_best)
        self.assertIn("multiple_results_equivalent_to_best", report.warnings)
        self.assertIn("parameter_shift_exceeds_tolerance", report.rows[1].warnings)
        self.assertIn("result_not_converged", report.rows[1].warnings)
        self.assertEqual(report.to_dict()["reference_label"], "global")

    def test_compare_optimizer_results_rejects_missing_objective(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing 'objective_value'"):
            compare_optimizer_results([{"parameters": [1.0]}])

    def test_parameter_freezing_recommends_unstable_correlated_parameter(self) -> None:
        report = recommend_parameter_freezing(
            [10.0, 0.2, 4.999999],
            parameter_labels=["scale", "background", "zero_shift"],
            parameter_units=["counts", "counts", "degrees_two_theta"],
            standard_uncertainties=[1.0, 2.0, 0.1],
            correlation_matrix=[
                [1.0, 0.995, 0.0],
                [0.995, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            bounds=[(0.0, 20.0), (0.0, None), (-5.0, 5.0)],
            relative_uncertainty_threshold=1.0,
            high_correlation_threshold=0.98,
            near_bound_fraction=1.0e-6,
        )

        self.assertEqual(report.status, "recommendations")
        by_label = {recommendation.label: recommendation for recommendation in report.recommendations}
        self.assertIn("background", by_label)
        self.assertIn("zero_shift", by_label)
        self.assertEqual(by_label["background"].severity, "freeze_candidate")
        self.assertIn("large_relative_uncertainty", by_label["background"].reasons)
        self.assertIn("high_correlation_with:scale", by_label["background"].reasons)
        self.assertEqual(by_label["zero_shift"].severity, "review")
        self.assertIn("near_finite_bound", by_label["zero_shift"].reasons)
        self.assertEqual(report.to_dict()["parameter_units"][2], "degrees_two_theta")

    def test_parameter_freezing_rejects_shape_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "standard_uncertainties length"):
            recommend_parameter_freezing([1.0, 2.0], standard_uncertainties=[1.0])

        with self.assertRaisesRegex(ValueError, "correlation_matrix values"):
            recommend_parameter_freezing([1.0], correlation_matrix=[[1.5]])

    def test_overparameterization_detects_rank_deficient_pathology(self) -> None:
        report = detect_overparameterization(
            jacobian=[
                [1.0, 2.0],
                [2.0, 4.0],
            ],
            parameter_labels=["scale", "background"],
            correlation_matrix=[
                [1.0, 0.99],
                [0.99, 1.0],
            ],
            high_correlation_threshold=0.98,
        )

        self.assertEqual(report.status, "overparameterized")
        self.assertEqual(report.parameter_count, 2)
        self.assertEqual(report.observation_count, 2)
        self.assertEqual(report.degrees_of_freedom, 0)
        self.assertLess(report.rank, report.parameter_count)
        self.assertEqual(report.condition_number, float("inf"))
        self.assertIn("observations_not_greater_than_parameters", report.flags)
        self.assertIn("rank_deficient", report.flags)
        self.assertIn("high_parameter_correlation", report.flags)
        self.assertEqual(report.to_dict()["parameter_labels"], ["scale", "background"])

    def test_overparameterization_reports_ok_for_full_rank_system(self) -> None:
        report = detect_overparameterization(
            jacobian=[
                [1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [2.0, -1.0],
            ],
            parameter_labels=["a", "b"],
            parameter_units=["angstrom", "degree"],
            max_condition_number=1.0e6,
        )

        self.assertEqual(report.status, "ok")
        self.assertEqual(report.flags, ())
        self.assertEqual(report.degrees_of_freedom, 2)
        self.assertEqual(report.rank, 2)
        self.assertEqual(report.parameter_units, ("angstrom", "degree"))

    def test_model_selection_scores_and_ranks_candidates(self) -> None:
        simple = ModelSelectionInput("simple", objective_value=5.0, observation_count=20, parameter_count=2)
        complex_model = ModelSelectionInput("complex", objective_value=4.0, observation_count=20, parameter_count=5)

        simple_score = score_model_selection(simple, criterion="aic")
        expected = 20.0 * __import__("math").log(10.0 / 20.0) + 4.0

        self.assertAlmostEqual(simple_score.score, expected, places=15)
        self.assertEqual(simple_score.rank, 0)
        ranked = rank_model_selection([complex_model, simple], criterion="bic")
        self.assertEqual([score.rank for score in ranked], [1, 2])
        self.assertEqual(ranked[0].model_id, "simple")
        self.assertEqual(ranked[0].to_dict()["criterion"], "bic")

    def test_model_selection_applies_zero_residual_floor_and_validates_aicc(self) -> None:
        zero = ModelSelectionInput("exact", objective_value=0.0, observation_count=5, parameter_count=1)
        score = score_model_selection(zero, criterion="aic")

        self.assertIn("zero_residual_sum_squares_floor_applied", score.warnings)

        with self.assertRaisesRegex(ValueError, "AICc requires"):
            score_model_selection(
                ModelSelectionInput("too_small", objective_value=1.0, observation_count=2, parameter_count=1),
                criterion="aicc",
            )

    def test_seed_derivation_and_plan_are_deterministic(self) -> None:
        first = derive_optimizer_seed(123, "start", index=2)
        second = derive_optimizer_seed(123, "start", index=2)
        plan = create_seed_plan(123, ["start_a", "start_b"])
        repeat = create_seed_plan(123, ["start_a", "start_b"])

        self.assertEqual(first, second)
        self.assertGreaterEqual(first, 0)
        self.assertLessEqual(first, 2**32 - 1)
        self.assertEqual(plan.to_dict(), repeat.to_dict())
        self.assertEqual(list(plan.to_dict()["seeds"]), ["start_a", "start_b"])

    def test_seed_plan_rejects_invalid_seed_and_duplicate_labels(self) -> None:
        with self.assertRaisesRegex(ValueError, "base_seed"):
            create_seed_plan(2**32, ["start"])

        with self.assertRaisesRegex(ValueError, "duplicate seed label"):
            create_seed_plan(1, ["start", "start"])


if __name__ == "__main__":
    unittest.main()
