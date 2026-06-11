"""Parameter scaling and bounded transform helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ParameterScale:
    """Affine parameter scaling metadata.

    Args:
        offset: Physical value corresponding to scaled zero.
        scale: Positive scale factor.
    """

    offset: float = 0.0
    scale: float = 1.0

    def __post_init__(self) -> None:
        """Validate finite affine scaling metadata."""
        _finite_float(self.offset, "offset")
        _positive_float(self.scale, "scale")

    def to_scaled(self, value: float) -> float:
        """Convert a physical value to scaled coordinates."""
        return (_finite_float(value, "value") - self.offset) / self.scale

    def from_scaled(self, value: float) -> float:
        """Convert a scaled value back to physical coordinates."""
        return self.offset + self.scale * _finite_float(value, "value")


@dataclass(frozen=True)
class BoundTransform:
    """Smooth transform between unconstrained and bounded coordinates.

    Args:
        lower: Optional lower physical bound.
        upper: Optional upper physical bound.

    Raises:
        ValueError: If both bounds are present and ``lower >= upper``.
    """

    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        """Validate finite bound metadata."""
        if self.lower is not None:
            _finite_float(self.lower, "lower")
        if self.upper is not None:
            _finite_float(self.upper, "upper")
        if self.lower is not None and self.upper is not None and self.lower >= self.upper:
            raise ValueError("lower must be less than upper.")

    def to_unbounded(self, value: float) -> float:
        """Map a bounded physical value into unconstrained coordinates.

        Raises:
            ValueError: If ``value`` is outside the transform bounds.
        """
        physical = _finite_float(value, "value")
        self.validate_value(physical)
        if self.lower is None and self.upper is None:
            return physical
        if self.lower is not None and self.upper is not None:
            fraction = (physical - self.lower) / (self.upper - self.lower)
            if fraction <= 0.0 or fraction >= 1.0:
                raise ValueError("value must be strictly inside finite bounds for logistic inverse.")
            return math.log(fraction / (1.0 - fraction))
        if self.lower is not None:
            if physical <= self.lower:
                raise ValueError("value must be strictly greater than the lower bound for lower-bound inverse.")
            return math.log(physical - self.lower)
        if self.upper is not None:
            if physical >= self.upper:
                raise ValueError("value must be strictly less than the upper bound for upper-bound inverse.")
            return math.log(self.upper - physical)
        raise AssertionError("unreachable transform state")

    def from_unbounded(self, value: float) -> float:
        """Map unconstrained coordinates into bounded physical coordinates."""
        unbounded = _finite_float(value, "value")
        if self.lower is None and self.upper is None:
            return unbounded
        if self.lower is not None and self.upper is not None:
            if unbounded >= 0.0:
                exp_negative = math.exp(-unbounded)
                fraction = 1.0 / (1.0 + exp_negative)
            else:
                exp_positive = math.exp(unbounded)
                fraction = exp_positive / (1.0 + exp_positive)
            return self.lower + (self.upper - self.lower) * fraction
        if self.lower is not None:
            return self.lower + math.exp(unbounded)
        if self.upper is not None:
            return self.upper - math.exp(unbounded)
        raise AssertionError("unreachable transform state")

    def validate_value(self, value: float) -> None:
        """Validate that a physical value is within inclusive bounds."""
        physical = _finite_float(value, "value")
        if self.lower is not None and physical < self.lower:
            raise ValueError(f"value must be greater than or equal to lower bound {self.lower!r}.")
        if self.upper is not None and physical > self.upper:
            raise ValueError(f"value must be less than or equal to upper bound {self.upper!r}.")


def scale_parameters(values: Sequence[float], scales: Sequence[ParameterScale]) -> list[float]:
    """Scale a parameter vector with per-parameter affine scales."""
    value_list = _finite_sequence(values, "values")
    scale_list = _scale_sequence(scales)
    if len(value_list) != len(scale_list):
        raise ValueError(f"values and scales must have the same length, got {len(value_list)} and {len(scale_list)}.")
    return [scale.to_scaled(value) for value, scale in zip(value_list, scale_list, strict=True)]


def unscale_parameters(values: Sequence[float], scales: Sequence[ParameterScale]) -> list[float]:
    """Unscale a parameter vector with per-parameter affine scales."""
    value_list = _finite_sequence(values, "values")
    scale_list = _scale_sequence(scales)
    if len(value_list) != len(scale_list):
        raise ValueError(f"values and scales must have the same length, got {len(value_list)} and {len(scale_list)}.")
    return [scale.from_scaled(value) for value, scale in zip(value_list, scale_list, strict=True)]


def _scale_sequence(scales: Sequence[ParameterScale]) -> list[ParameterScale]:
    if isinstance(scales, str) or not isinstance(scales, Sequence):
        raise ValueError("scales must be a sequence of ParameterScale values.")
    scale_list = list(scales)
    for index, scale in enumerate(scale_list):
        if not isinstance(scale, ParameterScale):
            raise ValueError(f"scales[{index}] must be a ParameterScale.")
    return scale_list


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
