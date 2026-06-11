"""Framework-neutral view models for UI shells."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from rietveld_next.workflows import WorkflowStep


@dataclass(frozen=True)
class ViewCommand:
    """A UI command that can be converted into a replayable workflow step."""

    name: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ViewCommand.name must be non-empty")
        if not isinstance(self.payload, Mapping):
            raise TypeError("ViewCommand.payload must be a mapping")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class ViewState:
    """Framework-neutral UI state for project-oriented screens."""

    status: str
    message: str | None
    commands: tuple[ViewCommand, ...]

    def __post_init__(self) -> None:
        if self.status not in {"idle", "loading", "ready", "error"}:
            raise ValueError("ViewState.status must be idle, loading, ready, or error")


def build_project_open_state(
    *,
    project_id: str | None = None,
    loading: bool = False,
    error: str | None = None,
) -> ViewState:
    """Build view state for a project-open screen."""

    if loading and error is not None:
        raise ValueError("Project open state cannot be both loading and error")
    if loading:
        return ViewState(status="loading", message="Opening project", commands=())
    if error is not None:
        return ViewState(status="error", message=error, commands=(ViewCommand("open_project", {}),))
    if project_id is not None:
        return ViewState(
            status="ready",
            message=f"Project {project_id} is open",
            commands=(
                ViewCommand("import_dataset", {"project_id": project_id}),
                ViewCommand("start_refinement", {"project_id": project_id}),
            ),
        )
    return ViewState(status="idle", message=None, commands=(ViewCommand("open_project", {}),))


def command_to_workflow_step(command: ViewCommand, *, step_id: str) -> WorkflowStep:
    """Convert a UI command to a replayable workflow step."""

    return WorkflowStep(step_id=step_id, tool=command.name, inputs=command.payload)
