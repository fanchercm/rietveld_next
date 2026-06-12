"""Neutron sample-geometry and extinction correction interfaces."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


class SampleGeometryCorrectionHook(Protocol):
    """Protocol for dimensionless neutron sample-geometry corrections.

    Implementations return a positive multiplicative factor for calculated
    intensity at a finite CW neutron wavelength and two-theta angle.
    """

    def correction_factor(self, *, two_theta_degrees: float, wavelength_angstrom: float) -> float:
        """Return a positive dimensionless correction factor."""


class ExtinctionCorrectionHook(Protocol):
    """Protocol for dimensionless neutron extinction corrections.

    Implementations return a bounded multiplicative attenuation factor on
    ``(0, 1]``. The interface is intentionally independent of profile kernels.
    """

    def extinction_factor(self, *, structure_factor_squared: float, wavelength_angstrom: float) -> float:
        """Return a factor on ``(0, 1]`` applied to calculated intensity."""


@dataclass(frozen=True)
class ConstantSampleGeometryCorrection:
    """Constant sample-geometry correction interface implementation.

    This is a deterministic plumbing fixture, not a validated sample-shape
    correction model.

    Args:
        factor: Positive dimensionless correction factor.
        geometry: Non-empty sample geometry label for audit metadata.

    Raises:
        ValueError: If ``factor`` is not positive and finite, or ``geometry``
            is empty.

    Example:
        >>> ConstantSampleGeometryCorrection(1.2, geometry="capillary").correction_factor(
        ...     two_theta_degrees=60.0,
        ...     wavelength_angstrom=1.8,
        ... )
        1.2
    """

    factor: float = 1.0
    geometry: str = "unspecified"

    def __post_init__(self) -> None:
        """Validate correction factor and geometry label."""
        object.__setattr__(self, "factor", _positive_float(self.factor, "factor"))
        object.__setattr__(self, "geometry", _non_empty_string(self.geometry, "geometry"))

    def correction_factor(self, *, two_theta_degrees: float, wavelength_angstrom: float) -> float:
        """Return the configured factor after validating inputs."""
        _valid_two_theta(two_theta_degrees)
        _positive_float(wavelength_angstrom, "wavelength_angstrom")
        return self.factor


@dataclass(frozen=True)
class SimplePrimaryExtinctionCorrection:
    """Small bounded extinction correction interface.

    The factor is:

    ```text
    1 / (1 + coefficient * structure_factor_squared * wavelength)
    ```

    It is intended only as an interface and validation fixture.

    Args:
        coefficient_per_fm2_angstrom: Non-negative coefficient in inverse
            femtometer-squared angstrom units for the synthetic fixture.

    Raises:
        ValueError: If the coefficient is non-finite or negative.

    Example:
        >>> hook = SimplePrimaryExtinctionCorrection(0.01)
        >>> round(hook.extinction_factor(structure_factor_squared=4.0, wavelength_angstrom=2.0), 6)
        0.925926
    """

    coefficient_per_fm2_angstrom: float

    def __post_init__(self) -> None:
        """Validate extinction coefficient."""
        coefficient = _finite_float(self.coefficient_per_fm2_angstrom, "coefficient_per_fm2_angstrom")
        if coefficient < 0.0:
            raise ValueError("coefficient_per_fm2_angstrom must be non-negative.")
        object.__setattr__(self, "coefficient_per_fm2_angstrom", coefficient)

    def extinction_factor(self, *, structure_factor_squared: float, wavelength_angstrom: float) -> float:
        """Evaluate a bounded dimensionless extinction factor."""
        fsq = _finite_float(structure_factor_squared, "structure_factor_squared")
        if fsq < 0.0:
            raise ValueError("structure_factor_squared must be non-negative.")
        wavelength = _positive_float(wavelength_angstrom, "wavelength_angstrom")
        return 1.0 / (1.0 + self.coefficient_per_fm2_angstrom * fsq * wavelength)


def evaluate_sample_geometry_correction(
    hook: SampleGeometryCorrectionHook | None,
    *,
    two_theta_degrees: float,
    wavelength_angstrom: float,
) -> float:
    """Evaluate an optional sample-geometry correction hook.

    Args:
        hook: Sample-geometry hook or ``None`` for unit correction.
        two_theta_degrees: Scattering angle in degrees two-theta, open interval
            ``(0, 180)``.
        wavelength_angstrom: Positive neutron wavelength in angstroms.

    Returns:
        Positive dimensionless correction factor.

    Raises:
        ValueError: If inputs or the hook return value are invalid.
    """

    _valid_two_theta(two_theta_degrees)
    _positive_float(wavelength_angstrom, "wavelength_angstrom")
    if hook is None:
        return 1.0
    evaluator = getattr(hook, "correction_factor", None)
    if not callable(evaluator):
        raise ValueError(
            "sample geometry hook must define "
            "correction_factor(two_theta_degrees=..., wavelength_angstrom=...)."
        )
    return _positive_float(
        evaluator(two_theta_degrees=two_theta_degrees, wavelength_angstrom=wavelength_angstrom),
        "sample geometry correction",
    )


def evaluate_extinction_correction(
    hook: ExtinctionCorrectionHook | None,
    *,
    structure_factor_squared: float,
    wavelength_angstrom: float,
) -> float:
    """Evaluate an optional extinction correction hook.

    Args:
        hook: Extinction hook or ``None`` for unit correction.
        structure_factor_squared: Non-negative squared structure-factor
            magnitude in femtometer-squared units for this synthetic interface.
        wavelength_angstrom: Positive neutron wavelength in angstroms.

    Returns:
        Dimensionless extinction factor on ``(0, 1]``.

    Raises:
        ValueError: If inputs or the hook return value are invalid.
    """

    fsq = _finite_float(structure_factor_squared, "structure_factor_squared")
    if fsq < 0.0:
        raise ValueError("structure_factor_squared must be non-negative.")
    _positive_float(wavelength_angstrom, "wavelength_angstrom")
    if hook is None:
        return 1.0
    evaluator = getattr(hook, "extinction_factor", None)
    if not callable(evaluator):
        raise ValueError(
            "extinction hook must define "
            "extinction_factor(structure_factor_squared=..., wavelength_angstrom=...)."
        )
    value = _finite_float(
        evaluator(structure_factor_squared=fsq, wavelength_angstrom=wavelength_angstrom),
        "extinction correction",
    )
    if value <= 0.0 or value > 1.0:
        raise ValueError(f"extinction correction must be on (0, 1], got {value!r}.")
    return value


def _valid_two_theta(value: float) -> float:
    number = _finite_float(value, "two_theta_degrees")
    if number <= 0.0 or number >= 180.0:
        raise ValueError("two_theta_degrees must be between 0 and 180 degrees.")
    return number


def _positive_float(value: float, name: str) -> float:
    number = _finite_float(value, name)
    if number <= 0.0:
        raise ValueError(f"{name} must be positive, got {number!r}.")
    return number


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)


def _non_empty_string(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value
