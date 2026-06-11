"""Continuous-wave X-ray instrument metadata models."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import ClassVar

from rietveld_next.xray.wavelength import WavelengthMetadata, validate_wavelength_metadata


@dataclass(frozen=True)
class LabCwXrdInstrument:
    """Laboratory continuous-wave XRD instrument metadata.

    Args:
        name: Instrument name or local identifier.
        wavelength_metadata: Incident wavelength metadata in angstroms.
        tube_anode: X-ray tube anode material, such as ``"Cu"``.
        radiation_line: Laboratory emission line label, such as
            ``"Kalpha1"``.
        goniometer_geometry: Measurement geometry label.
        generator_voltage_kv: Optional tube voltage in kilovolts.
        generator_current_ma: Optional tube current in milliamps.

    Raises:
        ValueError: If required metadata is missing, empty, or outside bounds.

    Example:
        >>> wavelength = WavelengthMetadata(1.5406, label="Cu Kalpha1")
        >>> LabCwXrdInstrument("lab-1", wavelength, tube_anode="Cu").instrument_type
        'lab_cw_xrd'
    """

    name: str
    wavelength_metadata: WavelengthMetadata
    tube_anode: str
    radiation_line: str = "Kalpha"
    goniometer_geometry: str = "bragg-brentano"
    generator_voltage_kv: float | None = None
    generator_current_ma: float | None = None

    instrument_type: ClassVar[str] = "lab_cw_xrd"

    def __post_init__(self) -> None:
        """Validate lab instrument metadata and normalize numeric values."""

        _raise_for_wavelength_diagnostics(
            validate_wavelength_metadata(self.wavelength_metadata),
            "lab CW XRD instrument",
        )
        name = _required_non_empty_string(self.name, "name")
        tube_anode = _required_non_empty_string(self.tube_anode, "tube_anode")
        radiation_line = _required_non_empty_string(self.radiation_line, "radiation_line")
        geometry = _required_non_empty_string(self.goniometer_geometry, "goniometer_geometry")
        voltage = _optional_positive_float(self.generator_voltage_kv, "generator_voltage_kv")
        current = _optional_positive_float(self.generator_current_ma, "generator_current_ma")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "tube_anode", tube_anode)
        object.__setattr__(self, "radiation_line", radiation_line)
        object.__setattr__(self, "goniometer_geometry", geometry)
        object.__setattr__(self, "generator_voltage_kv", voltage)
        object.__setattr__(self, "generator_current_ma", current)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "instrument_type": self.instrument_type,
            "name": self.name,
            "wavelength_metadata": self.wavelength_metadata.to_dict(),
            "tube_anode": self.tube_anode,
            "radiation_line": self.radiation_line,
            "goniometer_geometry": self.goniometer_geometry,
            "units": {
                "wavelength": "angstrom",
                "generator_voltage": "kV",
                "generator_current": "mA",
            },
        }
        if self.generator_voltage_kv is not None:
            payload["generator_voltage_kv"] = self.generator_voltage_kv
        if self.generator_current_ma is not None:
            payload["generator_current_ma"] = self.generator_current_ma
        return payload


@dataclass(frozen=True)
class SynchrotronCwXrdInstrument:
    """Synchrotron continuous-wave XRD instrument metadata.

    Args:
        name: Instrument or experimental station identifier.
        wavelength_metadata: Incident wavelength metadata in angstroms.
        facility_name: Synchrotron facility name.
        beamline_name: Required beamline identifier.
        monochromator: Optional monochromator description.
        storage_ring_mode: Optional storage-ring mode or fill pattern label.

    Raises:
        ValueError: If required wavelength, facility, or beamline metadata is
            missing or invalid.

    Example:
        >>> wavelength = WavelengthMetadata(0.7995, label="monochromatic")
        >>> instrument = SynchrotronCwXrdInstrument(
        ...     "powder-station",
        ...     wavelength,
        ...     facility_name="Example Light Source",
        ...     beamline_name="BL-1",
        ... )
        >>> instrument.instrument_type
        'synchrotron_cw_xrd'
    """

    name: str
    wavelength_metadata: WavelengthMetadata
    facility_name: str
    beamline_name: str
    monochromator: str | None = None
    storage_ring_mode: str | None = None

    instrument_type: ClassVar[str] = "synchrotron_cw_xrd"

    def __post_init__(self) -> None:
        """Validate synchrotron instrument and beamline metadata."""

        _raise_for_wavelength_diagnostics(
            validate_wavelength_metadata(self.wavelength_metadata),
            "synchrotron CW XRD instrument",
        )
        name = _required_non_empty_string(self.name, "name")
        facility = _required_non_empty_string(self.facility_name, "facility_name")
        beamline = _required_non_empty_string(self.beamline_name, "beamline_name")
        monochromator = _optional_non_empty_string(self.monochromator, "monochromator")
        storage_ring_mode = _optional_non_empty_string(self.storage_ring_mode, "storage_ring_mode")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "facility_name", facility)
        object.__setattr__(self, "beamline_name", beamline)
        object.__setattr__(self, "monochromator", monochromator)
        object.__setattr__(self, "storage_ring_mode", storage_ring_mode)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "instrument_type": self.instrument_type,
            "name": self.name,
            "wavelength_metadata": self.wavelength_metadata.to_dict(),
            "facility_name": self.facility_name,
            "beamline_name": self.beamline_name,
            "units": {"wavelength": "angstrom"},
        }
        if self.monochromator is not None:
            payload["monochromator"] = self.monochromator
        if self.storage_ring_mode is not None:
            payload["storage_ring_mode"] = self.storage_ring_mode
        return payload


def _raise_for_wavelength_diagnostics(diagnostics: tuple[str, ...], context: str) -> None:
    if diagnostics:
        raise ValueError(f"Invalid {context} metadata: {' '.join(diagnostics)}")


def _required_non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required and must be a non-empty string.")
    return value


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when supplied.")
    return value


def _optional_positive_float(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    numeric_value = float(value)
    if numeric_value <= 0.0:
        raise ValueError(f"{name} must be positive, got {numeric_value!r}.")
    return numeric_value
