"""Dependency-free uncertainty diagnostics for small least-squares systems."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Literal

UncertaintyStatus = Literal["ok", "singular", "ill_conditioned"]


@dataclass(frozen=True)
class CovarianceDiagnostics:
    """Structured covariance result with numerical diagnostics.

    Args:
        covariance: Parameter covariance matrix, or ``None`` when the normal
            matrix is singular or too ill-conditioned to report uncertainties.
        standard_uncertainties: Square roots of covariance diagonal entries, or
            ``None`` when ``covariance`` is unavailable.
        normal_matrix: Symmetric normal matrix used for the covariance solve.
        parameter_labels: Stable labels matching matrix rows and columns.
        parameter_units: Units matching ``parameter_labels``. Use ``""`` for
            dimensionless parameters.
        residual_variance: Variance scale applied to the inverse normal matrix.
        condition_number: Infinity-norm condition estimate, or ``math.inf`` for
            singular systems.
        status: ``"ok"`` for usable uncertainties, ``"singular"`` for rank
            failure, or ``"ill_conditioned"`` when the configured condition
            limit is exceeded.
        warnings: Human-readable diagnostic warnings.

    Example:
        >>> result = covariance_from_normal_matrix([[4.0]], parameter_labels=["scale"])
        >>> result.standard_uncertainties
        [0.5]
    """

    covariance: list[list[float]] | None
    standard_uncertainties: list[float] | None
    normal_matrix: list[list[float]]
    parameter_labels: tuple[str, ...]
    parameter_units: tuple[str, ...]
    residual_variance: float
    condition_number: float
    status: UncertaintyStatus = "ok"
    warnings: tuple[str, ...] = ()

    @property
    def matrix(self) -> list[list[float]] | None:
        """Return covariance as a compatibility alias for matrix-like diagnostics."""
        return self.covariance

    def __post_init__(self) -> None:
        """Validate result metadata and matrix consistency."""
        labels = _label_tuple(self.parameter_labels, "parameter_labels")
        units = _unit_tuple(self.parameter_units, "parameter_units")
        if len(labels) != len(units):
            raise ValueError(
                "parameter_labels and parameter_units must have the same "
                f"length, got {len(labels)} and {len(units)}."
            )
        _square_matrix(self.normal_matrix, "normal_matrix", expected_size=len(labels))
        _finite_float(self.residual_variance, "residual_variance")
        _finite_or_infinite_float(self.condition_number, "condition_number")
        if self.status not in {"ok", "singular", "ill_conditioned"}:
            raise ValueError(f"status must be ok, singular, or ill_conditioned, got {self.status!r}.")
        if self.covariance is None:
            if self.status == "ok":
                raise ValueError("covariance is required when status is 'ok'.")
            if self.standard_uncertainties is not None:
                raise ValueError("standard_uncertainties must be None when covariance is None.")
        else:
            _square_matrix(self.covariance, "covariance", expected_size=len(labels))
            if self.standard_uncertainties is None:
                raise ValueError("standard_uncertainties are required when covariance is available.")
            _finite_sequence(self.standard_uncertainties, "standard_uncertainties")
            if len(self.standard_uncertainties) != len(labels):
                raise ValueError(
                    "standard_uncertainties must match parameter_labels length, "
                    f"got {len(self.standard_uncertainties)} and {len(labels)}."
                )
        _warning_tuple(self.warnings)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "covariance": self.covariance,
            "standard_uncertainties": self.standard_uncertainties,
            "normal_matrix": self.normal_matrix,
            "parameter_labels": list(self.parameter_labels),
            "parameter_units": list(self.parameter_units),
            "residual_variance": self.residual_variance,
            "condition_number": self.condition_number,
            "status": self.status,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class HighCorrelation:
    """Pairwise high-correlation diagnostic.

    Args:
        left_index: Row index for the first parameter.
        right_index: Row index for the second parameter.
        left_label: Label for the first parameter.
        right_label: Label for the second parameter.
        coefficient: Correlation coefficient for the parameter pair.
    """

    left_index: int
    right_index: int
    left_label: str
    right_label: str
    coefficient: float

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "left_index": self.left_index,
            "right_index": self.right_index,
            "left_label": self.left_label,
            "right_label": self.right_label,
            "coefficient": self.coefficient,
        }


@dataclass(frozen=True)
class CorrelationDiagnostics:
    """Structured correlation result with pairwise diagnostics.

    Args:
        correlation: Correlation matrix, or ``None`` when covariance variances
            are non-positive.
        parameter_labels: Stable labels matching matrix rows and columns.
        status: ``"ok"`` for usable correlations or ``"singular"`` when
            variances cannot support correlation scaling.
        high_correlations: Off-diagonal pairs whose absolute coefficient meets
            the configured high-correlation threshold.
        warnings: Human-readable diagnostic warnings.
    """

    correlation: list[list[float]] | None
    parameter_labels: tuple[str, ...]
    status: Literal["ok", "singular"] = "ok"
    high_correlations: tuple[HighCorrelation, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate result metadata and matrix consistency."""
        labels = _label_tuple(self.parameter_labels, "parameter_labels")
        if self.status not in {"ok", "singular"}:
            raise ValueError(f"status must be ok or singular, got {self.status!r}.")
        if self.correlation is None:
            if self.status == "ok":
                raise ValueError("correlation is required when status is 'ok'.")
        else:
            _square_matrix(self.correlation, "correlation", expected_size=len(labels))
        for index, pair in enumerate(self.high_correlations):
            if not isinstance(pair, HighCorrelation):
                raise ValueError(f"high_correlations[{index}] must be a HighCorrelation.")
        _warning_tuple(self.warnings)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "correlation": self.correlation,
            "parameter_labels": list(self.parameter_labels),
            "status": self.status,
            "high_correlations": [pair.to_dict() for pair in self.high_correlations],
            "warnings": list(self.warnings),
        }


def covariance_from_jacobian(
    jacobian: Sequence[Sequence[float]],
    *,
    residual_variance: float = 1.0,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    singular_tolerance: float = 1e-12,
    max_condition_number: float = 1e12,
) -> CovarianceDiagnostics:
    """Estimate parameter covariance from a dense residual Jacobian.

    This helper computes ``residual_variance * inv(J^T J)`` with a small
    dependency-free Gauss-Jordan solve. It is intended for deterministic
    synthetic tests and diagnostics, not large production sparse refinements.

    Args:
        jacobian: Dense residual-by-parameter Jacobian matrix.
        residual_variance: Non-negative residual variance scale.
        parameter_labels: Optional labels for Jacobian columns. Defaults to
            ``p0``, ``p1``, and so on.
        parameter_units: Optional units for each parameter. Defaults to ``""``.
        singular_tolerance: Pivot tolerance for singular normal matrices.
        max_condition_number: Maximum acceptable infinity-norm condition
            estimate. Larger values return ``status="ill_conditioned"``.

    Returns:
        Structured covariance diagnostics. Singular or ill-conditioned systems
        return warnings and no covariance matrix.

    Raises:
        ValueError: If shapes, labels, units, tolerances, or numeric values are
            invalid.

    Example:
        >>> result = covariance_from_jacobian([[1.0, 0.0], [0.0, 2.0]])
        >>> result.covariance
        [[1.0, 0.0], [0.0, 0.25]]
    """
    rows = [_finite_sequence(row, f"jacobian[{index}]") for index, row in enumerate(jacobian)]
    parameter_count = _infer_parameter_count(rows, parameter_labels, matrix_name="jacobian")
    labels = _resolved_labels(parameter_labels, parameter_count)
    units = _resolved_units(parameter_units, parameter_count)
    for row_index, row in enumerate(rows):
        if len(row) != parameter_count:
            raise ValueError(
                f"jacobian row {row_index} has length {len(row)} but "
                f"{parameter_count} parameters were expected."
            )

    warnings: list[str] = []
    if len(rows) < parameter_count:
        warnings.append(
            "Jacobian has fewer residual rows than parameters; covariance is underdetermined."
        )
    normal_matrix = _normal_matrix(rows, parameter_count)
    return covariance_from_normal_matrix(
        normal_matrix,
        residual_variance=residual_variance,
        parameter_labels=labels,
        parameter_units=units,
        singular_tolerance=singular_tolerance,
        max_condition_number=max_condition_number,
        additional_warnings=tuple(warnings),
    )


def covariance_from_normal_matrix(
    normal_matrix: Sequence[Sequence[float]],
    *,
    residual_variance: float = 1.0,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    singular_tolerance: float = 1e-12,
    max_condition_number: float = 1e12,
    symmetry_tolerance: float = 1e-12,
    additional_warnings: Sequence[str] = (),
) -> CovarianceDiagnostics:
    """Estimate parameter covariance from a normal matrix.

    Args:
        normal_matrix: Square symmetric normal matrix, usually ``J^T J``.
        residual_variance: Non-negative residual variance scale.
        parameter_labels: Optional labels for rows and columns. Defaults to
            ``p0``, ``p1``, and so on.
        parameter_units: Optional units for each parameter. Defaults to ``""``.
        singular_tolerance: Pivot tolerance for singular matrices.
        max_condition_number: Maximum acceptable infinity-norm condition
            estimate. Larger values return ``status="ill_conditioned"``.
        symmetry_tolerance: Absolute tolerance for symmetry validation.
        additional_warnings: Deterministic warnings from upstream diagnostics.

    Returns:
        Structured covariance diagnostics. Singular or ill-conditioned systems
        return warnings and no covariance matrix.

    Raises:
        ValueError: If shapes, labels, units, tolerances, or numeric values are
            invalid.
    """
    matrix = _square_matrix(normal_matrix, "normal_matrix")
    parameter_count = len(matrix)
    labels = _resolved_labels(parameter_labels, parameter_count)
    units = _resolved_units(parameter_units, parameter_count)
    variance = _finite_float(residual_variance, "residual_variance")
    singular_limit = _positive_float(singular_tolerance, "singular_tolerance")
    condition_limit = _positive_float(max_condition_number, "max_condition_number")
    symmetry_limit = _positive_float(symmetry_tolerance, "symmetry_tolerance")
    if variance < 0.0:
        raise ValueError(f"residual_variance must be non-negative, got {variance!r}.")
    _validate_symmetric(matrix, "normal_matrix", symmetry_limit)
    warnings = list(_warning_tuple(additional_warnings))

    inverse = _invert_square_matrix(matrix, singular_tolerance=singular_limit)
    if inverse is None:
        warnings.append("Normal matrix is singular within the configured pivot tolerance.")
        return CovarianceDiagnostics(
            covariance=None,
            standard_uncertainties=None,
            normal_matrix=matrix,
            parameter_labels=labels,
            parameter_units=units,
            residual_variance=variance,
            condition_number=math.inf,
            status="singular",
            warnings=tuple(warnings),
        )

    condition_number = _infinity_norm(matrix) * _infinity_norm(inverse)
    if condition_number > condition_limit:
        warnings.append(
            "Normal matrix is ill-conditioned; covariance uncertainties are not reported."
        )
        return CovarianceDiagnostics(
            covariance=None,
            standard_uncertainties=None,
            normal_matrix=matrix,
            parameter_labels=labels,
            parameter_units=units,
            residual_variance=variance,
            condition_number=condition_number,
            status="ill_conditioned",
            warnings=tuple(warnings),
        )

    covariance = [[variance * value for value in row] for row in inverse]
    standard_uncertainties = _standard_uncertainties(covariance)
    return CovarianceDiagnostics(
        covariance=covariance,
        standard_uncertainties=standard_uncertainties,
        normal_matrix=matrix,
        parameter_labels=labels,
        parameter_units=units,
        residual_variance=variance,
        condition_number=condition_number,
        warnings=tuple(warnings),
    )


def correlation_from_covariance(
    covariance: Sequence[Sequence[float]],
    *,
    parameter_labels: Sequence[str] | None = None,
    high_correlation_threshold: float = 0.95,
    symmetry_tolerance: float = 1e-12,
) -> CorrelationDiagnostics:
    """Convert covariance to correlation with high-correlation diagnostics.

    Args:
        covariance: Square covariance matrix.
        parameter_labels: Optional labels for rows and columns. Defaults to
            ``p0``, ``p1``, and so on.
        high_correlation_threshold: Absolute off-diagonal coefficient threshold
            for reporting high-correlation pairs. Must be in ``(0, 1]``.
        symmetry_tolerance: Absolute tolerance for covariance symmetry.

    Returns:
        Structured correlation diagnostics. Non-positive covariance variances
        return ``status="singular"`` and no correlation matrix.

    Raises:
        ValueError: If shape, labels, tolerances, threshold, or numeric values
            are invalid.

    Example:
        >>> result = correlation_from_covariance([[4.0, 1.0], [1.0, 9.0]])
        >>> round(result.correlation[0][1], 6)
        0.166667
    """
    matrix = _square_matrix(covariance, "covariance")
    parameter_count = len(matrix)
    labels = _resolved_labels(parameter_labels, parameter_count)
    threshold = _finite_float(high_correlation_threshold, "high_correlation_threshold")
    symmetry_limit = _positive_float(symmetry_tolerance, "symmetry_tolerance")
    if threshold <= 0.0 or threshold > 1.0:
        raise ValueError(
            "high_correlation_threshold must be greater than 0 and less than "
            f"or equal to 1, got {threshold!r}."
        )
    _validate_symmetric(matrix, "covariance", symmetry_limit)

    variances = [matrix[index][index] for index in range(parameter_count)]
    invalid_variance_indices = [
        index for index, variance in enumerate(variances) if variance <= 0.0
    ]
    if invalid_variance_indices:
        joined_indices = ", ".join(str(index) for index in invalid_variance_indices)
        return CorrelationDiagnostics(
            correlation=None,
            parameter_labels=labels,
            status="singular",
            warnings=(
                "Covariance has non-positive variance entries at indices "
                f"{joined_indices}; correlation is not reported.",
            ),
        )

    correlation = [
        [
            _correlation_entry(matrix[row][column], variances[row], variances[column])
            for column in range(parameter_count)
        ]
        for row in range(parameter_count)
    ]
    high_correlations = _high_correlations(correlation, labels, threshold)
    warnings = ()
    if high_correlations:
        warnings = (
            "High absolute parameter correlations meet or exceed "
            f"{threshold:g}; inspect constraints or model identifiability.",
        )
    return CorrelationDiagnostics(
        correlation=correlation,
        parameter_labels=labels,
        high_correlations=high_correlations,
        warnings=warnings,
    )


def _infer_parameter_count(
    rows: Sequence[Sequence[float]],
    parameter_labels: Sequence[str] | None,
    *,
    matrix_name: str,
) -> int:
    if parameter_labels is not None:
        return len(_label_tuple(parameter_labels, "parameter_labels"))
    if not rows:
        raise ValueError(f"{matrix_name} must contain at least one row when parameter_labels are omitted.")
    parameter_count = len(rows[0])
    if parameter_count == 0:
        raise ValueError(f"{matrix_name} must contain at least one parameter column.")
    return parameter_count


def _normal_matrix(rows: Sequence[Sequence[float]], parameter_count: int) -> list[list[float]]:
    return [
        [
            sum(row[left] * row[right] for row in rows)
            for right in range(parameter_count)
        ]
        for left in range(parameter_count)
    ]


def _invert_square_matrix(
    matrix: Sequence[Sequence[float]],
    *,
    singular_tolerance: float,
) -> list[list[float]] | None:
    size = len(matrix)
    augmented = [
        list(row) + [1.0 if row_index == column_index else 0.0 for column_index in range(size)]
        for row_index, row in enumerate(matrix)
    ]

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row_index: abs(augmented[row_index][pivot_column]),
        )
        if abs(augmented[pivot_row][pivot_column]) <= singular_tolerance:
            return None
        if pivot_row != pivot_column:
            augmented[pivot_column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[pivot_column],
            )
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


def _standard_uncertainties(covariance: Sequence[Sequence[float]]) -> list[float]:
    standard_uncertainties: list[float] = []
    for index, row in enumerate(covariance):
        variance = row[index]
        if variance < 0.0:
            raise ValueError(f"covariance diagonal entry {index} is negative, got {variance!r}.")
        standard_uncertainties.append(math.sqrt(variance))
    return standard_uncertainties


def _high_correlations(
    correlation: Sequence[Sequence[float]],
    labels: Sequence[str],
    threshold: float,
) -> tuple[HighCorrelation, ...]:
    pairs: list[HighCorrelation] = []
    for left_index in range(len(correlation)):
        for right_index in range(left_index + 1, len(correlation)):
            coefficient = correlation[left_index][right_index]
            if abs(coefficient) >= threshold:
                pairs.append(
                    HighCorrelation(
                        left_index=left_index,
                        right_index=right_index,
                        left_label=labels[left_index],
                        right_label=labels[right_index],
                        coefficient=coefficient,
                    )
                )
    return tuple(pairs)


def _correlation_entry(covariance: float, left_variance: float, right_variance: float) -> float:
    coefficient = covariance / math.sqrt(left_variance * right_variance)
    if 1.0 < coefficient <= 1.0 + 1e-12:
        return 1.0
    if -1.0 - 1e-12 <= coefficient < -1.0:
        return -1.0
    return coefficient


def _infinity_norm(matrix: Sequence[Sequence[float]]) -> float:
    return max(sum(abs(value) for value in row) for row in matrix)


def _square_matrix(
    matrix: Sequence[Sequence[float]],
    name: str,
    *,
    expected_size: int | None = None,
) -> list[list[float]]:
    if isinstance(matrix, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of numeric rows.")
    try:
        row_items = list(enumerate(matrix))
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of numeric rows.") from exc
    rows = [_finite_sequence(row, f"{name}[{index}]") for index, row in row_items]
    if not rows:
        raise ValueError(f"{name} must contain at least one row.")
    size = len(rows)
    if expected_size is not None and size != expected_size:
        raise ValueError(f"{name} must have {expected_size} rows, got {size}.")
    for row_index, row in enumerate(rows):
        if len(row) != size:
            raise ValueError(f"{name} must be square; row {row_index} has length {len(row)} instead of {size}.")
    return rows


def _validate_symmetric(matrix: Sequence[Sequence[float]], name: str, tolerance: float) -> None:
    for row_index in range(len(matrix)):
        for column_index in range(row_index + 1, len(matrix)):
            left = matrix[row_index][column_index]
            right = matrix[column_index][row_index]
            if abs(left - right) > tolerance:
                raise ValueError(
                    f"{name} must be symmetric; entries ({row_index}, {column_index}) "
                    f"and ({column_index}, {row_index}) differ by {abs(left - right)!r}."
                )


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    try:
        value_items = list(enumerate(values))
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of finite numbers.") from exc
    result = [_finite_float(value, f"{name}[{index}]") for index, value in value_items]
    return result


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    return result


def _finite_or_infinite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric, got {value!r}.")
    result = float(value)
    if math.isnan(result):
        raise ValueError(f"{name} must not be NaN.")
    return result


def _positive_float(value: float, name: str) -> float:
    result = _finite_float(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive, got {result!r}.")
    return result


def _resolved_labels(parameter_labels: Sequence[str] | None, parameter_count: int) -> tuple[str, ...]:
    if parameter_count <= 0:
        raise ValueError(f"parameter_count must be positive, got {parameter_count!r}.")
    if parameter_labels is None:
        return tuple(f"p{index}" for index in range(parameter_count))
    labels = _label_tuple(parameter_labels, "parameter_labels")
    if len(labels) != parameter_count:
        raise ValueError(
            f"parameter_labels must contain {parameter_count} labels, got {len(labels)}."
        )
    return labels


def _label_tuple(labels: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(labels, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of labels, not a string.")
    result: list[str] = []
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"{name}[{index}] must be a non-empty string.")
        result.append(label)
    if not result:
        raise ValueError(f"{name} must contain at least one label.")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicate labels.")
    return tuple(result)


def _resolved_units(parameter_units: Sequence[str] | None, parameter_count: int) -> tuple[str, ...]:
    if parameter_units is None:
        return tuple("" for _ in range(parameter_count))
    units = _unit_tuple(parameter_units, "parameter_units")
    if len(units) != parameter_count:
        raise ValueError(f"parameter_units must contain {parameter_count} units, got {len(units)}.")
    return units


def _unit_tuple(units: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(units, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of units, not a string.")
    result: list[str] = []
    for index, unit in enumerate(units):
        if not isinstance(unit, str):
            raise ValueError(f"{name}[{index}] must be a string.")
        result.append(unit)
    return tuple(result)


def _warning_tuple(warnings: Sequence[str]) -> tuple[str, ...]:
    if isinstance(warnings, (str, bytes)):
        raise ValueError("warnings must be a sequence of strings, not a string.")
    result: list[str] = []
    for index, warning in enumerate(warnings):
        if not isinstance(warning, str) or not warning:
            raise ValueError(f"warnings[{index}] must be a non-empty string.")
        result.append(warning)
    return tuple(result)
