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
    DEFAULT_MAGNITUDE_TOLERANCE_BOHR_MAGNETON = 1.0e-12

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
            raise ValueError(
                f"MagneticMoment payload is missing required key(s): {', '.join(missing)}."
            )
        moment = cls(
            site_id=data["site_id"],
            components_bohr_magneton=data["components_bohr_magneton"],
            coordinate_frame=data.get("coordinate_frame", "crystal_fractional"),
        )
        if "magnitude_bohr_magneton" in data:
            declared_magnitude = _finite_float(
                data["magnitude_bohr_magneton"],
                "magnitude_bohr_magneton",
            )
            if declared_magnitude < 0.0:
                raise ValueError("magnitude_bohr_magneton must be non-negative.")
            if not math.isclose(
                declared_magnitude,
                moment.magnitude_bohr_magneton,
                rel_tol=0.0,
                abs_tol=cls.DEFAULT_MAGNITUDE_TOLERANCE_BOHR_MAGNETON,
            ):
                raise ValueError(
                    "magnitude_bohr_magneton must match the Euclidean norm of "
                    "components_bohr_magneton within 1e-12 Bohr magneton."
                )
        return moment

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

    def validate_magnitude(
        self,
        *,
        min_bohr_magneton: float = 0.0,
        max_bohr_magneton: float | None = None,
        tolerance_bohr_magneton: float = DEFAULT_MAGNITUDE_TOLERANCE_BOHR_MAGNETON,
    ) -> None:
        """Validate the moment magnitude against explicit Bohr-magneton bounds.

        Args:
            min_bohr_magneton: Inclusive lower bound in Bohr magnetons.
            max_bohr_magneton: Optional inclusive upper bound in Bohr magnetons.
            tolerance_bohr_magneton: Absolute tolerance applied to both bounds.

        Raises:
            ValueError: If bounds are invalid or the moment magnitude lies
                outside the tolerated range.

        Example:
            >>> MagneticMoment("mn1", (0.0, 0.0, 3.2)).validate_magnitude(max_bohr_magneton=5.0)
        """

        lower = _non_negative_finite_float(min_bohr_magneton, "min_bohr_magneton")
        tolerance = _non_negative_finite_float(tolerance_bohr_magneton, "tolerance_bohr_magneton")
        upper = None
        if max_bohr_magneton is not None:
            upper = _non_negative_finite_float(max_bohr_magneton, "max_bohr_magneton")
            if upper < lower:
                raise ValueError(
                    "max_bohr_magneton must be greater than or equal to min_bohr_magneton."
                )

        magnitude = self.magnitude_bohr_magneton
        if magnitude + tolerance < lower:
            raise ValueError(
                "moment magnitude is below the minimum bound: "
                f"{magnitude} < {lower} Bohr magneton."
            )
        if upper is not None and magnitude - tolerance > upper:
            raise ValueError(
                "moment magnitude exceeds the maximum bound: "
                f"{magnitude} > {upper} Bohr magneton."
            )


def _three_finite_components(values: Sequence[float]) -> tuple[float, float, float]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("components_bohr_magneton must be a three-item sequence.")
    if len(values) != 3:
        raise ValueError("components_bohr_magneton must contain exactly three components.")
    components = []
    for index, value in enumerate(values):
        components.append(_finite_float(value, f"components_bohr_magneton[{index}]"))
    return (components[0], components[1], components[2])


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def _non_negative_finite_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative.")
    return number
