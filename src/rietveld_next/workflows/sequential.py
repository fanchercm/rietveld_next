"""Sequential refinement workflow primitives.

The APIs in this module orchestrate deterministic refinement handlers. They do
not implement scientific kernels or storage backends; callers provide the
refinement callable and persist returned dictionaries if desired.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any

from rietveld_next.workflows.replay import WorkflowAction


RefinementHandler = Callable[["SequentialRunRequest"], Mapping[str, Any]]


@dataclass(frozen=True)
class SequentialPointSpec:
    """Dataset point in a sequential study.

    Args:
        point_id: Stable point identifier unique within the study.
        dataset_id: Dataset identifier consumed by the refinement handler.
        variables: External variables such as temperature or pressure.
    """

    point_id: str
    dataset_id: str
    variables: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate point identity and variable values."""

        _non_empty_string(self.point_id, "point_id")
        _non_empty_string(self.dataset_id, "dataset_id")
        converted = {str(name): _finite_float(value, f"variables.{name}") for name, value in self.variables.items()}
        object.__setattr__(self, "variables", MappingProxyType(converted))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping.

        Example:
            >>> SequentialPointSpec("p1", "scan-1", {"temperature_k": 300.0}).to_dict()["point_id"]
            'p1'
        """

        return {
            "point_id": self.point_id,
            "dataset_id": self.dataset_id,
            "variables": dict(sorted(self.variables.items())),
        }


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic retry policy for failed sequential points.

    Args:
        max_attempts: Total attempts per point, including the first attempt.
        retry_statuses: Handler status values that should be retried.
    """

    max_attempts: int = 1
    retry_statuses: tuple[str, ...] = ("error",)

    def __post_init__(self) -> None:
        """Validate retry bounds and status labels."""

        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            raise ValueError("RetryPolicy.max_attempts must be a positive integer")
        if not self.retry_statuses:
            raise ValueError("RetryPolicy.retry_statuses must not be empty")
        for status in self.retry_statuses:
            _non_empty_string(status, "retry_statuses")

    def should_retry(self, status: str, attempt: int) -> bool:
        """Return whether another attempt should be made."""

        return status in self.retry_statuses and attempt < self.max_attempts

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {"max_attempts": self.max_attempts, "retry_statuses": list(self.retry_statuses)}


@dataclass(frozen=True)
class PreviousPointInitialization:
    """Initial parameter policy for sequential execution.

    Args:
        mode: ``"static"`` keeps the recipe initial parameters for every point;
            ``"previous_successful"`` seeds each point from the previous
            successful point's final parameters.
    """

    mode: str = "previous_successful"

    def __post_init__(self) -> None:
        """Validate initialization mode."""

        if self.mode not in {"static", "previous_successful"}:
            raise ValueError("PreviousPointInitialization.mode must be 'static' or 'previous_successful'")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {"mode": self.mode}


@dataclass(frozen=True)
class SequentialRunRequest:
    """Single deterministic refinement request passed to a handler.

    Args:
        study_id: Stable study identifier.
        point: Sequential point metadata.
        attempt: One-based attempt number.
        initial_parameters: Parameter values used to initialize refinement.
        provenance: Deterministic workflow metadata.
    """

    study_id: str
    point: SequentialPointSpec
    attempt: int
    initial_parameters: Mapping[str, float]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Validate request payload."""

        _non_empty_string(self.study_id, "study_id")
        if self.attempt < 1:
            raise ValueError("SequentialRunRequest.attempt must be positive")
        _validate_parameter_values(self.initial_parameters, "initial_parameters")
        object.__setattr__(self, "initial_parameters", MappingProxyType(dict(sorted(self.initial_parameters.items()))))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "study_id": self.study_id,
            "point": self.point.to_dict(),
            "attempt": self.attempt,
            "initial_parameters": dict(self.initial_parameters),
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class ParameterEstimate:
    """Refined parameter value recorded in a result table.

    Args:
        name: Stable parameter path or identifier.
        value: Refined parameter value.
        unit: Display or scientific unit string.
        uncertainty: Optional one-sigma uncertainty in the same unit.
        provenance: Deterministic source metadata.
    """

    name: str
    value: float
    unit: str
    uncertainty: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate parameter estimate fields."""

        _non_empty_string(self.name, "name")
        _non_empty_string(self.unit, "unit")
        object.__setattr__(self, "value", _finite_float(self.value, "value"))
        if self.uncertainty is not None:
            uncertainty = _finite_float(self.uncertainty, "uncertainty")
            if uncertainty < 0.0:
                raise ValueError("ParameterEstimate.uncertainty must be non-negative")
            object.__setattr__(self, "uncertainty", uncertainty)
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "uncertainty": self.uncertainty,
            "provenance": dict(sorted(self.provenance.items())),
        }


@dataclass(frozen=True)
class SequentialPointResult:
    """Result for one sequential point."""

    index: int
    point_id: str
    dataset_id: str
    variables: Mapping[str, float]
    status: str
    attempts: int
    parameters: Mapping[str, ParameterEstimate] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    residuals: tuple[float, ...] = ()
    error: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate point result fields."""

        if self.index < 0:
            raise ValueError("SequentialPointResult.index must be non-negative")
        _non_empty_string(self.point_id, "point_id")
        _non_empty_string(self.dataset_id, "dataset_id")
        if self.status not in {"ok", "error"}:
            raise ValueError("SequentialPointResult.status must be 'ok' or 'error'")
        if self.attempts < 1:
            raise ValueError("SequentialPointResult.attempts must be positive")
        variables = {str(name): _finite_float(value, f"variables.{name}") for name, value in self.variables.items()}
        metrics = {str(name): _finite_float(value, f"metrics.{name}") for name, value in self.metrics.items()}
        residuals = tuple(_finite_float(value, "residuals") for value in self.residuals)
        object.__setattr__(self, "variables", MappingProxyType(dict(sorted(variables.items()))))
        object.__setattr__(self, "parameters", MappingProxyType(dict(sorted(self.parameters.items()))))
        object.__setattr__(self, "metrics", MappingProxyType(dict(sorted(metrics.items()))))
        object.__setattr__(self, "residuals", residuals)
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))

    @property
    def final_parameter_values(self) -> dict[str, float]:
        """Return final parameter values keyed by parameter name."""

        return {name: estimate.value for name, estimate in self.parameters.items()}

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "index": self.index,
            "point_id": self.point_id,
            "dataset_id": self.dataset_id,
            "variables": dict(self.variables),
            "status": self.status,
            "attempts": self.attempts,
            "parameters": {name: estimate.to_dict() for name, estimate in self.parameters.items()},
            "metrics": dict(self.metrics),
            "residuals": list(self.residuals),
            "error": self.error,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class SequentialResultTable:
    """Tabular sequential-study results with deterministic exports."""

    study_id: str
    rows: tuple[SequentialPointResult, ...]
    actions: tuple[WorkflowAction, ...] = ()

    def __post_init__(self) -> None:
        """Validate result table identity and row ordering."""

        _non_empty_string(self.study_id, "study_id")
        seen: set[str] = set()
        for expected_index, row in enumerate(self.rows):
            if row.index != expected_index:
                raise ValueError("SequentialResultTable rows must use contiguous zero-based indices")
            if row.point_id in seen:
                raise ValueError(f"Duplicate sequential point_id '{row.point_id}'")
            seen.add(row.point_id)

    @property
    def succeeded(self) -> bool:
        """Whether every point completed successfully."""

        return all(row.status == "ok" for row in self.rows)

    def parameter_evolution(self, parameter_name: str) -> tuple[dict[str, Any], ...]:
        """Export parameter values across successful points.

        Args:
            parameter_name: Parameter path to export.

        Returns:
            Rows containing point metadata, external variables, units,
            uncertainty, and provenance.
        """

        _non_empty_string(parameter_name, "parameter_name")
        evolution: list[dict[str, Any]] = []
        for row in self.rows:
            estimate = row.parameters.get(parameter_name)
            if estimate is None:
                continue
            evolution.append(
                {
                    "index": row.index,
                    "point_id": row.point_id,
                    "dataset_id": row.dataset_id,
                    "variables": dict(row.variables),
                    "parameter": parameter_name,
                    "value": estimate.value,
                    "unit": estimate.unit,
                    "uncertainty": estimate.uncertainty,
                    "provenance": dict(estimate.provenance),
                }
            )
        return tuple(evolution)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "study_id": self.study_id,
            "rows": [row.to_dict() for row in self.rows],
            "actions": [
                {
                    "sequence": action.sequence,
                    "step_id": action.step_id,
                    "tool": action.tool,
                    "inputs": dict(action.inputs),
                    "status": action.status,
                    "output": dict(action.output) if action.output is not None else None,
                    "error": action.error,
                }
                for action in self.actions
            ],
        }


class SequentialRunner:
    """Run a deterministic sequential refinement study.

    Example:
        >>> def refine(request):
        ...     return {"status": "ok", "parameters": {"a": {"value": request.attempt, "unit": "A"}}}
        >>> runner = SequentialRunner("study", [SequentialPointSpec("p1", "d1")], {"a": 0.0}, refine)
        >>> runner.run().rows[0].parameters["a"].value
        1.0
    """

    def __init__(
        self,
        study_id: str,
        points: Sequence[SequentialPointSpec],
        initial_parameters: Mapping[str, float],
        refinement_handler: RefinementHandler,
        *,
        initialization: PreviousPointInitialization | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Create a sequential runner.

        Args:
            study_id: Stable study identifier.
            points: Ordered study points.
            initial_parameters: Recipe-level starting parameter values.
            refinement_handler: Deterministic callable for one point.
            initialization: Previous-point initialization policy.
            retry_policy: Failed-point retry policy.

        Raises:
            ValueError: If identifiers, points, parameters, or handler are invalid.
        """

        _non_empty_string(study_id, "study_id")
        if not callable(refinement_handler):
            raise ValueError("refinement_handler must be callable")
        point_tuple = tuple(points)
        _validate_unique_point_ids(point_tuple)
        _validate_parameter_values(initial_parameters, "initial_parameters")
        self._study_id = study_id
        self._points = point_tuple
        self._initial_parameters = dict(sorted(initial_parameters.items()))
        self._handler = refinement_handler
        self._initialization = initialization or PreviousPointInitialization()
        self._retry_policy = retry_policy or RetryPolicy()

    def run(self) -> SequentialResultTable:
        """Run points in order and return a deterministic result table."""

        rows: list[SequentialPointResult] = []
        actions: list[WorkflowAction] = []
        current_initial = dict(self._initial_parameters)
        last_successful: dict[str, float] | None = None

        for index, point in enumerate(self._points):
            if self._initialization.mode == "previous_successful" and last_successful is not None:
                current_initial = dict(last_successful)
            row, point_actions = self._run_point(index, point, current_initial, len(actions))
            rows.append(row)
            actions.extend(point_actions)
            if row.status == "ok":
                last_successful = row.final_parameter_values

        return SequentialResultTable(self._study_id, tuple(rows), tuple(actions))

    def _run_point(
        self,
        index: int,
        point: SequentialPointSpec,
        initial_parameters: Mapping[str, float],
        action_offset: int,
    ) -> tuple[SequentialPointResult, tuple[WorkflowAction, ...]]:
        actions: list[WorkflowAction] = []
        final_output: Mapping[str, Any] | None = None
        final_error: str | None = None
        final_status = "error"
        attempt = 1

        while True:
            request = SequentialRunRequest(
                study_id=self._study_id,
                point=point,
                attempt=attempt,
                initial_parameters=initial_parameters,
                provenance={
                    "workflow": "sequential",
                    "initialization": self._initialization.to_dict(),
                    "retry_policy": self._retry_policy.to_dict(),
                },
            )
            try:
                output = self._handler(request)
            except Exception as exc:  # pragma: no cover - behavior tested through result
                output = None
                final_error = f"{type(exc).__name__}: {exc}"
                final_status = "error"
            else:
                if not isinstance(output, Mapping):
                    final_error = "Sequential refinement handler output must be a mapping"
                    final_status = "error"
                else:
                    final_output = output
                    final_status = str(output.get("status", "ok"))
                    if final_status not in {"ok", "error"}:
                        final_error = f"Unsupported sequential handler status '{final_status}'"
                        final_status = "error"
                    else:
                        final_error = str(output.get("error")) if output.get("error") is not None else None

            actions.append(
                WorkflowAction(
                    sequence=action_offset + len(actions),
                    step_id=f"{point.point_id}:attempt-{attempt}",
                    tool="sequential.refine_point",
                    inputs=request.to_dict(),
                    status="ok" if final_status == "ok" else "error",
                    output=final_output if final_status == "ok" else None,
                    error=final_error,
                )
            )
            if final_status == "ok" or not self._retry_policy.should_retry(final_status, attempt):
                break
            attempt += 1

        return (
            _point_result_from_output(
                index=index,
                point=point,
                status=final_status,
                attempts=attempt,
                output=final_output,
                error=final_error,
            ),
            tuple(actions),
        )


def export_parameter_evolution(
    table: SequentialResultTable,
    parameter_names: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    """Export evolution rows for one or more parameters.

    Args:
        table: Sequential result table.
        parameter_names: Ordered parameter names to export.

    Returns:
        Deterministic JSON-compatible rows sorted by requested parameter order
        and sequential point order.
    """

    rows: list[dict[str, Any]] = []
    for parameter_name in parameter_names:
        rows.extend(table.parameter_evolution(parameter_name))
    return tuple(rows)


def build_dashboard_data(table: SequentialResultTable) -> dict[str, Any]:
    """Build framework-neutral data for a sequential dashboard."""

    status_counts: dict[str, int] = {}
    metric_names: set[str] = set()
    parameter_names: set[str] = set()
    for row in table.rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
        metric_names.update(row.metrics)
        parameter_names.update(row.parameters)

    return {
        "study_id": table.study_id,
        "point_count": len(table.rows),
        "status_counts": dict(sorted(status_counts.items())),
        "points": [
            {
                "index": row.index,
                "point_id": row.point_id,
                "dataset_id": row.dataset_id,
                "status": row.status,
                "variables": dict(row.variables),
                "attempts": row.attempts,
                "error": row.error,
            }
            for row in table.rows
        ],
        "metrics": {
            name: [
                {"index": row.index, "point_id": row.point_id, "value": row.metrics.get(name)}
                for row in table.rows
                if name in row.metrics
            ]
            for name in sorted(metric_names)
        },
        "parameters": {
            name: list(table.parameter_evolution(name))
            for name in sorted(parameter_names)
        },
    }


def build_residual_heatmap_data(table: SequentialResultTable) -> dict[str, Any]:
    """Build rectangular residual heatmap data without rendering."""

    rows_with_residuals = [row for row in table.rows if row.residuals]
    if not rows_with_residuals:
        return {"study_id": table.study_id, "point_ids": [], "x_indices": [], "values": []}
    width = len(rows_with_residuals[0].residuals)
    for row in rows_with_residuals:
        if len(row.residuals) != width:
            raise ValueError("Residual heatmap requires equal residual vector lengths")
    return {
        "study_id": table.study_id,
        "point_ids": [row.point_id for row in rows_with_residuals],
        "x_indices": list(range(width)),
        "values": [list(row.residuals) for row in rows_with_residuals],
    }


def _point_result_from_output(
    *,
    index: int,
    point: SequentialPointSpec,
    status: str,
    attempts: int,
    output: Mapping[str, Any] | None,
    error: str | None,
) -> SequentialPointResult:
    output = output or {}
    return SequentialPointResult(
        index=index,
        point_id=point.point_id,
        dataset_id=point.dataset_id,
        variables=point.variables,
        status=status,
        attempts=attempts,
        parameters=_parse_parameters(output.get("parameters", {})),
        metrics=_parse_numeric_mapping(output.get("metrics", {}), "metrics"),
        residuals=tuple(_finite_float(value, "residuals") for value in output.get("residuals", ())),
        error=error,
        provenance={
            "source": "sequential_runner",
            "handler_status": status,
            "attempts": attempts,
        },
    )


def _parse_parameters(value: Any) -> dict[str, ParameterEstimate]:
    if not isinstance(value, Mapping):
        raise TypeError("parameters must be a mapping")
    estimates: dict[str, ParameterEstimate] = {}
    for name, raw in value.items():
        parameter_name = str(name)
        if isinstance(raw, Mapping):
            estimates[parameter_name] = ParameterEstimate(
                name=parameter_name,
                value=raw["value"],
                unit=str(raw.get("unit", "dimensionless")),
                uncertainty=raw.get("uncertainty"),
                provenance=raw.get("provenance", {}),
            )
        else:
            estimates[parameter_name] = ParameterEstimate(
                name=parameter_name,
                value=raw,
                unit="dimensionless",
                provenance={"assumption": "unit omitted by handler"},
            )
    return estimates


def _parse_numeric_mapping(value: Any, name: str) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return {str(key): _finite_float(raw, f"{name}.{key}") for key, raw in value.items()}


def _validate_parameter_values(values: Mapping[str, float], name: str) -> None:
    if not isinstance(values, Mapping):
        raise TypeError(f"{name} must be a mapping")
    for parameter, value in values.items():
        _non_empty_string(str(parameter), f"{name}.key")
        _finite_float(value, f"{name}.{parameter}")


def _validate_unique_point_ids(points: Sequence[SequentialPointSpec]) -> None:
    seen: set[str] = set()
    for point in points:
        if not isinstance(point, SequentialPointSpec):
            raise TypeError("points must contain SequentialPointSpec values")
        if point.point_id in seen:
            raise ValueError(f"Duplicate sequential point_id '{point.point_id}'")
        seen.add(point.point_id)


def _non_empty_string(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite number")
    return converted
