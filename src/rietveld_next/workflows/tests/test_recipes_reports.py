"""Tests for workflow recipes, checkpoints, reports, and summaries."""

from __future__ import annotations

import unittest

from rietveld_next.workflows import (
    BatchRecipe,
    ParameterEstimate,
    ParameterTolerance,
    ParametricExpression,
    ParametricParameterModel,
    SequentialPointResult,
    SequentialPointSpec,
    SequentialResultTable,
    compare_workflow_results,
    create_checkpoint,
    remaining_points,
    summarize_high_throughput_results,
)


class RecipeCheckpointTests(unittest.TestCase):
    """Validate versioned batch recipes and resume checkpoints."""

    def test_recipe_round_trips_and_checkpoint_lists_remaining_points(self) -> None:
        recipe = BatchRecipe(
            recipe_id="recipe",
            points=(
                SequentialPointSpec("p1", "scan-1"),
                SequentialPointSpec("p2", "scan-2"),
            ),
            initial_parameters={"a": 4.0},
            parametric_models=(
                ParametricParameterModel("a", ParametricExpression("a0 + da", "angstrom")),
            ),
            metadata={"assumption": "synthetic fixture"},
        )

        restored = BatchRecipe.from_dict(recipe.to_dict())
        self.assertEqual(restored.to_dict(), recipe.to_dict())
        self.assertEqual(restored.digest(), recipe.digest())

        checkpoint = create_checkpoint(recipe, _table("study", ("p1",), (1.0,)), "cp-1")
        self.assertEqual([point.point_id for point in remaining_points(recipe, checkpoint)], ["p2"])

    def test_remaining_points_rejects_mismatched_recipe_digest(self) -> None:
        recipe = BatchRecipe("recipe", (SequentialPointSpec("p1", "scan-1"),), {"a": 1.0})
        other = BatchRecipe("other", (SequentialPointSpec("p1", "scan-1"),), {"a": 1.0})
        checkpoint = create_checkpoint(other, _table("study", ("p1",), (1.0,)), "cp-1")

        with self.assertRaisesRegex(ValueError, "recipe_digest"):
            remaining_points(recipe, checkpoint)


class ReportTests(unittest.TestCase):
    """Validate deterministic comparison and high-throughput summaries."""

    def test_comparison_report_applies_parameter_tolerances(self) -> None:
        baseline = _table("baseline", ("p1", "p2"), (1.0, 2.0))
        candidate = _table("candidate", ("p1", "p2"), (1.05, 2.5))

        report = compare_workflow_results(
            baseline,
            candidate,
            tolerances=(ParameterTolerance("a", 0.1),),
        )

        self.assertEqual(report["status_counts"], {"different": 1, "ok": 1})
        self.assertEqual(report["rows"][0]["parameters"][0]["status"], "ok")
        self.assertEqual(report["rows"][1]["parameters"][0]["status"], "different")

    def test_high_throughput_summary_counts_status_and_best_metric(self) -> None:
        ok_table = _table("ok", ("p1", "p2"), (1.0, 2.0), objectives=(5.0, 2.0))
        failed_table = SequentialResultTable(
            "failed",
            (
                SequentialPointResult(
                    index=0,
                    point_id="p1",
                    dataset_id="scan-1",
                    variables={},
                    status="error",
                    attempts=1,
                    error="not converged",
                ),
            ),
        )

        summary = summarize_high_throughput_results((ok_table, failed_table))

        self.assertEqual(summary["status_counts"], {"error": 1, "ok": 1})
        self.assertEqual(summary["best_study"]["study_id"], "ok")
        self.assertEqual(summary["best_study"]["best_metric"], 2.0)


def _table(
    study_id: str,
    point_ids: tuple[str, ...],
    values: tuple[float, ...],
    *,
    objectives: tuple[float, ...] | None = None,
) -> SequentialResultTable:
    rows = []
    for index, (point_id, value) in enumerate(zip(point_ids, values, strict=True)):
        metrics = {"objective": objectives[index]} if objectives is not None else {}
        rows.append(
            SequentialPointResult(
                index=index,
                point_id=point_id,
                dataset_id=f"scan-{index + 1}",
                variables={},
                status="ok",
                attempts=1,
                parameters={
                    "a": ParameterEstimate(
                        "a",
                        value,
                        "angstrom",
                        uncertainty=0.01,
                        provenance={"fixture": study_id},
                    )
                },
                metrics=metrics,
            )
        )
    return SequentialResultTable(study_id, tuple(rows))


if __name__ == "__main__":
    unittest.main()
