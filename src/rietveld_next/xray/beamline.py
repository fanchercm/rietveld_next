"""Synchrotron beamline metadata templates."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


@dataclass(frozen=True)
class SynchrotronBeamlineTemplate:
    """Reusable metadata template for synchrotron CW XRD datasets.

    Args:
        facility_name: Synchrotron facility name.
        beamline_name: Beamline or station identifier.
        detector_name: Detector identifier or model.
        monochromator: Optional monochromator description.
        default_wavelength_angstrom: Optional default wavelength in angstroms.
        required_log_fields: Beamline log fields required for import.
    """

    facility_name: str
    beamline_name: str
    detector_name: str
    monochromator: str | None = None
    default_wavelength_angstrom: float | None = None
    required_log_fields: tuple[str, ...] = field(default_factory=lambda: ("wavelength_angstrom", "sample_id"))

    def __post_init__(self) -> None:
        """Validate template metadata."""
        object.__setattr__(self, "facility_name", _non_empty_string(self.facility_name, "facility_name"))
        object.__setattr__(self, "beamline_name", _non_empty_string(self.beamline_name, "beamline_name"))
        object.__setattr__(self, "detector_name", _non_empty_string(self.detector_name, "detector_name"))
        object.__setattr__(self, "monochromator", _optional_non_empty_string(self.monochromator, "monochromator"))
        if self.default_wavelength_angstrom is not None:
            wavelength = _positive_float(self.default_wavelength_angstrom, "default_wavelength_angstrom")
            object.__setattr__(self, "default_wavelength_angstrom", wavelength)
        fields = _string_tuple(self.required_log_fields, "required_log_fields")
        if not fields:
            raise ValueError("required_log_fields must contain at least one field.")
        object.__setattr__(self, "required_log_fields", fields)

    def missing_fields(self, metadata: dict[str, Any]) -> tuple[str, ...]:
        """Return required template fields absent from ``metadata``."""
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a mapping.")
        return tuple(field for field in self.required_log_fields if metadata.get(field) in (None, ""))

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""
        payload: dict[str, object] = {
            "template_type": "synchrotron_beamline_metadata",
            "facility_name": self.facility_name,
            "beamline_name": self.beamline_name,
            "detector_name": self.detector_name,
            "required_log_fields": list(self.required_log_fields),
            "units": {"wavelength": "angstrom"},
        }
        if self.monochromator is not None:
            payload["monochromator"] = self.monochromator
        if self.default_wavelength_angstrom is not None:
            payload["default_wavelength_angstrom"] = self.default_wavelength_angstrom
        return payload


def default_synchrotron_beamline_template(
    *,
    facility_name: str,
    beamline_name: str,
    detector_name: str,
) -> SynchrotronBeamlineTemplate:
    """Create the default beamline template used by startup import workflows."""
    return SynchrotronBeamlineTemplate(
        facility_name=facility_name,
        beamline_name=beamline_name,
        detector_name=detector_name,
        required_log_fields=(
            "wavelength_angstrom",
            "sample_id",
            "scan_id",
            "detector_distance_mm",
            "calibration_provenance",
        ),
    )


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, name)


def _string_tuple(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple of strings.")
    return tuple(_non_empty_string(value, f"{name}[{index}]") for index, value in enumerate(values))


def _positive_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    number = float(value)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number
