"""Optimization diagnostic helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class LabeledMatrix:
    """Matrix result with parameter labels, units, status, and warnings.

    Args:
        matrix: Square matrix values, or ``None`` when the calculation is
            singular or otherwise invalid.
        parameter_labels: Stable labels matching matrix rows and columns.
        parameter_units: Units matching ``parameter_labels``. Use ``""`` for
            dimensionless parameters.
        status: ``"ok"`` for usable results, otherwise a structured failure
            label such as ``"singular"``.
        warnings: Human-readable diagnostic warnings.

    Example:
        >>> result = LabeledMatrix([[1.0]], ("scale",), ("dimensionless",))
        >>> result.status
        'ok'
    """

    matrix: list[list[float]] | None
    parameter_labels: tuple[str, ...]
    parameter_units: tuple[str, ...]
    status: str = "ok"
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate labels, units, matrix shape, and status."""
        labels = _label_tuple(self.parameter_labels, "parameter_labels")
        units = _unit_tuple(self.parameter_units, "parameter_units")
        if len(labels) != len(units):
            raise ValueError(
                "parameter_labels and parameter_units must have the same length, "
                f"got {len(labels)} and {len(units)}."
            )
        if self.status not in {"ok", "singular", "invalid"}:
            raise ValueError(f"status must be 'ok', 'singular', or 'invalid', got {self.status!r}.")
        if self.matrix is None:
            if self.status == "ok":
                raise ValueError("matrix is required when status is 'ok'.")
        else:
            _square_matrix(self.matrix, "matrix", expected_size=len(labels))
        for index, warning in enumerate(self.warnings):
            if not isinstance(warning, str) or not warning:
                raise ValueError(f"warnings[{index}] must be a non-empty string.")

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        return {
            "matrix": self.matrix,
            "parameter_labels": list(self.parameter_labels),
            "parameter_units": list(self.parameter_units),
            "status": self.status,
            "warnings": list(self.warnings),
        }


def parameter_error_metrics(parameters: Sequence[float], reference: Sequence[float]) -> dict[str, float]:
    """Compute deterministic absolute-error metrics against a reference vector.

    Args:
        parameters: Estimated parameter vector.
        reference: Reference or synthetic ground-truth vector.

    Returns:
        Mapping with ``max_abs_error`` and ``rms_error``.

    Raises:
        ValueError: If lengths differ or values are non-finite.
    """
    values = _finite_sequence(parameters, "parameters")
    reference_values = _finite_sequence(reference, "reference")
    if len(values) != len(reference_values):
        raise ValueError(f"parameters and reference must have the same length, got {len(values)} and {len(reference_values)}.")
    if not values:
        return {"max_abs_error": 0.0, "rms_error": 0.0}

    errors = [value - expected for value, expected in zip(values, reference_values, strict=True)]
    max_abs_error = max(abs(error) for error in errors)
    rms_error = math.sqrt(sum(error**2 for error in errors) / len(errors))
    return {"max_abs_error": max_abs_error, "rms_error": rms_error}


def covariance_from_jacobian(
    jacobian: Sequence[Sequence[float]],
    *,
    residual_variance: float,
    parameter_labels: Sequence[str],
    parameter_units: Sequence[str] | None = None,
    singular_tolerance: float = 1e-12,
) -> LabeledMatrix:
    """Estimate parameter covariance from a dense residual Jacobian.

    This lightweight helper computes ``residual_variance * inv(J^T J)`` for
    synthetic diagnostics and small validation fixtures. It is not a production
    sparse least-squares covariance engine.

    Args:
        jacobian: Dense residual-by-parameter Jacobian matrix.
        residual_variance: Residual variance scale. Must be finite and
            non-negative.
        parameter_labels: Labels for Jacobian columns and covariance
            rows/columns.
        parameter_units: Units for each parameter. Defaults to dimensionless
            units.
        singular_tolerance: Pivot tolerance for singular normal matrices.

    Returns:
        Labeled covariance matrix result. Singular or underdetermined systems
        return ``status="singular"`` with warnings instead of misleading
        uncertainties.

    Raises:
        ValueError: If input shapes, labels, units, or numeric values are
            invalid.

    Example:
        >>> result = covariance_from_jacobian([[1.0, 0.0], [0.0, 2.0]], residual_variance=4.0, parameter_labels=["a", "b"])
        >>> result.matrix
        [[4.0, 0.0], [0.0, 1.0]]
    """
    rows = [_finite_sequence(row, f"jacobian[{index}]") for index, row in enumerate(jacobian)]
    labels = _label_tuple(parameter_labels, "parameter_labels")
    units = _resolved_units(parameter_units, len(labels))
    variance = _finite_float(residual_variance, "residual_variance")
    tolerance = _finite_float(singular_tolerance, "singular_tolerance")
    if variance < 0.0:
        raise ValueError(f"residual_variance must be non-negative, got {variance!r}.")
    if tolerance <= 0.0:
        raise ValueError(f"singular_tolerance must be positive, got {tolerance!r}.")
    if not labels:
        raise ValueError("parameter_labels must contain at least one label.")
    for row_index, row in enumerate(rows):
        if len(row) != len(labels):
            raise ValueError(
                f"jacobian row {row_index} has length {len(row)} but "
                f"{len(labels)} parameter labels were provided."
            )

    warnings: list[str] = []
    if len(rows) < len(labels):
        warnings.append(
            "Jacobian has fewer residual rows than parameters; covariance is underdetermined."
        )
    normal_matrix = _normal_matrix(rows, len(labels))
    inverse = _invert_square_matrix(normal_matrix, singular_tolerance=tolerance)
    if inverse is None:
        warnings.append("Normal matrix is singular or ill-conditioned within the configured tolerance.")
        return LabeledMatrix(None, labels, units, status="singular", warnings=tuple(warnings))
    covariance = [[variance * value for value in row] for row in inverse]
    return LabeledMatrix(covariance, labels, units, warnings=tuple(warnings))


def correlation_matrix_from_covariance(covariance: Sequence[Sequence[float]]) -> list[list[float]]:
    """Convert a covariance matrix to a correlation matrix.

    Args:
        covariance: Square covariance matrix.

    Returns:
        Correlation matrix with unit diagonal.

    Raises:
        ValueError: If the matrix is non-square, non-finite, or has non-positive
            variance on the diagonal.
    """
    matrix = [_finite_sequence(row, f"covariance[{index}]") for index, row in enumerate(covariance)]
    size = len(matrix)
    for index, row in enumerate(matrix):
        if len(row) != size:
            raise ValueError(f"covariance must be square; row {index} has length {len(row)} instead of {size}.")
    variances = [matrix[index][index] for index in range(size)]
    for index, variance in enumerate(variances):
        if variance <= 0.0:
            raise ValueError(f"covariance diagonal entry {index} must be positive, got {variance!r}.")
    return [
        [
            matrix[row][column] / math.sqrt(variances[row] * variances[column])
            for column in range(size)
        ]
        for row in range(size)
    ]


def labeled_correlation_matrix_from_covariance(
    covariance: Sequence[Sequence[float]],
    *,
    parameter_labels: Sequence[str],
    parameter_units: Sequence[str] | None = None,
) -> LabeledMatrix:
    """Convert covariance to a labeled correlation matrix with diagnostics.

    Args:
        covariance: Square covariance matrix.
        parameter_labels: Labels for covariance rows and columns.
        parameter_units: Units for each parameter. Defaults to dimensionless
            units.

    Returns:
        Labeled correlation matrix. Non-positive variances return
        ``status="singular"`` with warnings rather than raising.

    Raises:
        ValueError: If the covariance shape, labels, units, or numeric values
            are invalid.

    Example:
        >>> result = labeled_correlation_matrix_from_covariance([[4.0, 1.0], [1.0, 9.0]], parameter_labels=["a", "b"])
        >>> round(result.matrix[0][1], 6)
        0.166667
    """
    labels = _label_tuple(parameter_labels, "parameter_labels")
    units = _resolved_units(parameter_units, len(labels))
    matrix = _square_matrix(covariance, "covariance", expected_size=len(labels))
    variances = [matrix[index][index] for index in range(len(matrix))]
    non_positive = [index for index, variance in enumerate(variances) if variance <= 0.0]
    if non_positive:
        warnings = (
            "Covariance has non-positive variance entries at indices "
            f"{', '.join(str(index) for index in non_positive)}."
        )
        return LabeledMatrix(None, labels, units, status="singular", warnings=(warnings,))
    correlation = [
        [
            matrix[row][column] / math.sqrt(variances[row] * variances[column])
            for column in range(len(matrix))
        ]
        for row in range(len(matrix))
    ]
    return LabeledMatrix(correlation, labels, units)


def _normal_matrix(rows: Sequence[Sequence[float]], parameter_count: int) -> list[list[float]]:
    return [
        [
            sum(row[left] * row[right] for row in rows)
            for right in range(parameter_count)
        ]
        for left in range(parameter_count)
    ]


def _invert_square_matrix(matrix: Sequence[Sequence[float]], *, singular_tolerance: float) -> list[list[float]] | None:
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


def _square_matrix(
    values: Sequence[Sequence[float]],
    name: str,
    *,
    expected_size: int | None = None,
) -> list[list[float]]:
    matrix = [_finite_sequence(row, f"{name}[{index}]") for index, row in enumerate(values)]
    size = len(matrix)
    if expected_size is not None and size != expected_size:
        raise ValueError(f"{name} size must match parameter labels; got {size} and {expected_size}.")
    for index, row in enumerate(matrix):
        if len(row) != size:
            raise ValueError(f"{name} must be square; row {index} has length {len(row)} instead of {size}.")
    return matrix


def _label_tuple(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of non-empty strings.")
    labels = tuple(values)
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"{name}[{index}] must be a non-empty string.")
    if len(set(labels)) != len(labels):
        raise ValueError(f"{name} must not contain duplicate labels.")
    return labels


def _unit_tuple(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of strings.")
    units = tuple(values)
    for index, unit in enumerate(units):
        if not isinstance(unit, str):
            raise ValueError(f"{name}[{index}] must be a string.")
    return units


def _resolved_units(values: Sequence[str] | None, size: int) -> tuple[str, ...]:
    if values is None:
        return tuple("dimensionless" for _ in range(size))
    units = _unit_tuple(values, "parameter_units")
    if len(units) != size:
        raise ValueError(f"parameter_units must match parameter_labels length, got {len(units)} and {size}.")
    return units


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
