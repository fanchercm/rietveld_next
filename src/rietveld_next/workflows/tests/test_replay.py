"""Tests for deterministic workflow replay."""

from __future__ import annotations

import unittest

from rietveld_next.workflows import WorkflowStep, replay_workflow


class WorkflowReplayTests(unittest.TestCase):
    """Validate replay behavior and provenance action logs."""

    def test_replays_steps_in_order(self) -> None:
        steps = [
            WorkflowStep("load", "echo", {"value": 1}),
            WorkflowStep("refine", "echo", {"value": 2}),
        ]

        result = replay_workflow(steps, {"echo": lambda payload: {"seen": payload["value"]}})

        self.assertTrue(result.succeeded)
        self.assertEqual([action.step_id for action in result.actions], ["load", "refine"])
        self.assertEqual(result.actions[1].output, {"seen": 2})

    def test_duplicate_step_ids_raise(self) -> None:
        steps = [
            WorkflowStep("same", "echo", {}),
            WorkflowStep("same", "echo", {}),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate workflow step_id"):
            replay_workflow(steps, {"echo": lambda payload: payload})

    def test_missing_handler_fails_closed(self) -> None:
        result = replay_workflow([WorkflowStep("step", "unknown", {})], {})

        self.assertFalse(result.succeeded)
        self.assertEqual(result.actions[0].status, "error")
        self.assertIn("No deterministic handler", result.actions[0].error or "")

    def test_handler_exception_is_logged_and_stops(self) -> None:
        def fail(_: object) -> dict[str, object]:
            raise RuntimeError("boom")

        steps = [
            WorkflowStep("bad", "fail", {}),
            WorkflowStep("after", "echo", {}),
        ]

        result = replay_workflow(steps, {"fail": fail, "echo": lambda payload: payload})

        self.assertEqual(len(result.actions), 1)
        self.assertFalse(result.succeeded)
        self.assertIn("RuntimeError: boom", result.actions[0].error or "")


if __name__ == "__main__":
    unittest.main()
