"""Deterministic global-search and uncertainty placeholder APIs.

The adapters in this module are intentionally small, dependency-free
infrastructure pieces for synthetic fixtures and workflow plumbing. They use
physical parameter values, explicit bounds, and explicit random seeds so that
tests and audit logs can reproduce every trial.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import math
import random
from typing import Any

from rietveld_next.optimization.local import (
    ConvergenceReport,
    LocalOptimizerOptions,
    OptimizerSnapshot,
    coordinate_search_minimize,
)
from rietveld_next.optimization.objectives import ObjectiveEvaluation, ObjectiveFunction
from rietveld_next.optimization.transforms import BoundTransform

LogPosteriorFunction = Callable[[tuple[float, ...]], float]


@dataclass(frozen=True)
class DifferentialEvolutionOptions:
    """Options for the deterministic differential-evolution-style adapter.

    Args:
        population_size: Number of candidate vectors. Must be at least four.
        max_generations: Maximum number of generations.
        differential_weight: Mutation scale applied to vector differences.
        crossover_probability: Per-parameter binomial crossover probability.
        seed: Non-negative seed for deterministic pseudo-random choices.
        tolerance: Absolute best-objective improvement threshold for early stop.

    Example:
        >>> options = DifferentialEvolutionOptions(seed=7, max_generations=3)
        >>> options.seed
        7
    """

    population_size: int = 8
    max_generations: int = 12
    differential_weight: float = 0.6
    crossover_probability: float = 0.7
    seed: int = 0
    tolerance: float = 1.0e-10

    def __post_init__(self) -> None:
        """Validate differential evolution options."""
        _positive_int(self.population_size, "population_size")
        if self.population_size < 4:
            raise ValueError(f"population_size must be at least 4, got {self.population_size!r}.")
        _positive_int(self.max_generations, "max_generations")
        weight = _finite_float(self.differential_weight, "differential_weight")
        if weight <= 0.0 or weight > 2.0:
            raise ValueError(f"differential_weight must be in (0, 2], got {weight!r}.")
        probability = _finite_float(self.crossover_probability, "crossover_probability")
        if probability < 0.0 or probability > 1.0:
            raise ValueError(f"crossover_probability must be in [0, 1], got {probability!r}.")
        _non_negative_int(self.seed, "seed")
        tolerance = _finite_float(self.tolerance, "tolerance")
        if tolerance < 0.0:
            raise ValueError(f"tolerance must be non-negative, got {tolerance!r}.")


@dataclass(frozen=True)
class SimulatedAnnealingOptions:
    """Options for the deterministic simulated-annealing-style adapter.

    Args:
        max_iterations: Maximum number of proposal steps.
        initial_temperature: Initial Metropolis temperature in objective units.
        cooling_rate: Multiplicative cooling factor in ``(0, 1)``.
        proposal_scale: Gaussian proposal scale in physical parameter units.
        seed: Non-negative seed for deterministic pseudo-random choices.
        temperature_tolerance: Stop when the temperature falls below this value.
    """

    max_iterations: int = 40
    initial_temperature: float = 1.0
    cooling_rate: float = 0.85
    proposal_scale: float = 1.0
    seed: int = 0
    temperature_tolerance: float = 1.0e-6

    def __post_init__(self) -> None:
        """Validate simulated annealing options."""
        _positive_int(self.max_iterations, "max_iterations")
        _positive_float(self.initial_temperature, "initial_temperature")
        cooling_rate = _finite_float(self.cooling_rate, "cooling_rate")
        if cooling_rate <= 0.0 or cooling_rate >= 1.0:
            raise ValueError(f"cooling_rate must be in (0, 1), got {cooling_rate!r}.")
        _positive_float(self.proposal_scale, "proposal_scale")
        _non_negative_int(self.seed, "seed")
        _positive_float(self.temperature_tolerance, "temperature_tolerance")


@dataclass(frozen=True)
class MultiStartOptions:
    """Options for deterministic multi-start local optimization.

    Args:
        start_count: Number of starts to generate when explicit starts are not
            provided.
        seed: Non-negative seed for generated starts.
        include_midpoint: Whether to include finite-bound midpoints as the
            first generated start.
        local_options: Options passed to the local coordinate-search runner.
    """

    start_count: int = 4
    seed: int = 0
    include_midpoint: bool = True
    local_options: LocalOptimizerOptions = field(
        default_factory=lambda: LocalOptimizerOptions(max_iterations=40, initial_step=1.0, tolerance=1.0e-6)
    )

    def __post_init__(self) -> None:
        """Validate multi-start options."""
        _positive_int(self.start_count, "start_count")
        _non_negative_int(self.seed, "seed")
        if not isinstance(self.include_midpoint, bool):
            raise ValueError(f"include_midpoint must be a boolean, got {self.include_midpoint!r}.")
        if not isinstance(self.local_options, LocalOptimizerOptions):
            raise ValueError("local_options must be a LocalOptimizerOptions instance.")


@dataclass(frozen=True)
class MultiStartReport:
    """Structured result from a deterministic multi-start run.

    Args:
        status: Machine-readable run status.
        message: Human-readable status message.
        best_report: Best local optimizer report by objective value.
        reports: Per-start local optimizer reports in deterministic order.
        starts: Physical starting vectors used for each local run.
        diagnostics: JSON-compatible diagnostic metadata.
    """

    status: str
    message: str
    best_report: ConvergenceReport
    reports: tuple[ConvergenceReport, ...]
    starts: tuple[tuple[float, ...], ...]
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate report consistency."""
        if self.status not in {"completed", "all_failed"}:
            raise ValueError(f"status must be 'completed' or 'all_failed', got {self.status!r}.")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string.")
        if not isinstance(self.best_report, ConvergenceReport):
            raise ValueError("best_report must be a ConvergenceReport.")
        if not self.reports:
            raise ValueError("reports must contain at least one ConvergenceReport.")
        if len(self.reports) != len(self.starts):
            raise ValueError(f"reports and starts lengths must match, got {len(self.reports)} and {len(self.starts)}.")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "status": self.status,
            "message": self.message,
            "best_report": self.best_report.to_dict(),
            "reports": [report.to_dict() for report in self.reports],
            "starts": [list(start) for start in self.starts],
            "diagnostics": dict(sorted(self.diagnostics.items())),
        }


@dataclass(frozen=True)
class PlaceholderReport:
    """Structured placeholder result for APIs that are not implemented yet.

    Args:
        feature: Stable feature name.
        status: Placeholder status. Currently always ``"not_implemented"``.
        message: Human-readable limitation statement.
        seed: Non-negative seed recorded for reproducibility.
        parameters: Optional physical parameter vector associated with the
            placeholder request.
        parameter_labels: Optional stable labels matching ``parameters``.
        parameter_units: Optional units matching ``parameter_labels``. Use
            ``""`` for dimensionless parameters.
        diagnostics: JSON-compatible metadata describing the requested workload.
    """

    feature: str
    status: str
    message: str
    seed: int
    parameters: tuple[float, ...] = ()
    parameter_labels: tuple[str, ...] = ()
    parameter_units: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate placeholder metadata."""
        if not isinstance(self.feature, str) or not self.feature:
            raise ValueError("feature must be a non-empty string.")
        if self.status != "not_implemented":
            raise ValueError(f"status must be 'not_implemented', got {self.status!r}.")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string.")
        _non_negative_int(self.seed, "seed")
        _finite_sequence(self.parameters, "parameters")
        _label_tuple(self.parameter_labels, "parameter_labels")
        _unit_tuple(self.parameter_units, "parameter_units")
        if self.parameter_labels and len(self.parameter_labels) != len(self.parameters):
            raise ValueError(
                "parameter_labels length must match parameters length, "
                f"got {len(self.parameter_labels)} and {len(self.parameters)}."
            )
        if self.parameter_units and len(self.parameter_units) != len(self.parameter_labels):
            raise ValueError(
                "parameter_units length must match parameter_labels length, "
                f"got {len(self.parameter_units)} and {len(self.parameter_labels)}."
            )
        _json_compatible(self.diagnostics, "diagnostics")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "feature": self.feature,
            "status": self.status,
            "message": self.message,
            "seed": self.seed,
            "parameters": list(self.parameters),
            "parameter_labels": list(self.parameter_labels),
            "parameter_units": list(self.parameter_units),
            "diagnostics": dict(sorted(self.diagnostics.items())),
        }


def differential_evolution_minimize(
    objective: ObjectiveFunction,
    bounds: Sequence[BoundTransform],
    *,
    initial_parameters: Sequence[float] | None = None,
    options: DifferentialEvolutionOptions | None = None,
) -> ConvergenceReport:
    """Minimize an objective with a tiny deterministic differential evolution loop.

    Args:
        objective: Callable objective returning :class:`ObjectiveEvaluation`.
        bounds: Finite lower and upper physical bounds for each parameter.
        initial_parameters: Optional physical vector inserted into the initial
            population after bounds validation.
        options: Adapter options, including an explicit seed.

    Returns:
        Structured convergence report. Invalid objective evaluations are treated
        as high-penalty trials and recorded in diagnostics.

    Raises:
        ValueError: If the objective, bounds, initial parameters, or options are
            malformed.

    Example:
        >>> from rietveld_next.optimization import BoundTransform, least_squares_evaluation
        >>> def objective(values):
        ...     return least_squares_evaluation(values, [values[0] - 1.0])
        >>> report = differential_evolution_minimize(objective, [BoundTransform(-2.0, 2.0)])
        >>> report.evaluations > 0
        True
    """
    if not callable(objective):
        raise ValueError("objective must be callable.")
    settings = options or DifferentialEvolutionOptions()
    bound_list = _finite_bounds(bounds)
    dimension = len(bound_list)
    if dimension == 0:
        raise ValueError("bounds must contain at least one parameter bound.")

    rng = random.Random(settings.seed)
    population: list[tuple[float, ...]] = []
    if initial_parameters is not None:
        initial = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
        _validate_dimension(initial, dimension, "initial_parameters")
        _validate_inside_bounds(initial, bound_list)
        population.append(initial)
    while len(population) < settings.population_size:
        population.append(tuple(rng.uniform(bound.lower, bound.upper) for bound in bound_list))

    evaluations_by_index: list[ObjectiveEvaluation] = []
    evaluations = 0
    invalid_trials = 0
    for candidate in population:
        evaluation, count = _safe_evaluate(objective, candidate)
        evaluations += count
        if evaluation.status != "ok":
            invalid_trials += 1
        evaluations_by_index.append(evaluation)

    best_index = _best_evaluation_index(evaluations_by_index)
    if best_index is None:
        return _convergence_report(
            status="invalid_initial_population",
            message="No usable objective evaluation was produced by the initial population.",
            converged=False,
            iterations=0,
            evaluations=evaluations,
            objective_value=1.0e300,
            parameters=population[0],
            snapshots=(),
            diagnostics={"method": "differential_evolution", "seed": settings.seed, "invalid_trials": invalid_trials},
        )

    best_parameters = population[best_index]
    best_value = evaluations_by_index[best_index].objective_value
    snapshots = [OptimizerSnapshot(iteration=0, parameters=best_parameters, objective_value=best_value)]

    for generation in range(1, settings.max_generations + 1):
        previous_best_value = best_value
        for target_index, target in enumerate(population):
            donor_indices = [index for index in range(settings.population_size) if index != target_index]
            first, second, third = rng.sample(donor_indices, 3)
            forced_index = rng.randrange(dimension)
            trial = []
            for parameter_index, bound in enumerate(bound_list):
                if parameter_index == forced_index or rng.random() < settings.crossover_probability:
                    value = population[first][parameter_index] + settings.differential_weight * (
                        population[second][parameter_index] - population[third][parameter_index]
                    )
                    trial.append(_clip_to_bound(value, bound))
                else:
                    trial.append(target[parameter_index])
            trial_parameters = tuple(trial)
            trial_evaluation, count = _safe_evaluate(objective, trial_parameters)
            evaluations += count
            if trial_evaluation.status != "ok":
                invalid_trials += 1
                continue
            current_evaluation = evaluations_by_index[target_index]
            if current_evaluation.status != "ok" or trial_evaluation.objective_value < current_evaluation.objective_value:
                population[target_index] = trial_parameters
                evaluations_by_index[target_index] = trial_evaluation
                if trial_evaluation.objective_value < best_value:
                    best_parameters = trial_parameters
                    best_value = trial_evaluation.objective_value

        snapshots.append(OptimizerSnapshot(iteration=generation, parameters=best_parameters, objective_value=best_value))
        if previous_best_value - best_value <= settings.tolerance:
            return _convergence_report(
                status="converged",
                message="Best objective improvement fell below the configured tolerance.",
                converged=True,
                iterations=generation,
                evaluations=evaluations,
                objective_value=best_value,
                parameters=best_parameters,
                snapshots=tuple(snapshots),
                diagnostics={"method": "differential_evolution", "seed": settings.seed, "invalid_trials": invalid_trials},
            )

    return _convergence_report(
        status="max_generations",
        message="Maximum generations reached before improvement tolerance convergence.",
        converged=False,
        iterations=settings.max_generations,
        evaluations=evaluations,
        objective_value=best_value,
        parameters=best_parameters,
        snapshots=tuple(snapshots),
        diagnostics={"method": "differential_evolution", "seed": settings.seed, "invalid_trials": invalid_trials},
    )


def simulated_annealing_minimize(
    objective: ObjectiveFunction,
    initial_parameters: Sequence[float],
    *,
    bounds: Sequence[BoundTransform] | None = None,
    options: SimulatedAnnealingOptions | None = None,
) -> ConvergenceReport:
    """Minimize an objective with a tiny deterministic simulated annealing loop.

    Args:
        objective: Callable objective returning :class:`ObjectiveEvaluation`.
        initial_parameters: Initial physical parameter vector.
        bounds: Optional inclusive physical bounds.
        options: Adapter options, including an explicit seed.

    Returns:
        Structured convergence report with the best accepted state.

    Raises:
        ValueError: If the objective, parameters, bounds, or options are
            malformed.
    """
    if not callable(objective):
        raise ValueError("objective must be callable.")
    settings = options or SimulatedAnnealingOptions()
    current_parameters = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
    if not current_parameters:
        raise ValueError("initial_parameters must contain at least one value.")
    bound_list = _bounds_for_parameters(current_parameters, bounds)
    _validate_inside_bounds(current_parameters, bound_list)

    current_evaluation, evaluations = _safe_evaluate(objective, current_parameters)
    if current_evaluation.status != "ok":
        return _convergence_report(
            status="invalid_initial_model",
            message=current_evaluation.message or "Initial objective evaluation was invalid.",
            converged=False,
            iterations=0,
            evaluations=evaluations,
            objective_value=current_evaluation.objective_value,
            parameters=current_parameters,
            snapshots=(),
            diagnostics=current_evaluation.diagnostics,
        )

    rng = random.Random(settings.seed)
    current_value = current_evaluation.objective_value
    best_parameters = current_parameters
    best_value = current_value
    temperature = settings.initial_temperature
    accepted_trials = 0
    invalid_trials = 0
    snapshots = [OptimizerSnapshot(iteration=0, parameters=best_parameters, objective_value=best_value)]

    for iteration in range(1, settings.max_iterations + 1):
        trial_parameters = tuple(
            _clip_to_bound(value + rng.gauss(0.0, settings.proposal_scale * temperature), bound)
            for value, bound in zip(current_parameters, bound_list, strict=True)
        )
        trial_evaluation, count = _safe_evaluate(objective, trial_parameters)
        evaluations += count
        if trial_evaluation.status != "ok":
            invalid_trials += 1
            temperature *= settings.cooling_rate
            snapshots.append(OptimizerSnapshot(iteration=iteration, parameters=best_parameters, objective_value=best_value))
            continue

        delta = trial_evaluation.objective_value - current_value
        if delta <= 0.0 or rng.random() < math.exp(-delta / max(temperature, 1.0e-300)):
            current_parameters = trial_parameters
            current_value = trial_evaluation.objective_value
            accepted_trials += 1
            if current_value < best_value:
                best_parameters = current_parameters
                best_value = current_value

        temperature *= settings.cooling_rate
        snapshots.append(OptimizerSnapshot(iteration=iteration, parameters=best_parameters, objective_value=best_value))
        if temperature <= settings.temperature_tolerance:
            return _convergence_report(
                status="converged",
                message="Temperature tolerance reached.",
                converged=True,
                iterations=iteration,
                evaluations=evaluations,
                objective_value=best_value,
                parameters=best_parameters,
                snapshots=tuple(snapshots),
                diagnostics={
                    "method": "simulated_annealing",
                    "seed": settings.seed,
                    "accepted_trials": accepted_trials,
                    "invalid_trials": invalid_trials,
                    "final_temperature": temperature,
                },
            )

    return _convergence_report(
        status="max_iterations",
        message="Maximum iterations reached before temperature convergence.",
        converged=False,
        iterations=settings.max_iterations,
        evaluations=evaluations,
        objective_value=best_value,
        parameters=best_parameters,
        snapshots=tuple(snapshots),
        diagnostics={
            "method": "simulated_annealing",
            "seed": settings.seed,
            "accepted_trials": accepted_trials,
            "invalid_trials": invalid_trials,
            "final_temperature": temperature,
        },
    )


def multi_start_minimize(
    objective: ObjectiveFunction,
    *,
    bounds: Sequence[BoundTransform] | None = None,
    starts: Sequence[Sequence[float]] | None = None,
    options: MultiStartOptions | None = None,
) -> MultiStartReport:
    """Run deterministic local coordinate search from multiple starts.

    Args:
        objective: Callable objective returning :class:`ObjectiveEvaluation`.
        bounds: Optional inclusive physical bounds for all local runs. Finite
            bounds are required when starts are generated.
        starts: Optional explicit physical starts. When omitted, starts are
            generated uniformly from finite bounds using ``options.seed``.
        options: Multi-start options.

    Returns:
        Structured report containing every local run and the best run.

    Raises:
        ValueError: If inputs are malformed or generated starts are requested
            without finite bounds.
    """
    if not callable(objective):
        raise ValueError("objective must be callable.")
    settings = options or MultiStartOptions()
    start_vectors = _resolve_starts(bounds=bounds, starts=starts, options=settings)
    bound_list = _bounds_for_parameters(start_vectors[0], bounds)

    reports = tuple(
        coordinate_search_minimize(objective, start, bounds=bound_list, options=settings.local_options)
        for start in start_vectors
    )
    successful_reports = [report for report in reports if report.status not in {"invalid_initial_model"}]
    best_pool = successful_reports or list(reports)
    best_report = min(best_pool, key=lambda report: (report.objective_value, report.evaluations, report.parameters))
    status = "completed" if successful_reports else "all_failed"
    return MultiStartReport(
        status=status,
        message="Multi-start local optimization completed." if successful_reports else "All starts failed before local search.",
        best_report=best_report,
        reports=reports,
        starts=start_vectors,
        diagnostics={"method": "multi_start", "seed": settings.seed, "start_count": len(start_vectors)},
    )


def bayesian_optimization_placeholder(
    objective: ObjectiveFunction,
    bounds: Sequence[BoundTransform],
    *,
    seed: int = 0,
    max_trials: int = 8,
    acquisition: str = "expected_improvement",
) -> PlaceholderReport:
    """Return a structured placeholder for future Bayesian optimization.

    The objective is validated for callability but is not evaluated. This avoids
    inventing surrogate-model behavior before a backend, acquisition optimizer,
    and validation suite are selected.

    Args:
        objective: Callable objective reserved for the future implementation.
        bounds: Finite physical parameter bounds for the requested search.
        seed: Non-negative seed to record for reproducibility.
        max_trials: Requested maximum surrogate-guided trials.
        acquisition: Requested acquisition strategy name.

    Returns:
        Placeholder report with ``status="not_implemented"``.

    Raises:
        ValueError: If request metadata is malformed.
    """
    if not callable(objective):
        raise ValueError("objective must be callable.")
    _non_negative_int(seed, "seed")
    _positive_int(max_trials, "max_trials")
    if not isinstance(acquisition, str) or not acquisition:
        raise ValueError("acquisition must be a non-empty string.")
    bound_list = _finite_bounds(bounds)
    return PlaceholderReport(
        feature="bayesian_optimization",
        status="not_implemented",
        message="Bayesian optimization requires a validated surrogate-model backend and is not implemented yet.",
        seed=seed,
        diagnostics={
            "acquisition": acquisition,
            "bounds": [[bound.lower, bound.upper] for bound in bound_list],
            "max_trials": max_trials,
            "reason": "surrogate_backend_not_selected",
        },
    )


def mcmc_uncertainty_placeholder(
    log_posterior: LogPosteriorFunction,
    initial_parameters: Sequence[float],
    *,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    seed: int = 0,
    chains: int = 2,
    draws: int = 32,
) -> PlaceholderReport:
    """Return a structured placeholder for future MCMC uncertainty estimation.

    The log-posterior is validated for callability but is not evaluated. This
    avoids reporting unvalidated posterior samples, uncertainties, or
    correlations before an MCMC backend and convergence diagnostics are chosen.

    Args:
        log_posterior: Callable log-posterior reserved for future sampling.
        initial_parameters: Initial physical parameter vector.
        parameter_labels: Optional parameter labels.
        parameter_units: Optional units matching labels.
        seed: Non-negative seed to record for reproducibility.
        chains: Requested number of chains.
        draws: Requested number of retained draws per chain.

    Returns:
        Placeholder report with ``status="not_implemented"``.

    Raises:
        ValueError: If request metadata is malformed.
    """
    if not callable(log_posterior):
        raise ValueError("log_posterior must be callable.")
    parameters = tuple(_finite_sequence(initial_parameters, "initial_parameters"))
    if not parameters:
        raise ValueError("initial_parameters must contain at least one value.")
    labels = _resolved_labels(parameter_labels, len(parameters))
    units = _resolved_units(parameter_units, len(labels))
    _non_negative_int(seed, "seed")
    _positive_int(chains, "chains")
    _positive_int(draws, "draws")
    return PlaceholderReport(
        feature="mcmc_uncertainty",
        status="not_implemented",
        message="MCMC uncertainty estimation requires validated sampling and convergence diagnostics and is not implemented yet.",
        seed=seed,
        parameters=parameters,
        parameter_labels=labels,
        parameter_units=units,
        diagnostics={"chains": chains, "draws": draws, "reason": "sampler_backend_not_selected"},
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


def _resolve_starts(
    *,
    bounds: Sequence[BoundTransform] | None,
    starts: Sequence[Sequence[float]] | None,
    options: MultiStartOptions,
) -> tuple[tuple[float, ...], ...]:
    if starts is not None:
        if isinstance(starts, str) or not isinstance(starts, Sequence) or not starts:
            raise ValueError("starts must be a non-empty sequence of parameter vectors.")
        start_vectors = tuple(tuple(_finite_sequence(start, f"starts[{index}]")) for index, start in enumerate(starts))
        dimension = len(start_vectors[0])
        if dimension == 0:
            raise ValueError("starts must contain at least one parameter per start.")
        for index, start in enumerate(start_vectors):
            _validate_dimension(start, dimension, f"starts[{index}]")
        if bounds is not None:
            bound_list = _bounds_for_parameters(start_vectors[0], bounds)
            for start in start_vectors:
                _validate_inside_bounds(start, bound_list)
        return start_vectors

    bound_list = _finite_bounds(bounds)
    if not bound_list:
        raise ValueError("bounds must contain at least one parameter bound.")
    rng = random.Random(options.seed)
    generated: list[tuple[float, ...]] = []
    if options.include_midpoint:
        generated.append(tuple(0.5 * (bound.lower + bound.upper) for bound in bound_list))
    while len(generated) < options.start_count:
        generated.append(tuple(rng.uniform(bound.lower, bound.upper) for bound in bound_list))
    return tuple(generated[: options.start_count])


def _best_evaluation_index(evaluations: Sequence[ObjectiveEvaluation]) -> int | None:
    best_index: int | None = None
    best_value = math.inf
    for index, evaluation in enumerate(evaluations):
        if evaluation.status == "ok" and evaluation.objective_value < best_value:
            best_index = index
            best_value = evaluation.objective_value
    return best_index


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


def _finite_bounds(bounds: Sequence[BoundTransform] | None) -> list[BoundTransform]:
    if bounds is None or isinstance(bounds, str) or not isinstance(bounds, Sequence):
        raise ValueError("bounds must be a sequence of finite BoundTransform values.")
    bound_list = list(bounds)
    for index, bound in enumerate(bound_list):
        if not isinstance(bound, BoundTransform):
            raise ValueError(f"bounds[{index}] must be a BoundTransform.")
        if bound.lower is None or bound.upper is None:
            raise ValueError(f"bounds[{index}] must have finite lower and upper bounds.")
    return bound_list


def _validate_inside_bounds(values: Sequence[float], bounds: Sequence[BoundTransform]) -> None:
    for value, bound in zip(values, bounds, strict=True):
        bound.validate_value(value)


def _validate_dimension(values: Sequence[float], expected: int, name: str) -> None:
    if len(values) != expected:
        raise ValueError(f"{name} length must be {expected}, got {len(values)}.")


def _clip_to_bound(value: float, bound: BoundTransform) -> float:
    finite_value = _finite_float(value, "value")
    if bound.lower is not None:
        finite_value = max(bound.lower, finite_value)
    if bound.upper is not None:
        finite_value = min(bound.upper, finite_value)
    return finite_value


def _convergence_report(
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


def _resolved_labels(labels: Sequence[str] | None, size: int) -> tuple[str, ...]:
    if labels is None:
        return tuple(f"parameter_{index}" for index in range(size))
    resolved = _label_tuple(labels, "parameter_labels")
    if len(resolved) != size:
        raise ValueError(f"parameter_labels length must be {size}, got {len(resolved)}.")
    return resolved


def _resolved_units(units: Sequence[str] | None, size: int) -> tuple[str, ...]:
    if units is None:
        return tuple("" for _ in range(size))
    resolved = _unit_tuple(units, "parameter_units")
    if len(resolved) != size:
        raise ValueError(f"parameter_units length must be {size}, got {len(resolved)}.")
    return resolved


def _label_tuple(labels: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(labels, str) or not isinstance(labels, Sequence):
        raise ValueError(f"{name} must be a sequence of non-empty strings.")
    resolved: list[str] = []
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"{name}[{index}] must be a non-empty string.")
        resolved.append(label)
    return tuple(resolved)


def _unit_tuple(units: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(units, str) or not isinstance(units, Sequence):
        raise ValueError(f"{name} must be a sequence of strings.")
    resolved: list[str] = []
    for index, unit in enumerate(units):
        if not isinstance(unit, str):
            raise ValueError(f"{name}[{index}] must be a string.")
        resolved.append(unit)
    return tuple(resolved)


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


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")
    return value


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")
    return value


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
