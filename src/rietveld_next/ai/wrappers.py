"""Deterministic AI tool wrappers for refinement agent workflows."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from copy import deepcopy
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.ai.diagnostics import diagnose_residuals
from rietveld_next.ai.safety import evaluate_tool_call_safety, safety_allows
from rietveld_next.ai.tools import ToolContract, ToolField, ToolRegistry


TOOL_CONTRACTS: tuple[ToolContract, ...] = (
    ToolContract(
        name="run_refinement",
        input_fields=("project_id", "request", "backend_result"),
        output_fields=("run_id", "status", "model_state", "metrics", "diagnostics"),
        description="Wrap a deterministic refinement backend result with provenance and diagnostics.",
        input_schema=(
            ToolField("project_id", "string", "Stable project identifier."),
            ToolField("request", "object", "Deterministic refinement request."),
            ToolField("backend_result", "object", "Result from a deterministic refinement backend."),
        ),
        output_schema=(
            ToolField("run_id", "string", "Stable run identifier derived from request content."),
            ToolField("status", "string", "Backend execution status."),
            ToolField("model_state", "object", "Backend-produced model state."),
            ToolField("metrics", "object", "Backend-produced metrics."),
            ToolField("diagnostics", "array", "Backend or wrapper diagnostics."),
        ),
        requires_approval=True,
    ),
    ToolContract(
        name="diagnose_residuals",
        input_fields=("residuals",),
        output_fields=("count", "mean", "median", "max_abs", "pattern", "diagnostics"),
        description="Summarize residuals and classify simple residual patterns deterministically.",
    ),
    ToolContract(
        name="set_refinement_flags",
        input_fields=("model_state", "flags", "provenance"),
        output_fields=("model_state", "changed_parameters"),
        description="Return a model state with selected refinement flags changed.",
        mutates_state=True,
        requires_approval=True,
    ),
    ToolContract(
        name="rollback",
        input_fields=("snapshots", "snapshot_id", "provenance"),
        output_fields=("model_state", "snapshot_id"),
        description="Restore a model state from a deterministic snapshot list.",
        mutates_state=True,
        requires_approval=True,
    ),
    ToolContract(
        name="freeze_parameter",
        input_fields=("model_state", "parameter", "provenance"),
        output_fields=("model_state", "changed_parameters"),
        description="Return a model state with one parameter frozen.",
        mutates_state=True,
        requires_approval=True,
    ),
    ToolContract(
        name="add_constraint",
        input_fields=("model_state", "constraint", "provenance"),
        output_fields=("model_state", "constraint_id"),
        description="Return a model state with one deterministic constraint added.",
        mutates_state=True,
        requires_approval=True,
    ),
    ToolContract(
        name="compare_models",
        input_fields=("models",),
        output_fields=("best_model_id", "comparisons"),
        description="Compare candidate model metrics without changing data.",
    ),
)


def create_refinement_tool_registry(*, approved_tools: Sequence[str] = ()) -> ToolRegistry:
    """Create a registry with Batch E deterministic refinement tool wrappers.

    Args:
        approved_tools: Tool names with human approval for this registry.

    Returns:
        A configured ``ToolRegistry``.
    """

    approved = frozenset(approved_tools)
    registry = ToolRegistry()
    registry.register(TOOL_CONTRACTS[0], lambda payload: run_refinement_tool(payload, approved="run_refinement" in approved))
    registry.register(TOOL_CONTRACTS[1], diagnose_residuals_tool)
    registry.register(
        TOOL_CONTRACTS[2],
        lambda payload: set_refinement_flags_tool(payload, approved="set_refinement_flags" in approved),
    )
    registry.register(TOOL_CONTRACTS[3], lambda payload: rollback_tool(payload, approved="rollback" in approved))
    registry.register(TOOL_CONTRACTS[4], lambda payload: freeze_parameter_tool(payload, approved="freeze_parameter" in approved))
    registry.register(TOOL_CONTRACTS[5], lambda payload: add_constraint_tool(payload, approved="add_constraint" in approved))
    registry.register(TOOL_CONTRACTS[6], compare_models_tool)
    return registry


def run_refinement_tool(payload: Mapping[str, Any], *, approved: bool = False) -> Mapping[str, Any]:
    """Wrap a deterministic backend refinement result.

    Args:
        payload: Tool payload with ``project_id``, ``request``, and
            ``backend_result``. The wrapper does not compute refinement results.
        approved: Whether human approval has been granted for this run.

    Returns:
        Run payload with stable run ID and backend-provided state/metrics.

    Raises:
        PermissionError: If safety policy blocks the call.
        TypeError: If structured fields have invalid types.
        ValueError: If backend results are incomplete.
    """

    _assert_safe(TOOL_CONTRACTS[0], payload, approved)
    project_id = _non_empty_string(payload, "project_id")
    request = _mapping(payload, "request")
    backend_result = _mapping(payload, "backend_result")
    model_state = _mapping(backend_result, "model_state")
    metrics = _mapping(backend_result, "metrics")
    status = str(backend_result.get("status", "completed"))
    if not status:
        raise ValueError("backend_result.status must be non-empty when provided")
    diagnostics = tuple(backend_result.get("diagnostics", ()))
    run_id = _stable_id("run", project_id, _stable_repr(request), _stable_repr(metrics))
    return MappingProxyType(
        {
            "run_id": run_id,
            "status": status,
            "model_state": MappingProxyType(dict(model_state)),
            "metrics": MappingProxyType(dict(metrics)),
            "diagnostics": diagnostics,
        }
    )


def diagnose_residuals_tool(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Tool wrapper for deterministic residual diagnostics."""

    residuals = _sequence(payload, "residuals")
    unit = str(payload.get("unit", "count"))
    return diagnose_residuals(tuple(float(value) for value in residuals), unit=unit)


def set_refinement_flags_tool(payload: Mapping[str, Any], *, approved: bool = False) -> Mapping[str, Any]:
    """Return a model state with selected parameter refinement flags changed."""

    _assert_safe(TOOL_CONTRACTS[2], payload, approved)
    model_state = _copy_model_state(_mapping(payload, "model_state"))
    flags = _mapping(payload, "flags")
    parameters = _parameters(model_state)
    changed: list[str] = []
    for name in sorted(flags):
        if name not in parameters:
            raise ValueError(f"Unknown parameter `{name}`")
        flag = flags[name]
        if not isinstance(flag, bool):
            raise TypeError(f"flags.`{name}` must be a bool")
        parameter = _parameter_mapping(parameters[name], name)
        if parameter.get("refine") != flag:
            parameter["refine"] = flag
            parameters[name] = parameter
            changed.append(name)
    model_state["parameters"] = parameters
    return MappingProxyType({"model_state": MappingProxyType(model_state), "changed_parameters": tuple(changed)})


def rollback_tool(payload: Mapping[str, Any], *, approved: bool = False) -> Mapping[str, Any]:
    """Restore a model state from an explicit snapshot list."""

    _assert_safe(TOOL_CONTRACTS[3], payload, approved)
    snapshots = _sequence(payload, "snapshots")
    target_id = _non_empty_string(payload, "snapshot_id")
    for raw_snapshot in snapshots:
        if not isinstance(raw_snapshot, MappingABC):
            raise TypeError("snapshots entries must be mappings")
        snapshot = dict(raw_snapshot)
        if snapshot.get("snapshot_id") == target_id:
            return MappingProxyType(
                {
                    "model_state": MappingProxyType(_copy_model_state(_mapping(snapshot, "model_state"))),
                    "snapshot_id": target_id,
                }
            )
    raise ValueError(f"snapshot_id `{target_id}` was not found")


def freeze_parameter_tool(payload: Mapping[str, Any], *, approved: bool = False) -> Mapping[str, Any]:
    """Return a model state with one parameter frozen."""

    _assert_safe(TOOL_CONTRACTS[4], payload, approved)
    parameter = _non_empty_string(payload, "parameter")
    nested_payload = {
        "model_state": _mapping(payload, "model_state"),
        "flags": {parameter: False},
        "provenance": _mapping(payload, "provenance"),
    }
    return set_refinement_flags_tool(nested_payload, approved=True)


def add_constraint_tool(payload: Mapping[str, Any], *, approved: bool = False) -> Mapping[str, Any]:
    """Return a model state with one validated constraint appended."""

    _assert_safe(TOOL_CONTRACTS[5], payload, approved)
    model_state = _copy_model_state(_mapping(payload, "model_state"))
    constraint = dict(_mapping(payload, "constraint"))
    constraint_id = _non_empty_mapping_string(constraint, "constraint_id")
    expression = _non_empty_mapping_string(constraint, "expression")
    parameters = tuple(_sequence(constraint, "parameters"))
    if not parameters:
        raise ValueError("constraint.parameters must be non-empty")
    for parameter in parameters:
        if not isinstance(parameter, str) or not parameter:
            raise ValueError("constraint.parameters entries must be non-empty strings")
    constraints = list(model_state.get("constraints", ()))
    if any(isinstance(item, MappingABC) and item.get("constraint_id") == constraint_id for item in constraints):
        raise ValueError(f"constraint_id `{constraint_id}` already exists")
    constraints.append(
        MappingProxyType(
            {
                "constraint_id": constraint_id,
                "expression": expression,
                "parameters": parameters,
            }
        )
    )
    model_state["constraints"] = tuple(constraints)
    return MappingProxyType({"model_state": MappingProxyType(model_state), "constraint_id": constraint_id})


def compare_models_tool(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Compare model metrics and select the lowest Rwp/AIC candidate."""

    models = _sequence(payload, "models")
    if not models:
        raise ValueError("models must be non-empty")
    rows: list[dict[str, Any]] = []
    for raw_model in models:
        if not isinstance(raw_model, MappingABC):
            raise TypeError("models entries must be mappings")
        model = dict(raw_model)
        model_id = _non_empty_mapping_string(model, "model_id")
        metrics = _mapping(model, "metrics")
        rwp = _finite_metric(metrics, "rwp")
        aic = _finite_metric(metrics, "aic", default=0.0)
        rows.append({"model_id": model_id, "rwp": rwp, "aic": aic})
    rows.sort(key=lambda row: (row["rwp"], row["aic"], row["model_id"]))
    best = rows[0]
    comparisons = tuple(
        MappingProxyType(
            {
                "model_id": row["model_id"],
                "rank": index + 1,
                "rwp": row["rwp"],
                "aic": row["aic"],
                "delta_rwp": row["rwp"] - best["rwp"],
                "delta_aic": row["aic"] - best["aic"],
            }
        )
        for index, row in enumerate(rows)
    )
    return MappingProxyType({"best_model_id": best["model_id"], "comparisons": comparisons})


def _assert_safe(contract: ToolContract, payload: Mapping[str, Any], approved: bool) -> None:
    findings = evaluate_tool_call_safety(contract, payload, approved=approved)
    if not safety_allows(findings):
        messages = "; ".join(str(finding["message"]) for finding in findings if finding.get("severity") == "error")
        raise PermissionError(messages)


def _copy_model_state(model_state: Mapping[str, Any]) -> dict[str, Any]:
    copied = deepcopy(dict(model_state))
    if "parameters" not in copied:
        raise ValueError("model_state must include parameters")
    if not isinstance(copied["parameters"], MappingABC):
        raise TypeError("model_state.parameters must be a mapping")
    return copied


def _parameters(model_state: dict[str, Any]) -> dict[str, Any]:
    return dict(model_state["parameters"])


def _parameter_mapping(raw: Any, name: str) -> dict[str, Any]:
    if not isinstance(raw, MappingABC):
        raise TypeError(f"model_state.parameters.`{name}` must be a mapping")
    return dict(raw)


def _mapping(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    if field not in payload:
        raise ValueError(f"{field} is required")
    value = payload[field]
    if not isinstance(value, MappingABC):
        raise TypeError(f"{field} must be a mapping")
    return value


def _sequence(payload: Mapping[str, Any], field: str) -> Sequence[Any]:
    if field not in payload:
        raise ValueError(f"{field} is required")
    value = payload[field]
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, SequenceABC):
        raise TypeError(f"{field} must be a sequence")
    return value


def _non_empty_string(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _non_empty_mapping_string(payload: Mapping[str, Any], field: str) -> str:
    return _non_empty_string(payload, field)


def _finite_metric(metrics: Mapping[str, Any], field: str, *, default: float | None = None) -> float:
    if field not in metrics:
        if default is None:
            raise ValueError(f"metrics.{field} is required")
        return default
    value = float(metrics[field])
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"metrics.{field} must be finite")
    return value


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _stable_repr(value: Any) -> str:
    if isinstance(value, MappingABC):
        return "{" + ",".join(f"{key}:{_stable_repr(value[key])}" for key in sorted(value)) + "}"
    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes, bytearray)):
        return "[" + ",".join(_stable_repr(item) for item in value) + "]"
    return repr(value)
