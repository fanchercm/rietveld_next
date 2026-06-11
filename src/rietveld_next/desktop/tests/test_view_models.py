"""Tests for framework-neutral view models."""

from __future__ import annotations

import unittest

from rietveld_next.desktop import ViewCommand, build_project_open_state, command_to_workflow_step


class ViewModelTests(unittest.TestCase):
    """Validate UI state and command conversion."""

    def test_idle_state_exposes_open_command(self) -> None:
        state = build_project_open_state()

        self.assertEqual(state.status, "idle")
        self.assertEqual(state.commands[0].name, "open_project")

    def test_ready_state_exposes_project_commands(self) -> None:
        state = build_project_open_state(project_id="p1")

        self.assertEqual(state.status, "ready")
        self.assertEqual([command.name for command in state.commands], ["import_dataset", "start_refinement"])

    def test_loading_and_error_is_invalid(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be both loading and error"):
            build_project_open_state(loading=True, error="failed")

    def test_command_to_workflow_step_preserves_payload(self) -> None:
        command = ViewCommand("import_dataset", {"project_id": "p1", "path": "data.xy"})

        step = command_to_workflow_step(command, step_id="ui-1")

        self.assertEqual(step.step_id, "ui-1")
        self.assertEqual(step.tool, "import_dataset")
        self.assertEqual(step.inputs, {"project_id": "p1", "path": "data.xy"})


if __name__ == "__main__":
    unittest.main()
