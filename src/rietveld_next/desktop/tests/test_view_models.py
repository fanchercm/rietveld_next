"""Tests for framework-neutral view models."""

from __future__ import annotations

import unittest

from rietveld_next.desktop import (
    CommandPaletteItem,
    ConstraintRow,
    CorrelationCell,
    CovarianceDetail,
    DiagnosticEntry,
    GuidedWorkflowStep,
    ParameterRow,
    ParameterGraphEdge,
    ParameterGraphNode,
    PatternTrace,
    ProvenanceEntry,
    RecipeStep,
    ReflectionTick,
    ReportSection,
    ResidualSeries,
    SequentialRunRow,
    ValidationMessage,
    ViewCommand,
    build_cif_validation_state,
    build_beginner_guided_workflow_state,
    build_command_palette_state,
    build_constraint_editor_state,
    build_correlation_heatmap_state,
    build_covariance_detail_state,
    build_data_import_state,
    build_diagnostics_state,
    build_expert_mode_state,
    build_parameter_graph_state,
    build_parameter_table_state,
    build_pattern_viewer_state,
    build_provenance_timeline_state,
    build_project_open_state,
    build_refinement_recipe_wizard_state,
    build_report_export_state,
    build_sequential_dashboard_state,
    command_to_workflow_step,
)


class ViewModelTests(unittest.TestCase):
    """Validate UI state and command conversion."""

    def test_idle_state_exposes_open_command(self) -> None:
        state = build_project_open_state()

        self.assertEqual(state.status, "idle")
        self.assertEqual(state.surface, "project_open")
        self.assertEqual(state.commands[0].name, "open_project")

    def test_ready_state_exposes_project_commands(self) -> None:
        state = build_project_open_state(project_id="p1", project_path="project.rnx")

        self.assertEqual(state.status, "ready")
        self.assertEqual([command.name for command in state.commands], ["import_dataset", "validate_cif"])
        self.assertEqual(state.data["project_path"], "project.rnx")

    def test_loading_and_error_is_invalid(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be both loading and error"):
            build_project_open_state(loading=True, error="failed")

    def test_data_import_adds_import_command_when_paths_are_selected(self) -> None:
        state = build_data_import_state(project_id="p1", candidate_paths=("run1.xy", "run2.xy"))

        self.assertEqual(state.status, "ready")
        self.assertEqual(state.surface, "data_import")
        self.assertEqual([command.name for command in state.commands], ["select_import_file", "import_dataset"])
        self.assertEqual(state.commands[1].payload["paths"], ("run1.xy", "run2.xy"))

    def test_data_import_rejects_empty_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate_paths entries must be non-empty"):
            build_data_import_state(project_id="p1", candidate_paths=("run1.xy", ""))

    def test_cif_validation_reports_structured_summary(self) -> None:
        state = build_cif_validation_state(
            project_id="p1",
            cif_path="phase.cif",
            messages=(
                ValidationMessage("warning", "Missing uncertainty", "_cell.length_a"),
                ValidationMessage("error", "Missing space group", "_symmetry_space_group_name_H-M"),
            ),
        )

        self.assertEqual(state.status, "ready")
        self.assertEqual(state.message, "1 error(s), 1 warning(s)")
        self.assertEqual(state.commands[-1].name, "validate_cif")

    def test_cif_validation_rejects_invalid_severity(self) -> None:
        with self.assertRaisesRegex(ValueError, "severity must be info, warning, or error"):
            ValidationMessage("fatal", "Unsupported CIF")

    def test_pattern_viewer_carries_traces_and_ticks(self) -> None:
        trace = PatternTrace("observed", (10.0, 20.0), (100.0, 40.0))
        tick = ReflectionTick("phase-a", 10.4, (1, 1, 1))

        state = build_pattern_viewer_state(project_id="p1", traces=(trace,), ticks=(tick,))

        self.assertEqual(state.surface, "pattern_viewer")
        self.assertEqual(state.data["traces"], (trace,))
        self.assertEqual(state.data["ticks"], (tick,))
        self.assertEqual([command.name for command in state.commands], ["toggle_difference_plot", "toggle_reflection_ticks"])

    def test_pattern_trace_rejects_mismatched_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "same length"):
            PatternTrace("observed", (10.0,), (100.0, 90.0))

    def test_parameter_table_exposes_edit_commands(self) -> None:
        row = ParameterRow("phase.alpha.cell.a", "a lattice", 5.43, "angstrom", bounds=(1.0, 20.0))

        state = build_parameter_table_state(project_id="p1", parameters=(row,))

        self.assertEqual(state.surface, "parameter_table")
        self.assertEqual(state.data["parameters"], (row,))
        self.assertEqual([command.name for command in state.commands], ["update_parameter", "toggle_parameter_vary"])

    def test_parameter_row_rejects_reversed_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "lower bound must not exceed upper bound"):
            ParameterRow("p", "p", 1.0, "angstrom", bounds=(2.0, 1.0))

    def test_parameter_graph_validates_edges_and_exposes_selection_command(self) -> None:
        a_node = ParameterGraphNode("a", "a lattice", "parameter", "phase.alpha.cell.a", 5.43, "angstrom")
        b_node = ParameterGraphNode("b", "b lattice", "parameter", "phase.alpha.cell.b", 5.44, "angstrom")
        edge = ParameterGraphEdge("a", "b", "correlated")

        state = build_parameter_graph_state(project_id="p1", nodes=(a_node, b_node), edges=(edge,))

        self.assertEqual(state.surface, "parameter_graph")
        self.assertEqual(state.data["edges"], (edge,))
        self.assertEqual(state.commands[0].name, "select_parameter_graph_node")

    def test_parameter_graph_rejects_unknown_edge_endpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "edges must reference existing nodes"):
            build_parameter_graph_state(
                project_id="p1",
                nodes=(ParameterGraphNode("a", "a lattice", "parameter"),),
                edges=(ParameterGraphEdge("a", "missing", "constraint"),),
            )

    def test_constraint_editor_summarizes_invalid_constraints(self) -> None:
        state = build_constraint_editor_state(
            project_id="p1",
            constraints=(
                ConstraintRow("c1", "a=b", ("phase.alpha.cell.a", "phase.alpha.cell.b")),
                ConstraintRow("c2", "bad", ("phase.alpha.cell.c",), status="invalid", message="Unknown target"),
            ),
        )

        self.assertEqual(state.surface, "constraint_editor")
        self.assertEqual(state.message, "2 constraint(s), 1 invalid")
        self.assertEqual([command.name for command in state.commands], ["add_constraint", "validate_constraints", "apply_constraints"])

    def test_constraint_row_rejects_empty_targets(self) -> None:
        with self.assertRaisesRegex(ValueError, "target_paths must be non-empty"):
            ConstraintRow("c1", "a=b", ())

    def test_correlation_heatmap_accepts_bounded_cells(self) -> None:
        cell = CorrelationCell("p.a", "p.b", -0.25)

        state = build_correlation_heatmap_state(project_id="p1", parameter_paths=("p.a", "p.b"), cells=(cell,))

        self.assertEqual(state.surface, "correlation_heatmap")
        self.assertEqual(state.data["cells"], (cell,))
        self.assertEqual(state.commands[0].name, "select_correlation_cell")

    def test_correlation_cell_rejects_out_of_range_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "between -1 and 1"):
            CorrelationCell("p.a", "p.b", 1.5)

    def test_covariance_detail_requires_selected_parameter(self) -> None:
        detail = CovarianceDetail("p.a", "p.b", 0.002, 0.5, "angstrom^2")

        state = build_covariance_detail_state(project_id="p1", selected_parameter_path="p.a", details=(detail,))

        self.assertEqual(state.surface, "covariance_detail")
        self.assertEqual(state.data["selected_parameter_path"], "p.a")
        self.assertEqual(state.commands[0].name, "export_covariance_detail")

    def test_covariance_detail_rejects_missing_selection(self) -> None:
        with self.assertRaisesRegex(ValueError, "must appear in covariance details"):
            build_covariance_detail_state(
                project_id="p1",
                selected_parameter_path="p.missing",
                details=(CovarianceDetail("p.a", "p.b", 0.002, 0.5, "angstrom^2"),),
            )

    def test_sequential_dashboard_sorts_runs_by_index(self) -> None:
        state = build_sequential_dashboard_state(
            project_id="p1",
            runs=(
                SequentialRunRow("run-2", 2, "error", {"phase.alpha.cell.a": 5.5}, objective=2.0),
                SequentialRunRow("run-1", 1, "ok", {"phase.alpha.cell.a": 5.4}, objective=1.0),
            ),
            selected_run_id="run-1",
        )

        self.assertEqual(state.surface, "sequential_dashboard")
        self.assertEqual([run.run_id for run in state.data["runs"]], ["run-1", "run-2"])
        self.assertEqual(state.message, "2 run(s), 1 failed")

    def test_sequential_dashboard_rejects_unknown_selected_run(self) -> None:
        with self.assertRaisesRegex(ValueError, "selected_run_id must reference an existing run"):
            build_sequential_dashboard_state(
                project_id="p1",
                runs=(SequentialRunRow("run-1", 1, "ok", {"p.a": 1.0}),),
                selected_run_id="missing",
            )

    def test_diagnostics_state_accepts_residual_series(self) -> None:
        series = ResidualSeries("standardized", (0.1, -0.2, 0.0))
        state = build_diagnostics_state(
            project_id="p1",
            diagnostics=(DiagnosticEntry("residual_runs", "warning", "Runs pattern may be structured"),),
            residual_series=(series,),
        )

        self.assertEqual(state.surface, "diagnostics")
        self.assertEqual(state.message, "1 diagnostic(s), 1 residual series")
        self.assertEqual(state.data["residual_series"], (series,))
        self.assertEqual(
            [command.name for command in state.commands],
            ["inspect_residuals", "acknowledge_diagnostic", "export_diagnostics"],
        )

    def test_residual_series_rejects_empty_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "values must be non-empty"):
            ResidualSeries("standardized", ())

    def test_refinement_recipe_wizard_exposes_active_step_command(self) -> None:
        command = ViewCommand("run_recipe_step", {"project_id": "p1", "stage": "background"}, label="Run stage")
        step = RecipeStep("background", "Fit background", command, status="ready", rationale="Stabilize baseline")

        state = build_refinement_recipe_wizard_state(project_id="p1", steps=(step,), active_step_id="background")

        self.assertEqual(state.surface, "refinement_recipe_wizard")
        self.assertEqual(state.commands[0], command)
        self.assertEqual(state.commands[1].name, "save_refinement_recipe")

    def test_refinement_recipe_wizard_rejects_unknown_active_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "active_step_id must reference an existing recipe step"):
            build_refinement_recipe_wizard_state(
                project_id="p1",
                steps=(RecipeStep("background", "Fit background", ViewCommand("run_recipe_step", {})),),
                active_step_id="missing",
            )

    def test_beginner_guided_workflow_omits_complete_command_when_blocked(self) -> None:
        state = build_beginner_guided_workflow_state(
            project_id="p1",
            steps=(
                GuidedWorkflowStep("open", "Open project", "project_open", completed=True),
                GuidedWorkflowStep("import", "Import data", "data_import", blocked_reason="Project required"),
            ),
            active_step_key="import",
        )

        self.assertEqual(state.surface, "beginner_guided_workflow")
        self.assertEqual(state.message, "1/2 step(s) complete")
        self.assertEqual([command.name for command in state.commands], ["open_guided_workflow_step"])

    def test_beginner_guided_workflow_adds_complete_command_when_unblocked(self) -> None:
        state = build_beginner_guided_workflow_state(
            project_id="p1",
            steps=(GuidedWorkflowStep("import", "Import data", "data_import"),),
            active_step_key="import",
        )

        self.assertEqual([command.name for command in state.commands], ["open_guided_workflow_step", "complete_guided_workflow_step"])

    def test_expert_mode_toggle_points_to_next_state(self) -> None:
        state = build_expert_mode_state(project_id="p1", enabled=False, warnings=("Advanced controls bypass guidance",))

        self.assertEqual(state.surface, "expert_mode")
        self.assertFalse(state.data["enabled"])
        self.assertEqual(state.commands[0].name, "set_expert_mode")
        self.assertEqual(state.commands[0].payload["enabled"], True)

    def test_report_export_requires_sections(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires at least one section"):
            build_report_export_state(project_id="p1", sections=())

    def test_report_export_exposes_formats(self) -> None:
        state = build_report_export_state(
            project_id="p1",
            sections=(ReportSection("summary", "Summary"), ReportSection("diagnostics", "Diagnostics", included=False)),
            formats=("html",),
        )

        self.assertEqual(state.surface, "report_export")
        self.assertEqual(state.commands[0].payload["formats"], ("html",))
        self.assertEqual(state.commands[0].payload["section_keys"], ("summary",))

    def test_report_export_requires_included_section(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires at least one included section"):
            build_report_export_state(project_id="p1", sections=(ReportSection("summary", "Summary", included=False),))

    def test_provenance_timeline_is_sorted_by_sequence(self) -> None:
        state = build_provenance_timeline_state(
            project_id="p1",
            entries=(
                ProvenanceEntry(2, "validate_cif", "ok", "Validated CIF"),
                ProvenanceEntry(1, "import_dataset", "ok", "Imported dataset"),
            ),
        )

        self.assertEqual([entry.sequence for entry in state.data["entries"]], [1, 2])
        self.assertEqual(state.commands[0].name, "replay_provenance")

    def test_command_palette_filters_deterministically(self) -> None:
        open_item = CommandPaletteItem("Open project", ViewCommand("open_project", {}, label="Open"), ("project",))
        report_item = CommandPaletteItem(
            "Export report",
            ViewCommand("export_report", {"project_id": "p1"}, label="Export"),
            ("report", "publication"),
        )

        state = build_command_palette_state(items=(open_item, report_item), query="report")

        self.assertEqual(state.surface, "command_palette")
        self.assertEqual(state.commands, (report_item.command,))
        self.assertEqual(state.data["items"], (report_item,))

    def test_command_palette_rejects_non_string_query(self) -> None:
        with self.assertRaisesRegex(TypeError, "query must be a string"):
            build_command_palette_state(items=(), query=5)  # type: ignore[arg-type]

    def test_command_to_workflow_step_preserves_payload(self) -> None:
        command = ViewCommand("import_dataset", {"project_id": "p1", "path": "data.xy"})

        step = command_to_workflow_step(command, step_id="ui-1")

        self.assertEqual(step.step_id, "ui-1")
        self.assertEqual(step.tool, "import_dataset")
        self.assertEqual(step.inputs, {"project_id": "p1", "path": "data.xy"})


if __name__ == "__main__":
    unittest.main()
