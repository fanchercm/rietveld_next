"""Optimization diagnostic helpers."""

from __future__ import annotations

from collections.abc import Sequence
import math


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


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return [_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values)]


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
