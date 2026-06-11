"""Dependency-free local optimizer adapter for small deterministic problems."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import math
from typing import Any

from rietveld_next.optimization.objectives import ObjectiveEvaluation, ObjectiveFunction
from rietveld_next.optimization.transforms import BoundTransform


@dataclass(frozen=True)
class OptimizerSnapshot:
    """Rollback snapshot captured during local optimization.

    Args:
        iteration: Iteration number.
        parameters: Best parameters at the snapshot.
        objective_value: Best objective value at the snapshot.
    """

    iteration: int
    parameters: tuple[float, ...]
    objective_value: float


@dataclass(frozen=True)
class LocalOptimizerOptions:
    """Options for the coordinate-search local optimizer.

    Args:
        max_iterations: Maximum outer iterations.
        initial_step: Initial coordinate step in physical parameter units.
        tolerance: Stop when the trial step falls below this value.
    """

    max_iterations: int = 100
    initial_step: float = 1.0
    tolerance: float = 1.0e-6

    def __post_init__(self) -> None:
        """Validate optimizer options."""
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int) or self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be a positive integer, got {self.max_iterations!r}.")
        _positive_float(self.initial_step, "initial_step")
        _positive_float(self.tolerance, "tolerance")


@dataclass(frozen=True)
class ConvergenceReport:
    """Structured convergence result returned by local optimizers.

    Args:
        status: Machine-readable status.
        message: Human-readable status message.
        converged: Whether convergence criteria were met.
        iterations: Number of outer iterations completed.
        evaluations: Number of objective evaluations performed.
        objective_value: Final best objective value.
        parameters: Final best parameter vector.
        snapshots: Rollback snapshots in deterministic order.
        diagnostics: JSON-compatible diagnostic metadata.
    """

    status: str
    message: str
    converged: bool
    iterations: int
    evaluations: int
    objective_value: float
    parameters: tuple[float, ...]
    snapshots: tuple[OptimizerSnapshot, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "status": self.status,
            "message": self.message,
            "converged": self.converged,
            "iterations": self.iterations,
            "evaluations": self.evaluations,
            "objective_value": self.objective_value,
            "parameters": list(self.parameters),
            "snapshots": [
                {
                    "iteration": snapshot.iteration,
                    "parameters": list(snapshot.parameters),
                    "objective_value": snapshot.objective_value,
                }
                for snapshot in self.snapshots
            ],
            "diagnostics": dict(sorted(self.diagnostics.items())),
        }


def coordinate_search_minimize(
    objective: ObjectiveFunction,
    initial_parameters: Sequence[float],
    *,
    bounds: Sequence[BoundTransform] | None = None,
    options: LocalOptimizerOptions | None = None,
) -> ConvergenceReport:
    """Minimize a generic objective using deterministic coordinate search.

    This optimizer is intended for small synthetic tests, smoke benchmarks, and
    dependency-free infrastructure validation. It is not a replacement for
    production least-squares, trust-region, or Levenberg-Marquardt adapters.

    Args:
        objective: Callable objective returning :class:`ObjectiveEvaluation`.
        initial_parameters: Initial physical parameter vector.
        bounds: Optional per-parameter bounds.
        options: Optimizer options.

    Returns:
        Structured convergence report with rollback snapshots.

    Raises:
        ValueError: If inputs are malformed or initial parameters violate
            supplied bounds.
    """
    if not callable(objective):
        raise ValueError("objective must be callable.")
    settings = options or LocalOptimizerOptions()
    parameters = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
    bound_list = _bounds_for_parameters(parameters, bounds)
    for value, bound in zip(parameters, bound_list, strict=True):
        bound.validate_value(value)

    current, evaluations = _safe_evaluate(objective, parameters)
    if current.status != "ok":
        return _report(
            status="invalid_initial_model",
            message=current.message or "Initial objective evaluation was invalid.",
            converged=False,
            iterations=0,
            evaluations=evaluations,
            objective_value=current.objective_value,
            parameters=parameters,
            snapshots=(),
            diagnostics=current.diagnostics,
        )

    best_parameters = parameters
    best_value = current.objective_value
    step = settings.initial_step
    snapshots = [OptimizerSnapshot(iteration=0, parameters=best_parameters, objective_value=best_value)]

    for iteration in range(1, settings.max_iterations + 1):
        improved = False
        for index in range(len(best_parameters)):
            for direction in (-1.0, 1.0):
                candidate = list(best_parameters)
                candidate[index] += direction * step
                if not _inside_bounds(candidate, bound_list):
                    continue
                evaluation, count = _safe_evaluate(objective, tuple(candidate))
                evaluations += count
                if evaluation.status != "ok":
                    continue
                if evaluation.objective_value < best_value:
                    best_parameters = tuple(candidate)
                    best_value = evaluation.objective_value
                    improved = True

        snapshots.append(OptimizerSnapshot(iteration=iteration, parameters=best_parameters, objective_value=best_value))
        if not improved:
            step *= 0.5
        if step <= settings.tolerance:
            return _report(
                status="converged",
                message="Step size tolerance reached.",
                converged=True,
                iterations=iteration,
                evaluations=evaluations,
                objective_value=best_value,
                parameters=best_parameters,
                snapshots=tuple(snapshots),
                diagnostics={"final_step": step},
            )

    return _report(
        status="max_iterations",
        message="Maximum iterations reached before step-size convergence.",
        converged=False,
        iterations=settings.max_iterations,
        evaluations=evaluations,
        objective_value=best_value,
        parameters=best_parameters,
        snapshots=tuple(snapshots),
        diagnostics={"final_step": step},
    )


def _safe_evaluate(objective: ObjectiveFunction, parameters: tuple[float, ...]) -> tuple[ObjectiveEvaluation, int]:
    try:
        evaluation = objective(parameters)
    except ValueError as exc:
        return (
            ObjectiveEvaluation(
                parameters=parameters,
                objective_value=1.0e300,
                status="invalid",
                message=str(exc),
                diagnostics={"exception": exc.__class__.__name__},
            ),
            1,
        )
    if not isinstance(evaluation, ObjectiveEvaluation):
        raise ValueError("objective must return an ObjectiveEvaluation.")
    return evaluation, 1


def _bounds_for_parameters(
    parameters: tuple[float, ...],
    bounds: Sequence[BoundTransform] | None,
) -> list[BoundTransform]:
    if bounds is None:
        return [BoundTransform() for _ in parameters]
    if isinstance(bounds, str) or not isinstance(bounds, Sequence):
        raise ValueError("bounds must be a sequence of BoundTransform values.")
    bound_list = list(bounds)
    if len(bound_list) != len(parameters):
        raise ValueError(f"bounds length must match parameters length, got {len(bound_list)} and {len(parameters)}.")
    for index, bound in enumerate(bound_list):
        if not isinstance(bound, BoundTransform):
            raise ValueError(f"bounds[{index}] must be a BoundTransform.")
    return bound_list


def _inside_bounds(values: Sequence[float], bounds: Sequence[BoundTransform]) -> bool:
    for value, bound in zip(values, bounds, strict=True):
        try:
            bound.validate_value(value)
        except ValueError:
            return False
    return True


def _report(
    *,
    status: str,
    message: str,
    converged: bool,
    iterations: int,
    evaluations: int,
    objective_value: float,
    parameters: tuple[float, ...],
    snapshots: tuple[OptimizerSnapshot, ...],
    diagnostics: dict[str, Any],
) -> ConvergenceReport:
    return ConvergenceReport(
        status=status,
        message=message,
        converged=converged,
        iterations=iterations,
        evaluations=evaluations,
        objective_value=objective_value,
        parameters=parameters,
        snapshots=snapshots,
        diagnostics=diagnostics,
    )


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
