"""Magnetic moment entity with explicit units and coordinate frame."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence
from typing import Any


@dataclass(frozen=True)
class MagneticMoment:
    """Magnetic moment vector for one atom site or magnetic component.

    Args:
        site_id: Stable atom-site or component identifier.
        components_bohr_magneton: Three vector components in Bohr magnetons.
        coordinate_frame: Coordinate frame for the components. Supported values
            are ``crystal_fractional``, ``cartesian_sample``, and
            ``cartesian_lab``.

    Raises:
        ValueError: If the site ID, vector shape, units, or frame are invalid.

    Example:
        >>> MagneticMoment("mn1", (0.0, 0.0, 3.2)).magnitude_bohr_magneton
        3.2
    """

    site_id: str
    components_bohr_magneton: tuple[float, float, float]
    coordinate_frame: str = "crystal_fractional"

    SUPPORTED_FRAMES = frozenset({"crystal_fractional", "cartesian_sample", "cartesian_lab"})

    def __post_init__(self) -> None:
        """Validate moment identity, component shape, and frame."""
        if not isinstance(self.site_id, str) or not self.site_id:
            raise ValueError("site_id must be a non-empty string.")
        components = _three_finite_components(self.components_bohr_magneton)
        if self.coordinate_frame not in self.SUPPORTED_FRAMES:
            allowed = ", ".join(sorted(self.SUPPORTED_FRAMES))
            raise ValueError(f"coordinate_frame must be one of: {allowed}.")
        object.__setattr__(self, "components_bohr_magneton", components)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MagneticMoment:
        """Create a magnetic moment from a JSON-compatible mapping.

        Args:
            data: Mapping produced by :meth:`to_dict`.

        Returns:
            Magnetic moment instance.

        Raises:
            ValueError: If required keys or values are invalid.
        """

        if not isinstance(data, dict):
            raise ValueError("MagneticMoment payload must be an object.")
        missing = [key for key in ("site_id", "components_bohr_magneton") if key not in data]
        if missing:
            raise ValueError(f"MagneticMoment payload is missing required key(s): {', '.join(missing)}.")
        return cls(
            site_id=data["site_id"],
            components_bohr_magneton=data["components_bohr_magneton"],
            coordinate_frame=data.get("coordinate_frame", "crystal_fractional"),
        )

    @property
    def magnitude_bohr_magneton(self) -> float:
        """Return the Euclidean moment magnitude in Bohr magnetons."""

        return math.sqrt(sum(component * component for component in self.components_bohr_magneton))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        return {
            "site_id": self.site_id,
            "units": "bohr_magneton",
            "coordinate_frame": self.coordinate_frame,
            "components_bohr_magneton": list(self.components_bohr_magneton),
            "magnitude_bohr_magneton": self.magnitude_bohr_magneton,
        }


def _three_finite_components(values: Sequence[float]) -> tuple[float, float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("components_bohr_magneton must be a three-item sequence.")
    if len(values) != 3:
        raise ValueError("components_bohr_magneton must contain exactly three components.")
    components = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
            raise ValueError(f"components_bohr_magneton[{index}] must be a finite number.")
        components.append(float(value))
    return (components[0], components[1], components[2])
