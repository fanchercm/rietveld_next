"""Deterministic tool contracts for AI-mediated workflows."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


ToolHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class ToolField:
    """Field metadata for an AI-callable deterministic tool contract.

    Args:
        name: Stable field name.
        field_type: Human-readable scalar or structured type name.
        description: Short field purpose.
        required: Whether the field is required in the payload.
        unit: Scientific unit when the value has dimensional meaning.
        bounds: Optional inclusive numeric bounds.

    Raises:
        ValueError: If names, type labels, units, or bounds are invalid.
    """

    name: str
    field_type: str
    description: str
    required: bool = True
    unit: str | None = None
    bounds: tuple[float | None, float | None] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ToolField.name must be non-empty")
        if not self.field_type:
            raise ValueError("ToolField.field_type must be non-empty")
        if not self.description:
            raise ValueError("ToolField.description must be non-empty")
        if self.unit is not None and not self.unit:
            raise ValueError("ToolField.unit must be non-empty when provided")
        if self.bounds is not None:
            lower, upper = self.bounds
            if lower is not None and upper is not None and lower > upper:
                raise ValueError("ToolField.bounds lower value cannot exceed upper value")

    def to_schema(self) -> Mapping[str, Any]:
        """Return a JSON-like schema payload for this field."""

        payload: dict[str, Any] = {
            "name": self.name,
            "type": self.field_type,
            "description": self.description,
            "required": self.required,
        }
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.bounds is not None:
            payload["bounds"] = self.bounds
        return MappingProxyType(payload)


@dataclass(frozen=True)
class ToolContract:
    """Schema-like contract for an AI-callable deterministic tool."""

    name: str
    input_fields: tuple[str, ...]
    output_fields: tuple[str, ...]
    description: str
    version: str = "1"
    input_schema: tuple[ToolField, ...] = ()
    output_schema: tuple[ToolField, ...] = ()
    mutates_state: bool = False
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ToolContract.name must be non-empty")
        if not self.description:
            raise ValueError("ToolContract.description must be non-empty")
        if not self.version:
            raise ValueError("ToolContract.version must be non-empty")
        _validate_field_names("input_fields", self.input_fields)
        _validate_field_names("output_fields", self.output_fields)
        _validate_unique("input_fields", self.input_fields)
        _validate_unique("output_fields", self.output_fields)
        _validate_schema_names("input_schema", self.input_schema, self.input_fields)
        _validate_schema_names("output_schema", self.output_schema, self.output_fields)
        object.__setattr__(
            self,
            "input_schema",
            _complete_schema(self.input_schema, self.input_fields, "input"),
        )
        object.__setattr__(
            self,
            "output_schema",
            _complete_schema(self.output_schema, self.output_fields, "output"),
        )

    def to_schema(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like contract payload."""

        return MappingProxyType(
            {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "inputs": tuple(field.to_schema() for field in self.input_schema),
                "outputs": tuple(field.to_schema() for field in self.output_schema),
                "mutates_state": self.mutates_state,
                "requires_approval": self.requires_approval,
            }
        )


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

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic viewer/replay payload for this log entry."""

        payload: dict[str, Any] = {
            "sequence": self.sequence,
            "tool": self.tool,
            "inputs": dict(self.inputs),
            "status": self.status,
        }
        if self.output is not None:
            payload["output"] = dict(self.output)
        if self.error is not None:
            payload["error"] = self.error
        return MappingProxyType(payload)


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

    @property
    def contracts(self) -> Mapping[str, ToolContract]:
        """Immutable mapping of registered tool contracts."""

        return MappingProxyType(dict(self._contracts))

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

    def contract_schema(self) -> tuple[Mapping[str, Any], ...]:
        """Return registered contracts sorted by tool name for stable display."""

        return tuple(self._contracts[name].to_schema() for name in sorted(self._contracts))

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


def _validate_unique(label: str, fields: Sequence[str]) -> None:
    seen: set[str] = set()
    for field in fields:
        if field in seen:
            raise ValueError(f"ToolContract.{label} contains duplicate field '{field}'")
        seen.add(field)


def _validate_schema_names(label: str, schema: Sequence[ToolField], fields: Sequence[str]) -> None:
    allowed = set(fields)
    for field in schema:
        if field.name not in allowed:
            raise ValueError(f"ToolContract.{label} field '{field.name}' is not declared")


def _complete_schema(schema: Sequence[ToolField], fields: Sequence[str], direction: str) -> tuple[ToolField, ...]:
    by_name = {field.name: field for field in schema}
    return tuple(
        by_name.get(field, ToolField(name=field, field_type="json", description=f"Required {direction} field `{field}`."))
        for field in fields
    )
