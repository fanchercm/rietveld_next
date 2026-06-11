"""Generic objective interfaces and scalar objective helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import math
from typing import Any


ObjectiveFunction = Callable[[Sequence[float]], "ObjectiveEvaluation"]


@dataclass(frozen=True)
class ObjectiveEvaluation:
    """Structured result from evaluating an optimization objective.

    Args:
        parameters: Parameter vector used for the evaluation.
        objective_value: Scalar objective value. Lower is better.
        residuals: Optional residual vector in deterministic order.
        status: ``"ok"`` for usable evaluations or ``"invalid"`` for
            structured invalid-model handling.
        message: Human-readable diagnostic message.
        diagnostics: JSON-compatible diagnostic metadata.

    Raises:
        ValueError: If numeric values are non-finite, status is unknown, or
            diagnostics are not JSON-compatible.
    """

    parameters: tuple[float, ...]
    objective_value: float
    residuals: tuple[float, ...] = ()
    status: str = "ok"
    message: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate objective evaluation fields."""
        if self.status not in {"ok", "invalid"}:
            raise ValueError(f"status must be 'ok' or 'invalid', got {self.status!r}.")
        _finite_sequence(self.parameters, "parameters")
        _finite_sequence(self.residuals, "residuals")
        _finite_float(self.objective_value, "objective_value")
        if self.status == "ok" and self.objective_value < 0.0:
            raise ValueError(f"objective_value must be non-negative for ok evaluations, got {self.objective_value!r}.")
        _json_compatible(self.diagnostics, "diagnostics")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "parameters": list(self.parameters),
            "objective_value": self.objective_value,
            "residuals": list(self.residuals),
            "status": self.status,
            "message": self.message,
            "diagnostics": dict(sorted(self.diagnostics.items())),
        }


class ObjectiveRegistry:
    """Name-to-objective registry with explicit duplicate handling."""

    def __init__(self) -> None:
        """Create an empty registry."""
        self._objectives: dict[str, ObjectiveFunction] = {}

    def register(self, name: str, objective: ObjectiveFunction) -> None:
        """Register an objective function.

        Args:
            name: Stable objective name.
            objective: Callable accepting a parameter vector.

        Raises:
            ValueError: If the name is empty, duplicated, or objective is not
                callable.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("objective name must be a non-empty string.")
        if not callable(objective):
            raise ValueError("objective must be callable.")
        if name in self._objectives:
            raise ValueError(f"Objective {name!r} is already registered.")
        self._objectives[name] = objective

    def get(self, name: str) -> ObjectiveFunction:
        """Return a registered objective by name.

        Raises:
            KeyError: If ``name`` is not registered.
        """
        try:
            return self._objectives[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._objectives))
            raise KeyError(f"Unknown objective {name!r}. Available objectives: {available}.") from exc

    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order."""
        return tuple(sorted(self._objectives))


def least_squares_evaluation(
    parameters: Sequence[float],
    residuals: Sequence[float],
    *,
    loss: str = "linear",
    loss_scale: float = 1.0,
) -> ObjectiveEvaluation:
    """Create a scalar least-squares objective evaluation.

    Args:
        parameters: Parameter vector used for the evaluation.
        residuals: Residual vector.
        loss: Robust loss name: ``"linear"``, ``"huber"``, or ``"soft_l1"``.
        loss_scale: Positive robust-loss scale.

    Returns:
        Objective evaluation with ``0.5 * sum(r_i^2)`` for the linear loss.

    Raises:
        ValueError: If inputs are invalid or the loss name is unknown.
    """
    parameter_values = tuple(_finite_sequence(parameters, "parameters"))
    residual_values = tuple(_finite_sequence(residuals, "residuals"))
    scale = _positive_float(loss_scale, "loss_scale")
    objective_value = sum(_loss_value(residual, loss=loss, scale=scale) for residual in residual_values)
    return ObjectiveEvaluation(
        parameters=parameter_values,
        objective_value=objective_value,
        residuals=residual_values,
        diagnostics={"loss": loss, "loss_scale": scale},
    )


def invalid_model_evaluation(parameters: Sequence[float], message: str, **diagnostics: Any) -> ObjectiveEvaluation:
    """Create a structured invalid-model objective evaluation.

    Args:
        parameters: Parameter vector that produced an invalid model.
        message: Human-readable diagnostic.
        **diagnostics: JSON-compatible metadata.

    Returns:
        Invalid objective evaluation with a large finite penalty value.
    """
    if not isinstance(message, str) or not message:
        raise ValueError("message must be a non-empty string.")
    return ObjectiveEvaluation(
        parameters=tuple(_finite_sequence(parameters, "parameters")),
        objective_value=1.0e300,
        residuals=(),
        status="invalid",
        message=message,
        diagnostics=diagnostics,
    )


def poisson_deviance_evaluation(
    parameters: Sequence[float],
    observed: Sequence[float],
    expected: Sequence[float],
) -> ObjectiveEvaluation:
    """Evaluate the Poisson deviance objective for count data.

    The implemented deviance is:

    ```text
    D = 2 * sum(expected_i - observed_i + observed_i * log(observed_i / expected_i))
    ```

    with the conventional zero-count contribution ``2 * expected_i``.

    Args:
        parameters: Parameter vector used for the evaluation.
        observed: Observed non-negative counts.
        expected: Positive expected counts.

    Returns:
        Objective evaluation with residual-like signed square-root deviance
        components.

    Raises:
        ValueError: If lengths differ, observed counts are negative, or expected
            counts are not strictly positive.
    """
    parameter_values = tuple(_finite_sequence(parameters, "parameters"))
    observed_values = _finite_sequence(observed, "observed")
    expected_values = _finite_sequence(expected, "expected")
    if len(observed_values) != len(expected_values):
        raise ValueError(
            "observed and expected must have the same length, "
            f"got {len(observed_values)} and {len(expected_values)}."
        )

    objective_value = 0.0
    residuals: list[float] = []
    for index, (observed_value, expected_value) in enumerate(zip(observed_values, expected_values, strict=True)):
        if observed_value < 0.0:
            raise ValueError(f"observed[{index}] must be non-negative, got {observed_value!r}.")
        if expected_value <= 0.0:
            raise ValueError(f"expected[{index}] must be positive, got {expected_value!r}.")
        contribution = 2.0 * expected_value if observed_value == 0.0 else 2.0 * (
            expected_value - observed_value + observed_value * math.log(observed_value / expected_value)
        )
        contribution = max(0.0, contribution)
        objective_value += contribution
        sign = -1.0 if observed_value < expected_value else 1.0
        residuals.append(sign * math.sqrt(contribution))

    return ObjectiveEvaluation(
        parameters=parameter_values,
        objective_value=objective_value,
        residuals=tuple(residuals),
        diagnostics={"objective": "poisson_deviance"},
    )


def _loss_value(residual: float, *, loss: str, scale: float) -> float:
    scaled = residual / scale
    if loss == "linear":
        return 0.5 * residual**2
    if loss == "huber":
        absolute = abs(scaled)
        if absolute <= 1.0:
            return 0.5 * residual**2
        return scale**2 * (absolute - 0.5)
    if loss == "soft_l1":
        return scale**2 * (math.sqrt(1.0 + scaled**2) - 1.0)
    raise ValueError(f"Unknown loss {loss!r}.")


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _json_compatible(value: Any, name: str) -> None:
    if value is None or isinstance(value, str | bool):
        return
    if isinstance(value, int | float) and not isinstance(value, bool):
        _finite_float(value, name)
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _json_compatible(item, f"{name}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{name} keys must be strings, got {key!r}.")
            _json_compatible(item, f"{name}.{key}")
        return
    raise ValueError(f"{name} must be JSON-compatible, got {value!r}.")
