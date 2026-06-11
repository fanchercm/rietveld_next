"""Dependency-free Jacobian helpers for deterministic refinement tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import math


ResidualFunction = Callable[[Sequence[float]], Sequence[float]]
DenseMatrix = Sequence[Sequence[float]]
Bounds = Sequence[tuple[float | None, float | None] | None]


@dataclass(frozen=True)
class SparseJacobianEntry:
    """Single non-zero Jacobian entry in coordinate-list form.

    Args:
        row: Zero-based residual row index.
        column: Zero-based parameter column index.
        value: Finite derivative value.

    Raises:
        ValueError: If indices are negative or the value is non-finite.
    """

    row: int
    column: int
    value: float

    def __post_init__(self) -> None:
        """Validate entry indices and derivative value."""
        _non_negative_int(self.row, "row")
        _non_negative_int(self.column, "column")
        _finite_float(self.value, "value")


@dataclass(frozen=True)
class SparseJacobian:
    """Small dependency-free sparse residual Jacobian.

    The matrix uses deterministic coordinate-list storage sorted by
    ``(row, column)``. Rows represent residuals, columns represent parameters,
    and values use residual units divided by parameter units.

    Args:
        row_count: Number of residual rows.
        column_count: Number of parameter columns.
        entries: Non-zero entries in any order. Duplicate coordinates are
            summed deterministically.
        parameter_labels: Optional stable labels for columns.
        parameter_units: Optional units for columns. Defaults to
            ``"dimensionless"`` for every parameter.

    Raises:
        ValueError: If shape, metadata, or entries are invalid.

    Example:
        >>> jacobian = SparseJacobian(2, 2, [SparseJacobianEntry(0, 1, 3.0)])
        >>> jacobian.to_dense()
        [[0.0, 3.0], [0.0, 0.0]]
    """

    row_count: int
    column_count: int
    entries: tuple[SparseJacobianEntry, ...] = ()
    parameter_labels: tuple[str, ...] = ()
    parameter_units: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate shape, metadata, and entry coordinates."""
        _non_negative_int(self.row_count, "row_count")
        _non_negative_int(self.column_count, "column_count")
        labels = _labels_or_default(self.parameter_labels, self.column_count)
        units = _units_or_default(self.parameter_units, self.column_count)
        merged: dict[tuple[int, int], float] = {}
        for index, entry in enumerate(self.entries):
            if not isinstance(entry, SparseJacobianEntry):
                raise ValueError(f"entries[{index}] must be a SparseJacobianEntry.")
            if entry.row >= self.row_count:
                raise ValueError(f"entries[{index}].row {entry.row} is outside row_count {self.row_count}.")
            if entry.column >= self.column_count:
                raise ValueError(
                    f"entries[{index}].column {entry.column} is outside column_count {self.column_count}."
                )
            coordinate = (entry.row, entry.column)
            merged[coordinate] = merged.get(coordinate, 0.0) + entry.value
        normalized = tuple(
            SparseJacobianEntry(row, column, value)
            for (row, column), value in sorted(merged.items())
            if value != 0.0
        )
        object.__setattr__(self, "entries", normalized)
        object.__setattr__(self, "parameter_labels", labels)
        object.__setattr__(self, "parameter_units", units)

    @classmethod
    def from_dense(
        cls,
        values: DenseMatrix,
        *,
        parameter_labels: Sequence[str] | None = None,
        parameter_units: Sequence[str] | None = None,
        zero_tolerance: float = 0.0,
    ) -> "SparseJacobian":
        """Create a sparse Jacobian from a dense residual-by-parameter matrix.

        Args:
            values: Dense matrix of derivative values.
            parameter_labels: Optional column labels.
            parameter_units: Optional column units.
            zero_tolerance: Non-negative absolute threshold for dropping small
                values.

        Returns:
            Sparse Jacobian with deterministic coordinate ordering.

        Raises:
            ValueError: If the dense matrix is ragged or contains non-finite
                values.
        """
        tolerance = _non_negative_float(zero_tolerance, "zero_tolerance")
        rows = _finite_matrix(values, "values")
        column_count = len(rows[0]) if rows else _metadata_size(parameter_labels, parameter_units)
        entries = [
            SparseJacobianEntry(row_index, column_index, value)
            for row_index, row in enumerate(rows)
            for column_index, value in enumerate(row)
            if abs(value) > tolerance
        ]
        return cls(
            len(rows),
            column_count,
            tuple(entries),
            parameter_labels=_labels_or_default(parameter_labels, column_count),
            parameter_units=_units_or_default(parameter_units, column_count),
        )

    def to_dense(self) -> list[list[float]]:
        """Return a dense residual-by-parameter matrix."""
        dense = [[0.0 for _ in range(self.column_count)] for _ in range(self.row_count)]
        for entry in self.entries:
            dense[entry.row][entry.column] = entry.value
        return dense

    def column(self, index: int) -> tuple[float, ...]:
        """Return one dense Jacobian column.

        Args:
            index: Zero-based column index.

        Returns:
            Dense derivative column.

        Raises:
            ValueError: If the index is outside the matrix shape.
        """
        _column_index(index, self.column_count)
        values = [0.0 for _ in range(self.row_count)]
        for entry in self.entries:
            if entry.column == index:
                values[entry.row] = entry.value
        return tuple(values)


@dataclass(frozen=True)
class GradientCheckResult:
    """Result from comparing analytic and finite-difference Jacobians.

    Args:
        passed: Whether all entries satisfy the configured tolerances.
        max_abs_error: Maximum absolute entry error.
        max_relative_error: Maximum scale-aware relative entry error.
        absolute_tolerance: Absolute tolerance used for the check.
        relative_tolerance: Relative tolerance used for the check.
        row_count: Number of residual rows compared.
        column_count: Number of parameter columns compared.
        failures: Human-readable mismatch diagnostics in deterministic order.
    """

    passed: bool
    max_abs_error: float
    max_relative_error: float
    absolute_tolerance: float
    relative_tolerance: float
    row_count: int
    column_count: int
    failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate result fields."""
        _finite_float(self.max_abs_error, "max_abs_error")
        _finite_float(self.max_relative_error, "max_relative_error")
        _non_negative_float(self.absolute_tolerance, "absolute_tolerance")
        _non_negative_float(self.relative_tolerance, "relative_tolerance")
        _non_negative_int(self.row_count, "row_count")
        _non_negative_int(self.column_count, "column_count")
        for index, failure in enumerate(self.failures):
            if not isinstance(failure, str) or not failure:
                raise ValueError(f"failures[{index}] must be a non-empty string.")


def finite_difference_jacobian(
    residual_function: ResidualFunction,
    parameters: Sequence[float],
    *,
    step_size: float = 1.0e-6,
    method: str = "central",
    bounds: Bounds | None = None,
    parameter_labels: Sequence[str] | None = None,
    parameter_units: Sequence[str] | None = None,
    zero_tolerance: float = 0.0,
) -> SparseJacobian:
    """Approximate a residual Jacobian by finite differences.

    Args:
        residual_function: Callable that maps a parameter vector to residuals.
        parameters: Parameter vector in physical units.
        step_size: Positive finite-difference step in parameter units.
        method: ``"central"`` or ``"forward"``.
        bounds: Optional inclusive lower/upper bounds for each parameter. Use
            ``None`` for an unbounded side.
        parameter_labels: Optional stable parameter labels.
        parameter_units: Optional parameter units.
        zero_tolerance: Non-negative absolute threshold for dropping small
            derivative entries.

    Returns:
        Sparse residual Jacobian with derivative units of residual per
        parameter unit.

    Raises:
        ValueError: If inputs are invalid, bounds are violated, or residual
            evaluations are malformed.
    """
    if not callable(residual_function):
        raise ValueError("residual_function must be callable.")
    parameter_values = tuple(_finite_sequence(parameters, "parameters"))
    step = _positive_float(step_size, "step_size")
    tolerance = _non_negative_float(zero_tolerance, "zero_tolerance")
    if method not in {"central", "forward"}:
        raise ValueError(f"method must be 'central' or 'forward', got {method!r}.")
    bound_values = _bounds_or_default(bounds, len(parameter_values))
    _validate_within_bounds(parameter_values, bound_values, "parameters")
    labels = _labels_or_default(parameter_labels, len(parameter_values))
    units = _units_or_default(parameter_units, len(parameter_values))

    base_residuals = _evaluate_residuals(residual_function, parameter_values, "residual_function(parameters)")
    rows = len(base_residuals)
    dense = [[0.0 for _ in parameter_values] for _ in base_residuals]
    for column, value in enumerate(parameter_values):
        lower, upper = bound_values[column]
        if method == "central" and _inside_optional_bounds(value - step, lower, upper):
            plus = _replace(parameter_values, column, value + step)
            minus = _replace(parameter_values, column, value - step)
            if _inside_optional_bounds(plus[column], lower, upper):
                plus_residuals = _evaluate_residuals(residual_function, plus, f"residual_function(parameters + e{column})")
                minus_residuals = _evaluate_residuals(
                    residual_function,
                    minus,
                    f"residual_function(parameters - e{column})",
                    expected_size=rows,
                )
                denominator = 2.0 * step
            else:
                plus_residuals, minus_residuals, denominator = _forward_column(
                    residual_function, parameter_values, base_residuals, column, step, lower, upper
                )
        else:
            plus_residuals, minus_residuals, denominator = _forward_column(
                residual_function, parameter_values, base_residuals, column, step, lower, upper
            )
        if len(plus_residuals) != rows:
            raise ValueError(f"residual_function changed residual length for parameter {column}.")
        if len(minus_residuals) != rows:
            raise ValueError(f"residual_function changed residual length for parameter {column}.")
        for row in range(rows):
            dense[row][column] = (plus_residuals[row] - minus_residuals[row]) / denominator

    return SparseJacobian.from_dense(
        dense,
        parameter_labels=labels,
        parameter_units=units,
        zero_tolerance=tolerance,
    )


def scale_residual_derivative(
    unscaled_calculated: Sequence[float],
    *,
    sigma: Sequence[float] | None = None,
) -> tuple[float, ...]:
    """Return analytic residual derivatives for a multiplicative scale.

    The assumed model is ``calculated_i = scale * unscaled_calculated_i`` and
    the residual convention is ``observed - calculated``. With uncertainties,
    the weighted residual derivative is divided by ``sigma_i``.

    Args:
        unscaled_calculated: Calculated intensities before scale is applied.
        sigma: Optional positive intensity uncertainty for each residual.

    Returns:
        Derivative column ``dr_i / dscale`` in deterministic residual order.

    Raises:
        ValueError: If inputs are non-finite, length-mismatched, or sigma values
            are non-positive.
    """
    values = _finite_sequence(unscaled_calculated, "unscaled_calculated")
    weights = _sigma_or_ones(sigma, len(values))
    return tuple(-value / weight for value, weight in zip(values, weights, strict=True))


def polynomial_background_residual_jacobian(
    x_values: Sequence[float],
    degree: int,
    *,
    sigma: Sequence[float] | None = None,
    x_origin: float = 0.0,
    x_scale: float = 1.0,
    parameter_prefix: str = "background_c",
) -> SparseJacobian:
    """Return analytic residual derivatives for polynomial background terms.

    The assumed background is ``sum(c_k * z_i**k)`` with
    ``z_i = (x_i - x_origin) / x_scale``. Residuals use the
    ``observed - calculated`` convention, so each derivative is negative.
    ``x_values``, ``x_origin``, and ``x_scale`` must use compatible axis units.

    Args:
        x_values: Diffraction axis values.
        degree: Non-negative polynomial degree.
        sigma: Optional positive intensity uncertainty for each residual.
        x_origin: Axis origin used for stable polynomial coordinates.
        x_scale: Positive axis scale used for stable polynomial coordinates.
        parameter_prefix: Prefix for generated coefficient labels.

    Returns:
        Sparse Jacobian with one column per coefficient.

    Raises:
        ValueError: If inputs are invalid or uncertainties are non-positive.
    """
    x_axis = _finite_sequence(x_values, "x_values")
    if isinstance(degree, bool) or not isinstance(degree, int) or degree < 0:
        raise ValueError(f"degree must be a non-negative integer, got {degree!r}.")
    origin = _finite_float(x_origin, "x_origin")
    scale = _positive_float(x_scale, "x_scale")
    if not isinstance(parameter_prefix, str) or not parameter_prefix:
        raise ValueError("parameter_prefix must be a non-empty string.")
    weights = _sigma_or_ones(sigma, len(x_axis))
    dense: list[list[float]] = []
    for value, weight in zip(x_axis, weights, strict=True):
        coordinate = (value - origin) / scale
        row = [-(coordinate**power) / weight for power in range(degree + 1)]
        dense.append(row)
    return SparseJacobian.from_dense(
        dense,
        parameter_labels=tuple(f"{parameter_prefix}{index}" for index in range(degree + 1)),
        parameter_units=tuple("intensity" for _ in range(degree + 1)),
    )


def gradient_check(
    residual_function: ResidualFunction,
    parameters: Sequence[float],
    analytic_jacobian: SparseJacobian | DenseMatrix,
    *,
    step_size: float = 1.0e-6,
    absolute_tolerance: float = 1.0e-6,
    relative_tolerance: float = 1.0e-6,
    bounds: Bounds | None = None,
) -> GradientCheckResult:
    """Compare an analytic residual Jacobian to finite differences.

    Args:
        residual_function: Callable that maps parameters to residuals.
        parameters: Parameter vector in physical units.
        analytic_jacobian: Analytic sparse or dense Jacobian.
        step_size: Positive finite-difference step.
        absolute_tolerance: Non-negative absolute tolerance.
        relative_tolerance: Non-negative scale-aware relative tolerance.
        bounds: Optional inclusive lower/upper parameter bounds.

    Returns:
        Deterministic pass/fail result with maximum mismatch diagnostics.

    Raises:
        ValueError: If inputs are invalid or Jacobian shapes differ.
    """
    absolute = _non_negative_float(absolute_tolerance, "absolute_tolerance")
    relative = _non_negative_float(relative_tolerance, "relative_tolerance")
    analytic = analytic_jacobian if isinstance(analytic_jacobian, SparseJacobian) else SparseJacobian.from_dense(analytic_jacobian)
    finite = finite_difference_jacobian(
        residual_function,
        parameters,
        step_size=step_size,
        bounds=bounds,
        parameter_labels=analytic.parameter_labels,
        parameter_units=analytic.parameter_units,
    )
    if analytic.row_count != finite.row_count or analytic.column_count != finite.column_count:
        raise ValueError(
            "analytic_jacobian shape must match finite-difference shape, "
            f"got {analytic.row_count}x{analytic.column_count} and {finite.row_count}x{finite.column_count}."
        )
    analytic_dense = analytic.to_dense()
    finite_dense = finite.to_dense()
    failures: list[str] = []
    max_abs_error = 0.0
    max_relative_error = 0.0
    for row in range(analytic.row_count):
        for column in range(analytic.column_count):
            expected = finite_dense[row][column]
            actual = analytic_dense[row][column]
            abs_error = abs(actual - expected)
            scale = max(1.0, abs(actual), abs(expected))
            relative_error = abs_error / scale
            max_abs_error = max(max_abs_error, abs_error)
            max_relative_error = max(max_relative_error, relative_error)
            if abs_error > absolute and relative_error > relative:
                failures.append(
                    f"row {row}, column {column}: analytic {actual!r}, finite_difference {expected!r}, "
                    f"abs_error {abs_error!r}, relative_error {relative_error!r}"
                )
    return GradientCheckResult(
        passed=not failures,
        max_abs_error=max_abs_error,
        max_relative_error=max_relative_error,
        absolute_tolerance=absolute,
        relative_tolerance=relative,
        row_count=analytic.row_count,
        column_count=analytic.column_count,
        failures=tuple(failures),
    )


def _forward_column(
    residual_function: ResidualFunction,
    parameters: tuple[float, ...],
    base_residuals: tuple[float, ...],
    column: int,
    step: float,
    lower: float | None,
    upper: float | None,
) -> tuple[tuple[float, ...], tuple[float, ...], float]:
    value = parameters[column]
    if _inside_optional_bounds(value + step, lower, upper):
        plus = _replace(parameters, column, value + step)
        return (
            _evaluate_residuals(residual_function, plus, f"residual_function(parameters + e{column})"),
            base_residuals,
            step,
        )
    if _inside_optional_bounds(value - step, lower, upper):
        minus = _replace(parameters, column, value - step)
        return (
            base_residuals,
            _evaluate_residuals(residual_function, minus, f"residual_function(parameters - e{column})"),
            step,
        )
    raise ValueError(f"finite-difference step for parameter {column} violates both bounds.")


def _evaluate_residuals(
    residual_function: ResidualFunction,
    parameters: tuple[float, ...],
    name: str,
    *,
    expected_size: int | None = None,
) -> tuple[float, ...]:
    residuals = tuple(_finite_sequence(residual_function(parameters), name))
    if expected_size is not None and len(residuals) != expected_size:
        raise ValueError(f"{name} returned {len(residuals)} residuals; expected {expected_size}.")
    return residuals


def _replace(values: tuple[float, ...], index: int, value: float) -> tuple[float, ...]:
    result = list(values)
    result[index] = value
    return tuple(result)


def _finite_matrix(values: DenseMatrix, name: str) -> list[list[float]]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numeric rows.")
    rows = [_finite_sequence(row, f"{name}[{index}]") for index, row in enumerate(values)]
    if not rows:
        return rows
    column_count = len(rows[0])
    for index, row in enumerate(rows):
        if len(row) != column_count:
            raise ValueError(f"{name} must be rectangular; row {index} has length {len(row)} instead of {column_count}.")
    return rows


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


def _non_negative_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative, got {number!r}.")
    return number


def _non_negative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")
    return value


def _column_index(value: int, column_count: int) -> int:
    _non_negative_int(value, "index")
    if value >= column_count:
        raise ValueError(f"index {value} is outside column_count {column_count}.")
    return value


def _labels_or_default(values: Sequence[str] | None, size: int) -> tuple[str, ...]:
    if values is None:
        return tuple(f"p{index}" for index in range(size))
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("parameter_labels must be a sequence of non-empty strings.")
    if len(values) == 0:
        return tuple(f"p{index}" for index in range(size))
    labels = tuple(values)
    if len(labels) != size:
        raise ValueError(f"parameter_labels length must be {size}, got {len(labels)}.")
    for index, label in enumerate(labels):
        if not isinstance(label, str) or not label:
            raise ValueError(f"parameter_labels[{index}] must be a non-empty string.")
    if len(set(labels)) != len(labels):
        raise ValueError("parameter_labels must not contain duplicates.")
    return labels


def _units_or_default(values: Sequence[str] | None, size: int) -> tuple[str, ...]:
    if values is None:
        return tuple("dimensionless" for _ in range(size))
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("parameter_units must be a sequence of strings.")
    if len(values) == 0:
        return tuple("dimensionless" for _ in range(size))
    units = tuple(values)
    if len(units) != size:
        raise ValueError(f"parameter_units length must be {size}, got {len(units)}.")
    for index, unit in enumerate(units):
        if not isinstance(unit, str):
            raise ValueError(f"parameter_units[{index}] must be a string.")
    return units


def _metadata_size(labels: Sequence[str] | None, units: Sequence[str] | None) -> int:
    if labels is not None and (isinstance(labels, str) or not isinstance(labels, Sequence)):
        raise ValueError("parameter_labels must be a sequence of non-empty strings.")
    if units is not None and (isinstance(units, str) or not isinstance(units, Sequence)):
        raise ValueError("parameter_units must be a sequence of strings.")
    sizes = [len(values) for values in (labels, units) if values is not None]
    if not sizes:
        return 0
    if len(set(sizes)) != 1:
        raise ValueError("parameter_labels and parameter_units must have the same length for an empty matrix.")
    return sizes[0]


def _bounds_or_default(bounds: Bounds | None, size: int) -> tuple[tuple[float | None, float | None], ...]:
    if bounds is None:
        return tuple((None, None) for _ in range(size))
    if isinstance(bounds, str) or not isinstance(bounds, Sequence):
        raise ValueError("bounds must be a sequence of (lower, upper) pairs or None values.")
    if len(bounds) != size:
        raise ValueError(f"bounds length must match parameters length, got {len(bounds)} and {size}.")
    normalized: list[tuple[float | None, float | None]] = []
    for index, bound in enumerate(bounds):
        if bound is None:
            normalized.append((None, None))
            continue
        if not isinstance(bound, tuple) or len(bound) != 2:
            raise ValueError(f"bounds[{index}] must be a (lower, upper) tuple or None.")
        lower = None if bound[0] is None else _finite_float(bound[0], f"bounds[{index}][0]")
        upper = None if bound[1] is None else _finite_float(bound[1], f"bounds[{index}][1]")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError(f"bounds[{index}] lower must be <= upper.")
        normalized.append((lower, upper))
    return tuple(normalized)


def _validate_within_bounds(
    parameters: tuple[float, ...],
    bounds: tuple[tuple[float | None, float | None], ...],
    name: str,
) -> None:
    for index, (value, (lower, upper)) in enumerate(zip(parameters, bounds, strict=True)):
        if not _inside_optional_bounds(value, lower, upper):
            raise ValueError(f"{name}[{index}]={value!r} is outside bounds ({lower!r}, {upper!r}).")


def _inside_optional_bounds(value: float, lower: float | None, upper: float | None) -> bool:
    if lower is not None and value < lower:
        return False
    if upper is not None and value > upper:
        return False
    return True


def _sigma_or_ones(sigma: Sequence[float] | None, size: int) -> tuple[float, ...]:
    if sigma is None:
        return tuple(1.0 for _ in range(size))
    values = tuple(_finite_sequence(sigma, "sigma"))
    if len(values) != size:
        raise ValueError(f"sigma length must be {size}, got {len(values)}.")
    for index, value in enumerate(values):
        if value <= 0.0:
            raise ValueError(f"sigma[{index}] must be positive, got {value!r}.")
    return values
