"""Tests for sequential workflow orchestration."""

from __future__ import annotations

import unittest

from rietveld_next.workflows import (
    RetryPolicy,
    SequentialPointSpec,
    SequentialResultTable,
    SequentialRunner,
    build_dashboard_data,
    build_residual_heatmap_data,
    export_parameter_evolution,
)


class SequentialRunnerTests(unittest.TestCase):
    """Validate deterministic sequential execution and table exports."""

    def test_runner_retries_and_uses_previous_successful_parameters(self) -> None:
        points = (
            SequentialPointSpec("p1", "scan-1", {"temperature_k": 300.0}),
            SequentialPointSpec("p2", "scan-2", {"temperature_k": 310.0}),
            SequentialPointSpec("p3", "scan-3", {"temperature_k": 320.0}),
        )
        seen_initials: list[tuple[str, int, float]] = []

        def refine(request):
            seen_initials.append((request.point.point_id, request.attempt, request.initial_parameters["a"]))
            if request.point.point_id == "p2" and request.attempt == 1:
                return {"status": "error", "error": "synthetic retry"}
            value = {"p1": 1.0, "p2": 2.0, "p3": 3.0}[request.point.point_id]
            return {
                "status": "ok",
                "parameters": {
                    "a": {
                        "value": value,
                        "unit": "angstrom",
                        "uncertainty": 0.01,
                        "provenance": {"handler": "synthetic"},
                    }
                },
                "metrics": {"objective": 10.0 - value},
                "residuals": [value, -value],
            }

        table = SequentialRunner(
            "study",
            points,
            {"a": 0.5},
            refine,
            retry_policy=RetryPolicy(max_attempts=2),
        ).run()

        self.assertTrue(table.succeeded)
        self.assertEqual([row.attempts for row in table.rows], [1, 2, 1])
        self.assertEqual(
            seen_initials,
            [("p1", 1, 0.5), ("p2", 1, 1.0), ("p2", 2, 1.0), ("p3", 1, 2.0)],
        )
        self.assertEqual([action.step_id for action in table.actions], ["p1:attempt-1", "p2:attempt-1", "p2:attempt-2", "p3:attempt-1"])

        evolution = export_parameter_evolution(table, ("a",))
        self.assertEqual([row["value"] for row in evolution], [1.0, 2.0, 3.0])
        self.assertEqual(evolution[0]["unit"], "angstrom")
        self.assertEqual(evolution[0]["uncertainty"], 0.01)

        dashboard = build_dashboard_data(table)
        self.assertEqual(dashboard["status_counts"], {"ok": 3})
        self.assertIn("objective", dashboard["metrics"])

        heatmap = build_residual_heatmap_data(table)
        self.assertEqual(heatmap["point_ids"], ["p1", "p2", "p3"])
        self.assertEqual(heatmap["values"][1], [2.0, -2.0])

    def test_retry_exhaustion_records_structured_error(self) -> None:
        point = SequentialPointSpec("p1", "scan-1")

        def fail(_request):
            return {"status": "error", "error": "not converged"}

        table = SequentialRunner(
            "study",
            (point,),
            {"scale": 1.0},
            fail,
            retry_policy=RetryPolicy(max_attempts=2),
        ).run()

        self.assertFalse(table.succeeded)
        self.assertEqual(table.rows[0].attempts, 2)
        self.assertEqual(table.rows[0].error, "not converged")
        self.assertEqual([action.status for action in table.actions], ["error", "error"])

    def test_heatmap_rejects_ragged_residual_vectors(self) -> None:
        table = SequentialResultTable(
            "study",
            (
                _row("p1", [1.0, 2.0]),
                _row("p2", [1.0]),
            ),
        )

        with self.assertRaisesRegex(ValueError, "equal residual vector lengths"):
            build_residual_heatmap_data(table)


def _row(point_id: str, residuals: list[float]):
    from rietveld_next.workflows import SequentialPointResult

    index = 0 if point_id == "p1" else 1
    return SequentialPointResult(
        index=index,
        point_id=point_id,
        dataset_id=f"scan-{index}",
        variables={},
        status="ok",
        attempts=1,
        residuals=tuple(residuals),
    )


if __name__ == "__main__":
    unittest.main()
