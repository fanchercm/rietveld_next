"""High-pressure EDXRD marker records and equation-of-state hooks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class HighPressureMarker:
    """High-pressure metadata marker for an EDXRD spectrum or refinement step.

    Args:
        marker_id: Stable non-empty marker identifier.
        pressure_gpa: Non-negative pressure in gigapascals.
        pressure_standard: Non-empty pressure standard label.
        temperature_kelvin: Positive sample temperature in kelvin.
        calibrant: Optional non-empty calibrant label.
        pressure_uncertainty_gpa: Optional non-negative pressure uncertainty.
        provenance: Deterministic provenance labels.

    Raises:
        ValueError: If units, bounds, or metadata are invalid.

    Example:
        >>> marker = HighPressureMarker("run-1", pressure_gpa=12.5, pressure_standard="ruby")
        >>> marker.to_project_entity()["units"]["pressure"]
        'GPa'
    """

    marker_id: str
    pressure_gpa: float
    pressure_standard: str
    temperature_kelvin: float = 300.0
    calibrant: str | None = None
    pressure_uncertainty_gpa: float | None = None
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate high-pressure marker metadata."""

        object.__setattr__(self, "marker_id", _non_empty_string(self.marker_id, "marker_id"))
        object.__setattr__(self, "pressure_gpa", _non_negative_float(self.pressure_gpa, "pressure_gpa"))
        object.__setattr__(self, "pressure_standard", _non_empty_string(self.pressure_standard, "pressure_standard"))
        object.__setattr__(
            self,
            "temperature_kelvin",
            _positive_float(self.temperature_kelvin, "temperature_kelvin"),
        )
        if self.calibrant is not None:
            object.__setattr__(self, "calibrant", _non_empty_string(self.calibrant, "calibrant"))
        if self.pressure_uncertainty_gpa is not None:
            object.__setattr__(
                self,
                "pressure_uncertainty_gpa",
                _non_negative_float(self.pressure_uncertainty_gpa, "pressure_uncertainty_gpa"),
            )
        object.__setattr__(self, "provenance", _string_mapping(self.provenance, "provenance"))

    def to_project_entity(self) -> dict[str, object]:
        """Return a deterministic project-model compatible marker entity."""

        payload: dict[str, object] = {
            "entity_type": "edxrd_high_pressure_marker",
            "schema_version": "edxrd-high-pressure-marker-v1",
            "marker_id": self.marker_id,
            "pressure_gpa": self.pressure_gpa,
            "pressure_standard": self.pressure_standard,
            "temperature_kelvin": self.temperature_kelvin,
            "units": {
                "pressure": "GPa",
                "temperature": "K",
                "pressure_uncertainty": "GPa",
            },
            "bounds": {
                "pressure_gpa": "[0, +inf)",
                "temperature_kelvin": "(0, +inf)",
            },
            "provenance": dict(sorted(self.provenance.items())),
        }
        if self.calibrant is not None:
            payload["calibrant"] = self.calibrant
        if self.pressure_uncertainty_gpa is not None:
            payload["pressure_uncertainty_gpa"] = self.pressure_uncertainty_gpa
        return payload


@dataclass(frozen=True)
class BirchMurnaghanEquationOfState:
    """Third-order Birch-Murnaghan equation-of-state helper.

    Args:
        reference_volume_angstrom3: Positive zero-pressure reference volume.
        bulk_modulus_gpa: Positive bulk modulus ``K0`` in GPa.
        bulk_modulus_derivative: Dimensionless pressure derivative ``K0'``.
        label: Non-empty EOS label.

    Raises:
        ValueError: If EOS parameters are non-finite or outside supported
            bounds.
    """

    reference_volume_angstrom3: float
    bulk_modulus_gpa: float
    bulk_modulus_derivative: float
    label: str = "birch_murnaghan_3rd"

    def __post_init__(self) -> None:
        """Validate equation-of-state parameters."""

        object.__setattr__(
            self,
            "reference_volume_angstrom3",
            _positive_float(self.reference_volume_angstrom3, "reference_volume_angstrom3"),
        )
        object.__setattr__(self, "bulk_modulus_gpa", _positive_float(self.bulk_modulus_gpa, "bulk_modulus_gpa"))
        object.__setattr__(
            self,
            "bulk_modulus_derivative",
            _positive_float(self.bulk_modulus_derivative, "bulk_modulus_derivative"),
        )
        object.__setattr__(self, "label", _non_empty_string(self.label, "label"))

    def pressure_gpa(self, volume_angstrom3: float) -> float:
        """Evaluate pressure at a compressed unit-cell volume.

        Args:
            volume_angstrom3: Positive volume in cubic angstroms.

        Returns:
            Pressure in GPa. Volumes greater than the reference volume return a
            negative tensile value; callers that model compression should use
            :meth:`volume_at_pressure_gpa`.
        """

        volume = _positive_float(volume_angstrom3, "volume_angstrom3")
        compression = (self.reference_volume_angstrom3 / volume) ** (1.0 / 3.0)
        eta2 = compression * compression
        finite_strain_term = eta2**3.5 - eta2**2.5
        correction = 1.0 + 0.75 * (self.bulk_modulus_derivative - 4.0) * (eta2 - 1.0)
        return 1.5 * self.bulk_modulus_gpa * finite_strain_term * correction

    def volume_at_pressure_gpa(self, pressure_gpa: float) -> float:
        """Solve compressed volume for a non-negative pressure using bisection.

        Args:
            pressure_gpa: Non-negative target pressure in GPa.

        Returns:
            Volume in cubic angstroms.

        Raises:
            ValueError: If pressure is invalid or outside the conservative
                synthetic solver range.
        """

        pressure = _non_negative_float(pressure_gpa, "pressure_gpa")
        if pressure == 0.0:
            return self.reference_volume_angstrom3
        lower = self.reference_volume_angstrom3 * 0.25
        upper = self.reference_volume_angstrom3
        if self.pressure_gpa(lower) < pressure:
            raise ValueError("pressure_gpa is outside the supported compression range for this EOS.")
        for _ in range(96):
            midpoint = 0.5 * (lower + upper)
            if self.pressure_gpa(midpoint) > pressure:
                lower = midpoint
            else:
                upper = midpoint
        return 0.5 * (lower + upper)

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-compatible EOS metadata."""

        return {
            "eos": "birch_murnaghan_3rd",
            "label": self.label,
            "reference_volume_angstrom3": self.reference_volume_angstrom3,
            "bulk_modulus_gpa": self.bulk_modulus_gpa,
            "bulk_modulus_derivative": self.bulk_modulus_derivative,
            "units": {
                "volume": "angstrom^3",
                "bulk_modulus": "GPa",
                "pressure": "GPa",
            },
        }


@dataclass(frozen=True)
class EquationOfStateHook:
    """Apply isotropic EOS compression to reference d-spacings.

    Args:
        eos: Birch-Murnaghan equation-of-state helper.
        reference_d_spacings_angstrom: Positive zero-pressure d-spacings.
        labels: Optional labels for each d-spacing.

    Raises:
        ValueError: If EOS metadata, d-spacings, or labels are invalid.
    """

    eos: BirchMurnaghanEquationOfState
    reference_d_spacings_angstrom: tuple[float, ...]
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate EOS hook fixture metadata."""

        if not isinstance(self.eos, BirchMurnaghanEquationOfState):
            raise ValueError("eos must be a BirchMurnaghanEquationOfState.")
        d_spacings = _positive_float_tuple(self.reference_d_spacings_angstrom, "reference_d_spacings_angstrom")
        if not d_spacings:
            raise ValueError("reference_d_spacings_angstrom must contain at least one value.")
        labels = _labels_tuple(self.labels, len(d_spacings))
        object.__setattr__(self, "reference_d_spacings_angstrom", d_spacings)
        object.__setattr__(self, "labels", labels)

    def compressed_d_spacings_angstrom(self, marker: HighPressureMarker) -> tuple[float, ...]:
        """Return pressure-compressed d-spacings for a marker.

        The hook assumes isotropic compression, so d-spacings scale by
        ``(V(P) / V0) ** (1 / 3)``. This is a deterministic validation fixture,
        not a material-specific high-pressure refinement model.
        """

        pressure_marker = _marker(marker)
        volume = self.eos.volume_at_pressure_gpa(pressure_marker.pressure_gpa)
        scale = (volume / self.eos.reference_volume_angstrom3) ** (1.0 / 3.0)
        return tuple(d_spacing * scale for d_spacing in self.reference_d_spacings_angstrom)

    def marker_prediction(self, marker: HighPressureMarker) -> dict[str, object]:
        """Return compressed d-spacing prediction and provenance metadata."""

        pressure_marker = _marker(marker)
        compressed = self.compressed_d_spacings_angstrom(pressure_marker)
        return {
            "prediction_type": "edxrd_eos_compressed_d_spacing",
            "marker": pressure_marker.to_project_entity(),
            "eos": self.eos.to_dict(),
            "assumption": "isotropic d-spacing scaling from volume compression",
            "reference_d_spacings_angstrom": list(self.reference_d_spacings_angstrom),
            "compressed_d_spacings_angstrom": list(compressed),
            "labels": list(self.labels),
            "units": {"d_spacing": "angstrom", "pressure": "GPa"},
        }


def _marker(value: HighPressureMarker) -> HighPressureMarker:
    if not isinstance(value, HighPressureMarker):
        raise ValueError("marker must be a HighPressureMarker.")
    return value


def _labels_tuple(labels: Sequence[str], count: int) -> tuple[str, ...]:
    if not labels:
        return tuple(f"reflection-{index + 1}" for index in range(count))
    if isinstance(labels, str) or not isinstance(labels, Sequence):
        raise ValueError("labels must be a sequence of strings.")
    label_tuple = tuple(_non_empty_string(label, f"labels[{index}]") for index, label in enumerate(labels))
    if len(label_tuple) != count:
        raise ValueError("labels must match reference_d_spacings_angstrom length.")
    return label_tuple


def _positive_float_tuple(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_positive_float(value, f"{name}[{index}]") for index, value in enumerate(values))


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


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _string_mapping(values: Mapping[str, str], name: str) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a mapping.")
    payload: dict[str, str] = {}
    for key, value in values.items():
        payload[_non_empty_string(key, f"{name} key")] = _non_empty_string(value, f"{name}[{key!r}]")
    return dict(sorted(payload.items()))
