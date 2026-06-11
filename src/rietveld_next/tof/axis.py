"""Time-of-flight histogram axis model.

The axis model stores bin edges in microseconds and derives centers and widths
deterministically. It deliberately does not assume a single detector bank; the
optional ``bank_id`` is metadata used to bind one axis instance to a specific
bank in multi-bank reductions.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence


@dataclass(frozen=True)
class TimeOfFlightHistogramAxis:
    """Monotonic TOF histogram bin-edge axis.

    Args:
        bin_edges_microseconds: Histogram bin edges in microseconds. At least
            two strictly increasing finite values are required.
        bank_id: Optional detector-bank identifier for multi-bank datasets.

    Raises:
        ValueError: If edges are not finite, positive, or strictly increasing.

    Example:
        >>> TimeOfFlightHistogramAxis((1000.0, 1010.0, 1025.0)).centers_microseconds
        (1005.0, 1017.5)
    """

    bin_edges_microseconds: tuple[float, ...]
    bank_id: str | None = None

    def __post_init__(self) -> None:
        """Validate TOF bin edges and optional bank metadata."""
        edges = _finite_float_tuple(self.bin_edges_microseconds, "bin_edges_microseconds")
        if len(edges) < 2:
            raise ValueError("bin_edges_microseconds must contain at least two edges.")
        if any(edge <= 0.0 for edge in edges):
            raise ValueError("bin_edges_microseconds values must be positive microsecond values.")
        _require_strictly_increasing(edges, "bin_edges_microseconds")
        if self.bank_id is not None and not self.bank_id:
            raise ValueError("bank_id must be non-empty when supplied.")
        object.__setattr__(self, "bin_edges_microseconds", edges)

    @classmethod
    def from_centers(
        cls,
        centers_microseconds: Sequence[float],
        *,
        bin_width_microseconds: float,
        bank_id: str | None = None,
    ) -> TimeOfFlightHistogramAxis:
        """Build a uniformly binned TOF axis from bin centers.

        Args:
            centers_microseconds: Strictly increasing bin centers in
                microseconds.
            bin_width_microseconds: Positive uniform bin width in microseconds.
            bank_id: Optional detector-bank identifier.

        Returns:
            Histogram axis with one more edge than center.

        Raises:
            ValueError: If centers or width are invalid.
        """

        centers = _finite_float_tuple(centers_microseconds, "centers_microseconds")
        if not centers:
            raise ValueError("centers_microseconds must contain at least one center.")
        if any(center <= 0.0 for center in centers):
            raise ValueError("centers_microseconds values must be positive microsecond values.")
        _require_strictly_increasing(centers, "centers_microseconds")
        width = _finite_float(bin_width_microseconds, "bin_width_microseconds")
        if width <= 0.0:
            raise ValueError("bin_width_microseconds must be positive.")

        half_width = 0.5 * width
        edges = [centers[0] - half_width]
        edges.extend(center + half_width for center in centers)
        return cls(tuple(edges), bank_id=bank_id)

    @property
    def centers_microseconds(self) -> tuple[float, ...]:
        """Return bin centers in microseconds."""

        return tuple(
            0.5 * (left + right)
            for left, right in zip(self.bin_edges_microseconds, self.bin_edges_microseconds[1:])
        )

    @property
    def widths_microseconds(self) -> tuple[float, ...]:
        """Return bin widths in microseconds."""

        return tuple(
            right - left
            for left, right in zip(self.bin_edges_microseconds, self.bin_edges_microseconds[1:])
        )

    @property
    def bin_count(self) -> int:
        """Return the number of histogram bins."""

        return len(self.bin_edges_microseconds) - 1

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "axis_type": "tof",
            "units": "microsecond",
            "bin_edges_microseconds": list(self.bin_edges_microseconds),
        }
        if self.bank_id is not None:
            payload["bank_id"] = self.bank_id
        return payload


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
