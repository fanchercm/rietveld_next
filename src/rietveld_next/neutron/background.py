"""Container-background helpers for neutron reduced data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ContainerBackgroundModel:
    """Additive neutron container-background model.

    The model stores a tabulated container contribution and evaluates it with
    piecewise-linear interpolation. It is intended for reduced-data plumbing
    and synthetic tests; it is not a container-scattering physics engine.

    Args:
        axis_values: Strictly increasing scattering-axis values.
        intensity_values: Non-negative additive background intensities.
        axis_unit: Unit label for ``axis_values``.
        intensity_unit: Unit label for ``intensity_values``.
        scale: Non-negative dimensionless multiplier.
        source: Non-empty provenance label for the background table.

    Raises:
        ValueError: If lengths, units, scale, axis ordering, or intensities are
            invalid.

    Example:
        >>> model = ContainerBackgroundModel([10.0, 20.0], [2.0, 4.0])
        >>> model.evaluate(15.0)
        3.0
    """

    axis_values: Sequence[float]
    intensity_values: Sequence[float]
    axis_unit: str = "degrees_two_theta"
    intensity_unit: str = "counts"
    scale: float = 1.0
    source: str = "synthetic_container_background"

    def __post_init__(self) -> None:
        """Validate and freeze the tabulated background."""

        axis = _finite_sequence(self.axis_values, "axis_values")
        intensity = _finite_sequence(self.intensity_values, "intensity_values")
        if len(axis) < 2:
            raise ValueError("axis_values must contain at least two points.")
        if len(axis) != len(intensity):
            raise ValueError("axis_values and intensity_values must have the same length.")
        for index in range(1, len(axis)):
            if axis[index] <= axis[index - 1]:
                raise ValueError("axis_values must be strictly increasing.")
        for index, value in enumerate(intensity):
            if value < 0.0:
                raise ValueError(f"intensity_values[{index}] must be non-negative, got {value!r}.")
        scale = _finite_float(self.scale, "scale")
        if scale < 0.0:
            raise ValueError(f"scale must be non-negative, got {scale!r}.")
        object.__setattr__(self, "axis_values", axis)
        object.__setattr__(self, "intensity_values", intensity)
        object.__setattr__(self, "axis_unit", _non_empty_string(self.axis_unit, "axis_unit"))
        object.__setattr__(self, "intensity_unit", _non_empty_string(self.intensity_unit, "intensity_unit"))
        object.__setattr__(self, "scale", scale)
        object.__setattr__(self, "source", _non_empty_string(self.source, "source"))

    def evaluate(self, axis_value: float) -> float:
        """Evaluate the scaled container background at one axis value.

        Args:
            axis_value: Scattering-axis value in ``axis_unit``.

        Returns:
            Additive background intensity in ``intensity_unit``.

        Raises:
            ValueError: If ``axis_value`` is non-finite or outside the table
                domain.
        """

        value = _finite_float(axis_value, "axis_value")
        axis = self.axis_values
        if value < axis[0] or value > axis[-1]:
            raise ValueError(
                f"axis_value must be within the background domain [{axis[0]}, {axis[-1]}] {self.axis_unit}."
            )
        for index in range(1, len(axis)):
            right = axis[index]
            if value <= right:
                left = axis[index - 1]
                left_intensity = self.intensity_values[index - 1]
                right_intensity = self.intensity_values[index]
                fraction = (value - left) / (right - left)
                return self.scale * (left_intensity + fraction * (right_intensity - left_intensity))
        return self.scale * self.intensity_values[-1]

    def evaluate_many(self, axis_values: Sequence[float]) -> tuple[float, ...]:
        """Evaluate the background at multiple axis values."""

        return tuple(self.evaluate(value) for value in _finite_sequence(axis_values, "axis_values"))

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible background metadata."""

        return {
            "model_type": "container_background_linear",
            "axis_values": list(self.axis_values),
            "intensity_values": list(self.intensity_values),
            "axis_unit": self.axis_unit,
            "intensity_unit": self.intensity_unit,
            "scale": self.scale,
            "source": self.source,
        }


def _finite_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()
