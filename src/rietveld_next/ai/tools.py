"""Deterministic tool contracts for AI-mediated workflows."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class ToolContract:
    """Schema-like contract for an AI-callable deterministic tool."""

    name: str
    input_fields: tuple[str, ...]
    output_fields: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ToolContract.name must be non-empty")
        if not self.description:
            raise ValueError("ToolContract.description must be non-empty")
        _validate_field_names("input_fields", self.input_fields)
        _validate_field_names("output_fields", self.output_fields)


@dataclass(frozen=True)
class ToolCallResult:
    """Result of a deterministic tool call."""

    tool: str
    status: str
    output: Mapping[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ok", "error"}:
            raise ValueError("ToolCallResult.status must be 'ok' or 'error'")
        if self.output is not None:
            object.__setattr__(self, "output", MappingProxyType(dict(self.output)))


@dataclass(frozen=True)
class ActionLogEntry:
    """Audit log entry for an AI-mediated deterministic tool call."""

    sequence: int
    tool: str
    inputs: Mapping[str, Any]
    status: str
    output: Mapping[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("ActionLogEntry.sequence must be non-negative")
        if self.status not in {"ok", "error"}:
            raise ValueError("ActionLogEntry.status must be 'ok' or 'error'")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        if self.output is not None:
            object.__setattr__(self, "output", MappingProxyType(dict(self.output)))


class ToolRegistry:
    """Registry that exposes only deterministic tools to AI agents."""

    def __init__(self) -> None:
        self._contracts: dict[str, ToolContract] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._log: list[ActionLogEntry] = []

    @property
    def action_log(self) -> tuple[ActionLogEntry, ...]:
        """Immutable action log for audit and replay diagnostics."""

        return tuple(self._log)

    def register(self, contract: ToolContract, handler: ToolHandler) -> None:
        """Register a deterministic tool handler.

        Args:
            contract: Tool contract with required input and output fields.
            handler: Deterministic callable implementing the tool.

        Raises:
            ValueError: If a tool name is registered twice.
            TypeError: If handler is not callable.
        """

        if contract.name in self._contracts:
            raise ValueError(f"Tool '{contract.name}' is already registered")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._contracts[contract.name] = contract
        self._handlers[contract.name] = handler

    def call_tool(self, name: str, payload: Mapping[str, Any]) -> ToolCallResult:
        """Call a registered deterministic tool and record an action log entry."""

        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        contract = self._contracts.get(name)
        if contract is None:
            return self._record(name=name, payload=payload, status="error", error=f"Unknown tool '{name}'")

        missing_inputs = [field for field in contract.input_fields if field not in payload]
        if missing_inputs:
            return self._record(
                name=name,
                payload=payload,
                status="error",
                error=f"Missing required input fields: {', '.join(missing_inputs)}",
            )

        try:
            output = self._handlers[name](payload)
        except Exception as exc:  # pragma: no cover - behavior tested via result
            return self._record(
                name=name,
                payload=payload,
                status="error",
                error=f"{type(exc).__name__}: {exc}",
            )

        if not isinstance(output, Mapping):
            return self._record(
                name=name,
                payload=payload,
                status="error",
                error="Tool output must be a mapping",
            )

        missing_outputs = [field for field in contract.output_fields if field not in output]
        if missing_outputs:
            return self._record(
                name=name,
                payload=payload,
                status="error",
                error=f"Missing required output fields: {', '.join(missing_outputs)}",
            )

        return self._record(name=name, payload=payload, status="ok", output=output)

    def _record(
        self,
        *,
        name: str,
        payload: Mapping[str, Any],
        status: str,
        output: Mapping[str, Any] | None = None,
        error: str | None = None,
    ) -> ToolCallResult:
        sequence = len(self._log)
        self._log.append(
            ActionLogEntry(
                sequence=sequence,
                tool=name,
                inputs=payload,
                status=status,
                output=output,
                error=error,
            )
        )
        return ToolCallResult(tool=name, status=status, output=output, error=error)


def _validate_field_names(label: str, fields: Sequence[str]) -> None:
    for field in fields:
        if not field:
            raise ValueError(f"ToolContract.{label} entries must be non-empty")
