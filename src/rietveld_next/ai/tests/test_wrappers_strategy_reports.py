"""Tests for AI tool wrappers, strategy, reports, approvals, evals, and planning."""

from __future__ import annotations

import unittest

from rietveld_next.ai import (
    ApprovalLedger,
    Citation,
    action_log_viewer_payload,
    add_constraint_tool,
    compare_models_tool,
    create_refinement_tool_registry,
    default_ai_evaluation_suite,
    default_strategy_engine,
    freeze_parameter_tool,
    generate_copilot_report,
    plan_autonomous_recipe,
    rollback_tool,
    run_refinement_tool,
    set_refinement_flags_tool,
)


class WrapperStrategyReportTests(unittest.TestCase):
    """Validate deterministic wrappers and agent payload helpers."""

    def test_mutating_wrappers_require_approval_and_do_not_mutate_input(self) -> None:
        model_state = {"parameters": {"scale": {"value": 1.0, "refine": True}}}

        with self.assertRaises(PermissionError):
            freeze_parameter_tool(
                {
                    "model_state": model_state,
                    "parameter": "scale",
                    "provenance": {"source": "test"},
                }
            )

        result = freeze_parameter_tool(
            {
                "model_state": model_state,
                "parameter": "scale",
                "provenance": {"source": "test"},
            },
            approved=True,
        )

        self.assertEqual(result["changed_parameters"], ("scale",))
        self.assertFalse(result["model_state"]["parameters"]["scale"]["refine"])
        self.assertTrue(model_state["parameters"]["scale"]["refine"])

    def test_set_flags_add_constraint_and_rollback_return_copied_state(self) -> None:
        model_state = {"parameters": {"a": {"value": 1.0, "refine": True}}, "constraints": ()}

        flagged = set_refinement_flags_tool(
            {
                "model_state": model_state,
                "flags": {"a": False},
                "provenance": {"source": "test"},
            },
            approved=True,
        )
        constrained = add_constraint_tool(
            {
                "model_state": flagged["model_state"],
                "constraint": {"constraint_id": "c1", "expression": "a = 1", "parameters": ("a",)},
                "provenance": {"source": "test"},
            },
            approved=True,
        )
        restored = rollback_tool(
            {
                "snapshots": ({"snapshot_id": "s0", "model_state": model_state},),
                "snapshot_id": "s0",
                "provenance": {"source": "test"},
            },
            approved=True,
        )

        self.assertEqual(flagged["changed_parameters"], ("a",))
        self.assertEqual(constrained["constraint_id"], "c1")
        self.assertEqual(restored["snapshot_id"], "s0")
        self.assertEqual(model_state["constraints"], ())

    def test_compare_models_ranks_by_rwp_then_aic(self) -> None:
        result = compare_models_tool(
            {
                "models": (
                    {"model_id": "m2", "metrics": {"rwp": 9.0, "aic": 5.0}},
                    {"model_id": "m1", "metrics": {"rwp": 9.0, "aic": 3.0}},
                )
            }
        )

        self.assertEqual(result["best_model_id"], "m1")
        self.assertEqual(result["comparisons"][0]["rank"], 1)

    def test_run_refinement_wraps_backend_result_with_stable_run_id(self) -> None:
        payload = {
            "project_id": "p1",
            "request": {"cycles": 2},
            "backend_result": {
                "status": "completed",
                "model_state": {"parameters": {}},
                "metrics": {"rwp": 10.0},
                "diagnostics": (),
            },
            "provenance": {"source": "test"},
        }

        first = run_refinement_tool(payload, approved=True)
        second = run_refinement_tool(payload, approved=True)

        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(first["metrics"]["rwp"], 10.0)

    def test_registry_logs_and_evaluation_suite_passes(self) -> None:
        registry = create_refinement_tool_registry()

        result = registry.call_tool("diagnose_residuals", {"residuals": [0.0, 1.0, -1.0, 0.5]})
        evaluation = default_ai_evaluation_suite().run(registry)
        viewer = action_log_viewer_payload(registry.action_log)

        self.assertEqual(result.status, "ok")
        self.assertEqual(evaluation["passed_count"], evaluation["task_count"])
        self.assertGreaterEqual(viewer["entry_count"], 1)

    def test_strategy_and_recipe_planner_block_disallowed_tools(self) -> None:
        context = {
            "residuals": [1.0, -1.0],
            "candidate_models": (
                {"model_id": "m1", "metrics": {"rwp": 8.0}},
                {"model_id": "m2", "metrics": {"rwp": 9.0}},
            ),
        }

        recommendations = default_strategy_engine().recommend(context)
        plan = plan_autonomous_recipe(
            goal="diagnose and compare",
            context=context,
            allowed_tools=("diagnose_residuals",),
        )

        self.assertEqual(len(recommendations), 2)
        self.assertEqual(plan.steps[0].tool, "diagnose_residuals")
        self.assertEqual(plan.blocked_reasons, ("Tool `compare_models` is not allowed for this recipe.",))

    def test_approval_ledger_and_report_payloads(self) -> None:
        ledger = ApprovalLedger()
        checkpoint = ledger.request(tool="rollback", payload={"snapshot_id": "s0"}, rationale="Validation regressed.")
        decided = ledger.decide(checkpoint.checkpoint_id, approved=True, reviewer="unit-test")
        registry = create_refinement_tool_registry()
        registry.call_tool("missing", {})
        report = generate_copilot_report(
            project_id="p1",
            diagnostics=({"code": "residual_pattern", "severity": "info"},),
            recommendations=(),
            action_log=registry.action_log,
            citations=(Citation("c1", "knowledge-base", "Rietveld refinement notes"),),
        )

        self.assertTrue(ledger.is_approved(checkpoint.checkpoint_id))
        self.assertEqual(decided.status, "approved")
        self.assertIn("Project p1", report.summary)
        self.assertEqual(report.citations[0]["citation_id"], "c1")


if __name__ == "__main__":
    unittest.main()
