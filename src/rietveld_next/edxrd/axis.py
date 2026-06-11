"""Energy-axis histogram model for EDXRD data."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence


@dataclass(frozen=True)
class EnergyHistogramAxis:
    """Monotonic EDXRD histogram axis in keV.

    Args:
        bin_edges_keV: Histogram bin edges in kiloelectronvolts. At least two
            strictly increasing finite positive values are required.
        channel_start: Detector channel index for the first bin.

    Raises:
        ValueError: If energy edges or channel metadata are invalid.

    Example:
        >>> EnergyHistogramAxis((20.0, 20.5, 21.25)).centers_keV
        (20.25, 20.875)
    """

    bin_edges_keV: tuple[float, ...]
    channel_start: int = 0

    def __post_init__(self) -> None:
        """Validate EDXRD axis values and channel metadata."""
        edges = _finite_float_tuple(self.bin_edges_keV, "bin_edges_keV")
        if len(edges) < 2:
            raise ValueError("bin_edges_keV must contain at least two edges.")
        if any(edge <= 0.0 for edge in edges):
            raise ValueError("bin_edges_keV values must be positive keV values.")
        _require_strictly_increasing(edges, "bin_edges_keV")
        if isinstance(self.channel_start, bool) or not isinstance(self.channel_start, int):
            raise ValueError("channel_start must be an integer channel index.")
        if self.channel_start < 0:
            raise ValueError("channel_start must be non-negative.")
        object.__setattr__(self, "bin_edges_keV", edges)

    @classmethod
    def from_linear_calibration(
        cls,
        *,
        channel_count: int,
        offset_keV: float,
        gain_keV_per_channel: float,
        channel_start: int = 0,
    ) -> EnergyHistogramAxis:
        """Build an energy axis from a linear channel-to-energy calibration.

        The edge convention is:

        ```text
        E_edge(i) = offset_keV + gain_keV_per_channel * (channel_start + i)
        ```

        Args:
            channel_count: Number of histogram bins.
            offset_keV: Energy intercept in keV.
            gain_keV_per_channel: Positive energy increment per channel.
            channel_start: Detector channel index for the first bin.

        Returns:
            Energy histogram axis with ``channel_count + 1`` edges.

        Raises:
            ValueError: If calibration values produce invalid edges.
        """

        if isinstance(channel_count, bool) or not isinstance(channel_count, int):
            raise ValueError("channel_count must be an integer.")
        if channel_count <= 0:
            raise ValueError("channel_count must be positive.")
        if isinstance(channel_start, bool) or not isinstance(channel_start, int):
            raise ValueError("channel_start must be an integer channel index.")
        if channel_start < 0:
            raise ValueError("channel_start must be non-negative.")
        offset = _finite_float(offset_keV, "offset_keV")
        gain = _finite_float(gain_keV_per_channel, "gain_keV_per_channel")
        if gain <= 0.0:
            raise ValueError("gain_keV_per_channel must be positive.")
        edges = tuple(offset + gain * (channel_start + index) for index in range(channel_count + 1))
        return cls(edges, channel_start=channel_start)

    @property
    def centers_keV(self) -> tuple[float, ...]:
        """Return bin centers in keV."""

        return tuple(0.5 * (left + right) for left, right in zip(self.bin_edges_keV, self.bin_edges_keV[1:]))

    @property
    def widths_keV(self) -> tuple[float, ...]:
        """Return bin widths in keV."""

        return tuple(right - left for left, right in zip(self.bin_edges_keV, self.bin_edges_keV[1:]))

    @property
    def bin_count(self) -> int:
        """Return the number of histogram bins."""

        return len(self.bin_edges_keV) - 1

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "axis_type": "energy",
            "units": "keV",
            "channel_start": self.channel_start,
            "bin_edges_keV": list(self.bin_edges_keV),
        }


def _finite_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _require_strictly_increasing(values: tuple[float, ...], name: str) -> None:
    for index, (left, right) in enumerate(zip(values, values[1:])):
        if right <= left:
            raise ValueError(f"{name} must be strictly increasing at index {index + 1}.")
