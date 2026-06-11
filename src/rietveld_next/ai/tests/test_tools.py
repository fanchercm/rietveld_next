"""Tests for deterministic AI tool contracts."""

from __future__ import annotations

import unittest

from rietveld_next.ai import ToolContract, ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    """Validate AI tool boundary behavior."""

    def test_registered_tool_call_is_logged(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolContract(
                name="diagnose",
                input_fields=("residuals",),
                output_fields=("summary",),
                description="Summarize deterministic diagnostics.",
            ),
            lambda payload: {"summary": f"{len(payload['residuals'])} residuals"},
        )

        result = registry.call_tool("diagnose", {"residuals": [1.0, -1.0]})

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.output, {"summary": "2 residuals"})
        self.assertEqual(registry.action_log[0].tool, "diagnose")
        self.assertEqual(registry.action_log[0].sequence, 0)

    def test_unknown_tool_fails_closed_and_logs(self) -> None:
        registry = ToolRegistry()

        result = registry.call_tool("missing", {})

        self.assertEqual(result.status, "error")
        self.assertIn("Unknown tool", result.error or "")
        self.assertEqual(len(registry.action_log), 1)

    def test_missing_required_input_is_error(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolContract(
                name="run",
                input_fields=("project_id",),
                output_fields=("status",),
                description="Run deterministic action.",
            ),
            lambda payload: {"status": payload["project_id"]},
        )

        result = registry.call_tool("run", {})

        self.assertEqual(result.status, "error")
        self.assertIn("Missing required input fields", result.error or "")

    def test_missing_required_output_is_error(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolContract(
                name="run",
                input_fields=("project_id",),
                output_fields=("status",),
                description="Run deterministic action.",
            ),
            lambda payload: {"project_id": payload["project_id"]},
        )

        result = registry.call_tool("run", {"project_id": "p1"})

        self.assertEqual(result.status, "error")
        self.assertIn("Missing required output fields", result.error or "")


if __name__ == "__main__":
    unittest.main()
