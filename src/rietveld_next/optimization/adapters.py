"""Local optimizer adapter contracts for optional SciPy and Rust backends."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib import import_module
import math
from typing import Any, Protocol

from rietveld_next.optimization.local import ConvergenceReport, OptimizerSnapshot
from rietveld_next.optimization.objectives import ObjectiveEvaluation, ObjectiveFunction
from rietveld_next.optimization.transforms import BoundTransform


_SCIPY_AUTO = object()


@dataclass(frozen=True)
class ScipyOptimizerOptions:
    """Options shared by optional SciPy local optimizer adapters.

    Args:
        max_evaluations: Maximum objective or residual evaluations.
        tolerance: Solver tolerance passed to SciPy where supported.
    """

    max_evaluations: int = 100
    tolerance: float = 1.0e-8

    def __post_init__(self) -> None:
        """Validate option values."""
        if isinstance(self.max_evaluations, bool) or not isinstance(self.max_evaluations, int):
            raise ValueError("max_evaluations must be a positive integer.")
        if self.max_evaluations <= 0:
            raise ValueError("max_evaluations must be a positive integer.")
        _positive_float(self.tolerance, "tolerance")


@dataclass(frozen=True)
class RustOptimizerBound:
    """JSON-compatible bound record for a Rust local optimizer request.

    Args:
        lower: Optional inclusive lower bound in physical parameter units.
        upper: Optional inclusive upper bound in physical parameter units.
    """

    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        """Validate bound values."""
        lower = _optional_float(self.lower, "lower")
        upper = _optional_float(self.upper, "upper")
        if lower is not None and upper is not None and lower >= upper:
            raise ValueError(f"lower must be less than upper, got {lower!r} and {upper!r}.")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    def to_dict(self) -> dict[str, float | None]:
        """Return a JSON-compatible bound mapping."""
        return {"lower": self.lower, "upper": self.upper}


@dataclass(frozen=True)
class RustLocalOptimizerRequest:
    """Portable request contract for a Rust local optimizer backend.

    Args:
        objective_name: Stable objective identifier implemented by the backend.
        initial_parameters: Initial physical parameter vector.
        bounds: Optional per-parameter bounds.
        options: JSON-compatible backend options.
    """

    objective_name: str
    initial_parameters: tuple[float, ...]
    bounds: tuple[RustOptimizerBound, ...] = ()
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate request fields."""
        if not isinstance(self.objective_name, str) or not self.objective_name:
            raise ValueError("objective_name must be a non-empty string.")
        parameters = tuple(_finite_sequence(self.initial_parameters, "initial_parameters"))
        object.__setattr__(self, "initial_parameters", parameters)
        bounds = _rust_bounds_for_parameters(parameters, self.bounds)
        object.__setattr__(self, "bounds", bounds)
        _json_compatible(self.options, "options")
        object.__setattr__(self, "options", dict(sorted(self.options.items())))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "objective_name": self.objective_name,
            "initial_parameters": list(self.initial_parameters),
            "bounds": [bound.to_dict() for bound in self.bounds],
            "options": dict(self.options),
        }


class RustLocalOptimizerBackend(Protocol):
    """Protocol implemented by Rust-backed local optimizer bindings."""

    def optimize(self, request: RustLocalOptimizerRequest) -> ConvergenceReport:
        """Run local optimization and return a convergence report."""


def scipy_trust_region_minimize(
    objective: ObjectiveFunction,
    initial_parameters: Sequence[float],
    *,
    bounds: Sequence[BoundTransform] | None = None,
    options: ScipyOptimizerOptions | None = None,
    scipy_optimize: Any = _SCIPY_AUTO,
) -> ConvergenceReport:
    """Run the optional SciPy trust-region adapter.

    The adapter uses ``scipy.optimize.minimize(method="trust-constr")`` when
    SciPy is importable. If SciPy is unavailable, it returns a structured
    ``dependency_unavailable`` report without fabricating convergence.

    Args:
        objective: Objective callable.
        initial_parameters: Initial physical parameter vector.
        bounds: Optional parameter bounds.
        options: Adapter options.
        scipy_optimize: Test hook for a SciPy-like optimize module.

    Returns:
        Structured convergence report.
    """
    settings = options or ScipyOptimizerOptions()
    parameters = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
    bound_list = _bounds_for_parameters(parameters, bounds)
    initial_evaluation = _evaluate_objective(objective, parameters)
    if initial_evaluation.status != "ok":
        return _initial_failure_report(initial_evaluation, "trust_region")
    module = _scipy_optimize_module(scipy_optimize)
    if module is None:
        return _dependency_unavailable_report(parameters, initial_evaluation, "trust_region")

    lower, upper = _scipy_bounds(bound_list)
    scipy_bounds = module.Bounds(lower, upper)
    result = module.minimize(
        lambda values: _evaluate_objective(objective, tuple(float(value) for value in values)).objective_value,
        parameters,
        method="trust-constr",
        bounds=scipy_bounds,
        options={"maxiter": settings.max_evaluations, "gtol": settings.tolerance, "xtol": settings.tolerance},
    )
    final_parameters = tuple(_finite_sequence(tuple(float(value) for value in result.x), "result.x"))
    final_value = _finite_float(float(result.fun), "result.fun")
    return _adapter_report(
        adapter="trust_region",
        success=bool(result.success),
        status_code=getattr(result, "status", ""),
        message=str(getattr(result, "message", "")),
        initial=initial_evaluation,
        final_parameters=final_parameters,
        final_value=final_value,
        iterations=int(getattr(result, "nit", 0) or 0),
        evaluations=int(getattr(result, "nfev", 0) or 0),
    )


def scipy_levenberg_marquardt_minimize(
    objective: ObjectiveFunction,
    initial_parameters: Sequence[float],
    *,
    options: ScipyOptimizerOptions | None = None,
    scipy_optimize: Any = _SCIPY_AUTO,
) -> ConvergenceReport:
    """Run the optional SciPy Levenberg-Marquardt adapter.

    The adapter uses ``scipy.optimize.least_squares(method="lm")`` when SciPy
    is importable. Bounds are intentionally not accepted because SciPy's LM
    method is unconstrained.

    Args:
        objective: Objective callable.
        initial_parameters: Initial physical parameter vector.
        options: Adapter options.
        scipy_optimize: Test hook for a SciPy-like optimize module.

    Returns:
        Structured convergence report.
    """
    settings = options or ScipyOptimizerOptions()
    parameters = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
    initial_evaluation = _evaluate_objective(objective, parameters)
    if initial_evaluation.status != "ok":
        return _initial_failure_report(initial_evaluation, "levenberg_marquardt")
    module = _scipy_optimize_module(scipy_optimize)
    if module is None:
        return _dependency_unavailable_report(parameters, initial_evaluation, "levenberg_marquardt")

    result = module.least_squares(
        lambda values: _lm_residuals(objective, tuple(float(value) for value in values)),
        parameters,
        method="lm",
        max_nfev=settings.max_evaluations,
        xtol=settings.tolerance,
        ftol=settings.tolerance,
        gtol=settings.tolerance,
    )
    final_parameters = tuple(_finite_sequence(tuple(float(value) for value in result.x), "result.x"))
    final_value = _finite_float(float(getattr(result, "cost", 0.0)), "result.cost")
    return _adapter_report(
        adapter="levenberg_marquardt",
        success=bool(result.success),
        status_code=getattr(result, "status", ""),
        message=str(getattr(result, "message", "")),
        initial=initial_evaluation,
        final_parameters=final_parameters,
        final_value=final_value,
        iterations=int(getattr(result, "njev", 0) or 0),
        evaluations=int(getattr(result, "nfev", 0) or 0),
    )


def run_rust_local_optimizer(
    backend: RustLocalOptimizerBackend,
    request: RustLocalOptimizerRequest,
) -> ConvergenceReport:
    """Run a Rust local optimizer backend through the typed protocol.

    Args:
        backend: Object implementing ``RustLocalOptimizerBackend``.
        request: Portable optimizer request.

    Returns:
        Backend convergence report.

    Raises:
        ValueError: If backend or request objects are malformed.
    """
    if not isinstance(request, RustLocalOptimizerRequest):
        raise ValueError("request must be a RustLocalOptimizerRequest.")
    optimize = getattr(backend, "optimize", None)
    if not callable(optimize):
        raise ValueError("backend must provide an optimize(request) method.")
    report = optimize(request)
    if not isinstance(report, ConvergenceReport):
        raise ValueError("backend optimize(request) must return a ConvergenceReport.")
    return report


def _scipy_optimize_module(scipy_optimize: Any) -> Any | None:
    if scipy_optimize is None:
        return None
    if scipy_optimize is not _SCIPY_AUTO:
        return scipy_optimize
    try:
        return import_module("scipy.optimize")
    except ImportError:
        return None


def _evaluate_objective(objective: ObjectiveFunction, parameters: tuple[float, ...]) -> ObjectiveEvaluation:
    if not callable(objective):
        raise ValueError("objective must be callable.")
    try:
        evaluation = objective(parameters)
    except ValueError as exc:
        return ObjectiveEvaluation(
            parameters=parameters,
            objective_value=1.0e300,
            status="invalid",
            message=str(exc),
            diagnostics={"exception": exc.__class__.__name__},
        )
    if not isinstance(evaluation, ObjectiveEvaluation):
        raise ValueError("objective must return an ObjectiveEvaluation.")
    return evaluation


def _initial_failure_report(evaluation: ObjectiveEvaluation, adapter: str) -> ConvergenceReport:
    return ConvergenceReport(
        status="invalid_initial_model",
        message=evaluation.message or "Initial objective evaluation was invalid.",
        converged=False,
        iterations=0,
        evaluations=1,
        objective_value=evaluation.objective_value,
        parameters=evaluation.parameters,
        snapshots=(),
        diagnostics={"adapter": adapter, **evaluation.diagnostics},
    )


def _dependency_unavailable_report(
    parameters: tuple[float, ...],
    evaluation: ObjectiveEvaluation,
    adapter: str,
) -> ConvergenceReport:
    return ConvergenceReport(
        status="dependency_unavailable",
        message="SciPy is not available; local optimizer adapter was not run.",
        converged=False,
        iterations=0,
        evaluations=1,
        objective_value=evaluation.objective_value,
        parameters=parameters,
        snapshots=(OptimizerSnapshot(iteration=0, parameters=parameters, objective_value=evaluation.objective_value),),
        diagnostics={"adapter": adapter, "dependency": "scipy.optimize"},
    )


def _adapter_report(
    *,
    adapter: str,
    success: bool,
    status_code: Any,
    message: str,
    initial: ObjectiveEvaluation,
    final_parameters: tuple[float, ...],
    final_value: float,
    iterations: int,
    evaluations: int,
) -> ConvergenceReport:
    status = "converged" if success else "failed"
    return ConvergenceReport(
        status=status,
        message=message or status,
        converged=success,
        iterations=max(iterations, 0),
        evaluations=max(evaluations, 1),
        objective_value=final_value,
        parameters=final_parameters,
        snapshots=(
            OptimizerSnapshot(iteration=0, parameters=initial.parameters, objective_value=initial.objective_value),
            OptimizerSnapshot(iteration=max(iterations, 0), parameters=final_parameters, objective_value=final_value),
        ),
        diagnostics={"adapter": adapter, "status_code": status_code},
    )


def _lm_residuals(objective: ObjectiveFunction, parameters: tuple[float, ...]) -> tuple[float, ...]:
    evaluation = _evaluate_objective(objective, parameters)
    if evaluation.status != "ok":
        return (math.sqrt(2.0 * evaluation.objective_value),)
    if evaluation.residuals:
        return evaluation.residuals
    return (math.sqrt(max(0.0, 2.0 * evaluation.objective_value)),)


def _bounds_for_parameters(
    parameters: tuple[float, ...],
    bounds: Sequence[BoundTransform] | None,
) -> tuple[BoundTransform, ...]:
    if bounds is None:
        return tuple(BoundTransform() for _ in parameters)
    if isinstance(bounds, str) or not isinstance(bounds, Sequence):
        raise ValueError("bounds must be a sequence of BoundTransform values.")
    bound_list = tuple(bounds)
    if len(bound_list) != len(parameters):
        raise ValueError(f"bounds length must match parameters length, got {len(bound_list)} and {len(parameters)}.")
    for index, bound in enumerate(bound_list):
        if not isinstance(bound, BoundTransform):
            raise ValueError(f"bounds[{index}] must be a BoundTransform.")
        bound.validate_value(parameters[index])
    return bound_list


def _scipy_bounds(bounds: Sequence[BoundTransform]) -> tuple[list[float], list[float]]:
    lower = [bound.lower if bound.lower is not None else -math.inf for bound in bounds]
    upper = [bound.upper if bound.upper is not None else math.inf for bound in bounds]
    return lower, upper


def _rust_bounds_for_parameters(
    parameters: tuple[float, ...],
    bounds: Sequence[RustOptimizerBound],
) -> tuple[RustOptimizerBound, ...]:
    if not bounds:
        return tuple(RustOptimizerBound() for _ in parameters)
    if isinstance(bounds, str) or not isinstance(bounds, Sequence):
        raise ValueError("bounds must be a sequence of RustOptimizerBound values.")
    bound_tuple = tuple(bounds)
    if len(bound_tuple) != len(parameters):
        raise ValueError(f"bounds length must match parameters length, got {len(bound_tuple)} and {len(parameters)}.")
    for index, bound in enumerate(bound_tuple):
        if not isinstance(bound, RustOptimizerBound):
            raise ValueError(f"bounds[{index}] must be a RustOptimizerBound.")
        if bound.lower is not None and parameters[index] < bound.lower:
            raise ValueError(f"initial_parameters[{index}] is below its lower bound.")
        if bound.upper is not None and parameters[index] > bound.upper:
            raise ValueError(f"initial_parameters[{index}] is above its upper bound.")
    return bound_tuple


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _optional_float(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    return _finite_float(value, name)


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _json_compatible(value: Any, name: str) -> None:
    if value is None or isinstance(value, str | int | float | bool):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{name} must be JSON-compatible.")
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{name} keys must be strings.")
            _json_compatible(nested, f"{name}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, str):
        for index, nested in enumerate(value):
            _json_compatible(nested, f"{name}[{index}]")
        return
    raise ValueError(f"{name} must be JSON-compatible.")
