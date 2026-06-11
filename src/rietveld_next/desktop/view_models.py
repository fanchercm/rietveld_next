"""Framework-neutral view models for desktop and web UI shells."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.workflows import WorkflowStep

_VIEW_STATUSES = {"idle", "loading", "ready", "error"}
_VALIDATION_SEVERITIES = {"info", "warning", "error"}
_DIAGNOSTIC_SEVERITIES = {"info", "warning", "error"}
_TRACE_ROLES = {"observed", "calculated", "background", "difference"}
_CONSTRAINT_STATUSES = {"active", "inactive", "invalid"}
_RUN_STATUSES = {"pending", "running", "ok", "error"}
_STEP_STATUSES = {"pending", "ready", "running", "done", "error"}


@dataclass(frozen=True)
class ViewCommand:
    """A UI command that can be converted into a replayable workflow step.

    Args:
        name: Stable deterministic command name.
        payload: JSON-like command input payload.
        label: Optional display label for command palettes and menus.
        description: Optional short user-facing detail.
        shortcut: Optional keyboard shortcut hint.

    Raises:
        ValueError: If command identifiers are empty.
        TypeError: If payload is not a mapping.

    Example:
        >>> command = ViewCommand("open_project", {"path": "demo.rnx"})
        >>> command.name
        'open_project'
    """

    name: str
    payload: Mapping[str, Any]
    label: str | None = None
    description: str | None = None
    shortcut: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ViewCommand.name must be non-empty")
        if not isinstance(self.payload, Mapping):
            raise TypeError("ViewCommand.payload must be a mapping")
        for field_name, value in (
            ("label", self.label),
            ("description", self.description),
            ("shortcut", self.shortcut),
        ):
            if value is not None and not value:
                raise ValueError(f"ViewCommand.{field_name} must be non-empty when provided")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class ViewState:
    """Framework-neutral UI state for project-oriented screens.

    Args:
        status: One of ``idle``, ``loading``, ``ready``, or ``error``.
        message: Optional status or error message.
        commands: Scriptable commands available from the surface.
        surface: Stable surface identifier for routing in a UI shell.
        data: Immutable surface-specific view data.
    """

    status: str
    message: str | None
    commands: tuple[ViewCommand, ...]
    surface: str = "project_open"
    data: Mapping[str, Any] = MappingProxyType({})

    def __post_init__(self) -> None:
        if self.status not in _VIEW_STATUSES:
            raise ValueError("ViewState.status must be idle, loading, ready, or error")
        if not self.surface:
            raise ValueError("ViewState.surface must be non-empty")
        if not isinstance(self.data, Mapping):
            raise TypeError("ViewState.data must be a mapping")
        commands = tuple(self.commands)
        if any(not isinstance(command, ViewCommand) for command in commands):
            raise TypeError("ViewState.commands must contain ViewCommand instances")
        object.__setattr__(self, "commands", commands)
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))


@dataclass(frozen=True)
class ValidationMessage:
    """A structured validation message for import and CIF review surfaces."""

    severity: str
    message: str
    field_path: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in _VALIDATION_SEVERITIES:
            raise ValueError("ValidationMessage.severity must be info, warning, or error")
        if not self.message:
            raise ValueError("ValidationMessage.message must be non-empty")
        if self.field_path is not None and not self.field_path:
            raise ValueError("ValidationMessage.field_path must be non-empty when provided")


@dataclass(frozen=True)
class PatternTrace:
    """A plotted pattern trace with explicit units and equal-length arrays."""

    role: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    x_unit: str = "degree_2theta"
    y_unit: str = "counts"

    def __post_init__(self) -> None:
        if self.role not in _TRACE_ROLES:
            raise ValueError("PatternTrace.role must be observed, calculated, background, or difference")
        if len(self.x_values) != len(self.y_values):
            raise ValueError("PatternTrace x_values and y_values must have the same length")
        if not self.x_values:
            raise ValueError("PatternTrace values must be non-empty")
        if not self.x_unit or not self.y_unit:
            raise ValueError("PatternTrace units must be non-empty")
        object.__setattr__(self, "x_values", tuple(float(value) for value in self.x_values))
        object.__setattr__(self, "y_values", tuple(float(value) for value in self.y_values))


@dataclass(frozen=True)
class ReflectionTick:
    """A reflection marker shown over a pattern trace."""

    phase_id: str
    position: float
    hkl: tuple[int, int, int]
    unit: str = "degree_2theta"

    def __post_init__(self) -> None:
        if not self.phase_id:
            raise ValueError("ReflectionTick.phase_id must be non-empty")
        if len(self.hkl) != 3:
            raise ValueError("ReflectionTick.hkl must contain three Miller indices")
        if not self.unit:
            raise ValueError("ReflectionTick.unit must be non-empty")
        object.__setattr__(self, "position", float(self.position))
        object.__setattr__(self, "hkl", tuple(int(index) for index in self.hkl))


@dataclass(frozen=True)
class ParameterRow:
    """A parameter table row with explicit units, bounds, and refinement flag."""

    path: str
    label: str
    value: float
    unit: str
    vary: bool = True
    bounds: tuple[float | None, float | None] = (None, None)
    uncertainty: float | None = None

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("ParameterRow.path must be non-empty")
        if not self.label:
            raise ValueError("ParameterRow.label must be non-empty")
        if not self.unit:
            raise ValueError("ParameterRow.unit must be non-empty")
        if len(self.bounds) != 2:
            raise ValueError("ParameterRow.bounds must contain lower and upper bounds")
        lower, upper = self.bounds
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("ParameterRow lower bound must not exceed upper bound")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("ParameterRow.uncertainty must be non-negative")
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class DiagnosticEntry:
    """A residual or refinement diagnostic surfaced to the user."""

    kind: str
    severity: str
    message: str
    value: float | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        if not self.kind:
            raise ValueError("DiagnosticEntry.kind must be non-empty")
        if self.severity not in _DIAGNOSTIC_SEVERITIES:
            raise ValueError("DiagnosticEntry.severity must be info, warning, or error")
        if not self.message:
            raise ValueError("DiagnosticEntry.message must be non-empty")
        if self.unit is not None and not self.unit:
            raise ValueError("DiagnosticEntry.unit must be non-empty when provided")
        if self.value is not None:
            object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class ReportSection:
    """A selectable report export section."""

    key: str
    title: str
    included: bool = True

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("ReportSection.key must be non-empty")
        if not self.title:
            raise ValueError("ReportSection.title must be non-empty")


@dataclass(frozen=True)
class ProvenanceEntry:
    """A provenance timeline entry derived from a deterministic UI command."""

    sequence: int
    command_name: str
    status: str
    summary: str

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("ProvenanceEntry.sequence must be non-negative")
        if not self.command_name:
            raise ValueError("ProvenanceEntry.command_name must be non-empty")
        if self.status not in {"pending", "ok", "error"}:
            raise ValueError("ProvenanceEntry.status must be pending, ok, or error")
        if not self.summary:
            raise ValueError("ProvenanceEntry.summary must be non-empty")


@dataclass(frozen=True)
class CommandPaletteItem:
    """A searchable command palette item."""

    title: str
    command: ViewCommand
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("CommandPaletteItem.title must be non-empty")
        if not isinstance(self.command, ViewCommand):
            raise TypeError("CommandPaletteItem.command must be a ViewCommand")
        object.__setattr__(self, "keywords", tuple(keyword for keyword in self.keywords if keyword))


@dataclass(frozen=True)
class ParameterGraphNode:
    """A parameter graph node for constraints, correlations, and dependencies."""

    node_id: str
    label: str
    kind: str
    parameter_path: str | None = None
    value: float | None = None
    unit: str | None = None

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("ParameterGraphNode.node_id must be non-empty")
        if not self.label:
            raise ValueError("ParameterGraphNode.label must be non-empty")
        if not self.kind:
            raise ValueError("ParameterGraphNode.kind must be non-empty")
        if self.parameter_path is not None and not self.parameter_path:
            raise ValueError("ParameterGraphNode.parameter_path must be non-empty when provided")
        if self.unit is not None and not self.unit:
            raise ValueError("ParameterGraphNode.unit must be non-empty when provided")
        if self.value is not None:
            object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class ParameterGraphEdge:
    """A directed parameter graph edge with a named relationship."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("ParameterGraphEdge.source_id must be non-empty")
        if not self.target_id:
            raise ValueError("ParameterGraphEdge.target_id must be non-empty")
        if not self.relation:
            raise ValueError("ParameterGraphEdge.relation must be non-empty")


@dataclass(frozen=True)
class ConstraintRow:
    """A constraint editor row with target parameter paths and validation status."""

    constraint_id: str
    expression: str
    target_paths: tuple[str, ...]
    status: str = "active"
    message: str | None = None

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ValueError("ConstraintRow.constraint_id must be non-empty")
        if not self.expression:
            raise ValueError("ConstraintRow.expression must be non-empty")
        targets = _validated_strings("target_paths", self.target_paths)
        if not targets:
            raise ValueError("ConstraintRow.target_paths must be non-empty")
        if self.status not in _CONSTRAINT_STATUSES:
            raise ValueError("ConstraintRow.status must be active, inactive, or invalid")
        if self.message is not None and not self.message:
            raise ValueError("ConstraintRow.message must be non-empty when provided")
        object.__setattr__(self, "target_paths", targets)


@dataclass(frozen=True)
class CorrelationCell:
    """A single correlation heatmap cell."""

    row_path: str
    column_path: str
    value: float

    def __post_init__(self) -> None:
        if not self.row_path:
            raise ValueError("CorrelationCell.row_path must be non-empty")
        if not self.column_path:
            raise ValueError("CorrelationCell.column_path must be non-empty")
        value = float(self.value)
        if value < -1.0 or value > 1.0:
            raise ValueError("CorrelationCell.value must be between -1 and 1")
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class CovarianceDetail:
    """Covariance and correlation detail for a parameter pair."""

    parameter_path: str
    partner_path: str
    covariance: float
    correlation: float
    covariance_unit: str

    def __post_init__(self) -> None:
        if not self.parameter_path:
            raise ValueError("CovarianceDetail.parameter_path must be non-empty")
        if not self.partner_path:
            raise ValueError("CovarianceDetail.partner_path must be non-empty")
        if not self.covariance_unit:
            raise ValueError("CovarianceDetail.covariance_unit must be non-empty")
        correlation = float(self.correlation)
        if correlation < -1.0 or correlation > 1.0:
            raise ValueError("CovarianceDetail.correlation must be between -1 and 1")
        object.__setattr__(self, "covariance", float(self.covariance))
        object.__setattr__(self, "correlation", correlation)


@dataclass(frozen=True)
class SequentialRunRow:
    """A sequential dashboard row for one refinement run."""

    run_id: str
    index: int
    status: str
    parameter_values: Mapping[str, float]
    objective: float | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("SequentialRunRow.run_id must be non-empty")
        if self.index < 0:
            raise ValueError("SequentialRunRow.index must be non-negative")
        if self.status not in _RUN_STATUSES:
            raise ValueError("SequentialRunRow.status must be pending, running, ok, or error")
        if not isinstance(self.parameter_values, Mapping):
            raise TypeError("SequentialRunRow.parameter_values must be a mapping")
        values = {path: float(value) for path, value in self.parameter_values.items()}
        if any(not path for path in values):
            raise ValueError("SequentialRunRow.parameter_values keys must be non-empty")
        object.__setattr__(self, "parameter_values", MappingProxyType(values))
        if self.objective is not None:
            object.__setattr__(self, "objective", float(self.objective))


@dataclass(frozen=True)
class ResidualSeries:
    """Residual values for diagnostics panels with explicit units."""

    name: str
    values: tuple[float, ...]
    unit: str = "standardized_residual"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ResidualSeries.name must be non-empty")
        if not self.values:
            raise ValueError("ResidualSeries.values must be non-empty")
        if not self.unit:
            raise ValueError("ResidualSeries.unit must be non-empty")
        object.__setattr__(self, "values", tuple(float(value) for value in self.values))


@dataclass(frozen=True)
class RecipeStep:
    """A refinement recipe wizard step backed by a deterministic command."""

    step_id: str
    title: str
    command: ViewCommand
    status: str = "pending"
    rationale: str | None = None

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("RecipeStep.step_id must be non-empty")
        if not self.title:
            raise ValueError("RecipeStep.title must be non-empty")
        if not isinstance(self.command, ViewCommand):
            raise TypeError("RecipeStep.command must be a ViewCommand")
        if self.status not in _STEP_STATUSES:
            raise ValueError("RecipeStep.status must be pending, ready, running, done, or error")
        if self.rationale is not None and not self.rationale:
            raise ValueError("RecipeStep.rationale must be non-empty when provided")


@dataclass(frozen=True)
class GuidedWorkflowStep:
    """A beginner workflow step that routes to a framework-neutral surface."""

    step_key: str
    title: str
    surface: str
    completed: bool = False
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.step_key:
            raise ValueError("GuidedWorkflowStep.step_key must be non-empty")
        if not self.title:
            raise ValueError("GuidedWorkflowStep.title must be non-empty")
        if not self.surface:
            raise ValueError("GuidedWorkflowStep.surface must be non-empty")
        if self.blocked_reason is not None and not self.blocked_reason:
            raise ValueError("GuidedWorkflowStep.blocked_reason must be non-empty when provided")


def build_project_open_state(
    *,
    project_id: str | None = None,
    project_path: str | None = None,
    loading: bool = False,
    error: str | None = None,
) -> ViewState:
    """Build view state for a project-open screen.

    Example:
        >>> build_project_open_state(project_id="p1").commands[0].name
        'import_dataset'
    """

    if loading and error is not None:
        raise ValueError("Project open state cannot be both loading and error")
    if loading:
        return ViewState(status="loading", message="Opening project", commands=(), surface="project_open")
    if error is not None:
        return ViewState(
            status="error",
            message=error,
            commands=(ViewCommand("open_project", {}, label="Open project", shortcut="Ctrl+O"),),
            surface="project_open",
        )
    if project_id is not None:
        return ViewState(
            status="ready",
            message=f"Project {project_id} is open",
            commands=(
                ViewCommand("import_dataset", {"project_id": project_id}, label="Import dataset"),
                ViewCommand("validate_cif", {"project_id": project_id}, label="Validate CIF"),
            ),
            surface="project_open",
            data={"project_id": project_id, "project_path": project_path},
        )
    return ViewState(
        status="idle",
        message=None,
        commands=(ViewCommand("open_project", {}, label="Open project", shortcut="Ctrl+O"),),
        surface="project_open",
    )


def build_data_import_state(
    *,
    project_id: str,
    candidate_paths: Sequence[str] = (),
    loading: bool = False,
    error: str | None = None,
) -> ViewState:
    """Build import-screen state for project data files."""

    _require_project_id(project_id)
    if loading and error is not None:
        raise ValueError("Data import state cannot be both loading and error")
    paths = _validated_strings("candidate_paths", candidate_paths)
    if loading:
        return ViewState(status="loading", message="Importing data", commands=(), surface="data_import")
    if error is not None:
        return ViewState(
            status="error",
            message=error,
            commands=(ViewCommand("select_import_file", {"project_id": project_id}, label="Select data file"),),
            surface="data_import",
            data={"project_id": project_id, "candidate_paths": paths},
        )
    commands = (ViewCommand("select_import_file", {"project_id": project_id}, label="Select data file"),)
    if paths:
        commands += (
            ViewCommand(
                "import_dataset",
                {"project_id": project_id, "paths": paths},
                label="Import selected data",
            ),
        )
    return ViewState(
        status="ready" if paths else "idle",
        message=f"{len(paths)} import file(s) selected" if paths else None,
        commands=commands,
        surface="data_import",
        data={"project_id": project_id, "candidate_paths": paths},
    )


def build_cif_validation_state(
    *,
    project_id: str,
    cif_path: str | None = None,
    messages: Sequence[ValidationMessage] = (),
    loading: bool = False,
    error: str | None = None,
) -> ViewState:
    """Build CIF validation surface state with structured validation messages."""

    _require_project_id(project_id)
    if loading and error is not None:
        raise ValueError("CIF validation state cannot be both loading and error")
    _validate_optional_string("cif_path", cif_path)
    validation_messages = tuple(messages)
    if loading:
        return ViewState(status="loading", message="Validating CIF", commands=(), surface="cif_validation")
    if error is not None:
        return ViewState(
            status="error",
            message=error,
            commands=(ViewCommand("select_cif", {"project_id": project_id}, label="Select CIF"),),
            surface="cif_validation",
            data={"project_id": project_id, "cif_path": cif_path, "messages": validation_messages},
        )
    commands = (ViewCommand("select_cif", {"project_id": project_id}, label="Select CIF"),)
    if cif_path is not None:
        commands += (
            ViewCommand(
                "validate_cif",
                {"project_id": project_id, "cif_path": cif_path},
                label="Validate CIF",
            ),
        )
    return ViewState(
        status="ready" if cif_path is not None else "idle",
        message=_validation_summary(validation_messages) if validation_messages else None,
        commands=commands,
        surface="cif_validation",
        data={"project_id": project_id, "cif_path": cif_path, "messages": validation_messages},
    )


def build_pattern_viewer_state(
    *,
    project_id: str,
    traces: Sequence[PatternTrace],
    ticks: Sequence[ReflectionTick] = (),
    selected_trace_role: str = "observed",
) -> ViewState:
    """Build pattern viewer state from precomputed plot traces and ticks."""

    _require_project_id(project_id)
    if selected_trace_role not in _TRACE_ROLES:
        raise ValueError("selected_trace_role must be observed, calculated, background, or difference")
    plot_traces = tuple(traces)
    if not plot_traces:
        raise ValueError("Pattern viewer requires at least one trace")
    reflection_ticks = tuple(ticks)
    return ViewState(
        status="ready",
        message=f"{len(plot_traces)} trace(s), {len(reflection_ticks)} reflection tick(s)",
        commands=(
            ViewCommand("toggle_difference_plot", {"project_id": project_id}, label="Toggle difference plot"),
            ViewCommand("toggle_reflection_ticks", {"project_id": project_id}, label="Toggle reflection ticks"),
        ),
        surface="pattern_viewer",
        data={
            "project_id": project_id,
            "traces": plot_traces,
            "ticks": reflection_ticks,
            "selected_trace_role": selected_trace_role,
        },
    )


def build_parameter_table_state(
    *,
    project_id: str,
    parameters: Sequence[ParameterRow],
) -> ViewState:
    """Build editable parameter table state."""

    _require_project_id(project_id)
    rows = tuple(parameters)
    if not rows:
        raise ValueError("Parameter table requires at least one parameter")
    return ViewState(
        status="ready",
        message=f"{len(rows)} parameter(s)",
        commands=(
            ViewCommand("update_parameter", {"project_id": project_id}, label="Update parameter"),
            ViewCommand("toggle_parameter_vary", {"project_id": project_id}, label="Toggle refinement flag"),
        ),
        surface="parameter_table",
        data={"project_id": project_id, "parameters": rows},
    )


def build_parameter_graph_state(
    *,
    project_id: str,
    nodes: Sequence[ParameterGraphNode],
    edges: Sequence[ParameterGraphEdge] = (),
) -> ViewState:
    """Build parameter graph state for dependency and relationship views."""

    _require_project_id(project_id)
    graph_nodes = tuple(nodes)
    if not graph_nodes:
        raise ValueError("Parameter graph requires at least one node")
    graph_edges = tuple(edges)
    node_ids = {node.node_id for node in graph_nodes}
    for edge in graph_edges:
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            raise ValueError("Parameter graph edges must reference existing nodes")
    return ViewState(
        status="ready",
        message=f"{len(graph_nodes)} node(s), {len(graph_edges)} edge(s)",
        commands=(ViewCommand("select_parameter_graph_node", {"project_id": project_id}, label="Select parameter"),),
        surface="parameter_graph",
        data={"project_id": project_id, "nodes": graph_nodes, "edges": graph_edges},
    )


def build_constraint_editor_state(
    *,
    project_id: str,
    constraints: Sequence[ConstraintRow] = (),
) -> ViewState:
    """Build constraint editor state with scriptable edit and validation commands."""

    _require_project_id(project_id)
    rows = tuple(constraints)
    invalid_count = sum(1 for row in rows if row.status == "invalid")
    return ViewState(
        status="ready",
        message=f"{len(rows)} constraint(s), {invalid_count} invalid",
        commands=(
            ViewCommand("add_constraint", {"project_id": project_id}, label="Add constraint"),
            ViewCommand("validate_constraints", {"project_id": project_id}, label="Validate constraints"),
            ViewCommand("apply_constraints", {"project_id": project_id}, label="Apply constraints"),
        ),
        surface="constraint_editor",
        data={"project_id": project_id, "constraints": rows},
    )


def build_correlation_heatmap_state(
    *,
    project_id: str,
    parameter_paths: Sequence[str],
    cells: Sequence[CorrelationCell],
) -> ViewState:
    """Build correlation heatmap state from bounded correlation cells."""

    _require_project_id(project_id)
    paths = _validated_strings("parameter_paths", parameter_paths)
    if not paths:
        raise ValueError("Correlation heatmap requires at least one parameter path")
    heatmap_cells = tuple(cells)
    if not heatmap_cells:
        raise ValueError("Correlation heatmap requires at least one cell")
    allowed_paths = set(paths)
    for cell in heatmap_cells:
        if cell.row_path not in allowed_paths or cell.column_path not in allowed_paths:
            raise ValueError("Correlation heatmap cells must reference parameter_paths")
    return ViewState(
        status="ready",
        message=f"{len(paths)} parameter(s)",
        commands=(ViewCommand("select_correlation_cell", {"project_id": project_id}, label="Select correlation"),),
        surface="correlation_heatmap",
        data={"project_id": project_id, "parameter_paths": paths, "cells": heatmap_cells},
    )


def build_covariance_detail_state(
    *,
    project_id: str,
    selected_parameter_path: str,
    details: Sequence[CovarianceDetail],
) -> ViewState:
    """Build covariance detail state for one selected parameter."""

    _require_project_id(project_id)
    if not selected_parameter_path:
        raise ValueError("selected_parameter_path must be non-empty")
    covariance_details = tuple(details)
    if not covariance_details:
        raise ValueError("Covariance detail requires at least one detail row")
    if all(detail.parameter_path != selected_parameter_path for detail in covariance_details):
        raise ValueError("selected_parameter_path must appear in covariance details")
    return ViewState(
        status="ready",
        message=f"{len(covariance_details)} covariance detail row(s)",
        commands=(ViewCommand("export_covariance_detail", {"project_id": project_id}, label="Export covariance detail"),),
        surface="covariance_detail",
        data={
            "project_id": project_id,
            "selected_parameter_path": selected_parameter_path,
            "details": covariance_details,
        },
    )


def build_sequential_dashboard_state(
    *,
    project_id: str,
    runs: Sequence[SequentialRunRow],
    selected_run_id: str | None = None,
) -> ViewState:
    """Build sequential refinement dashboard state ordered by run index."""

    _require_project_id(project_id)
    run_rows = tuple(sorted(runs, key=lambda run: run.index))
    if not run_rows:
        raise ValueError("Sequential dashboard requires at least one run")
    _validate_optional_string("selected_run_id", selected_run_id)
    run_ids = {run.run_id for run in run_rows}
    if selected_run_id is not None and selected_run_id not in run_ids:
        raise ValueError("selected_run_id must reference an existing run")
    failed_count = sum(1 for run in run_rows if run.status == "error")
    return ViewState(
        status="ready",
        message=f"{len(run_rows)} run(s), {failed_count} failed",
        commands=(
            ViewCommand("open_sequential_run", {"project_id": project_id}, label="Open run"),
            ViewCommand("export_sequential_table", {"project_id": project_id}, label="Export sequential table"),
        ),
        surface="sequential_dashboard",
        data={"project_id": project_id, "runs": run_rows, "selected_run_id": selected_run_id},
    )


def build_diagnostics_state(
    *,
    project_id: str,
    diagnostics: Sequence[DiagnosticEntry],
    residual_series: Sequence[ResidualSeries] = (),
) -> ViewState:
    """Build residual diagnostics panel state."""

    _require_project_id(project_id)
    entries = tuple(diagnostics)
    series = tuple(residual_series)
    return ViewState(
        status="ready",
        message=f"{len(entries)} diagnostic(s), {len(series)} residual series",
        commands=(
            ViewCommand("inspect_residuals", {"project_id": project_id}, label="Inspect residuals"),
            ViewCommand("acknowledge_diagnostic", {"project_id": project_id}, label="Acknowledge diagnostic"),
            ViewCommand("export_diagnostics", {"project_id": project_id}, label="Export diagnostics"),
        ),
        surface="diagnostics",
        data={"project_id": project_id, "diagnostics": entries, "residual_series": series},
    )


def build_refinement_recipe_wizard_state(
    *,
    project_id: str,
    steps: Sequence[RecipeStep],
    active_step_id: str,
) -> ViewState:
    """Build staged refinement recipe wizard state."""

    _require_project_id(project_id)
    recipe_steps = tuple(steps)
    if not recipe_steps:
        raise ValueError("Refinement recipe wizard requires at least one step")
    if not active_step_id:
        raise ValueError("active_step_id must be non-empty")
    active_steps = tuple(step for step in recipe_steps if step.step_id == active_step_id)
    if not active_steps:
        raise ValueError("active_step_id must reference an existing recipe step")
    active_step = active_steps[0]
    return ViewState(
        status="ready",
        message=f"{len(recipe_steps)} recipe step(s)",
        commands=(
            active_step.command,
            ViewCommand("save_refinement_recipe", {"project_id": project_id}, label="Save recipe"),
        ),
        surface="refinement_recipe_wizard",
        data={"project_id": project_id, "steps": recipe_steps, "active_step_id": active_step_id},
    )


def build_beginner_guided_workflow_state(
    *,
    project_id: str,
    steps: Sequence[GuidedWorkflowStep],
    active_step_key: str,
) -> ViewState:
    """Build beginner guided workflow state with deterministic progress data."""

    _require_project_id(project_id)
    workflow_steps = tuple(steps)
    if not workflow_steps:
        raise ValueError("Beginner guided workflow requires at least one step")
    if not active_step_key:
        raise ValueError("active_step_key must be non-empty")
    active_matches = tuple(step for step in workflow_steps if step.step_key == active_step_key)
    if not active_matches:
        raise ValueError("active_step_key must reference an existing workflow step")
    completed_count = sum(1 for step in workflow_steps if step.completed)
    active_step = active_matches[0]
    commands = (
        ViewCommand(
            "open_guided_workflow_step",
            {"project_id": project_id, "surface": active_step.surface, "step_key": active_step.step_key},
            label="Open guided step",
        ),
    )
    if active_step.blocked_reason is None:
        commands += (
            ViewCommand(
                "complete_guided_workflow_step",
                {"project_id": project_id, "step_key": active_step.step_key},
                label="Complete guided step",
            ),
        )
    return ViewState(
        status="ready",
        message=f"{completed_count}/{len(workflow_steps)} step(s) complete",
        commands=commands,
        surface="beginner_guided_workflow",
        data={"project_id": project_id, "steps": workflow_steps, "active_step_key": active_step_key},
    )


def build_expert_mode_state(
    *,
    project_id: str,
    enabled: bool,
    warnings: Sequence[str] = (),
) -> ViewState:
    """Build expert mode toggle state without changing scientific behavior."""

    _require_project_id(project_id)
    warning_messages = _validated_strings("warnings", warnings)
    next_enabled = not enabled
    return ViewState(
        status="ready",
        message="Expert mode enabled" if enabled else "Expert mode disabled",
        commands=(
            ViewCommand(
                "set_expert_mode",
                {"project_id": project_id, "enabled": next_enabled},
                label="Disable expert mode" if enabled else "Enable expert mode",
            ),
        ),
        surface="expert_mode",
        data={"project_id": project_id, "enabled": enabled, "warnings": warning_messages},
    )


def build_report_export_state(
    *,
    project_id: str,
    sections: Sequence[ReportSection],
    formats: Sequence[str] = ("html", "pdf"),
) -> ViewState:
    """Build report export state with selectable sections and formats."""

    _require_project_id(project_id)
    report_sections = tuple(sections)
    if not report_sections:
        raise ValueError("Report export requires at least one section")
    export_formats = _validated_strings("formats", formats)
    if not export_formats:
        raise ValueError("Report export requires at least one format")
    included_section_keys = tuple(section.key for section in report_sections if section.included)
    if not included_section_keys:
        raise ValueError("Report export requires at least one included section")
    return ViewState(
        status="ready",
        message=f"{len(report_sections)} report section(s)",
        commands=(
            ViewCommand(
                "export_report",
                {"project_id": project_id, "formats": export_formats, "section_keys": included_section_keys},
                label="Export report",
            ),
        ),
        surface="report_export",
        data={
            "project_id": project_id,
            "sections": report_sections,
            "formats": export_formats,
            "included_section_keys": included_section_keys,
        },
    )


def build_provenance_timeline_state(
    *,
    project_id: str,
    entries: Sequence[ProvenanceEntry],
) -> ViewState:
    """Build provenance timeline state ordered by event sequence."""

    _require_project_id(project_id)
    timeline = tuple(sorted(entries, key=lambda entry: entry.sequence))
    return ViewState(
        status="ready",
        message=f"{len(timeline)} provenance event(s)",
        commands=(ViewCommand("replay_provenance", {"project_id": project_id}, label="Replay provenance"),),
        surface="provenance_timeline",
        data={"project_id": project_id, "entries": timeline},
    )


def build_command_palette_state(
    *,
    items: Sequence[CommandPaletteItem],
    query: str = "",
) -> ViewState:
    """Build keyboard command palette state using deterministic text filtering."""

    if query is None:
        raise TypeError("query must be a string")
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    palette_items = tuple(items)
    filtered_items = _filter_palette_items(palette_items, query)
    return ViewState(
        status="ready",
        message=f"{len(filtered_items)} command(s)",
        commands=tuple(item.command for item in filtered_items),
        surface="command_palette",
        data={"items": filtered_items, "query": query},
    )


def command_to_workflow_step(command: ViewCommand, *, step_id: str) -> WorkflowStep:
    """Convert a UI command to a replayable workflow step.

    Args:
        command: UI command selected by the user or a keyboard workflow.
        step_id: Stable replay step identifier.

    Returns:
        A deterministic workflow step preserving the command payload.
    """

    return WorkflowStep(step_id=step_id, tool=command.name, inputs=command.payload)


def _require_project_id(project_id: str) -> None:
    if not project_id:
        raise ValueError("project_id must be non-empty")


def _validate_optional_string(name: str, value: str | None) -> None:
    if value is not None and not value:
        raise ValueError(f"{name} must be non-empty when provided")


def _validated_strings(name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise TypeError(f"{name} must be a sequence of strings, not a string")
    output = tuple(values)
    if any(not isinstance(value, str) for value in output):
        raise TypeError(f"{name} entries must be strings")
    if any(not value for value in output):
        raise ValueError(f"{name} entries must be non-empty")
    return output


def _validation_summary(messages: Sequence[ValidationMessage]) -> str:
    errors = sum(1 for message in messages if message.severity == "error")
    warnings = sum(1 for message in messages if message.severity == "warning")
    if errors:
        return f"{errors} error(s), {warnings} warning(s)"
    if warnings:
        return f"{warnings} warning(s)"
    return "No CIF validation issues"


def _filter_palette_items(
    items: Sequence[CommandPaletteItem],
    query: str,
) -> tuple[CommandPaletteItem, ...]:
    normalized_query = query.strip().lower()
    if not normalized_query:
        return tuple(items)
    matches: list[CommandPaletteItem] = []
    for item in items:
        haystack = " ".join((item.title, item.command.name, *(item.keywords))).lower()
        if normalized_query in haystack:
            matches.append(item)
    return tuple(matches)
