"""Wavelength validation and simple continuous-wave X-ray helpers."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class WavelengthMetadata:
    """Auditable continuous-wave X-ray wavelength metadata.

    Args:
        wavelength_angstrom: Incident radiation wavelength in angstroms.
        label: Optional human-readable line or beam description.
        uncertainty_angstrom: Optional one-sigma wavelength uncertainty in
            angstroms.
        provenance: Optional source of the wavelength value, such as a
            calibration record, beamline log, or reference table.

    Raises:
        ValueError: If numeric values are non-finite, not positive, or optional
            strings are empty.

    Example:
        >>> metadata = WavelengthMetadata(1.5406, label="Cu Kalpha1")
        >>> metadata.to_dict()["units"]
        'angstrom'
    """

    wavelength_angstrom: float
    label: str | None = None
    uncertainty_angstrom: float | None = None
    provenance: str | None = None

    def __post_init__(self) -> None:
        """Validate wavelength value, units, and optional metadata."""

        wavelength = validate_wavelength_angstrom(self.wavelength_angstrom)
        uncertainty = _optional_positive_float(self.uncertainty_angstrom, "uncertainty_angstrom")
        label = _optional_non_empty_string(self.label, "label")
        provenance = _optional_non_empty_string(self.provenance, "provenance")

        object.__setattr__(self, "wavelength_angstrom", wavelength)
        object.__setattr__(self, "uncertainty_angstrom", uncertainty)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "provenance", provenance)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible representation."""

        payload: dict[str, object] = {
            "wavelength_angstrom": self.wavelength_angstrom,
            "units": "angstrom",
        }
        if self.label is not None:
            payload["label"] = self.label
        if self.uncertainty_angstrom is not None:
            payload["uncertainty_angstrom"] = self.uncertainty_angstrom
        if self.provenance is not None:
            payload["provenance"] = self.provenance
        return payload


def validate_wavelength_angstrom(wavelength_angstrom: float) -> float:
    """Validate a positive finite X-ray wavelength in angstroms.

    Args:
        wavelength_angstrom: Incident radiation wavelength in angstroms.

    Returns:
        The wavelength as a ``float``.

    Raises:
        ValueError: If the wavelength is not finite and strictly positive.

    Example:
        >>> validate_wavelength_angstrom(1.5406)
        1.5406
    """
    wavelength = _finite_float(wavelength_angstrom, "wavelength_angstrom")
    if wavelength <= 0.0:
        raise ValueError(f"wavelength_angstrom must be positive, got {wavelength!r}.")
    return wavelength


def validate_wavelength_metadata(wavelength_metadata: WavelengthMetadata | None) -> tuple[str, ...]:
    """Return actionable diagnostics for required wavelength metadata.

    Args:
        wavelength_metadata: Wavelength metadata object to check.

    Returns:
        Empty tuple when metadata is present and already validated, otherwise
        diagnostics describing the missing or invalid field.

    Example:
        >>> validate_wavelength_metadata(WavelengthMetadata(1.5406))
        ()
    """

    if wavelength_metadata is None:
        return ("wavelength_metadata is required; provide wavelength_angstrom in angstroms.",)
    if not isinstance(wavelength_metadata, WavelengthMetadata):
        return ("wavelength_metadata must be a WavelengthMetadata instance.",)
    return ()


def bragg_two_theta_degrees(d_spacing_angstrom: float, wavelength_angstrom: float, *, order: int = 1) -> float:
    """Compute a Bragg peak position for continuous-wave diffraction.

    This helper implements Bragg's law for a single reflection:

    ```text
    n lambda = 2 d sin(theta)
    two_theta = 2 theta
    ```

    Args:
        d_spacing_angstrom: Lattice-plane spacing in angstroms. Must be
            positive.
        wavelength_angstrom: Incident wavelength in angstroms. Must be
            positive.
        order: Positive diffraction order ``n``.

    Returns:
        Peak position in degrees two-theta.

    Raises:
        ValueError: If inputs are invalid or the requested reflection is not
            physically reachable because ``n * wavelength > 2 * d``.

    Example:
        >>> round(bragg_two_theta_degrees(1.0, 1.0), 6)
        60.0
    """
    d_spacing = _finite_float(d_spacing_angstrom, "d_spacing_angstrom")
    wavelength = validate_wavelength_angstrom(wavelength_angstrom)
    if d_spacing <= 0.0:
        raise ValueError(f"d_spacing_angstrom must be positive, got {d_spacing!r}.")
    if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
        raise ValueError(f"order must be a positive integer, got {order!r}.")

    argument = order * wavelength / (2.0 * d_spacing)
    if argument > 1.0:
        raise ValueError(
            "Bragg condition is unreachable: order * wavelength_angstrom "
            "must be less than or equal to 2 * d_spacing_angstrom."
        )
    return math.degrees(2.0 * math.asin(argument))


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _optional_positive_float(value: float | None, name: str) -> float | None:
    if value is None:
        return None
    numeric_value = _finite_float(value, name)
    if numeric_value <= 0.0:
        raise ValueError(f"{name} must be positive, got {numeric_value!r}.")
    return numeric_value


def _optional_non_empty_string(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string when supplied.")
    return value
