"""Deterministic workflow replay helpers."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


WorkflowHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class WorkflowStep:
    """A replayable workflow step.

    Args:
        step_id: Stable identifier unique within a workflow.
        tool: Deterministic tool or command name to execute.
        inputs: JSON-like tool input payload.

    Raises:
        ValueError: If required identifiers are empty.
        TypeError: If inputs is not a mapping.
    """

    step_id: str
    tool: str
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("WorkflowStep.step_id must be non-empty")
        if not self.tool:
            raise ValueError("WorkflowStep.tool must be non-empty")
        if not isinstance(self.inputs, Mapping):
            raise TypeError("WorkflowStep.inputs must be a mapping")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))


@dataclass(frozen=True)
class WorkflowAction:
    """An executed workflow action suitable for provenance logs."""

    sequence: int
    step_id: str
    tool: str
    inputs: Mapping[str, Any]
    status: str
    output: Mapping[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("WorkflowAction.sequence must be non-negative")
        if self.status not in {"ok", "error"}:
            raise ValueError("WorkflowAction.status must be 'ok' or 'error'")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        if self.output is not None:
            object.__setattr__(self, "output", MappingProxyType(dict(self.output)))


@dataclass(frozen=True)
class WorkflowResult:
    """Result from replaying a workflow."""

    actions: tuple[WorkflowAction, ...]

    @property
    def succeeded(self) -> bool:
        """Whether every action completed successfully."""

        return all(action.status == "ok" for action in self.actions)


def replay_workflow(
    steps: Sequence[WorkflowStep],
    handlers: Mapping[str, WorkflowHandler],
) -> WorkflowResult:
    """Replay workflow steps using deterministic handlers.

    Args:
        steps: Ordered workflow steps.
        handlers: Mapping from tool name to deterministic handler.

    Returns:
        A provenance-ready action log. Execution stops after the first failed
        step so replay order remains deterministic.

    Raises:
        ValueError: If step IDs are duplicated.
        TypeError: If handlers is not a mapping.
    """

    if not isinstance(handlers, Mapping):
        raise TypeError("handlers must be a mapping")
    _validate_unique_step_ids(steps)

    actions: list[WorkflowAction] = []
    for sequence, step in enumerate(steps):
        handler = handlers.get(step.tool)
        if handler is None:
            actions.append(
                WorkflowAction(
                    sequence=sequence,
                    step_id=step.step_id,
                    tool=step.tool,
                    inputs=step.inputs,
                    status="error",
                    error=f"No deterministic handler registered for tool '{step.tool}'",
                )
            )
            break

        try:
            output = handler(step.inputs)
        except Exception as exc:  # pragma: no cover - type tested by behavior
            actions.append(
                WorkflowAction(
                    sequence=sequence,
                    step_id=step.step_id,
                    tool=step.tool,
                    inputs=step.inputs,
                    status="error",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            break

        if not isinstance(output, Mapping):
            actions.append(
                WorkflowAction(
                    sequence=sequence,
                    step_id=step.step_id,
                    tool=step.tool,
                    inputs=step.inputs,
                    status="error",
                    error="Workflow handler output must be a mapping",
                )
            )
            break

        actions.append(
            WorkflowAction(
                sequence=sequence,
                step_id=step.step_id,
                tool=step.tool,
                inputs=step.inputs,
                status="ok",
                output=output,
            )
        )

    return WorkflowResult(actions=tuple(actions))


def _validate_unique_step_ids(steps: Sequence[WorkflowStep]) -> None:
    seen: set[str] = set()
    for step in steps:
        if step.step_id in seen:
            raise ValueError(f"Duplicate workflow step_id '{step.step_id}'")
        seen.add(step.step_id)
