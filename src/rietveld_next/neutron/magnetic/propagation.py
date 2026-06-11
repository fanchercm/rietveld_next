"""Magnetic propagation vector entity with explicit reciprocal-space units."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class PropagationVector:
    """Magnetic propagation vector in reciprocal lattice units.

    The components use the reciprocal-lattice fractional convention:

    ```text
    k = h a* + k b* + l c*
    ```

    Args:
        vector_id: Stable propagation-vector identifier, such as ``k1``.
        components_rlu: Three components in reciprocal lattice units.
        coordinate_frame: Coordinate convention for the components. The initial
            supported value is ``reciprocal_lattice_fractional``.

    Raises:
        ValueError: If the identifier, vector shape, finite values, or
            coordinate frame are invalid.

    Example:
        >>> PropagationVector("k1", (0.5, 0.0, 0.0)).phase_turns((1.0, 0.0, 0.0))
        0.5
    """

    vector_id: str
    components_rlu: tuple[float, float, float]
    coordinate_frame: str = "reciprocal_lattice_fractional"

    SUPPORTED_FRAMES = frozenset({"reciprocal_lattice_fractional"})

    def __post_init__(self) -> None:
        """Validate vector identity, reciprocal-space components, and frame."""
        if not isinstance(self.vector_id, str) or not self.vector_id:
            raise ValueError("vector_id must be a non-empty string.")
        components = _three_finite_components(self.components_rlu, "components_rlu")
        if self.coordinate_frame not in self.SUPPORTED_FRAMES:
            allowed = ", ".join(sorted(self.SUPPORTED_FRAMES))
            raise ValueError(f"coordinate_frame must be one of: {allowed}.")
        object.__setattr__(self, "components_rlu", components)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PropagationVector:
        """Create a propagation vector from a JSON-compatible mapping.

        Args:
            data: Mapping produced by :meth:`to_dict`.

        Returns:
            Propagation vector instance.

        Raises:
            ValueError: If required keys or values are invalid.
        """

        if not isinstance(data, dict):
            raise ValueError("PropagationVector payload must be an object.")
        missing = [key for key in ("vector_id", "components_rlu") if key not in data]
        if missing:
            raise ValueError(
                f"PropagationVector payload is missing required key(s): {', '.join(missing)}."
            )
        return cls(
            vector_id=data["vector_id"],
            components_rlu=data["components_rlu"],
            coordinate_frame=data.get("coordinate_frame", "reciprocal_lattice_fractional"),
        )

    def phase_turns(self, fractional_position: Sequence[float]) -> float:
        """Return ``k dot r`` in turns for a fractional direct-lattice position.

        Args:
            fractional_position: Three direct-lattice fractional coordinates.

        Returns:
            Magnetic modulation phase in cycles/turns, before multiplying by
            ``2*pi`` to obtain radians.

        Raises:
            ValueError: If ``fractional_position`` is not a finite 3-vector.
        """

        position = _three_finite_components(fractional_position, "fractional_position")
        return sum(
            component * coordinate
            for component, coordinate in zip(self.components_rlu, position, strict=True)
        )

    def phase_radians(self, fractional_position: Sequence[float]) -> float:
        """Return ``2*pi*k dot r`` in radians for a fractional position."""

        return 2.0 * math.pi * self.phase_turns(fractional_position)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "vector_id": self.vector_id,
            "units": "reciprocal_lattice_units",
            "coordinate_frame": self.coordinate_frame,
            "components_rlu": list(self.components_rlu),
        }


def _three_finite_components(values: Sequence[float], name: str) -> tuple[float, float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a three-item sequence.")
    if len(values) != 3:
        raise ValueError(f"{name} must contain exactly three components.")
    components = []
    for index, value in enumerate(values):
        if (
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name}[{index}] must be a finite number.")
        components.append(float(value))
    return (components[0], components[1], components[2])
