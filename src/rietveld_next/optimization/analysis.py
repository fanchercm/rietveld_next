"""Deterministic optimizer analysis helpers.

The helpers in this module compare optimizer outputs, rank model-selection
scores, recommend parameter freezes, detect overparameterization, and derive
stable seeds. They are generic analysis utilities; they do not mutate models or
change numerical optimizer kernels.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import math
from typing import Any, Literal

ModelCriterion = Literal["aic", "aicc", "bic"]

_MAX_SEED = 2**32 - 1
_SEED_ALGORITHM = "sha256-u32-v1"


@dataclass(frozen=True)
class OptimizerComparisonRow:
    """Single optimizer result in a deterministic comparison table.

    Args:
        label: Stable result label.
        rank: One-based objective rank. Lower objective values rank first.
        status: Source optimizer status, or ``"unknown"`` when unavailable.
        converged: Source convergence flag, or ``None`` when unavailable.
        objective_value: Scalar objective value. Lower is better.
        objective_delta: Difference from the best objective value.
        parameters: Final parameter vector.
        max_abs_parameter_delta: Largest absolute parameter difference from the
            selected comparison reference.
        equivalent_to_best: Whether the objective is within the configured
            objective tolerance of the best result.
        warnings: Human-readable comparison warnings.
    """

    label: str
    rank: int
    status: str
    converged: bool | None
    objective_value: float
    objective_delta: float
    parameters: tuple[float, ...]
    max_abs_parameter_delta: float
    equivalent_to_best: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "label": self.label,
            "rank": self.rank,
            "status": self.status,
            "converged": self.converged,
            "objective_value": self.objective_value,
            "objective_delta": self.objective_delta,
            "parameters": list(self.parameters),
            "max_abs_parameter_delta": self.max_abs_parameter_delta,
            "equivalent_to_best": self.equivalent_to_best,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class OptimizerComparisonReport:
    """Deterministic comparison of multiple optimizer result records.

    Args:
        best_label: Label for the lowest-objective result.
        rows: Comparison rows sorted by objective value then label.
        objective_tolerance: Absolute tolerance for objective equivalence.
        parameter_tolerance: Absolute tolerance for parameter-shift warnings.
        reference_label: Label of the parameter reference, or ``"provided"``
            when explicit reference parameters were supplied.
        warnings: Human-readable report warnings.
    """

    best_label: str
    rows: tuple[OptimizerComparisonRow, ...]
    objective_tolerance: float
    parameter_tolerance: float
    reference_label: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "best_label": self.best_label,
            "rows": [row.to_dict() for row in self.rows],
            "objective_tolerance": self.objective_tolerance,
            "parameter_tolerance": self.parameter_tolerance,
            "reference_label": self.reference_label,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ParameterFreezeRecommendation:
    """Recommendation to review or freeze one parameter.

    Args:
        index: Parameter index.
        label: Stable parameter label.
        unit: Parameter unit. Use ``""`` for dimensionless parameters.
        severity: ``"freeze_candidate"`` or ``"review"``.
        reasons: Deterministic reason codes.
        evidence: JSON-compatible numerical evidence.
    """

    index: int
    label: str
    unit: str
    severity: Literal["freeze_candidate", "review"]
    reasons: tuple[str, ...]
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "index": self.index,
            "label": self.label,
            "unit": self.unit,
            "severity": self.severity,
            "reasons": list(self.reasons),
            "evidence": dict(sorted(self.evidence.items())),
        }


@dataclass(frozen=True)
class ParameterFreezeReport:
    """Parameter-freezing recommendations without model mutation.

    Args:
        status: ``"ok"`` when no candidates are found, otherwise
            ``"recommendations"``.
        recommendations: Parameters recommended for review or freezing.
        parameter_labels: Labels matching the analyzed parameter vector.
        parameter_units: Units matching ``parameter_labels``.
        warnings: Human-readable diagnostic warnings.
    """

    status: Literal["ok", "recommendations"]
    recommendations: tuple[ParameterFreezeRecommendation, ...]
    parameter_labels: tuple[str, ...]
    parameter_units: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "status": self.status,
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
            "parameter_labels": list(self.parameter_labels),
            "parameter_units": list(self.parameter_units),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class OverparameterizationReport:
    """Structured overparameterization diagnostic.

    Args:
        status: ``"ok"``, ``"suspect"``, or ``"overparameterized"``.
        parameter_count: Number of model parameters.
        observation_count: Number of residual observations, when known.
        degrees_of_freedom: ``observation_count - parameter_count`` when known.
        rank: Estimated rank of the Jacobian or normal matrix.
        condition_number: Infinity-norm condition estimate, or ``math.inf``
            when singular.
        flags: Deterministic machine-readable diagnostic flags.
        parameter_labels: Labels for the analyzed parameters.
        parameter_units: Units matching ``parameter_labels``.
        warnings: Human-readable diagnostic warnings.
    """

    status: Literal["ok", "suspect", "overparameterized"]
    parameter_count: int
    observation_count: int | None
    degrees_of_freedom: int | None
    rank: int
    condition_number: float
    flags: tuple[str, ...]
    parameter_labels: tuple[str, ...]
    parameter_units: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "status": self.status,
            "parameter_count": self.parameter_count,
            "observation_count": self.observation_count,
            "degrees_of_freedom": self.degrees_of_freedom,
            "rank": self.rank,
            "condition_number": self.condition_number,
            "flags": list(self.flags),
            "parameter_labels": list(self.parameter_labels),
            "parameter_units": list(self.parameter_units),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ModelSelectionInput:
    """Input record for information-criterion model scoring.

    Args:
        model_id: Stable model identifier.
        objective_value: Scalar optimizer objective. For
            ``objective_kind="half_sum_squares"``, this is interpreted as
            ``0.5 * sum(residual_i ** 2)``.
        observation_count: Number of residual observations used by the model.
        parameter_count: Number of fitted model parameters.
        objective_kind: Objective interpretation. Currently only
            ``"half_sum_squares"`` is supported.
    """

    model_id: str
    objective_value: float
    observation_count: int
    parameter_count: int
    objective_kind: Literal["half_sum_squares"] = "half_sum_squares"

    def __post_init__(self) -> None:
        """Validate model-selection input."""
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string.")
        objective = _finite_float(self.objective_value, "objective_value")
        if objective < 0.0:
            raise ValueError(f"objective_value must be non-negative, got {objective!r}.")
        _positive_int(self.observation_count, "observation_count")
        _non_negative_int(self.parameter_count, "parameter_count")
        if self.parameter_count >= self.observation_count:
            raise ValueError(
                "parameter_count must be smaller than observation_count for information-criterion scoring, "
                f"got {self.parameter_count} and {self.observation_count}."
            )
        if self.objective_kind != "half_sum_squares":
            raise ValueError(f"objective_kind must be 'half_sum_squares', got {self.objective_kind!r}.")


@dataclass(frozen=True)
class ModelSelectionScore:
    """Information-criterion score for one model.

    Args:
        model_id: Stable model identifier.
        criterion: Score criterion.
        score: Criterion value. Lower is better.
        rank: One-based rank when returned from ``rank_model_selection``.
        objective_value: Source scalar objective value.
        observation_count: Number of residual observations.
        parameter_count: Number of fitted parameters.
        likelihood_assumption: Recorded scoring assumption.
        warnings: Human-readable scoring warnings.
    """

    model_id: str
    criterion: ModelCriterion
    score: float
    rank: int
    objective_value: float
    observation_count: int
    parameter_count: int
    likelihood_assumption: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "model_id": self.model_id,
            "criterion": self.criterion,
            "score": self.score,
            "rank": self.rank,
            "objective_value": self.objective_value,
            "observation_count": self.observation_count,
            "parameter_count": self.parameter_count,
            "likelihood_assumption": self.likelihood_assumption,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SeedPlan:
    """Deterministic seed plan for optimizer runs.

    Args:
        base_seed: User-provided base seed.
        algorithm: Stable derivation algorithm identifier.
        seeds: Mapping from run label to derived unsigned 32-bit seed.
    """

    base_seed: int
    algorithm: str
    seeds: dict[str, int]

    def __post_init__(self) -> None:
        """Validate seed plan values."""
        _seed_value(self.base_seed, "base_seed")
        if self.algorithm != _SEED_ALGORITHM:
            raise ValueError(f"algorithm must be {_SEED_ALGORITHM!r}, got {self.algorithm!r}.")
        if not isinstance(self.seeds, dict) or not self.seeds:
            raise ValueError("seeds must be a non-empty mapping.")
        labels = set()
        for label, seed in self.seeds.items():
            if not isinstance(label, str) or not label:
                raise ValueError("seed labels must be non-empty strings.")
            if label in labels:
                raise ValueError(f"duplicate seed label {label!r}.")
            labels.add(label)
            _seed_value(seed, f"seeds[{label!r}]")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "base_seed": self.base_seed,
            "algorithm": self.algorithm,
            "seeds": {label: self.seeds[label] for label in sorted(self.seeds)},
        }


def compare_optimizer_results(
    results: Sequence[Any],
    *,
    labels: Sequence[str] | None = None,
    reference_parameters: Sequence[float] | None = None,
    objective_tolerance: float = 1.0e-12,
    parameter_tolerance: float = 1.0e-8,
) -> OptimizerComparisonReport:
    """Compare optimizer results by objective value and parameter shifts.

    Args:
        results: Result objects or mappings with ``objective_value`` and
            ``parameters`` fields.
        labels: Optional stable labels. Defaults to ``result_0``, ``result_1``,
            and so on.
        reference_parameters: Optional parameter vector for shift comparison.
            When omitted, the best result parameters are used.
        objective_tolerance: Absolute tolerance for objective equivalence.
        parameter_tolerance: Absolute tolerance for parameter-shift warnings.

    Returns:
        Comparison report sorted deterministically by objective value then
        label.

    Raises:
        ValueError: If result fields, labels, or tolerances are invalid.

    Example:
        >>> report = compare_optimizer_results([{"objective_value": 2.0, "parameters": [1.0]}])
        >>> report.best_label
        'result_0'
    """
    tolerance = _non_negative_float(objective_tolerance, "objective_tolerance")
    parameter_shift_tolerance = _non_negative_float(parameter_tolerance, "parameter_tolerance")
    records = [_optimizer_record(result, index) for index, result in enumerate(results)]
    if not records:
        raise ValueError("results must contain at least one optimizer result.")
    resolved_labels = _resolved_labels(labels, len(records), prefix="result")
    labeled_records = [
        (resolved_labels[index], record[0], record[1], record[2], record[3])
        for index, record in enumerate(records)
    ]
    sorted_records = sorted(labeled_records, key=lambda item: (item[1], item[0]))
    best_label, best_objective, best_parameters, _best_status, _best_converged = sorted_records[0]
    if reference_parameters is None:
        reference = best_parameters
        reference_label = best_label
    else:
        reference = tuple(_finite_sequence(reference_parameters, "reference_parameters"))
        if len(reference) != len(best_parameters):
            raise ValueError(
                "reference_parameters length must match result parameter length, "
                f"got {len(reference)} and {len(best_parameters)}."
            )
        reference_label = "provided"

    rows: list[OptimizerComparisonRow] = []
    report_warnings: list[str] = []
    for rank, (label, objective, parameters, status, converged) in enumerate(sorted_records, start=1):
        if len(parameters) != len(reference):
            raise ValueError(
                f"parameters for {label!r} have length {len(parameters)} but reference length is {len(reference)}."
            )
        objective_delta = objective - best_objective
        max_parameter_delta = _max_abs_delta(parameters, reference)
        warnings = []
        if max_parameter_delta > parameter_shift_tolerance:
            warnings.append("parameter_shift_exceeds_tolerance")
        if converged is False:
            warnings.append("result_not_converged")
        if status not in {"ok", "converged", "completed", "max_iterations", "max_generations", "unknown"}:
            warnings.append(f"source_status:{status}")
        rows.append(
            OptimizerComparisonRow(
                label=label,
                rank=rank,
                status=status,
                converged=converged,
                objective_value=objective,
                objective_delta=objective_delta,
                parameters=parameters,
                max_abs_parameter_delta=max_parameter_delta,
                equivalent_to_best=abs(objective_delta) <= tolerance,
                warnings=tuple(warnings),
            )
        )
    if sum(1 for row in rows if row.equivalent_to_best) > 1:
        report_warnings.append("multiple_results_equivalent_to_best")
    return OptimizerComparisonReport(
        best_label=best_label,
        rows=tuple(rows),
        objective_tolerance=tolerance,
        parameter_tolerance=parameter_shift_tolerance,
        reference_label=reference_label,
        warnings=tuple(report_warnings),
    )


def recommend_parameter_freezing(
    parameter_values: Sequence[float],
    *,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    standard_uncertainties: Sequence[float] | None = None,
    correlation_matrix: Sequence[Sequence[float]] | None = None,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    relative_uncertainty_threshold: float = 1.0,
    high_correlation_threshold: float = 0.98,
    near_bound_fraction: float = 1.0e-6,
) -> ParameterFreezeReport:
    """Recommend parameters for freezing or review.

    Recommendations are diagnostic only. The function never changes parameter
    values, bounds, or model state.

    Args:
        parameter_values: Current fitted parameter vector.
        parameter_labels: Optional labels. Defaults to ``p0``, ``p1``, and so
            on.
        parameter_units: Optional units. Defaults to ``""``.
        standard_uncertainties: Optional parameter standard uncertainties.
        correlation_matrix: Optional parameter correlation matrix.
        bounds: Optional ``(lower, upper)`` bounds per parameter. Use ``None``
            for an open side.
        relative_uncertainty_threshold: Flag parameters with
            ``uncertainty / max(abs(value), 1)`` at or above this threshold.
        high_correlation_threshold: Flag pairs whose absolute correlation is at
            or above this threshold.
        near_bound_fraction: Flag finite-bound parameters within this fraction
            of the bound width.

    Returns:
        Structured recommendation report.

    Raises:
        ValueError: If shapes, units, thresholds, bounds, or numeric values are
            invalid.
    """
    values = tuple(_finite_sequence(parameter_values, "parameter_values"))
    labels = _resolved_labels(parameter_labels, len(values), prefix="p")
    units = _resolved_units(parameter_units, len(values))
    if not values:
        raise ValueError("parameter_values must contain at least one value.")
    rel_threshold = _positive_float(relative_uncertainty_threshold, "relative_uncertainty_threshold")
    corr_threshold = _bounded_threshold(high_correlation_threshold, "high_correlation_threshold")
    bound_fraction = _non_negative_float(near_bound_fraction, "near_bound_fraction")
    uncertainties = None
    if standard_uncertainties is not None:
        uncertainties = tuple(_finite_sequence(standard_uncertainties, "standard_uncertainties"))
        if len(uncertainties) != len(values):
            raise ValueError(
                "standard_uncertainties length must match parameter_values length, "
                f"got {len(uncertainties)} and {len(values)}."
            )
        for index, uncertainty in enumerate(uncertainties):
            if uncertainty < 0.0:
                raise ValueError(f"standard_uncertainties[{index}] must be non-negative, got {uncertainty!r}.")
    correlations = None
    if correlation_matrix is not None:
        correlations = _square_matrix(correlation_matrix, "correlation_matrix", expected_size=len(values))
        for row_index, row in enumerate(correlations):
            for column_index, coefficient in enumerate(row):
                if coefficient < -1.0 or coefficient > 1.0:
                    raise ValueError(
                        "correlation_matrix values must be in [-1, 1], "
                        f"got {coefficient!r} at ({row_index}, {column_index})."
                    )
    resolved_bounds = None
    if bounds is not None:
        if len(bounds) != len(values):
            raise ValueError(f"bounds length must match parameter_values length, got {len(bounds)} and {len(values)}.")
        resolved_bounds = tuple(_bound_pair(bound, index) for index, bound in enumerate(bounds))

    reasons_by_index: dict[int, list[str]] = {index: [] for index in range(len(values))}
    evidence_by_index: dict[int, dict[str, Any]] = {index: {} for index in range(len(values))}
    severities: dict[int, Literal["freeze_candidate", "review"]] = {}

    if uncertainties is not None:
        for index, uncertainty in enumerate(uncertainties):
            ratio = uncertainty / max(abs(values[index]), 1.0)
            evidence_by_index[index]["relative_uncertainty"] = ratio
            if ratio >= rel_threshold:
                reasons_by_index[index].append("large_relative_uncertainty")
                severities[index] = "freeze_candidate"

    if resolved_bounds is not None:
        for index, (lower, upper) in enumerate(resolved_bounds):
            if lower is None or upper is None:
                continue
            width = upper - lower
            if width <= 0.0:
                raise ValueError(f"bounds[{index}] upper must be greater than lower.")
            distance = min(abs(values[index] - lower), abs(upper - values[index]))
            fraction = distance / width
            evidence_by_index[index]["nearest_bound_fraction"] = fraction
            if fraction <= bound_fraction:
                reasons_by_index[index].append("near_finite_bound")
                severities.setdefault(index, "review")

    if correlations is not None:
        for left in range(len(values)):
            for right in range(left + 1, len(values)):
                coefficient = correlations[left][right]
                if abs(coefficient) < corr_threshold:
                    continue
                selected = _select_correlated_freeze_candidate(left, right, values, uncertainties)
                other = right if selected == left else left
                reasons_by_index[selected].append(f"high_correlation_with:{labels[other]}")
                evidence_by_index[selected][f"correlation_with:{labels[other]}"] = coefficient
                severities[selected] = "freeze_candidate"

    recommendations = []
    for index in range(len(values)):
        unique_reasons = tuple(sorted(set(reasons_by_index[index])))
        if not unique_reasons:
            continue
        recommendations.append(
            ParameterFreezeRecommendation(
                index=index,
                label=labels[index],
                unit=units[index],
                severity=severities.get(index, "review"),
                reasons=unique_reasons,
                evidence=evidence_by_index[index],
            )
        )
    status: Literal["ok", "recommendations"] = "recommendations" if recommendations else "ok"
    return ParameterFreezeReport(status, tuple(recommendations), labels, units)


def detect_overparameterization(
    *,
    jacobian: Sequence[Sequence[float]] | None = None,
    normal_matrix: Sequence[Sequence[float]] | None = None,
    observation_count: int | None = None,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    rank_tolerance: float = 1.0e-12,
    max_condition_number: float = 1.0e12,
    correlation_matrix: Sequence[Sequence[float]] | None = None,
    high_correlation_threshold: float = 0.98,
) -> OverparameterizationReport:
    """Detect underdetermined or unstable parameterizations.

    Args:
        jacobian: Optional residual-by-parameter Jacobian.
        normal_matrix: Optional square normal matrix. Required when
            ``jacobian`` is not provided.
        observation_count: Optional observation count. Defaults to the Jacobian
            row count when ``jacobian`` is provided.
        parameter_labels: Optional labels. Defaults to ``p0``, ``p1``, and so
            on.
        parameter_units: Optional units. Defaults to ``""``.
        rank_tolerance: Pivot tolerance for rank and inverse diagnostics.
        max_condition_number: Maximum acceptable infinity-norm condition
            estimate.
        correlation_matrix: Optional correlation matrix for high-correlation
            overparameterization flags.
        high_correlation_threshold: Absolute correlation threshold.

    Returns:
        Structured diagnostic report with machine-readable flags.

    Raises:
        ValueError: If input shapes, thresholds, or counts are invalid.
    """
    tolerance = _positive_float(rank_tolerance, "rank_tolerance")
    condition_limit = _positive_float(max_condition_number, "max_condition_number")
    corr_threshold = _bounded_threshold(high_correlation_threshold, "high_correlation_threshold")
    if jacobian is None and normal_matrix is None:
        raise ValueError("Provide jacobian or normal_matrix.")
    rows = None
    if jacobian is not None:
        rows = [_finite_sequence(row, f"jacobian[{index}]") for index, row in enumerate(jacobian)]
        if not rows:
            raise ValueError("jacobian must contain at least one residual row.")
        parameter_count = len(rows[0])
        if parameter_count == 0:
            raise ValueError("jacobian rows must contain at least one parameter column.")
        for row_index, row in enumerate(rows):
            if len(row) != parameter_count:
                raise ValueError(
                    f"jacobian row {row_index} has length {len(row)} but {parameter_count} was expected."
                )
        inferred_observations = len(rows)
        normal = _normal_matrix(rows, parameter_count)
        rank = _matrix_rank(rows, tolerance=tolerance)
    else:
        normal = _square_matrix(normal_matrix, "normal_matrix")
        parameter_count = len(normal)
        if parameter_count == 0:
            raise ValueError("normal_matrix must contain at least one parameter.")
        rank = _matrix_rank(normal, tolerance=tolerance)
        inferred_observations = None

    observations = inferred_observations if observation_count is None else _positive_int(observation_count, "observation_count")
    labels = _resolved_labels(parameter_labels, parameter_count, prefix="p")
    units = _resolved_units(parameter_units, parameter_count)
    condition_number = _condition_number(normal, singular_tolerance=tolerance)
    degrees_of_freedom = None if observations is None else observations - parameter_count
    flags: list[str] = []
    warnings: list[str] = []

    if observations is not None and observations <= parameter_count:
        flags.append("observations_not_greater_than_parameters")
        warnings.append("Observation count does not exceed parameter count; residual degrees of freedom are non-positive.")
    if rank < parameter_count:
        flags.append("rank_deficient")
        warnings.append("Jacobian or normal matrix rank is lower than the parameter count.")
    if condition_number > condition_limit:
        flags.append("ill_conditioned")
        warnings.append("Normal matrix condition estimate exceeds the configured limit.")

    if correlation_matrix is not None:
        correlations = _square_matrix(correlation_matrix, "correlation_matrix", expected_size=parameter_count)
        high_pairs = []
        for left in range(parameter_count):
            for right in range(left + 1, parameter_count):
                coefficient = correlations[left][right]
                if coefficient < -1.0 or coefficient > 1.0:
                    raise ValueError(
                        "correlation_matrix values must be in [-1, 1], "
                        f"got {coefficient!r} at ({left}, {right})."
                    )
                if abs(coefficient) >= corr_threshold:
                    high_pairs.append(f"{labels[left]}:{labels[right]}")
        if high_pairs:
            flags.append("high_parameter_correlation")
            warnings.append("High parameter correlations: " + ", ".join(high_pairs) + ".")

    ordered_flags = tuple(dict.fromkeys(flags))
    if "rank_deficient" in ordered_flags or "observations_not_greater_than_parameters" in ordered_flags:
        status: Literal["ok", "suspect", "overparameterized"] = "overparameterized"
    elif ordered_flags:
        status = "suspect"
    else:
        status = "ok"
    return OverparameterizationReport(
        status=status,
        parameter_count=parameter_count,
        observation_count=observations,
        degrees_of_freedom=degrees_of_freedom,
        rank=rank,
        condition_number=condition_number,
        flags=ordered_flags,
        parameter_labels=labels,
        parameter_units=units,
        warnings=tuple(warnings),
    )


def score_model_selection(
    candidate: ModelSelectionInput,
    *,
    criterion: ModelCriterion = "aicc",
    residual_floor: float = 1.0e-300,
) -> ModelSelectionScore:
    """Score one model with AIC, corrected AIC, or BIC.

    The score uses the Gaussian least-squares profile-likelihood term
    ``n * log(RSS / n)`` and omits constants shared by all compared models.

    Args:
        candidate: Model-selection input record.
        criterion: ``"aic"``, ``"aicc"``, or ``"bic"``.
        residual_floor: Positive RSS floor used only for exact zero objectives.

    Returns:
        Model-selection score with recorded likelihood assumptions.

    Raises:
        ValueError: If the candidate, criterion, or floor is invalid.
    """
    if not isinstance(candidate, ModelSelectionInput):
        raise ValueError("candidate must be a ModelSelectionInput.")
    if criterion not in {"aic", "aicc", "bic"}:
        raise ValueError(f"criterion must be 'aic', 'aicc', or 'bic', got {criterion!r}.")
    floor = _positive_float(residual_floor, "residual_floor")
    rss = 2.0 * candidate.objective_value
    warnings = []
    if rss == 0.0:
        rss = floor
        warnings.append("zero_residual_sum_squares_floor_applied")
    n = candidate.observation_count
    k = candidate.parameter_count
    likelihood_term = n * math.log(rss / n)
    if criterion == "aic":
        score = likelihood_term + 2.0 * k
    elif criterion == "bic":
        score = likelihood_term + k * math.log(n)
    else:
        denominator = n - k - 1
        if denominator <= 0:
            raise ValueError(
                "AICc requires observation_count greater than parameter_count + 1, "
                f"got {n} and {k}."
            )
        score = likelihood_term + 2.0 * k + (2.0 * k * (k + 1.0)) / denominator
    return ModelSelectionScore(
        model_id=candidate.model_id,
        criterion=criterion,
        score=score,
        rank=0,
        objective_value=candidate.objective_value,
        observation_count=n,
        parameter_count=k,
        likelihood_assumption="gaussian_profile_likelihood_from_half_sum_squares_without_constants",
        warnings=tuple(warnings),
    )


def rank_model_selection(
    candidates: Sequence[ModelSelectionInput],
    *,
    criterion: ModelCriterion = "aicc",
    residual_floor: float = 1.0e-300,
) -> tuple[ModelSelectionScore, ...]:
    """Score and rank models by an information criterion.

    Args:
        candidates: Candidate models to score.
        criterion: ``"aic"``, ``"aicc"``, or ``"bic"``.
        residual_floor: Positive RSS floor passed to ``score_model_selection``.

    Returns:
        Scores sorted by score then model id. Lower scores rank first.

    Raises:
        ValueError: If candidates are empty, duplicated, or invalid.
    """
    if not candidates:
        raise ValueError("candidates must contain at least one model.")
    seen = set()
    scores = []
    for candidate in candidates:
        if candidate.model_id in seen:
            raise ValueError(f"duplicate model_id {candidate.model_id!r}.")
        seen.add(candidate.model_id)
        scores.append(score_model_selection(candidate, criterion=criterion, residual_floor=residual_floor))
    ranked = sorted(scores, key=lambda score: (score.score, score.model_id))
    return tuple(
        ModelSelectionScore(
            model_id=score.model_id,
            criterion=score.criterion,
            score=score.score,
            rank=index,
            objective_value=score.objective_value,
            observation_count=score.observation_count,
            parameter_count=score.parameter_count,
            likelihood_assumption=score.likelihood_assumption,
            warnings=score.warnings,
        )
        for index, score in enumerate(ranked, start=1)
    )


def derive_optimizer_seed(base_seed: int, label: str, *, index: int = 0) -> int:
    """Derive a deterministic unsigned 32-bit optimizer seed.

    Args:
        base_seed: Explicit user-controlled base seed in ``[0, 2**32 - 1]``.
        label: Stable run label.
        index: Non-negative run index for repeated labels.

    Returns:
        Derived unsigned 32-bit seed.

    Raises:
        ValueError: If the seed, label, or index is invalid.

    Example:
        >>> derive_optimizer_seed(7, "start", index=0) == derive_optimizer_seed(7, "start", index=0)
        True
    """
    base = _seed_value(base_seed, "base_seed")
    if not isinstance(label, str) or not label:
        raise ValueError("label must be a non-empty string.")
    _non_negative_int(index, "index")
    payload = f"{_SEED_ALGORITHM}|{base}|{index}|{label}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], "big", signed=False)


def create_seed_plan(base_seed: int, labels: Sequence[str]) -> SeedPlan:
    """Create a deterministic seed plan for labeled optimizer runs.

    Args:
        base_seed: Explicit user-controlled base seed in ``[0, 2**32 - 1]``.
        labels: Stable labels for derived seeds. Labels must be unique.

    Returns:
        Seed plan with labels sorted in deterministic output order.

    Raises:
        ValueError: If the seed or labels are invalid.
    """
    base = _seed_value(base_seed, "base_seed")
    if isinstance(labels, str) or not isinstance(labels, Sequence) or not labels:
        raise ValueError("labels must be a non-empty sequence of strings.")
    seen = set()
    seeds: dict[str, int] = {}
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"labels[{index}] must be a non-empty string.")
        if label in seen:
            raise ValueError(f"duplicate seed label {label!r}.")
        seen.add(label)
        seeds[label] = derive_optimizer_seed(base, label, index=index)
    return SeedPlan(base_seed=base, algorithm=_SEED_ALGORITHM, seeds=seeds)


def _optimizer_record(result: Any, index: int) -> tuple[float, tuple[float, ...], str, bool | None]:
    objective = _extract_field(result, "objective_value", index)
    parameters = _extract_field(result, "parameters", index)
    status = _optional_field(result, "status", "unknown")
    converged = _optional_field(result, "converged", None)
    objective_value = _finite_float(objective, f"results[{index}].objective_value")
    parameter_values = tuple(_finite_sequence(parameters, f"results[{index}].parameters"))
    if not parameter_values:
        raise ValueError(f"results[{index}].parameters must contain at least one value.")
    if not isinstance(status, str) or not status:
        raise ValueError(f"results[{index}].status must be a non-empty string when provided.")
    if converged is not None and not isinstance(converged, bool):
        raise ValueError(f"results[{index}].converged must be a boolean when provided.")
    return objective_value, parameter_values, status, converged


def _extract_field(result: Any, field_name: str, index: int) -> Any:
    if isinstance(result, Mapping):
        if field_name not in result:
            raise ValueError(f"results[{index}] is missing {field_name!r}.")
        return result[field_name]
    if not hasattr(result, field_name):
        raise ValueError(f"results[{index}] is missing {field_name!r}.")
    return getattr(result, field_name)


def _optional_field(result: Any, field_name: str, default: Any) -> Any:
    if isinstance(result, Mapping):
        return result.get(field_name, default)
    return getattr(result, field_name, default)


def _select_correlated_freeze_candidate(
    left: int,
    right: int,
    values: Sequence[float],
    uncertainties: Sequence[float] | None,
) -> int:
    if uncertainties is None:
        return right
    left_ratio = uncertainties[left] / max(abs(values[left]), 1.0)
    right_ratio = uncertainties[right] / max(abs(values[right]), 1.0)
    if right_ratio > left_ratio:
        return right
    if left_ratio > right_ratio:
        return left
    return right


def _max_abs_delta(values: Sequence[float], reference: Sequence[float]) -> float:
    if len(values) != len(reference):
        raise ValueError(f"values and reference lengths must match, got {len(values)} and {len(reference)}.")
    return max((abs(value - expected) for value, expected in zip(values, reference, strict=True)), default=0.0)


def _normal_matrix(rows: Sequence[Sequence[float]], parameter_count: int) -> list[list[float]]:
    return [
        [
            sum(row[left] * row[right] for row in rows)
            for right in range(parameter_count)
        ]
        for left in range(parameter_count)
    ]


def _matrix_rank(matrix: Sequence[Sequence[float]], *, tolerance: float) -> int:
    rows = [list(row) for row in matrix]
    if not rows:
        return 0
    row_count = len(rows)
    column_count = len(rows[0])
    rank = 0
    pivot_row = 0
    for column in range(column_count):
        candidate = max(range(pivot_row, row_count), key=lambda row: abs(rows[row][column]), default=pivot_row)
        if pivot_row >= row_count or abs(rows[candidate][column]) <= tolerance:
            continue
        rows[pivot_row], rows[candidate] = rows[candidate], rows[pivot_row]
        pivot = rows[pivot_row][column]
        rows[pivot_row] = [value / pivot for value in rows[pivot_row]]
        for row in range(row_count):
            if row == pivot_row:
                continue
            factor = rows[row][column]
            rows[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(rows[row], rows[pivot_row], strict=True)
            ]
        rank += 1
        pivot_row += 1
        if pivot_row == row_count:
            break
    return rank


def _condition_number(matrix: Sequence[Sequence[float]], *, singular_tolerance: float) -> float:
    inverse = _invert_square_matrix(matrix, singular_tolerance=singular_tolerance)
    if inverse is None:
        return math.inf
    return _infinity_norm(matrix) * _infinity_norm(inverse)


def _invert_square_matrix(matrix: Sequence[Sequence[float]], *, singular_tolerance: float) -> list[list[float]] | None:
    size = len(matrix)
    augmented = [
        list(row) + [1.0 if row_index == column_index else 0.0 for column_index in range(size)]
        for row_index, row in enumerate(matrix)
    ]
    for pivot_column in range(size):
        pivot_row = max(range(pivot_column, size), key=lambda row: abs(augmented[row][pivot_column]))
        if abs(augmented[pivot_row][pivot_column]) <= singular_tolerance:
            return None
        augmented[pivot_column], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_column]
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row_index in range(size):
            if row_index == pivot_column:
                continue
            factor = augmented[row_index][pivot_column]
            augmented[row_index] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row_index], augmented[pivot_column], strict=True)
            ]
    return [row[size:] for row in augmented]


def _infinity_norm(matrix: Sequence[Sequence[float]]) -> float:
    return max((sum(abs(value) for value in row) for row in matrix), default=0.0)


def _resolved_labels(labels: Sequence[str] | None, count: int, *, prefix: str) -> tuple[str, ...]:
    if labels is None:
        return tuple(f"{prefix}_{index}" if prefix == "result" else f"{prefix}{index}" for index in range(count))
    if isinstance(labels, str) or not isinstance(labels, Sequence):
        raise ValueError("labels must be a sequence of strings.")
    if len(labels) != count:
        raise ValueError(f"labels length must be {count}, got {len(labels)}.")
    resolved = []
    seen = set()
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"labels[{index}] must be a non-empty string.")
        if label in seen:
            raise ValueError(f"duplicate label {label!r}.")
        seen.add(label)
        resolved.append(label)
    return tuple(resolved)


def _resolved_units(units: Sequence[str] | None, count: int) -> tuple[str, ...]:
    if units is None:
        return tuple("" for _ in range(count))
    if isinstance(units, str) or not isinstance(units, Sequence):
        raise ValueError("parameter_units must be a sequence of strings.")
    if len(units) != count:
        raise ValueError(f"parameter_units length must be {count}, got {len(units)}.")
    for index, unit in enumerate(units):
        if not isinstance(unit, str):
            raise ValueError(f"parameter_units[{index}] must be a string.")
    return tuple(units)


def _bound_pair(bound: tuple[float | None, float | None], index: int) -> tuple[float | None, float | None]:
    if not isinstance(bound, tuple) or len(bound) != 2:
        raise ValueError(f"bounds[{index}] must be a (lower, upper) tuple.")
    lower = None if bound[0] is None else _finite_float(bound[0], f"bounds[{index}][0]")
    upper = None if bound[1] is None else _finite_float(bound[1], f"bounds[{index}][1]")
    if lower is not None and upper is not None and upper <= lower:
        raise ValueError(f"bounds[{index}] upper must be greater than lower.")
    return lower, upper


def _square_matrix(
    matrix: Sequence[Sequence[float]] | None,
    name: str,
    *,
    expected_size: int | None = None,
) -> list[list[float]]:
    if matrix is None:
        raise ValueError(f"{name} is required.")
    if isinstance(matrix, (str, bytes)) or not isinstance(matrix, Sequence):
        raise ValueError(f"{name} must be a square sequence of finite-number rows.")
    rows = [_finite_sequence(row, f"{name}[{index}]") for index, row in enumerate(matrix)]
    size = len(rows)
    if expected_size is not None and size != expected_size:
        raise ValueError(f"{name} size must be {expected_size}, got {size}.")
    for index, row in enumerate(rows):
        if len(row) != size:
            raise ValueError(f"{name} must be square; row {index} has length {len(row)} instead of {size}.")
    return rows


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    return result


def _positive_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive, got {result!r}.")
    return result


def _non_negative_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative, got {result!r}.")
    return result


def _positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")
    return value


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")
    return value


def _bounded_threshold(value: float, name: str) -> float:
    threshold = _finite_float(value, name)
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {threshold!r}.")
    return threshold


def _seed_value(value: int, name: str) -> int:
    seed = _non_negative_int(value, name)
    if seed > _MAX_SEED:
        raise ValueError(f"{name} must be <= {_MAX_SEED}, got {seed!r}.")
    return seed
