"""EDXRD import template validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math

from rietveld_next.edxrd.calibration import (
    EDXRDCalibrationPoint,
    EDXRDCalibrationResult,
    calibration_points_from_fixed_angle_standard,
    fit_fixed_angle_edxrd_calibration,
)


EDXRD_IMPORT_TEMPLATE_SCHEMA_VERSION = "edxrd_import_template.v1"
"""Schema version tag for the initial EDXRD import template."""


@dataclass(frozen=True)
class EDXRDImportedSpectrum:
    """Validated EDXRD channel-count rows.

    Args:
        channels: Strictly increasing detector-channel coordinates.
        counts: Intensity counts in the template count units.
        uncertainties: Optional non-negative uncertainties in count units.

    Raises:
        ValueError: If array lengths, channel order, or values are invalid.
    """

    channels: tuple[float, ...]
    counts: tuple[float, ...]
    uncertainties: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        """Validate imported arrays and optional uncertainties."""

        channels = _finite_float_sequence(self.channels, "channels")
        counts = _finite_float_sequence(self.counts, "counts")
        if len(channels) != len(counts):
            raise ValueError("channels and counts must have the same length.")
        if not channels:
            raise ValueError("imported spectrum must contain at least one row.")
        _require_strictly_increasing(channels, "channels")
        uncertainties = None
        if self.uncertainties is not None:
            uncertainties = _finite_float_sequence(self.uncertainties, "uncertainties")
            if len(uncertainties) != len(channels):
                raise ValueError("uncertainties must have the same length as channels.")
            if any(value < 0.0 for value in uncertainties):
                raise ValueError("uncertainties must be non-negative.")
        object.__setattr__(self, "channels", channels)
        object.__setattr__(self, "counts", counts)
        object.__setattr__(self, "uncertainties", uncertainties)

    @property
    def point_count(self) -> int:
        """Return the number of imported spectrum rows."""

        return len(self.channels)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""

        payload: dict[str, object] = {
            "channels": list(self.channels),
            "counts": list(self.counts),
            "point_count": self.point_count,
        }
        if self.uncertainties is not None:
            payload["uncertainties"] = list(self.uncertainties)
        return payload


@dataclass(frozen=True)
class EDXRDImportTemplate:
    """Template describing required EDXRD import fields.

    Args:
        name: Template name.
        required_columns: Required tabular data columns.
        required_metadata: Required metadata keys.
        energy_units: Energy units, currently ``"keV"``.
        schema_version: Version tag for this import template.
        optional_columns: Optional spectrum data columns.
        calibration_standard_columns: Calibration-standard row columns.

    Raises:
        ValueError: If identifiers, columns, metadata, or units are invalid.
    """

    name: str = "edxrd_energy_histogram_v1"
    required_columns: tuple[str, ...] = ("channel", "counts")
    required_metadata: tuple[str, ...] = ("energy_calibration", "two_theta_degrees", "detector_id")
    energy_units: str = "keV"
    schema_version: str = EDXRD_IMPORT_TEMPLATE_SCHEMA_VERSION
    optional_columns: tuple[str, ...] = ("uncertainty",)
    calibration_standard_columns: tuple[str, ...] = ("channel", "d_spacing_angstrom", "label")

    def __post_init__(self) -> None:
        """Validate template fields."""
        object.__setattr__(self, "name", _non_empty_string(self.name, "name"))
        object.__setattr__(self, "required_columns", _string_sequence(self.required_columns, "required_columns"))
        object.__setattr__(self, "required_metadata", _string_sequence(self.required_metadata, "required_metadata"))
        object.__setattr__(self, "optional_columns", _string_sequence(self.optional_columns, "optional_columns"))
        object.__setattr__(
            self,
            "calibration_standard_columns",
            _string_sequence(self.calibration_standard_columns, "calibration_standard_columns"),
        )
        if self.energy_units != "keV":
            raise ValueError("energy_units must be 'keV'.")
        if self.schema_version != EDXRD_IMPORT_TEMPLATE_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {EDXRD_IMPORT_TEMPLATE_SCHEMA_VERSION!r}.")

    def validate_payload(
        self,
        *,
        columns: Sequence[str],
        metadata: Mapping[str, object],
    ) -> tuple[str, ...]:
        """Return actionable diagnostics for an import payload."""
        observed_columns = set(_string_sequence(tuple(columns), "columns"))
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping.")
        diagnostics: list[str] = []
        for column in self.required_columns:
            if column not in observed_columns:
                diagnostics.append(f"missing required column: {column}")
        for key in self.required_metadata:
            if metadata.get(key) in (None, ""):
                diagnostics.append(f"missing required metadata: {key}")
        return tuple(diagnostics)

    def parse_spectrum_rows(
        self,
        rows: Sequence[Mapping[str, object]],
    ) -> EDXRDImportedSpectrum:
        """Validate channel-count rows for this import template.

        Args:
            rows: Row mappings with required ``channel`` and ``counts`` values
                plus optional non-negative ``uncertainty`` values.

        Returns:
            Validated imported spectrum arrays.

        Raises:
            ValueError: If rows are missing columns or contain invalid values.
        """

        row_values = _row_sequence(rows)
        channels: list[float] = []
        counts: list[float] = []
        uncertainties: list[float] = []
        has_uncertainty = False
        for index, row in enumerate(row_values):
            channels.append(_required_float(row, "channel", index))
            counts.append(_required_float(row, "counts", index))
            if "uncertainty" in row and row["uncertainty"] is not None:
                has_uncertainty = True
                uncertainties.append(_required_float(row, "uncertainty", index))
            else:
                uncertainties.append(0.0)
        return EDXRDImportedSpectrum(
            channels=tuple(channels),
            counts=tuple(counts),
            uncertainties=tuple(uncertainties) if has_uncertainty else None,
        )

    def calibration_points_from_standard_rows(
        self,
        rows: Sequence[Mapping[str, object]],
        *,
        two_theta_degrees: float,
        order: int = 1,
    ) -> tuple[EDXRDCalibrationPoint, ...]:
        """Create calibration points from fixed-angle standard import rows.

        Args:
            rows: Row mappings with ``channel`` and ``d_spacing_angstrom`` plus
                optional ``label`` values.
            two_theta_degrees: Fixed scattering angle in degrees two-theta.
            order: Positive diffraction order for the Bragg conversion.

        Returns:
            Calibration points with reference energies in keV.

        Raises:
            ValueError: If required columns or physical inputs are invalid.
        """

        row_values = _row_sequence(rows)
        channels = tuple(_required_float(row, "channel", index) for index, row in enumerate(row_values))
        d_spacings = tuple(
            _required_float(row, "d_spacing_angstrom", index)
            for index, row in enumerate(row_values)
        )
        labels = tuple(_optional_string(row, "label", index) for index, row in enumerate(row_values))
        return calibration_points_from_fixed_angle_standard(
            channels=channels,
            d_spacings_angstrom=d_spacings,
            two_theta_degrees=two_theta_degrees,
            labels=_standard_labels(labels),
            order=order,
        )

    def fit_calibration_from_standard_rows(
        self,
        rows: Sequence[Mapping[str, object]],
        *,
        two_theta_degrees: float,
        polynomial_order: int = 1,
        order: int = 1,
        provenance: Mapping[str, str] | None = None,
    ) -> EDXRDCalibrationResult:
        """Fit channel-to-energy calibration from standard import rows.

        Args:
            rows: Row mappings with ``channel`` and ``d_spacing_angstrom`` plus
                optional ``label`` values.
            two_theta_degrees: Fixed scattering angle in degrees two-theta.
            polynomial_order: Calibration polynomial order, currently 1 or 2.
            order: Positive diffraction order for the Bragg conversion.
            provenance: Optional workflow provenance labels.

        Returns:
            Fitted calibration result with residuals and provenance.

        Raises:
            ValueError: If required columns, metadata, or fit inputs are invalid.
        """

        row_values = _row_sequence(rows)
        channels = tuple(_required_float(row, "channel", index) for index, row in enumerate(row_values))
        d_spacings = tuple(
            _required_float(row, "d_spacing_angstrom", index)
            for index, row in enumerate(row_values)
        )
        labels = tuple(_optional_string(row, "label", index) for index, row in enumerate(row_values))
        workflow_provenance = {"template": self.name, "schema_version": self.schema_version}
        if provenance is not None:
            workflow_provenance.update(_string_mapping(provenance, "provenance"))
        return fit_fixed_angle_edxrd_calibration(
            channels=channels,
            d_spacings_angstrom=d_spacings,
            two_theta_degrees=two_theta_degrees,
            polynomial_order=polynomial_order,
            labels=_standard_labels(labels),
            order=order,
            provenance=workflow_provenance,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible template."""
        return {
            "template_type": "edxrd_import_template",
            "schema_version": self.schema_version,
            "name": self.name,
            "required_columns": list(self.required_columns),
            "optional_columns": list(self.optional_columns),
            "calibration_standard_columns": list(self.calibration_standard_columns),
            "required_metadata": list(self.required_metadata),
            "energy_units": self.energy_units,
            "column_units": {
                "channel": "detector_channel",
                "counts": "counts",
                "uncertainty": "counts",
                "d_spacing_angstrom": "angstrom",
                "label": "text",
            },
            "calibration_workflow": {
                "model": "energy_keV = c0 + c1*channel + c2*channel^2",
                "reference_geometry": "fixed_angle_bragg",
            },
        }


def default_edxrd_import_template() -> EDXRDImportTemplate:
    """Return the default startup EDXRD import template."""
    return EDXRDImportTemplate()


def _string_sequence(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of strings.")
    result = tuple(_non_empty_string(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not result:
        raise ValueError(f"{name} must not be empty.")
    return result


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _row_sequence(values: Sequence[Mapping[str, object]]) -> tuple[Mapping[str, object], ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError("rows must be a sequence of mappings.")
    rows = tuple(values)
    if not rows:
        raise ValueError("rows must contain at least one row.")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{index}] must be a mapping.")
    return rows


def _required_float(row: Mapping[str, object], key: str, index: int) -> float:
    if key not in row:
        raise ValueError(f"rows[{index}] is missing required column {key!r}.")
    return _finite_float(row[key], f"rows[{index}][{key!r}]")


def _optional_string(row: Mapping[str, object], key: str, index: int) -> str | None:
    if key not in row or row[key] is None:
        return None
    if not isinstance(row[key], str) or not row[key].strip():
        raise ValueError(f"rows[{index}][{key!r}] must be a non-empty string when supplied.")
    return row[key].strip()


def _standard_labels(labels: tuple[str | None, ...]) -> tuple[str, ...] | None:
    if all(label is None for label in labels):
        return None
    return tuple(label if label is not None else f"standard-{index + 1}" for index, label in enumerate(labels))


def _finite_float_sequence(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence of finite numbers.")
    return tuple(_finite_float(value, f"{name}[{index}]") for index, value in enumerate(values))


def _finite_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _require_strictly_increasing(values: tuple[float, ...], name: str) -> None:
    for index, (left, right) in enumerate(zip(values, values[1:])):
        if right <= left:
            raise ValueError(f"{name} must be strictly increasing at index {index + 1}.")


def _string_mapping(values: Mapping[str, str], name: str) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a mapping.")
    payload: dict[str, str] = {}
    for key, value in values.items():
        payload[_non_empty_string(key, f"{name} key")] = _non_empty_string(value, f"{name}[{key!r}]")
    return dict(sorted(payload.items()))
