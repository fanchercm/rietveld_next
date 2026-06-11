"""Data-series transforms for plotting layers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class PlotSeries:
    """A numeric series ready for a plotting frontend."""

    label: str
    x: tuple[float, ...]
    y: tuple[float, ...]
    x_units: str
    y_units: str

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("PlotSeries.label must be non-empty")
        if not self.x_units:
            raise ValueError("PlotSeries.x_units must be non-empty")
        if not self.y_units:
            raise ValueError("PlotSeries.y_units must be non-empty")
        if len(self.x) != len(self.y):
            raise ValueError("PlotSeries.x and y lengths must match")
        _validate_numeric_sequence("x", self.x)
        _validate_numeric_sequence("y", self.y)


def profile_plot_series(
    x: Sequence[float],
    observed: Sequence[float],
    calculated: Sequence[float] | None = None,
    *,
    x_units: str,
    intensity_units: str,
) -> tuple[PlotSeries, ...]:
    """Build observed and optional calculated profile plot series."""

    x_values = _as_float_tuple("x", x)
    observed_values = _as_float_tuple("observed", observed)
    if len(x_values) != len(observed_values):
        raise ValueError("x and observed lengths must match")

    series = [
        PlotSeries(
            label="observed",
            x=x_values,
            y=observed_values,
            x_units=x_units,
            y_units=intensity_units,
        )
    ]
    if calculated is not None:
        calculated_values = _as_float_tuple("calculated", calculated)
        if len(x_values) != len(calculated_values):
            raise ValueError("x and calculated lengths must match")
        series.append(
            PlotSeries(
                label="calculated",
                x=x_values,
                y=calculated_values,
                x_units=x_units,
                y_units=intensity_units,
            )
        )
    return tuple(series)


def difference_series(
    x: Sequence[float],
    observed: Sequence[float],
    calculated: Sequence[float],
    *,
    x_units: str,
    intensity_units: str,
) -> PlotSeries:
    """Build an unweighted observed-minus-calculated display series."""

    x_values = _as_float_tuple("x", x)
    observed_values = _as_float_tuple("observed", observed)
    calculated_values = _as_float_tuple("calculated", calculated)
    if len(x_values) != len(observed_values) or len(x_values) != len(calculated_values):
        raise ValueError("x, observed, and calculated lengths must match")
    difference = tuple(obs - calc for obs, calc in zip(observed_values, calculated_values))
    return PlotSeries(
        label="difference",
        x=x_values,
        y=difference,
        x_units=x_units,
        y_units=intensity_units,
    )


def _as_float_tuple(name: str, values: Sequence[float]) -> tuple[float, ...]:
    converted = tuple(float(value) for value in values)
    _validate_numeric_sequence(name, converted)
    return converted


def _validate_numeric_sequence(name: str, values: Sequence[float]) -> None:
    if not values:
        raise ValueError(f"{name} must contain at least one value")
    for value in values:
        if not math.isfinite(value):
            raise ValueError(f"{name} values must be finite")
