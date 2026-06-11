"""Wavelength-dependent neutron absorption hook interfaces.

This module defines a small attachment point for neutron absorption terms. It
does not implement a validated sample-shape, path-length, or microabsorption
correction; it only standardizes how early neutron instrument models can ask a
hook for a wavelength-dependent transmission factor.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


class WavelengthDependentAbsorptionHook(Protocol):
    """Protocol for neutron absorption transmission hooks.

    Implementations return a dimensionless transmission factor on ``[0, 1]``
    for a neutron wavelength in angstroms.

    Example:
        >>> hook = ConstantNeutronAbsorption(transmission=0.75)
        >>> hook.transmission_factor(1.8)
        0.75
    """

    def transmission_factor(self, wavelength_angstrom: float) -> float:
        """Return dimensionless transmission for ``wavelength_angstrom``."""


@dataclass(frozen=True)
class ConstantNeutronAbsorption:
    """Constant neutron absorption transmission hook.

    This is useful for plumbing tests and explicit no-geometry corrections; it
    is not a validated absorption correction model.

    Args:
        transmission: Dimensionless transmission factor on ``[0, 1]``.

    Raises:
        ValueError: If ``transmission`` is non-finite or outside ``[0, 1]``.

    Example:
        >>> ConstantNeutronAbsorption(0.5).transmission_factor(2.4)
        0.5
    """

    transmission: float

    def __post_init__(self) -> None:
        """Validate the stored dimensionless transmission factor."""

        object.__setattr__(self, "transmission", _transmission_factor(self.transmission, "transmission"))

    def transmission_factor(self, wavelength_angstrom: float) -> float:
        """Return the same transmission after wavelength validation."""

        validate_wavelength_angstrom(wavelength_angstrom)
        return self.transmission


@dataclass(frozen=True)
class LinearWavelengthNeutronAbsorption:
    """Linear wavelength-dependent transmission hook skeleton.

    The model is a deterministic placeholder:

    ```text
    transmission(lambda) = reference_transmission
        + slope_per_angstrom * (lambda - reference_wavelength_angstrom)
    ```

    It raises when the evaluated value leaves ``[0, 1]`` instead of silently
    clipping, because this skeleton is not a validated correction model.

    Args:
        reference_wavelength_angstrom: Positive reference wavelength in
            angstroms.
        reference_transmission: Dimensionless transmission on ``[0, 1]`` at
            the reference wavelength.
        slope_per_angstrom: Finite dimensionless transmission slope per
            angstrom.

    Raises:
        ValueError: If any value is non-finite, the reference wavelength is not
            positive, or a transmission value is outside ``[0, 1]``.

    Example:
        >>> hook = LinearWavelengthNeutronAbsorption(1.8, 0.9, -0.1)
        >>> round(hook.transmission_factor(2.0), 3)
        0.88
    """

    reference_wavelength_angstrom: float
    reference_transmission: float
    slope_per_angstrom: float

    def __post_init__(self) -> None:
        """Validate reference wavelength, transmission, and slope."""

        object.__setattr__(
            self,
            "reference_wavelength_angstrom",
            validate_wavelength_angstrom(self.reference_wavelength_angstrom),
        )
        object.__setattr__(
            self,
            "reference_transmission",
            _transmission_factor(self.reference_transmission, "reference_transmission"),
        )
        object.__setattr__(self, "slope_per_angstrom", _finite_float(self.slope_per_angstrom, "slope_per_angstrom"))

    def transmission_factor(self, wavelength_angstrom: float) -> float:
        """Evaluate linear wavelength-dependent transmission."""

        wavelength = validate_wavelength_angstrom(wavelength_angstrom)
        value = self.reference_transmission + self.slope_per_angstrom * (
            wavelength - self.reference_wavelength_angstrom
        )
        return _transmission_factor(value, "evaluated transmission")


def evaluate_absorption_transmission(
    hook: WavelengthDependentAbsorptionHook | None,
    wavelength_angstrom: float,
) -> float:
    """Evaluate an optional neutron absorption hook.

    Args:
        hook: Absorption hook or ``None``. ``None`` represents no attenuation
            and returns ``1.0``.
        wavelength_angstrom: Positive neutron wavelength in angstroms.

    Returns:
        Dimensionless transmission factor on ``[0, 1]``.

    Raises:
        ValueError: If wavelength or returned transmission is invalid, or if
            the hook does not expose ``transmission_factor``.

    Example:
        >>> evaluate_absorption_transmission(None, 1.8)
        1.0
    """

    wavelength = validate_wavelength_angstrom(wavelength_angstrom)
    if hook is None:
        return 1.0
    evaluator = getattr(hook, "transmission_factor", None)
    if not callable(evaluator):
        raise ValueError("absorption hook must define a transmission_factor(wavelength_angstrom) method.")
    return _transmission_factor(evaluator(wavelength), "absorption transmission")


def validate_wavelength_angstrom(wavelength_angstrom: float) -> float:
    """Validate a positive finite neutron wavelength in angstroms.

    Args:
        wavelength_angstrom: Neutron wavelength in angstroms.

    Returns:
        The wavelength as a ``float``.

    Raises:
        ValueError: If the value is not finite and strictly positive.

    Example:
        >>> validate_wavelength_angstrom(1.8)
        1.8
    """

    wavelength = _finite_float(wavelength_angstrom, "wavelength_angstrom")
    if wavelength <= 0.0:
        raise ValueError(f"wavelength_angstrom must be positive, got {wavelength!r}.")
    return wavelength


def _transmission_factor(value: float, name: str) -> float:
    transmission = _finite_float(value, name)
    if transmission < 0.0 or transmission > 1.0:
        raise ValueError(f"{name} must be on [0, 1], got {transmission!r}.")
    return transmission


def _finite_float(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}.")
    return float(value)
